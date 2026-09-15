"""Trade Package Quality Benchmark V1 (NWR Prospective Outcomes V1, Work
Unit 16) -- MEASUREMENT ONLY.

Preregistered rubric (written before this module was run against real
data): `docs/codex/prospective_outcomes_v1/TRADE_PACKAGE_QUALITY_
BENCHMARK_V1.md`. Every constant below matches that document exactly.

This module never modifies, re-implements, or bypasses `trade_package_
search_service.py`'s own generation/gating logic -- it only READS the
`TradePackageSearchResult`/`TradePackageCandidate` objects that module's
real `search_win_win_packages`/`search_target_player_packages`/
`search_improve_position_packages` functions already produce (or, for
gate-function unit coverage, hand-built fixtures of the exact same
dataclasses) and computes diagnostic reports over them. No new roster
value/utility formula is introduced anywhere in this file.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from src.services.redraft_engine_v1_service import LeagueProfile
from src.services.trade_package_search_service import (
    TradePackageCandidate,
    TradePackageSearchResult,
)

# --- Preregistered thresholds (see the rubric doc) -------------------------
STARTER_VALUE_EPSILON = 0.5
NEAR_DUPLICATE_JACCARD_THRESHOLD = 0.5


def _package_players(candidate: TradePackageCandidate) -> frozenset[str]:
    return frozenset(candidate.you_send) | frozenset(candidate.you_receive)


def _package_size(candidate: TradePackageCandidate) -> int:
    return len(candidate.you_send) + len(candidate.you_receive)


# ---------------------------------------------------------------------------
# Dimension 1 -- dominance re-verification (black-box, on the generator's
# own output, never re-running its private filter).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DominanceViolation:
    opponent_roster_id: str
    dominated_send: tuple[str, ...]
    dominated_receive: tuple[str, ...]
    dominator_send: tuple[str, ...]
    dominator_receive: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "opponentRosterId": self.opponent_roster_id,
            "dominatedSend": list(self.dominated_send),
            "dominatedReceive": list(self.dominated_receive),
            "dominatorSend": list(self.dominator_send),
            "dominatorReceive": list(self.dominator_receive),
        }


def check_dominance_violations(
    candidates: Sequence[TradePackageCandidate],
) -> tuple[DominanceViolation, ...]:
    """Rubric dimension 1: for every (opponent, candidate) pair, is there a
    real, RETURNED, equal-or-smaller package for the same opponent that
    weakly dominates it on both owner and opponent net utility? A real
    violation here means the generator's own gate 4 has a real hole; an
    empty result confirms the invariant holds on real output."""

    violations: list[DominanceViolation] = []
    by_opponent: dict[str, list[TradePackageCandidate]] = {}
    for candidate in candidates:
        by_opponent.setdefault(candidate.opponent_roster_id, []).append(candidate)
    for opponent_id, group in by_opponent.items():
        for candidate in group:
            c_owner = candidate.owner_evaluation.net_marginal_utility or 0.0
            c_opp = candidate.opponent_evaluation.net_marginal_utility or 0.0
            c_size = _package_size(candidate)
            for other in group:
                if other is candidate:
                    continue
                o_size = _package_size(other)
                if o_size > c_size:
                    continue
                o_owner = other.owner_evaluation.net_marginal_utility or 0.0
                o_opp = other.opponent_evaluation.net_marginal_utility or 0.0
                same_values = o_owner == c_owner and o_opp == c_opp
                if o_owner >= c_owner and o_opp >= c_opp and not (same_values and o_size == c_size):
                    violations.append(
                        DominanceViolation(
                            opponent_roster_id=opponent_id,
                            dominated_send=candidate.you_send,
                            dominated_receive=candidate.you_receive,
                            dominator_send=other.you_send,
                            dominator_receive=other.you_receive,
                        )
                    )
                    break
    return tuple(violations)


# ---------------------------------------------------------------------------
# Dimension 2 -- mutual real starter-value gain.
# ---------------------------------------------------------------------------

StarterImpactLabel = str  # "BOTH_SIDES_STARTER_IMPACT" | "ONE_SIDED_STARTER_IMPACT" | "NEITHER_SIDE_STARTER_IMPACT"


@dataclass(frozen=True)
class StarterImpactRow:
    you_send: tuple[str, ...]
    you_receive: tuple[str, ...]
    owner_starting_lineup_value_delta: float
    opponent_starting_lineup_value_delta: float
    label: StarterImpactLabel

    def to_dict(self) -> dict[str, Any]:
        return {
            "youSend": list(self.you_send),
            "youReceive": list(self.you_receive),
            "ownerStartingLineupValueDelta": self.owner_starting_lineup_value_delta,
            "opponentStartingLineupValueDelta": self.opponent_starting_lineup_value_delta,
            "label": self.label,
        }


def _starter_impact_label(owner_delta: float, opponent_delta: float) -> StarterImpactLabel:
    owner_moved = abs(owner_delta) >= STARTER_VALUE_EPSILON
    opponent_moved = abs(opponent_delta) >= STARTER_VALUE_EPSILON
    if owner_moved and opponent_moved:
        return "BOTH_SIDES_STARTER_IMPACT"
    if owner_moved or opponent_moved:
        return "ONE_SIDED_STARTER_IMPACT"
    return "NEITHER_SIDE_STARTER_IMPACT"


def check_mutual_starter_gain(
    candidates: Sequence[TradePackageCandidate],
) -> tuple[StarterImpactRow, ...]:
    """Rubric dimension 2 (also feeds dimension 4, bench-for-bench
    clutter, via the NEITHER_SIDE label)."""

    rows: list[StarterImpactRow] = []
    for candidate in candidates:
        owner_delta = candidate.owner_evaluation.starting_lineup_value_delta or 0.0
        opponent_delta = candidate.opponent_evaluation.starting_lineup_value_delta or 0.0
        rows.append(
            StarterImpactRow(
                you_send=candidate.you_send,
                you_receive=candidate.you_receive,
                owner_starting_lineup_value_delta=owner_delta,
                opponent_starting_lineup_value_delta=opponent_delta,
                label=_starter_impact_label(owner_delta, opponent_delta),
            )
        )
    return tuple(rows)


def bench_for_bench_clutter_rate(rows: Sequence[StarterImpactRow]) -> float | None:
    """Rubric dimension 4, summarized: the fraction of candidates with
    NEITHER side showing a real starting-lineup impact. `None` on an empty
    input (no candidates to rate) rather than a misleading 0.0."""

    if not rows:
        return None
    clutter = sum(1 for row in rows if row.label == "NEITHER_SIDE_STARTER_IMPACT")
    return round(clutter / len(rows), 4)


# ---------------------------------------------------------------------------
# Dimension 3 -- real position-need fit (starter-hole resolution).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HoleFitRow:
    you_send: tuple[str, ...]
    you_receive: tuple[str, ...]
    owner_holes_resolved: tuple[str, ...]
    addressed_a_real_hole: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "youSend": list(self.you_send),
            "youReceive": list(self.you_receive),
            "ownerHolesResolved": list(self.owner_holes_resolved),
            "addressedARealHole": self.addressed_a_real_hole,
        }


def check_position_need_fit(candidates: Sequence[TradePackageCandidate]) -> tuple[HoleFitRow, ...]:
    rows: list[HoleFitRow] = []
    for candidate in candidates:
        evaluation = candidate.owner_evaluation
        resolved = tuple(sorted(set(evaluation.starter_holes_before) - set(evaluation.starter_holes_after)))
        rows.append(
            HoleFitRow(
                you_send=candidate.you_send,
                you_receive=candidate.you_receive,
                owner_holes_resolved=resolved,
                addressed_a_real_hole=bool(resolved),
            )
        )
    return tuple(rows)


# ---------------------------------------------------------------------------
# Dimension 5 -- near-duplicate packages (Jaccard similarity, per opponent).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NearDuplicatePair:
    opponent_roster_id: str
    package_a: tuple[tuple[str, ...], tuple[str, ...]]
    package_b: tuple[tuple[str, ...], tuple[str, ...]]
    jaccard_similarity: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "opponentRosterId": self.opponent_roster_id,
            "packageA": {"youSend": list(self.package_a[0]), "youReceive": list(self.package_a[1])},
            "packageB": {"youSend": list(self.package_b[0]), "youReceive": list(self.package_b[1])},
            "jaccardSimilarity": self.jaccard_similarity,
        }


def check_near_duplicates(
    candidates: Sequence[TradePackageCandidate],
    *,
    threshold: float = NEAR_DUPLICATE_JACCARD_THRESHOLD,
) -> tuple[NearDuplicatePair, ...]:
    pairs: list[NearDuplicatePair] = []
    by_opponent: dict[str, list[TradePackageCandidate]] = {}
    for candidate in candidates:
        by_opponent.setdefault(candidate.opponent_roster_id, []).append(candidate)
    for opponent_id, group in by_opponent.items():
        for i, a in enumerate(group):
            a_players = _package_players(a)
            for b in group[i + 1 :]:
                if a.you_send == b.you_send and a.you_receive == b.you_receive:
                    continue  # exact duplicates are structurally impossible; not this dimension's concern
                b_players = _package_players(b)
                union = a_players | b_players
                if not union:
                    continue
                similarity = len(a_players & b_players) / len(union)
                if similarity >= threshold:
                    pairs.append(
                        NearDuplicatePair(
                            opponent_roster_id=opponent_id,
                            package_a=(a.you_send, a.you_receive),
                            package_b=(b.you_send, b.you_receive),
                            jaccard_similarity=round(similarity, 4),
                        )
                    )
    return tuple(pairs)


# ---------------------------------------------------------------------------
# Dimension 6 -- package-size distribution (diagnostic, not pass/fail).
# ---------------------------------------------------------------------------


def size_utility_distribution(candidates: Sequence[TradePackageCandidate]) -> dict[str, dict[str, float | int]]:
    by_shape: dict[str, list[float]] = {}
    for candidate in candidates:
        by_shape.setdefault(candidate.package_shape, []).append(
            candidate.owner_evaluation.net_marginal_utility or 0.0
        )
    report: dict[str, dict[str, float | int]] = {}
    for shape, utilities in by_shape.items():
        sorted_utilities = sorted(utilities)
        n = len(sorted_utilities)
        median = (
            sorted_utilities[n // 2]
            if n % 2 == 1
            else (sorted_utilities[n // 2 - 1] + sorted_utilities[n // 2]) / 2
        )
        report[shape] = {
            "count": n,
            "meanOwnerNetUtility": round(sum(sorted_utilities) / n, 4) if n else 0.0,
            "medianOwnerNetUtility": round(median, 4) if n else 0.0,
        }
    return report


# ---------------------------------------------------------------------------
# Dimension 7 -- roster consolidation legality/sensibility (re-verified
# externally, never trusting the generator's own internal gate blindly).
# ---------------------------------------------------------------------------


def _total_roster_slots(profile: LeagueProfile) -> int:
    r = profile.roster
    return r.qb + r.rb + r.wr + r.te + r.flex + r.superflex + r.k + r.dst + r.bench_size


@dataclass(frozen=True)
class RosterConsolidationViolation:
    you_send: tuple[str, ...]
    you_receive: tuple[str, ...]
    side: str  # "OWNER" | "OPPONENT"
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "youSend": list(self.you_send),
            "youReceive": list(self.you_receive),
            "side": self.side,
            "reason": self.reason,
        }


def check_roster_consolidation_legality(
    candidates: Sequence[TradePackageCandidate],
    *,
    owner_roster_size_before: int,
    opponent_roster_size_before_by_id: Mapping[str, int],
    profile: LeagueProfile,
) -> tuple[RosterConsolidationViolation, ...]:
    """Re-verifies gate 1 externally against the candidate's own
    `you_send`/`you_receive` and real pre-trade roster sizes -- never
    reusing the generator's own private `_roster_size_legal` function, so
    this is a genuinely independent re-check, not a re-run of the same
    code path."""

    cap = _total_roster_slots(profile)
    violations: list[RosterConsolidationViolation] = []
    for candidate in candidates:
        owner_after = (
            owner_roster_size_before - len(set(candidate.you_send)) + len(set(candidate.you_receive))
        )
        if not (0 <= owner_after <= cap):
            violations.append(
                RosterConsolidationViolation(
                    candidate.you_send, candidate.you_receive, "OWNER",
                    f"post-trade roster size {owner_after} outside [0, {cap}]",
                )
            )
        opponent_before = opponent_roster_size_before_by_id.get(candidate.opponent_roster_id)
        if opponent_before is not None:
            opponent_after = (
                opponent_before - len(set(candidate.you_receive)) + len(set(candidate.you_send))
            )
            if not (0 <= opponent_after <= cap):
                violations.append(
                    RosterConsolidationViolation(
                        candidate.you_send, candidate.you_receive, "OPPONENT",
                        f"post-trade roster size {opponent_after} outside [0, {cap}]",
                    )
                )
    return tuple(violations)


# ---------------------------------------------------------------------------
# Dimension 8 -- package diversity.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiversityReport:
    total_candidates: int
    distinct_players_used: int
    distinct_player_ratio: float | None
    max_single_player_frequency: int
    most_recycled_player_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "totalCandidates": self.total_candidates,
            "distinctPlayersUsed": self.distinct_players_used,
            "distinctPlayerRatio": self.distinct_player_ratio,
            "maxSinglePlayerFrequency": self.max_single_player_frequency,
            "mostRecycledPlayerId": self.most_recycled_player_id,
        }


def check_diversity(candidates: Sequence[TradePackageCandidate]) -> DiversityReport:
    total = len(candidates)
    frequency: dict[str, int] = {}
    for candidate in candidates:
        for player_id in _package_players(candidate):
            frequency[player_id] = frequency.get(player_id, 0) + 1
    distinct = len(frequency)
    most_recycled = max(frequency, key=lambda pid: frequency[pid]) if frequency else None
    return DiversityReport(
        total_candidates=total,
        distinct_players_used=distinct,
        distinct_player_ratio=round(distinct / total, 4) if total else None,
        max_single_player_frequency=frequency.get(most_recycled, 0) if most_recycled else 0,
        most_recycled_player_id=most_recycled,
    )


# ---------------------------------------------------------------------------
# Dimension 9 -- latency (real wall-clock, not a claim).
# ---------------------------------------------------------------------------


def measure_latency(callable_: Callable[[], Any]) -> tuple[Any, float]:
    start = time.perf_counter()
    result = callable_()
    elapsed = time.perf_counter() - start
    return result, elapsed


# ---------------------------------------------------------------------------
# Top-level orchestrator.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TradePackageQualityReport:
    label: str
    mode: str
    candidate_count: int
    packages_evaluated: int
    truncated: bool
    elapsed_seconds: float
    dominance_violations: tuple[DominanceViolation, ...]
    starter_impact_rows: tuple[StarterImpactRow, ...]
    bench_for_bench_clutter_rate: float | None
    hole_fit_rows: tuple[HoleFitRow, ...]
    near_duplicate_pairs: tuple[NearDuplicatePair, ...]
    size_utility_distribution: dict[str, dict[str, float | int]]
    roster_consolidation_violations: tuple[RosterConsolidationViolation, ...]
    diversity: DiversityReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "mode": self.mode,
            "candidateCount": self.candidate_count,
            "packagesEvaluated": self.packages_evaluated,
            "truncated": self.truncated,
            "elapsedSeconds": round(self.elapsed_seconds, 4),
            "dominanceViolations": [v.to_dict() for v in self.dominance_violations],
            "starterImpactRows": [r.to_dict() for r in self.starter_impact_rows],
            "benchForBenchClutterRate": self.bench_for_bench_clutter_rate,
            "holeFitRows": [r.to_dict() for r in self.hole_fit_rows],
            "nearDuplicatePairs": [p.to_dict() for p in self.near_duplicate_pairs],
            "sizeUtilityDistribution": self.size_utility_distribution,
            "rosterConsolidationViolations": [v.to_dict() for v in self.roster_consolidation_violations],
            "diversity": self.diversity.to_dict(),
        }


def run_trade_package_quality_benchmark(
    result: TradePackageSearchResult,
    *,
    label: str,
    owner_roster_size_before: int,
    opponent_roster_size_before_by_id: Mapping[str, int],
    profile: LeagueProfile,
    elapsed_seconds: float,
) -> TradePackageQualityReport:
    """Applies every rubric dimension to one real `TradePackageSearchResult`
    (one mode, one run). Pure, read-only -- never mutates `result` or calls
    back into the generator."""

    candidates = result.candidates
    starter_rows = check_mutual_starter_gain(candidates)
    return TradePackageQualityReport(
        label=label,
        mode=result.mode,
        candidate_count=len(candidates),
        packages_evaluated=result.packages_evaluated,
        truncated=result.truncated,
        elapsed_seconds=elapsed_seconds,
        dominance_violations=check_dominance_violations(candidates),
        starter_impact_rows=starter_rows,
        bench_for_bench_clutter_rate=bench_for_bench_clutter_rate(starter_rows),
        hole_fit_rows=check_position_need_fit(candidates),
        near_duplicate_pairs=check_near_duplicates(candidates),
        size_utility_distribution=size_utility_distribution(candidates),
        roster_consolidation_violations=check_roster_consolidation_legality(
            candidates,
            owner_roster_size_before=owner_roster_size_before,
            opponent_roster_size_before_by_id=opponent_roster_size_before_by_id,
            profile=profile,
        ),
        diversity=check_diversity(candidates),
    )
