"""K/DST Prospective Benchmark V1 (NWR Prospective Outcomes V1, Work Unit
17) -- SCAFFOLDING, not a full multi-week study.

Preregistered design: `docs/codex/prospective_outcomes_v1/KDST_
PROSPECTIVE_BENCHMARK_V1.md` (read that first -- it documents a real,
mechanical DST identity-matching defect this cycle found in
`fantasypros_kdst_consensus_service.py` and explains why this pass does
NOT fix it, per the hard boundary).

This module is pure composition over ALREADY-FETCHED real inputs (real
FantasyPros consensus rows, real Sleeper roster/projection/stats
payloads) -- it performs NO network I/O itself, matching this cycle's own
established "network at the edges, pure composition in the middle"
discipline (see `prospective_outcome_source_adapter_v1_service.py`).
Never modifies, re-implements, or bypasses `fantasypros_kdst_consensus_
service.py`'s own `streamer_actions`/`sleeper_streamer_actions` -- this
module CALLS those real functions to build Arm 1 (NWR_RECOMMENDATION),
never re-deriving that logic independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# A disclosed, arbitrary transparency floor -- NOT a claim of statistical
# power at this count. See the design doc's "Sample-size honesty rule".
PRELIMINARY_SAMPLE_SIZE_WEEKS_FLOOR = 8

ARM_NWR_RECOMMENDATION = "NWR_RECOMMENDATION"
ARM_PROVIDER_CONSENSUS = "PROVIDER_CONSENSUS"
ARM_RAW_PROJECTION = "RAW_PROJECTION"
ARM_REPLACEMENT_LEVEL = "REPLACEMENT_LEVEL"
ARM_NAMES = (ARM_NWR_RECOMMENDATION, ARM_PROVIDER_CONSENSUS, ARM_RAW_PROJECTION, ARM_REPLACEMENT_LEVEL)

DATA_STATUS_OK = "OK"
DATA_STATUS_NOT_AVAILABLE = "NOT_AVAILABLE"
DATA_STATUS_PENDING = "PENDING"

# FantasyPros team code -> Sleeper team code. Every other real team code
# checked live this pass matched exactly; this is the one real, disclosed
# exception (see the design doc). This benchmark's own join logic only --
# `fantasypros_kdst_consensus_service.py` itself is untouched and its own
# (name-based, not team-code-based) identity join is unaffected.
FANTASYPROS_TO_SLEEPER_TEAM_CODE: Mapping[str, str] = {"JAC": "JAX"}


def sleeper_team_code(fantasypros_team_code: str) -> str:
    return FANTASYPROS_TO_SLEEPER_TEAM_CODE.get(fantasypros_team_code, fantasypros_team_code)


@dataclass(frozen=True)
class KdstBenchmarkArmResult:
    arm: str
    player_id: str | None  # Sleeper id, or None if the arm has no real candidate
    player_name: str | None
    team: str | None
    source_value: float | None  # ECR rank (lower=better) or projected points (higher=better), per arm
    actual_points: float | None
    data_status: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "playerId": self.player_id,
            "playerName": self.player_name,
            "team": self.team,
            "sourceValue": self.source_value,
            "actualPoints": self.actual_points,
            "dataStatus": self.data_status,
            "note": self.note,
        }


@dataclass(frozen=True)
class KdstBenchmarkWeekRecord:
    season: int
    week: int
    position: str  # "K" | "DST"
    league_id: str
    owner_roster_id: str
    arms: tuple[KdstBenchmarkArmResult, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def arm(self, name: str) -> KdstBenchmarkArmResult | None:
        return next((a for a in self.arms if a.arm == name), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "season": self.season,
            "week": self.week,
            "position": self.position,
            "leagueId": self.league_id,
            "ownerRosterId": self.owner_roster_id,
            "arms": [a.to_dict() for a in self.arms],
            "notes": list(self.notes),
        }


def build_kdst_benchmark_week_record(
    *,
    season: int,
    week: int,
    position: str,
    league_id: str,
    owner_roster_id: str,
    nwr_recommendation: Mapping[str, Any] | None,
    provider_consensus_rank1: Mapping[str, Any] | None,
    raw_projection_best: Mapping[str, Any] | None,
    replacement_level_current: Mapping[str, Any] | None,
    actual_points_by_sleeper_id: Mapping[str, float],
    notes: Sequence[str] = (),
) -> KdstBenchmarkWeekRecord:
    """Pure composition. Each `*_best`/`*_current`/`*_rank1` argument is a
    plain mapping the CALLER already built from real, already-fetched data
    (e.g. `{"playerId": "...", "playerName": "...", "team": "...",
    "ecr": 3}` or `{"playerId": "...", "projectedPoints": 12.4}`) -- this
    function performs no lookups of its own beyond joining real actual
    points by Sleeper id, and never fabricates a candidate that was not
    supplied."""

    if position not in ("K", "DST"):
        raise ValueError(f"position must be 'K' or 'DST', got {position!r}.")

    def _arm(arm_name: str, source: Mapping[str, Any] | None, *, value_key: str) -> KdstBenchmarkArmResult:
        if source is None:
            return KdstBenchmarkArmResult(
                arm=arm_name, player_id=None, player_name=None, team=None, source_value=None,
                actual_points=None, data_status=DATA_STATUS_NOT_AVAILABLE,
                note="No real candidate was supplied for this arm this week.",
            )
        player_id = source.get("playerId")
        actual = actual_points_by_sleeper_id.get(str(player_id)) if player_id else None
        return KdstBenchmarkArmResult(
            arm=arm_name, player_id=str(player_id) if player_id else None,
            player_name=source.get("playerName"), team=source.get("team"),
            source_value=source.get(value_key),
            actual_points=actual,
            data_status=DATA_STATUS_OK if actual is not None else DATA_STATUS_PENDING,
        )

    arms = (
        _arm(ARM_NWR_RECOMMENDATION, nwr_recommendation, value_key="ecr"),
        _arm(ARM_PROVIDER_CONSENSUS, provider_consensus_rank1, value_key="ecr"),
        _arm(ARM_RAW_PROJECTION, raw_projection_best, value_key="projectedPoints"),
        _arm(ARM_REPLACEMENT_LEVEL, replacement_level_current, value_key="ecr"),
    )
    return KdstBenchmarkWeekRecord(
        season=season, week=week, position=position, league_id=league_id,
        owner_roster_id=owner_roster_id, arms=arms, notes=tuple(notes),
    )


def compare_arms(record: KdstBenchmarkWeekRecord) -> dict[str, Any]:
    """Real, honest deltas vs the NWR_RECOMMENDATION arm -- `None` for any
    pair where either side's real actual points are not yet observable.
    Never substitutes a projected/ECR value in place of a missing real
    result."""

    nwr = record.arm(ARM_NWR_RECOMMENDATION)
    deltas: dict[str, float | None] = {}
    for arm_name in (ARM_PROVIDER_CONSENSUS, ARM_RAW_PROJECTION, ARM_REPLACEMENT_LEVEL):
        other = record.arm(arm_name)
        if (
            nwr is not None and other is not None
            and nwr.actual_points is not None and other.actual_points is not None
        ):
            deltas[arm_name] = round(other.actual_points - nwr.actual_points, 2)
        else:
            deltas[arm_name] = None
    return {
        "season": record.season, "week": record.week, "position": record.position,
        "nwrRecommendationActualPoints": nwr.actual_points if nwr else None,
        # Positive delta means the OTHER arm out-scored NWR's real pick
        # that week; negative means NWR's real pick out-scored it.
        "deltaVsProviderConsensus": deltas[ARM_PROVIDER_CONSENSUS],
        "deltaVsRawProjection": deltas[ARM_RAW_PROJECTION],
        "deltaVsReplacementLevel": deltas[ARM_REPLACEMENT_LEVEL],
    }


def summarize_kdst_benchmark(records: Sequence[KdstBenchmarkWeekRecord]) -> dict[str, Any]:
    """Aggregates across whatever real weeks have actually been recorded.
    ALWAYS reports the real sample size; ALWAYS labels the result
    `PRELIMINARY` while that count is below the disclosed transparency
    floor. Never computes a false "verdict" from a tiny sample -- this
    function reports raw per-week comparisons, not a synthesized
    conclusion, regardless of sample size."""

    by_position: dict[str, list[dict[str, Any]]] = {"K": [], "DST": []}
    for record in records:
        by_position.setdefault(record.position, []).append(compare_arms(record))

    def _mean_of(values: Sequence[float | None]) -> float | None:
        real = [v for v in values if v is not None]
        return round(sum(real) / len(real), 2) if real else None

    report: dict[str, Any] = {"generatedFromRealWeeks": len(records)}
    for position, comparisons in by_position.items():
        sample_size = len(comparisons)
        report[position] = {
            "sampleSizeWeeks": sample_size,
            "sampleSizeLabel": (
                "PRELIMINARY" if sample_size < PRELIMINARY_SAMPLE_SIZE_WEEKS_FLOOR else "STANDARD"
            ),
            "meanDeltaVsProviderConsensus": _mean_of([c["deltaVsProviderConsensus"] for c in comparisons]),
            "meanDeltaVsRawProjection": _mean_of([c["deltaVsRawProjection"] for c in comparisons]),
            "meanDeltaVsReplacementLevel": _mean_of([c["deltaVsReplacementLevel"] for c in comparisons]),
            "perWeekComparisons": comparisons,
        }
    return report
