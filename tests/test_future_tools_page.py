from __future__ import annotations

from pathlib import Path

APP_DIR = Path("app")
PAGES_DIR = APP_DIR / "pages"


def _page(name: str) -> str:
    return (PAGES_DIR / name).read_text(encoding="utf-8")


def test_development_lab_home_is_control_board() -> None:
    text = _page("35_development_lab_v1.py")

    assert '"Lab Home"' in text
    assert "Control board for Safe V0 manual/display tools" in text
    assert "render_safe_v0_table" in text
    assert "render_blocked_tools_table" in text
    assert "render_lab_links" in text
    assert "No model input" in text
    assert "No source truth" in text


def test_future_tools_page_is_ideas_only() -> None:
    text = _page("34_future_tools_v1.py")

    assert '"Future Tools"' in text
    assert "Roadmap Ideas" in text
    assert "Ideas-only parking lot" in text
    assert "render_blocked_tools_table" in text
    assert "render_roadmap_warning" in text
    assert "Safe V0 lab pages" in text
    assert "render_roster_weakness_tracker" not in text
    assert "render_future_pick_planning" not in text
    assert "render_deadline_prep" not in text


def test_safe_v0_lab_pages_render_their_own_tools() -> None:
    roster = _page("36_roster_weakness_tracker_v1.py")
    picks = _page("37_future_pick_planning_v1.py")
    keeper = _page("38_keeper_deadline_prep_v1.py")
    drop = _page("39_drop_deadline_prep_v1.py")
    trade = _page("40_trade_deadline_prep_v1.py")

    assert "render_roster_weakness_tracker" in roster
    assert "does not recommend drops, trades, waivers, or starters" in roster
    assert "render_future_pick_planning" in picks
    assert "No pick value" in picks
    assert 'render_deadline_prep("keeper_deadline_prep"' in keeper
    assert "No keeper advice" in keeper
    assert 'render_deadline_prep("drop_deadline_prep"' in drop
    assert "No drop advice" in drop
    assert 'render_deadline_prep("trade_deadline_prep"' in trade
    assert "No trade valuation" in trade


def test_development_lab_component_blocks_fake_recommendations() -> None:
    text = (APP_DIR / "components" / "development_lab.py").read_text(encoding="utf-8")

    assert "Development Lab tool. Safe V0 / display-only / manual workflow" in text
    assert "Roadmap only. Not active." in text
    assert "No roster recommendation is generated" in text
    assert "No pick valuation" in text
    assert "Manual checklist only" in text
    assert "fake rankings" in text
    assert "fake projections" in text
    assert "fake trade targets" in text
    assert "model input" in text
    assert "DynastyProcess" in text
