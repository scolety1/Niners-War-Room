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
    upcoming = _page("41_upcoming_draft_prep_v1.py")
    keeper = _page("38_keeper_deadline_prep_v1.py")
    drop = _page("39_drop_deadline_prep_v1.py")
    trade = _page("40_trade_deadline_prep_v1.py")

    assert "render_roster_weakness_tracker" in roster
    assert "does not recommend drops, trades, waivers, or starters" in roster
    assert "render_future_pick_planning" in picks
    assert "No pick value" in picks
    assert "render_upcoming_draft_prep" in upcoming
    assert "No rookie ranks" in upcoming
    assert "No recommendations" in upcoming
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
    assert "No rookie rankings, class grades, or automated recommendations" in text
    assert "Manual checklist only" in text
    assert "fake rankings" in text
    assert "fake projections" in text
    assert "fake trade targets" in text
    assert "model input" in text
    assert "DynastyProcess" in text


def test_upcoming_draft_prep_is_manual_planning_only() -> None:
    text = (APP_DIR / "components" / "development_lab.py").read_text(encoding="utf-8")
    page_text = _page("41_upcoming_draft_prep_v1.py")
    compat_text = _page("42_draft_prep_compat_v1.py")

    assert '"Upcoming Draft Prep"' in page_text
    assert "manual planning workspace" in page_text.lower()
    assert "No rookie rankings, class grades, or automated recommendations" in text
    assert "Draft Setup Checklist" in text
    assert "Roster Needs Snapshot" in text
    assert "Pick Inventory / Asset Prep" in text
    assert "Rookie / Prospect Watchlist Placeholder" in text
    assert "Manual watchlist only. CFBD/prospect data remains review-only" in text
    assert "Mock Draft Scenario Prep" in text
    assert "Questions to Answer Before Draft" in text
    assert "Data Readiness Checklist" in text
    assert "no pick valuation" in text.lower()
    assert "class-strength grade" in text
    assert "trade calculator" in text
    assert "Compatibility page only" in compat_text
    assert "/upcoming-draft-prep" in compat_text
