from __future__ import annotations

import pandas as pd

from src.services.draft_day_trade_lab_service import (
    NOT_ENOUGH_INFORMATION,
    add_trade_item,
    build_trade_item_lookup,
    clear_trade_state,
    display_package_summary,
    display_trade_item_rows,
    empty_trade_state,
    package_summary_rows,
    pick_context_options,
    player_key,
    player_options,
    remove_trade_item,
    review_trade_package,
    trade_item_rows,
)


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
