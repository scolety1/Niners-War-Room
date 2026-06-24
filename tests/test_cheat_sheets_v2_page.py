from __future__ import annotations

from pathlib import Path

PAGE = Path("app/pages/18_cheat_sheets_v2.py")


def test_cheat_sheet_page_keeps_draft_day_scan_controls() -> None:
    text = PAGE.read_text(encoding="utf-8")

    assert "Overall Ranking" in text
    assert "Density" in text
    assert '"Compact", "Standard", "Detailed"' in text
    assert "Summary notes" in text
    assert "Data-health warnings" in text
    assert "Drafted rows" in text
    assert "Hide drafted" in text
    assert "Show drafted" in text
    assert "Show K/DST" in text
    assert "show_drafted" in text
    assert "show_kdst" in text
    assert "Position filters" in text
    assert "Current pick:" in text
    assert "Not enough information" in text or "NOT_ENOUGH_INFORMATION" in text


def test_cheat_sheet_page_preserves_display_only_guardrails() -> None:
    text = PAGE.read_text(encoding="utf-8")

    assert "change Final Board Rank, Dynasty Rank, tier assignments" in text
    assert "ADP/range/current-pick context is display-only" in text
    assert "Market, ADP, DynastyProcess" in text
    assert "sort_workflow_frame(filtered, \"Dynasty Asset Tier/Rank\")" in text
