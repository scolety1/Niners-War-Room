from __future__ import annotations

from pathlib import Path


def test_future_tools_page_is_roadmap_only() -> None:
    text = Path("app/pages/34_future_tools_v1.py").read_text(encoding="utf-8")

    assert '"Future Tools"' in text
    assert "Roadmap / Ideas Only" in text
    assert "not active yet" in text
    assert "does not run models" in text
    assert "No data pull" in text
    assert "not app decision wiring" in text
    assert "No rank, tier, Dynasty Rank, Final Board Rank" in text
