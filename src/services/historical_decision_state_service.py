"""Historical decision state + Team Score / Championship Equity / Cost of
Waiting / Pick Score wiring for historical replay (sections 3-7 of the
follow-up directive).

`HistoricalDecisionState` is the one reusable constructor the directive
asks for: everything a historical pick decision needs (season, as_of,
league profile, pick number, round, owner slot, rosters before the pick,
available players, the bridged RankingResult/AdpSnapshot/feature store,
strategy version) -- built ONLY from what was knowable at `as_of`, never
from a later pick, later season data, or a realized outcome. Outcome data
is attached only afterward, by the outcome evaluator, never during
recommendation generation -- this module has no realized-outcome input
at all.

Team Score / Championship Equity / Pick Score are wired via the real,
unmodified `team_score()` / `championship_equity()` / `pick_score()`
functions -- the SAME functions the live Draft Room's DecisionBundle
uses -- called directly on before/after roster states (the same
methodology `QB_PATHOLOGY_MONEYBALL_DEMONSTRATION_20260903.md` already
established and documented: isolating one pick's own marginal effect,
rather than the full look-ahead pipeline).

Deliberately NOT reused: `evaluate_pick_candidates` /
`evaluate_cost_of_waiting_v2` / `simulate_pick_now`. Those depend on
`redraft_draft_room_v1_service`'s live mock-room CPU-simulation
machinery, keyed by its own `draft_order()` snake-order implementation --
a SEPARATE implementation from this session's `historical_draft_replay_engine_service`'s
own snake order. Bridging the two without dedicated alignment testing
would risk a silent team-slot misattribution; not attempted this wave.
Cost of Waiting here instead uses a disclosed, versioned, ADP-distance
survival heuristic (`estimate_historical_survival_probability`) -- real,
bounded, and tested, but explicitly NOT the full CPU Monte Carlo the live
Draft Room uses, and labeled as such throughout.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from src.services.decision_bundle_service import (
    EQUITY_TO_PERCENTILE_WEIGHT,
    CandidateBundle,
    DecisionBundle,
)
from src.services.historical_ranking_bridge_service import (
    ExcludedHistoricalPlayer,
    HistoricalRankingBridgeResult,
)
from src.services.point_in_time_feature_store_service import PointInTimeFeatureStore
from src.services.redraft_draft_room_v1_service import AdpSnapshot
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult
from src.services.score_provenance_service import ScoreProvenance
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    championship_equity,
    pick_score,
    team_score,
)

HISTORICAL_DECISION_ENGINE_VERSION = "historical-decision-state-v1"
SURVIVAL_HEURISTIC_VERSION = "historical-adp-survival-heuristic-v1"


class HistoricalDecisionStateError(ValueError):
    pass


@dataclass(frozen=True)
class HistoricalDecisionState:
    season: int
    as_of: str
    profile: LeagueProfile
    pick_number: int
    round_number: int
    owner_slot: int
    rosters_by_slot: Mapping[int, tuple[str, ...]]
    available_player_ids: tuple[str, ...]
    ranking: RankingResult
    manual_assets: tuple[Mapping[str, Any], ...]
    adp: AdpSnapshot
    feature_store: PointInTimeFeatureStore
    strategy_version: str
    bridge_excluded_players: tuple[ExcludedHistoricalPlayer, ...]


def build_historical_decision_state(
    bridge_result: HistoricalRankingBridgeResult,
    *,
    season: int,
    as_of: str,
    pick_number: int,
    round_number: int,
    owner_slot: int,
    rosters_by_slot: Mapping[int, Sequence[str]],
    strategy_version: str,
    manual_assets: Sequence[Mapping[str, Any]] = (),
) -> HistoricalDecisionState:
    """Rosters are the caller's responsibility to have built using ONLY
    picks 1..pick_number-1 -- this constructor does not (and cannot)
    verify that on its own, but it does enforce the one thing it CAN
    verify: available_player_ids never includes anyone already on a
    roster, and never includes anyone the bridge itself excluded for
    missing projection data."""
    if pick_number < 1:
        raise HistoricalDecisionStateError("pick_number must be >= 1.")
    drafted: set[str] = set()
    for roster in rosters_by_slot.values():
        drafted.update(roster)
    available = tuple(
        pid for pid in bridge_result.included_player_ids if pid not in drafted
    )
    return HistoricalDecisionState(
        season=season,
        as_of=as_of,
        profile=bridge_result.ranking.profile,
        pick_number=pick_number,
        round_number=round_number,
        owner_slot=owner_slot,
        rosters_by_slot={slot: tuple(ids) for slot, ids in rosters_by_slot.items()},
        available_player_ids=available,
        ranking=bridge_result.ranking,
        manual_assets=tuple(manual_assets),
        adp=bridge_result.adp,
        feature_store=bridge_result.feature_store,
        strategy_version=strategy_version,
        bridge_excluded_players=bridge_result.excluded_players,
    )


def estimate_historical_survival_probability(
    *,
    adp_expected_pick: float | None,
    current_pick_number: int,
    team_count: int,
    picks_until_next_turn: int,
) -> float | None:
    """A disclosed, versioned, bounded ADP-distance heuristic for
    P(player survives until the owner's next pick) -- NOT the live Draft
    Room's CPU Monte Carlo simulation (see module docstring for why).
    Returns None (never a fabricated probability) when no real ADP is
    known for this player. `gap_rounds` is how many ROUNDS past the
    current pick the player's real market ADP suggests they typically
    go; a logistic curve centered so a gap of zero rounds gives ~50%
    survival and each additional round past `picks_until_next_turn`
    (in round terms) raises survival probability, matching the intuitive
    real-world shape without claiming Monte-Carlo-grade precision."""
    if adp_expected_pick is None or team_count <= 0:
        return None
    gap_picks = adp_expected_pick - current_pick_number
    gap_rounds = gap_picks / team_count
    next_turn_rounds = picks_until_next_turn / team_count if team_count else 0.0
    centered = gap_rounds - next_turn_rounds
    # Logistic curve, disclosed steepness constant (not fit to any data).
    probability = 1.0 / (1.0 + math.exp(-1.5 * centered))
    return round(min(1.0, max(0.0, probability)), 4)


def evaluate_historical_candidates(
    state: HistoricalDecisionState,
    *,
    candidate_player_ids: Sequence[str],
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    provenance: ScoreProvenance,
    player_scores: Mapping[str, float] | None = None,
    picks_until_next_turn: int = 1,
    seasons: int = 200,
    base_seed: int = 20260903,
) -> DecisionBundle:
    """Produces a real DecisionBundle for a historical pick -- same
    dataclass shapes `decision_bundle_service` defines, computed via the
    real team_score()/championship_equity()/pick_score() functions on
    before/after roster states. Never consumes a realized outcome."""
    start = time.perf_counter()
    player_scores = player_scores or {}
    current_owner_ids = state.rosters_by_slot.get(state.owner_slot, ())
    default_slot = next(iter(comparable_leagues[0]))
    target_slot = state.owner_slot if state.owner_slot in comparable_leagues[0] else default_slot

    current_team = team_score(
        current_owner_ids, state.profile, state.ranking, state.manual_assets,
        comparable_leagues=comparable_leagues,
    )
    current_equity = championship_equity(
        current_owner_ids, state.profile, state.ranking, state.manual_assets,
        comparable_league=comparable_leagues[0], target_team_slot=target_slot,
        seasons=seasons, base_seed=base_seed,
    )

    adp_by_id = {entry.player_id: entry.expected_pick for entry in state.adp.entries}
    results: dict[str, tuple] = {}
    survival_by_id: dict[str, float | None] = {}
    for player_id in candidate_player_ids:
        after_ids = (*current_owner_ids, player_id)
        team_after = team_score(
            after_ids, state.profile, state.ranking, state.manual_assets,
            comparable_leagues=comparable_leagues,
        )
        equity_after = championship_equity(
            after_ids, state.profile, state.ranking, state.manual_assets,
            comparable_league=comparable_leagues[0], target_team_slot=target_slot,
            seasons=seasons, base_seed=base_seed,
        )
        results[player_id] = (team_after, equity_after)
        survival_by_id[player_id] = estimate_historical_survival_probability(
            adp_expected_pick=adp_by_id.get(player_id),
            current_pick_number=state.pick_number,
            team_count=state.profile.team_count,
            picks_until_next_turn=picks_until_next_turn,
        )

    scores = pick_score(results)
    candidates: list[CandidateBundle] = []
    for player_id, score in scores.items():
        survival = survival_by_id.get(player_id)
        cost_of_waiting = (
            round((1.0 - survival) * (score.team_score_after - current_team.percentile), 4)
            if survival is not None
            else score.cost_of_waiting
        )
        warnings: list[str] = []
        if player_id not in player_scores:
            warnings.append("No standalone Player Score supplied for this candidate.")
        if survival is None:
            warnings.append(
                "No real market ADP for this player -- make_it_back_probability is UNKNOWN, "
                "not estimated."
            )
        team_score_component = round(score.team_score_after - current_team.percentile, 4)
        equity_component = round(
            EQUITY_TO_PERCENTILE_WEIGHT
            * (score.championship_equity_after - current_equity.win_probability),
            4,
        )
        candidates.append(
            CandidateBundle(
                player_id=player_id,
                player_score=player_scores.get(player_id),
                team_score_after=score.team_score_after,
                team_score_delta=round(score.team_score_after - current_team.percentile, 2),
                championship_equity_after=score.championship_equity_after,
                equity_gain=score.equity_gain,
                cost_of_waiting=cost_of_waiting,
                make_it_back_probability=survival,
                # This service's survival estimate is an ADP-based heuristic,
                # not the live Monte Carlo simulation -- no real trial count
                # to disclose here.
                make_it_back_trials=None,
                raw_decision_utility=round(team_score_component + equity_component, 4),
                team_score_utility_component=team_score_component,
                equity_utility_component=equity_component,
                pick_score=score.relative_score,
                action="UNSCORED",  # historical Cost-of-Waiting is a disclosed heuristic, not
                # the live Draft Room's labeled decision taxonomy -- never mislabeled as one.
                warnings=tuple(warnings),
                uncertainty=(
                    "HISTORICAL_PROXY (Championship Equity SE="
                    f"{current_equity.standard_error:.4f}, "
                    f"survival heuristic {SURVIVAL_HEURISTIC_VERSION})"
                ),
            )
        )
    candidates.sort(key=lambda c: c.pick_score, reverse=True)

    elapsed = time.perf_counter() - start
    return DecisionBundle(
        version=HISTORICAL_DECISION_ENGINE_VERSION,
        current_team_score=current_team,
        current_championship_equity=current_equity,
        candidates=tuple(candidates),
        provenance=provenance,
        latency_seconds=round(elapsed, 4),
        simulation_metadata={
            "season": state.season, "pick_number": state.pick_number,
            "round_number": state.round_number, "seasons": seasons, "base_seed": base_seed,
            "candidate_count": len(candidates),
            "bridge_excluded_player_count": len(state.bridge_excluded_players),
        },
    )
