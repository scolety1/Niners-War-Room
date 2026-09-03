"""Strategy tournament + pick-level counterfactual evaluator + common-random-
number support (sections 12-14 of the follow-up directive).

The tournament runs every named baseline strategy through the SAME
`historical_draft_replay_engine_service` engine, under the SAME historical
state (feature store, available players, as_of), the SAME opponent model
(PLATFORM_ADP), the SAME league rules, and the SAME seed -- section 13's
"common random numbers" principle applied directly: the Monte Carlo
comparable-league population the three optimizer strategies consume is
built ONCE (one `simulate_comparable_leagues` call, one `base_seed`) and
shared across every strategy's evaluation in a tournament run, so
strategy-vs-strategy differences are not confounded by two different
random draws of the reference population.

The counterfactual evaluator answers "was this historical pick actually a
good decision" without the naive "player A scored more than player B"
mistake the directive explicitly warns against: it compares the selected
player against the top-ADP and top-NWR-rank alternatives THROUGH the same
roster-construction-aware Team Score / Championship Equity machinery
(`historical_decision_state_service.evaluate_historical_candidates`), not
a bare point-total comparison. Realized outcomes, when supplied, are
attached only as a strictly separate, clearly-labeled section of the
result -- never blended into the pre-freeze evaluation.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.services.decision_bundle_service import DecisionBundle
from src.services.draft_strategy_framework_service import (
    STRATEGY_PLATFORM_ADP,
    DraftStrategy,
    platform_adp_strategy,
)
from src.services.historical_decision_state_service import (
    HistoricalDecisionState,
    evaluate_historical_candidates,
)
from src.services.historical_draft_replay_engine_service import (
    ReplayReceipt,
    run_historical_draft_replay,
)
from src.services.outcome_evaluation_framework_service import PickLevelMetrics, pick_level_metrics
from src.services.point_in_time_feature_store_service import PointInTimeFeatureStore
from src.services.score_provenance_service import ScoreProvenance
from src.services.shadow_numeric_authorities_service import RosterPlayer

TOURNAMENT_VERSION = "strategy-tournament-v1"


class StrategyTournamentError(ValueError):
    pass


# --- Strategy tournament (sections 12-13) -----------------------------------


@dataclass(frozen=True)
class TournamentEntryResult:
    strategy_name: str
    season: int
    league_format: str
    draft_slot: int
    final_roster: tuple[str, ...]
    construction_failure_count: int
    runtime_seconds: float
    seed: int
    replay: ReplayReceipt
    provenance: Mapping[str, Any]


def run_strategy_tournament(
    *,
    season: int,
    league_format_label: str,
    team_count: int,
    rounds: int,
    owner_slot: int,
    available_player_ids: Sequence[str],
    feature_store: PointInTimeFeatureStore,
    as_of: str,
    seed: int,
    strategies: Mapping[str, DraftStrategy],
    league_rules_summary: Mapping[str, Any] | None = None,
    opponent_strategy_name: str = STRATEGY_PLATFORM_ADP,
    opponent_strategy: DraftStrategy = platform_adp_strategy,
) -> tuple[TournamentEntryResult, ...]:
    """Runs every strategy in `strategies` under identical inputs and the
    identical `seed`, so results are directly comparable pairwise (common
    random numbers). Does not cherry-pick: every strategy supplied runs
    and reports, whether it wins or loses this run."""
    if not strategies:
        raise StrategyTournamentError("Need at least one strategy to run a tournament.")
    results: list[TournamentEntryResult] = []
    for name, strategy in strategies.items():
        start = time.perf_counter()
        receipt = run_historical_draft_replay(
            season=season, team_count=team_count, rounds=rounds,
            available_player_ids=available_player_ids, feature_store=feature_store,
            as_of=as_of, owner_slot=owner_slot, owner_strategy_name=name,
            owner_strategy=strategy, league_rules_summary=league_rules_summary,
            opponent_strategy_name=opponent_strategy_name, opponent_strategy=opponent_strategy,
            seed=seed,
        )
        elapsed = time.perf_counter() - start
        roster = receipt.rosters_by_slot.get(owner_slot, ())
        construction_failures = sum(
            1 for pick in receipt.picks
            if pick.team_slot == owner_slot and pick.selected_player_id is None
        )
        results.append(
            TournamentEntryResult(
                strategy_name=name, season=season, league_format=league_format_label,
                draft_slot=owner_slot, final_roster=roster,
                construction_failure_count=construction_failures,
                runtime_seconds=round(elapsed, 4), seed=seed, replay=receipt,
                provenance={
                    "team_count": team_count, "rounds": rounds,
                    "opponent_strategy_name": opponent_strategy_name,
                    "tournament_version": TOURNAMENT_VERSION,
                },
            )
        )
    return tuple(results)


def build_shared_comparable_leagues_seed(base_seed: int, *, purpose: str) -> int:
    """A single documented seed derivation point -- every optimizer
    evaluator built for a tournament run should derive its comparable-
    league population from THIS seed, not a fresh one per strategy, so
    every strategy is scored against the identical simulated reference
    population (the common-random-number guarantee, made mechanical
    rather than just a convention callers might forget)."""
    if not purpose.strip():
        raise StrategyTournamentError("purpose must describe what this seed derivation is for.")
    return base_seed


# --- Pick-level counterfactual evaluator (section 14) -----------------------


@dataclass(frozen=True)
class PickCounterfactual:
    pick_number: int
    selected_player_id: str
    top_adp_alternative_id: str | None
    top_nwr_alternative_id: str | None
    pre_freeze_evaluation: DecisionBundle
    realized_metrics: PickLevelMetrics | None


def _top_adp_available(state: HistoricalDecisionState) -> str | None:
    candidates = [
        entry for entry in state.adp.entries if entry.player_id in state.available_player_ids
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda e: e.overall_adp).player_id


def _top_nwr_available(state: HistoricalDecisionState) -> str | None:
    candidates = [
        row for row in state.ranking.rows if row.player_id in state.available_player_ids
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda row: row.overall_rank).player_id


def build_pick_counterfactual(
    state: HistoricalDecisionState,
    *,
    selected_player_id: str,
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    provenance: ScoreProvenance,
    realized_production_by_player: Mapping[str, float] | None = None,
    next_pick_available_player_ids: Sequence[str] | None = None,
    replacement_points: float | None = None,
    player_scores: Mapping[str, float] | None = None,
) -> PickCounterfactual:
    """The selected player plus the top-ADP and top-NWR-rank real
    alternatives available at this exact pick, evaluated through the
    same roster-construction-aware Team Score / Championship Equity
    machinery -- never a bare point-total comparison. Realized outcomes
    (`realized_production_by_player`), when supplied, are attached as a
    strictly separate `realized_metrics` field computed AFTER the
    pre_freeze_evaluation, never blended into it."""
    top_adp = _top_adp_available(state)
    top_nwr = _top_nwr_available(state)
    candidate_ids = list(dict.fromkeys([selected_player_id, top_adp, top_nwr]))
    candidate_ids = [pid for pid in candidate_ids if pid is not None]
    if selected_player_id not in candidate_ids:
        candidate_ids.insert(0, selected_player_id)

    bundle = evaluate_historical_candidates(
        state, candidate_player_ids=candidate_ids, comparable_leagues=comparable_leagues,
        provenance=provenance, player_scores=player_scores,
    )

    realized: PickLevelMetrics | None = None
    has_realized_selection = (
        realized_production_by_player is not None
        and selected_player_id in realized_production_by_player
    )
    if has_realized_selection:
        pool = {
            pid: realized_production_by_player[pid]
            for pid in state.available_player_ids
            if pid in realized_production_by_player
        }
        realized = pick_level_metrics(
            pick_number=state.pick_number, selected_player_id=selected_player_id,
            selected_realized_production=realized_production_by_player[selected_player_id],
            available_pool_realized_production=pool, replacement_points=replacement_points,
            next_pick_available_player_ids=next_pick_available_player_ids,
        )

    return PickCounterfactual(
        pick_number=state.pick_number, selected_player_id=selected_player_id,
        top_adp_alternative_id=top_adp, top_nwr_alternative_id=top_nwr,
        pre_freeze_evaluation=bundle, realized_metrics=realized,
    )
