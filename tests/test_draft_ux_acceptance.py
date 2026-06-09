from __future__ import annotations

from src.services.draft_state_service import (
    apply_draft_status_to_rankings,
    available_players_after_picks,
    best_options_at_pick,
    create_empty_draft_state,
    is_my_turn,
    mark_player_drafted,
    reset_mock,
    undo_pick,
)
from src.services.draft_ux_service import DRAFT_TOTAL_PICKS, filter_rankings_rows
from src.services.mock_draft_storage_service import load_mock_draft, save_mock_draft


def _pick_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    my_picks = {4, 14, 24, 34, 44}
    for overall_pick in range(1, DRAFT_TOTAL_PICKS + 1):
        round_number = ((overall_pick - 1) // 10) + 1
        round_pick = ((overall_pick - 1) % 10) + 1
        rows.append(
            {
                "overall_pick": overall_pick,
                "round": round_number,
                "round_pick": round_pick,
                "pick_label": f"{round_number}.{round_pick:02d}",
                "current_owner": "Niners" if overall_pick in my_picks else "Other",
                "original_owner": "Niners" if overall_pick in my_picks else "Other",
                "is_my_pick": overall_pick in my_picks,
            }
        )
    return rows


def _available_rows(count: int = 55) -> list[dict[str, object]]:
    positions = ("WR", "RB", "QB", "TE")
    rows: list[dict[str, object]] = []
    for index in range(1, count + 1):
        position = positions[(index - 1) % len(positions)]
        rows.append(
            {
                "overall_rank": index,
                "asset_id": f"rookie:player_{index:03d}",
                "player": f"Player {index:03d}",
                "position": position,
                "nfl_team": "Rookie Pool",
                "asset_type": "rookie",
                "why_available": "Rookie pool entrant.",
                "draft_status": "available",
                "stats_model_value": 101.0 - index,
                "model_value": 101.0 - index,
                "market_edge": 0.0,
                "confidence": 90.0,
                "warning": "",
            }
        )
    return rows


def test_live_draft_acceptance_flow_for_rankings_and_draft_board(tmp_path) -> None:
    rows = _available_rows()
    state = create_empty_draft_state(pick_rows=_pick_rows(), available_rows=rows)

    assert best_options_at_pick(state, limit=1)[0].player == "Player 001"

    state = mark_player_drafted(state, "rookie:player_001")
    annotated = apply_draft_status_to_rankings(rows, state)
    available_rankings = filter_rankings_rows(annotated, statuses={"available"})

    assert "rookie:player_001" not in {str(row["asset_id"]) for row in available_rankings}
    assert best_options_at_pick(state, limit=1)[0].player == "Player 002"

    state = mark_player_drafted(state, "rookie:player_002")
    state = mark_player_drafted(state, "rookie:player_003")

    assert state.current_pick == 4
    assert is_my_turn(state) is True

    state = undo_pick(state)

    assert state.current_pick == 3
    assert any(row.asset_id == "rookie:player_003" for row in available_players_after_picks(state))

    state = mark_player_drafted(state, "rookie:player_003")
    while state.current_pick is not None:
        next_asset = best_options_at_pick(state, limit=1)[0].asset_id
        state = mark_player_drafted(state, next_asset)

    assert state.current_pick is None
    assert len(state.drafted_players) == DRAFT_TOTAL_PICKS
    assert len(available_players_after_picks(state)) == 5

    saved_path = save_mock_draft(
        state,
        mock_name="Full 50 Pick Acceptance",
        active_data_pack="acceptance-pack",
        root=tmp_path,
    )
    loaded = load_mock_draft(
        saved_path,
        base_state=create_empty_draft_state(pick_rows=_pick_rows(), available_rows=rows),
    )

    assert len(loaded.drafted_players) == DRAFT_TOTAL_PICKS
    assert loaded.current_pick is None

    reset = reset_mock(loaded)

    assert reset.current_pick == 1
    assert reset.drafted_players == ()
    assert len(available_players_after_picks(reset)) == len(rows)
