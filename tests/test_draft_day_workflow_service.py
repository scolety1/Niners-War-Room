from __future__ import annotations

import pandas as pd
import pytest

from src.services.draft_day_app_v1_service import EXPECTED_ROW_COUNT, load_frozen_board
from src.services.draft_day_workflow_service import (
    DraftWorkflowError,
    assign_player_to_pick,
    available_board_frame,
    current_pick_number,
    display_draft_board_frame,
    display_ranking_frame,
    draft_board_frame,
    empty_workflow_state,
    player_key_from_row,
    remove_pick_assignment,
    undo_last_pick,
    validate_no_duplicate_assignments,
    with_workflow_columns,
    workflow_summary,
)


def _board(rows: int = EXPECTED_ROW_COUNT) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "final_board_rank": index + 1,
                "final_tier": "Tier 1" if index < 3 else "Tier 2",
                "position_rank": index + 1,
                "player": f"Fixture Player {index + 1}",
                "position": "WR" if index % 2 else "RB",
                "nfl_team": "SF",
                "age": "23.4" if index == 0 else "Not enough information",
                "asset_type": "rookie" if index < 10 else "veteran",
                "cross_asset_candidate_rank": index + 1,
                "cross_asset_candidate_value": f"{75 - index:.2f}",
                "candidate_value_band": "Priority candidate" if index < 3 else "Depth",
                "confidence_band": "Medium",
                "available_pool_adp_rank": index + 1,
                "available_pool_adp_range": (
                    "Early 1st equivalent" if index == 0 else "Depth / later"
                ),
                "candidate_key_caveat": "Review-only candidate context",
                "adp_display_only": "10.0" if index == 0 else "Not enough information",
                "adp_range_display_only": (
                    "8.0-12.0" if index == 0 else "Not enough information"
                ),
                "source_label_display_only": "Frozen Board",
                "availability_status": "rookie_pool",
                "final_board_score_visible": f"{90 - index:.2f}",
                "draft_action_display_only": "target" if index < 5 else "watch",
                "warning_severity_display_only": "none",
                "risk_notes": "",
                "needs_manual_review": "false",
                "source_file": r"C:\local\hidden.csv",
            }
            for index in range(rows)
        ]
    )


def _picks() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "overall_pick": index + 1,
                "round": 1,
                "round_pick": index + 1,
                "pick_label": f"1.{index + 1:02d}",
                "current_owner": "Niners" if index == 2 else "Other Team",
                "original_owner": "Original Team",
            }
            for index in range(5)
        ]
    )


def _nwr_picks() -> pd.DataFrame:
    return pd.DataFrame([{"overall_pick": 3, "pick_label": "1.03", "owner": "Niners"}])


def test_player_can_be_marked_picked_and_removed_from_available_view() -> None:
    board = _board()
    picks = _picks()
    state = empty_workflow_state()
    player_key = player_key_from_row(board.iloc[0])

    state = assign_player_to_pick(
        state,
        board=board,
        pick_frame=picks,
        player_key=player_key,
        overall_pick=1,
    )

    available = available_board_frame(board, state)
    workflow = with_workflow_columns(board, state)

    assert workflow.iloc[0]["draft_status"] == "Drafted"
    assert board.iloc[0]["player"] not in set(available["player"])
    assert workflow_summary(board, picks, state).drafted_count == 1
    assert workflow_summary(board, picks, state).available_count == EXPECTED_ROW_COUNT - 1


def test_player_cannot_be_duplicated_without_warning() -> None:
    board = _board()
    picks = _picks()
    state = assign_player_to_pick(
        empty_workflow_state(),
        board=board,
        pick_frame=picks,
        player_key=player_key_from_row(board.iloc[0]),
        overall_pick=1,
    )

    with pytest.raises(DraftWorkflowError, match="already assigned"):
        assign_player_to_pick(
            state,
            board=board,
            pick_frame=picks,
            player_key=player_key_from_row(board.iloc[0]),
            overall_pick=2,
        )


def test_undo_restores_player_availability() -> None:
    board = _board()
    picks = _picks()
    state = assign_player_to_pick(
        empty_workflow_state(),
        board=board,
        pick_frame=picks,
        player_key=player_key_from_row(board.iloc[0]),
        overall_pick=1,
    )

    state, message = undo_last_pick(state)

    assert "Undid" in message
    assert board.iloc[0]["player"] in set(available_board_frame(board, state)["player"])
    assert workflow_summary(board, picks, state).drafted_count == 0


def test_empty_undo_is_clear_noop_message() -> None:
    state, message = undo_last_pick(empty_workflow_state())

    assert state == empty_workflow_state()
    assert message == "No drafted pick to undo."


def test_draft_board_state_updates_and_supports_edit_remove() -> None:
    board = _board()
    picks = _picks()
    state = assign_player_to_pick(
        empty_workflow_state(),
        board=board,
        pick_frame=picks,
        player_key=player_key_from_row(board.iloc[0]),
        overall_pick=3,
    )

    board_rows = draft_board_frame(picks, _nwr_picks(), state)
    display = display_draft_board_frame(board_rows)

    assert board_rows.loc[2, "pick_status"] == "Drafted"
    assert board_rows.loc[2, "player"] == "Fixture Player 1"
    assert board_rows.loc[2, "is_nwr_pick"] == "Yes"
    assert "Player" in display.columns
    assert isinstance(display.loc[2, "Board Rank"], str)
    assert isinstance(display.loc[0, "Player"], str)

    state, message = remove_pick_assignment(state, 3)

    assert message == "Removed the selected pick assignment."
    assert not validate_no_duplicate_assignments(state)
    assert draft_board_frame(picks, _nwr_picks(), state).loc[2, "player"] == ""


def test_frozen_board_still_loads_sixty_six_rows() -> None:
    bundle = load_frozen_board()

    assert bundle.loaded
    assert bundle.row_count == EXPECTED_ROW_COUNT


def test_display_frames_do_not_expose_internal_or_hidden_columns() -> None:
    board = _board(2)
    workflow = with_workflow_columns(board, empty_workflow_state())
    display = display_ranking_frame(workflow)

    assert "source_file" not in display.columns
    assert not any("hidden" in column.lower() for column in display.columns)
    assert "Final Board Rank" in display.columns
    assert "Draft Status" not in display.columns


def test_live_draft_table_prioritizes_practical_visible_columns() -> None:
    board = _board(2)
    workflow = with_workflow_columns(board, empty_workflow_state())
    display = display_ranking_frame(workflow, current_pick=5)

    assert list(display.columns[:13]) == [
        "Candidate Rank (Review-Only)",
        "Final Board Rank",
        "Player",
        "Pos",
        "NFL Team",
        "Age",
        "Position Rank",
        "Candidate Band",
        "Candidate Value (Review-Only)",
        "Confidence",
        "ADP (Display-Only)",
        "Available-Pool ADP Range (Display-Only)",
        "Current Pick Value (Display-Only)",
    ]
    assert "Visible Score (Mixed Basis)" not in display.columns
    assert "Board Availability" not in display.columns
    assert "Draft Action (Display-Only)" not in display.columns
    assert display.loc[0, "Current Pick Value (Display-Only)"] == "Value"


def test_drafted_context_only_appears_when_toggle_context_is_requested() -> None:
    board = _board(2)
    workflow = with_workflow_columns(board, empty_workflow_state())

    default_display = display_ranking_frame(workflow)
    expanded_display = display_ranking_frame(workflow, show_drafted_context=True)

    assert "Draft Status" not in default_display.columns
    assert "Assigned Pick" not in default_display.columns
    assert "Draft Status" in expanded_display.columns
    assert "Assigned Pick" in expanded_display.columns


def test_current_pick_advances_and_recomputes_after_remove_or_undo() -> None:
    board = _board()
    picks = _picks()
    first_player_key = player_key_from_row(board.iloc[0])
    second_player_key = player_key_from_row(board.iloc[1])

    state = assign_player_to_pick(
        empty_workflow_state(),
        board=board,
        pick_frame=picks,
        player_key=first_player_key,
        overall_pick=1,
    )
    assert current_pick_number(picks, state) == 2

    state = assign_player_to_pick(
        state,
        board=board,
        pick_frame=picks,
        player_key=second_player_key,
        overall_pick=2,
    )
    assert current_pick_number(picks, state) == 3

    state, _message = remove_pick_assignment(state, 1)
    assert current_pick_number(picks, state) == 1

    state, _message = undo_last_pick(state)
    assert current_pick_number(picks, state) == 1
