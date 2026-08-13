from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import src.services.owner_asset_evidence_service as evidence_service
from src.services.draft_day_app_v1_service import (
    FULL_DYNASTY_VIEW,
    display_unified_player_board_frame,
    sort_rankings_frame_by_column,
)
from src.services.draft_day_trade_lab_service import (
    build_registry_trade_item_lookup,
    build_trade_narrative,
    cross_side_duplicates,
    replace_trade_state,
    trade_asset_ids_by_side,
    trade_item_rows,
)
from src.services.owner_asset_evidence_service import compose_owner_asset_evidence
from src.services.owner_caveat_presentation_service import (
    owner_caveat_summary,
    owner_evidence_status,
)
from src.services.trade_brief_export_service import build_trade_brief


def _asset(
    asset_id: str,
    name: str,
    *,
    asset_type: str = "Current Player",
    position: str = "WR",
    rank: str = "",
    score: str = "",
    warning: str = "",
    age: str = "",
) -> dict[str, str]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_name": name,
        "position": position,
        "team": "TEST",
        "age": age,
        "source_label": "Finished V1" if asset_type == "Current Player" else "Rookie Review",
        "authority_status": "Production" if asset_type == "Current Player" else "Review-Only",
        "rank_label": "NWR Dynasty Rank"
        if asset_type == "Current Player"
        else "Rookie Review Rank",
        "rank_value": rank,
        "tier": "",
        "score_label": "NWR Dynasty Score",
        "score_value": score,
        "confidence": "usable",
        "warnings": warning,
        "blocking_reason": "",
        "comparison_scope": "Source-separated only",
    }


def test_market_numeric_sort_regression_exact_owner_example_and_missing_last() -> None:
    values = ["98", "978", "9716", "9626", "96", "9184", "9141", "91", ""]
    frame = pd.DataFrame(
        {
            "player_name": [f"Player {index}" for index in range(len(values))],
            "position": "WR",
            "nwr_rank": [str(index + 1) for index in range(len(values))],
            "nwr_dynasty_score": "1.0",
            "dp_value_1qb": values,
        }
    )

    descending = sort_rankings_frame_by_column(
        frame,
        "dp_value_1qb",
        ascending=False,
        view_mode=FULL_DYNASTY_VIEW,
    )
    ascending = sort_rankings_frame_by_column(
        frame,
        "dp_value_1qb",
        ascending=True,
        view_mode=FULL_DYNASTY_VIEW,
    )

    assert descending["dp_value_1qb"].tolist() == [
        "9716",
        "9626",
        "9184",
        "9141",
        "978",
        "98",
        "96",
        "91",
        "",
    ]
    assert ascending["dp_value_1qb"].tolist() == [
        "91",
        "96",
        "98",
        "978",
        "9141",
        "9184",
        "9626",
        "9716",
        "",
    ]


def test_rendered_rankings_market_age_gap_and_percent_fields_remain_numeric() -> None:
    frame = pd.DataFrame(
        [
            {
                "nwr_rank": "85",
                "player_name": "Luther Burden",
                "position": "WR",
                "nfl_team": "CHI",
                "age": "22.5",
                "nwr_dynasty_score": "23.9912",
                "nwr_position_rank": "WR47",
                "dp_value_1qb": "4443",
                "dp_market_rank_1qb": "36.6",
                "dp_ecr_pos": "21.4",
                "dp_age": "22.5",
                "market_gap": "48.4",
                "wr_t24_display_only": "86%",
            }
        ]
    )
    display = display_unified_player_board_frame(
        frame,
        view_mode=FULL_DYNASTY_VIEW,
        show_market_baseline=True,
        outcome_mode="All outcome columns",
    )

    for column in (
        "Dynasty Rank",
        "Age",
        "NWR Dynasty Score",
        "DP Value",
        "DP Rank",
        "DP ECR",
        "DP Age",
        "Market Gap",
        "WR T24",
    ):
        assert pd.api.types.is_numeric_dtype(display[column]), column
    assert display.loc[0, "WR T24"] == 86


def test_canonical_evidence_preserves_finished_v1_and_recovers_market(monkeypatch) -> None:
    registry = (
        _asset("current:12519", "Luther Burden", rank="85", score="23.9912"),
        _asset("current:7594", "Chuba Hubbard", position="RB", rank="117", score="18.6020"),
        _asset("current:4217", "George Kittle", position="TE", rank="151", score="14.7218"),
        _asset("current:8183", "Brock Purdy", position="QB", rank="185", score="11.3396"),
        _asset("current:9493", "Puka Nacua", rank="1", score="83.0486"),
        _asset("rookie:BEL267684", "Chris Bell", asset_type="Rookie Review", rank="12"),
    )
    dynasty = pd.DataFrame(
        [
            {
                "player_id": asset_id.removeprefix("current:"),
                "player_name": name,
                "position": position,
                "nfl_team": "TEST",
                "age": age,
                "nwr_rank": rank,
                "nwr_position_rank": position_rank,
                "nwr_dynasty_score": score,
                "confidence_status": "usable",
            }
            for asset_id, name, position, age, rank, position_rank, score in (
                ("current:12519", "Luther Burden", "WR", "22.0", "85", "WR47", "23.9912"),
                ("current:7594", "Chuba Hubbard", "RB", "27.0", "117", "RB29", "18.6020"),
                ("current:4217", "George Kittle", "TE", "32.0", "151", "TE15", "14.7218"),
                ("current:8183", "Brock Purdy", "QB", "26.0", "185", "QB21", "11.3396"),
                ("current:9493", "Puka Nacua", "WR", "25.0", "1", "WR1", "83.0486"),
            )
        ]
    )
    market = {
        "12519": ("4443", "36.6"),
        "7594": ("538", "126.4"),
        "4217": ("916", "103.8"),
        "8183": ("2041", "69.7"),
        "9493": ("9076", "6.2"),
    }

    def fake_join(frame: pd.DataFrame, _artifact_dir) -> pd.DataFrame:
        enriched = frame.copy()
        enriched["dp_value_1qb"] = enriched["player_id"].map(lambda key: market[key][0])
        enriched["dp_market_rank_1qb"] = enriched["player_id"].map(lambda key: market[key][1])
        enriched["market_join_confidence"] = "exact_id"
        return enriched

    monkeypatch.setattr(evidence_service, "join_market_to_players", fake_join)
    monkeypatch.setattr(
        evidence_service,
        "load_market_freshness",
        lambda _artifact_dir: {
            "freshness_status": "YELLOW_STALE",
            "upstream_scrape_date": "2026-07-17",
        },
    )
    bundle = compose_owner_asset_evidence(registry, dynasty_frame=dynasty)

    expected = {
        "Luther Burden": ("85", "WR47", "23.9912", "4443", "36.6"),
        "Chuba Hubbard": ("117", "RB29", "18.6020", "538", "126.4"),
        "George Kittle": ("151", "TE15", "14.7218", "916", "103.8"),
        "Brock Purdy": ("185", "QB21", "11.3396", "2041", "69.7"),
        "Puka Nacua": ("1", "WR1", "83.0486", "9076", "6.2"),
    }
    for name, values in expected.items():
        row = next(item for item in bundle.rows if item["asset_name"] == name)
        assert (
            row["dynasty_rank"],
            row["position_rank"],
            row["nwr_dynasty_score"],
            row["market_dp_value"],
            row["market_dp_rank"],
        ) == values
        assert row["market_status"] == "Stale as of 2026-07-17"
    chris = next(item for item in bundle.rows if item["asset_name"] == "Chris Bell")
    assert chris["dynasty_rank"] == ""
    assert chris["rank_value"] == "12"


def test_owner_evidence_preserves_frozen_board_display_market_rank_without_legacy_join() -> None:
    rows = (_asset("current:9493", "Puka Nacua", rank="1"),)
    dynasty = pd.DataFrame(
        [
            {
                "player_id": "9493",
                "player_name": "Puka Nacua",
                "position": "WR",
                "nwr_rank": "1",
                "market_rank": "3.7",
                "market_rank_source": "market_gap_report.dynasty_startup_adp",
            }
        ]
    )

    evidence = compose_owner_asset_evidence(rows, dynasty_frame=dynasty, include_market=False)

    assert evidence.rows[0]["market_dp_rank"] == "3.7"
    assert evidence.rows[0]["market_status"] == "Display-only source context"


def test_owner_evidence_preserves_governed_rookie_age_without_current_player_row() -> None:
    rows = (
        _asset(
            "rookie:LOV121782",
            "Jeremiyah Love",
            asset_type="Rookie Review",
            position="RB",
            rank="1",
            age="20.895706",
        ),
    )

    evidence = compose_owner_asset_evidence(rows, include_market=False)

    assert evidence.rows[0]["age"] == "20.895706"


def test_current_trade_is_exact_and_brock_purdy_cannot_ghost_into_any_derived_output() -> None:
    rows = (
        _asset("current:12519", "Luther Burden", rank="85"),
        _asset("rookie:BEL267684", "Chris Bell", asset_type="Rookie Review", rank="12"),
        _asset("current:7594", "Chuba Hubbard", position="RB", rank="117"),
        _asset("current:4217", "George Kittle", position="TE", rank="151"),
        _asset("current:8183", "Brock Purdy", position="QB", rank="185"),
    )
    evidence = compose_owner_asset_evidence(rows, include_market=False)
    lookup = build_registry_trade_item_lookup(evidence.rows)
    keys = {str(row["player"]): key for key, row in lookup.items()}
    state = replace_trade_state(
        [keys["Luther Burden"], keys["Chris Bell"], "registry:stale-brock"],
        [keys["Chuba Hubbard"], keys["George Kittle"]],
    )

    selected = trade_item_rows(state, lookup)
    ids = trade_asset_ids_by_side(state, lookup)
    narrative = build_trade_narrative(state, lookup)
    assert selected["player"].tolist() == [
        "Luther Burden",
        "Chris Bell",
        "Chuba Hubbard",
        "George Kittle",
    ]
    assert ids == {
        "give": ["current:12519", "rookie:BEL267684"],
        "get": ["current:7594", "current:4217"],
    }
    assert "Brock Purdy" not in " ".join((*narrative.differences, *narrative.bottom_line))
    assert cross_side_duplicates([keys["Luther Burden"]], [keys["Luther Burden"]])


def test_current_trade_markdown_and_json_use_the_same_exact_sides() -> None:
    rows = (
        _asset("current:12519", "Luther Burden", rank="85"),
        _asset("rookie:BEL267684", "Chris Bell", asset_type="Rookie Review", rank="12"),
        _asset("current:7594", "Chuba Hubbard", position="RB", rank="117"),
        _asset("current:4217", "George Kittle", position="TE", rank="151"),
    )
    assets = compose_owner_asset_evidence(rows, include_market=False).by_id
    brief = build_trade_brief(
        {
            "title": "Owner trade",
            "created_at_utc": "2026-08-10T00:00:00+00:00",
            "side_a": ["current:12519", "rookie:BEL267684"],
            "side_b": ["current:7594", "current:4217"],
            "team_window": "Balanced",
            "rationale": "",
        },
        assets=assets,
    )
    payload = json.loads(brief.structured_json)
    assert [row["name"] for row in payload["side_a"]] == ["Luther Burden", "Chris Bell"]
    assert [row["name"] for row in payload["side_b"]] == ["Chuba Hubbard", "George Kittle"]
    assert "## You give" in brief.markdown
    assert "## You receive" in brief.markdown
    assert "Brock Purdy" not in brief.markdown


def test_owner_caveat_translation_hides_receipt_codes() -> None:
    summary = owner_caveat_summary(
        "licensed_route_metrics_not_available|rb_dynasty_age_curve_after_27_active",
        limit=3,
    )
    assert summary == (
        "Route-level metrics are unavailable. RB age-related decline adjustment is active."
    )
    assert "licensed_route_metrics_not_available" not in summary
    assert owner_evidence_status("RESEARCH_ONLY_NOT_ADMITTED") == (
        "Research-only; not admitted to Finished V1."
    )


def test_trade_narrative_prioritizes_supported_age_window_context() -> None:
    rows = (
        _asset("current:12519", "Luther Burden", rank="85"),
        _asset(
            "current:7594",
            "Chuba Hubbard",
            position="RB",
            rank="117",
            warning="licensed_route_metrics_not_available|rb_dynasty_age_curve_after_27_active",
        ),
        _asset(
            "current:4217",
            "George Kittle",
            position="TE",
            rank="151",
            warning="te_no_premium_age_curve_after_30_active",
        ),
    )
    evidence = compose_owner_asset_evidence(rows, include_market=False)
    lookup = build_registry_trade_item_lookup(evidence.rows)
    keys = {str(row["player"]): key for key, row in lookup.items()}
    narrative = build_trade_narrative(
        replace_trade_state(
            [keys["Luther Burden"]],
            [keys["Chuba Hubbard"], keys["George Kittle"]],
        ),
        lookup,
    )
    combined = " ".join((*narrative.differences, *narrative.bottom_line))
    assert "Chuba Hubbard" in combined
    assert "RB age-related decline adjustment is active" in combined
    assert "George Kittle" in combined
    assert "TE age-related decline adjustment is active" in combined


def test_trade_narrative_handles_required_asset_compositions_without_a_hidden_verdict() -> None:
    rows = (
        _asset("current:a", "Veteran A", rank="10"),
        _asset("current:b", "Veteran B", position="RB", rank="20"),
        _asset("rookie:r", "Rookie R", asset_type="Rookie Review", rank="5"),
        _asset("rookie:x", "Blocked X", asset_type="Blocked Rookie"),
        _asset("pick:2026:1.05", "2026 1.05", asset_type="Draft Pick"),
        _asset("pick:2028:R1", "2028 Round 1", asset_type="Future Pick"),
    )
    evidence = compose_owner_asset_evidence(rows, include_market=False)
    lookup = build_registry_trade_item_lookup(evidence.rows)
    keys = {str(row["player"]): key for key, row in lookup.items()}
    cases = (
        (["Veteran A"], ["Veteran B"]),
        (["Veteran A", "2026 1.05"], ["Veteran B"]),
        (["Rookie R", "2028 Round 1"], ["Veteran B"]),
        (["Blocked X"], ["Veteran B"]),
    )
    for give_names, receive_names in cases:
        narrative = build_trade_narrative(
            replace_trade_state(
                [keys[name] for name in give_names],
                [keys[name] for name in receive_names],
            ),
            lookup,
        )
        text = " ".join((*narrative.differences, *narrative.bottom_line)).casefold()
        assert narrative.differences
        assert narrative.bottom_line
        assert "winner" not in text
        assert "trade grade" not in text
        assert "package value" not in text
        assert "accept this trade" not in text

    empty = build_trade_narrative(
        replace_trade_state([keys["Veteran A"]], []),
        lookup,
    )
    assert empty.bottom_line == ("Add at least one asset to each side.",)

    duplicate = replace_trade_state([keys["Veteran A"]], [keys["Veteran A"]])
    assert duplicate == {"give": [keys["Veteran A"]], "get": []}


def test_primary_trade_page_uses_one_current_trade_and_owner_language() -> None:
    page = Path("app/pages/23_trading_lab_v1.py").read_text(encoding="utf-8")
    assert '"You give"' in page
    assert '"You receive"' in page
    assert "Trade at a glance" in page
    assert "How the sides differ" in page
    assert "Bottom line" in page
    assert "brief_side_a" not in page
    assert "brief_side_b" not in page
    assert "Shareable source-labeled trade brief" not in page
    assert "Full Dynasty Rankings | GREEN | 240 rows" not in page
