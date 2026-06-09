from __future__ import annotations

import py_compile
from pathlib import Path

from app.navigation import (
    ALL_NAVIGATION_PAGES,
    HIDDEN_ADVANCED_PAGES,
    VISIBLE_NAVIGATION_PAGES,
    app_page_path,
)

APP_DIR = Path("app")


def test_visible_navigation_is_decision_focused() -> None:
    assert [page.title for page in VISIBLE_NAVIGATION_PAGES] == [
        "Dynasty Rankings",
        "Decision Board",
        "Draft Room",
        "External Asset Reviews",
        "Settings",
    ]


def test_developer_plumbing_pages_are_hidden_from_sidebar() -> None:
    hidden_titles = {page.title for page in HIDDEN_ADVANCED_PAGES}
    visible_titles = {page.title for page in VISIBLE_NAVIGATION_PAGES}

    assert hidden_titles == {
        "Import & Refresh",
        "Review Workflow",
        "Command Center Legacy Alias",
        "Trade Lab Legacy Alias",
        "Historical Replay Advanced",
        "War Board",
        "My Team",
        "League Targets",
        "Player Board Legacy Alias",
        "Draft Board Legacy Alias",
        "June 15 Legacy Alias",
        "Model Lab",
        "Freeze",
        "Model Lab Sources",
        "Sources Legacy Alias",
        "Rookie Model Debug",
        "Rookie Model Legacy Alias",
        "Historical Replay Debug",
        "Historical Replay Legacy Alias",
    }
    assert hidden_titles.isdisjoint(visible_titles)
    assert all(page.visibility == "hidden" for page in HIDDEN_ADVANCED_PAGES)


def test_navigation_page_files_exist_and_compile() -> None:
    for page in ALL_NAVIGATION_PAGES:
        page_path = app_page_path(APP_DIR, page)
        assert page_path.exists(), page_path
        py_compile.compile(str(page_path), doraise=True)


def test_exactly_one_visible_default_page() -> None:
    defaults = [page for page in VISIBLE_NAVIGATION_PAGES if page.default]

    assert [page.title for page in defaults] == ["Dynasty Rankings"]
    assert sum(1 for page in ALL_NAVIGATION_PAGES if page.default) == 1


def test_command_center_is_the_first_click_ui_framework() -> None:
    command_center = (APP_DIR / "pages" / "00_command_center.py").read_text()
    ui_framework = (APP_DIR / "components" / "ui_framework.py").read_text()

    assert "Review Workflow" in command_center
    assert "Decision Board" in command_center
    assert "Player Board" in command_center
    assert "External Asset Reviews" in command_center
    assert "Draft Room" in command_center
    assert "Tonight's shortest path" in command_center
    assert "Review-only" in command_center
    assert "No final recommendations" in command_center
    assert "render_workflow_tiles" in command_center
    assert "What Each Page Answers" in command_center
    assert "nwr-page-header" in ui_framework
    assert "nwr-tile" in ui_framework


def test_june15_review_page_is_read_only_decision_surface() -> None:
    june15_page = (APP_DIR / "pages" / "08_june15_review.py").read_text()

    assert "Decision Board" in june15_page
    assert "Review-only" in june15_page
    assert "No My Team mutation" in june15_page
    assert "No War Board mutation" in june15_page
    assert "No final recommendations" in june15_page
    assert "human_decision_review_prep" in june15_page
    assert "st.multiselect" in june15_page
    assert "Download filtered review cards" in june15_page
    assert "What this page is for" in june15_page
    assert "What the model says" in june15_page
    assert "What you decide" in june15_page
    assert "Top-Five Drop Decision" in june15_page
    assert '"Pick & Roster Review"' in june15_page
    assert '"External Asset & Rookie Context"' in june15_page
    assert '"Advanced"' in june15_page
    assert "Veteran Risk" in june15_page
    assert "Audit notes to keep in mind" in june15_page
    assert "Human question: what must be reviewed before any normal cut logic?" in june15_page
    assert (
        "Review progress: Start Here -> Drop Candidates -> Cut Cost -> Context -> Advanced."
        in june15_page
    )
    assert "June 15 review progress checklist" in june15_page
    assert "Human question: what opportunity cost would the roster lose?" in june15_page
    assert "This page prepares the review. It does not make the final cut" in june15_page
    assert "Current top-five drop slot" in june15_page
    assert "separate from the generic roster-pressure cut list" in june15_page
    assert "Advanced: technical card rows" in june15_page
    assert "Advanced: technical top-five rule rows" in june15_page
    assert "Advanced: pick inventory source rows" in june15_page
    assert "My Team changed" not in june15_page
    assert "War Board changed" not in june15_page


def test_source_plumbing_is_not_direct_sidebar_inputs() -> None:
    source_page = (APP_DIR / "pages" / "07_source_overrides.py").read_text()
    data_pack_selector = (APP_DIR / "components" / "data_pack_selector.py").read_text()

    assert "st.sidebar.text_input" not in source_page
    assert 'st.title("Settings")' in source_page
    assert "Data Health Details" in source_page
    assert "Advanced Settings" in source_page
    assert "Pack Details" in data_pack_selector


def test_player_board_is_the_big_formula_table() -> None:
    player_board = (APP_DIR / "pages" / "05_rankings.py").read_text()
    draft_room = (APP_DIR / "pages" / "06_draft_board.py").read_text()

    assert '"Dynasty Rankings"' in player_board
    assert "Private NWR dynasty board" in player_board
    assert "DEFAULT_DYNASTY_COLUMNS" in player_board
    assert '"NWR Dynasty Score"' in player_board
    assert '"Market Rank"' in player_board
    assert '"League Rank"' in player_board
    assert "Market display-only" in player_board
    assert "Outcome percentage model in development" in player_board
    assert "Advanced: feature receipts" in player_board
    assert "Draft Pool View" not in player_board
    assert 'st.title("Draft Room")' in draft_room
    assert "Rookie Analyzer" in draft_room
    assert "Review-only rookie draft surface" in draft_room
    assert "Nearby Model Value" in draft_room
    assert "Review progress: 1 Start Here -> 2 Main Review" in draft_room
    assert "Review progress checklist" in draft_room
    assert "Human question: which pick windows deserve manual scouting?" in draft_room
    assert "The human decision comes after comparing" in draft_room
    assert "Nearby Model Value" in draft_room
    assert "Pick Decision Lab" in draft_room
    assert "Evidence & Risk" in draft_room
    assert "Scout / Research" in draft_room
    assert "rookie_research_overlay" in draft_room
    assert "review-only. It can flag where to scout" in draft_room
    assert "Evidence Available" in draft_room
    assert "Trust Level" in draft_room
    assert "Production" in draft_room
    assert "College Team Share" in draft_room
    assert "Landing Context" in draft_room
    assert "low evidence should be treated as a watchlist signal" in draft_room
    assert "Draftable Board" in draft_room
    assert "Watchlist / Data Incomplete" in draft_room
    assert "Research Conflicts" in draft_room
    assert "raw score cannot masquerade as a" in draft_room
    assert '"Startup Slot Simulator"' not in draft_room
    assert '"Scout Queue"' not in draft_room
    assert '"Research Overlay"' not in draft_room
    assert '"Rookie Warnings"' not in draft_room
    assert '"Rookie Receipts"' not in draft_room


def test_external_asset_reviews_use_clear_review_only_labels() -> None:
    trade_page = (APP_DIR / "pages" / "04_trade_central.py").read_text()

    assert 'st.title("External Asset Reviews")' in trade_page
    assert "roster_context_frame" in trade_page
    assert "external_asset_context_frame" in trade_page
    assert "market_context_frame" in trade_page
    assert "context_pairing_frame" in trade_page
    for stale_internal_name in (
        "sell_frame",
        "buy_frame",
        "sell_tab",
        "buy_tab",
        "filtered_buys",
    ):
        assert stale_internal_name not in trade_page
    assert "buy_signals =" not in trade_page
    assert "Start here: Roster Context is your roster" in trade_page
    assert '"Roster Context"' in trade_page
    assert '"External Asset Context"' in trade_page
    assert '"Market Context"' in trade_page
    assert "Normalized Market Gap" in trade_page
    assert "Market Context Finder" in trade_page
    assert '"Context Drill-Down"' in trade_page
    assert "Partial Market Context" in trade_page
    assert "League Rank 0-100" in trade_page
    assert "ADP 0-100" in trade_page
    assert '"model_value": "Model Value"' in trade_page
    assert '"market_value": "Market Context"' in trade_page
    assert '"market_edge": "Model vs Market"' in trade_page
    assert '"model_desirability": "Model External Context"' in trade_page
    assert '"model_edge": "Model Gap"' in trade_page
    assert '"roster_spot_cost": "Roster Spot Cost"' in trade_page
    assert '"acceptance_likelihood": "Conversation Difficulty"' in trade_page
    assert "Legacy Pick Paths" not in trade_page


def test_external_asset_reviews_ui_renamed_from_trade_review() -> None:
    command_center = (APP_DIR / "pages" / "00_command_center.py").read_text()
    june15_page = (APP_DIR / "pages" / "08_june15_review.py").read_text()
    trade_page = (APP_DIR / "pages" / "04_trade_central.py").read_text()

    assert "External Asset Reviews" in command_center
    assert "EXTERNAL_ASSET_ROOT" in june15_page
    assert "external_asset_context_review_rows.csv" in june15_page
    assert "External Asset Cards" in june15_page
    assert "Advanced: external asset review source rows" in june15_page
    assert "Trade Review" not in command_center
    assert "Trade Review" not in trade_page
    assert "Trade & Rookie Context" not in june15_page
    assert "Trade For" not in june15_page


def test_normal_pages_keep_advanced_machinery_out_of_first_view() -> None:
    import_page = (APP_DIR / "pages" / "01_import_review.py").read_text()
    team_page = (APP_DIR / "pages" / "02_team.py").read_text()
    league_page = (APP_DIR / "pages" / "06_league_intel.py").read_text()

    assert 'with st.expander("Advanced: readiness and calibration gate"):' in import_page
    assert "Start here: review the Required Top-Five Release Slot" in team_page
    assert "Start here: check Likely Forced Releases and Cheap Targets first." in league_page
    assert 'with st.expander("Opportunity pressure by team"):' in league_page
    assert "Secondary comparison rows are diagnostic only" in league_page


def test_model_lab_is_grouped_as_a_workbench() -> None:
    model_lab_page = (APP_DIR / "pages" / "07_model_lab.py").read_text()

    assert '"Decision Gate"' in model_lab_page
    assert '"Player Audit"' in model_lab_page
    assert '"Source Coverage"' in model_lab_page
    assert '"Outliers"' in model_lab_page
    assert '"Lifecycle"' in model_lab_page
    assert '"Imports/Sources"' in model_lab_page
    assert '"Calibration"' in model_lab_page
    assert "blocking_gate_rows" in model_lab_page
    assert "why_it_matters" in model_lab_page
    assert "next_action" in model_lab_page
    assert 'with st.expander("Full checklist and gate summaries"):' in model_lab_page
    assert 'with st.expander("All lifecycle rows"):' in model_lab_page
    assert 'with st.expander("Outlier rows", expanded=True):' in model_lab_page
