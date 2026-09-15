"""Prospective Outcomes V1 -- Work Unit 8: TRADE FINDER / TRADE PACKAGE
SEARCH evaluator.

Builds ON TOP OF Worker 1's `compute_outcome_evaluation` (never bypassed).
Per the contract's own decision-class table (Section 1): `TRADE_FINDER` and
`TRADE_PACKAGE_SEARCH` are two DIFFERENT real `TOOL_TYPES` (two different
live tools in `desktop_facade.py`, each recording its own recommendation
payload shape) that BOTH reuse the same `TradeFinderOutcomeDetail`
(`TRADE_FINDER_V1`) schema -- so this one evaluator module handles both
tool names, gated per-tool only for the recommendation-payload key-name
lookup (see `_recommended_package_sides` below), never blurring the two
into a third invented decision class.

=== REUSE, NEVER DUPLICATE, THE TRADE EVALUATOR'S REALIZED-OUTCOME LOGIC ===

Per this cycle's directive: "an accepted package IS a trade, don't
duplicate the realized-outcome computation." This module imports and calls
`prospective_outcome_trade_evaluator_v1_service.trade_realized_metrics_
from_detail` on the linked `TradeOutcomeDetail` payload
(`detail["linkedTradeOutcome"]`) -- the exact same function the TRADE
evaluator itself uses -- rather than re-reading `realizedRosterOutcome`
fields a second time in a second place.

=== PRODUCT QUALITY METRICS -- COUNTS ONLY, NEVER A PREDICTIVE RATE ===

Per the directive's own explicit, standing prohibition for this whole
project ("Do NOT convert adoption rate into an acceptance-probability
prediction"): `summarize_trade_finder_evaluations` reports raw
`packageDisposition` COUNTS (ignored/considered/sent/accepted/unknown) --
useful, real, descriptive numbers for a future human/benchmark to look at
-- and deliberately NEVER divides one count by another to produce a
rate/percentage/probability of acceptance. This is a stricter reading than
WAIVER's own `claimSubmissionRate`/`claimWinRate` (which ARE real observed
historical rates, not predictions) precisely because this cycle's
directive singles out trade-package adoption specifically -- so this
module errs conservative and reports counts only.

=== RECOMMENDED SIDES -- REAL, PER-TOOL KEY-NAME DIFFERENCES, DISCLOSED ===

The two real live call sites record genuinely different recommendation
shapes for the SAME schema kind:
- `TRADE_FINDER` (`desktop_facade.py` `redraft_trade_finder`):
  `{"myGivePlayerId": <single id>, "opponentGivePlayerId": <single id>,
  ...}`.
- `TRADE_PACKAGE_SEARCH` (`desktop_facade.py`
  `redraft_trade_package_search`): `{"youSend": [<ids>], "youReceive":
  [<ids>], ...}` (a real MULTI-player package, unlike TRADE_FINDER's
  single-for-single).

Both are read verbatim from the trace's own frozen `recommendation` field
-- never re-derived, never assumed to share one key-name convention.

=== A REAL, DISCLOSED FINDING: THE OWNER-ACTION -> DISPOSITION MAPPING GAP
===

`ingest_trade_finder_outcome` (prior cycle, unchanged) maps a trace's
`owner_action.action` string onto `packageDisposition` only when it is
EXACTLY `"SENT"` / `"CONSIDERED"` / `"IGNORED"` (case-insensitive) --
anything else, including the real app's OWN live owner-action UI
vocabulary ("Followed it" / "Did something else" / "Didn't act", see
`decision-history-format.ts`'s `ownerActionOptionsForDecisionType`), falls
through to `"UNKNOWN"`. This module does not attempt to guess a
translation between the two vocabularies (that would be inventing a
mapping, not reading a real fact) -- it reports `packageDisposition`
verbatim (including a real `"UNKNOWN"` when this mismatch occurs) and
separately reports `owner_action_raw` (the real, unmodified owner_action
string) so a human reader can see both real facts side by side. Flagged
again in the ledger's open issues -- fixing the vocabulary mismatch is a
`desktop_facade.py`/frontend change, out of this pass's scope.

=== HARD BOUNDARY ===

Never scores an unaccepted package's realized outcome. Never invents an
acceptance-probability model.
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
from src.services.prospective_outcome_trade_evaluator_v1_service import (
    trade_realized_metrics_from_detail,
)

DETAIL_KIND = "TRADE_FINDER_V1"
SUPPORTED_TOOLS = frozenset({"TRADE_FINDER", "TRADE_PACKAGE_SEARCH"})


@dataclass(frozen=True)
class TradeFinderEvaluatorResult:
    trace_id: str
    decision_type: str  # "TRADE_FINDER" | "TRADE_PACKAGE_SEARCH" -- real, distinct tools
    evaluation: OutcomeEvaluation
    owner_action_raw: str | None
    recommended_gives_ids: tuple[str, ...]
    recommended_receives_ids: tuple[str, ...]
    package_disposition: str | None
    # Only ever non-None fields when package_disposition == "ACCEPTED" --
    # mirrors TradeFinderOutcomeDetail.__post_init__'s own guard.
    trade_accepted: bool | None
    horizon_weeks: int | None
    net_subsequent_points_delta_points: float | None
    gives_subsequent_points_by_player: dict[str, Any] | None
    receives_subsequent_points_by_player: dict[str, Any] | None
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "decisionType": self.decision_type,
            "evaluation": self.evaluation.to_dict(),
            "ownerActionRaw": self.owner_action_raw,
            "recommendedGivesIds": list(self.recommended_gives_ids),
            "recommendedReceivesIds": list(self.recommended_receives_ids),
            "packageDisposition": self.package_disposition,
            "tradeAccepted": self.trade_accepted,
            "horizonWeeks": self.horizon_weeks,
            "netSubsequentPointsDeltaPoints": self.net_subsequent_points_delta_points,
            "givesSubsequentPointsByPlayer": self.gives_subsequent_points_by_player,
            "receivesSubsequentPointsByPlayer": self.receives_subsequent_points_by_player,
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


def _recommended_package_sides(
    decision_type: str, recommendation: Mapping[str, Any]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Real, per-tool key-name lookup -- see module docstring. Reads ONLY
    the trace's own frozen `recommendation` field."""

    if decision_type == "TRADE_FINDER":
        give = recommendation.get("myGivePlayerId")
        receive = recommendation.get("opponentGivePlayerId")
        gives = (str(give),) if give is not None else ()
        receives = (str(receive),) if receive is not None else ()
        return gives, receives

    # TRADE_PACKAGE_SEARCH
    send_raw = recommendation.get("youSend")
    receive_raw = recommendation.get("youReceive")
    gives = tuple(str(pid) for pid in send_raw) if isinstance(send_raw, Sequence) and not isinstance(send_raw, (str, bytes)) else ()
    receives = (
        tuple(str(pid) for pid in receive_raw)
        if isinstance(receive_raw, Sequence) and not isinstance(receive_raw, (str, bytes))
        else ()
    )
    return gives, receives


def _owner_action_raw(ctx: RecommendationTimeContext) -> str | None:
    if isinstance(ctx.owner_action, Mapping) and ctx.owner_action.get("action") is not None:
        return str(ctx.owner_action.get("action"))
    return None


def _empty_result(
    record: DecisionTraceRecord, evaluation: OutcomeEvaluation, ctx: RecommendationTimeContext
) -> TradeFinderEvaluatorResult:
    gives, receives = _recommended_package_sides(evaluation.decision_type, ctx.recommendation)
    return TradeFinderEvaluatorResult(
        trace_id=record.trace_id,
        decision_type=evaluation.decision_type,
        evaluation=evaluation,
        owner_action_raw=_owner_action_raw(ctx),
        recommended_gives_ids=gives,
        recommended_receives_ids=receives,
        package_disposition=None,
        trade_accepted=None,
        horizon_weeks=None,
        net_subsequent_points_delta_points=None,
        gives_subsequent_points_by_player=None,
        receives_subsequent_points_by_player=None,
        issues=evaluation.issues,
    )


def evaluate_trade_finder(
    record: DecisionTraceRecord, *, context: RecommendationTimeContext | None = None
) -> TradeFinderEvaluatorResult:
    evaluation = compute_outcome_evaluation(record)
    if evaluation.decision_type not in SUPPORTED_TOOLS:
        raise ValueError(
            f"evaluate_trade_finder requires a TRADE_FINDER or TRADE_PACKAGE_SEARCH trace, "
            f"got {evaluation.decision_type!r}."
        )

    ctx = context if context is not None else recommendation_time_context_from_trace(record)
    detail = _detail_of(evaluation)
    if detail is None:
        return _empty_result(record, evaluation, ctx)

    gives, receives = _recommended_package_sides(evaluation.decision_type, ctx.recommendation)
    disposition = detail.get("packageDisposition")
    linked = detail.get("linkedTradeOutcome")

    if disposition == "ACCEPTED" and isinstance(linked, Mapping):
        # REUSE, never duplicate -- see module docstring.
        metrics = trade_realized_metrics_from_detail(linked)
        trade_accepted = linked.get("tradeAccepted")
    else:
        metrics = {
            "horizonWeeks": None,
            "netSubsequentPointsDeltaPoints": None,
            "givesSubsequentPointsByPlayer": None,
            "receivesSubsequentPointsByPlayer": None,
        }
        trade_accepted = None

    return TradeFinderEvaluatorResult(
        trace_id=record.trace_id,
        decision_type=evaluation.decision_type,
        evaluation=evaluation,
        owner_action_raw=_owner_action_raw(ctx),
        recommended_gives_ids=gives,
        recommended_receives_ids=receives,
        package_disposition=disposition,
        trade_accepted=trade_accepted,
        horizon_weeks=metrics["horizonWeeks"],
        net_subsequent_points_delta_points=metrics["netSubsequentPointsDeltaPoints"],
        gives_subsequent_points_by_player=metrics["givesSubsequentPointsByPlayer"],
        receives_subsequent_points_by_player=metrics["receivesSubsequentPointsByPlayer"],
        issues=evaluation.issues,
    )


def summarize_trade_finder_evaluations(results: Sequence[TradeFinderEvaluatorResult]) -> dict[str, Any]:
    """PRODUCT QUALITY metrics (contract Section 6/9's "next worker" framing,
    plus this cycle's own directive) -- raw disposition COUNTS only, never a
    rate/probability (see module docstring). Separately, a minimum-sample-
    gated mean net points delta over ACCEPTED packages only, reusing TRADE's
    own realized-outcome numbers (never re-derived)."""

    status_counts: dict[str, int] = {}
    disposition_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.evaluation.evaluation_status] = status_counts.get(result.evaluation.evaluation_status, 0) + 1
        key = result.package_disposition or "NO_OUTCOME_YET"
        disposition_counts[key] = disposition_counts.get(key, 0) + 1

    accepted_deltas = [
        result.net_subsequent_points_delta_points
        for result in results
        if result.package_disposition == "ACCEPTED" and result.net_subsequent_points_delta_points is not None
    ]
    delta_status = summary_status(len(accepted_deltas))

    summary: dict[str, Any] = {
        "decisionType": "TRADE_FINDER",
        "statusCounts": status_counts,
        # Real counts only -- NEVER converted into an acceptance rate/
        # probability, per this cycle's own standing prohibition.
        "packageDispositionCounts": disposition_counts,
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


_assert_evaluator_signature_is_safe(evaluate_trade_finder)
