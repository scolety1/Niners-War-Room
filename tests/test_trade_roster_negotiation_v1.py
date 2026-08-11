from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.services.draft_day_trade_lab_service import replace_trade_state
from src.services.personal_workspace_service import create_decision, load_store
from src.services.trade_roster_negotiation_service import (
    COUNTER_BLOCKED,
    COUNTERPARTY_RESOLVED,
    MARKET_DATE,
    ROSTER_STATE,
    OwnedAsset,
    RosterOwnershipAudit,
    build_market_negotiation_context,
    build_opponent_opportunity_map,
    build_roster_composition,
    generate_roster_aware_counters,
    resolve_trade_ownership,
)


def _row(
    key: str,
    name: str,
    *,
    rank: object = "",
    position: str = "WR",
    market_value: object = "",
    market_rank: object = "",
    registry_type: str = "Current Player",
) -> tuple[str, dict[str, object]]:
    return key, {
        "item_key": key,
        "asset_id": key.removeprefix("registry:"),
        "asset_type": "Pick context" if registry_type == "Future Pick" else "Player",
        "registry_asset_type": registry_type,
        "player": name,
        "label": name,
        "position": position,
        "dynasty_rank": rank,
        "market_dp_value": market_value,
        "market_dp_rank": market_rank,
        "market_status": f"Stale as of {MARKET_DATE}" if market_value else "Not available",
    }


def _asset(
    asset_id: str,
    name: str,
    team_id: str,
    team_name: str,
    *,
    position: str = "WR",
) -> OwnedAsset:
    return OwnedAsset(asset_id, name, "player", team_id, team_name, position)


def _audit(*assets: OwnedAsset) -> RosterOwnershipAudit:
    return RosterOwnershipAudit(
        classification=ROSTER_STATE,
        source_path="fixture/fact_rosters.csv",
        snapshot_date="2026-pre-draft",
        league_id="league-1",
        owner_team_id="7",
        owner_team_name="Niners",
        player_assets=tuple(assets),
        pick_assets=(),
        team_asset_counts=(("Niners", 2), ("Opponent", 4)),
        warnings=("Future-pick ownership is incomplete.",),
    )


def test_actual_owner_trade_fails_closed_on_split_teams_and_missing_assets() -> None:
    keys = {
        "luther": "registry:current:12519",
        "bell": "registry:rookie:BEL267684",
        "first": "registry:pick:2027:1st",
        "kittle": "registry:current:4217",
        "chuba": "registry:current:7594",
        "purdy": "registry:current:8183",
        "second": "registry:pick:2028:2nd",
    }
    lookup = dict(
        [
            _row(keys["luther"], "Luther Burden", rank=85),
            _row(keys["bell"], "Chris Bell", registry_type="Rookie Review"),
            _row(keys["first"], "2027 1st", registry_type="Future Pick", position="PICK"),
            _row(keys["kittle"], "George Kittle", rank=151, position="TE"),
            _row(keys["chuba"], "Chuba Hubbard", rank=117, position="RB"),
            _row(keys["purdy"], "Brock Purdy", rank=185, position="QB"),
            _row(keys["second"], "2028 2nd", registry_type="Future Pick", position="PICK"),
        ]
    )
    audit = _audit(
        _asset("current:12519", "Luther Burden", "7", "Niners"),
        _asset("current:4217", "George Kittle", "3", "The Mighty Canucks", position="TE"),
        _asset("current:7594", "Chuba Hubbard", "3", "The Mighty Canucks", position="RB"),
        _asset("current:8183", "Brock Purdy", "6", "WhoDat?", position="QB"),
    )
    state = replace_trade_state(
        [keys["luther"], keys["bell"], keys["first"]],
        [keys["kittle"], keys["chuba"], keys["purdy"], keys["second"]],
    )

    resolved = resolve_trade_ownership(state, lookup, audit)

    assert resolved.classification == "PARTIAL_ROSTER_STATE"
    assert resolved.status == COUNTER_BLOCKED
    assert resolved.candidate_counterparty_teams == ("The Mighty Canucks", "WhoDat?")
    assert any("multiple teams" in conflict for conflict in resolved.conflicts)
    assert any("Chris Bell" in conflict for conflict in resolved.conflicts)
    assert any("2027 1st" in conflict for conflict in resolved.conflicts)
    assert generate_roster_aware_counters(
        state, lookup, audit, resolved, team_window="Balanced"
    ) == ()


def test_market_negotiation_totals_are_same_snapshot_partial_and_not_nwr_value() -> None:
    lookup = dict(
        [
            _row("registry:current:12519", "Luther Burden", market_value=4443),
            _row("registry:rookie:bell", "Chris Bell", registry_type="Rookie Review"),
            _row(
                "registry:pick:2027:1st",
                "2027 1st",
                registry_type="Future Pick",
                position="PICK",
            ),
            _row("registry:current:4217", "George Kittle", market_value=916),
            _row("registry:current:7594", "Chuba Hubbard", market_value=538),
            _row("registry:current:8183", "Brock Purdy", market_value=2041),
            _row(
                "registry:pick:2028:2nd",
                "2028 2nd",
                registry_type="Future Pick",
                position="PICK",
            ),
        ]
    )
    state = replace_trade_state(
        ["registry:current:12519", "registry:rookie:bell", "registry:pick:2027:1st"],
        [
            "registry:current:4217",
            "registry:current:7594",
            "registry:current:8183",
            "registry:pick:2028:2nd",
        ],
    )

    market = build_market_negotiation_context(state, lookup)

    assert market.same_snapshot
    assert market.give.displayed_total == 4443
    assert market.receive.displayed_total == 3495
    assert market.displayed_delta_receive_minus_give == -948
    assert market.give.excluded_assets == ("Chris Bell", "2027 1st")
    assert market.receive.excluded_assets == ("2028 2nd",)
    assert "not an NWR package value" in market.warning
    assert MARKET_DATE in market.label


def test_resolved_opponent_map_and_counters_use_only_exact_owned_assets() -> None:
    owner_a, owner_b = "registry:current:owner-a", "registry:current:owner-b"
    offered, elite, buy_low, depth = (
        "registry:current:offered",
        "registry:current:elite",
        "registry:current:buy-low",
        "registry:current:depth",
    )
    lookup = dict(
        [
            _row(owner_a, "Owner Premium", rank=35, market_value=5000, market_rank=30),
            _row(owner_b, "Owner Depth", rank=130, market_value=900, market_rank=130),
            _row(offered, "Offered Veteran", rank=140, market_value=1000, market_rank=130),
            _row(elite, "Opponent Elite", rank=20, market_value=6500, market_rank=22),
            _row(buy_low, "Opponent Buy Low", rank=45, market_value=2500, market_rank=115),
            _row(depth, "Opponent Depth", rank=120, market_value=1100, market_rank=125),
        ]
    )
    audit = _audit(
        _asset("current:owner-a", "Owner Premium", "7", "Niners"),
        _asset("current:owner-b", "Owner Depth", "7", "Niners"),
        _asset("current:offered", "Offered Veteran", "3", "Opponent", position="RB"),
        _asset("current:elite", "Opponent Elite", "3", "Opponent"),
        _asset("current:buy-low", "Opponent Buy Low", "3", "Opponent"),
        _asset("current:depth", "Opponent Depth", "3", "Opponent", position="TE"),
    )
    state = replace_trade_state([owner_a, owner_b], [offered])
    resolved = resolve_trade_ownership(state, lookup, audit)

    assert resolved.status == COUNTERPARTY_RESOLVED
    assert resolved.counterparty_team_name == "Opponent"
    opportunities = build_opponent_opportunity_map(
        audit, resolved, lookup, team_window="Balanced"
    )
    buy_low_row = next(row for row in opportunities if row.asset_name == "Opponent Buy Low")
    assert buy_low_row.gap_interpretation.startswith("NWR higher than market")
    counters = generate_roster_aware_counters(
        state, lookup, audit, resolved, team_window="Balanced"
    )
    assert len(counters) >= 2
    assert any("Keep the premium" in row.title for row in counters)
    assert any(owner_a in row.give for row in counters)
    owner_ids = {"current:owner-a", "current:owner-b"}
    opponent_ids = {
        "current:offered",
        "current:elite",
        "current:buy-low",
        "current:depth",
    }
    for counter in counters:
        assert {lookup[key]["asset_id"] for key in counter.give} <= owner_ids
        assert {lookup[key]["asset_id"] for key in counter.receive} <= opponent_ids
        assert not (set(counter.give) & set(counter.receive))


def test_roster_composition_uses_factual_positions_without_inferred_plan() -> None:
    audit = _audit(
        _asset("current:a", "A", "3", "Opponent", position="QB"),
        _asset("current:b", "B", "3", "Opponent", position="WR"),
        _asset("current:c", "C", "3", "Opponent", position="WR"),
    )
    composition = build_roster_composition(audit, "3")
    assert composition.team_name == "Opponent"
    assert dict(composition.position_counts) == {"QB": 1, "WR": 2}
    assert composition.pick_count == 0


def test_advisory_trade_receipt_persists_and_reloads_without_source_mutation(
    tmp_path: Path,
) -> None:
    registry = {"current:a": "Current Player", "current:b": "Current Player"}
    source_snapshot = {
        key: {"asset_type": asset_type, "source_version": "fixture-v1"}
        for key, asset_type in registry.items()
    }
    result = create_decision(
        {
            "decision_id": "trade-advisory-1",
            "decision_type": "trade considered",
            "status": "Considered",
            "assets": list(registry),
            "source_snapshot": source_snapshot,
            "rationale": "Owner is reviewing the advisory result.",
            "team_window": "Balanced",
            "trade_sides": {
                "you_give": ["current:a"],
                "you_receive": ["current:b"],
            },
            "advisory_decision_support": {
                "authority": "ADVISORY_DECISION_SUPPORT",
                "recommendation": "COUNTER",
                "confidence": "MEDIUM",
                "reasons": ["Named ordinal evidence is mixed."],
            },
            "counter_considered": "Roster-aware counter",
            "owner_final_decision": "Undecided",
        },
        asset_registry=registry,
        root=tmp_path,
        now_utc="2026-08-11T12:00:00+00:00",
    )

    assert result.status == "SAVED"
    reloaded = load_store("decision_journal", root=tmp_path)
    assert reloaded.status == "LOADED"
    assert reloaded.records[0]["advisory_decision_support"]["recommendation"] == "COUNTER"
    assert reloaded.records[0]["source_snapshot"] == source_snapshot


def test_pick_ownership_resolves_only_from_exact_year_round_and_team() -> None:
    give = "registry:current:owner"
    receive = "registry:current:opponent"
    future = "registry:pick:2028:2nd"
    lookup = dict(
        [
            _row(give, "Owner Player", rank=80),
            _row(receive, "Opponent Player", rank=90),
            _row(future, "2028 2nd", registry_type="Future Pick", position="PICK"),
        ]
    )
    base = _audit(
        _asset("current:owner", "Owner Player", "7", "Niners"),
        _asset("current:opponent", "Opponent Player", "3", "Opponent"),
    )
    pick = OwnedAsset(
        "pick:2028:2:3",
        "2028 2.03",
        "pick",
        "3",
        "Opponent",
        "PICK",
        2028,
        2,
        "Opponent",
    )
    audit = replace(base, pick_assets=(pick,), warnings=())
    resolved = resolve_trade_ownership(
        replace_trade_state([give], [receive, future]), lookup, audit
    )

    assert resolved.status == COUNTERPARTY_RESOLVED
    pick_check = next(row for row in resolved.checks if row.asset_name == "2028 2nd")
    assert pick_check.resolved_team == "Opponent"
    assert "one exact" in pick_check.evidence


def test_market_totals_fail_closed_when_dates_do_not_match() -> None:
    give = "registry:current:a"
    receive = "registry:current:b"
    lookup = dict(
        [
            _row(give, "A", market_value=1000),
            _row(receive, "B", market_value=900),
        ]
    )
    lookup[receive]["market_status"] = "Stale as of 2026-07-16"

    market = build_market_negotiation_context(
        replace_trade_state([give], [receive]), lookup
    )

    assert not market.same_snapshot
    assert market.displayed_delta_receive_minus_give is None


def test_page_wires_load_compare_receipt_and_no_generic_fallback() -> None:
    page = (
        Path(__file__).resolve().parents[1] / "app" / "pages" / "23_trading_lab_v1.py"
    ).read_text(encoding="utf-8")
    assert "Load this counter" in page
    assert "Original vs loaded counter" in page
    assert "Save Decision Receipt" in page
    assert "No generic fallback is shown" in page
    assert "generate_roster_aware_counters(" in page
