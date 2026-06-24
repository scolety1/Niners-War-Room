from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_drafting_mode_page_is_cockpit_not_navigation_hub() -> None:
    text = _text("app/pages/19_drafting_mode_v2.py")

    assert "On-Clock Cockpit" in text
    assert "Best Available Board" in text
    assert "Your Draft Rail" in text
    assert "Decision Panel" in text
    assert "Record Trade" in text
    assert "Drafting Mode is a navigation hub" not in text


def test_drafting_mode_top_bar_and_guardrails_are_present() -> None:
    text = _text("app/pages/19_drafting_mode_v2.py")

    assert "Current pick" in text
    assert "On-clock team" in text
    assert "Drafted" in text
    assert "Trades" in text
    assert "Autosave" in text
    assert "Refresh Data" in text
    assert "Save State" in text
    assert "Load Latest" in text
    assert "Export" in text
    assert "Market/ADP context is display-only and never drives default sort" in text


def test_drafting_mode_top_bar_exposes_session_selector_and_reset_warning() -> None:
    text = _text("app/pages/19_drafting_mode_v2.py")

    assert "Draft Session:" in text
    assert "Live Draft" in text
    assert "Mock Draft / Practice" in text
    assert "LIVE DRAFT MODE" in text
    assert "MOCK PRACTICE MODE" in text
    assert "Practice state only — does not affect live draft." in text
    assert "Resetting Live Draft state clears live picks and trades only" in text
    assert "reset_runtime_state" in text


def test_drafting_mode_deep_tool_links_carry_session_type_to_cheat_sheets() -> None:
    text = _text("app/pages/19_drafting_mode_v2.py")

    assert '("Cheat Sheets", f"/cheat-sheets?session_type={session_query}")' in text
    assert 'with st.expander("Tools / Review", expanded=False):' in text
    assert "Secondary tools stay available here and by direct URL." in text


def test_drafting_mode_selection_and_decision_panel_copy_are_clear() -> None:
    text = _text("app/pages/19_drafting_mode_v2.py")

    assert "Select player for Decision Panel" in text
    assert "Selection drives the right-side decision summary" in text
    assert "**Selected:" in text
    assert "Why this player" in text
    assert "Review checks" in text
    assert "Choose a player to see the decision summary." in text


def test_settings_data_health_label_spacing_is_consistent_in_cockpit() -> None:
    text = _text("app/pages/19_drafting_mode_v2.py")

    assert "Settings / Data Health" in text
    assert "Settings/Data Health" not in text


def test_cheat_sheets_reads_cockpit_session_type_when_launched_from_cockpit() -> None:
    text = _text("app/pages/18_cheat_sheets_v2.py")

    assert '_query_value("session_type")' in text
    assert "runtime_mode = _runtime_mode_from_query()" in text
    assert "load_runtime_state(mode=runtime_mode)" in text
    assert "Practice state only — does not affect live draft." in text


def test_post_draft_mode_defaults_to_live_state() -> None:
    text = _text("app/pages/29_post_draft_mode_v2.py")

    assert 'st.radio("Draft session", ["Live", "Mock"]' in text
    assert 'index=1' not in text


def test_deep_pages_expose_back_to_drafting_mode_link() -> None:
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
    ]

    for page in pages:
        text = _text(page)
        assert '<a href="/drafting-mode" target="_self">Back to Drafting Mode</a>' in text
