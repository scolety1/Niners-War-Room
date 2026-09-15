"""Prospective Outcomes V1 -- Work Unit 4: WAIVER evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` and
`recommendation_time_context_from_trace` (never bypassed). Per this cycle's
governing directive: "Separate RECOMMENDATION QUALITY from TRANSACTION
EXECUTION" -- and per the directive's own explicit instruction, "If a claim
was never submitted, that's adoption/follow-through information, not
automatic recommendation failure -- keep these conceptually distinct in the
output."

=== A REAL, DISCLOSED REFINEMENT OVER THE BASE `OutcomeEvaluation` LAYER ===

`compute_outcome_evaluation`'s own `_extract_waiver` (Worker 1) intentionally
blanks ALL of `claimSubmitted`/`claimWon`/`faabPaid` to `{}` whenever the
evaluation status is `PENDING_WINDOW` (claim won, bounded-horizon subsequent
value not yet observed) -- a structural side effect of `OutcomeEvaluation`
having exactly ONE `evaluationStatus` per record (its own
`__post_init__` forbids a non-`EVALUATED` status from carrying any non-`None`
metric value, contract Section 4). That is correct for the SINGLE combined
evaluation-status field, but it silently erases a REAL, already-known fact:
whether the claim was submitted/won is observable immediately, independent
of whether the horizon has closed yet.

This module reads `claimSubmitted`/`claimWon`/`faabPaid`/
`subsequentTotalPoints`/`subsequentRosterUsageWeeks` directly from the
already-stored, already-computed `outcome.detail` payload (not from
`evaluation.evaluation_metrics`) precisely so a real, observed "claim
submitted=True, won=True, window still pending" fact is never lost just
because the aggregate status hasn't reached `EVALUATED` yet. No new
arithmetic is invented here -- every field is read verbatim from the SAME
`WaiverOutcomeDetail.to_detail_dict()` payload
`prospective_outcome_ingestion_v1_service.ingest_waiver_outcome` already
produced, using the PREREGISTERED 4-week horizon (contract Section 3,
`DEFAULT_HORIZON_WEEKS`) it was computed with -- never a new/invented
horizon.

=== CLAIMABLE AT RECOMMENDATION TIME ===

`claimable_at_recommendation_time` is a NEW, honest reconstruction this
module adds: was `recommendedPlayerId` actually present in the trace's own
FROZEN `free_agent_state_player_ids` (via
`recommendation_time_context_from_trace` -- zero network I/O, the trace's
own recorded field, never a "current" free-agent read)? When a call site
never recorded a free-agent snapshot at all (`free_agent_state_player_ids
is None` -- a real, disclosed gap for some real call sites, e.g. the FAAB
tool's own trace does not populate this field), this stays honestly `None`
with an issue, never guessed `True`/`False`.

=== HARD BOUNDARY ===

Never invents opponent-roster claim probabilities, never treats a hidden or
still-pending claim as observable, never changes the preregistered 4-week
horizon.
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
from src.services.prospective_outcome_source_adapter_v1_service import (
    RecommendationTimeContext,
    recommendation_time_context_from_trace,
)

DETAIL_KIND = "WAIVER_V1"

# Real, already-used trace `recommendation` payload key names this module
# will honestly check for a "recommended drop" concept -- WAIVER's own
# schema (WaiverOutcomeDetail) carries no structured drop field (that
# concept belongs to ADD_DROP); a waiver claim does not always imply a
# planned drop. `None` (not fabricated) when none of these keys were ever
# populated by the real call site that recorded this trace.
_RECOMMENDATION_DROP_KEYS = ("dropCanonicalId", "dropPlayerId", "recommendedDropPlayerId")


@dataclass(frozen=True)
class WaiverEvaluatorResult:
    trace_id: str
    evaluation: OutcomeEvaluation
    recommended_player_id: str | None
    recommended_drop_player_id: str | None
    claimable_at_recommendation_time: bool | None
    claim_submitted: bool | None
    claim_won: bool | None
    faab_paid: float | None
    horizon_weeks: int | None
    subsequent_total_points: float | None
    subsequent_roster_usage_weeks: int | None
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "evaluation": self.evaluation.to_dict(),
            "recommendedPlayerId": self.recommended_player_id,
            "recommendedDropPlayerId": self.recommended_drop_player_id,
            "claimableAtRecommendationTime": self.claimable_at_recommendation_time,
            "claimSubmitted": self.claim_submitted,
            "claimWon": self.claim_won,
            "faabPaid": self.faab_paid,
            "horizonWeeks": self.horizon_weeks,
            "subsequentTotalPoints": self.subsequent_total_points,
            "subsequentRosterUsageWeeks": self.subsequent_roster_usage_weeks,
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


def _recommended_drop_id(context: RecommendationTimeContext) -> str | None:
    for key in _RECOMMENDATION_DROP_KEYS:
        value = context.recommendation.get(key)
        if value is not None:
            return str(value)
    return None


def evaluate_waiver(
    record: DecisionTraceRecord, *, context: RecommendationTimeContext | None = None
) -> WaiverEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type != "WAIVER":
        raise ValueError(f"evaluate_waiver requires a WAIVER trace, got {evaluation.decision_type!r}.")

    ctx = context if context is not None else recommendation_time_context_from_trace(record)
    detail = _detail_of(evaluation)
    issues = list(evaluation.issues)

    if detail is None:
        return WaiverEvaluatorResult(
            trace_id=record.trace_id,
            evaluation=evaluation,
            recommended_player_id=None,
            recommended_drop_player_id=_recommended_drop_id(ctx),
            claimable_at_recommendation_time=None,
            claim_submitted=None,
            claim_won=None,
            faab_paid=None,
            horizon_weeks=None,
            subsequent_total_points=None,
            subsequent_roster_usage_weeks=None,
            issues=tuple(issues),
        )

    recommended_player_id = detail.get("recommendedPlayerId")
    claimable_at_recommendation_time: bool | None = None
    if recommended_player_id is not None:
        if ctx.free_agent_state_player_ids is not None:
            claimable_at_recommendation_time = str(recommended_player_id) in ctx.free_agent_state_player_ids
        else:
            issues.append(
                "claimableAtRecommendationTime could not be determined -- this trace's "
                "free_agent_state_player_ids was never recorded at recommendation time."
            )

    return WaiverEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        recommended_player_id=str(recommended_player_id) if recommended_player_id is not None else None,
        recommended_drop_player_id=_recommended_drop_id(ctx),
        claimable_at_recommendation_time=claimable_at_recommendation_time,
        claim_submitted=detail.get("claimSubmitted"),
        claim_won=detail.get("claimWon"),
        faab_paid=detail.get("faabPaid"),
        horizon_weeks=detail.get("horizonWeeks"),
        subsequent_total_points=detail.get("subsequentTotalPoints"),
        subsequent_roster_usage_weeks=detail.get("subsequentRosterUsageWeeks"),
        issues=tuple(issues),
    )


def summarize_waiver_evaluations(results: Sequence[WaiverEvaluatorResult]) -> dict[str, Any]:
    """Two genuinely separate axes, gated INDEPENDENTLY (mirrors FAAB's own
    split, and the directive's own "adoption/follow-through is not
    recommendation failure" instruction): claim-win-rate (TRANSACTION
    EXECUTION, gated on every real submitted-or-not claim) and mean
    subsequent value (RECOMMENDATION QUALITY, gated only on real won claims
    with an observed horizon)."""

    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.evaluation.evaluation_status] = (
            status_counts.get(result.evaluation.evaluation_status, 0) + 1
        )

    submitted_flags = [result.claim_submitted for result in results if result.claim_submitted is not None]
    won_flags = [result.claim_won for result in results if result.claim_submitted]
    won_status = summary_status(len(won_flags))
    submitted_status = summary_status(len(submitted_flags))

    subsequent_points = [
        result.subsequent_total_points for result in results if result.claim_won and result.subsequent_total_points is not None
    ]
    value_status = summary_status(len(subsequent_points))

    summary: dict[str, Any] = {
        "decisionType": "WAIVER",
        "statusCounts": status_counts,
        "claimSubmissionRate": {
            "summaryStatus": submitted_status,
            "sampleSize": len(submitted_flags),
        },
        "claimWinRate": {
            "summaryStatus": won_status,
            "sampleSize": len(won_flags),
        },
        "subsequentValue": {
            "summaryStatus": value_status,
            "sampleSize": len(subsequent_points),
        },
    }
    if submitted_status == "SUMMARIZED":
        summary["claimSubmissionRate"]["rate"] = rate_of(submitted_flags)
    if won_status == "SUMMARIZED":
        summary["claimWinRate"]["rate"] = rate_of(won_flags)
    if value_status == "SUMMARIZED":
        summary["subsequentValue"]["meanSubsequentTotalPoints"] = mean_of(subsequent_points)
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


_assert_evaluator_signature_is_safe(evaluate_waiver)
