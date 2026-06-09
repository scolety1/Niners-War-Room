from __future__ import annotations

import json

import pytest

from src.services.draft_state_service import (
    create_empty_draft_state,
    mark_player_drafted,
)
from src.services.mock_draft_storage_service import (
    MockDraftValidationError,
    clear_mock_draft,
    duplicate_mock_draft,
    list_mock_drafts,
    load_mock_draft,
    save_mock_draft,
)


def _pick_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for overall_pick in range(1, 51):
        round_number = ((overall_pick - 1) // 10) + 1
        round_pick = ((overall_pick - 1) % 10) + 1
        rows.append(
            {
                "overall_pick": overall_pick,
                "round": round_number,
                "round_pick": round_pick,
                "pick_label": f"{round_number}.{round_pick:02d}",
                "current_owner": "Niners" if overall_pick == 4 else "Other",
                "original_owner": "Niners" if overall_pick == 4 else "Other",
                "is_my_pick": overall_pick == 4,
            }
        )
    return rows


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
            "overall_rank": 2,
        },
    ]


def _state():
    return create_empty_draft_state(
        pick_rows=_pick_rows(),
        available_rows=_available_rows(),
    )


def test_save_and_load_mock_draft_round_trips_without_pack_mutation(tmp_path) -> None:
    state = mark_player_drafted(_state(), "rookie:wr_1", overall_pick=4)

    path = save_mock_draft(
        state,
        mock_name="Aggressive WR Start",
        active_data_pack="sample_data/pack",
        root=tmp_path,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    loaded = load_mock_draft(path, base_state=_state())

    assert path.parent == tmp_path
    assert payload["active_data_pack"] == "sample_data/pack"
    assert payload["mock_name"] == "Aggressive WR Start"
    assert payload["drafted_players"][0]["asset_id"] == "rookie:wr_1"
    assert loaded.drafted_players[0].player == "Alpha WR"
    assert loaded.drafted_players[0].pick.overall_pick == 4
    assert [row.player for row in loaded.available_players] == ["Bellcow RB"]


def test_list_duplicate_and_clear_mock_drafts(tmp_path) -> None:
    state = mark_player_drafted(_state(), "rookie:wr_1", overall_pick=4)
    path = save_mock_draft(
        state,
        mock_name="Base Mock",
        active_data_pack="sample_data/pack",
        root=tmp_path,
    )

    duplicate = duplicate_mock_draft(path, new_mock_name="Base Mock Copy", root=tmp_path)
    summaries = list_mock_drafts(tmp_path)

    assert {row.mock_name for row in summaries} == {"Base Mock", "Base Mock Copy"}
    assert duplicate.exists()

    clear_mock_draft(duplicate)

    assert not duplicate.exists()
    assert path.exists()


def test_invalid_mock_files_do_not_load_or_crash_listing(tmp_path) -> None:
    invalid = tmp_path / "bad.json"
    invalid.write_text("{not-json", encoding="utf-8")
    wrong_schema = tmp_path / "wrong.json"
    wrong_schema.write_text(
        json.dumps(
            {
                "schema_version": 999,
                "mock_name": "Wrong",
                "created_at": "now",
                "active_data_pack": "pack",
                "picks": [],
                "drafted_players": [],
            }
        ),
        encoding="utf-8",
    )

    assert list_mock_drafts(tmp_path) == []
    with pytest.raises(MockDraftValidationError, match="valid JSON"):
        load_mock_draft(invalid, base_state=_state())
    with pytest.raises(MockDraftValidationError, match="Unsupported"):
        load_mock_draft(wrong_schema, base_state=_state())


def test_bad_mock_player_reference_is_rejected(tmp_path) -> None:
    path = tmp_path / "bad-player.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "mock_name": "Bad Player",
                "created_at": "now",
                "active_data_pack": "pack",
                "picks": [],
                "drafted_players": [{"overall_pick": 1, "asset_id": "missing"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(MockDraftValidationError, match="not available"):
        load_mock_draft(path, base_state=_state())
