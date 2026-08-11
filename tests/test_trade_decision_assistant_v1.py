from __future__ import annotations

from copy import deepcopy

import pytest

from src.services.draft_day_trade_lab_service import replace_trade_state
from src.services.trade_decision_assistant_service import (
    AUTHORITY,
    DIMENSION_OUTCOMES,
    RECOMMENDATIONS,
    evaluate_team_windows,
    evaluate_trade_decision,
)


def _player(
    key: str,
    name: str,
    *,
    rank: object = "",
    position: str = "WR",
    position_rank: str = "",
    age: object = "",
    registry_type: str = "Current Player",
    caveats: tuple[str, ...] = (),
    market_rank: object = "",
    market_status: str = "Not available",
) -> tuple[str, dict[str, object]]:
    return key, {
        "item_key": key,
        "asset_id": key.removeprefix("registry:"),
        "asset_type": "Player",
        "registry_asset_type": registry_type,
        "label": name,
        "player": name,
        "position": position,
        "position_rank": position_rank,
        "age": age,
        "dynasty_rank": rank if registry_type == "Current Player" else "",
        "final_board_rank": rank if registry_type == "Rookie Review" else "",
        "market_dp_rank": market_rank,
        "market_status": market_status,
        "owner_caveats": caveats,
        "outcome_signals": (),
    }


def _pick(key: str, name: str) -> tuple[str, dict[str, object]]:
    return key, {
        "item_key": key,
        "asset_id": key.removeprefix("registry:"),
        "asset_type": "Pick context",
        "registry_asset_type": "Future Pick",
        "label": name,
        "player": name,
        "position": "PICK",
        "dynasty_rank": "",
        "owner_caveats": (
            "Slot unknown.",
            "No governed player-equivalence value is available for this pick.",
        ),
        "market_dp_rank": "",
        "market_status": "Not available",
        "outcome_signals": (),
    }


def _blocked(key: str, name: str) -> tuple[str, dict[str, object]]:
    item_key, row = _player(
        key,
        name,
        registry_type="Blocked Rookie",
        caveats=("Identity evidence is blocked.",),
    )
    return item_key, row


def _decision(
    entries: list[tuple[str, dict[str, object]]],
    give: list[str],
    receive: list[str],
    *,
    team_window: str = "Balanced",
):
    return evaluate_trade_decision(
        replace_trade_state(give, receive),
        dict(entries),
        team_window=team_window,
    )


def test_t1_clear_top_asset_advantage_follows_declared_rank_bands() -> None:
    a = "registry:current:a"
    b = "registry:current:b"
    decision = _decision(
        [_player(a, "Premium WR", rank=10, age=23), _player(b, "Depth WR", rank=170, age=29)],
        [a],
        [b],
    )

    best = next(row for row in decision.dimensions if row.code == "D1")
    assert best.outcome == "SIDE_A_CLEAR"
    assert decision.preferred_side == "Your current side"
    assert decision.recommendation in {"LEAN_REJECT", "REJECT"}


def test_t2_depth_package_versus_premium_asset_is_mixed_not_secretly_summed() -> None:
    premium = "registry:current:premium"
    depth_a = "registry:current:depth-a"
    depth_b = "registry:current:depth-b"
    decision = _decision(
        [
            _player(premium, "Premium Asset", rank=20),
            _player(depth_a, "Depth One", rank=65),
            _player(depth_b, "Depth Two", rank=90),
        ],
        [premium],
        [depth_a, depth_b],
    )

    by_code = {row.code: row for row in decision.dimensions}
    assert by_code["D1"].outcome == "SIDE_A_CLEAR"
    assert by_code["D2"].outcome == "SIDE_B_LEAN"
    assert by_code["D4"].outcome == "SIDE_B_LEAN"
    assert decision.recommendation in {"COUNTER", "TOO_CLOSE"}
    assert "package score" in decision.synthesis_trace[-1]


def test_t3_rookie_heavy_trade_stays_on_rookie_authority() -> None:
    a = "registry:rookie:a"
    b = "registry:rookie:b"
    decision = _decision(
        [
            _player(a, "Rookie A", rank=1, registry_type="Rookie Review"),
            _player(b, "Rookie B", rank=5, registry_type="Rookie Review"),
        ],
        [a],
        [b],
    )

    assert next(row for row in decision.dimensions if row.code == "D1").outcome == "UNKNOWN"
    assert decision.recommendation == "TOO_CLOSE"
    assert "Finished V1" in decision.main_uncertainty


def test_t4_future_pick_heavy_trade_uses_round_then_year_only() -> None:
    a1, a2 = "registry:pick:2027:1st", "registry:pick:2028:1st"
    b1, b2 = "registry:pick:2027:2nd", "registry:pick:2028:2nd"
    decision = _decision(
        [
            _pick(a1, "2027 1st"),
            _pick(a2, "2028 1st"),
            _pick(b1, "2027 2nd"),
            _pick(b2, "2028 2nd"),
        ],
        [a1, a2],
        [b1, b2],
    )

    future = next(row for row in decision.dimensions if row.code == "D6")
    assert future.outcome == "SIDE_A_CLEAR"
    assert "No player-equivalent" in future.explanation
    assert decision.preferred_side == "Your current side"


def test_t5_aging_veterans_versus_youth_uses_lifecycle_evidence() -> None:
    youth = "registry:current:youth"
    veteran = "registry:current:veteran"
    decision = _decision(
        [
            _player(youth, "Young WR", rank=80, age=23),
            _player(
                veteran,
                "Older RB",
                rank=70,
                age=30,
                position="RB",
                caveats=("RB age-related decline adjustment is active.",),
            ),
        ],
        [youth],
        [veteran],
        team_window="Rebuilding",
    )

    by_code = {row.code: row for row in decision.dimensions}
    assert by_code["D3"].outcome == "SIDE_A_CLEAR"
    assert by_code["D8"].outcome == "SIDE_A_CLEAR"


def test_t6_qb_heavy_trade_is_discounted_in_declared_one_qb_format() -> None:
    flex = "registry:current:flex"
    qb = "registry:current:qb"
    decision = _decision(
        [
            _player(flex, "Flex WR", rank=95, position="WR"),
            _player(
                qb,
                "Replaceable QB",
                rank=80,
                position="QB",
                position_rank="QB18",
                caveats=("1QB replacement depth limits QB scarcity value.",),
            ),
        ],
        [flex],
        [qb],
    )

    league_fit = next(row for row in decision.dimensions if row.code == "D7")
    assert league_fit.outcome == "SIDE_A_LEAN"
    assert "1QB" in league_fit.explanation


def test_t7_team_window_changes_only_context_dimension_not_base_ranks() -> None:
    young, old_a, old_b = (
        "registry:current:young",
        "registry:current:old-a",
        "registry:current:old-b",
    )
    first = "registry:pick:2027:1st"
    entries = [
        _player(young, "Young WR", rank=45, age=23),
        _pick(first, "2027 1st"),
        _player(old_a, "Veteran RB", rank=60, age=29, position="RB"),
        _player(old_b, "Veteran TE", rank=110, age=31, position="TE"),
    ]
    state = replace_trade_state([young, first], [old_a, old_b])
    lookup = dict(entries)
    original = deepcopy(lookup)
    views = evaluate_team_windows(state, lookup)

    context = {
        row.team_window: next(item for item in row.dimensions if item.code == "D8") for row in views
    }
    assert context["Contending"].outcome.startswith("SIDE_B")
    assert context["Rebuilding"].outcome.startswith("SIDE_A")
    assert lookup == original
    assert all(
        lookup[key].get("dynasty_rank") == original[key].get("dynasty_rank") for key in lookup
    )


def test_t8_blocked_prospect_trade_returns_insufficient_evidence() -> None:
    a, b = "registry:blocked:a", "registry:blocked:b"
    decision = _decision([_blocked(a, "Blocked A"), _blocked(b, "Blocked B")], [a], [b])

    assert decision.recommendation == "INSUFFICIENT_EVIDENCE"
    assert decision.confidence == "LOW"
    assert decision.counters == ()


def test_t9_close_trade_returns_too_close() -> None:
    a, b = "registry:current:a", "registry:current:b"
    decision = _decision(
        [_player(a, "Similar A", rank=55, age=26), _player(b, "Similar B", rank=65, age=26)],
        [a],
        [b],
    )

    assert decision.recommendation == "TOO_CLOSE"
    assert decision.preferred_side == "No clear side"


def test_t10_structurally_mixed_trade_recommends_counter_without_inferred_counters() -> None:
    premium = "registry:current:premium"
    rookie = "registry:rookie:upside"
    first = "registry:pick:2027:1st"
    veteran_a = "registry:current:veteran-a"
    veteran_b = "registry:current:veteran-b"
    qb = "registry:current:qb"
    second = "registry:pick:2028:2nd"
    upgrade = "registry:pick:2028:1st"
    entries = [
        _player(premium, "Premium WR", rank=85, market_rank=36.6, market_status="Stale"),
        _player(rookie, "Rookie Upside", rank=9, registry_type="Rookie Review"),
        _pick(first, "2027 1st"),
        _player(
            veteran_a,
            "Older TE",
            rank=151,
            age=32,
            caveats=("TE age-related decline adjustment is active.",),
        ),
        _player(
            veteran_b,
            "Older RB",
            rank=117,
            age=27,
            position="RB",
            caveats=("RB age-related decline adjustment is active.",),
        ),
        _player(
            qb,
            "QB Depth",
            rank=185,
            position="QB",
            position_rank="QB21",
            caveats=("1QB replacement depth limits QB scarcity value.",),
        ),
        _pick(second, "2028 2nd"),
        _pick(upgrade, "2028 1st"),
    ]
    state = replace_trade_state(
        [premium, rookie, first],
        [veteran_a, veteran_b, qb, second],
    )
    lookup = dict(entries)
    decision = evaluate_trade_decision(state, lookup)

    assert decision.authority == AUTHORITY
    assert decision.recommendation == "COUNTER"
    assert decision.preferred_side == "Your current side"
    # The evidence engine cannot infer ownership. Specific counters are supplied only
    # by the separately tested roster-aware negotiation adapter.
    assert decision.counters == ()


def test_negation_display_formatting_does_not_change_recommendation() -> None:
    a, b = "registry:current:a", "registry:current:b"
    integer = _decision([_player(a, "A", rank=25), _player(b, "B", rank=125)], [a], [b])
    formatted = _decision(
        [_player(a, "A", rank="25.0"), _player(b, "B", rank="125.0")],
        [a],
        [b],
    )
    assert (integer.recommendation, integer.preferred_side) == (
        formatted.recommendation,
        formatted.preferred_side,
    )


def test_negation_stale_unknown_key_cannot_affect_decision() -> None:
    a, b = "registry:current:a", "registry:current:b"
    lookup = dict([_player(a, "A", rank=25), _player(b, "B", rank=125)])
    clean = evaluate_trade_decision(replace_trade_state([a], [b]), lookup)
    stale = evaluate_trade_decision(replace_trade_state([a, "registry:ghost"], [b]), lookup)
    assert (clean.recommendation, clean.dimensions) == (stale.recommendation, stale.dimensions)


def test_negation_missing_values_are_unknown_not_zero() -> None:
    a, b = "registry:current:a", "registry:current:b"
    decision = _decision([_player(a, "A"), _player(b, "B")], [a], [b])
    assert next(row for row in decision.dimensions if row.code == "D1").outcome == "UNKNOWN"


def test_negation_market_is_individual_secondary_context_not_package_total() -> None:
    a1, a2, b = "registry:current:a1", "registry:current:a2", "registry:current:b"
    decision = _decision(
        [
            _player(a1, "A1", rank=100, market_rank=80, market_status="Stale"),
            _player(a2, "A2", rank=110, market_rank=90, market_status="Stale"),
            _player(b, "B", rank=105, market_rank=40, market_status="Stale"),
        ],
        [a1, a2],
        [b],
    )
    market = next(row for row in decision.dimensions if row.code == "D10")
    assert market.outcome == "SIDE_B_LEAN"
    assert any("No market side total" in value for value in market.evidence)
    assert market.confidence == "LOW"


def test_contract_enums_and_dimensions_are_closed() -> None:
    assert set(RECOMMENDATIONS) == {
        "ACCEPT",
        "LEAN_ACCEPT",
        "COUNTER",
        "LEAN_REJECT",
        "REJECT",
        "TOO_CLOSE",
        "INSUFFICIENT_EVIDENCE",
    }
    assert set(DIMENSION_OUTCOMES) == {
        "SIDE_A_CLEAR",
        "SIDE_A_LEAN",
        "EVEN",
        "SIDE_B_LEAN",
        "SIDE_B_CLEAR",
        "UNKNOWN",
    }


@pytest.mark.parametrize("team_window", ("Win now", "Tank"))
def test_unknown_team_window_fails_closed(team_window: str) -> None:
    with pytest.raises(ValueError, match="Unsupported team window"):
        evaluate_trade_decision({"give": [], "get": []}, {}, team_window=team_window)
