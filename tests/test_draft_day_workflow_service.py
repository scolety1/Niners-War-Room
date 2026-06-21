from __future__ import annotations

import pandas as pd
import pytest

from src.services.draft_day_app_v1_service import EXPECTED_ROW_COUNT, load_frozen_board
from src.services.draft_day_workflow_service import (
    DraftWorkflowError,
    assign_player_to_pick,
    available_board_frame,
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
                "asset_type": "rookie" if index < 10 else "veteran",
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
    assert "Draft Status" in display.columns
