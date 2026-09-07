"""DecisionBundle API (directive section 29).

Composes the existing, already-tested SHADOW/RESEARCH numeric authorities
(`team_score`, `championship_equity`, `evaluate_pick_candidates`,
`evaluate_cost_of_waiting_v2`, `label_pick_decisions`) into ONE structured
result for one pick: current state, a per-candidate breakdown, and a
reproducibility provenance bundle. This module does not reimplement any of
those calculations -- it is purely a composition layer, so "the UI should
not independently recompute the math" (the directive's own requirement)
has exactly one real implementation to consume, here.

This stays a backend/SHADOW artifact: nothing in this module writes to a
production decision surface, and every value in a DecisionBundle already
carries the SHADOW/RESEARCH labels the underlying functions attach
(`TEAM_SCORE_LABEL`, `CHAMPIONSHIP_EQUITY_LABEL`, `PICK_SCORE_LABEL`, ...).
Wiring a DecisionBundle into Draft Room's live HTTP surface is a distinct,
separable follow-on decision, not made by this module existing.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from src.services.metric_status_contract_service import (
    MetricStatus,
    championship_equity_status,
    cost_of_waiting_status,
    make_it_back_status,
    pick_score_status,
    player_score_status,
    team_score_status,
)
from src.services.redraft_draft_room_v1_service import AdpSnapshot
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.score_provenance_service import ScoreProvenance
from src.services.shadow_numeric_authorities_service import (
    ChampionshipEquityResult,
    CostOfWaitingV2Result,
    PickScoreResult,
    RosterPlayer,
    TeamScoreResult,
    championship_equity,
    evaluate_cost_of_waiting_v2,
    evaluate_pick_candidates,
    label_pick_decisions,
    team_score,
)

DECISION_BUNDLE_VERSION = "decision-bundle-v1"

# Raw Decision Utility (section 8, follow-up directive) = team_score_utility_component
# + equity_utility_component, where equity_utility_component multiplies a 0.0-1.0
# probability delta by this constant to put it on a scale roughly commensurate
# with a 0-100 Team Score percentile delta. This IS an arbitrary weight -- disclosed
# here, not disguised by normalization -- see
# docs/codex/RAW_DECISION_UTILITY_CONSTRUCTION_20260903.md for the full writeup and
# exactly what historical calibration would need to replace it with something learned.
EQUITY_TO_PERCENTILE_WEIGHT = 100.0


@dataclass(frozen=True)
class CandidateBundle:
    player_id: str
    player_score: float | None
    team_score_after: float
    team_score_delta: float
    championship_equity_after: float
    equity_gain: float
    cost_of_waiting: float
    make_it_back_probability: float | None
    # Owner-test follow-up: real trial count behind make_it_back_probability
    # -- a candidate "surviving" 100% of a SMALL number of simulated
    # continuations is a real, disclosed modeled estimate, not a guarantee.
    # Additive only; None exactly when make_it_back_probability is None
    # (no evaluated Cost-of-Waiting result for this candidate).
    make_it_back_trials: int | None
    raw_decision_utility: float
    # The two additive components raw_decision_utility is built from, preserved
    # separately (not just the combined scalar) so historical calibration can
    # later learn or replace EQUITY_TO_PERCENTILE_WEIGHT without re-deriving them.
    team_score_utility_component: float
    equity_utility_component: float
    pick_score: float
    # Owner feedback closure (result-status taxonomy): True exactly when
    # every candidate evaluated alongside this one shared the same
    # championship-equity win_probability -- pick_score is a genuine,
    # honest 50.0 (or every score in the set collapses to the same
    # value) because the frozen formula has no spread to work with, not
    # because this candidate was skipped or unevaluated. Additive only;
    # never changes pick_score's own value.
    pick_score_tied_no_spread: bool
    action: str
    warnings: tuple[str, ...]
    uncertainty: str
    # Owner feedback closure (shared cross-metric result-status contract):
    # one MetricStatus per metric family, keyed by the same short name the
    # camelCase JSON payload uses. Additive only -- every field above keeps
    # its own already-computed value; this only labels it. Defaults to empty
    # so any older/test construction site that predates this field still
    # builds; both real construction sites (this module and
    # historical_decision_state_service.py) always pass a populated dict.
    metric_status: Mapping[str, MetricStatus] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionBundle:
    version: str
    current_team_score: TeamScoreResult
    current_championship_equity: ChampionshipEquityResult
    candidates: tuple[CandidateBundle, ...]
    provenance: ScoreProvenance
    latency_seconds: float
    simulation_metadata: Mapping[str, Any]


def _uncertainty_label(equity: ChampionshipEquityResult) -> str:
    """A disclosed, simple uncertainty class from the Monte Carlo standard
    error already computed by championship_equity() -- not a new model,
    just surfacing an existing number as a first-class field (section 27)."""
    if equity.standard_error >= 0.03:
        return f"HIGH_MODEL_UNCERTAINTY (SE={equity.standard_error:.4f})"
    if equity.standard_error >= 0.015:
        return f"MODERATE_MODEL_UNCERTAINTY (SE={equity.standard_error:.4f})"
    return f"LOW_MODEL_UNCERTAINTY (SE={equity.standard_error:.4f})"


def build_decision_bundle(
    *,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    owner_slot: int,
    current_owner_player_ids: Sequence[str],
    candidate_player_ids: Sequence[str],
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    provenance: ScoreProvenance,
    player_scores: Mapping[str, float] | None = None,
    from_state: Mapping[str, Any] | None = None,
    include_cost_of_waiting: bool = True,
    current_pick_number: int = 1,
    trials: int = 200,
    seasons: int = 200,
    base_seed: int = 20260903,
) -> DecisionBundle:
    """Builds one DecisionBundle for the pick described by `current_owner_player_ids`
    (the owner's roster BEFORE this pick) and `candidate_player_ids` (the
    actionable candidates being compared, already legality-filtered by the
    caller -- this function does not re-derive roster-legal candidates).
    """
    start = time.perf_counter()
    player_scores = player_scores or {}

    current_team = team_score(
        current_owner_player_ids, profile, ranking, manual_assets,
        comparable_leagues=comparable_leagues,
    )
    default_slot = next(iter(comparable_leagues[0]))
    target_slot = owner_slot if owner_slot in comparable_leagues[0] else default_slot
    current_equity = championship_equity(
        current_owner_player_ids, profile, ranking, manual_assets,
        comparable_league=comparable_leagues[0],
        target_team_slot=target_slot,
        seasons=seasons, base_seed=base_seed,
    )

    pick_scores: dict[str, PickScoreResult] = evaluate_pick_candidates(
        profile, ranking, manual_assets, adp,
        owner_slot=owner_slot, candidate_player_ids=candidate_player_ids,
        from_state=from_state, comparable_leagues=comparable_leagues,
        trials=trials, seasons=seasons, base_seed=base_seed,
    )

    cost_of_waiting_results: dict[str, CostOfWaitingV2Result] = {}
    actions: dict[str, str] = {}
    if include_cost_of_waiting and pick_scores:
        cost_of_waiting_results = evaluate_cost_of_waiting_v2(
            profile, ranking, manual_assets, adp,
            owner_slot=owner_slot, candidate_player_ids=list(pick_scores.keys()),
            pick_scores=pick_scores, from_state=from_state,
            trials=trials, base_seed=base_seed,
        )
        adp_expected_pick_by_id = {
            entry.player_id: entry.expected_pick for entry in adp.entries
        }
        actions = label_pick_decisions(
            cost_of_waiting_results,
            adp_expected_pick_by_id=adp_expected_pick_by_id,
            current_pick_number=current_pick_number,
            team_count=profile.team_count,
        )

    source_as_of = ranking.rows[0].source_as_of if ranking.rows else ""

    candidates: list[CandidateBundle] = []
    for player_id, pick in pick_scores.items():
        warnings: list[str] = []
        cow = cost_of_waiting_results.get(player_id)
        if player_id not in player_scores:
            warnings.append("No standalone Player Score supplied for this candidate.")
        team_score_component = round(pick.team_score_after - current_team.percentile, 4)
        equity_component = round(
            EQUITY_TO_PERCENTILE_WEIGHT
            * (pick.championship_equity_after - current_equity.win_probability),
            4,
        )
        cow_value = cow.expected_cost if cow is not None else pick.cost_of_waiting
        mib_probability = cow.survival_probability if cow is not None else None
        mib_trials = cow.trials if cow is not None else None
        metric_status = {
            "playerScore": player_score_status(
                player_scores.get(player_id), source_as_of=source_as_of
            ),
            "teamScore": team_score_status(pick.team_score_after, source_as_of=source_as_of),
            "championshipEquity": championship_equity_status(
                pick.championship_equity_after,
                standard_error=current_equity.standard_error,
                source_as_of=source_as_of,
            ),
            "costOfWaiting": cost_of_waiting_status(
                cow_value, from_v2_evaluation=cow is not None, source_as_of=source_as_of
            ),
            "makeItBack": make_it_back_status(
                mib_probability, mib_trials, source_as_of=source_as_of
            ),
            "pickScore": pick_score_status(
                pick.relative_score,
                tied_no_spread=pick.tied_no_spread,
                source_as_of=source_as_of,
            ),
        }
        candidates.append(
            CandidateBundle(
                player_id=player_id,
                player_score=player_scores.get(player_id),
                team_score_after=pick.team_score_after,
                team_score_delta=round(pick.team_score_after - current_team.percentile, 2),
                championship_equity_after=pick.championship_equity_after,
                equity_gain=pick.equity_gain,
                cost_of_waiting=cow_value,
                make_it_back_probability=mib_probability,
                make_it_back_trials=mib_trials,
                raw_decision_utility=round(team_score_component + equity_component, 4),
                team_score_utility_component=team_score_component,
                equity_utility_component=equity_component,
                pick_score=pick.relative_score,
                pick_score_tied_no_spread=pick.tied_no_spread,
                action=actions.get(player_id, "UNSCORED"),
                warnings=tuple(warnings),
                uncertainty=_uncertainty_label(current_equity),
                metric_status=metric_status,
            )
        )
    candidates.sort(key=lambda c: c.pick_score, reverse=True)

    elapsed = time.perf_counter() - start
    return DecisionBundle(
        version=DECISION_BUNDLE_VERSION,
        current_team_score=current_team,
        current_championship_equity=current_equity,
        candidates=tuple(candidates),
        provenance=provenance,
        latency_seconds=round(elapsed, 4),
        simulation_metadata={
            "trials": trials,
            "seasons": seasons,
            "base_seed": base_seed,
            "candidate_count": len(candidates),
        },
    )
