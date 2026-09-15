"""Prospective Outcomes V1 -- the canonical outcome-EVENT contract and the
(derived, not stored) single-event EVALUATION layer built on top of it.

Frozen decisions, preregistered in
`docs/codex/prospective_outcomes_v1/PROSPECTIVE_OUTCOME_EVALUATION_CONTRACT.md`
BEFORE this module was written -- read that document first; this module's
comments reference it by section number rather than re-litigating the
reasoning inline.

=== WHERE THIS MODULE SITS IN THE EXISTING FOUNDATION ===

This is a NEW layer ON TOP OF three already-real, already-tested pieces
from the prior cycle -- nothing below replaces or duplicates them:

1. `in_season_decision_trace_service.py` -- the append-only ledger itself
   (`DecisionTraceRecord`, `record_decision_trace` /
   `record_owner_action` / `record_outcome`). Immutable recommendation
   line, append-only owner-action/outcome lines. UNCHANGED by this module
   except for `record_outcome`'s three new, additive, independently
   omittable provenance keyword parameters (`outcome_source` /
   `outcome_source_as_of` / `outcome_observed_at`) added alongside this
   module in the same pass.
2. `prospective_outcome_schema_v1_service.py` -- the 8 decision-type
   outcome dataclasses (`StartSitOutcomeDetail`, `WaiverOutcomeDetail`,
   etc.), each with its own real, already-computed metric fields. THIS
   module does not recompute or duplicate any of that arithmetic -- it
   only reads the already-computed `outcome.detail` dict a
   `record_outcome(..., detail=<schema>.to_detail_dict())` call already
   stored, and (for K_STREAMER/DST_STREAMER only, see Section 2 of the
   contract) computes ONE new, simple, transparent point-delta that
   mirrors START_SIT's own already-proven opportunity-cost formula.
3. `prospective_outcome_ingestion_v1_service.py` -- the pure functions
   that turn frozen trace fields + real after-the-fact Sleeper JSON into
   one of those schema dataclasses. Untouched by this module.

=== WHAT "EVALUATION" IS HERE: A DERIVED VIEW, NOT A NEW LEDGER LINE ===

Per the contract's own explicit instruction to "decide and document this
precisely": an `OutcomeEvaluation` is **always recomputed on demand from
the immutable trace chain** (`compute_outcome_evaluation(record)`,
a pure function over an already-loaded `DecisionTraceRecord`). It is
**never itself appended as a new ledger line**. Two real consequences of
this design choice:

- Calling `compute_outcome_evaluation` twice on the same `DecisionTraceRecord`
  is guaranteed to return an equal value every time (proven by
  `test_compute_outcome_evaluation_is_pure_and_deterministic` below) --
  there is no "evaluation ledger" that could ever drift out of sync with
  the real recommendation/owner-action/outcome chain it is computed from,
  because it is never stored independently of that chain at all.
- If a future pass changes how a metric is computed (e.g. a smarter
  regret formula), every HISTORICAL trace's evaluation automatically
  reflects the new logic the next time it is read -- there is no stale,
  frozen-at-write-time evaluation row to migrate or invalidate. The
  trade-off (also disclosed here, not hidden): this means
  `OutcomeEvaluation` is NOT itself an audit trail of "what NWR told the
  owner its own evaluation was, at the time" -- only the underlying
  `recommendation`/`owner_action`/`outcome` ledger lines are that audit
  trail, and they remain untouched and immutable exactly as before.

=== WORK UNIT 1's REAL SCOPE, NOT OVER-CLAIMED ===

Per the contract Section 9 and this cycle's own directive: this module
builds the CANONICAL SINGLE-EVENT contract shape and extracts the metric(s)
each decision-type's schema ALREADY computed -- it does not build
per-class AGGREGATION/SUMMARY across many real outcomes (mean regret,
calibration hit-rate, minimum-sample-gated rollups). That is explicitly
the next worker's job (contract Section 9, ledger Work Units 3-6).
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.services.in_season_decision_trace_service import DecisionTraceRecord

SCHEMA_VERSION = "prospective_outcome_evaluation_v1"

# ---------------------------------------------------------------------------
# evaluationStatus -- a closed, frozen set (contract Section 4). Adding a
# new member requires a new, dated contract section, never a silent edit.
# ---------------------------------------------------------------------------

EVALUATION_STATUSES = frozenset(
    {
        "PENDING_OUTCOME",
        "PENDING_WINDOW",
        "EVALUATED",
        "INSUFFICIENT_DECISION_CONTEXT",
        "NOT_APPLICABLE",
    }
)

# Preregistered per-class evaluation windows (contract Section 3). Frozen --
# a new use case gets a NEW label, this dict's existing entries are never
# silently changed.
EVALUATION_WINDOWS: Mapping[str, Mapping[str, Any]] = {
    "START_SIT": {"label": "SAME_WEEK_LOCK_TO_FINAL", "horizonWeeks": 0},
    "K_STREAMER": {"label": "SAME_WEEK", "horizonWeeks": 0},
    "DST_STREAMER": {"label": "SAME_WEEK", "horizonWeeks": 0},
    "WAIVER": {"label": "BOUNDED_HORIZON", "horizonWeeks": 4},
    "ADD_DROP": {"label": "BOUNDED_HORIZON", "horizonWeeks": 4},
    "FAAB": {"label": "BOUNDED_HORIZON", "horizonWeeks": 4},
    "TRADE": {"label": "BOUNDED_HORIZON_ACCEPTED_ONLY", "horizonWeeks": 4},
    "TRADE_FINDER": {"label": "BOUNDED_HORIZON_ACCEPTED_ONLY", "horizonWeeks": 4},
    "TRADE_PACKAGE_SEARCH": {"label": "BOUNDED_HORIZON_ACCEPTED_ONLY", "horizonWeeks": 4},
    "DRAFT": {"label": "DEFERRED_SEASON_LONG", "horizonWeeks": None},
}

# Contract Section 7 -- deliberately the SAME number as the frontend's own
# `MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP` constant
# (desktop/apps/redraft/src/decision-history-format.ts). Duplicated, not
# shared, across the Python/TypeScript boundary -- a real, disclosed gap
# (contract Section 7 / Section 9), not silently left undocumented. This
# constant is not consumed by anything in this module (this pass computes
# single-event evaluations only, never an aggregate) -- it exists here so a
# future per-class summary (Work Units 3-6) has a single, named Python-side
# constant to import rather than re-inventing the number.
MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY = 20


class ProspectiveOutcomeEvaluationError(ValueError):
    pass


@dataclass(frozen=True)
class OutcomeEvaluation:
    """The canonical outcome-EVENT contract for one decision trace --
    contract Section 1-6, every field named directly after the governing
    directive's own list. A DERIVED VIEW (see module docstring): never
    stored independently of the `DecisionTraceRecord` it was computed
    from."""

    schema_version: str
    trace_id: str
    decision_type: str
    league_key: str  # this app's own real per-profile scoping key (profile_id)
    league_id: str
    league_snapshot_id: str | None
    recommendation_generated_at: str
    outcome_observed_at: str | None
    outcome_window_label: str
    outcome_window_horizon_weeks: int | None
    outcome_source: str | None
    outcome_source_as_of: str | None
    owner_action: dict[str, Any] | None
    # The raw, already-recorded outcome payload verbatim (outcome/notes and,
    # when present, detail/source/sourceAsOf/observedAt) -- never re-derived,
    # never mutated. `None` when no outcome has been recorded at all yet.
    factual_outcome: dict[str, Any] | None
    evaluation_status: str
    evaluation_metrics: dict[str, Any]
    issues: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.evaluation_status not in EVALUATION_STATUSES:
            raise ProspectiveOutcomeEvaluationError(
                f"Unknown evaluationStatus: {self.evaluation_status!r}. Must be one of "
                f"{sorted(EVALUATION_STATUSES)}."
            )
        if self.evaluation_status == "EVALUATED" and not self.evaluation_metrics:
            raise ProspectiveOutcomeEvaluationError(
                "evaluationStatus 'EVALUATED' requires at least one real computed metric in "
                "evaluation_metrics -- never claim a real evaluation happened with an empty result."
            )
        if self.evaluation_status != "EVALUATED" and any(
            value is not None for value in self.evaluation_metrics.values()
        ):
            raise ProspectiveOutcomeEvaluationError(
                f"evaluationStatus {self.evaluation_status!r} must not carry a non-None metric value -- "
                "only 'EVALUATED' may report a real computed number (contract Section 4: never fabricate "
                "regret, never blur 'insufficient context' with a real answer)."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "traceId": self.trace_id,
            "decisionType": self.decision_type,
            "leagueKey": self.league_key,
            "leagueId": self.league_id,
            "leagueSnapshotId": self.league_snapshot_id,
            "recommendationGeneratedAt": self.recommendation_generated_at,
            "outcomeObservedAt": self.outcome_observed_at,
            "outcomeWindow": {
                "label": self.outcome_window_label,
                "horizonWeeks": self.outcome_window_horizon_weeks,
            },
            "outcomeSource": self.outcome_source,
            "outcomeSourceAsOf": self.outcome_source_as_of,
            "ownerAction": self.owner_action,
            "factualOutcome": self.factual_outcome,
            "evaluationStatus": self.evaluation_status,
            "evaluationMetrics": dict(self.evaluation_metrics),
            "issues": list(self.issues),
        }


# ---------------------------------------------------------------------------
# Per-class metric extraction -- reads ONLY the already-computed fields the
# real schema/ingestion layer produced (contract Section 2). No new
# arithmetic except the one, explicitly-labeled STREAMER opportunity-cost
# delta, which mirrors START_SIT's own already-proven formula rather than
# inventing a new methodology.
# ---------------------------------------------------------------------------


def _issue(*parts: str) -> tuple[str, ...]:
    return tuple(parts)


def _extract_start_sit(detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    cost = detail.get("lineupOpportunityCost")
    if cost is None:
        return (
            "INSUFFICIENT_DECISION_CONTEXT",
            {},
            _issue(
                "lineupOpportunityCost could not be computed -- real points data was missing for at "
                "least one of the players that differed between the recommended and actual lineups."
            ),
        )
    return "EVALUATED", {"lineupOpportunityCostPoints": cost}, ()


def _extract_waiver(detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    if detail.get("recommendedPlayerId") is None:
        return (
            "INSUFFICIENT_DECISION_CONTEXT",
            {},
            _issue("recommendedPlayerId was never resolved -- no player identity to evaluate against."),
        )
    metrics: dict[str, Any] = {
        "claimSubmitted": detail.get("claimSubmitted"),
        "claimWon": detail.get("claimWon"),
        "faabPaid": detail.get("faabPaid"),
    }
    if detail.get("claimWon") is True and detail.get("subsequentTotalPoints") is None:
        # The claim was won but no horizon data has been observed yet --
        # the window genuinely has not closed/been fetched (contract
        # Section 4: PENDING_WINDOW, never INSUFFICIENT_DECISION_CONTEXT).
        return "PENDING_WINDOW", {}, _issue(
            "Claim was won but no horizon matchup data has been ingested yet -- subsequent value is "
            "not yet observable, not structurally unknowable."
        )
    metrics["subsequentTotalPoints"] = detail.get("subsequentTotalPoints")
    metrics["subsequentRosterUsageWeeks"] = detail.get("subsequentRosterUsageWeeks")
    return "EVALUATED", metrics, ()


def _extract_add_drop(detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    if detail.get("addedPlayerId") is None:
        return (
            "INSUFFICIENT_DECISION_CONTEXT",
            {},
            _issue("addedPlayerId was never resolved -- no player identity to evaluate against."),
        )
    if detail.get("addedPlayerSubsequentPoints") is None:
        return "PENDING_WINDOW", {}, _issue(
            "No horizon matchup data has been ingested yet for the added player -- subsequent value "
            "is not yet observable, not structurally unknowable."
        )
    return (
        "EVALUATED",
        {
            "addedPlayerSubsequentPoints": detail.get("addedPlayerSubsequentPoints"),
            "addedPlayerSubsequentRosterUsageWeeks": detail.get("addedPlayerSubsequentRosterUsageWeeks"),
            "droppedPlayerSubsequentPoints": detail.get("droppedPlayerSubsequentPoints"),
            "droppedPlayerReversed": detail.get("droppedPlayerReversed"),
        },
        (),
    )


def _extract_faab(detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    if detail.get("recommendedPlayerId") is None:
        return (
            "INSUFFICIENT_DECISION_CONTEXT",
            {},
            _issue("recommendedPlayerId was never resolved -- no player identity to evaluate against."),
        )
    quality = detail.get("playerDecisionQuality") or {}
    calibration = detail.get("bidRangeCalibration") or {}
    # Kept as two GENUINELY SEPARATE sub-objects, per the contract's FAAB
    # rule (Section 2) and the schema's own structural separation -- never
    # flattened or merged into one figure.
    return (
        "EVALUATED",
        {
            "playerDecisionQuality": dict(quality),
            "bidRangeCalibration": dict(calibration),
        },
        (),
    )


def _extract_trade(detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    acceptance = detail.get("acceptanceStatus")
    if acceptance != "ACCEPTED" or detail.get("tradeAccepted") is not True:
        # A rejected/unknown trade is NEVER scored against an unobserved
        # counterfactual -- contract Section 2, mirroring the schema's own
        # structural refusal (`TradeOutcomeDetail.__post_init__`).
        return "NOT_APPLICABLE", {}, _issue(
            f"Trade acceptanceStatus is {acceptance!r} -- a rejected/unknown trade is never scored "
            "against an unobserved counterfactual."
        )
    realized = detail.get("realizedRosterOutcome")
    if not realized or realized.get("netSubsequentPointsDelta") is None:
        return "PENDING_WINDOW", {}, _issue(
            "Trade was accepted but no realized-roster-outcome horizon data has been ingested yet."
        )
    return "EVALUATED", {"netSubsequentPointsDeltaPoints": realized.get("netSubsequentPointsDelta")}, ()


def _extract_trade_finder(detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    disposition = detail.get("packageDisposition")
    if disposition != "ACCEPTED":
        return "NOT_APPLICABLE", {}, _issue(
            f"packageDisposition is {disposition!r} -- only an ACCEPTED package reuses TRADE's "
            "realized-outcome metric."
        )
    linked = detail.get("linkedTradeOutcome") or {}
    return _extract_trade(linked)


def _extract_streamer(detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    if detail.get("recommendedPlayerId") is None:
        return (
            "INSUFFICIENT_DECISION_CONTEXT",
            {},
            _issue("recommendedPlayerId was never resolved -- no player identity to evaluate against."),
        )
    recommended_points = detail.get("recommendedPlayerActualPoints")
    starter_points = detail.get("actualStarterActualPoints")
    # The ONE new derived number this module computes: mirrors START_SIT's
    # own already-proven opportunity-cost formula (recommended vs. what the
    # owner actually started) -- contract Section 2/5's explicit rule that
    # this NEVER substitutes `bestAvailableAlternativeActualPoints` (a
    # hindsight-best comparison) for this recommendation-vs-actual one.
    if recommended_points is None or starter_points is None:
        opportunity_cost = None
    else:
        opportunity_cost = round(float(recommended_points) - float(starter_points), 2)
    if opportunity_cost is None:
        return (
            "INSUFFICIENT_DECISION_CONTEXT",
            {},
            _issue(
                "Real actual points were missing for the recommended player and/or the actually-"
                "started player at this position -- opportunity cost is not honestly computable."
            ),
        )
    return (
        "EVALUATED",
        {
            "streamerOpportunityCostPoints": opportunity_cost,
            "bestAvailableAlternativeActualPoints": detail.get("bestAvailableAlternativeActualPoints"),
        },
        (),
    )


def _extract_draft(_detail: Mapping[str, Any]) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    # Deliberately NOT_APPLICABLE for the whole cycle -- contract Section 2:
    # real season-long roster-utility evaluation belongs to
    # `marginal_roster_utility_v2`, outside this cycle's hard boundary.
    return "NOT_APPLICABLE", {}, _issue(
        "DRAFT outcome evaluation is deferred to a future, boundary-cleared pass "
        "(see DraftOutcomeDetail.evaluation_method)."
    )


_METRIC_EXTRACTORS_BY_DETAIL_KIND: Mapping[str, Any] = {
    "START_SIT_LINEUP_V1": _extract_start_sit,
    "WAIVER_V1": _extract_waiver,
    "ADD_DROP_V1": _extract_add_drop,
    "FAAB_V1": _extract_faab,
    "TRADE_V1": _extract_trade,
    "TRADE_FINDER_V1": _extract_trade_finder,
    "STREAMER_V1": _extract_streamer,
    "DRAFT_V1": _extract_draft,
}


def compute_outcome_evaluation(record: DecisionTraceRecord) -> OutcomeEvaluation:
    """The single canonical entry point for this module (contract Section
    1-6). PURE -- see the module docstring's "derived view" section. Takes
    ONLY an already-loaded `DecisionTraceRecord`; accepts no "current
    roster"/"current free agents"/network-fetch parameter of any kind
    (contract Section 5, hindsight rule 2 -- enforced structurally by this
    function's own signature, see
    `test_compute_outcome_evaluation_signature_accepts_no_current_state_
    parameter` below, not merely promised in prose).
    """

    outcome_window = EVALUATION_WINDOWS.get(record.tool, {"label": "UNDEFINED", "horizonWeeks": None})

    if record.tool == "DRAFT":
        status, metrics, issues = _extract_draft({})
        return OutcomeEvaluation(
            schema_version=SCHEMA_VERSION,
            trace_id=record.trace_id,
            decision_type=record.tool,
            league_key=record.profile_id,
            league_id=record.league_id,
            league_snapshot_id=record.league_snapshot_id,
            recommendation_generated_at=record.recorded_at_utc,
            outcome_observed_at=None,
            outcome_window_label=outcome_window["label"],
            outcome_window_horizon_weeks=outcome_window["horizonWeeks"],
            outcome_source=None,
            outcome_source_as_of=None,
            owner_action=record.owner_action,
            factual_outcome=record.outcome,
            evaluation_status=status,
            evaluation_metrics=metrics,
            issues=issues,
        )

    if record.outcome is None:
        return OutcomeEvaluation(
            schema_version=SCHEMA_VERSION,
            trace_id=record.trace_id,
            decision_type=record.tool,
            league_key=record.profile_id,
            league_id=record.league_id,
            league_snapshot_id=record.league_snapshot_id,
            recommendation_generated_at=record.recorded_at_utc,
            outcome_observed_at=None,
            outcome_window_label=outcome_window["label"],
            outcome_window_horizon_weeks=outcome_window["horizonWeeks"],
            outcome_source=None,
            outcome_source_as_of=None,
            owner_action=record.owner_action,
            factual_outcome=None,
            evaluation_status="PENDING_OUTCOME",
            evaluation_metrics={},
            issues=_issue("No outcome has been recorded for this trace yet."),
        )

    detail = record.outcome.get("detail")
    if not isinstance(detail, Mapping):
        status: str = "INSUFFICIENT_DECISION_CONTEXT"
        metrics: dict[str, Any] = {}
        issues: tuple[str, ...] = _issue(
            "No structured outcome detail was recorded -- only the legacy free-text outcome/notes "
            "pair exists. A real per-decision-type metric requires a structured detail payload from "
            "prospective_outcome_ingestion_v1_service."
        )
    else:
        extractor = _METRIC_EXTRACTORS_BY_DETAIL_KIND.get(str(detail.get("kind") or ""))
        if extractor is None:
            status, metrics, issues = (
                "INSUFFICIENT_DECISION_CONTEXT",
                {},
                _issue(f"Unrecognized outcome detail kind: {detail.get('kind')!r}."),
            )
        else:
            status, metrics, issues = extractor(detail)

    return OutcomeEvaluation(
        schema_version=SCHEMA_VERSION,
        trace_id=record.trace_id,
        decision_type=record.tool,
        league_key=record.profile_id,
        league_id=record.league_id,
        league_snapshot_id=record.league_snapshot_id,
        recommendation_generated_at=record.recorded_at_utc,
        outcome_observed_at=record.outcome.get("observedAt"),
        outcome_window_label=outcome_window["label"],
        outcome_window_horizon_weeks=outcome_window["horizonWeeks"],
        outcome_source=record.outcome.get("source"),
        outcome_source_as_of=record.outcome.get("sourceAsOf"),
        owner_action=record.owner_action,
        factual_outcome=record.outcome,
        evaluation_status=status,
        evaluation_metrics=metrics,
        issues=issues,
    )


# A structural (not merely conventional) hindsight-leakage defense: assert,
# at import time, that `compute_outcome_evaluation`'s own signature carries
# no parameter whose name suggests a "current"/"live"/"now" state read. Any
# future edit that adds such a parameter fails immediately and loudly,
# rather than silently reintroducing the exact leakage class the prior
# cycle's ingestion module spent real effort proving closed.
_FORBIDDEN_PARAMETER_NAME_FRAGMENTS = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")


def _assert_no_current_state_parameter(function: Any) -> None:
    for name in inspect.signature(function).parameters:
        lowered = name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_PARAMETER_NAME_FRAGMENTS):
            raise ProspectiveOutcomeEvaluationError(
                f"{function.__qualname__} accepts a parameter named {name!r}, which matches a "
                "forbidden 'current state' naming pattern -- the evaluation layer must only ever "
                "consume the trace's own frozen fields and already-ingested outcome data."
            )


_assert_no_current_state_parameter(compute_outcome_evaluation)
