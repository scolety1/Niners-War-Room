from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NavigationPageSpec:
    title: str
    file_path: str
    url_path: str
    default: bool = False
    visible: bool = True

    @property
    def visibility(self) -> str:
        return "visible" if self.visible else "hidden"


VISIBLE_NAVIGATION_PAGES: tuple[NavigationPageSpec, ...] = (
    NavigationPageSpec(
        title="Draft",
        file_path="pages/21_live_draft_room_v1.py",
        url_path="draft-cockpit",
    ),
    NavigationPageSpec(
        title="Mock Drafts",
        file_path="pages/24_mock_draft_v1.py",
        url_path="mock-draft",
    ),
    NavigationPageSpec(
        title="Rankings",
        file_path="pages/54_owner_rankings_v2.py",
        url_path="rankings",
    ),
    NavigationPageSpec(
        title="Market Analysis",
        file_path="pages/55_market_analysis_v2.py",
        url_path="market-analysis",
    ),
    NavigationPageSpec(
        title="Why NWR Ranks Them",
        file_path="pages/56_why_nwr_ranks_them_v2.py",
        url_path="why-nwr-ranks",
    ),
    NavigationPageSpec(
        title="All Dynasty Assets",
        file_path="pages/47_asset_explorer_v1.py",
        url_path="asset-explorer",
    ),
    NavigationPageSpec(
        title="Compare",
        file_path="pages/57_owner_compare_v2.py",
        url_path="player-compare",
    ),
    NavigationPageSpec(
        title="Analyze Trade",
        file_path="pages/23_trading_lab_v1.py",
        url_path="trading-lab",
    ),
    NavigationPageSpec(
        title="Rookie Review",
        file_path="pages/48_rookie_board_review_v1.py",
        url_path="rookie-board",
    ),
    NavigationPageSpec(
        title="Draft Analyzer",
        file_path="pages/29_post_draft_mode_v2.py",
        url_path="post-draft-mode",
    ),
    NavigationPageSpec(
        title="Research Tools",
        file_path="pages/35_development_lab_v1.py",
        url_path="development-lab",
    ),
    NavigationPageSpec(
        title="Roster Planner",
        file_path="pages/36_roster_weakness_tracker_v1.py",
        url_path="roster-weakness-tracker",
    ),
    NavigationPageSpec(
        title="Future Pick Planner",
        file_path="pages/37_future_pick_planning_v1.py",
        url_path="future-pick-planning",
    ),
    NavigationPageSpec(
        title="Upcoming Draft Prep",
        file_path="pages/41_upcoming_draft_prep_v1.py",
        url_path="upcoming-draft-prep",
    ),
    NavigationPageSpec(
        title="Keeper Prep",
        file_path="pages/38_keeper_deadline_prep_v1.py",
        url_path="keeper-deadline-prep",
    ),
    NavigationPageSpec(
        title="Drop Prep",
        file_path="pages/39_drop_deadline_prep_v1.py",
        url_path="drop-deadline-prep",
    ),
    NavigationPageSpec(
        title="Trade Deadline Prep",
        file_path="pages/40_trade_deadline_prep_v1.py",
        url_path="trade-deadline-prep",
    ),
    NavigationPageSpec(
        title="Future Tools",
        file_path="pages/34_future_tools_v1.py",
        url_path="future-tools",
    ),
    NavigationPageSpec(
        title="Refresh Data",
        file_path="pages/24_refresh_data_v1.py",
        url_path="refresh-data",
    ),
    NavigationPageSpec(
        title="Evidence Review",
        file_path="pages/33_evidence_integration_review_v1.py",
        url_path="evidence-integration-review",
    ),
    NavigationPageSpec(
        title="Evidence Review Hub",
        file_path="pages/45_evidence_review_hub_v1.py",
        url_path="evidence-review-hub",
    ),
    NavigationPageSpec(
        title="Settings / Data Health",
        file_path="pages/28_settings_data_health_v1.py",
        url_path="settings-data-health",
    ),
    NavigationPageSpec(
        title="My Board",
        file_path="pages/49_personal_board_v1.py",
        url_path="personal-board",
    ),
    NavigationPageSpec(
        title="Decision Tracker",
        file_path="pages/50_decision_journal_v1.py",
        url_path="decision-journal",
    ),
    NavigationPageSpec(
        title="Scenario Playground",
        file_path="pages/51_saved_scenarios_v1.py",
        url_path="saved-scenarios",
    ),
    NavigationPageSpec(
        title="Home",
        file_path="pages/46_draft_cockpit_default_root.py",
        url_path="owner-home",
    ),
    NavigationPageSpec(
        title="Player Detail",
        file_path="pages/58_owner_player_detail_v2.py",
        url_path="player-detail",
    ),
    NavigationPageSpec(
        title="Dynasty Outcomes",
        file_path="pages/26_outcome_columns_v1.py",
        url_path="outcome-columns",
    ),
    NavigationPageSpec(
        title="Rankings Data",
        file_path="pages/20_final_board_v1.py",
        url_path="rankings-data",
    ),
    NavigationPageSpec(
        title="Compare Data",
        file_path="pages/22_player_compare_v1.py",
        url_path="compare-data",
    ),
)


def _visible_page(url_path: str) -> NavigationPageSpec:
    return next(page for page in VISIBLE_NAVIGATION_PAGES if page.url_path == url_path)


VISIBLE_NAVIGATION_PAGE_GROUPS: tuple[tuple[str, tuple[NavigationPageSpec, ...]], ...] = (
    (
        "Rankings & Players",
        (
            _visible_page("owner-home"),
            _visible_page("rankings"),
            _visible_page("player-detail"),
            _visible_page("player-compare"),
            _visible_page("rookie-board"),
            _visible_page("asset-explorer"),
            _visible_page("personal-board"),
        ),
    ),
    (
        "Trades & Team",
        (
            _visible_page("trading-lab"),
            _visible_page("saved-scenarios"),
            _visible_page("decision-journal"),
            _visible_page("roster-weakness-tracker"),
            _visible_page("future-pick-planning"),
            _visible_page("keeper-deadline-prep"),
            _visible_page("drop-deadline-prep"),
            _visible_page("trade-deadline-prep"),
        ),
    ),
    (
        "Draft Tools",
        (
            _visible_page("draft-cockpit"),
            _visible_page("mock-draft"),
            _visible_page("post-draft-mode"),
            _visible_page("upcoming-draft-prep"),
        ),
    ),
    (
        "NWR Analysis",
        (
            _visible_page("market-analysis"),
            _visible_page("why-nwr-ranks"),
            _visible_page("outcome-columns"),
        ),
    ),
    (
        "Advanced/Data",
        (
            _visible_page("rankings-data"),
            _visible_page("compare-data"),
            _visible_page("development-lab"),
            _visible_page("evidence-integration-review"),
            _visible_page("evidence-review-hub"),
            _visible_page("settings-data-health"),
            _visible_page("refresh-data"),
        ),
    ),
    (
        "Advanced/Roadmap",
        (_visible_page("future-tools"),),
    ),
)

DEFAULT_ROOT_PAGE = NavigationPageSpec(
    title="Niners War Room Home",
    file_path="pages/46_draft_cockpit_default_root.py",
    url_path="",
    default=True,
    visible=False,
)

HIDDEN_ADVANCED_PAGES: tuple[NavigationPageSpec, ...] = (
    NavigationPageSpec(
        title="Redraft Legacy Route",
        file_path="pages/59_redraft_launcher.py",
        url_path="redraft",
        visible=False,
    ),
    NavigationPageSpec(
        title="Draft Cockpit Root",
        file_path="pages/44_draft_cockpit_root.py",
        url_path="draft-cockpit-root",
        visible=False,
    ),
    NavigationPageSpec(
        title="Drafting Mode Compatibility",
        file_path="pages/19_drafting_mode_v2.py",
        url_path="drafting-mode",
        visible=False,
    ),
    NavigationPageSpec(
        title="Draft Cockpit Legacy URL Alias",
        file_path="pages/43_live_draft_room_url_alias.py",
        url_path="live-draft-room",
        visible=False,
    ),
    NavigationPageSpec(
        title="Drafting Mode Root",
        file_path="pages/32_drafting_mode_root_v1.py",
        url_path="drafting-mode-root",
        visible=False,
    ),
    NavigationPageSpec(
        title="Dynasty Rankings Home",
        file_path="pages/54_owner_rankings_v2.py",
        url_path="home",
        visible=False,
    ),
    NavigationPageSpec(
        title="Dynasty Rankings URL Alias",
        file_path="pages/54_owner_rankings_v2.py",
        url_path="draft-day-home",
        visible=False,
    ),
    NavigationPageSpec(
        title="Cheat Sheets",
        file_path="pages/18_cheat_sheets_v2.py",
        url_path="cheat-sheets",
        visible=False,
    ),
    NavigationPageSpec(
        title="Draft Prep",
        file_path="pages/25_draft_prep_v1.py",
        url_path="draft-room",
        visible=False,
    ),
    NavigationPageSpec(
        title="Draft Prep Compatibility",
        file_path="pages/42_draft_prep_compat_v1.py",
        url_path="draft-prep",
        visible=False,
    ),
    NavigationPageSpec(
        title="Decision Board",
        file_path="pages/27_decision_board_v1.py",
        url_path="decision-board",
        visible=False,
    ),
    NavigationPageSpec(
        title="NFL Usage Evidence Review",
        file_path="pages/32_nfl_usage_evidence_review.py",
        url_path="nfl-usage-evidence-review",
        visible=False,
    ),
    NavigationPageSpec(
        title="Unified Universe Review",
        file_path="pages/31_unified_universe_review_v1.py",
        url_path="unified-universe-review",
        visible=False,
    ),
    NavigationPageSpec(
        title="Settings Data Health Legacy Alias",
        file_path="pages/30_settings_data_health_alias.py",
        url_path="settings",
        visible=False,
    ),
    NavigationPageSpec(
        title="Post-Draft Mode Legacy Alias",
        file_path="pages/29_post_draft_mode_v2.py",
        url_path="post-draft",
        visible=False,
    ),
    NavigationPageSpec(
        title="Draft Analyzer URL Alias",
        file_path="pages/29_post_draft_mode_v2.py",
        url_path="draft-analyzer",
        visible=False,
    ),
    NavigationPageSpec(
        title="Legacy Dynasty Rankings",
        file_path="legacy_pages/05_rankings_legacy.py",
        url_path="legacy-rankings",
        visible=False,
    ),
    NavigationPageSpec(
        title="Legacy Draft Prep",
        file_path="pages/06_draft_board.py",
        url_path="legacy-draft-room",
        visible=False,
    ),
    NavigationPageSpec(
        title="Legacy Draft Cockpit",
        file_path="pages/07_live_draft_room.py",
        url_path="legacy-live-draft-room",
        visible=False,
    ),
    NavigationPageSpec(
        title="Legacy Decision Board",
        file_path="pages/08_june15_review.py",
        url_path="legacy-decision-board",
        visible=False,
    ),
    NavigationPageSpec(
        title="Legacy External Asset Reviews",
        file_path="pages/04_trade_central.py",
        url_path="legacy-external-asset-reviews",
        visible=False,
    ),
    NavigationPageSpec(
        title="Legacy Settings",
        file_path="pages/07_source_overrides.py",
        url_path="legacy-settings",
        visible=False,
    ),
    NavigationPageSpec(
        title="Review Workflow",
        file_path="pages/00_command_center.py",
        url_path="review-workflow",
        visible=False,
    ),
    NavigationPageSpec(
        title="Command Center Legacy Alias",
        file_path="pages/00_command_center.py",
        url_path="command-center",
        visible=False,
    ),
    NavigationPageSpec(
        title="Trade Lab Legacy Alias",
        file_path="pages/04_trade_central.py",
        url_path="trade-lab",
        visible=False,
    ),
    NavigationPageSpec(
        title="Historical Replay Advanced",
        file_path="pages/09_model_tuning.py",
        url_path="model-tuning",
        visible=False,
    ),
    NavigationPageSpec(
        title="Import & Refresh",
        file_path="pages/01_import_review.py",
        url_path="import-refresh",
        visible=False,
    ),
    NavigationPageSpec(
        title="War Board",
        file_path="pages/03_war_board.py",
        url_path="war-board",
        visible=False,
    ),
    NavigationPageSpec(
        title="My Team",
        file_path="pages/02_team.py",
        url_path="my-team",
        visible=False,
    ),
    NavigationPageSpec(
        title="League Targets",
        file_path="pages/06_league_intel.py",
        url_path="league-targets",
        visible=False,
    ),
    NavigationPageSpec(
        title="Player Board Legacy Alias",
        file_path="pages/54_owner_rankings_v2.py",
        url_path="player-board",
        visible=False,
    ),
    NavigationPageSpec(
        title="Draft Board Legacy Alias",
        file_path="pages/06_draft_board.py",
        url_path="draft-board",
        visible=False,
    ),
    NavigationPageSpec(
        title="June 15 Legacy Alias",
        file_path="pages/08_june15_review.py",
        url_path="june-15-review",
        visible=False,
    ),
    NavigationPageSpec(
        title="Model Lab",
        file_path="pages/07_model_lab.py",
        url_path="model-lab",
        visible=False,
    ),
    NavigationPageSpec(
        title="Freeze",
        file_path="pages/09_draft_freeze.py",
        url_path="freeze",
        visible=False,
    ),
    NavigationPageSpec(
        title="Model Lab Sources",
        file_path="pages/07_source_overrides.py",
        url_path="model-lab-sources",
        visible=False,
    ),
    NavigationPageSpec(
        title="Sources Legacy Alias",
        file_path="pages/07_source_overrides.py",
        url_path="source_overrides",
        visible=False,
    ),
    NavigationPageSpec(
        title="Rookie Model Debug",
        file_path="pages/08_rookie_model.py",
        url_path="rookie-model-debug",
        visible=False,
    ),
    NavigationPageSpec(
        title="Rookie Model Legacy Alias",
        file_path="pages/08_rookie_model.py",
        url_path="rookie_model",
        visible=False,
    ),
    NavigationPageSpec(
        title="Historical Replay Debug",
        file_path="pages/10_historical_replay.py",
        url_path="historical-replay-debug",
        visible=False,
    ),
    NavigationPageSpec(
        title="Historical Replay Legacy Alias",
        file_path="pages/10_historical_replay.py",
        url_path="historical_replay",
        visible=False,
    ),
)

ALL_NAVIGATION_PAGES: tuple[NavigationPageSpec, ...] = (
    *VISIBLE_NAVIGATION_PAGES,
    *HIDDEN_ADVANCED_PAGES,
)


def app_page_path(app_dir: Path, spec: NavigationPageSpec) -> Path:
    return app_dir / spec.file_path


def registered_route_spec(
    url_path: str,
    pages: tuple[NavigationPageSpec, ...] = ALL_NAVIGATION_PAGES,
) -> NavigationPageSpec:
    matches = tuple(page for page in pages if page.url_path == url_path)
    if len(matches) != 1:
        raise LookupError(f"Expected one registered route for {url_path!r}; found {len(matches)}.")
    spec = matches[0]
    if spec.default:
        raise ValueError(
            f"Registered route {url_path!r} cannot also be the default root page; "
            "Streamlit ignores a default page's configured URL path."
        )
    return spec
