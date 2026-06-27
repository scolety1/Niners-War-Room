from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.development_lab_state_service import (
    VALID_TOOL_KEYS,
    export_tool_state_json,
    import_tool_state,
    list_saved_tool_states,
    load_tool_state,
    preview_import_tool_state,
    reset_tool_state,
    save_tool_state,
)


def test_missing_state_returns_missing_without_creating_file(tmp_path: Path) -> None:
    result = load_tool_state("upcoming_draft_prep", root=tmp_path)

    assert result.status == "MISSING"
    assert result.payload == {}
    assert not result.path.exists()


def test_save_and_load_tool_state_round_trip(tmp_path: Path) -> None:
    save = save_tool_state(
        "future_pick_planning",
        {"manual_future_pick_notes": "2028,1st,acquired,Team A,note"},
        root=tmp_path,
    )
    loaded = load_tool_state("future_pick_planning", root=tmp_path)

    assert save.status == "SAVED"
    assert loaded.status == "LOADED"
    assert loaded.payload["manual_future_pick_notes"].startswith("2028")
    assert loaded.saved_at_utc
    assert "source_truth" in json.loads(save.path.read_text(encoding="utf-8"))["guardrail"]


def test_save_creates_backup_before_overwrite(tmp_path: Path) -> None:
    save_tool_state("roster_weakness_tracker", {"manual_roster_rows": "A,RB"}, root=tmp_path)
    second = save_tool_state(
        "roster_weakness_tracker",
        {"manual_roster_rows": "B,WR"},
        root=tmp_path,
    )

    assert second.backup_path is not None
    assert second.backup_path.exists()
    assert load_tool_state("roster_weakness_tracker", root=tmp_path).payload == {
        "manual_roster_rows": "B,WR"
    }


def test_reset_requires_confirmation_and_backs_up(tmp_path: Path) -> None:
    save_tool_state("keeper_deadline_prep", {"manual_notes": "review"}, root=tmp_path)

    blocked = reset_tool_state("keeper_deadline_prep", confirmed=False, root=tmp_path)

    assert blocked.status == "BLOCKED_CONFIRMATION_REQUIRED"
    assert blocked.path.exists()
    reset = reset_tool_state("keeper_deadline_prep", confirmed=True, root=tmp_path)

    assert reset.status == "RESET"
    assert reset.backup_path is not None
    assert reset.backup_path.exists()
    assert not reset.path.exists()


def test_corrupt_state_is_quarantined_without_silent_reset(tmp_path: Path) -> None:
    path = tmp_path / "drop_deadline_prep.json"
    path.write_text("{not json", encoding="utf-8")

    result = load_tool_state("drop_deadline_prep", root=tmp_path)

    assert result.status == "CORRUPT_QUARANTINED"
    assert result.payload == {}
    assert not path.exists()
    assert list((tmp_path / "corrupt").glob("drop_deadline_prep_*.json"))


def test_export_preview_and_import_require_confirmation(tmp_path: Path) -> None:
    exported = export_tool_state_json(
        "trade_deadline_prep",
        {"manual_notes": "call list"},
    )
    preview = preview_import_tool_state(exported)
    blocked = import_tool_state(
        "trade_deadline_prep",
        exported,
        confirmed=False,
        root=tmp_path,
    )

    assert preview.valid is True
    assert preview.payload == {"manual_notes": "call list"}
    assert blocked.status == "IMPORT_BLOCKED_CONFIRMATION_REQUIRED"
    assert not blocked.path.exists()
    imported = import_tool_state(
        "trade_deadline_prep",
        exported,
        confirmed=True,
        root=tmp_path,
    )

    assert imported.status == "SAVED"
    assert load_tool_state("trade_deadline_prep", root=tmp_path).payload == {
        "manual_notes": "call list"
    }


def test_import_rejects_wrong_tool_key(tmp_path: Path) -> None:
    exported = export_tool_state_json("upcoming_draft_prep", {"setup_notes": "x"})
    result = import_tool_state(
        "future_pick_planning",
        exported,
        confirmed=True,
        root=tmp_path,
    )

    assert result.status == "IMPORT_BLOCKED_TOOL_MISMATCH"
    assert not result.path.exists()


def test_list_saved_tool_states_returns_all_known_tools(tmp_path: Path) -> None:
    save_tool_state("upcoming_draft_prep", {"setup_notes": "saved"}, root=tmp_path)
    states = list_saved_tool_states(root=tmp_path)

    assert [state.tool_key for state in states] == list(VALID_TOOL_KEYS)
    assert {state.status for state in states} == {"LOADED", "MISSING"}


def test_unknown_tool_key_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown Development Lab tool key"):
        save_tool_state("live_draft", {"notes": "nope"}, root=tmp_path)
