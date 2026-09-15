"""Prospective Outcomes V1 -- Work Unit 9: K STREAMER evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` (never bypassed,
never re-derives `streamerOpportunityCostPoints` -- that number is read
verbatim from the base evaluation). Per this cycle's governing directive
and the contract's own table (Section 1): K_STREAMER is evaluated
INDEPENDENTLY from DST_STREAMER.

=== WHY THIS IS A GENUINELY SEPARATE MODULE, NOT A SHARED "STREAMER"
FUNCTION PARAMETERIZED BY POSITION ===

This cycle's directive is explicit: "kept as a fully separate evaluation
(not merged into one 'streamer' evaluator that could blur K and DST regret
together)." This module is intentionally NOT a thin wrapper that calls a
shared `_evaluate_streamer(position=...)` helper -- `evaluate_k_streamer`
is its own standalone function, in its own file, with its own two hard
gates: (1) `record.tool` must literally equal `"K_STREAMER"` (a wrong-tool
trace is rejected outright), and (2) the stored detail's own `position`
field must literally equal `"K"` (a defensive second check -- if a K_STREAMER
trace's detail was somehow mis-tagged `"DST"`, this function refuses to
silently evaluate it as a K result). See
`prospective_outcome_dst_streamer_evaluator_v1_service.py` for the
DST-side twin, which is its own independent module with its own two gates
-- proven genuinely separate by
`tests/test_prospective_outcome_k_streamer_evaluator_v1_service.py`'s own
cross-contamination tests (a DST-tagged trace passed to
`evaluate_k_streamer` is rejected, and vice versa in the DST test file).

=== METRICS COMPUTED ===

- `recommended_player_actual_points` / `actual_starter_actual_points` /
  `best_available_alternative_*` -- read verbatim from the already-stored
  `StreamerOutcomeDetail` payload (`prospective_outcome_schema_v1_service.py`,
  prior cycle). No new arithmetic.
- `current_option_player_id` / `current_option_actual_points` -- the SAME
  real field the schema already calls `priorRosterOptionPlayerId`/
  `priorRosterOptionActualPoints` (the K who was actually on the roster
  BEFORE this streaming recommendation), read verbatim, under a clearer
  name for this evaluation layer's own output.
- `regret_vs_actual_starter_points` -- the base evaluation's own
  `streamerOpportunityCostPoints`, read verbatim (never recomputed): real
  points the recommended K actually scored minus real points the K the
  owner actually started scored.
- `replacement_level_delta_points` -- ONE NEW, simple, transparent number
  this evaluation layer adds: `recommendedPlayerActualPoints -
  priorRosterOptionActualPoints`. This is this pass's own honest,
  disclosed interpretation of the directive's "replacement-level
  comparison" -- the real replacement-level baseline this schema already
  tracks is the player who WOULD have stayed rostered/started absent the
  streaming pickup (`priorRosterOptionPlayerId`), not a synthesized
  league-average bench score (which this codebase has no real, non-
  fabricated source for at this layer). `None` when either side's real
  points are not observable. NEVER substituted into
  `regret_vs_actual_starter_points` -- reported alongside it, per the
  contract's own explicit rule (Section 5, rule 4) against silently
  swapping one comparison for another.

=== NEVER A HINDSIGHT-BEST ALTERNATIVE ===

`best_available_alternative_*` is read verbatim from the base detail,
which itself (per `ingest_streamer_outcome`, unchanged, prior cycle) draws
candidates ONLY from `available_alternative_ids_at_recommendation` -- the
trace's own frozen, at-recommendation-time alternative set, never a
full-week hindsight search. This module never promotes that field into
`regret_vs_actual_starter_points`, matching the contract's own explicit
K/DST_STREAMER rule.

=== HARD BOUNDARY ===

Never compares against a kicker who was not genuinely available/rosterable
at recommendation time (structurally guaranteed by the base ingestion
layer, reused unchanged). Never merges with the DST evaluation.
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
EXPECTED_TOOL = "K_STREAMER"
EXPECTED_POSITION = "K"


@dataclass(frozen=True)
class KStreamerEvaluatorResult:
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


def _empty_result(record: DecisionTraceRecord, evaluation: OutcomeEvaluation) -> KStreamerEvaluatorResult:
    return KStreamerEvaluatorResult(
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


def evaluate_k_streamer(record: DecisionTraceRecord) -> KStreamerEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type != EXPECTED_TOOL:
        raise ValueError(f"evaluate_k_streamer requires a {EXPECTED_TOOL} trace, got {evaluation.decision_type!r}.")

    detail = _detail_of(evaluation)
    if detail is None:
        return _empty_result(record, evaluation)

    position = detail.get("position")
    if position != EXPECTED_POSITION:
        # Defensive second gate -- see module docstring. A K_STREAMER trace
        # whose stored detail claims a different position is a real data
        # integrity problem, not something this function silently papers
        # over by evaluating it anyway.
        raise ValueError(
            f"evaluate_k_streamer requires a STREAMER_V1 detail with position={EXPECTED_POSITION!r}, "
            f"got {position!r}."
        )

    recommended_points = detail.get("recommendedPlayerActualPoints")
    current_option_points = detail.get("priorRosterOptionActualPoints")
    def _is_real_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    replacement_delta: float | None = None
    if _is_real_number(recommended_points) and _is_real_number(current_option_points):
        replacement_delta = round(float(recommended_points) - float(current_option_points), 2)

    return KStreamerEvaluatorResult(
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


def summarize_k_streamer_evaluations(results: Sequence[KStreamerEvaluatorResult]) -> dict[str, Any]:
    """Per-class-only aggregation (contract Section 6/9) -- K's own numbers,
    never blended with DST's (a completely separate summary function in a
    completely separate module)."""

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
        "decisionType": "K_STREAMER",
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


_assert_evaluator_signature_is_safe(evaluate_k_streamer)
