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
        title="Dynasty Rankings",
        file_path="pages/05_rankings.py",
        url_path="rankings",
    ),
    NavigationPageSpec(
        title="Decision Board",
        file_path="pages/08_june15_review.py",
        url_path="decision-board",
    ),
    NavigationPageSpec(
        title="Draft Prep",
        file_path="pages/06_draft_board.py",
        url_path="draft-room",
    ),
    NavigationPageSpec(
        title="Live Draft Room",
        file_path="pages/07_live_draft_room.py",
        url_path="live-draft-room",
    ),
    NavigationPageSpec(
        title="External Asset Reviews",
        file_path="pages/04_trade_central.py",
        url_path="trade-review",
    ),
    NavigationPageSpec(
        title="Settings",
        file_path="pages/07_source_overrides.py",
        url_path="settings",
    ),
)

HIDDEN_ADVANCED_PAGES: tuple[NavigationPageSpec, ...] = (
    NavigationPageSpec(
        title="Dynasty Rankings Home",
        file_path="pages/05_rankings.py",
        url_path="home",
        default=True,
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
        file_path="pages/05_rankings.py",
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
