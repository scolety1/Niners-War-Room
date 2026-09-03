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
from dataclasses import dataclass, field, replace
from typing import Any

from src.services.ai_intelligence_backend_service import ImpactHypothesis
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


def _select_starting_lineup(
    players: Sequence[RosterPlayer], profile: LeagueProfile
) -> tuple[list[RosterPlayer], tuple[str, ...]]:
    """Shared greedy starter-selection: fill each required position slot
    with the best-by-value player at that position, then fill FLEX (and
    superflex, if configured) with the best remaining FLEX-eligible
    players. This is a documented heuristic, not a proven globally-optimal
    assignment -- for the single-FLEX-type case it is standard and nearly
    always optimal in practice (see
    test_optimal_starting_lineup_value_matches_brute_force_on_small_rosters
    for an empirical check against exhaustive search), but is not
    exhaustively verified against every possible roster shape.

    Returns (chosen starters, unmet-requirement labels) -- the labels are
    used by roster_composition_report() to surface real starter holes
    rather than silently under-filling a lineup.
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
    holes: list[str] = []
    for position, count in slot_requirements:
        if count <= 0:
            continue
        available = [p for p in remaining if p.position == position and p.player_id not in used_ids]
        chosen = available[:count]
        starters.extend(chosen)
        used_ids.update(p.player_id for p in chosen)
        if len(chosen) < count:
            holes.append(f"{position} {len(chosen)}/{count}")
    flex_needed = profile.roster.flex
    if flex_needed > 0:
        flex_pool = [
            p for p in remaining if p.player_id not in used_ids and p.position in FLEX_ELIGIBLE
        ][:flex_needed]
        starters.extend(flex_pool)
        used_ids.update(p.player_id for p in flex_pool)
        if len(flex_pool) < flex_needed:
            holes.append(f"FLEX {len(flex_pool)}/{flex_needed}")
    superflex_needed = profile.roster.superflex
    if superflex_needed > 0:
        superflex_eligible = FLEX_ELIGIBLE | {"QB"}
        superflex_pool = [
            p for p in remaining if p.player_id not in used_ids and p.position in superflex_eligible
        ][:superflex_needed]
        starters.extend(superflex_pool)
        used_ids.update(p.player_id for p in superflex_pool)
        if len(superflex_pool) < superflex_needed:
            holes.append(f"SUPERFLEX {len(superflex_pool)}/{superflex_needed}")
    return starters, tuple(holes)


def optimal_starting_lineup_value(players: Sequence[RosterPlayer], profile: LeagueProfile) -> float:
    """Greedy starting-lineup value -- see _select_starting_lineup for the
    selection algorithm this reports on."""
    starters, _holes = _select_starting_lineup(players, profile)
    return sum(p.value for p in starters)


@dataclass(frozen=True)
class RosterCompositionReport:
    """Diagnostic beyond a single Team Score percentile: which starter
    slots this roster cannot currently fill, how much value its bench
    provides as depth/bye-week/injury insurance, and how many rostered
    players at each position exceed what starters+FLEX can even use.
    Built directly on _select_starting_lineup's own selection -- this is
    a report on that selection, not a second, competing lineup algorithm.
    """

    starter_holes: tuple[str, ...]
    starting_lineup_value: float
    bench_contingency_value: float
    total_roster_value: float
    position_redundancy: Mapping[str, int]


def roster_composition_report(
    players: Sequence[RosterPlayer], profile: LeagueProfile
) -> RosterCompositionReport:
    starters, holes = _select_starting_lineup(players, profile)
    starter_ids = {p.player_id for p in starters}
    bench = sorted(
        (p for p in players if p.player_id not in starter_ids), key=lambda p: -p.value
    )[: max(0, profile.roster.bench_size)]
    flex_needed = profile.roster.flex
    superflex_needed = profile.roster.superflex
    position_starter_slots = {
        "QB": profile.roster.qb,
        "RB": profile.roster.rb,
        "WR": profile.roster.wr,
        "TE": profile.roster.te,
    }
    redundancy: dict[str, int] = {}
    for position, required in position_starter_slots.items():
        rostered = sum(1 for p in players if p.position == position)
        usable = required
        if position in FLEX_ELIGIBLE:
            usable += flex_needed
        if position in FLEX_ELIGIBLE | {"QB"}:
            usable += superflex_needed
        redundancy[position] = max(0, rostered - usable)
    return RosterCompositionReport(
        starter_holes=holes,
        starting_lineup_value=round(sum(p.value for p in starters), 2),
        bench_contingency_value=round(sum(p.value for p in bench), 2),
        total_roster_value=round(sum(p.value for p in players), 2),
        position_redundancy=redundancy,
    )


def availability_discount_for_hypotheses(
    player_id: str, impact_hypotheses: Sequence[ImpactHypothesis]
) -> float:
    """A value multiplier in [0.0, 1.0] driven ONLY by an existing
    HIGH-confidence NEGATIVE Impact Analyst hypothesis about this exact
    player (ai_intelligence_backend_service.py's own disclosed rule
    table -- not a new invented severity model). Anything else (MEDIUM/
    LOW confidence, UNCERTAIN direction, or no hypothesis at all) returns
    1.0 -- no discount without a real, already-computed, high-confidence
    structural signal."""
    for hypothesis in impact_hypotheses:
        if hypothesis.subject_player_id != player_id:
            continue
        if hypothesis.direction == "NEGATIVE" and hypothesis.confidence == "HIGH":
            return 0.0
    return 1.0


def availability_adjusted_players(
    players: Sequence[RosterPlayer], impact_hypotheses: Sequence[ImpactHypothesis]
) -> list[RosterPlayer]:
    """Applies availability_discount_for_hypotheses to every player.
    Callers pass the result into optimal_starting_lineup_value/team_score/
    roster_composition_report in place of the raw player list -- those
    functions themselves stay unaware of Impact Analyst hypotheses,
    keeping the "status availability" concern in one place."""
    if not impact_hypotheses:
        return list(players)
    return [
        replace(
            player,
            value=player.value * availability_discount_for_hypotheses(
                player.player_id, impact_hypotheses
            ),
        )
        for player in players
    ]


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


# --- Cost of Waiting V2 (section 15) ------------------------------------
# V1's cost_of_waiting() above is an explicitly-labeled lower bound: the
# Team Score gap to the best alternative, with no weighting for whether
# the candidate would actually still be there if the owner waited. V2
# layers an empirical, Monte Carlo survival probability on top of that
# same gap -- estimated by re-running the real CPU market-ADP simulator
# (_advance_cpu / _select_asset, redraft_draft_room_v1_service.py) across
# several seeds, exactly the same reuse-the-real-simulator approach Team
# Score and Championship Equity already use. Not a closed-form/normal-
# distribution ADP model.
COST_OF_WAITING_V2_VERSION = "shadow-cost-of-waiting-v2"
COST_OF_WAITING_V2_LABEL = "COST_OF_WAITING_V2 — RESEARCH (Monte Carlo survival-weighted)"


def candidate_survival_probability(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    state: Mapping[str, Any],
    *,
    owner_slot: int,
    candidate_player_id: str,
    alternative_player_id: str,
    trials: int = DEFAULT_TRIALS,
    base_seed: int = DEFAULT_SEED,
) -> float:
    """Empirical probability `candidate_player_id` is still undrafted when
    it becomes the owner's next turn, given the owner takes
    `alternative_player_id` right now instead. Estimated across `trials`
    independently-seeded re-runs of the real CPU-only advance between
    picks (_advance_cpu with stop_at_owner=True) -- never mutates the
    caller's `state`. If the candidate or alternative is already
    unavailable, returns 1.0 (nothing left to lose by waiting) as the
    honest structural answer rather than a fabricated number; if the
    draft is already complete at `state`, likewise 1.0 (there is no next
    owner turn to wait for)."""
    from src.services.redraft_draft_room_v1_service import (
        _advance_cpu,
        _asset_pool,
        _complete,
        _record_pick,
    )

    drafted = set(state.get("drafted", []))
    pool = _asset_pool(ranking, manual_assets)
    alternative_asset = pool.get(alternative_player_id)
    if (
        alternative_asset is None
        or candidate_player_id not in pool
        or candidate_player_id in drafted
        or alternative_player_id in drafted
        or _complete(profile, state)
    ):
        return 1.0
    survived = 0
    trial_count = max(1, trials)
    for trial in range(trial_count):
        trial_state: dict[str, Any] = {**dict(state), "seed": base_seed + trial}
        trial_state = _record_pick(
            profile,
            trial_state,
            alternative_asset,
            actor="OWNER_SIMULATED_ALTERNATIVE",
            behavior="COST_OF_WAITING_V2_TRIAL",
        )
        trial_state = _advance_cpu(
            profile, ranking, manual_assets, adp, trial_state, stop_at_owner=True
        )
        if candidate_player_id not in trial_state.get("drafted", []):
            survived += 1
    return round(survived / trial_count, 4)


@dataclass(frozen=True)
class CostOfWaitingV2Result:
    candidate_player_id: str
    best_alternative_player_id: str
    survival_probability: float
    trials: int
    value_gap: float  # V1's plain Team-Score-gap lower bound, kept for transparency
    expected_cost: float  # (1 - survival_probability) * value_gap
    label: str = COST_OF_WAITING_V2_LABEL


def evaluate_cost_of_waiting_v2(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    candidate_player_ids: Sequence[str],
    pick_scores: Mapping[str, PickScoreResult],
    from_state: Mapping[str, Any] | None = None,
    trials: int = DEFAULT_TRIALS,
    base_seed: int = DEFAULT_SEED,
) -> dict[str, CostOfWaitingV2Result]:
    """Layers survival-weighting on top of evaluate_pick_candidates()'s own
    pick_score() output -- additive transparency, not a competing concept.
    For each candidate, 'the best alternative' is whichever OTHER
    evaluated candidate has the highest team_score_after, matching
    pick_score()'s own definition exactly. Candidates not present in
    `pick_scores`, or with no other evaluated candidate to compare
    against, are skipped rather than guessed."""
    state = from_state or {
        "schema_version": 1,
        "profile_id": profile.profile_id,
        "owner_slot": owner_slot,
        "seed": base_seed,
        "speed": "FAST",
        "mode": "MOCK",
        "drafted": [],
        "picks": [],
        "updated_at_utc": "",
    }
    out: dict[str, CostOfWaitingV2Result] = {}
    for candidate in candidate_player_ids:
        score = pick_scores.get(candidate)
        if score is None:
            continue
        others = {
            pid: other.team_score_after for pid, other in pick_scores.items() if pid != candidate
        }
        if not others:
            continue
        alternative = max(others, key=lambda pid: others[pid])
        survival = candidate_survival_probability(
            profile,
            ranking,
            manual_assets,
            adp,
            state,
            owner_slot=owner_slot,
            candidate_player_id=candidate,
            alternative_player_id=alternative,
            trials=trials,
            base_seed=base_seed,
        )
        expected = round((1.0 - survival) * score.cost_of_waiting, 2)
        out[candidate] = CostOfWaitingV2Result(
            candidate_player_id=candidate,
            best_alternative_player_id=alternative,
            survival_probability=survival,
            trials=trials,
            value_gap=score.cost_of_waiting,
            expected_cost=expected,
        )
    return out


# Disclosed threshold labels -- section 11: distinguish "NWR likes this
# player" (an individually solid replacement_adjusted_value/rank) from
# "spend this pick on him now" (real market-survival-weighted urgency).
# Driven entirely by already-computed cost_of_waiting_v2 fields plus real
# ADP, RELATIVE TO THE SAME EVALUATED CANDIDATE SET -- matching Pick
# Score's own "relative to the other candidates evaluated in this call
# only" philosophy, not a new absolute-threshold concept, with the one
# exception of WAIVER_WATCH (driven purely by real ADP margin: a player
# realistically many rounds past where a redraft league's bench even
# reaches). Thresholds are disclosed here, not hand-tuned per player.
PICK_DECISION_LABELS = frozenset(
    {"TAKE_NOW", "GOOD_VALUE", "WAIT", "DEEP_TARGET", "WAIVER_WATCH"}
)
WAIVER_WATCH_ROUNDS_PAST_CURRENT = 8.0
DEEP_TARGET_ROUNDS_PAST_CURRENT = 2.0
DEEP_TARGET_SURVIVAL_THRESHOLD = 0.85
WAIT_SURVIVAL_THRESHOLD = 0.6
TAKE_NOW_RELATIVE_COST_FRACTION = 0.5


def label_pick_decisions(
    results: Mapping[str, CostOfWaitingV2Result],
    *,
    adp_expected_pick_by_id: Mapping[str, float | None],
    current_pick_number: int,
    team_count: int,
) -> dict[str, str]:
    """Maps each evaluate_cost_of_waiting_v2() result to one of
    PICK_DECISION_LABELS. See module comment above this constant block
    for the exact, disclosed rule -- summarized:
      WAIVER_WATCH: real ADP says this player is realistically more than
        WAIVER_WATCH_ROUNDS_PAST_CURRENT rounds away (or off the board
        entirely) -- not worth a roster spot at this point in the draft,
        regardless of survival probability.
      DEEP_TARGET: real ADP margin exceeds DEEP_TARGET_ROUNDS_PAST_CURRENT
        rounds AND survival_probability is high -- safe to wait multiple
        rounds and still land him.
      WAIT: survival_probability alone is high enough that passing this
        pick carries little real risk of losing the player.
      TAKE_NOW: this candidate's expected_cost is at least
        TAKE_NOW_RELATIVE_COST_FRACTION of the largest expected_cost in
        this evaluated set -- real, material risk of losing real value
        by waiting, relative to the alternatives actually on the table.
      GOOD_VALUE: everything else -- some risk, but not the largest in
        this set; a reasonable, non-urgent pick.
    """
    max_cost = max((result.expected_cost for result in results.values()), default=0.0)
    labels: dict[str, str] = {}
    for player_id, result in results.items():
        adp_expected_pick = adp_expected_pick_by_id.get(player_id)
        if adp_expected_pick is not None:
            rounds_past_current = (adp_expected_pick - current_pick_number) / max(1, team_count)
            if rounds_past_current > WAIVER_WATCH_ROUNDS_PAST_CURRENT:
                labels[player_id] = "WAIVER_WATCH"
                continue
            if (
                rounds_past_current > DEEP_TARGET_ROUNDS_PAST_CURRENT
                and result.survival_probability > DEEP_TARGET_SURVIVAL_THRESHOLD
            ):
                labels[player_id] = "DEEP_TARGET"
                continue
        if result.survival_probability > WAIT_SURVIVAL_THRESHOLD:
            labels[player_id] = "WAIT"
        elif max_cost > 0 and result.expected_cost >= TAKE_NOW_RELATIVE_COST_FRACTION * max_cost:
            labels[player_id] = "TAKE_NOW"
        else:
            labels[player_id] = "GOOD_VALUE"
    return labels


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
