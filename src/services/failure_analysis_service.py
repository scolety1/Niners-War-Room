"""Failure analysis slicing (directive section 17).

When a challenger loses (or a strategy underperforms), preserve WHY --
this module slices a set of real evaluation records by any named
dimension (position, rookie/veteran, league size, 1QB/Superflex, draft
round, market tier, ADP-disagreement magnitude, injury/availability
class, score uncertainty, ...) so a future AI research system (section
18) can inspect where a challenger actually struggled rather than only
its aggregate score.

Pure aggregation over caller-supplied records -- computes no evaluation
metric itself; a `record` is any mapping of dimension name -> value plus
one `outcome_value` (already computed elsewhere, e.g. realized pick
regret or a Team Score delta).
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

MIN_SLICE_SAMPLE_SIZE = 3  # below this, a slice's mean is flagged low-confidence, not hidden


class FailureAnalysisError(ValueError):
    pass


@dataclass(frozen=True)
class EvaluationRecord:
    record_id: str
    dimensions: Mapping[str, Any]
    outcome_value: float


@dataclass(frozen=True)
class SliceResult:
    dimension_name: str
    dimension_value: Any
    sample_size: int
    mean_outcome: float
    low_confidence: bool
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class FailureSliceReport:
    dimension_name: str
    slices: tuple[SliceResult, ...]
    worst_slice: SliceResult | None
    best_slice: SliceResult | None


def slice_by_dimension(
    records: Sequence[EvaluationRecord], *, dimension_name: str
) -> FailureSliceReport:
    """Groups records by `dimensions[dimension_name]`. A record missing
    that dimension is simply excluded from this report (not silently
    counted into a default bucket) -- callers wanting to know about
    missing-dimension coverage should check `records` vs.
    `sum(s.sample_size for s in report.slices)` themselves."""
    groups: dict[Any, list[EvaluationRecord]] = {}
    for record in records:
        if dimension_name not in record.dimensions:
            continue
        groups.setdefault(record.dimensions[dimension_name], []).append(record)
    if not groups:
        raise FailureAnalysisError(
            f"No record carries dimension {dimension_name!r} -- nothing to slice."
        )
    slices: list[SliceResult] = []
    for value, group in groups.items():
        outcomes = [r.outcome_value for r in group]
        slices.append(
            SliceResult(
                dimension_name=dimension_name, dimension_value=value, sample_size=len(group),
                mean_outcome=round(statistics.fmean(outcomes), 4),
                low_confidence=len(group) < MIN_SLICE_SAMPLE_SIZE,
                record_ids=tuple(r.record_id for r in group),
            )
        )
    slices.sort(key=lambda s: s.mean_outcome)
    return FailureSliceReport(
        dimension_name=dimension_name, slices=tuple(slices),
        worst_slice=slices[0] if slices else None,
        best_slice=slices[-1] if slices else None,
    )


def slice_by_every_dimension(
    records: Sequence[EvaluationRecord], *, dimension_names: Sequence[str]
) -> dict[str, FailureSliceReport]:
    """Convenience: runs slice_by_dimension for every named dimension,
    skipping (not erroring on) a dimension no record carries at all --
    a caller inspecting many candidate dimensions should not have one
    absent dimension abort the whole analysis."""
    reports: dict[str, FailureSliceReport] = {}
    for name in dimension_names:
        try:
            reports[name] = slice_by_dimension(records, dimension_name=name)
        except FailureAnalysisError:
            continue
    return reports
