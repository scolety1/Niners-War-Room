from __future__ import annotations

import pytest

from src.services.draft_state_service import (
    available_players_after_picks,
    best_option_rows_at_pick,
    best_options_at_pick,
    best_remaining_by_position,
    create_empty_draft_state,
    current_draft_pick,
    draft_board_export_rows,
    draft_pick_grid_cells,
    draft_pick_grid_rows,
    draft_progress_summary,
    drafted_player_at_pick,
    is_my_turn,
    mark_player_drafted,
    pick_guardrail_status,
    recent_drafted_players,
    remaining_pool_export_rows,
    replace_drafted_player_at_pick,
    reset_mock,
    search_available_players,
    undo_pick,
)
from src.services.draft_ux_service import DRAFT_TOTAL_PICKS, build_draft_ux_contract


def _available_rows() -> list[dict[str, object]]:
    return [
        {
            "asset_id": "rookie:wr_1",
            "player": "Alpha WR",
            "position": "WR",
            "nfl_team": "Rookie Pool",
            "asset_type": "Rookie",
            "stats_model_value": 91.0,
            "market_edge": 4.0,
            "confidence": 88.0,
            "warning": "",
            "overall_rank": 1,
        },
        {
            "asset_id": "rookie:rb_1",
            "player": "Bellcow RB",
            "position": "RB",
            "nfl_team": "Rookie Pool",
            "asset_type": "Rookie",
            "stats_model_value": 87.0,
            "market_edge": 2.0,
            "confidence": 82.0,
            "warning": "",
            "overall_rank": 2,
        },
        {
            "asset_id": "vet:wr_2",
            "player": "Released WR",
            "position": "WR",
            "nfl_team": "FA",
            "asset_type": "Released Veteran",
            "stats_model_value": 74.0,
            "market_edge": -1.0,
            "confidence": 78.0,
            "warning": "",
            "overall_rank": 3,
        },
    ]


def _pick_rows(my_picks: set[int] | None = None) -> list[dict[str, object]]:
    my_picks = my_picks or set()
    rows: list[dict[str, object]] = []
    for overall_pick in range(1, DRAFT_TOTAL_PICKS + 1):
        round_number = ((overall_pick - 1) // 10) + 1
        round_pick = ((overall_pick - 1) % 10) + 1
        rows.append(
            {
                "overall_pick": overall_pick,
                "round": round_number,
                "round_pick": round_pick,
                "pick_label": f"{round_number}.{round_pick:02d}",
                "current_owner": "Niners" if overall_pick in my_picks else "Other Team",
                "original_owner": "Niners" if overall_pick in my_picks else "Other Team",
                "is_my_pick": overall_pick in my_picks,
            }
        )
    return rows


def test_create_empty_draft_state_builds_fifty_picks_and_available_pool() -> None:
    contract = build_draft_ux_contract("sample_data/2026_pre_declaration")
    state = create_empty_draft_state(
        pick_rows=contract.pick_grid_rows,
        available_rows=_available_rows(),
    )

    assert len(state.picks) == DRAFT_TOTAL_PICKS
    assert state.current_pick == 1
    assert len(state.available_players) == 3
    assert state.available_players[0].player == "Alpha WR"
    assert state.my_pick_numbers


def test_current_pick_detection_knows_when_it_is_my_turn() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({1}),
        available_rows=_available_rows(),
    )

    assert current_draft_pick(state).overall_pick == 1
    assert is_my_turn(state) is True

    state = mark_player_drafted(state, "rookie:wr_1")

    assert current_draft_pick(state).overall_pick == 2
    assert is_my_turn(state) is False


def test_draft_progress_summary_tracks_next_my_pick_and_counts() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({4}),
        available_rows=_available_rows(),
    )
    state = mark_player_drafted(state, "rookie:wr_1")

    summary = draft_progress_summary(state)

    assert summary.current_pick_label == "1.02"
    assert summary.next_my_pick_label == "1.04"
    assert summary.picks_until_my_pick == 2
    assert summary.drafted_count == 1
    assert summary.available_count == 2
    assert summary.total_picks == 50


def test_draft_pick_grid_cells_create_five_by_ten_live_board() -> None:
    contract = build_draft_ux_contract("sample_data/2026_pre_declaration")
    state = create_empty_draft_state(
        pick_rows=contract.pick_grid_rows,
        available_rows=_available_rows(),
    )

    cells = draft_pick_grid_cells(state, selected_pick=4)
    grid_rows = draft_pick_grid_rows(state, selected_pick=4)

    assert len(cells) == 50
    assert {cell.round for cell in cells} == {1, 2, 3, 4, 5}
    assert all(1 <= cell.round_pick <= 10 for cell in cells)
    assert cells[0].status_label == "On clock"
    assert cells[3].is_selected_pick is True
    assert "[MY]" in cells[3].button_label
    assert len(grid_rows) == 50
    assert grid_rows[3]["selected"] is True


def test_draft_pick_grid_cells_show_drafted_player_and_position() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1")

    first_cell = draft_pick_grid_cells(state)[0]

    assert first_cell.status_label == "Drafted"
    assert first_cell.drafted_player == "Alpha WR"
    assert first_cell.drafted_position == "WR"
    assert "Alpha WR (WR)" in first_cell.button_label


def test_export_rows_create_draft_board_and_remaining_pool_backups() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({4}),
        available_rows=_available_rows(),
    )
    state = mark_player_drafted(state, "rookie:wr_1", overall_pick=4)

    board_rows = draft_board_export_rows(state)
    pool_rows = remaining_pool_export_rows(state)

    assert len(board_rows) == 50
    assert board_rows[3]["pick"] == "1.04"
    assert board_rows[3]["status"] == "drafted"
    assert board_rows[3]["player"] == "Alpha WR"
    assert "rookie:wr_1" not in {row["asset_id"] for row in pool_rows}
    assert [row["player"] for row in pool_rows] == ["Bellcow RB", "Released WR"]


def test_mark_player_drafted_advances_current_pick_and_removes_available_player() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())

    state = mark_player_drafted(state, "rookie:wr_1")

    assert state.current_pick == 2
    assert len(state.drafted_players) == 1
    assert state.drafted_players[0].pick.overall_pick == 1
    assert state.drafted_players[0].player == "Alpha WR"
    assert [row.asset_id for row in available_players_after_picks(state)] == [
        "rookie:rb_1",
        "vet:wr_2",
    ]


def test_mark_player_drafted_can_target_specific_pick() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())

    state = mark_player_drafted(state, "rookie:rb_1", overall_pick=7)

    assert state.current_pick == 1
    assert state.drafted_players[0].pick.overall_pick == 7
    assert state.drafted_players[0].player == "Bellcow RB"


def test_undo_pick_restores_last_drafted_player() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1")
    state = mark_player_drafted(state, "rookie:rb_1")

    state = undo_pick(state)

    assert state.current_pick == 2
    assert [row.player for row in state.drafted_players] == ["Alpha WR"]
    assert [row.player for row in state.available_players] == ["Bellcow RB", "Released WR"]


def test_reset_mock_restores_available_players_and_first_pick() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1")
    state = mark_player_drafted(state, "rookie:rb_1")

    state = reset_mock(state)

    assert state.current_pick == 1
    assert state.drafted_players == ()
    assert [row.player for row in state.available_players] == [
        "Alpha WR",
        "Bellcow RB",
        "Released WR",
    ]


def test_best_options_at_pick_returns_remaining_sorted_options() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1")

    options = best_options_at_pick(state, limit=2)

    assert [row.player for row in options] == ["Bellcow RB", "Released WR"]


def test_search_available_players_filters_by_name_position_or_asset_type() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())

    assert [row.player for row in search_available_players(state, "alpha")] == ["Alpha WR"]
    assert [row.player for row in search_available_players(state, "wr rookie")] == ["Alpha WR"]
    assert [row.player for row in search_available_players(state, "released")] == [
        "Released WR"
    ]


def test_best_remaining_by_position_returns_top_remaining_by_position() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1")

    rows = best_remaining_by_position(state, limit_per_position=2)

    assert [(row.position, row.player) for row in rows] == [
        ("RB", "Bellcow RB"),
        ("WR", "Released WR"),
    ]


def test_recent_drafted_players_returns_latest_picks_in_pick_order() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1", overall_pick=4)
    state = mark_player_drafted(state, "rookie:rb_1", overall_pick=7)

    recent = recent_drafted_players(state)

    assert [(row.pick_label, row.player, row.position) for row in recent] == [
        ("1.04", "Alpha WR", "WR"),
        ("1.07", "Bellcow RB", "RB"),
    ]


def test_best_option_rows_include_decision_fields_and_review_warning() -> None:
    rows = [
        {
            **_available_rows()[0],
            "do_not_draft_before_pick": 4,
        },
        {
            **_available_rows()[1],
            "do_not_draft_before_pick": 1,
        },
    ]
    state = create_empty_draft_state(
        pick_rows=_pick_rows({1}),
        available_rows=rows,
    )

    options = best_option_rows_at_pick(state, overall_pick=1, review_only=True)

    assert options[0].player == "Alpha WR"
    assert options[0].position == "WR"
    assert options[0].asset_type == "Rookie"
    assert options[0].stats_model_value == 91.0
    assert options[0].confidence == 88.0
    assert options[0].warning == "Review-only: calibration blocked"
    assert options[0].reach_value_label == "Reach"


def test_best_option_rows_filter_out_drafted_players() -> None:
    state = create_empty_draft_state(
        pick_rows=_pick_rows({1}),
        available_rows=_available_rows(),
    )

    state = mark_player_drafted(state, "rookie:wr_1")
    options = best_option_rows_at_pick(state, overall_pick=2)

    assert [row.player for row in options] == ["Bellcow RB", "Released WR"]


def test_draft_state_rejects_duplicate_player_or_filled_pick() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1")

    with pytest.raises(ValueError, match="already drafted"):
        mark_player_drafted(state, "rookie:wr_1", overall_pick=2)
    with pytest.raises(ValueError, match="already has"):
        mark_player_drafted(state, "rookie:rb_1", overall_pick=1)


def test_replace_drafted_player_at_pick_edits_prior_pick_and_restores_old_player() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1", overall_pick=1)
    state = mark_player_drafted(state, "rookie:rb_1", overall_pick=2)

    state = replace_drafted_player_at_pick(state, "vet:wr_2", overall_pick=1)

    assert drafted_player_at_pick(state, 1).player == "Released WR"
    assert [row.player for row in state.drafted_players] == ["Released WR", "Bellcow RB"]
    assert [row.player for row in state.available_players] == ["Alpha WR"]
    assert state.current_pick == 3


def test_replace_drafted_player_rejects_player_already_drafted_elsewhere() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1", overall_pick=1)
    state = mark_player_drafted(state, "rookie:rb_1", overall_pick=2)

    with pytest.raises(ValueError, match="already drafted"):
        replace_drafted_player_at_pick(state, "rookie:rb_1", overall_pick=1)


def test_pick_guardrail_status_marks_prior_future_and_edit_modes() -> None:
    state = create_empty_draft_state(available_rows=_available_rows())
    state = mark_player_drafted(state, "rookie:wr_1", overall_pick=1)

    edit_status = pick_guardrail_status(state, 1)
    current_status = pick_guardrail_status(state, 2)
    future_status = pick_guardrail_status(state, 7)

    assert edit_status.edit_mode is True
    assert edit_status.is_filled_pick is True
    assert "Edit mode" in edit_status.warning
    assert current_status.is_current_pick is True
    assert current_status.warning == ""
    assert future_status.is_future_pick is True
    assert "ahead of the current pick" in future_status.warning
