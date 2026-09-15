"""Prospective Outcomes V1 -- Work Unit 6: FAAB evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` (never bypassed).
Per this cycle's governing directive: separate two questions structurally
-- (A) was the player a good acquisition target (`player_decision_quality`,
mirrors WAIVER's own subsequent-value axis), (B) was the suggested bid
range calibrated (`bid_range_calibration`). This mirrors the
`FaabPlayerDecisionQuality`/`FaabBidRangeCalibration` split already built
into `prospective_outcome_schema_v1_service.py` in a prior cycle -- REUSED
verbatim here, never re-derived or merged.

This module reads both nested objects directly, verbatim, from the
already-stored `outcome.detail` payload -- no new arithmetic. The one real
value this module adds over the base `OutcomeEvaluation` layer is
AGGREGATION: `summarize_faab_evaluations` gates the two axes INDEPENDENTLY
(contract Section 7's minimum-sample rule, applied separately to each
axis's own real sample count) -- one axis can clear the bar while the
other genuinely has not, and the two summaries are never combined into one
figure.

=== HARD BOUNDARY ===

Never uses a hidden/pending bid that was never observable (this module only
ever reads `actualWinningBid`, sourced upstream by
`ingest_faab_outcome`/`_actual_winning_bid_for_player` from a real,
COMPLETED Sleeper transaction -- never an in-flight/pending one). Never
invents an opponent bid probability.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_evaluation_v1_service import (
    OutcomeEvaluation,
    compute_outcome_evaluation,
)
from src.services.prospective_outcome_evaluator_shared_v1_service import (
    mean_of,
    rate_of,
    summary_status,
)

DETAIL_KIND = "FAAB_V1"


@dataclass(frozen=True)
class FaabEvaluatorResult:
    trace_id: str
    evaluation: OutcomeEvaluation
    recommended_player_id: str | None
    player_decision_quality: dict[str, Any] | None
    bid_range_calibration: dict[str, Any] | None
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "evaluation": self.evaluation.to_dict(),
            "recommendedPlayerId": self.recommended_player_id,
            # Deliberately TWO SEPARATE keys, never merged (contract/directive).
            "playerDecisionQuality": self.player_decision_quality,
            "bidRangeCalibration": self.bid_range_calibration,
            "issues": list(self.issues),
        }


def _detail_of(evaluation: OutcomeEvaluation) -> Mapping[str, Any] | None:
    factual = evaluation.factual_outcome
    if not isinstance(factual, Mapping):
        return None
    detail = factual.get("detail")
    if not isinstance(detail, Mapping) or detail.get("kind") != DETAIL_KIND:
        return None
    return detail


def evaluate_faab(record: DecisionTraceRecord) -> FaabEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type != "FAAB":
        raise ValueError(f"evaluate_faab requires a FAAB trace, got {evaluation.decision_type!r}.")

    detail = _detail_of(evaluation)
    if detail is None:
        return FaabEvaluatorResult(
            trace_id=record.trace_id,
            evaluation=evaluation,
            recommended_player_id=None,
            player_decision_quality=None,
            bid_range_calibration=None,
            issues=evaluation.issues,
        )

    quality = detail.get("playerDecisionQuality")
    calibration = detail.get("bidRangeCalibration")
    recommended_player_id = detail.get("recommendedPlayerId")
    return FaabEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        recommended_player_id=str(recommended_player_id) if recommended_player_id is not None else None,
        player_decision_quality=dict(quality) if isinstance(quality, Mapping) else None,
        bid_range_calibration=dict(calibration) if isinstance(calibration, Mapping) else None,
        issues=evaluation.issues,
    )


def summarize_faab_evaluations(results: Sequence[FaabEvaluatorResult]) -> dict[str, Any]:
    """TWO independently-gated summaries -- see module docstring. Neither
    axis's sample size or gate status is derived from, or influences, the
    other's."""

    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.evaluation.evaluation_status] = (
            status_counts.get(result.evaluation.evaluation_status, 0) + 1
        )

    quality_points = [
        result.player_decision_quality.get("subsequentPoints")
        for result in results
        if result.player_decision_quality is not None and result.player_decision_quality.get("subsequentPoints") is not None
    ]
    quality_status = summary_status(len(quality_points))

    calibration_flags = [
        result.bid_range_calibration.get("bidWithinSuggestedRange")
        for result in results
        if result.bid_range_calibration is not None
        and result.bid_range_calibration.get("bidWithinSuggestedRange") is not None
    ]
    calibration_status = summary_status(len(calibration_flags))

    summary: dict[str, Any] = {
        "decisionType": "FAAB",
        "statusCounts": status_counts,
        "playerDecisionQuality": {
            "summaryStatus": quality_status,
            "sampleSize": len(quality_points),
        },
        "bidRangeCalibration": {
            "summaryStatus": calibration_status,
            "sampleSize": len(calibration_flags),
        },
    }
    if quality_status == "SUMMARIZED":
        summary["playerDecisionQuality"]["meanSubsequentPoints"] = mean_of(quality_points)
    if calibration_status == "SUMMARIZED":
        summary["bidRangeCalibration"]["bidWithinSuggestedRangeRate"] = rate_of(calibration_flags)
    return summary


_FORBIDDEN_PARAMETER_NAME_FRAGMENTS = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")


def _assert_evaluator_signature_is_safe(function: Any) -> None:
    for name in inspect.signature(function).parameters:
        lowered = name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_PARAMETER_NAME_FRAGMENTS):
            raise ValueError(
                f"{function.__qualname__} accepts a parameter named {name!r}, matching a forbidden "
                "'current state' naming pattern -- an evaluator must only ever consume the trace's own "
                "frozen fields and already-fetched outcome data."
            )


_assert_evaluator_signature_is_safe(evaluate_faab)
