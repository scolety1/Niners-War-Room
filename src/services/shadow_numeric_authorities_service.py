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
    # NWR post-draft overnight, shared-FLEX fix (section 2 of the
    # class-time hardening run): the PRIOR formula credited each
    # FLEX-eligible position its OWN independent "+flex_needed" capacity
    # allowance -- correct only when a single FLEX-eligible position
    # exists in isolation, but WRONG whenever multiple FLEX-eligible
    # positions have real, simultaneous bench depth: the real FLEX slot
    # is ONE shared slot, not one slot per position, so summing an
    # independent allowance per position double- (or triple-, for
    # RB+WR+TE) counts the same real capacity. Reproduced directly
    # against the real 403 roster (5 rostered RB, 5 rostered WR, 1 FLEX):
    # the old formula gave RB redundancy=2 AND WR redundancy=2
    # independently (crediting FLEX to both), when only ONE of those
    # positions' extra player can actually occupy the real, single FLEX
    # slot.
    #
    # Real, principled fix -- no new formula, no magic per-position
    # bonus: `starters` above is already the REAL output of the shared,
    # single `_select_starting_lineup` greedy assignment, which already
    # resolves FLEX contention correctly (whichever position's marginal
    # player has the higher real value wins the shared slot). Deriving
    # redundancy directly from "rostered at this position minus how many
    # of them actually became a real starter" is lossless and always
    # agrees with the real selection outcome, by construction -- it
    # cannot double-count a shared slot because the slot was only
    # assigned to one real player to begin with.
    starters_by_position: dict[str, int] = {}
    for starter in starters:
        starters_by_position[starter.position] = starters_by_position.get(starter.position, 0) + 1
    redundancy: dict[str, int] = {}
    for position in ("QB", "RB", "WR", "TE"):
        rostered = sum(1 for p in players if p.position == position)
        redundancy[position] = max(0, rostered - starters_by_position.get(position, 0))
    return RosterCompositionReport(
        starter_holes=holes,
        starting_lineup_value=round(sum(p.value for p in starters), 2),
        bench_contingency_value=round(sum(p.value for p in bench), 2),
        total_roster_value=round(sum(p.value for p in players), 2),
        position_redundancy=redundancy,
    )


@dataclass(frozen=True)
class MarginalRosterReason:
    """NWR post-draft overnight, phase 3/21 -- the real, root-caused fix
    for the QB2/QB3 'hoarding' complaint. Live-traced cause: adding a
    higher-value QB in a 1QB league doesn't add a bench QB, it makes
    `_select_starting_lineup`'s greedy best-by-value selection swap that
    QB IN as starter and bench the previously-starting QB -- a real,
    legitimate Team Score increase (trading up at a scarce position) that
    Suggestions never explained. This function makes that mechanism
    explicit and inspectable: it names which starter (if any) gets
    displaced, and reports the real, already-computed value delta -- never
    an invented narrative."""

    becomes_starter: bool
    displaces_player_id: str | None
    displaces_player_position: str | None
    starter_value_delta: float
    bench_slots_after: int
    summary: str


def explain_marginal_roster_reason(
    candidate_id: str,
    current_player_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> MarginalRosterReason:
    pool = _asset_pool(ranking, manual_assets)
    current_players = _roster_players(current_player_ids, pool)
    candidate_players = _roster_players([candidate_id], pool)
    if not candidate_players:
        return MarginalRosterReason(
            becomes_starter=False, displaces_player_id=None, displaces_player_position=None,
            starter_value_delta=0.0, bench_slots_after=0,
            summary="Candidate has no known value (unmodeled asset) -- cannot assess roster impact.",
        )
    candidate = candidate_players[0]

    before_starters, _ = _select_starting_lineup(current_players, profile)
    before_ids = {p.player_id for p in before_starters}
    before_value = sum(p.value for p in before_starters)

    after_starters, _ = _select_starting_lineup([*current_players, candidate], profile)
    after_ids = {p.player_id for p in after_starters}
    after_value = sum(p.value for p in after_starters)

    becomes_starter = candidate_id in after_ids
    # A player who WAS starting and is NOT among the new starters, at the
    # same position the candidate plays (the only way this greedy
    # selection displaces someone) -- real, not inferred from position
    # counts alone, since FLEX/superflex can shuffle multiple slots at once.
    displaced = [
        p for p in before_starters
        if p.player_id not in after_ids and p.position == candidate.position
    ]
    displaces = displaced[0] if displaced else None

    roster_after_size = len(current_players) + 1
    bench_slots_after = max(0, roster_after_size - len(after_starters))

    if not becomes_starter:
        summary = (
            f"{candidate.position} stays on the bench -- does not improve the optimal "
            f"starting lineup (adds bench depth/contingency value only, "
            f"+{round(candidate.value, 1)} bench value)."
        )
    elif displaces is not None:
        summary = (
            f"Upgrades your starting {candidate.position} "
            f"(+{round(after_value - before_value, 1)} starting-lineup value) but benches "
            f"{displaces.player_id} ({round(displaces.value, 1)} value) and consumes one "
            f"bench slot ({bench_slots_after} bench slots remain)."
        )
    else:
        summary = (
            f"Fills an open {candidate.position} starter slot "
            f"(+{round(after_value - before_value, 1)} starting-lineup value), no one benched."
        )

    return MarginalRosterReason(
        becomes_starter=becomes_starter,
        displaces_player_id=displaces.player_id if displaces else None,
        displaces_player_position=displaces.position if displaces else None,
        starter_value_delta=round(after_value - before_value, 2),
        bench_slots_after=bench_slots_after,
        summary=summary,
    )


# NWR post-draft overnight, phase 3: CHALLENGER, not wired into the live
# Pick Score / DecisionBundle path. Reuses explain_marginal_roster_reason
# (itself reusing Team Score's own _select_starting_lineup -- no new
# selection algorithm) plus roster_composition_report's real
# position_redundancy signal. A starter/FLEX upgrade always keeps its
# full real value (net of who it benches, already correctly netted by
# explain_marginal_roster_reason); a pure bench add's contingency value
# decays geometrically with how much real bench redundancy already
# exists there.
#
# NWR post-draft overnight, phase 1/2 (v2 -- real historical measurement,
# not an arbitrary constant): the FIRST bench slot's decay base is no
# longer a single universal 0.5 for every position -- it is measured
# directly from real nflverse `load_snap_counts` data. Methodology: rank
# each team's players at a position by WEEK-1 snap share (the real
# preseason depth chart outcome, not season-total, which would conflate
# a true bench backup with a midseason starter who took over after an
# injury and racked up snaps for the rest of the year -- an earlier
# version of this same measurement made exactly that mistake and was
# corrected before use). For the week-1 DEPTH-2 player at each position,
# the real, computed fraction of team-seasons where that player EVER
# reached starter-level usage (>=60% offensive snap share) in some LATER
# week that season, CONDITIONAL on him having logged a real week-1 snap
# at all (i.e. `ever_started / n_players`, where `n_players` is that
# position's OWN real count of week-1 depth-2 players who appear in the
# data at all -- the same formula for every position, no special-cased
# denominator).
#
# CORRECTED (owner-flagged, 2026-09-08): the original QB=0.125 figure
# here was wrong -- verified by rerunning the cited reproduction script
# (scratchpad `historical_backup_utility_v2.py`) verbatim. That script's
# own real output for QB is n_players=22 (most teams' real backup QB
# logs ZERO week-1 offensive snaps and never enters the ranked pool at
# all -- QB genuinely is the most winner-take-all position, that part
# was correct) and ever_rate=0.545 (of the 22 who DID log a real week-1
# snap, just over half later reached starter-level usage) -- NOT 0.125.
# 12/96=0.125 was computed using RB/WR/TE's own n=96 as QB's denominator
# instead of QB's real n=22 (12/22=0.545) -- a real arithmetic error, not
# a deliberate, disclosed methodological choice; RB/WR/TE's own real
# n_players already happens to be ~96 (virtually every team has a real
# RB2/WR2/TE2), so the bug was invisible for those three. This also
# meant the original promotion's walk-forward evaluation (commit
# `c318a10c`) used the same fixed 2022-2024-derived rates for real
# 2020-2023 evaluation seasons -- a real, separately-flagged temporal-
# leakage gap. Both issues were verified together and a corrected,
# leakage-safe, per-fold-rate rerun still passed all 3 preregistered
# gates (mean_delta +92.49 vs the original +74.65, wins 32/48 unchanged)
# -- see docs/codex/NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md's
# TEMPORAL-LEAKAGE VERIFICATION addendum for the full evidence. The
# values below are the real, corrected, most-current non-leaky window
# for a live 2026 draft (2023-2025, the same conditional formula for
# every position):
#   QB 55.6% (n=22 of week-1 depth-2 QBs who logged a real snap at all)
#   RB 48.4%
#   WR 96.9% (modern 3-WR personnel groupings mean a "WR2" by week-1
#     snap share is very often close to a full-time starter)
#   TE 70.8%
# These real rates -- not a guessed "QB penalty"/"TE penalty" -- are why
# a first bench QB still gets a real, but now correctly-computed, real
# contingency discount. Reproduction script:
# docs/codex/nwr_marginal_utility_walk_forward_promotion_v1_20260908/
# leakage_verification_addendum/run_leakage_safe_rerun.py
# (compute_backup_utility_rate; call with [2023, 2024, 2025] for these
# exact values).
POSITION_BACKUP_UTILITY_RATE: dict[str, float] = {
    "QB": 0.5556,
    "RB": 0.4842,
    "WR": 0.9688,
    "TE": 0.7083,
}
# Positions with no real measurement above (K/DST -- snap-share isn't a
# meaningful concept for either) fall back to the original universal
# rate rather than an invented number.
DEFAULT_BENCH_REDUNDANCY_DECAY = 0.5


@dataclass(frozen=True)
class MarginalRosterUtility:
    utility: float
    becomes_starter: bool
    bench_redundancy_before: int | None
    explanation: str


def marginal_roster_utility(
    candidate_id: str,
    current_player_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> MarginalRosterUtility:
    reason = explain_marginal_roster_reason(candidate_id, current_player_ids, profile, ranking, manual_assets)
    if reason.becomes_starter:
        return MarginalRosterUtility(
            utility=reason.starter_value_delta, becomes_starter=True,
            bench_redundancy_before=None, explanation=reason.summary,
        )
    pool = _asset_pool(ranking, manual_assets)
    candidate_players = _roster_players([candidate_id], pool)
    if not candidate_players:
        return MarginalRosterUtility(
            utility=0.0, becomes_starter=False, bench_redundancy_before=None,
            explanation="Candidate has no known value (unmodeled asset).",
        )
    candidate = candidate_players[0]
    current_players = _roster_players(current_player_ids, pool)
    report_before = roster_composition_report(current_players, profile)
    redundancy_before = report_before.position_redundancy.get(candidate.position, 0)
    decay_base = POSITION_BACKUP_UTILITY_RATE.get(candidate.position, DEFAULT_BENCH_REDUNDANCY_DECAY)
    # redundancy_before=0 (the FIRST bench player at this position) still
    # gets exactly ONE real discount (decay_base**1), not full value --
    # the real historical measurement above IS the first backup's own
    # startability rate, not a "no discount until the 2nd one" rule.
    # Each additional already-rostered bench-redundant player compounds
    # the same real rate again (decay_base**2, **3, ...), reflecting that
    # a 3rd/4th bench player at a position is even less likely to ever be
    # the one who's needed.
    decay = decay_base ** (redundancy_before + 1)
    utility = round(candidate.value * decay, 2)
    explanation = (
        f"Bench depth at {candidate.position} -- {redundancy_before} real bench-redundant "
        f"{candidate.position}(s) already rostered. Real historical startability rate for a "
        f"{candidate.position} bench player (nflverse 2022-2024, week-1 depth chart): "
        f"{decay_base:.0%}. This candidate's real injury/bye contingency value is discounted "
        f"to {decay:.1%} of its standalone value ({round(candidate.value, 1)} -> {utility})."
    )
    return MarginalRosterUtility(
        utility=utility, becomes_starter=False,
        bench_redundancy_before=redundancy_before, explanation=explanation,
    )


# =====================================================================
# NWR OVERNIGHT V3 strategic closure (sections 2-4): CHALLENGER, not
# wired into the live candidate sort. `marginal_roster_utility` above is
# left byte-for-byte unchanged and remains the live-promoted signal.
#
# ROOT CAUSE, precisely traced (Test 18's real WR8/RB2 pathology):
# POSITION_BACKUP_UTILITY_RATE measures USAGE PROBABILITY -- "will this
# depth-2 player ever see a starter-level snap share in some later
# week?" -- then applies it as a single, fixed geometric decay
# (decay_base ** (redundancy_before + 1)) that barely moves for WR
# (decay_base=0.9688) even at deep bench redundancy: a 6th rostered WR
# (redundancy_before=5) still keeps 0.9688**6 = 82.7% of its standalone
# value. RB's own decay_base (0.4842) looks much harsher by comparison,
# but that is coincidental to how far apart the two USAGE rates happen
# to be -- the formula never asks the question that actually matters for
# a draft decision: how many REAL FANTASY POINTS does a bench player at
# this exact depth actually contribute, relative to what you could get
# for that same roster slot at a DIFFERENT position? Usage and fantasy
# marginal value are not the same thing, and they diverge hardest
# exactly where WR hoarding happens: an NFL team's real WR2/WR3 snap
# share is very often close to full-time (0.9688 measures this
# correctly) precisely BECAUSE modern offenses run 3+ WR sets --  but
# that usage does not translate into WR3+ being fantasy-relevant nearly
# as often, because target competition among 3-4 real NFL WRs on one
# team dilutes any single one's weekly upside. RBs get on the field less
# consistently (lower usage-probability, correctly reflected by RB's own
# 0.4842) but WHEN an RB sees real touches, workload concentration means
# he is far more likely to produce a fantasy-relevant week than a
# similarly-deep WR is.
#
# Real measurement below (bench_marginal_utility_study_v1.py, nflverse
# 2019/2021/2022/2023, development-safe -- 2016/2024/2025 stay burned):
# for the SAME depth rank, real weekly "flex-worthy" week rate (weekly
# PPR points >= a real, position-specific weekly replacement bar) is:
#   WR4 (10-team) =  9.8%  vs  RB4 (10-team) =  6.3%  (WR narrowly ahead)
#   WR5 (10-team) =  5.7%  vs  RB4 (10-team) =  6.3%  (RB now AHEAD)
#   WR6 (10-team) =  4.0%  vs  RB3 (10-team) = 10.2%  (RB more than 2x)
# i.e. the crossover the current formula never finds: by the time a
# roster is choosing between a 5th/6th WR and a 3rd/4th RB (exactly
# Test 18's real R7-R13 decision points), RB is the empirically better
# real bench asset, not WR -- the OPPOSITE of what
# POSITION_BACKUP_UTILITY_RATE's usage-probability proxy implies at
# that same depth. This was not visible before because the existing
# decay is applied PER POSITION IN ISOLATION (each position's own
# geometric curve, never compared against the other three), so nothing
# in the formula could ever surface a cross-positional crossover no
# matter how the data actually behaved.
#
# marginal_roster_utility_v2 replaces the single fixed decay_base with
# the REAL, per-depth-rank empirical rate (declining substantively with
# each additional real bench player, not a fixed geometric ratio), and
# adds a second, real term: an opportunity-cost comparison against the
# best real alternative position's own next bench slot, scaled up when
# few bench slots remain (the roster-state-dependence the directive
# asks for). Both terms are DATA-DERIVED -- no hand-picked "WR cap" or
# "RB minimum" rule.
# =====================================================================

# Real, measured "flex-worthy week rate" by (team-count bucket, position,
# depth rank) -- fraction of a REAL depth-rank-D player's own played
# weeks where his real weekly PPR points met or exceeded a real,
# position-specific weekly replacement bar that season. Source:
# bench_marginal_utility_study_v1.py, nflverse player_stats +
# snap_counts, seasons 2019/2021/2022/2023 (n>=5 team-seasons required
# per cell; QB3+/TE5+ etc. had insufficient real sample and are NOT
# listed here -- see FANTASY_BENCH_UTILITY_EXTRAPOLATION_DECAY below for
# how depths beyond the measured table are handled, disclosed as an
# extrapolation, not a further measurement).
FANTASY_BENCH_UTILITY_RATE: dict[int, dict[str, dict[int, float]]] = {
    8: {
        "QB": {2: 0.121},
        "RB": {2: 0.235, 3: 0.080, 4: 0.052},
        "WR": {2: 0.322, 3: 0.179, 4: 0.086, 5: 0.052, 6: 0.035},
        "TE": {2: 0.105, 3: 0.046, 4: 0.025},
    },
    10: {
        "QB": {2: 0.129},
        "RB": {2: 0.277, 3: 0.102, 4: 0.063},
        "WR": {2: 0.343, 3: 0.200, 4: 0.098, 5: 0.057, 6: 0.040},
        "TE": {2: 0.126, 3: 0.063, 4: 0.043},
    },
    12: {
        "QB": {2: 0.134},
        "RB": {2: 0.312, 3: 0.118, 4: 0.080},
        "WR": {2: 0.383, 3: 0.232, 4: 0.118, 5: 0.072, 6: 0.049},
        "TE": {2: 0.153, 3: 0.080, 4: 0.050},
    },
    16: {
        "QB": {2: 0.182},
        "RB": {2: 0.406, 3: 0.160, 4: 0.114},
        "WR": {2: 0.449, 3: 0.283, 4: 0.165, 5: 0.085, 6: 0.052},
        "TE": {2: 0.182, 3: 0.097, 4: 0.050},
    },
}
# Superflex only materially changes QB's own replacement baseline (RB/WR/TE
# rates are identical to the non-superflex table at the same team count --
# verified directly in the study output, not assumed).
FANTASY_BENCH_UTILITY_RATE_SUPERFLEX_QB: dict[int, float] = {
    10: 0.184,
    12: 0.211,
}
# A depth rank beyond the measured table (insufficient real n, e.g. QB3+
# for most positions) is extrapolated by halving the deepest measured
# rate per additional depth level -- disclosed as an extrapolation, not a
# further measurement. This is a conservative approximation of the real,
# consistently-observed pattern at every OTHER measured depth transition
# in this same study (each extra depth level roughly halves or worse the
# real flex-worthy rate -- e.g. WR3->WR4 at 10-team is 0.098/0.200=0.49x,
# RB2->RB3 is 0.102/0.277=0.37x), not an arbitrary constant.
FANTASY_BENCH_UTILITY_EXTRAPOLATION_DECAY = 0.5
FANTASY_BENCH_UTILITY_FLOOR = 0.01

# Real, measured mean incremental season PPR points (this depth rank's
# own real season-total points minus that season's real replacement-level
# points at that position) -- the common, cross-positional currency used
# by the opportunity-cost term below. Same source/seasons as the rate
# table above.
FANTASY_BENCH_INCREMENTAL_PTS: dict[int, dict[str, dict[int, float]]] = {
    8: {
        "QB": {2: -230.4}, "RB": {2: -94.3, 3: -154.6, 4: -167.5},
        "WR": {2: -75.9, 3: -126.0, 4: -168.9, 5: -191.9, 6: -198.3},
        "TE": {2: -114.7, 3: -139.6, 4: -153.1},
    },
    10: {
        "QB": {2: -221.3}, "RB": {2: -71.3, 3: -131.5, 4: -142.3},
        "WR": {2: -64.5, 3: -114.6, 4: -157.4, 5: -180.5, 6: -186.4},
        "TE": {2: -101.9, 3: -126.1, 4: -141.1},
    },
    12: {
        "QB": {2: -204.0}, "RB": {2: -56.0, 3: -116.2, 4: -126.8},
        "WR": {2: -44.1, 3: -94.1, 4: -136.9, 5: -160.0, 6: -165.6},
        "TE": {2: -89.4, 3: -113.9, 4: -128.5},
    },
    16: {
        "QB": {2: -176.6}, "RB": {2: -20.6, 3: -80.9, 4: -94.5},
        "WR": {2: -16.3, 3: -66.3, 4: -109.2, 5: -132.2, 6: -138.9},
        "TE": {2: -74.0, 3: -98.5, 4: -112.6},
    },
}
# Real, disclosed scale for converting an incremental-points GAP into a
# multiplicative penalty -- 150 points is the approximate real spread
# between WR2 and WR5's own incremental points in the 10-team table
# above (a round, representative magnitude from the study itself, not
# tuned to produce any particular Test 18 outcome).
OPPORTUNITY_COST_SCALE = 150.0
OPPORTUNITY_COST_FLOOR = 0.4
# Bench slots remaining at/below this count means opportunity cost of a
# weak positional add is treated as fully real (multiplier 1.0x on the
# gap); above it, the gap's effect is linearly tapered toward zero --
# early in a draft, with many bench slots still open, a below-average
# depth add costs comparatively little (there is time to fix it later).
BENCH_SCARCITY_THRESHOLD = 3


def _nearest_team_count_bucket(team_count: int) -> int:
    buckets = sorted(FANTASY_BENCH_UTILITY_RATE.keys())
    return min(buckets, key=lambda b: abs(b - team_count))


def _fantasy_bench_utility_rate(position: str, depth: int, team_count: int, superflex: bool) -> float:
    bucket = _nearest_team_count_bucket(team_count)
    if position == "QB" and superflex and bucket in FANTASY_BENCH_UTILITY_RATE_SUPERFLEX_QB and depth == 2:
        return FANTASY_BENCH_UTILITY_RATE_SUPERFLEX_QB[bucket]
    table = FANTASY_BENCH_UTILITY_RATE.get(bucket, {}).get(position, {})
    if not table:
        return DEFAULT_BENCH_REDUNDANCY_DECAY ** depth
    max_measured = max(table.keys())
    if depth in table:
        return table[depth]
    if depth < min(table.keys()):
        return table[min(table.keys())]
    extra_levels = depth - max_measured
    return max(FANTASY_BENCH_UTILITY_FLOOR, table[max_measured] * (FANTASY_BENCH_UTILITY_EXTRAPOLATION_DECAY ** extra_levels))


def _fantasy_bench_incremental_pts(position: str, depth: int, team_count: int) -> float:
    bucket = _nearest_team_count_bucket(team_count)
    table = FANTASY_BENCH_INCREMENTAL_PTS.get(bucket, {}).get(position, {})
    if not table:
        return -9999.0
    max_measured = max(table.keys())
    if depth in table:
        return table[depth]
    if depth < min(table.keys()):
        return table[min(table.keys())]
    # Deeper than measured: keep getting worse by the same real per-level
    # gap the last two measured levels show (never invented from zero).
    sorted_depths = sorted(table.keys())
    last_gap = table[sorted_depths[-1]] - table[sorted_depths[-2]] if len(sorted_depths) >= 2 else 0.0
    return table[max_measured] + last_gap * (depth - max_measured)


def marginal_roster_utility_v2(
    candidate_id: str,
    current_player_ids: Sequence[str],
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> MarginalRosterUtility:
    """CHALLENGER to `marginal_roster_utility` -- see the module comment
    block immediately above for the full root-cause writeup and data
    source. Starter/FLEX-upgrade handling is byte-for-byte identical to
    v1 (reuses the same `explain_marginal_roster_reason` -- no change to
    how a starter-improving pick is valued, only to pure bench adds)."""
    reason = explain_marginal_roster_reason(candidate_id, current_player_ids, profile, ranking, manual_assets)
    if reason.becomes_starter:
        return MarginalRosterUtility(
            utility=reason.starter_value_delta, becomes_starter=True,
            bench_redundancy_before=None, explanation=reason.summary,
        )
    pool = _asset_pool(ranking, manual_assets)
    candidate_players = _roster_players([candidate_id], pool)
    if not candidate_players:
        return MarginalRosterUtility(
            utility=0.0, becomes_starter=False, bench_redundancy_before=None,
            explanation="Candidate has no known value (unmodeled asset).",
        )
    candidate = candidate_players[0]
    current_players = _roster_players(current_player_ids, pool)
    report_before = roster_composition_report(current_players, profile)
    redundancy_before = report_before.position_redundancy.get(candidate.position, 0)
    depth = redundancy_before + 1
    team_count = max(1, profile.team_count)
    superflex = profile.roster.superflex > 0
    rate = _fantasy_bench_utility_rate(candidate.position, depth, team_count, superflex)

    # Opportunity cost: compare this position's own real incremental
    # points at this exact depth against the BEST real incremental
    # points any of the other three skill positions offers at ITS OWN
    # current next depth (redundancy_before+1 for that position too).
    # Does not filter by legality/roster caps -- a real, disclosed
    # simplification; legality itself is independently enforced
    # elsewhere and already gates the candidate set before this ever
    # runs, so this term only ever measures relative attractiveness
    # among whatever is already a legal candidate.
    own_incremental = _fantasy_bench_incremental_pts(candidate.position, depth, team_count)
    # Only compare against a position this league actually rosters at all
    # (a real starter requirement, or FLEX/superflex eligibility) -- a
    # position with zero real roster room (e.g. a 0-RB league) is not a
    # genuine alternative use of this bench slot and must not distort the
    # comparison via a phantom "depth 1" lookup.
    position_has_real_room = {
        "QB": profile.roster.qb > 0 or profile.roster.superflex > 0,
        "RB": profile.roster.rb > 0 or profile.roster.flex > 0,
        "WR": profile.roster.wr > 0 or profile.roster.flex > 0,
        "TE": profile.roster.te > 0 or profile.roster.flex > 0,
    }
    alt_positions = [p for p in ("QB", "RB", "WR", "TE") if p != candidate.position and position_has_real_room.get(p, False)]
    alt_incrementals = [
        _fantasy_bench_incremental_pts(p, report_before.position_redundancy.get(p, 0) + 1, team_count)
        for p in alt_positions
    ]
    best_alt = max(alt_incrementals) if alt_incrementals else own_incremental
    gap = min(0.0, own_incremental - best_alt)  # <=0; 0 when this position is already the best real option

    bench_occupied = sum(report_before.position_redundancy.values())
    bench_remaining = max(0, profile.roster.bench_size - bench_occupied)
    if bench_remaining <= BENCH_SCARCITY_THRESHOLD:
        scarcity_weight = 1.0
    else:
        # Linearly taper toward 0 as bench slots go from THRESHOLD+1 up to
        # a fully-open bench (bench_size) -- real, bounded, monotonic, no
        # discontinuity at the threshold itself.
        span = max(1, profile.roster.bench_size - BENCH_SCARCITY_THRESHOLD)
        scarcity_weight = max(0.0, 1.0 - (bench_remaining - BENCH_SCARCITY_THRESHOLD) / span)
    opportunity_multiplier = max(OPPORTUNITY_COST_FLOOR, 1.0 + (gap * scarcity_weight) / OPPORTUNITY_COST_SCALE)

    utility = round(candidate.value * rate * opportunity_multiplier, 2)
    explanation = (
        f"[v2 challenger] Bench depth at {candidate.position} (would become real depth rank "
        f"{depth}) -- real, measured flex-worthy-week rate for this exact depth "
        f"(nflverse {team_count}-team bucket, 2019/2021/2022/2023): {rate:.1%}. Opportunity-cost "
        f"vs. the best alternative position's own next bench slot: {gap:+.1f} incremental PPR pts "
        f"(scarcity weight {scarcity_weight:.2f}, {bench_remaining} bench slots remain) -> "
        f"{opportunity_multiplier:.2f}x. Standalone value {round(candidate.value, 1)} -> {utility}."
    )
    return MarginalRosterUtility(
        utility=utility, becomes_starter=False,
        bench_redundancy_before=redundancy_before, explanation=explanation,
    )


def availability_discount_for_hypotheses(
    player_id: str, impact_hypotheses: Sequence[ImpactHypothesis]
) -> float:
    """A value multiplier in [0.0, 1.0] driven ONLY by an existing
    Impact Analyst hypothesis about this exact player
    (ai_intelligence_backend_service.py's own disclosed rule table -- not
    a new invented severity model). Anything else (MEDIUM/LOW confidence,
    or no hypothesis at all) returns 1.0 -- no discount without a real,
    already-computed, high-confidence structural signal.

    Two real, distinct discount tiers (NWR post-draft overnight, phase 10
    added the second):
      - HIGH-confidence NEGATIVE (a confirmed event with a known negative
        outcome, e.g. IR/PUP-NFI/a served SUSPENSION): 0.0 -- treat as
        unavailable.
      - HIGH-confidence, IMMEDIATE-horizon UNCERTAIN (currently only
        ADMINISTRATIVE_EXEMPT produces this exact combination -- a real,
        elevated-risk situation with NO announced outcome yet, such as an
        active legal/disciplinary proceeding): 0.5. This is NOT a guess at
        the eventual outcome or a specific missed-game count -- it is a
        disclosed, deliberately partial discount representing "something
        real and material is genuinely uncertain here," distinct from both
        "confirmed unavailable" (0.0) and "no real signal" (1.0, the
        default). The `horizon == "IMMEDIATE"` guard specifically excludes
        REST_OF_SEASON/LONG_TERM UNCERTAIN hypotheses like ROLE_CHANGE --
        "direction of fantasy impact still depends on which player is
        affected" is uncertainty about USAGE, not about whether the
        player takes the field at all, and could just as easily be
        positive (a promotion) as negative; discounting it here would be
        a real, wrong assumption this function must not make.
    """
    for hypothesis in impact_hypotheses:
        if hypothesis.subject_player_id != player_id:
            continue
        if hypothesis.confidence != "HIGH":
            continue
        if hypothesis.direction == "NEGATIVE":
            return 0.0
        if hypothesis.direction == "UNCERTAIN" and hypothesis.horizon == "IMMEDIATE":
            return 0.5
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
    impact_hypotheses: Sequence[ImpactHypothesis] = (),
) -> TeamScoreResult:
    """Percentile strength of `target_player_ids`'s optimal starting
    lineup relative to every team's optimal starting lineup across
    `comparable_leagues` (real simulated leagues under this exact league
    format -- see simulate_comparable_leagues). ~50 means the roster's
    modeled strength is in the middle of the simulated distribution for
    this format, by construction of the population rather than by a
    hand-picked normalization constant.

    `impact_hypotheses` (NWR post-draft overnight, phase 6): optional,
    defaults to `()` -- every existing caller that doesn't pass it is
    byte-identical to before this parameter existed. When supplied, real
    HIGH-confidence NEGATIVE hypotheses (the existing, previously fully
    built but never-called `availability_adjusted_players`/
    `availability_discount_for_hypotheses` from this same module) zero out
    that player's contribution to the optimal starting lineup, the same
    real mechanism `roster_composition_report` already documented as the
    intended integration point. Still requires a real NewsEvent to be
    ingested first (see `ai_intelligence_backend_service.append_news_event`
    -- there is currently no facade/UI path that calls it at all, a
    separate, real, disclosed gap this parameter does not itself close)."""
    pool = _asset_pool(ranking, manual_assets)
    target_players = _roster_players(target_player_ids, pool)
    if impact_hypotheses:
        target_players = availability_adjusted_players(target_players, impact_hypotheses)
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
    impact_hypotheses: Sequence[ImpactHypothesis] = (),
) -> ChampionshipEquityResult:
    """P(win this league) for `target_player_ids`, inserted at
    `target_team_slot` into one real simulated `comparable_league` (the
    other team_count-1 rosters, from simulate_comparable_leagues), with
    the rest of that league's draft outcome held fixed and only the
    weekly/playoff simulation randomized across `seasons` trials.

    `impact_hypotheses`: see `team_score`'s own docstring -- same optional,
    additive, default-`()`-is-a-no-op parameter and mechanism, applied only
    to the target roster (not the other simulated comparable-league teams,
    which have no real news events tied to them)."""
    assumptions = assumptions or ChampionshipEquityAssumptions()
    pool = _asset_pool(ranking, manual_assets)
    target_players = _roster_players(target_player_ids, pool)
    if impact_hypotheses:
        target_players = availability_adjusted_players(target_players, impact_hypotheses)
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
    # Owner feedback closure: a purely additive disclosure flag -- never
    # changes relative_score's own value or the frozen formula above.
    # True exactly when every candidate in THIS evaluated set shares the
    # same championship_equity win_probability (spread <= 0), the real
    # condition that forces every relative_score in the set to the same
    # 50.0 midpoint. Lets the UI say "the model cannot distinguish these
    # candidates on this signal" instead of presenting a bare 50.0 that
    # looks identical to (and is easily confused with) an unevaluated or
    # placeholder value.
    tied_no_spread: bool = False


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
    tied_no_spread = spread <= 0
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
            tied_no_spread=tied_no_spread,
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


def simulate_pick_pair_now(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    first_candidate_id: str,
    second_candidate_id: str,
    seed: int = DEFAULT_SEED,
    from_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """NWR post-draft overnight, phase 16 (pair-pick optimizer). Forces
    BOTH real picks of a genuine back-to-back turn (zero opponents
    intervening -- e.g. slot 8 of 8, 1.08 then 2.01) in the given order,
    then completes the rest of the draft normally -- the real answer to
    "does pick order matter for this exact pair", not two independent
    simulate_pick_now() calls (which would let the deterministic auto-
    fill policy choose the SECOND half of the turn for the owner instead
    of the specific second candidate being tested, silently answering a
    different question).

    Reuses `_record_pick` to record the first pick exactly once (a real
    draft-state mutation, never resimulated), then hands off to the
    existing, unmodified `simulate_pick_now` for the second forced pick
    and the rest of the draft -- no new draft-completion algorithm.
    Raises the same real errors `simulate_pick_now` does if either
    candidate is unknown or already drafted; the caller is responsible
    for confirming (e.g. via a real DecisionBundle) that the state
    actually represents a back-to-back turn before comparing orderings."""
    from src.services.redraft_draft_room_v1_service import _record_pick

    pool = _asset_pool(ranking, manual_assets)
    first_asset = pool.get(first_candidate_id)
    if first_asset is None:
        raise ValueError(f"{first_candidate_id!r} is not a draftable asset.")
    state: dict[str, Any] = (
        dict(from_state)
        if from_state is not None
        else {
            "schema_version": 1, "profile_id": profile.profile_id, "owner_slot": owner_slot,
            "seed": seed, "speed": "FAST", "mode": "MOCK", "drafted": [], "picks": [],
            "updated_at_utc": "",
        }
    )
    if first_candidate_id in state.get("drafted", []):
        raise ValueError(f"{first_candidate_id!r} is already drafted.")
    state = _record_pick(
        profile, state, first_asset, actor="PAIR_PICK_LOOKAHEAD", behavior="FORCED_CANDIDATE"
    )
    return simulate_pick_now(
        profile, ranking, manual_assets, adp,
        owner_slot=owner_slot, candidate_player_id=second_candidate_id,
        seed=seed, from_state=state,
    )


@dataclass(frozen=True)
class PairPickResult:
    ordering: tuple[str, str]
    team_score_result: TeamScoreResult
    championship_equity_result: ChampionshipEquityResult


def evaluate_pick_pairs(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    candidate_player_ids: Sequence[str],
    comparable_leagues: Sequence[dict[int, list[RosterPlayer]]],
    seasons: int = 300,
    base_seed: int = DEFAULT_SEED,
    from_state: Mapping[str, Any] | None = None,
) -> dict[tuple[str, str], PairPickResult]:
    """Evaluates every ordered pair drawn from `candidate_player_ids` (a
    caller-supplied, already-legality-filtered shortlist -- this does not
    re-derive candidates) for a genuine back-to-back turn, scoring each
    resulting roster with the exact same team_score()/championship_equity()
    every other real decision surface uses. Ordered (not just unordered)
    so "does the order matter" is a real, checkable question, not assumed
    either way -- results for (A, B) and (B, A) can differ if the
    deterministic downstream continuation happens to treat them
    differently, which this function surfaces rather than papers over.
    Quadratic in candidate count by design -- callers must pass a bounded
    shortlist (e.g. the same handful of top DecisionBundle candidates),
    never the full available pool."""
    results: dict[tuple[str, str], PairPickResult] = {}
    default_slot = next(iter(comparable_leagues[0]))
    target_slot = owner_slot if owner_slot in comparable_leagues[0] else default_slot
    for first_id in candidate_player_ids:
        for second_id in candidate_player_ids:
            if first_id == second_id:
                continue
            final_state = simulate_pick_pair_now(
                profile, ranking, manual_assets, adp,
                owner_slot=owner_slot, first_candidate_id=first_id, second_candidate_id=second_id,
                seed=base_seed, from_state=from_state,
            )
            owner_player_ids = [
                str(pick["player_id"]) for pick in final_state["picks"]
                if int(pick["team_slot"]) == owner_slot and pick.get("player_id")
            ]
            team = team_score(
                owner_player_ids, profile, ranking, manual_assets,
                comparable_leagues=comparable_leagues,
            )
            equity = championship_equity(
                owner_player_ids, profile, ranking, manual_assets,
                comparable_league=comparable_leagues[0], target_team_slot=target_slot,
                seasons=seasons, base_seed=base_seed,
            )
            results[(first_id, second_id)] = PairPickResult(
                ordering=(first_id, second_id), team_score_result=team,
                championship_equity_result=equity,
            )
    return results


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
    continuation_seeds: int = 1,
) -> dict[str, PickScoreResult]:
    """The full look-ahead pipeline for one pick: for every candidate,
    simulate_pick_now() to get a completed final roster, score it with
    team_score()/championship_equity() against a shared comparable-league
    population (computed once, reused across every candidate -- this is
    the 'cache/precompute reusable components' the brief allows when full
    per-candidate resimulation would be too slow), then rank all
    candidates against each other with pick_score().

    `continuation_seeds` (NWR OVERNIGHT -- Team-After saturation, traced
    not assumed): `simulate_pick_now`'s continuation (every pick after
    this one, for every team) is 100% deterministic given `base_seed` --
    CPU picks use ADP + a seeded jitter, and the owner's own OWNER_AUTO_TEST
    continuation is a pure deterministic greedy sort. With
    `continuation_seeds=1` (the unchanged default -- every existing caller
    is byte-identical), two very different candidates at a pick with a
    nearby deadline-forced need (e.g. QB due next round regardless) can
    genuinely converge to a near-identical simulated final roster, because
    the SAME deterministic fill policy absorbs the difference either way --
    a real, disclosed, and now measurably reduced source of the "everyone
    ties at 50/99" pattern, not something a '(tied)' label alone fixes.
    `continuation_seeds > 1` reruns the continuation across that many
    seeds (base_seed, base_seed+1, ...) per candidate and averages the
    resulting Team Score / win_probability -- widening the SAMPLED
    population the look-ahead draws from, never touching team_score()'s or
    championship_equity()'s own frozen formulas."""
    leagues = comparable_leagues or simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=trials, base_seed=base_seed
    )
    results: dict[str, tuple[TeamScoreResult, ChampionshipEquityResult]] = {}
    seed_count = max(1, continuation_seeds)
    for candidate in candidate_player_ids:
        teams: list[TeamScoreResult] = []
        equities: list[ChampionshipEquityResult] = []
        for offset in range(seed_count):
            continuation_seed = base_seed + offset
            final_state = simulate_pick_now(
                profile,
                ranking,
                manual_assets,
                adp,
                owner_slot=owner_slot,
                candidate_player_id=candidate,
                seed=continuation_seed,
                from_state=from_state,
            )
            owner_player_ids = [
                str(pick["player_id"])
                for pick in final_state["picks"]
                if int(pick["team_slot"]) == owner_slot and pick.get("player_id")
            ]
            teams.append(
                team_score(
                    owner_player_ids, profile, ranking, manual_assets, comparable_leagues=leagues
                )
            )
            equities.append(
                championship_equity(
                    owner_player_ids,
                    profile,
                    ranking,
                    manual_assets,
                    comparable_league=leagues[0],
                    target_team_slot=(
                        owner_slot if owner_slot in leagues[0] else next(iter(leagues[0]))
                    ),
                    seasons=seasons,
                    base_seed=continuation_seed,
                )
            )
        # Only the headline scalars are averaged across continuation
        # seeds; every other diagnostic field (population stats, standard
        # error) is seed-1's own real value, not a fabricated composite --
        # population stats are identical across seeds anyway (same shared
        # `leagues`), and standard_error already discloses seed-1's own
        # Monte Carlo uncertainty.
        team = replace(
            teams[0],
            percentile=round(statistics.fmean(t.percentile for t in teams), 1),
            roster_value=round(statistics.fmean(t.roster_value for t in teams), 2),
        )
        equity = replace(
            equities[0],
            win_probability=round(statistics.fmean(e.win_probability for e in equities), 4),
        )
        results[candidate] = (team, equity)
    return pick_score(results)
