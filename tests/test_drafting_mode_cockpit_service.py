from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd

from src.services.draft_day_runtime_state_service import empty_runtime_state, update_workflow_state
from src.services.draft_day_workflow_service import player_key_from_row
from src.services.drafting_mode_cockpit_service import (
    DEFAULT_SORT_LABEL,
    build_cockpit_board,
    build_cockpit_summary,
    compare_decision_rows,
    decision_panel_rows,
    display_cockpit_board,
    player_options,
    recent_trade_rows,
    record_cockpit_trade,
    selected_player_row,
    tier_count_rows,
)


def _board() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": "p1",
                "final_board_rank": 11,
                "dynasty_asset_rank": 3,
                "dynasty_asset_tier": "Tier 2: depth options",
                "player": "Later Market Player",
                "position": "WR",
                "nfl_team": "SF",
                "age": "24",
                "available_pool_adp_rank": 1,
                "why_draft": "Useful profile",
                "main_risk": "Depth chart role needs review",
                "market_sanity_label": "Aligned",
                "outcome_applicable_summary": "WR context",
                "source_group": "Core",
                "source_label_display_only": "Fixture",
            },
            {
                "player_id": "p2",
                "final_board_rank": 12,
                "dynasty_asset_rank": 1,
                "dynasty_asset_tier": "Tier 1A: core on-clock candidates",
                "player": "Best NWR Player",
                "position": "RB",
                "nfl_team": "DAL",
                "age": "22",
                "available_pool_adp_rank": 5,
                "why_draft": "Top tier profile",
                "main_risk": "None",
                "market_sanity_label": "No market match",
                "outcome_applicable_summary": "RB context",
                "source_group": "Core",
                "source_label_display_only": "Fixture",
            },
            {
                "player_id": "p3",
                "final_board_rank": 13,
                "dynasty_asset_rank": 2,
                "dynasty_asset_tier": "Tier 1B: strong alternatives",
                "player": "Drafted Player",
                "position": "TE",
                "nfl_team": "KC",
                "age": "25",
                "available_pool_adp_rank": 2,
                "why_draft": "Drafted already",
                "main_risk": "None",
                "market_sanity_label": "Aligned",
                "outcome_applicable_summary": "TE context",
                "source_group": "Core",
                "source_label_display_only": "Fixture",
            },
            {
                "player_id": "p4",
                "final_board_rank": 14,
                "dynasty_asset_rank": 4,
                "dynasty_asset_tier": "Tier 3: bench options",
                "player": "Default Hidden Kicker",
                "position": "K",
                "nfl_team": "BAL",
                "age": "",
                "available_pool_adp_rank": 3,
                "why_draft": "Specialist",
                "main_risk": "Specialist",
                "market_sanity_label": "Aligned",
                "outcome_applicable_summary": "Not enough information",
                "source_group": "Core",
                "source_label_display_only": "Fixture",
            },
        ]
    )


def _picks() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "overall_pick": 1,
                "pick_label": "1.01",
                "current_owner": "Other",
                "original_owner": "Other",
            },
            {
                "overall_pick": 4,
                "pick_label": "1.04",
                "current_owner": "NWR",
                "original_owner": "NWR",
            },
            {
                "overall_pick": 13,
                "pick_label": "2.03",
                "current_owner": "Team B",
                "original_owner": "Team B",
            },
        ]
    )


def _drafted_state() -> dict[str, object]:
    state = empty_runtime_state(mode="live")
    state["workflow_state"] = {
        "assignments": [
            {
                "player_key": player_key_from_row(_board().iloc[2]),
                "overall_pick": 1,
                "pick_label": "1.01",
                "player": "Drafted Player",
                "position": "TE",
            }
        ]
    }
    return state


def test_cockpit_summary_builds_empty_state() -> None:
    summary = build_cockpit_summary(
        board_frame=_board(),
        pick_frame=_picks(),
        runtime_state=empty_runtime_state(mode="live"),
    )

    assert summary.current_pick == "1.01"
    assert summary.drafted_count == 0
    assert summary.trade_count == 0
    assert summary.available_count == 4


def test_cockpit_summary_reads_runtime_state_counts(tmp_path: Path) -> None:
    state = update_workflow_state(
        empty_runtime_state(mode="live"),
        _drafted_state()["workflow_state"],
        event_type="pick_assigned",
        event_detail={"player": "Drafted Player", "pick_label": "1.01"},
        root=tmp_path,
    )
    state = record_cockpit_trade(
        state,
        team_a="NWR",
        team_a_sends="2026 1.04",
        team_b="Team B",
        team_b_sends="2026 2.03",
        notes="fixture",
        root=tmp_path,
    )

    summary = build_cockpit_summary(
        board_frame=_board(),
        pick_frame=_picks(),
        runtime_state=state,
    )

    assert summary.drafted_count == 1
    assert summary.trade_count == 1
    assert summary.event_count >= 2


def test_cockpit_board_hides_drafted_and_k_dst_by_default() -> None:
    board = build_cockpit_board(_board(), _drafted_state())

    assert "Drafted Player" not in set(board["player"])
    assert "Default Hidden Kicker" not in set(board["player"])
    assert list(board["player"]) == ["Best NWR Player", "Later Market Player"]


def test_cockpit_board_can_show_k_dst_when_requested() -> None:
    board = build_cockpit_board(_board(), empty_runtime_state(mode="live"), show_k_dst=True)

    assert "Default Hidden Kicker" in set(board["player"])


def test_market_sort_label_falls_back_to_nwr_default_sort() -> None:
    market_requested = build_cockpit_board(
        _board(),
        empty_runtime_state(mode="live"),
        sort_label="Available-Pool ADP Rank",
    )
    default_sorted = build_cockpit_board(
        _board(),
        empty_runtime_state(mode="live"),
        sort_label=DEFAULT_SORT_LABEL,
    )

    assert list(market_requested["player"]) == list(default_sorted["player"])
    assert market_requested.iloc[0]["player"] == "Best NWR Player"


def test_tier_counts_and_display_columns_are_available() -> None:
    board = build_cockpit_board(_board(), _drafted_state())
    counts = tier_count_rows(board)
    display = display_cockpit_board(board)

    assert {"Tier Availability": "Tier 1A - 1 available", "Available": "1"} in counts
    assert "NWR Draft Rank" in display.columns
    assert "Frozen Baseline Rank" in display.columns


def test_tier_counts_use_friendly_review_needed_label() -> None:
    frame = pd.DataFrame([{"final_tier": ""}, {"final_tier": "Review Needed"}])

    assert tier_count_rows(frame) == [
        {"Tier Availability": "Review Needed - 2", "Available": "2"}
    ]


def test_decision_panel_handles_no_selection_and_valid_player() -> None:
    empty_rows = decision_panel_rows(None)
    player = _board().iloc[1].to_dict()
    selected_rows = decision_panel_rows(player)

    assert "Choose a player from the selector" in empty_rows[0]["value"]
    assert any(
        row["field"] == "Player" and row["value"] == "Best NWR Player"
        for row in selected_rows
    )
    assert any(row["field"] == "Market sanity" for row in selected_rows)
    assert any(row["field"] == "Display-only guardrail" for row in selected_rows)


def test_player_selection_and_compare_summary_paths() -> None:
    board = build_cockpit_board(_board(), empty_runtime_state(mode="live"))
    options = player_options(board)
    selected = selected_player_row(board, next(iter(options.values())))
    comparison = selected_player_row(board, list(options.values())[1])

    assert selected is not None
    assert comparison is not None
    assert compare_decision_rows(selected, None)[0]["field"] == "Compare summary"
    assert {row["field"] for row in compare_decision_rows(selected, comparison)} >= {
        "Lean",
        "Market note",
    }


def test_record_cockpit_trade_uses_existing_schema_and_updates_picks(tmp_path: Path) -> None:
    state = record_cockpit_trade(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_a_sends="2026 1.04",
        team_b="Team B",
        team_b_sends="2026 2.03, 2028 1st",
        notes="required smoke fixture",
        root=tmp_path,
    )
    trade = state["trade_events"][0]

    assert trade["team_a"] == "NWR"
    assert trade["team_b"] == "Team B"
    assert trade["status"] == "active"
    assert state["pick_ownership_overrides"]["1.04"]["new_owner"] == "Team B"
    assert state["pick_ownership_overrides"]["2.03"]["new_owner"] == "NWR"
    assert trade["future_picks"] == ["2028 1st"]
    assert recent_trade_rows(state).iloc[0]["team_a"] == "NWR"


def test_cockpit_service_does_not_create_rank_model_or_source_truth_fields(
    tmp_path: Path,
) -> None:
    state = record_cockpit_trade(
        empty_runtime_state(mode="live"),
        team_a="NWR",
        team_a_sends="2026 1.04",
        team_b="Team B",
        team_b_sends="2026 2.03",
        notes="guardrail",
        root=tmp_path,
    )
    forbidden = {
        "final_board_rank_override",
        "dynasty_rank_override",
        "tier_assignment_override",
        "model_input",
        "hidden_sort",
        "source_truth_replacement",
        "latest_candidate",
        "latest_approved",
    }

    assert forbidden.isdisjoint(state)


def test_no_shared_raw_or_runtime_files_are_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], text=True)

    assert "NWR_SHARED_DATA" not in tracked
    assert "draft_runtime_state" not in tracked
    assert "_draft_log.json" not in tracked
