"""KHA shadow replay reader -- owner-test preview (directive section 12
Path B / section 13).

Reads the already-shipped, checked-in
`docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv`
(`scripts/run_kha_shadow_optimizer_replay_v1.py`'s real, tested output --
see `tests/test_kha_shadow_optimizer_replay.py`) and exposes it as a
structured, explicitly-labeled read-only preview. This module does NOT
regenerate the CSV, does NOT touch the live KHA draft board, and does
NOT extend or reinterpret any value in it -- it only parses what the
script already computed and disclosed.

Section 12's hard rule this module exists to satisfy: never label stale
or proxy data as current. Every row/column here is either (a) 100% real
evidence from the live 157-pick KHA board (pick identity, round, team,
`real_nwr_rank_at_time_of_pick`) or (b) an explicitly-labeled proxy/
NOT_COMPUTABLE marker -- never silently upgraded to look like a real
number. `HISTORICAL_REPLAY_LABEL` is the exact, unambiguous string every
consumer (facade payload, HTTP response, frontend panel) must display;
it is never presented as "current."
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HISTORICAL_REPLAY_LABEL = "HISTORICAL REPLAY — 2026-09-02"
SOURCE_RELATIVE_PATH = "docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv"

NUMERIC_COLUMNS = (
    "pick_number", "round", "real_nwr_rank_at_time_of_pick", "team_score_before",
    "team_score_after", "champ_equity_before", "champ_equity_after",
    "starting_lineup_value_delta",
)


class KhaShadowReplayUnavailable(Exception):
    """Raised (never a fabricated empty replay) when the checked-in CSV
    is missing -- an honest, explicit failure rather than pretending no
    replay data exists at all."""


@dataclass(frozen=True)
class KhaShadowReplayPick:
    pick_number: int
    round: int
    player_name: str
    position: str
    team: str
    real_nwr_rank_at_time_of_pick: int
    value_proxy: str
    team_score_before: float | None
    team_score_after: float | None
    champ_equity_before: float | None
    champ_equity_after: float | None
    starter_holes_before: str
    starter_holes_after: str
    starting_lineup_value_delta: float | None
    top_candidate_alternatives: str
    cost_of_waiting: str
    market_state_adp: str
    production_nwr_recommendation: str


@dataclass(frozen=True)
class KhaShadowReplayPreview:
    label: str
    source_relative_path: str
    disclosed_limitations: str
    picks: tuple[KhaShadowReplayPick, ...]


def _parse_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None  # a disclosed marker string like NOT_AVAILABLE_... -- never a fabricated 0.0


def load_kha_shadow_replay_preview(repo_root: str | Path) -> KhaShadowReplayPreview:
    """The single entry point. Never regenerates the CSV -- reads exactly
    what `scripts/run_kha_shadow_optimizer_replay_v1.py` already produced
    and tested. Raises KhaShadowReplayUnavailable (never returns a faked
    or empty-but-labeled-successful preview) if the file is missing."""
    path = Path(repo_root) / SOURCE_RELATIVE_PATH
    if not path.is_file():
        raise KhaShadowReplayUnavailable(
            f"{SOURCE_RELATIVE_PATH} does not exist -- run "
            "scripts/run_kha_shadow_optimizer_replay_v1.py first, or this preview is "
            "genuinely unavailable rather than silently empty."
        )
    with path.open(encoding="utf-8") as handle:
        first_line = handle.readline()
        disclosed_limitations = (
            first_line.lstrip("# ").strip() if first_line.startswith("#") else ""
        )
        reader = csv.DictReader(handle)
        rows: list[KhaShadowReplayPick] = []
        for raw in reader:
            rows.append(
                KhaShadowReplayPick(
                    pick_number=int(raw["pick_number"]),
                    round=int(raw["round"]),
                    player_name=raw["player_name"],
                    position=raw["position"],
                    team=raw["team"],
                    real_nwr_rank_at_time_of_pick=int(raw["real_nwr_rank_at_time_of_pick"]),
                    value_proxy=raw["value_proxy"],
                    team_score_before=_parse_float(raw["team_score_before"]),
                    team_score_after=_parse_float(raw["team_score_after"]),
                    champ_equity_before=_parse_float(raw["champ_equity_before"]),
                    champ_equity_after=_parse_float(raw["champ_equity_after"]),
                    starter_holes_before=raw["starter_holes_before"],
                    starter_holes_after=raw["starter_holes_after"],
                    starting_lineup_value_delta=_parse_float(raw["starting_lineup_value_delta"]),
                    top_candidate_alternatives=raw["top_candidate_alternatives"],
                    cost_of_waiting=raw["cost_of_waiting"],
                    market_state_adp=raw["market_state_adp"],
                    production_nwr_recommendation=raw["production_nwr_recommendation"],
                )
            )
    return KhaShadowReplayPreview(
        label=HISTORICAL_REPLAY_LABEL,
        source_relative_path=SOURCE_RELATIVE_PATH,
        disclosed_limitations=disclosed_limitations,
        picks=tuple(rows),
    )


def kha_shadow_replay_payload(preview: KhaShadowReplayPreview) -> dict[str, Any]:
    """camelCase JSON shape for the desktop facade/HTTP payload."""
    return {
        "label": preview.label,
        "sourceRelativePath": preview.source_relative_path,
        "disclosedLimitations": preview.disclosed_limitations,
        "picks": [
            {
                "pickNumber": pick.pick_number,
                "round": pick.round,
                "playerName": pick.player_name,
                "position": pick.position,
                "team": pick.team,
                "realNwrRankAtTimeOfPick": pick.real_nwr_rank_at_time_of_pick,
                "valueProxy": pick.value_proxy,
                "teamScoreBefore": pick.team_score_before,
                "teamScoreAfter": pick.team_score_after,
                "champEquityBefore": pick.champ_equity_before,
                "champEquityAfter": pick.champ_equity_after,
                "starterHolesBefore": pick.starter_holes_before,
                "starterHolesAfter": pick.starter_holes_after,
                "startingLineupValueDelta": pick.starting_lineup_value_delta,
                "topCandidateAlternatives": pick.top_candidate_alternatives,
                "costOfWaiting": pick.cost_of_waiting,
                "marketStateAdp": pick.market_state_adp,
                "productionNwrRecommendation": pick.production_nwr_recommendation,
            }
            for pick in preview.picks
        ],
    }
