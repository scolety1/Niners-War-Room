"""Prospective Outcomes V1 -- Work Unit 3: START/SIT evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` (never bypassed,
never re-derives `lineupOpportunityCostPoints` -- that number is read
verbatim from the base evaluation). This module adds exactly two real,
honestly-reconstructed extras the base single-event contract does not
itself expose, per this cycle's governing directive:

1. The two REALIZED-POINTS components that already feed
   `lineupOpportunityCostPoints`, decomposed for direct reporting
   (`recommended_player_realized_points` / `owner_selected_player_realized_
   points`) -- pure arithmetic over the already-stored, already-computed
   `actualPointsByPlayer` list, no new data required.
2. `best_legal_alternative_*` -- the best-scoring LEGAL bench alternative
   that was actually ROSTERED AT LOCK TIME (`eligibleAlternativeIdsAtLock`,
   the trace's own frozen field), i.e. real "regret versus legal
   recommendation-time alternatives." Computed ONLY when the caller
   supplies a real `matchup_fetch` (`RealizedOutcomeFetch`) -- the EXACT
   SAME after-the-fact Sleeper matchup entry
   `prospective_outcome_source_adapter_v1_service.fetch_owner_matchup_entry`
   already fetches to build the primary evaluation (its `players_points`
   map already carries every rostered player's real points, bench
   included, not only the starters) -- so this is REUSE of an existing
   fetch, never a second network call or a new projection source.

Per the contract's own explicit rule (Section 5, rule 4, K/DST_STREAMER),
extended here to START_SIT: `bestLegalAlternativeActualPoints` is reported
ALONGSIDE `lineupOpportunityCostPoints` but is NEVER substituted into it --
the primary metric always stays a recommendation-vs-actual comparison, not
a hindsight-best one.

A real, disclosed simplification: this metric is a WHOLE-BENCH maximum,
not position-slot-aware -- the trace's own frozen fields
(`roster_state_player_ids`/`recommendation.starters`) carry no positional
lineup-slot-eligibility data, so "best legal alternative" here means "the
best-scoring player who was genuinely on this roster at lock time and was
not actually used by either the recommended or the actual lineup," not
"the best legal alternative for the specific vacated slot." Disclosed here
for a future position-aware refinement, not silently overclaimed as
slot-exact.

=== HINDSIGHT SAFETY ===

`evaluate_start_sit` accepts only an already-loaded `DecisionTraceRecord`
and an OPTIONAL already-fetched `RealizedOutcomeFetch` -- never a
"current"/live parameter of any kind (structurally asserted below, same
pattern as `prospective_outcome_evaluation_v1_service._assert_no_current_
state_parameter`). `best_legal_alternative` candidates are drawn ONLY from
`eligibleAlternativeIdsAtLock` (itself derived, by the ingestion module,
from the trace's own frozen `roster_state_player_ids` minus its own frozen
`recommendation.starters` -- never a "current"/later roster read), and
their points come only from the ONE supplied `matchup_fetch`'s own
`players_points` map for THIS same week -- never a search across a
different, later week's data.
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
from src.services.prospective_outcome_source_adapter_v1_service import RealizedOutcomeFetch

DETAIL_KIND = "START_SIT_LINEUP_V1"


@dataclass(frozen=True)
class StartSitEvaluatorResult:
    trace_id: str
    evaluation: OutcomeEvaluation
    recommended_player_realized_points: float | None
    owner_selected_player_realized_points: float | None
    lineup_opportunity_cost_points: float | None
    best_legal_alternative_player_id: str | None
    best_legal_alternative_actual_points: float | None
    owner_action_observed: bool
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "evaluation": self.evaluation.to_dict(),
            "recommendedPlayerRealizedPoints": self.recommended_player_realized_points,
            "ownerSelectedPlayerRealizedPoints": self.owner_selected_player_realized_points,
            "lineupOpportunityCostPoints": self.lineup_opportunity_cost_points,
            "bestLegalAlternativePlayerId": self.best_legal_alternative_player_id,
            "bestLegalAlternativeActualPoints": self.best_legal_alternative_actual_points,
            "ownerActionObserved": self.owner_action_observed,
            "issues": list(self.issues),
        }


def _points_by_id(detail: Mapping[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for row in detail.get("actualPointsByPlayer") or []:
        if not isinstance(row, Mapping):
            continue
        points = row.get("points")
        if isinstance(points, (int, float)) and not isinstance(points, bool):
            result[str(row.get("playerId"))] = float(points)
    return result


def _empty_result(record: DecisionTraceRecord, evaluation: OutcomeEvaluation) -> StartSitEvaluatorResult:
    return StartSitEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        recommended_player_realized_points=None,
        owner_selected_player_realized_points=None,
        lineup_opportunity_cost_points=None,
        best_legal_alternative_player_id=None,
        best_legal_alternative_actual_points=None,
        owner_action_observed=False,
        issues=evaluation.issues,
    )


def evaluate_start_sit(
    record: DecisionTraceRecord, *, matchup_fetch: RealizedOutcomeFetch | None = None
) -> StartSitEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type != "START_SIT":
        raise ValueError(f"evaluate_start_sit requires a START_SIT trace, got {evaluation.decision_type!r}.")
    if evaluation.evaluation_status != "EVALUATED" or not isinstance(evaluation.factual_outcome, Mapping):
        return _empty_result(record, evaluation)

    detail = evaluation.factual_outcome.get("detail")
    if not isinstance(detail, Mapping) or detail.get("kind") != DETAIL_KIND:
        return _empty_result(record, evaluation)

    points_by_id = _points_by_id(detail)
    recommended_only = [str(pid) for pid in detail.get("recommendedOnlyIds") or []]
    actual_only = [str(pid) for pid in detail.get("actualOnlyIds") or []]
    eligible_bench = [str(pid) for pid in detail.get("eligibleAlternativeIdsAtLock") or []]
    actual_starters = {str(pid) for pid in detail.get("actualStarterIds") or []}
    recommended_starters = {str(pid) for pid in detail.get("recommendedStarterIds") or []}

    recommended_realized: float | None = None
    if recommended_only and all(pid in points_by_id for pid in recommended_only):
        recommended_realized = round(sum(points_by_id[pid] for pid in recommended_only), 2)
    elif not recommended_only:
        recommended_realized = 0.0

    owner_realized: float | None = None
    if actual_only and all(pid in points_by_id for pid in actual_only):
        owner_realized = round(sum(points_by_id[pid] for pid in actual_only), 2)
    elif not actual_only:
        owner_realized = 0.0

    already_used = actual_starters | recommended_starters
    candidate_bench_ids = [pid for pid in eligible_bench if pid not in already_used]

    best_alt_id: str | None = None
    best_alt_points: float | None = None
    extra_issues: list[str] = []
    if matchup_fetch is None:
        if candidate_bench_ids:
            extra_issues.append(
                "bestLegalAlternative was not computed -- no real matchup fetch (with per-player points "
                "for the full bench) was supplied; the stored outcome detail alone only retains points for "
                "the recommended/actual starters, not the full eligible bench."
            )
    else:
        payload = matchup_fetch.payload
        raw_points = payload.get("players_points") if isinstance(payload, Mapping) else None
        if not isinstance(raw_points, Mapping):
            extra_issues.append(
                "bestLegalAlternative was not computed -- the supplied matchup fetch had no real "
                "players_points map."
            )
        else:
            for player_id in candidate_bench_ids:
                raw_value = raw_points.get(player_id)
                if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
                    value = float(raw_value)
                    if best_alt_points is None or value > best_alt_points:
                        best_alt_id, best_alt_points = player_id, value

    return StartSitEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        recommended_player_realized_points=recommended_realized,
        owner_selected_player_realized_points=owner_realized,
        lineup_opportunity_cost_points=evaluation.evaluation_metrics.get("lineupOpportunityCostPoints"),
        best_legal_alternative_player_id=best_alt_id,
        best_legal_alternative_actual_points=best_alt_points,
        owner_action_observed=bool(actual_starters),
        issues=tuple(evaluation.issues) + tuple(extra_issues),
    )


def summarize_start_sit_evaluations(results: Sequence[StartSitEvaluatorResult]) -> dict[str, Any]:
    """Real per-class AGGREGATION (contract Section 6/9, LEDGER Open Issue
    1) -- per-class only, gated by Section 7's minimum-sample rule. Never
    combined with any other class's numbers (Section 8)."""

    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.evaluation.evaluation_status] = (
            status_counts.get(result.evaluation.evaluation_status, 0) + 1
        )
    evaluated_costs = [
        result.lineup_opportunity_cost_points
        for result in results
        if result.evaluation.evaluation_status == "EVALUATED" and result.lineup_opportunity_cost_points is not None
    ]
    status = summary_status(len(evaluated_costs))
    summary: dict[str, Any] = {
        "decisionType": "START_SIT",
        "summaryStatus": status,
        "evaluatedSampleSize": len(evaluated_costs),
        "statusCounts": status_counts,
    }
    if status == "SUMMARIZED":
        summary["meanLineupOpportunityCostPoints"] = mean_of(evaluated_costs)
    return summary


# Structural hindsight-leakage defense, same pattern as Worker 1's own
# `_assert_no_current_state_parameter` -- asserted at import time, not only
# promised in prose.
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


_assert_evaluator_signature_is_safe(evaluate_start_sit)
