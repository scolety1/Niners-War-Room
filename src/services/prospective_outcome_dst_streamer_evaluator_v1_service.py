"""Prospective Outcomes V1 -- Work Unit 10: DST STREAMER evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` (never bypassed,
never re-derives `streamerOpportunityCostPoints` -- that number is read
verbatim from the base evaluation). Per this cycle's governing directive
and the contract's own table (Section 1): DST_STREAMER is evaluated
INDEPENDENTLY from K_STREAMER.

=== WHY THIS IS A GENUINELY SEPARATE MODULE, NOT A SHARED "STREAMER"
FUNCTION PARAMETERIZED BY POSITION ===

This cycle's directive is explicit: "kept as a fully separate evaluation
(not merged into one 'streamer' evaluator that could blur K and DST regret
together)." This is the DST-side twin of
`prospective_outcome_k_streamer_evaluator_v1_service.py` -- its own
standalone module, its own standalone `evaluate_dst_streamer` function,
its own two hard gates: (1) `record.tool` must literally equal
`"DST_STREAMER"`, and (2) the stored detail's own `position` field must
literally equal `"DST"`. Neither module imports the other, and neither
shares a parameterized helper function -- they are two independently
written, independently tested code paths that happen to read the same
underlying `StreamerOutcomeDetail` schema shape (built once, in a prior
cycle, precisely because K_STREAMER/DST_STREAMER are meant to reuse ONE
schema while being evaluated as two separate instances -- contract Section
1's own explicit framing: "STREAMER_V1 (`position="K"`)" /
"STREAMER_V1 (`position="DST"`), evaluated INDEPENDENTLY of `K_STREAMER`").
`tests/test_prospective_outcome_dst_streamer_evaluator_v1_service.py`
proves a K-tagged trace passed to `evaluate_dst_streamer` is rejected (and
the K test file proves the reverse), demonstrating the two paths cannot
cross-contaminate.

=== METRICS COMPUTED ===

Identical DEFINITIONS to the K-side module (see its own docstring for the
full rationale of each), applied here to DST:
- `recommended_player_actual_points` / `actual_starter_actual_points` /
  `best_available_alternative_*` -- read verbatim from the stored
  `StreamerOutcomeDetail` payload. No new arithmetic.
- `current_option_player_id` / `current_option_actual_points` -- the real
  `priorRosterOptionPlayerId`/`priorRosterOptionActualPoints` fields, read
  verbatim (the DST actually on the roster before this streaming pickup --
  note DST ids are real Sleeper team codes, e.g. `"NE"`, per the schema
  module's own documented precedent, never a numeric player id).
- `regret_vs_actual_starter_points` -- the base evaluation's own
  `streamerOpportunityCostPoints`, read verbatim (never recomputed).
- `replacement_level_delta_points` -- the SAME honest, disclosed
  interpretation the K-side module uses:
  `recommendedPlayerActualPoints - priorRosterOptionActualPoints`. `None`
  when either side is not observable. Never substituted into
  `regret_vs_actual_starter_points`.

=== NEVER A HINDSIGHT-BEST ALTERNATIVE ===

`best_available_alternative_*` is read verbatim from the base detail,
itself (per `ingest_streamer_outcome`, unchanged, prior cycle) drawn only
from the trace's own frozen `available_alternative_ids_at_recommendation`
-- never a full-week hindsight search across every real DST that played
that week.

=== HARD BOUNDARY ===

Never compares against a defense that was not genuinely available/
rosterable at recommendation time. Never merges with the K evaluation.
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
    summary_status,
)

DETAIL_KIND = "STREAMER_V1"
EXPECTED_TOOL = "DST_STREAMER"
EXPECTED_POSITION = "DST"


@dataclass(frozen=True)
class DstStreamerEvaluatorResult:
    trace_id: str
    evaluation: OutcomeEvaluation
    recommended_player_id: str | None
    recommended_player_actual_points: float | None
    actual_starter_player_id: str | None
    actual_starter_actual_points: float | None
    current_option_player_id: str | None
    current_option_actual_points: float | None
    available_alternative_ids_at_recommendation: tuple[str, ...]
    best_available_alternative_id: str | None
    best_available_alternative_actual_points: float | None
    regret_vs_actual_starter_points: float | None
    replacement_level_delta_points: float | None
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "evaluation": self.evaluation.to_dict(),
            "position": EXPECTED_POSITION,
            "recommendedPlayerId": self.recommended_player_id,
            "recommendedPlayerActualPoints": self.recommended_player_actual_points,
            "actualStarterPlayerId": self.actual_starter_player_id,
            "actualStarterActualPoints": self.actual_starter_actual_points,
            "currentOptionPlayerId": self.current_option_player_id,
            "currentOptionActualPoints": self.current_option_actual_points,
            "availableAlternativeIdsAtRecommendation": list(self.available_alternative_ids_at_recommendation),
            "bestAvailableAlternativeId": self.best_available_alternative_id,
            "bestAvailableAlternativeActualPoints": self.best_available_alternative_actual_points,
            "regretVsActualStarterPoints": self.regret_vs_actual_starter_points,
            "replacementLevelDeltaPoints": self.replacement_level_delta_points,
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


def _empty_result(record: DecisionTraceRecord, evaluation: OutcomeEvaluation) -> DstStreamerEvaluatorResult:
    return DstStreamerEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        recommended_player_id=None,
        recommended_player_actual_points=None,
        actual_starter_player_id=None,
        actual_starter_actual_points=None,
        current_option_player_id=None,
        current_option_actual_points=None,
        available_alternative_ids_at_recommendation=(),
        best_available_alternative_id=None,
        best_available_alternative_actual_points=None,
        regret_vs_actual_starter_points=None,
        replacement_level_delta_points=None,
        issues=evaluation.issues,
    )


def _is_real_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluate_dst_streamer(record: DecisionTraceRecord) -> DstStreamerEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type != EXPECTED_TOOL:
        raise ValueError(f"evaluate_dst_streamer requires a {EXPECTED_TOOL} trace, got {evaluation.decision_type!r}.")

    detail = _detail_of(evaluation)
    if detail is None:
        return _empty_result(record, evaluation)

    position = detail.get("position")
    if position != EXPECTED_POSITION:
        # Defensive second gate -- see module docstring. A DST_STREAMER
        # trace whose stored detail claims a different position is a real
        # data integrity problem, not something this function silently
        # papers over by evaluating it anyway.
        raise ValueError(
            f"evaluate_dst_streamer requires a STREAMER_V1 detail with position={EXPECTED_POSITION!r}, "
            f"got {position!r}."
        )

    recommended_points = detail.get("recommendedPlayerActualPoints")
    current_option_points = detail.get("priorRosterOptionActualPoints")
    replacement_delta: float | None = None
    if _is_real_number(recommended_points) and _is_real_number(current_option_points):
        replacement_delta = round(float(recommended_points) - float(current_option_points), 2)

    return DstStreamerEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        recommended_player_id=detail.get("recommendedPlayerId"),
        recommended_player_actual_points=recommended_points,
        actual_starter_player_id=detail.get("actualStarterPlayerId"),
        actual_starter_actual_points=detail.get("actualStarterActualPoints"),
        current_option_player_id=detail.get("priorRosterOptionPlayerId"),
        current_option_actual_points=current_option_points,
        available_alternative_ids_at_recommendation=tuple(
            str(pid) for pid in detail.get("availableAlternativeIdsAtRecommendation") or []
        ),
        best_available_alternative_id=detail.get("bestAvailableAlternativeId"),
        best_available_alternative_actual_points=detail.get("bestAvailableAlternativeActualPoints"),
        regret_vs_actual_starter_points=evaluation.evaluation_metrics.get("streamerOpportunityCostPoints"),
        replacement_level_delta_points=replacement_delta,
        issues=evaluation.issues,
    )


def summarize_dst_streamer_evaluations(results: Sequence[DstStreamerEvaluatorResult]) -> dict[str, Any]:
    """Per-class-only aggregation (contract Section 6/9) -- DST's own
    numbers, never blended with K's (a completely separate summary function
    in a completely separate module)."""

    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.evaluation.evaluation_status] = status_counts.get(result.evaluation.evaluation_status, 0) + 1

    regrets = [
        result.regret_vs_actual_starter_points
        for result in results
        if result.evaluation.evaluation_status == "EVALUATED" and result.regret_vs_actual_starter_points is not None
    ]
    replacement_deltas = [
        result.replacement_level_delta_points for result in results if result.replacement_level_delta_points is not None
    ]
    regret_status = summary_status(len(regrets))
    replacement_status = summary_status(len(replacement_deltas))

    summary: dict[str, Any] = {
        "decisionType": "DST_STREAMER",
        "statusCounts": status_counts,
        "regretVsActualStarter": {"summaryStatus": regret_status, "sampleSize": len(regrets)},
        "replacementLevelDelta": {"summaryStatus": replacement_status, "sampleSize": len(replacement_deltas)},
    }
    if regret_status == "SUMMARIZED":
        summary["regretVsActualStarter"]["meanRegretPoints"] = mean_of(regrets)
    if replacement_status == "SUMMARIZED":
        summary["replacementLevelDelta"]["meanReplacementLevelDeltaPoints"] = mean_of(replacement_deltas)
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


_assert_evaluator_signature_is_safe(evaluate_dst_streamer)
