"""Prospective Outcomes V1 -- Work Unit 5: ADD/DROP evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` (never bypassed).
Per this cycle's governing directive: "Evaluate the pair" -- ADD player,
DROP player, owner action, transaction result, added/dropped future value,
usage, "replacement reversibility where measurable," and "Do not overclaim
causal impact from one transaction -- one add/drop among many other roster
changes shouldn't be scored as if it were the only variable."

Same real, disclosed refinement as the WAIVER evaluator: reads
`addedPlayerId`/`droppedPlayerId`/`droppedPlayerReversed` directly from the
already-stored `outcome.detail` payload (not from
`evaluation.evaluation_metrics`, which `_extract_add_drop`'s `PENDING_WINDOW`
branch blanks entirely) so real, already-known identity/reversal facts are
never lost just because the bounded-horizon added-player value hasn't been
observed yet.

=== `net_roster_value_points` -- HONESTLY LEFT UNCOMPUTABLE THIS PASS ===

The directive asks for "net roster value." A true net figure needs BOTH
`addedPlayerSubsequentPoints` and `droppedPlayerSubsequentPoints`.
`droppedPlayerSubsequentPoints` is, unchanged, the prior cycle's own
disclosed Open Issue 3 (`prospective_outcome_schema_v1_service.py`'s own
comment): once a player is dropped off THIS roster, their subsequent value
can only be read from whichever OTHER roster (if any) later adds them --
this codebase has no leaguewide roster-membership-over-time feed to do that
yet. This module does NOT invent that feed (out of this pass's real scope);
`net_roster_value_points` stays honestly `None` with a disclosed issue
whenever `droppedPlayerSubsequentPoints` is unavailable -- never
approximated as "added value only," which would silently misrepresent a
net figure as complete.

Per the directive's own explicit instruction, this module also never
overclaims causal isolation: every real result carries a fixed disclosure
note that one add/drop is one transaction among many concurrent roster
changes, never scored as if it were the sole driver of any later roster
outcome.
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

DETAIL_KIND = "ADD_DROP_V1"

CAUSAL_ISOLATION_DISCLOSURE = (
    "This evaluation scores ONE add/drop transaction in isolation -- it is one roster change among "
    "potentially many others made by this owner over the same horizon, and no causal claim is made that "
    "this specific transaction alone produced the roster's later real results."
)

NET_VALUE_UNCOMPUTABLE_ISSUE = (
    "netRosterValuePoints was not computed -- droppedPlayerSubsequentPoints is not honestly "
    "reconstructable this pass (inherited open issue: no leaguewide roster-membership-over-time feed "
    "exists yet to track a dropped player once they leave this roster). Reporting only the added "
    "player's value as a 'net' figure would misrepresent an incomplete number as complete."
)


@dataclass(frozen=True)
class AddDropEvaluatorResult:
    trace_id: str
    evaluation: OutcomeEvaluation
    added_player_id: str | None
    dropped_player_id: str | None
    horizon_weeks: int | None
    added_player_subsequent_points: float | None
    added_player_subsequent_roster_usage_weeks: int | None
    dropped_player_subsequent_points: float | None
    dropped_player_reversed: bool | None
    net_roster_value_points: float | None
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "evaluation": self.evaluation.to_dict(),
            "addedPlayerId": self.added_player_id,
            "droppedPlayerId": self.dropped_player_id,
            "horizonWeeks": self.horizon_weeks,
            "addedPlayerSubsequentPoints": self.added_player_subsequent_points,
            "addedPlayerSubsequentRosterUsageWeeks": self.added_player_subsequent_roster_usage_weeks,
            "droppedPlayerSubsequentPoints": self.dropped_player_subsequent_points,
            "droppedPlayerReversed": self.dropped_player_reversed,
            "netRosterValuePoints": self.net_roster_value_points,
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


def evaluate_add_drop(record: DecisionTraceRecord) -> AddDropEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type != "ADD_DROP":
        raise ValueError(f"evaluate_add_drop requires an ADD_DROP trace, got {evaluation.decision_type!r}.")

    detail = _detail_of(evaluation)
    issues = list(evaluation.issues) + [CAUSAL_ISOLATION_DISCLOSURE]

    if detail is None:
        return AddDropEvaluatorResult(
            trace_id=record.trace_id,
            evaluation=evaluation,
            added_player_id=None,
            dropped_player_id=None,
            horizon_weeks=None,
            added_player_subsequent_points=None,
            added_player_subsequent_roster_usage_weeks=None,
            dropped_player_subsequent_points=None,
            dropped_player_reversed=None,
            net_roster_value_points=None,
            issues=tuple(issues),
        )

    added_points = detail.get("addedPlayerSubsequentPoints")
    dropped_points = detail.get("droppedPlayerSubsequentPoints")
    net_value: float | None = None
    if added_points is not None and dropped_points is not None:
        net_value = round(float(added_points) - float(dropped_points), 2)
    elif detail.get("addedPlayerId") is not None:
        issues.append(NET_VALUE_UNCOMPUTABLE_ISSUE)

    return AddDropEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        added_player_id=detail.get("addedPlayerId"),
        dropped_player_id=detail.get("droppedPlayerId"),
        horizon_weeks=detail.get("horizonWeeks"),
        added_player_subsequent_points=added_points,
        added_player_subsequent_roster_usage_weeks=detail.get("addedPlayerSubsequentRosterUsageWeeks"),
        dropped_player_subsequent_points=dropped_points,
        dropped_player_reversed=detail.get("droppedPlayerReversed"),
        net_roster_value_points=net_value,
        issues=tuple(issues),
    )


def summarize_add_drop_evaluations(results: Sequence[AddDropEvaluatorResult]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.evaluation.evaluation_status] = (
            status_counts.get(result.evaluation.evaluation_status, 0) + 1
        )

    added_points = [
        result.added_player_subsequent_points for result in results if result.added_player_subsequent_points is not None
    ]
    added_status = summary_status(len(added_points))

    reversal_flags = [result.dropped_player_reversed for result in results if result.dropped_player_reversed is not None]
    reversal_status = summary_status(len(reversal_flags))

    summary: dict[str, Any] = {
        "decisionType": "ADD_DROP",
        "statusCounts": status_counts,
        "addedPlayerValue": {
            "summaryStatus": added_status,
            "sampleSize": len(added_points),
        },
        "dropReversalRate": {
            "summaryStatus": reversal_status,
            "sampleSize": len(reversal_flags),
        },
    }
    if added_status == "SUMMARIZED":
        summary["addedPlayerValue"]["meanAddedPlayerSubsequentPoints"] = mean_of(added_points)
    if reversal_status == "SUMMARIZED":
        summary["dropReversalRate"]["rate"] = rate_of(reversal_flags)
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


_assert_evaluator_signature_is_safe(evaluate_add_drop)
