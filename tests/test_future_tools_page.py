from __future__ import annotations

from pathlib import Path


def test_future_tools_page_is_roadmap_only() -> None:
    text = Path("app/pages/34_future_tools_v1.py").read_text(encoding="utf-8")

    assert '"Future Tools"' in text
    assert "Roadmap / Ideas Only" in text
    assert "Roadmap only. These tools are not active model outputs" in text
    assert "does not run models" in text
    assert "No data pull" in text
    assert "In-Season Tools" in text
    assert "Who Should I Start?" in text
    assert "Waiver Wire Rankings" in text
    assert "Future Draft Prep" in text
    assert "Upcoming Rookie Class Preview" in text
    assert "League Calendar Tools" in text
    assert "Keeper Deadline Prep" in text
    assert "Future / Not active" in text
    assert "no fake rankings" in text
    assert "not app decision wiring" in text
    assert "No rank, tier, Dynasty Rank, Final Board Rank" in text
