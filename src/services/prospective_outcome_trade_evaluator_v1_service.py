"""Prospective Outcomes V1 -- Work Unit 7: TRADE evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` (never bypassed,
never re-derives `netSubsequentPointsDeltaPoints` -- that number is read
verbatim from the base evaluation / the already-stored `outcome.detail`
payload). Per this cycle's governing directive: record the owner's real,
observable action (ignored/considered/sent/accepted/rejected/cancelled,
where observable), and evaluate realized roster outcome ONLY for an
ACTUALLY ACCEPTED trade.

=== THE REJECTED-TRADE GUARANTEE -- STRUCTURALLY ENFORCED, NOT JUST HERE ===

`TradeOutcomeDetail.__post_init__` (`prospective_outcome_schema_v1_service.py`,
built in a prior cycle, reused verbatim, never weakened) already raises
`ValueError` if `realized_roster_outcome` is set without
`trade_accepted is True`. `_extract_trade`
(`prospective_outcome_evaluation_v1_service.py`, Worker 1) already returns
`evaluationStatus = "NOT_APPLICABLE"` with empty metrics for any
non-ACCEPTED trade, which `OutcomeEvaluation.__post_init__` then further
enforces (a non-`EVALUATED` status may carry no non-`None` metric value).
This module adds a THIRD, additive layer of the same guarantee: it reads
`netSubsequentPointsDeltaPoints`/the per-player breakdown ONLY from
`detail.get("realizedRosterOutcome")`, which the schema dataclass itself
only ever populates for an accepted trade -- so a rejected trace's own
`realized_roster_outcome` field is `None` before this module ever sees it,
never re-derived, never guessed. `tests/test_prospective_outcome_trade_
evaluator_v1_service.py` re-proves all three layers hold, including a
direct construction test against the schema's own `__post_init__` guard.

=== OWNER ACTION IS RECORDED VERBATIM, NEVER RELABELED ===

`owner_action_raw` is read directly, unmodified, from the trace's own
frozen `owner_action` field (via `RecommendationTimeContext`, zero network
I/O) -- exactly whatever string the real call site recorded, never mapped
onto "ignored"/"considered"/"sent"/"accepted"/"rejected"/"cancelled" by
guesswork. A REAL, DISCLOSED FINDING this pass: the app's own live owner-
action UI (`desktop/apps/redraft/src/decision-history-format.ts`,
`ownerActionOptionsForDecisionType`) currently offers TRADE the SAME
generic 3-option vocabulary as WAIVER ("Followed it" / "Did something
else" / "Didn't act"), not a trade-specific
sent/accepted/rejected/cancelled vocabulary -- so `owner_action_raw` for a
real TRADE trace will currently read one of those three generic strings,
not the richer vocabulary this cycle's directive describes. The
AUTHORITATIVE acceptance signal this module actually scores against
(`acceptance_status` / `trade_accepted`) comes from `TradeOutcomeDetail`,
itself derived (by `ingest_trade_outcome`, a prior module, unchanged) from
a REAL matched Sleeper `type == "trade", status == "complete"` transaction
-- never from the free-text owner-action label. `owner_action_raw` is
reported alongside as a real, honest adoption-signal data point, never
substituted for the structurally-derived acceptance status.

=== RECOMMENDED SIDES -- READ FROM THE TRACE'S OWN FROZEN RECOMMENDATION ===

The one real live TRADE call site (`desktop_facade.py`,
`redraft_trade_analysis`) records `recommendation = {"gives": [...],
"receives": [...], ...}` (already-resolved canonical player ids). This
module reads those two exact keys -- never invents a different key name,
never re-derives them from a "current" roster read.

=== HARD BOUNDARY ===

Never scores a rejected/unknown trade's realized outcome. Never invents an
opponent's counter-offer probability. Never recomputes
`netSubsequentPointsDeltaPoints` -- always read verbatim from the
already-stored detail.
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
from src.services.prospective_outcome_source_adapter_v1_service import (
    RecommendationTimeContext,
    recommendation_time_context_from_trace,
)

DETAIL_KIND = "TRADE_V1"


@dataclass(frozen=True)
class TradeEvaluatorResult:
    trace_id: str
    evaluation: OutcomeEvaluation
    # Verbatim from the trace's own owner_action field -- see module
    # docstring's "owner action is recorded verbatim" section.
    owner_action_raw: str | None
    recommended_gives_ids: tuple[str, ...]
    recommended_receives_ids: tuple[str, ...]
    # The AUTHORITATIVE, structurally-derived acceptance signal (from a
    # real matched Sleeper trade transaction) -- never the free-text
    # owner_action label.
    acceptance_status: str | None
    trade_accepted: bool | None
    horizon_weeks: int | None
    net_subsequent_points_delta_points: float | None
    gives_subsequent_points_by_player: dict[str, Any] | None
    receives_subsequent_points_by_player: dict[str, Any] | None
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "evaluation": self.evaluation.to_dict(),
            "ownerActionRaw": self.owner_action_raw,
            "recommendedGivesIds": list(self.recommended_gives_ids),
            "recommendedReceivesIds": list(self.recommended_receives_ids),
            "acceptanceStatus": self.acceptance_status,
            "tradeAccepted": self.trade_accepted,
            "horizonWeeks": self.horizon_weeks,
            "netSubsequentPointsDeltaPoints": self.net_subsequent_points_delta_points,
            "givesSubsequentPointsByPlayer": self.gives_subsequent_points_by_player,
            "receivesSubsequentPointsByPlayer": self.receives_subsequent_points_by_player,
            "issues": list(self.issues),
        }


def _detail_of(evaluation: OutcomeEvaluation, *, expected_kind: str = DETAIL_KIND) -> Mapping[str, Any] | None:
    factual = evaluation.factual_outcome
    if not isinstance(factual, Mapping):
        return None
    detail = factual.get("detail")
    if not isinstance(detail, Mapping) or detail.get("kind") != expected_kind:
        return None
    return detail


def _recommended_trade_sides(recommendation: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Reads the exact `gives`/`receives` keys the one real TRADE call site
    (`desktop_facade.py`) records -- the trace's own frozen field, never a
    "current" roster re-derivation."""

    gives_raw = recommendation.get("gives")
    receives_raw = recommendation.get("receives")
    gives = tuple(str(pid) for pid in gives_raw) if isinstance(gives_raw, Sequence) and not isinstance(gives_raw, (str, bytes)) else ()
    receives = (
        tuple(str(pid) for pid in receives_raw)
        if isinstance(receives_raw, Sequence) and not isinstance(receives_raw, (str, bytes))
        else ()
    )
    return gives, receives


def trade_realized_metrics_from_detail(detail: Mapping[str, Any]) -> dict[str, Any]:
    """The ONE realized-outcome-metric extraction this evaluator layer
    performs for TRADE -- reads `realizedRosterOutcome` verbatim, no new
    arithmetic. REUSED (not duplicated) by
    `prospective_outcome_trade_finder_evaluator_v1_service.py`, per this
    cycle's directive: "an accepted package IS a trade, don't duplicate the
    realized-outcome computation." Honestly returns all-`None` fields when
    no realized outcome exists (a rejected/unknown/pending trade) -- never
    fabricates a number."""

    realized = detail.get("realizedRosterOutcome")
    if not isinstance(realized, Mapping):
        return {
            "horizonWeeks": None,
            "netSubsequentPointsDeltaPoints": None,
            "givesSubsequentPointsByPlayer": None,
            "receivesSubsequentPointsByPlayer": None,
        }
    return {
        "horizonWeeks": realized.get("horizonWeeks"),
        "netSubsequentPointsDeltaPoints": realized.get("netSubsequentPointsDelta"),
        "givesSubsequentPointsByPlayer": realized.get("givesSubsequentPointsByPlayer"),
        "receivesSubsequentPointsByPlayer": realized.get("receivesSubsequentPointsByPlayer"),
    }


def _empty_result(
    record: DecisionTraceRecord,
    evaluation: OutcomeEvaluation,
    ctx: RecommendationTimeContext,
) -> TradeEvaluatorResult:
    gives, receives = _recommended_trade_sides(ctx.recommendation)
    owner_action_raw = (
        str(ctx.owner_action.get("action")) if isinstance(ctx.owner_action, Mapping) and ctx.owner_action.get("action") is not None else None
    )
    return TradeEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        owner_action_raw=owner_action_raw,
        recommended_gives_ids=gives,
        recommended_receives_ids=receives,
        acceptance_status=None,
        trade_accepted=None,
        horizon_weeks=None,
        net_subsequent_points_delta_points=None,
        gives_subsequent_points_by_player=None,
        receives_subsequent_points_by_player=None,
        issues=evaluation.issues,
    )


def evaluate_trade(
    record: DecisionTraceRecord, *, context: RecommendationTimeContext | None = None
) -> TradeEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type != "TRADE":
        raise ValueError(f"evaluate_trade requires a TRADE trace, got {evaluation.decision_type!r}.")

    ctx = context if context is not None else recommendation_time_context_from_trace(record)
    detail = _detail_of(evaluation)
    if detail is None:
        return _empty_result(record, evaluation, ctx)

    gives, receives = _recommended_trade_sides(ctx.recommendation)
    owner_action_raw = (
        str(ctx.owner_action.get("action")) if isinstance(ctx.owner_action, Mapping) and ctx.owner_action.get("action") is not None else None
    )
    # Real, disclosed bug found and fixed THIS pass (boundary/property test
    # pack V2, Group 11): `trade_realized_metrics_from_detail` only checks
    # whether `realizedRosterOutcome` is present, not whether the trade was
    # actually accepted -- it trusted every real caller (`ingest_trade_
    # outcome`) to never populate `realizedRosterOutcome` for a rejected/
    # unknown trade, which IS always true for data produced by that real
    # ingestion function, but was not independently enforced HERE. A stored
    # `outcome.detail` dict that reached this evaluator any other way (a
    # malformed/legacy ledger row, a future caller writing `detail`
    # directly) could otherwise surface a scored counterfactual for a
    # rejected trade, contradicting this module's own documented
    # three-layer rejected-trade guarantee. Mirrors the SAME guard
    # `evaluate_trade_finder` (Work Unit 8) already applies at its own call
    # site -- narrowed to this one call, no other behavior touched.
    is_accepted = detail.get("acceptanceStatus") == "ACCEPTED" and detail.get("tradeAccepted") is True
    metrics = (
        trade_realized_metrics_from_detail(detail)
        if is_accepted
        else {
            "horizonWeeks": None,
            "netSubsequentPointsDeltaPoints": None,
            "givesSubsequentPointsByPlayer": None,
            "receivesSubsequentPointsByPlayer": None,
        }
    )

    return TradeEvaluatorResult(
        trace_id=record.trace_id,
        evaluation=evaluation,
        owner_action_raw=owner_action_raw,
        recommended_gives_ids=gives,
        recommended_receives_ids=receives,
        acceptance_status=detail.get("acceptanceStatus"),
        trade_accepted=detail.get("tradeAccepted"),
        horizon_weeks=metrics["horizonWeeks"],
        net_subsequent_points_delta_points=metrics["netSubsequentPointsDeltaPoints"],
        gives_subsequent_points_by_player=metrics["givesSubsequentPointsByPlayer"],
        receives_subsequent_points_by_player=metrics["receivesSubsequentPointsByPlayer"],
        issues=evaluation.issues,
    )


def summarize_trade_evaluations(results: Sequence[TradeEvaluatorResult]) -> dict[str, Any]:
    """Per-class-only aggregation (contract Section 6/9). TWO genuinely
    separate tallies, never blended: real acceptance-status counts (an
    adoption/product signal) and a minimum-sample-gated mean net points
    delta computed ONLY over trades this evaluator itself confirmed were
    ACCEPTED (never a rejected/unknown trade's unobserved counterfactual)."""

    status_counts: dict[str, int] = {}
    acceptance_status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.evaluation.evaluation_status] = status_counts.get(result.evaluation.evaluation_status, 0) + 1
        key = result.acceptance_status or "NO_OUTCOME_YET"
        acceptance_status_counts[key] = acceptance_status_counts.get(key, 0) + 1

    accepted_deltas = [
        result.net_subsequent_points_delta_points
        for result in results
        if result.trade_accepted is True and result.net_subsequent_points_delta_points is not None
    ]
    delta_status = summary_status(len(accepted_deltas))

    summary: dict[str, Any] = {
        "decisionType": "TRADE",
        "statusCounts": status_counts,
        "acceptanceStatusCounts": acceptance_status_counts,
        "acceptedNetSubsequentPointsDelta": {
            "summaryStatus": delta_status,
            "sampleSize": len(accepted_deltas),
        },
    }
    if delta_status == "SUMMARIZED":
        summary["acceptedNetSubsequentPointsDelta"]["meanNetSubsequentPointsDeltaPoints"] = mean_of(accepted_deltas)
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


_assert_evaluator_signature_is_safe(evaluate_trade)
