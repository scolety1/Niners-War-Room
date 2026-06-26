from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_live_draft_page_is_the_command_center() -> None:
    text = _text("app/pages/21_live_draft_room_v1.py")

    assert "## LIVE DRAFT" in text
    assert "Draft room command center" in text
    assert "Your Team / runtime rail" in text
    assert "Current pick" in text
    assert "On-clock team" in text
    assert "Drafted" in text
    assert "Trades" in text
    assert "Autosave" in text
    assert "build_cockpit_summary" in text
    assert "render_draft_workflow" in text


def test_live_draft_page_keeps_trade_and_runtime_guardrails() -> None:
    text = _text("app/pages/21_live_draft_room_v1.py")

    assert "runtime state is local/manual" in text.lower()
    assert "No trade valuation" in text
    assert "No trade valuation, model input, rank changes, or hidden market sort" in text
    assert "market/ADP/DynastyProcess trade valuation" not in text


def test_drafting_mode_route_is_compatibility_pointer() -> None:
    text = _text("app/pages/19_drafting_mode_v2.py")

    assert "Drafting Mode moved into Live Draft" in text
    assert "Compatibility Route" in text
    assert "Open Live Draft" in text
    assert "/live-draft-room" in text
    assert "no longer acts as a separate main workspace" in text
    assert "On-Clock Cockpit" not in text
    assert "Best Available Board" not in text


def test_mock_drafts_page_uses_named_practice_state_scope() -> None:
    text = _text("app/pages/24_mock_draft_v1.py")

    assert "## MOCK DRAFTS" in text
    assert "Practice state only" in text
    assert "Saved mock draft" in text
    assert "Create Mock" in text
    assert "Duplicate Mock" in text
    assert "Delete Mock" in text
    assert "draft_id=active_session.draft_id" in text
    assert "session_key=f\"draft_day_v1_mock_draft_workflow_{active_session.draft_id}\"" in text


def test_drafting_mode_root_switches_to_live_draft() -> None:
    text = _text("app/pages/32_drafting_mode_root_v1.py")

    assert 'st.switch_page("pages/21_live_draft_room_v1.py")' in text


def test_cheat_sheets_still_reads_session_type_when_launched_with_query() -> None:
    text = _text("app/pages/18_cheat_sheets_v2.py")

    assert '_query_value("session_type")' in text
    assert "runtime_mode = _runtime_mode_from_query()" in text
    assert "load_runtime_state(mode=runtime_mode)" in text
    assert "Practice state only" in text


def test_post_draft_mode_defaults_to_live_state() -> None:
    text = _text("app/pages/29_post_draft_mode_v2.py")

    assert 'st.radio("Draft session", ["Live", "Mock"]' in text
    assert 'index=1' not in text


def test_deep_pages_expose_back_to_live_draft_link() -> None:
    pages = [
        "app/pages/18_cheat_sheets_v2.py",
        "app/pages/20_final_board_v1.py",
        "app/pages/21_live_draft_room_v1.py",
        "app/pages/22_player_compare_v1.py",
        "app/pages/23_trading_lab_v1.py",
        "app/pages/24_mock_draft_v1.py",
        "app/pages/28_settings_data_health_v1.py",
        "app/pages/29_post_draft_mode_v2.py",
        "app/pages/31_unified_universe_review_v1.py",
        "app/pages/33_evidence_integration_review_v1.py",
    ]

    for page in pages:
        text = _text(page)
        assert '<a href="/live-draft-room" target="_self">Back to Live Draft</a>' in text
        assert "Back to Drafting Mode" not in text
