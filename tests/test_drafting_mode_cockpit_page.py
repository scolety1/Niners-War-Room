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


def test_deep_pages_expose_back_to_drafting_mode_link() -> None:
    pages = [
        "app/pages/18_cheat_sheets_v2.py",
        "app/pages/20_final_board_v1.py",
        "app/pages/22_player_compare_v1.py",
        "app/pages/23_trading_lab_v1.py",
        "app/pages/28_settings_data_health_v1.py",
        "app/pages/29_post_draft_mode_v2.py",
    ]

    for page in pages:
        text = _text(page)
        assert 'st.link_button("Back to Drafting Mode", "/drafting-mode")' in text
