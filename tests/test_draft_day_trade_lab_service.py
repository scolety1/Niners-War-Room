from __future__ import annotations

import pandas as pd

from src.services.draft_day_trade_lab_service import (
    NOT_ENOUGH_INFORMATION,
    add_trade_item,
    build_trade_item_lookup,
    classify_market_trade_gap,
    clear_trade_state,
    display_market_package_rows,
    display_package_summary,
    display_trade_item_rows,
    empty_trade_state,
    lookup_pick_market_value,
    lookup_player_market_value,
    package_summary_rows,
    parse_trade_asset_text,
    pick_context_options,
    player_key,
    player_options,
    remove_trade_item,
    review_trade_package,
    summarize_trade_package_market,
    trade_item_rows,
)
from src.services.market_baseline_registry import PAGE_USAGE, validate_market_baseline_registry


def _board() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Premium RB",
                "position": "RB",
                "nfl_team": "SF",
                "final_tier": "Tier 1",
                "position_rank": 1,
                "final_board_score_visible": "95.0",
                "risk_notes": "",
            },
            {
                "final_board_rank": 20,
                "player": "Depth WR",
                "position": "WR",
                "nfl_team": "DAL",
                "final_tier": "Tier 2",
                "position_rank": 9,
                "final_board_score_visible": "60.0",
                "risk_notes": "role check",
            },
        ]
    )


def _trade_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Premium RB",
                "position": "RB",
                "nfl_team": "SF",
                "visible_score_for_context": "95.0",
                "tier_movement_note": "premium tier",
                "position_scarcity_note": "scarce RB",
                "pick_window_note": "",
                "risk_manual_review_notes": "",
            },
            {
                "final_board_rank": 20,
                "player": "Depth WR",
                "position": "WR",
                "nfl_team": "DAL",
                "visible_score_for_context": "60.0",
                "tier_movement_note": "same tier",
                "position_scarcity_note": "",
                "pick_window_note": "late pick window",
                "risk_manual_review_notes": "role check",
            },
        ]
    )


def _pick_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": 1,
                "player": "Premium RB",
                "position": "RB",
                "nfl_team": "SF",
                "rookie_tier_display_only": "Tier 1",
                "pick_window_note": "round=1; pick=3",
                "caveat": "display-only pick context",
            }
        ]
    )


def test_trade_builder_add_remove_and_clear_state() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    players = player_options(lookup)
    premium = players["#1 - Premium RB (RB, SF)"]
    state = add_trade_item(empty_trade_state(), "give", premium)

    assert state["give"] == [premium]

    state = remove_trade_item(state, "give", premium)

    assert state == empty_trade_state()
    assert clear_trade_state() == empty_trade_state()


def test_trade_summary_uses_visible_context_and_not_enough_information() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    players = player_options(lookup)
    state = add_trade_item(empty_trade_state(), "give", players["#20 - Depth WR (WR, DAL)"])
    state = add_trade_item(state, "get", players["#1 - Premium RB (RB, SF)"])

    summary = package_summary_rows(state, lookup)
    review = review_trade_package(state, lookup)

    assert set(summary["side"]) == {"NWR gives", "NWR gets"}
    assert review.status == "Looks favorable"
    assert review.score_gap_display == "+35.00"
    assert "Best get rank 1" in review.rank_context
    display = display_package_summary(summary)
    assert "Visible Score Sum" in display.columns


def test_pick_context_can_be_added_but_does_not_create_trade_value() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    picks = pick_context_options(lookup)
    pick_key = next(iter(picks.values()))
    state = add_trade_item(empty_trade_state(), "give", pick_key)
    state = add_trade_item(
        state,
        "get",
        player_options(lookup)["#1 - Premium RB (RB, SF)"],
    )

    review = review_trade_package(state, lookup)
    rows = trade_item_rows(state, lookup)

    assert review.status == NOT_ENOUGH_INFORMATION
    assert "standalone pick/context" in review.explanation.lower()
    assert rows.loc[rows["asset_type"] == "Pick context", "visible_score_for_context"].isna().all()


def test_display_items_hide_internal_keys() -> None:
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    state = add_trade_item(
        empty_trade_state(),
        "give",
        player_options(lookup)["#1 - Premium RB (RB, SF)"],
    )

    display = display_trade_item_rows(trade_item_rows(state, lookup))

    assert "Asset" in display.columns
    assert "item_key" not in display.columns
    assert not any("hidden" in column.lower() for column in display.columns)


def test_player_key_is_visible_board_identity() -> None:
    row = _board().iloc[0]

    assert player_key(row) == "1|Premium RB|RB|SF"


def _market_artifacts(tmp_path) -> str:
    pd.DataFrame(
        [
            {
                "player": "Premium RB",
                "pos": "RB",
                "dp_market_rank_1qb": "10",
                "dp_value_1qb": "5000",
                "join_method": "exact_name_position",
                "join_confidence": "high",
                "dp_display_only_warning": "Display-only DynastyProcess market baseline",
                "freshness_status": "GREEN_CURRENT",
            }
        ]
    ).to_csv(tmp_path / "dp_market_baseline_context.csv", index=False)
    pd.DataFrame(
        [
            {
                "pick_label": "2026 1.04",
                "value_1qb": "3920",
                "ecr_1qb": "41.925",
                "freshness_status": "GREEN_CURRENT",
            },
            {
                "pick_label": "2026 2.03",
                "value_1qb": "1024",
                "ecr_1qb": "109.000",
                "freshness_status": "GREEN_CURRENT",
            },
            {
                "pick_label": "2028 1st",
                "value_1qb": "1490",
                "ecr_1qb": "83.094",
                "freshness_status": "GREEN_CURRENT",
            },
            {
                "pick_label": "2028 2nd",
                "value_1qb": "169",
                "ecr_1qb": "175.795",
                "freshness_status": "GREEN_CURRENT",
            },
            {
                "pick_label": "2027 3rd",
                "value_1qb": "38",
                "ecr_1qb": "239.462",
                "freshness_status": "GREEN_CURRENT",
            },
        ]
    ).to_csv(tmp_path / "dp_pick_value_context.csv", index=False)
    pd.DataFrame(
        [
            {
                "nwr_fetch_timestamp": "2026-06-23T22:37:05+00:00",
                "upstream_scrape_date": "2026-06-19",
                "upstream_latest_commit_sha": "abc",
                "upstream_latest_commit_timestamp": "2026-06-19T07:33:57Z",
                "freshness_status": "GREEN_CURRENT",
            }
        ]
    ).to_csv(tmp_path / "dp_freshness_report.csv", index=False)
    return str(tmp_path)


def test_market_pick_parsing_required_examples() -> None:
    rows = parse_trade_asset_text(
        "2026 1.04, 2026 2.03, 2028 1st, 2028 2nd, 2027 3rd, unknown text"
    )

    by_raw = {row["raw_text"]: row for row in rows}
    assert by_raw["2026 1.04"]["pick_label"] == "1.04"
    assert by_raw["2026 2.03"]["display_label"] == "2026 2.03"
    assert by_raw["2028 1st"]["asset_type"] == "future_pick"
    assert by_raw["2028 2nd"]["round"] == 2
    assert by_raw["2027 3rd"]["round"] == 3
    assert by_raw["unknown text"]["status"] == "REVIEW_NEEDED"


def test_pick_market_lookup_matches_pick_values(tmp_path) -> None:
    artifact_dir = _market_artifacts(tmp_path)

    value = lookup_pick_market_value("2026 1.04", artifact_dir=artifact_dir)

    assert value["dp_value"] == "3920"
    assert value["market_baseline_label"] == "Market Baseline / Display-Only"


def test_player_market_lookup_with_and_without_match(tmp_path) -> None:
    artifact_dir = _market_artifacts(tmp_path)

    matched = lookup_player_market_value(
        {"player": "Premium RB", "position": "RB"},
        artifact_dir=artifact_dir,
    )
    missing = lookup_player_market_value(
        {"player": "Unknown WR", "position": "WR"},
        artifact_dir=artifact_dir,
    )

    assert matched["dp_value"] == "5000"
    assert missing["dp_value"] == NOT_ENOUGH_INFORMATION
    assert missing["match_status"] == "No market match"


def test_market_package_total_excludes_unknown_without_zeroing(tmp_path) -> None:
    artifact_dir = _market_artifacts(tmp_path)
    lookup = build_trade_item_lookup(_board(), _trade_context(), _pick_context())
    option = player_options(lookup)["#1 - Premium RB (RB, SF)"]
    state = add_trade_item(empty_trade_state(), "give", option)

    summary = summarize_trade_package_market(
        state,
        lookup,
        get_assets_text="2026 2.03, 2028 1st, unknown text",
        artifact_dir=artifact_dir,
    )

    totals = {row["side"]: row for row in summary.totals.to_dict("records")}
    assert totals["NWR gives"]["dp_market_total"] == 5000.0
    assert totals["NWR gets"]["dp_market_total"] == 2514.0
    assert totals["NWR gets"]["unknown_assets"] == 1
    assert summary.status == "Market says give side higher"
    assert display_market_package_rows(summary.rows).columns.tolist()[0] == "Side"


def test_market_gap_not_enough_information_when_side_missing() -> None:
    status, difference = classify_market_trade_gap(
        pd.DataFrame(
            [
                {
                    "side": "NWR gives",
                    "dp_market_total": NOT_ENOUGH_INFORMATION,
                    "matched_assets": 0,
                    "unknown_assets": 1,
                },
                {
                    "side": "NWR gets",
                    "dp_market_total": 1490,
                    "matched_assets": 1,
                    "unknown_assets": 0,
                },
            ]
        )
    )

    assert status == NOT_ENOUGH_INFORMATION
    assert difference == NOT_ENOUGH_INFORMATION


def test_market_registry_allows_trading_lab_display_only_usage() -> None:
    usage = PAGE_USAGE["trading_lab"]

    assert usage.enabled
    assert not usage.model_input_allowed
    assert not usage.sort_allowed
    assert "dp_value_1qb" in usage.fields_allowed
    assert validate_market_baseline_registry() == []
