"""Source quality gate computation for the Live Player Intelligence V1 cycle
(Work Unit 5, branch `upgrade/nwr-live-player-intelligence-v1-20260913`).

Pure, network-free, no production wiring: nothing here is imported by
`src/application/desktop_facade.py`, `src/desktop_api/server.py`,
`player_availability_status_service.py`, or any recommendation/scoring
module. Computes REAL numbers for Gates 3 (official factual agreement) and
4 (coverage) of `docs/codex/live_player_intelligence_v1/
LIVE_PLAYER_INTELLIGENCE_ADMISSION_CONTRACT.md`, against Worker 2's real
182-row official truth benchmark and real candidate-source snapshots.
Gate 5 (freshness) is characterized using the small set of pure helpers
below (`diff_poll_rows`, `summarize_seconds`) plus real repeated-poll
evidence assembled by the companion script
(`scripts/build_live_player_intelligence_source_quality_v1.py`); this
module does not itself fabricate a P95 figure when the underlying evidence
does not support one.

Every function here is deliberately small and independently testable on
known constructed examples (not just trusted against the one real
aggregate run) -- see
`tests/test_live_player_intelligence_source_quality_v1_service.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

# ---------------------------------------------------------------------------
# Gate 4 -- coverage
# ---------------------------------------------------------------------------

GATE_4_COVERAGE_THRESHOLD = 0.95


@dataclass(frozen=True)
class CoverageResult:
    population_size: int
    covered_size: int
    coverage_ratio: float | None
    meets_gate: bool | None
    uncovered_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "populationSize": self.population_size,
            "coveredSize": self.covered_size,
            "coverageRatio": self.coverage_ratio,
            "meetsGate": self.meets_gate,
            "gateThreshold": GATE_4_COVERAGE_THRESHOLD,
            "uncoveredIds": list(self.uncovered_ids),
        }


def compute_coverage(population_ids: Sequence[str], covered_ids: Sequence[str]) -> CoverageResult:
    """Gate 4: what fraction of `population_ids` (the real official-report
    fantasy-relevant population) does `covered_ids` (a candidate source's
    own resolved/mapped id set) actually cover. An empty population is
    honestly reported as `None`/`None` (not computable, never a fabricated
    100% or 0%)."""

    population = list(dict.fromkeys(population_ids))
    covered_set = set(covered_ids)
    if not population:
        return CoverageResult(0, 0, None, None, ())
    covered = [pid for pid in population if pid in covered_set]
    uncovered = tuple(pid for pid in population if pid not in covered_set)
    ratio = len(covered) / len(population)
    return CoverageResult(
        population_size=len(population),
        covered_size=len(covered),
        coverage_ratio=round(ratio, 4),
        meets_gate=ratio >= GATE_4_COVERAGE_THRESHOLD,
        uncovered_ids=uncovered,
    )


# ---------------------------------------------------------------------------
# Gate 3 -- official factual agreement
# ---------------------------------------------------------------------------

GATE_3_AGREEMENT_THRESHOLD = 0.99

# Normalized "hard" buckets for the zero-contradictory-hard-status check.
# A HARD_OUT value means the player is NOT expected to play / is not on an
# active-and-healthy footing; HARD_ACTIVE means the source affirmatively
# reports no designation at all (i.e. reports the player as healthy this
# week). QUESTIONABLE/DOUBTFUL/other soft designations are neither -- they
# are a real, expected disagreement-tolerant middle ground, not a hard
# contradiction candidate.
HARD_OUT_CATEGORIES = frozenset({"OUT", "DOUBTFUL_TO_HARD_OUT_CLASS"})


def normalize_benchmark_report_status(report_status_category: str | None) -> str:
    """The official-truth-benchmark's own vocabulary
    (OUT/DOUBTFUL/QUESTIONABLE/CLEARED_OR_NOT_LISTED) is already
    normalized by Worker 2's build -- this passes it through, defaulting
    an empty/missing value to CLEARED_OR_NOT_LISTED (the benchmark's own
    documented meaning for "no game-status designation this week"), never
    to a guessed injury value."""

    value = (report_status_category or "").strip().upper()
    return value or "CLEARED_OR_NOT_LISTED"


# Real, disclosed Sleeper `injury_status` vocabulary (see
# `local_exports/.../sleeper_players/latest/sleeper_players_snapshot.json`,
# a real live pull, 2026-09-14): {'NA', 'COV', 'IR', 'Sus', 'Out',
# 'Questionable', 'PUP', 'DNR'}. Only 'Out'/'Doubtful'/'Questionable' are
# the SAME kind of weekly game-status designation the benchmark reports;
# 'Doubtful' does not currently appear in a real Sleeper pull (an honest,
# disclosed real-data limitation, not an omission in this mapping) but is
# still mapped for completeness/forward-compatibility. IR/PUP/COV/Sus are
# real, hard, "not playing" facts but are a DIFFERENT concept than a
# weekly injury designation (roster/list status, not a practice-report
# category) -- mapped to their own bucket, never silently folded into
# OUT/DOUBTFUL/QUESTIONABLE for the exact-agreement computation. DNR (did
# not report) and NA carry no real comparable signal.
SLEEPER_INJURY_STATUS_TO_DESIGNATION: dict[str, str] = {
    "Out": "OUT",
    "Doubtful": "DOUBTFUL",
    "Questionable": "QUESTIONABLE",
}
SLEEPER_INJURY_STATUS_TO_LIST_STATUS: dict[str, str] = {
    "IR": "ON_LIST_IR",
    "PUP": "ON_LIST_PUP",
    "Sus": "ON_LIST_SUSPENDED",
    "COV": "ON_LIST_COVID",
}


def normalize_sleeper_designation(injury_status: str | None) -> str:
    """Maps Sleeper's real `injury_status` value into the SAME
    OUT/DOUBTFUL/QUESTIONABLE/CLEARED_OR_NOT_LISTED vocabulary the
    benchmark uses, OR one of the disclosed non-designation buckets
    (`ON_LIST_*`, `DID_NOT_REPORT`) when the value is not a weekly
    game-status designation at all. An empty/'NA' value means Sleeper is
    not flagging anything -- treated the same as the benchmark's own
    'no designation' meaning, `CLEARED_OR_NOT_LISTED`."""

    value = (injury_status or "").strip()
    if not value or value == "NA":
        return "CLEARED_OR_NOT_LISTED"
    if value in SLEEPER_INJURY_STATUS_TO_DESIGNATION:
        return SLEEPER_INJURY_STATUS_TO_DESIGNATION[value]
    if value in SLEEPER_INJURY_STATUS_TO_LIST_STATUS:
        return SLEEPER_INJURY_STATUS_TO_LIST_STATUS[value]
    if value == "DNR":
        return "DID_NOT_REPORT"
    return f"UNRECOGNIZED:{value}"


def is_hard_out_like(normalized_category: str) -> bool:
    """A 'hard OUT-like' fact for the zero-contradictory-hard-status
    check: the official OUT designation, or a roster list (IR/PUP/
    Suspended) that means the player is definitely not playing."""

    return normalized_category == "OUT" or normalized_category.startswith("ON_LIST_")


def is_hard_active_like(normalized_category: str) -> bool:
    """The source affirmatively reports NO designation -- i.e. reports
    the player as healthy/active this week."""

    return normalized_category == "CLEARED_OR_NOT_LISTED"


@dataclass(frozen=True)
class AgreementPair:
    player_id: str
    benchmark_category: str
    candidate_category: str


@dataclass(frozen=True)
class AgreementResult:
    comparable_pairs: int
    exact_agreements: int
    agreement_ratio: float | None
    meets_gate: bool | None
    disagreements: tuple[AgreementPair, ...]
    hard_contradictions: tuple[AgreementPair, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparablePairs": self.comparable_pairs,
            "exactAgreements": self.exact_agreements,
            "agreementRatio": self.agreement_ratio,
            "meetsGate": self.meets_gate,
            "gateThreshold": GATE_3_AGREEMENT_THRESHOLD,
            "disagreements": [
                {"playerId": p.player_id, "benchmark": p.benchmark_category, "candidate": p.candidate_category}
                for p in self.disagreements
            ],
            "hardContradictions": [
                {"playerId": p.player_id, "benchmark": p.benchmark_category, "candidate": p.candidate_category}
                for p in self.hard_contradictions
            ],
            "zeroHardContradictions": len(self.hard_contradictions) == 0,
        }


def compute_agreement(pairs: Sequence[AgreementPair]) -> AgreementResult:
    """Gate 3. `pairs` should already be restricted to player-ids present
    in BOTH the benchmark and the candidate source. Two things are
    computed, per the directive, on the SAME pair set:
      1. Zero-contradictory-hard-status check -- any pair where one side
         is hard-OUT-like and the other is hard-ACTIVE-like (both
         directions checked).
      2. Exact-agreement ratio against the >=99% threshold -- restricted
         to pairs where BOTH sides carry a real, comparable weekly
         designation-shaped value (OUT/DOUBTFUL/QUESTIONABLE/
         CLEARED_OR_NOT_LISTED) -- an `ON_LIST_*`/`DID_NOT_REPORT`/
         `UNRECOGNIZED:*` candidate value is a real, different concept and
         is excluded from the exact-agreement denominator (never silently
         counted as either an agreement or a disagreement), but IS still
         checked by the hard-contradiction pass above."""

    hard_contradictions = tuple(
        p
        for p in pairs
        if (is_hard_out_like(p.benchmark_category) and is_hard_active_like(p.candidate_category))
        or (is_hard_active_like(p.benchmark_category) and is_hard_out_like(p.candidate_category))
    )

    _COMPARABLE = frozenset({"OUT", "DOUBTFUL", "QUESTIONABLE", "CLEARED_OR_NOT_LISTED"})
    comparable = [p for p in pairs if p.benchmark_category in _COMPARABLE and p.candidate_category in _COMPARABLE]
    if not comparable:
        return AgreementResult(0, 0, None, None, (), hard_contradictions)

    disagreements = tuple(p for p in comparable if p.benchmark_category != p.candidate_category)
    agreements = len(comparable) - len(disagreements)
    ratio = agreements / len(comparable)
    return AgreementResult(
        comparable_pairs=len(comparable),
        exact_agreements=agreements,
        agreement_ratio=round(ratio, 4),
        meets_gate=ratio >= GATE_3_AGREEMENT_THRESHOLD,
        disagreements=disagreements,
        hard_contradictions=hard_contradictions,
    )


# ---------------------------------------------------------------------------
# Gate 5 -- freshness
# ---------------------------------------------------------------------------


def diff_poll_rows(
    poll_a: Mapping[str, Mapping[str, Any]],
    poll_b: Mapping[str, Mapping[str, Any]],
    *,
    compare_fields: Sequence[str],
) -> dict[str, Any]:
    """Reusable revision-diff evidence: given two polls of the SAME
    keyed-by-id source (e.g. two successive nflverse injuries pulls keyed
    by `gsis_id`), reports which ids were added/removed, and how many
    shared ids changed on any of `compare_fields`. This is the only
    freshness proxy available for a source with no per-row update
    timestamp (see the module docstring)."""

    ids_a, ids_b = set(poll_a), set(poll_b)
    added = tuple(sorted(ids_b - ids_a))
    removed = tuple(sorted(ids_a - ids_b))
    changed: list[str] = []
    for pid in sorted(ids_a & ids_b):
        row_a, row_b = poll_a[pid], poll_b[pid]
        if any(row_a.get(field) != row_b.get(field) for field in compare_fields):
            changed.append(pid)
    return {
        "sharedIds": len(ids_a & ids_b),
        "added": list(added),
        "removed": list(removed),
        "changedIds": changed,
        "changedCount": len(changed),
    }


def summarize_seconds(values: Sequence[float]) -> dict[str, Any]:
    """P50/P95 over a real, non-empty sample of second-valued latencies.
    Honestly reports `None` for every statistic (never a fabricated
    number) when `values` is empty -- the caller is responsible for
    disclosing WHY no real sample exists in that case."""

    if not values:
        return {"sampleSize": 0, "p50Seconds": None, "p95Seconds": None, "maxSeconds": None, "minSeconds": None}
    ordered = sorted(values)
    n = len(ordered)

    def _percentile(p: float) -> float:
        if n == 1:
            return ordered[0]
        rank = p * (n - 1)
        lower = int(rank)
        upper = min(lower + 1, n - 1)
        frac = rank - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * frac

    return {
        "sampleSize": n,
        "p50Seconds": round(_percentile(0.50), 1),
        "p95Seconds": round(_percentile(0.95), 1),
        "maxSeconds": round(ordered[-1], 1),
        "minSeconds": round(ordered[0], 1),
    }
