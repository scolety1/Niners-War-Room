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
    assert "render_development_lab_readiness" in text
    assert "render_refresh_health_waiting_panel" in text
    assert "render_bulk_lab_state_controls" in text
    assert "render_future_tool_gate_badges" in text
    assert "render_blocked_tools_table" in text
    assert "render_lab_links" in text
    assert "render_local_lab_state_status" in text
    assert "No model input" in text
    assert "No source truth" in text
    assert "NFLVerse Display Context Status" in text


def test_future_tools_page_is_ideas_only() -> None:
    text = _page("34_future_tools_v1.py")

    assert '"Future Tools"' in text
    assert "Roadmap Ideas" in text
    assert "Ideas-only parking lot" in text
    assert "render_blocked_tools_table" in text
    assert "render_future_tool_gate_badges" in text
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
    assert "Decisions remain human/manual outside this page" in roster
    assert "render_future_pick_planning" in picks
    assert "descriptive and manual" in picks
    assert "render_upcoming_draft_prep" in upcoming
    assert "Manual context" in upcoming
    assert 'render_deadline_prep("keeper_deadline_prep"' in keeper
    assert "Human review" in keeper
    assert 'render_deadline_prep("drop_deadline_prep"' in drop
    assert "human-review status only" in drop
    assert 'render_deadline_prep("trade_deadline_prep"' in trade
    assert "factual/manual context only" in trade


def test_development_lab_component_blocks_fake_recommendations() -> None:
    text = (APP_DIR / "components" / "development_lab.py").read_text(encoding="utf-8")

    assert "Development Lab tool. Safe V0 / display-only / manual workflow" in text
    assert "Roadmap only. Not active." in text
    assert "Only manual/display-only summaries are shown" in text
    assert "Pick and trade context stays descriptive/manual" in text
    assert "Rookie/prospect context stays manual until approved gates clear" in text
    assert "NFLVerse refresh health and player context are available" in text
    assert "Player-context artifact status" in text
    assert "Dataset readiness / source policy" in text
    assert "NFLVerse Player Context" in text
    assert "NFLVerse Draft Capital Context" in text
    assert "NFLVerse Roster / Status Context" in text
    assert "Manual checklist only" in text
    assert "Local lab notes only. Not model input. Not source truth." in text
    assert "Save local lab state" in text
    assert "Import Development Lab state JSON" in text
    assert "Export all local lab notes JSON" in text
    assert "Import Development Lab bulk state JSON" in text
    assert "Confirm reset saved local state" in text
    assert "SAFE_REFRESH_CONTEXT_READY_DISPLAY_ONLY" not in text
    assert "Not enough information" in text
    assert "raw shared/cache files" in text
    assert "Blocked future" in text
    assert "model input" in text
    assert "DynastyProcess" in text


def test_upcoming_draft_prep_is_manual_planning_only() -> None:
    text = (APP_DIR / "components" / "development_lab.py").read_text(encoding="utf-8")
    page_text = _page("41_upcoming_draft_prep_v1.py")
    compat_text = _page("42_draft_prep_compat_v1.py")

    assert '"Upcoming Draft Prep"' in page_text
    assert "manual planning workspace" in page_text.lower()
    assert "Rookie/prospect context stays manual until approved gates clear" in text
    assert "Draft Setup Checklist" in text
    assert "Roster Needs Snapshot" in text
    assert "Pick Inventory / Asset Prep" in text
    assert "Rookie / Prospect Watchlist Placeholder" in text
    assert "Manual watchlist only. CFBD/prospect data remains review-only" in text
    assert "Mock Draft Scenario Prep" in text
    assert "Questions to Answer Before Draft" in text
    assert "Data Readiness Checklist" in text
    assert "no pick/trade math" in text.lower()
    assert "class-strength labels" in text
    assert "trade calculator" in text
    assert "Compatibility page only" in compat_text
    assert "/upcoming-draft-prep" in compat_text


def test_safe_v1_persistence_is_local_lab_state_only() -> None:
    text = (APP_DIR / "components" / "development_lab.py").read_text(encoding="utf-8")
    service = Path("src/services/development_lab_state_service.py").read_text(encoding="utf-8")

    for tool_key in (
        "roster_weakness_tracker",
        "future_pick_planning",
        "upcoming_draft_prep",
        "keeper_deadline_prep",
        "drop_deadline_prep",
        "trade_deadline_prep",
    ):
        assert tool_key in service
    assert "C:\\NWR_SHARED_DATA\\development_lab_state" in service
    assert "NWR_DEVELOPMENT_LAB_STATE_ROOT" in service
    assert "export_all_tool_states_json" in service
    assert "import_all_tool_states" in service
    assert "C:\\\\NWR_SHARED_DATA" not in text
    assert "load_runtime_state_with_status(mode=\"live\")" in text
    assert "Local lab notes only. Not model input. Not source truth." in text
    assert "Not draft-room runtime state" in text


def test_development_lab_safe_upgrade_words_stay_manual_and_display_only() -> None:
    files = [
        APP_DIR / "components" / "development_lab.py",
        PAGES_DIR / "34_future_tools_v1.py",
        PAGES_DIR / "35_development_lab_v1.py",
        PAGES_DIR / "36_roster_weakness_tracker_v1.py",
        PAGES_DIR / "37_future_pick_planning_v1.py",
        PAGES_DIR / "38_keeper_deadline_prep_v1.py",
        PAGES_DIR / "39_drop_deadline_prep_v1.py",
        PAGES_DIR / "40_trade_deadline_prep_v1.py",
        PAGES_DIR / "41_upcoming_draft_prep_v1.py",
        PAGES_DIR / "42_draft_prep_compat_v1.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in files)

    # These exact sentences are negative safety disclosures, not positive model output.
    # Require them before removing them from the positive-language scan so wording drift
    # cannot silently turn this into a broad exception.
    negative_disclosures = (
        "not a model score. ngs public thresholds may exclude low-volume players.",
        "score, recommendation, verdict, boost, hidden sort, or ranking effect.",
    )
    for disclosure in negative_disclosures:
        assert disclosure in text
        text = text.replace(disclosure, "")

    for blocked_phrase in (
        "recommendation",
        "recommendations",
        "valuation",
        "model score",
        "class grade",
    ):
        assert blocked_phrase not in text
    assert "manual" in text
    assert "display-only" in text
    assert "nflverse" in text
    assert "raw shared/cache files" in text
