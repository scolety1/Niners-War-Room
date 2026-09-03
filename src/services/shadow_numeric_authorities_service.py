"""SHADOW / RESEARCH numeric authorities: Team Score, Championship Equity,
Pick Score, and a bounded look-ahead optimizer.

Everything in this module is explicitly RESEARCH_ONLY -- see
docs/codex/NUMERIC_AUTHORITIES_RESEARCH_V1.md for the prior design pass
and docs/codex/SHADOW_NUMERIC_AUTHORITIES_V1.md for what shipped here.
Nothing in this module is wired into production ranking, Suggestions, or
any owner-facing decision surface. No weight here was hand-picked and
called validated -- every number is either a direct reuse of an existing,
already-governed value (RedraftRankingRow.replacement_adjusted_value) or
the output of an actual Monte Carlo simulation, with disclosed
assumptions and a reported Monte Carlo error where applicable.

Reuse, not reinvention: the "comparable roster" population for Team Score
and the per-team rosters for Championship Equity both come from re-running
the real, already-tested run_complete_mock() CPU-vs-CPU draft simulator
(redraft_draft_room_v1_service.py) with different seeds -- not a separate,
parallel simulation engine.
"""

from __future__ import annotations

import random
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from src.services.redraft_draft_room_v1_service import AdpSnapshot, _asset_pool, run_complete_mock
from src.services.redraft_engine_v1_service import LeagueProfile, RankingResult

FLEX_ELIGIBLE = {"RB", "WR", "TE"}
TEAM_SCORE_LABEL = "TEAM SCORE — RESEARCH"
CHAMPIONSHIP_EQUITY_LABEL = "CHAMPIONSHIP EQUITY — SIMULATED RESEARCH"
PICK_SCORE_LABEL = "RESEARCH_ONLY_PICK_SCORE"
# Version identifiers for experiment freeze receipts (NWR PURE 001) --
# bump whenever the corresponding function's algorithm changes.
TEAM_SCORE_VERSION = "shadow-team-score-v1"
CHAMPIONSHIP_EQUITY_VERSION = "shadow-championship-equity-v1"
PICK_SCORE_VERSION = "shadow-pick-score-v1"
DEFAULT_TRIALS = 30
DEFAULT_SEED = 20260817


@dataclass(frozen=True)
class RosterPlayer:
    player_id: str
    position: str
    # Player Score proxy: replacement_adjusted_value, 0.0 for unmodeled (K/DST etc.) assets
    value: float


def _roster_players(
    player_ids: Sequence[str], pool: Mapping[str, Mapping[str, Any]]
) -> list[RosterPlayer]:
    players: list[RosterPlayer] = []
    for player_id in player_ids:
        asset = pool.get(player_id)
        if asset is None:
            continue
        value = asset.get("replacement_adjusted_value")
        players.append(
            RosterPlayer(
                player_id=player_id,
                position=str(asset.get("position") or ""),
                value=float(value) if value is not None else 0.0,
            )
        )
    return players


def optimal_starting_lineup_value(players: Sequence[RosterPlayer], profile: LeagueProfile) -> float:
    """Greedy starting-lineup assignment: fill each required position slot
    with the best-by-value player at that position, then fill FLEX (and
    superflex, if configured) with the best remaining FLEX-eligible
    players. This is a documented heuristic, not a proven globally-optimal
    assignment -- for the single-FLEX-type case it is standard and nearly
    always optimal in practice, but is not exhaustively verified against
    every possible roster shape.
    """
    remaining = sorted(players, key=lambda p: -p.value)
    slot_requirements: list[tuple[str, int]] = [
        ("QB", profile.roster.qb),
        ("RB", profile.roster.rb),
        ("WR", profile.roster.wr),
        ("TE", profile.roster.te),
        ("K", profile.roster.k),
        ("DST", profile.roster.dst),
    ]
    used_ids: set[str] = set()
    starters: list[RosterPlayer] = []
    for position, count in slot_requirements:
        if count <= 0:
            continue
        chosen = [p for p in remaining if p.position == position and p.player_id not in used_ids][
            :count
        ]
        starters.extend(chosen)
        used_ids.update(p.player_id for p in chosen)
    flex_needed = profile.roster.flex
    if flex_needed > 0:
        flex_pool = [
            p for p in remaining if p.player_id not in used_ids and p.position in FLEX_ELIGIBLE
        ][:flex_needed]
        starters.extend(flex_pool)
        used_ids.update(p.player_id for p in flex_pool)
    superflex_needed = profile.roster.superflex
    if superflex_needed > 0:
        superflex_eligible = FLEX_ELIGIBLE | {"QB"}
        superflex_pool = [
            p for p in remaining if p.player_id not in used_ids and p.position in superflex_eligible
        ][:superflex_needed]
        starters.extend(superflex_pool)
        used_ids.update(p.player_id for p in superflex_pool)
    return sum(p.value for p in starters)


def _rosters_from_mock_state(state: Mapping[str, Any], team_count: int) -> dict[int, list[str]]:
    rosters: dict[int, list[str]] = {slot: [] for slot in range(1, team_count + 1)}
    for pick in state.get("picks", []):
        if not pick.get("player_id"):
            continue
        rosters[int(pick["team_slot"])].append(str(pick["player_id"]))
    return rosters


def simulate_comparable_leagues(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    trials: int = DEFAULT_TRIALS,
    base_seed: int = DEFAULT_SEED,
) -> list[dict[int, list[RosterPlayer]]]:
    """`trials` full simulated leagues under this exact profile (team
    count, roster shape, K/DST handling) via run_complete_mock() with
    varying seed and owner_slot draw. Each element is {team_slot ->
    roster} for one complete simulated draft.
    """
    pool = _asset_pool(ranking, manual_assets)
    leagues: list[dict[int, list[RosterPlayer]]] = []
    for trial in range(trials):
        seed = base_seed + trial
        owner_slot = (trial % profile.team_count) + 1
        state = run_complete_mock(
            profile, ranking, manual_assets, adp, owner_slot=owner_slot, seed=seed
        )
        rosters = _rosters_from_mock_state(state, profile.team_count)
        leagues.append({slot: _roster_players(ids, pool) for slot, ids in rosters.items()})
    return leagues


@dataclass(frozen=True)
class TeamScoreResult:
    percentile: float  # 0-100
    roster_value: float
    population_size: int
    population_mean: float
    population_median: float
    population_stdev: float
    label: str = TEAM_SCORE_LABEL


def team_score(
    target_player_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
) -> TeamScoreResult:
    """Percentile strength of `target_player_ids`'s optimal starting
    lineup relative to every team's optimal starting lineup across
    `comparable_leagues` (real simulated leagues under this exact league
    format -- see simulate_comparable_leagues). ~50 means the roster's
    modeled strength is in the middle of the simulated distribution for
    this format, by construction of the population rather than by a
    hand-picked normalization constant.
    """
    pool = _asset_pool(ranking, manual_assets)
    target_players = _roster_players(target_player_ids, pool)
    roster_value = optimal_starting_lineup_value(target_players, profile)
    population = [
        optimal_starting_lineup_value(roster, profile)
        for league in comparable_leagues
        for roster in league.values()
    ]
    if not population:
        raise ValueError("No comparable-league simulation population available.")
    below = sum(1 for value in population if value < roster_value)
    percentile = 100.0 * below / len(population)
    return TeamScoreResult(
        percentile=round(percentile, 1),
        roster_value=round(roster_value, 2),
        population_size=len(population),
        population_mean=round(statistics.fmean(population), 2),
        population_median=round(statistics.median(population), 2),
        population_stdev=round(statistics.pstdev(population), 2) if len(population) > 1 else 0.0,
    )


@dataclass(frozen=True)
class ChampionshipEquityAssumptions:
    regular_season_weeks: int = 14
    playoff_teams: int = 4
    playoff_rounds: int = 2
    weekly_noise_stdev_fraction: float = 0.18
    note: str = (
        "Regular-season standing is by simulated total points, not a real "
        "matchup-by-matchup win/loss schedule; playoffs are single-elimination "
        "seeded by that point total. These are disclosed simplifying "
        "assumptions, not the league's actual configured schedule/format "
        "(which this profile does not carry)."
    )


@dataclass(frozen=True)
class ChampionshipEquityResult:
    win_probability: float  # 0.0-1.0
    standard_error: float  # Monte Carlo standard error of the estimate
    seasons_simulated: int
    league_size: int
    assumptions: ChampionshipEquityAssumptions = field(
        default_factory=ChampionshipEquityAssumptions
    )
    label: str = CHAMPIONSHIP_EQUITY_LABEL


def _simulate_one_season_winner(
    weekly_means: Mapping[int, float],
    assumptions: ChampionshipEquityAssumptions,
    rng: random.Random,
) -> int:
    totals = dict.fromkeys(weekly_means, 0.0)
    for _week in range(assumptions.regular_season_weeks):
        for slot, mean_value in weekly_means.items():
            totals[slot] += rng.gauss(
                mean_value, mean_value * assumptions.weekly_noise_stdev_fraction
            )
    seeded = sorted(totals, key=lambda slot: -totals[slot])[: assumptions.playoff_teams]
    survivors = list(seeded)
    for _round in range(assumptions.playoff_rounds):
        if len(survivors) < 2:
            break
        next_round = []
        for i in range(0, len(survivors) - 1, 2):
            a, b = survivors[i], survivors[i + 1]
            a_score = rng.gauss(
                weekly_means[a], weekly_means[a] * assumptions.weekly_noise_stdev_fraction
            )
            b_score = rng.gauss(
                weekly_means[b], weekly_means[b] * assumptions.weekly_noise_stdev_fraction
            )
            next_round.append(a if a_score >= b_score else b)
        survivors = next_round
    return survivors[0] if survivors else seeded[0]


def championship_equity(
    target_player_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    comparable_league: Mapping[int, list[RosterPlayer]],
    target_team_slot: int = 1,
    seasons: int = 300,
    base_seed: int = DEFAULT_SEED,
    assumptions: ChampionshipEquityAssumptions | None = None,
) -> ChampionshipEquityResult:
    """P(win this league) for `target_player_ids`, inserted at
    `target_team_slot` into one real simulated `comparable_league` (the
    other team_count-1 rosters, from simulate_comparable_leagues), with
    the rest of that league's draft outcome held fixed and only the
    weekly/playoff simulation randomized across `seasons` trials.
    """
    assumptions = assumptions or ChampionshipEquityAssumptions()
    pool = _asset_pool(ranking, manual_assets)
    target_players = _roster_players(target_player_ids, pool)
    target_value = optimal_starting_lineup_value(target_players, profile)
    weekly_means: dict[int, float] = {
        target_team_slot: target_value / max(1, assumptions.regular_season_weeks)
    }
    for slot, roster in comparable_league.items():
        if slot == target_team_slot:
            continue
        weekly_means[slot] = optimal_starting_lineup_value(roster, profile) / max(
            1, assumptions.regular_season_weeks
        )
    rng = random.Random(base_seed)
    wins = sum(
        1
        for _ in range(seasons)
        if _simulate_one_season_winner(weekly_means, assumptions, rng) == target_team_slot
    )
    probability = wins / seasons
    # Binomial standard error of a Monte Carlo proportion estimate.
    standard_error = (probability * (1 - probability) / seasons) ** 0.5
    return ChampionshipEquityResult(
        win_probability=round(probability, 4),
        standard_error=round(standard_error, 4),
        seasons_simulated=seasons,
        league_size=len(weekly_means),
        assumptions=assumptions,
    )


@dataclass(frozen=True)
class PickScoreResult:
    relative_score: float  # 0-100 within the evaluated candidate set only
    team_score_after: float
    championship_equity_after: float
    equity_gain: float  # vs. doing nothing (best remaining alternative left for the room)
    cost_of_waiting: float  # expected loss from passing this candidate now
    label: str = PICK_SCORE_LABEL


def cost_of_waiting(
    candidate_team_score_after: float,
    best_alternative_team_score_after: float,
) -> float:
    """Expected roster-quality loss from passing this candidate now,
    approximated as the Team Score gap to the next-best actionable
    alternative at this exact pick. A structural placeholder for the full
    make-it-back-probability-weighted version in
    docs/codex/NUMERIC_AUTHORITIES_RESEARCH_V1.md -- not yet using ADP
    survival probability, so treat as a lower bound, not the final number.
    """
    return round(max(0.0, candidate_team_score_after - best_alternative_team_score_after), 2)


def pick_score(
    candidate_results: Mapping[str, tuple[TeamScoreResult, ChampionshipEquityResult]],
) -> dict[str, PickScoreResult]:
    """Maps each candidate's (Team Score, Championship Equity) after
    taking it to a 0-100 score RELATIVE TO THE OTHER CANDIDATES EVALUATED
    IN THIS CALL ONLY (100 = strongest of this set, 0 = weakest, 50 =
    middle) -- not a calibrated absolute probability of anything. See
    PICK_SCORE_LABEL: this is RESEARCH_ONLY until historical/prospective
    calibration exists (docs/codex/NUMERIC_AUTHORITIES_RESEARCH_V1.md).
    """
    if not candidate_results:
        return {}
    team_scores = {pid: team.percentile for pid, (team, _) in candidate_results.items()}
    equities = {pid: equity.win_probability for pid, (_, equity) in candidate_results.items()}
    best_equity = max(equities.values())
    worst_equity = min(equities.values())
    spread = best_equity - worst_equity
    out: dict[str, PickScoreResult] = {}
    for player_id, (team, equity) in candidate_results.items():
        others = [value for pid, value in team_scores.items() if pid != player_id]
        best_alternative = max(others) if others else team.percentile
        relative = 100.0 * (equity.win_probability - worst_equity) / spread if spread > 0 else 50.0
        out[player_id] = PickScoreResult(
            relative_score=round(relative, 1),
            team_score_after=team.percentile,
            championship_equity_after=equity.win_probability,
            equity_gain=round(equity.win_probability - worst_equity, 4),
            cost_of_waiting=cost_of_waiting(team.percentile, best_alternative),
        )
    return out


# --- Bounded look-ahead (section 12) ---
# At each candidate: force it as the owner's next pick, then let the rest
# of the draft (opponents AND the owner's own later picks) complete via
# the same, already-tested run_complete_mock() machinery (CPU market-ADP
# behavior when available, deterministic NWR-order/auto-score fallback
# otherwise). This is ONE plausible continuation per candidate -- not an
# exhaustive search over every future owner decision, which the brief
# this serves explicitly says not to brute-force. Candidates should be
# pre-filtered by the caller to actionable ones (e.g. _roster_candidate_allowed
# from redraft_draft_room_v1_service, the same position-max legality rule
# Suggestions already applies) before calling this.


def simulate_pick_now(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    candidate_player_id: str,
    seed: int = DEFAULT_SEED,
    from_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Force `candidate_player_id` as the very next owner selection (from
    `from_state`, or an empty draft if not given), then complete the rest
    of the draft with the same market/auto-score logic run_complete_mock()
    uses. Returns the full completed room state.
    """
    from src.services.redraft_draft_room_v1_service import (
        _complete,
        _current_team,
        _record_pick,
        _select_asset,
    )

    state: dict[str, Any] = (
        dict(from_state)
        if from_state is not None
        else {
            "schema_version": 1,
            "profile_id": profile.profile_id,
            "owner_slot": owner_slot,
            "seed": seed,
            "speed": "FAST",
            "mode": "MOCK",
            "drafted": [],
            "picks": [],
            "updated_at_utc": "",
        }
    )
    pool = _asset_pool(ranking, manual_assets)
    forced_pending = True
    while not _complete(profile, state):
        team_slot = _current_team(profile, state)
        if team_slot == owner_slot and forced_pending:
            asset = pool.get(candidate_player_id)
            if asset is None:
                raise ValueError(f"{candidate_player_id!r} is not a draftable asset.")
            if candidate_player_id in state.get("drafted", []):
                raise ValueError(f"{candidate_player_id!r} is already drafted.")
            state = _record_pick(
                profile, state, asset, actor="CANDIDATE_LOOKAHEAD", behavior="FORCED_CANDIDATE"
            )
            forced_pending = False
            continue
        actor = "OWNER_AUTO_TEST" if team_slot == owner_slot else "CPU"
        asset, behavior = _select_asset(profile, ranking, adp, state, pool, team_slot, actor)
        state = _record_pick(profile, state, asset, actor=actor, behavior=behavior)
    return state


@dataclass(frozen=True)
class CandidateEvaluation:
    player_id: str
    team_score_result: TeamScoreResult
    championship_equity_result: ChampionshipEquityResult


def evaluate_pick_candidates(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    candidate_player_ids: Sequence[str],
    from_state: Mapping[str, Any] | None = None,
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]] | None = None,
    trials: int = DEFAULT_TRIALS,
    seasons: int = 200,
    base_seed: int = DEFAULT_SEED,
) -> dict[str, PickScoreResult]:
    """The full look-ahead pipeline for one pick: for every candidate,
    simulate_pick_now() to get a completed final roster, score it with
    team_score()/championship_equity() against a shared comparable-league
    population (computed once, reused across every candidate -- this is
    the 'cache/precompute reusable components' the brief allows when full
    per-candidate resimulation would be too slow), then rank all
    candidates against each other with pick_score().
    """
    leagues = comparable_leagues or simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=trials, base_seed=base_seed
    )
    results: dict[str, tuple[TeamScoreResult, ChampionshipEquityResult]] = {}
    for candidate in candidate_player_ids:
        final_state = simulate_pick_now(
            profile,
            ranking,
            manual_assets,
            adp,
            owner_slot=owner_slot,
            candidate_player_id=candidate,
            seed=base_seed,
            from_state=from_state,
        )
        owner_player_ids = [
            str(pick["player_id"])
            for pick in final_state["picks"]
            if int(pick["team_slot"]) == owner_slot and pick.get("player_id")
        ]
        team = team_score(
            owner_player_ids, profile, ranking, manual_assets, comparable_leagues=leagues
        )
        equity = championship_equity(
            owner_player_ids,
            profile,
            ranking,
            manual_assets,
            comparable_league=leagues[0],
            target_team_slot=owner_slot if owner_slot in leagues[0] else next(iter(leagues[0])),
            seasons=seasons,
            base_seed=base_seed,
        )
        results[candidate] = (team, equity)
    return pick_score(results)
