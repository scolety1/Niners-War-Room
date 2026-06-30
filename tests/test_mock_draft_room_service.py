from __future__ import annotations

from src.services.draft_day_runtime_state_service import (
    empty_runtime_state,
    load_runtime_state,
    record_trade_event,
)
from src.services.mock_draft_room_service import (
    DEFAULT_MOCK_DRAFT_ID,
    create_mock_draft_session,
    delete_mock_draft_session,
    duplicate_mock_draft_session,
    load_mock_draft_sessions,
    mock_draft_manifest_health,
    mock_manifest_path,
    rename_mock_draft_session,
)


def test_mock_draft_sessions_default_without_writing_manifest(tmp_path) -> None:
    sessions = load_mock_draft_sessions(tmp_path)
    health = mock_draft_manifest_health(tmp_path)

    assert len(sessions) == 1
    assert sessions[0].draft_id == DEFAULT_MOCK_DRAFT_ID
    assert health.status == "MISSING_MANIFEST_USING_DEFAULT"
    assert "does not affect live Draft Cockpit state" in health.message
    assert not mock_manifest_path(tmp_path).exists()


def test_mock_draft_manifest_create_rename_delete(tmp_path) -> None:
    sessions = create_mock_draft_session("  Rookie run  ", root=tmp_path)
    created = sessions[-1]

    assert created.name == "Rookie run"
    assert mock_manifest_path(tmp_path).exists()

    renamed = rename_mock_draft_session(created.draft_id, "Round 1 chaos", root=tmp_path)
    assert any(
        session.draft_id == created.draft_id and session.name == "Round 1 chaos"
        for session in renamed
    )

    remaining = delete_mock_draft_session(created.draft_id, root=tmp_path)
    assert len(remaining) == 1
    assert remaining[0].draft_id == DEFAULT_MOCK_DRAFT_ID


def test_mock_duplicate_preserves_trade_state_without_touching_live(tmp_path) -> None:
    sessions = create_mock_draft_session("Trade practice", root=tmp_path)
    source = sessions[-1]
    source_state = empty_runtime_state(mode="mock", draft_id=source.draft_id)
    record_trade_event(
        source_state,
        team_a="NWR",
        team_b="Other Team",
        team_a_sends="2026 1.04",
        team_b_sends="2028 1st + 2026 2.03",
        notes="Mock trade smoke",
        root=tmp_path,
    )

    duplicated = duplicate_mock_draft_session(source.draft_id, "Trade practice copy", root=tmp_path)
    copy_session = duplicated[-1]
    copied_state = load_runtime_state(mode="mock", draft_id=copy_session.draft_id, root=tmp_path)
    live_state = load_runtime_state(mode="live", root=tmp_path)

    assert copied_state["mode"] == "mock"
    assert copied_state["draft_id"] == copy_session.draft_id
    assert copied_state["trade_events"]
    assert copied_state["trade_events"][0]["team_a_sends"] == "2026 1.04"
    assert "2028 1st" in copied_state["trade_events"][0]["future_picks"]
    assert copied_state["pick_ownership_overrides"]["1.04"]["new_owner"] == "Other Team"
    assert copied_state["pick_ownership_overrides"]["2.03"]["new_owner"] == "NWR"
    assert live_state["trade_events"] == []
    assert live_state["pick_ownership_overrides"] == {}


def test_mock_manifest_health_warns_on_unreadable_manifest(tmp_path) -> None:
    mock_manifest_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    mock_manifest_path(tmp_path).write_text("{not-json", encoding="utf-8")

    health = mock_draft_manifest_health(tmp_path)
    sessions = load_mock_draft_sessions(tmp_path)

    assert health.status == "UNREADABLE_MANIFEST_USING_DEFAULT"
    assert "using the default mock session" in health.message
    assert sessions[0].draft_id == DEFAULT_MOCK_DRAFT_ID
