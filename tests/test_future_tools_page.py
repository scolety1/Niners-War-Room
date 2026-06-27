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
    assert "Active model outputs" in text
    assert "group_future_tools" in text
    assert "framework/checklist shell" in text
    assert "No active output is available" in text
    assert "fake rankings" in text
    assert "not app decision wiring" in text
    assert "No rank, tier, Dynasty Rank, Final Board Rank" in text
    assert "fake trade targets" in text
