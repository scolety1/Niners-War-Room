from __future__ import annotations

from pathlib import Path


def test_future_tools_page_is_roadmap_only() -> None:
    text = Path("app/pages/34_future_tools_v1.py").read_text(encoding="utf-8")

    assert '"Future Tools"' in text
    assert "Roadmap / R&D Control Board" in text
    assert "Roadmap and R&D only. These are not active model outputs" in text
    assert "does not run models" in text
    assert "No data pull" in text
    assert "load_future_tools_status_matrix" in text
    assert "Safe V0 Tools" in text
    assert "Blocked / Needs Gate" in text
    assert "Safe V0 display/manual" in text
    assert "Roster Weakness Tracker" in text
    assert "Future Pick Planning" in text
    assert "Deadline Prep Toolkit" in text
    assert "Active model outputs" in text
    assert "manual/display-only" in text
    assert "No future picks found in the live runtime trade event log" in text
    assert "fake rankings" in text
    assert "not app decision wiring" in text
    assert "No rank, tier, Dynasty Rank, Final Board Rank" in text
    assert "fake trade targets" in text
