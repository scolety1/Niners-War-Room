from __future__ import annotations

from src.services.draft_service import build_draft_room

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_draft_room_joins_future_picks_to_snapshot_values() -> None:
    board = build_draft_room(SAMPLE_PACK)

    assert board.snapshot_date == "2026-08-01"
    assert board.teams == ["Niners"]
    assert board.certainties == ["known", "projected"]
    assert board.pick_rows[0] == {
        "pick": "2026 1.04",
        "current_team": "Niners",
        "original_team": "Niners",
        "pick_year": 2026,
        "round": 1,
        "overall_pick": 4,
        "certainty": "known",
        "base_value": 630.0,
        "snapshot_value": 630.0,
        "future_discount": 1.0,
        "certainty_factor": 1.0,
        "bucket": "round-1",
    }


def test_draft_room_team_totals_use_snapshot_values() -> None:
    board = build_draft_room(SAMPLE_PACK)

    assert board.team_rows == [
        {
            "team": "Niners",
            "picks": 3,
            "snapshot_value": 1283.6,
            "highest_pick": "2026 1.04",
        }
    ]
