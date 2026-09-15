"""Prospective Outcomes V1 -- shared helpers for the per-class EVALUATOR
modules (Work Units 3-6: Start/Sit, Waiver, Add/Drop, FAAB).

Per `docs/codex/prospective_outcomes_v1/PROSPECTIVE_OUTCOME_EVALUATION_CONTRACT.md`
Section 9 / LEDGER.md Open Issue 1: this cycle's Worker 1 built the
single-event `OutcomeEvaluation` contract only (`compute_outcome_evaluation`,
one trace in, one evaluation out). Real per-class AGGREGATION/SUMMARY across
MANY real outcomes -- gated by the contract's own Section 7 minimum-sample
rule -- is explicitly this worker's job. This tiny module holds the ONE
shared piece every per-class summary function needs so the gate/statistics
helpers are not reimplemented four times with four chances to drift.

Reuses (does not redefine) `MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY` from
`prospective_outcome_evaluation_v1_service.py` (already the same number,
20, as the frontend's own `MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP` --
contract Section 7's disclosed duplicated-constant gap, unchanged here).
"""

from __future__ import annotations

from typing import Sequence

from src.services.prospective_outcome_evaluation_v1_service import (
    MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY,
)

NOT_ENOUGH_DATA_YET = "NOT_ENOUGH_DATA_YET"
SUMMARIZED = "SUMMARIZED"


def summary_status(sample_size: int, *, minimum: int = MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY) -> str:
    """Contract Section 7: below the minimum, a per-class summary MUST show
    an honest "not enough data yet" status rather than a number computed
    from too few real outcomes to mean anything."""

    return SUMMARIZED if sample_size >= minimum else NOT_ENOUGH_DATA_YET


def mean_of(values: Sequence[float | None]) -> float | None:
    """Ignores `None` entries (an evaluation that could not honestly
    compute a value is not the same as a real zero) -- `None` only when
    there is nothing real to average."""

    real_values = [float(value) for value in values if value is not None]
    if not real_values:
        return None
    return round(sum(real_values) / len(real_values), 2)


def rate_of(values: Sequence[bool | None]) -> float | None:
    """Fraction `True` among the non-`None` entries -- `None` only when
    there is nothing real to compute a rate over. A real, observed `False`
    (e.g. "claim not submitted") counts fully in the denominator -- it is
    real data, not an unknown (contract's own WAIVER framing)."""

    real_values = [bool(value) for value in values if value is not None]
    if not real_values:
        return None
    return round(sum(1 for value in real_values if value) / len(real_values), 4)
