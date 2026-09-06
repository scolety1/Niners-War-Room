"""Team Score calibration corpus (NWR Team Score Recovery V1, sections
1-2): a genuine roster-calibration population, not a small strategy-
tournament comparison set.

**Audit finding (section 1)**: the Phase 2 n=63 result came from exactly
7 strategies x 9 seasons x ONE fixed draft_slot (1) x ONE fixed seed
(20260904) -- confirmed directly from
`scripts/run_team_score_roster_level_correlation_v1.py`. Varying `seed`
alone would not have diversified it further: none of the 7 registered
strategies read `StrategyDecisionContext.seed` for any real
randomization (they are deterministic ranking functions; the 3 optimizer
strategies draw their own Monte Carlo randomness from a `base_seed` fixed
at CONSTRUCTION time, not the per-pick context seed). This module adds
the two real levers that DO diversify the roster population within a
season: (1) draft slot (which genuinely changes who is available when
the strategy picks) and (2) a new, disclosed, bounded stochastic
perturbation strategy family (`make_noisy_greedy_strategy`) that adds
seeded Gaussian noise to the real NWR ranking feature before greedily
picking -- a legitimate Monte Carlo draft path, not an invented/illegal
roster.
"""

from __future__ import annotations

import random
import time
from collections.abc import Sequence
from dataclasses import dataclass

from src.services.draft_strategy_framework_service import StrategyDecision, StrategyDecisionContext
from src.services.point_in_time_feature_store_service import KNOWN

NOISY_GREEDY_STRATEGY_PREFIX = "NOISY_GREEDY_NWR"


class TeamScoreCalibrationCorpusError(ValueError):
    pass


def make_noisy_greedy_strategy(*, seed: int, noise_scale: float = 5.0):
    """A disclosed, bounded stochastic draft-path generator: the same
    real `nwr_component_scores.overall_rank` feature `greedy_nwr_strategy`
    uses, perturbed by seeded Gaussian noise (std `noise_scale`, in rank
    units) before picking greedily. Deterministic given `seed` -- the SAME
    seed always produces the SAME roster for a fixed draft state, so this
    is a real, reproducible Monte Carlo draft path, not randomness that
    can never be reproduced."""
    rng = random.Random(seed)
    strategy_name = f"{NOISY_GREEDY_STRATEGY_PREFIX}_SEED_{seed}"

    def strategy(context: StrategyDecisionContext) -> StrategyDecision:
        start = time.perf_counter()
        scored: list[tuple[str, float]] = []
        unresolved: list[str] = []
        for player_id in context.available_player_ids:
            feature = context.feature_store.lookup_as_of(
                player_id=player_id, season=context.season,
                feature_name="nwr_component_scores.overall_rank", as_of=context.as_of,
            )
            if feature.value_status != KNOWN or feature.value is None:
                unresolved.append(player_id)
                continue
            noisy_rank = float(feature.value) + rng.gauss(0.0, noise_scale)
            scored.append((player_id, noisy_rank))
        scored.sort(key=lambda item: item[1])  # lower (noisy) rank is better
        ranking = tuple(player_id for player_id, _ in scored)
        return StrategyDecision(
            strategy_name=strategy_name, strategy_version="v1",
            selected_player_id=ranking[0] if ranking else None, candidate_ranking=ranking,
            decision_metadata={
                "unresolved_player_ids": tuple(unresolved), "noise_scale": noise_scale,
            },
            runtime_seconds=round(time.perf_counter() - start, 4),
        )

    return strategy_name, strategy


@dataclass(frozen=True)
class RosterObservation:
    """Every field the directive's provenance requirement names."""

    season: int
    draft_slot: int
    generation_policy: str  # e.g. "BASELINE_STRATEGY" or "NOISY_GREEDY_PERTURBATION"
    strategy_name: str
    seed: int
    roster_player_ids: tuple[str, ...]
    team_score_percentile: float
    team_score_raw_value: float
    realized_total: float
    n_realized_known: int
    roster_size: int
    league_team_count: int
    draft_date: str


def build_roster_observation(
    *, season: int, draft_slot: int, generation_policy: str, strategy_name: str, seed: int,
    roster_player_ids: Sequence[str], team_score_percentile: float, team_score_raw_value: float,
    realized_by_player: dict, league_team_count: int, draft_date: str,
) -> RosterObservation:
    realized_total = round(sum(realized_by_player.get(pid, 0.0) for pid in roster_player_ids), 2)
    n_known = sum(1 for pid in roster_player_ids if pid in realized_by_player)
    return RosterObservation(
        season=season, draft_slot=draft_slot, generation_policy=generation_policy,
        strategy_name=strategy_name, seed=seed, roster_player_ids=tuple(roster_player_ids),
        team_score_percentile=team_score_percentile, team_score_raw_value=team_score_raw_value,
        realized_total=realized_total, n_realized_known=n_known,
        roster_size=len(roster_player_ids), league_team_count=league_team_count,
        draft_date=draft_date,
    )
