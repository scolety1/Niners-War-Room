"""NWR Prospective Outcomes V1 -- Work Units 13-14: History UI V3 / class-
specific summary PRESENTATION layer.

Pure composition, zero new evaluation logic. Every number this module
returns was already computed by one of the 8 real, already-tested per-class
evaluator modules (Workers 2/3) or the base `compute_outcome_evaluation`
contract (Worker 1) -- this module only (a) dispatches a `DecisionTraceRecord`
to the correct evaluator by its own `tool` field and returns that evaluator's
own `to_dict()` verbatim, and (b) groups many records by class and calls the
matching `summarize_*` function, also verbatim. Nothing here recomputes a
metric, re-derives a threshold, or invents a new status.

Hard boundary: does not import or touch `marginal_roster_utility_v2`,
`LeagueSnapshot`, `LeagueWorkspaceContext`, `lifecycle_resolver`,
`DecisionResultEnvelope`, or `PlayerAvailabilityStatus`. DRAFT has no real
evaluator this cycle (contract Section 2 -- deferred to season-long roster
utility, outside this cycle's hard boundary); every DRAFT trace is presented
via the base `compute_outcome_evaluation`, which the base module itself
always resolves to `NOT_APPLICABLE` with zero metrics for DRAFT.

Per-class only (contract Section 6): `class_specific_summaries` builds one
independent summary dict per real decision class -- TRADE_FINDER and
TRADE_PACKAGE_SEARCH are summarized TOGETHER under one shared "TRADE_FINDER"
key (Worker 3's own design: one shared evaluator/summary function for both
real tool types, per the contract's Section 1 table row), but this is never
merged with plain TRADE, and no key anywhere in this module's output is a
cross-class blend. Every `summarize_*` function already applies the
contract's Section 7 minimum-sample gate (`MIN_SAMPLE_SIZE_FOR_PER_CLASS_
SUMMARY = 20`, imported transitively, never re-derived here) via each
module's own `summary_status`/`SUMMARIZED`/`NOT_ENOUGH_DATA_YET` values --
this module does not re-implement or second-guess that gate.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_evaluation_v1_service import compute_outcome_evaluation
from src.services.prospective_outcome_add_drop_evaluator_v1_service import (
    evaluate_add_drop,
    summarize_add_drop_evaluations,
)
from src.services.prospective_outcome_dst_streamer_evaluator_v1_service import (
    evaluate_dst_streamer,
    summarize_dst_streamer_evaluations,
)
from src.services.prospective_outcome_faab_evaluator_v1_service import (
    evaluate_faab,
    summarize_faab_evaluations,
)
from src.services.prospective_outcome_k_streamer_evaluator_v1_service import (
    evaluate_k_streamer,
    summarize_k_streamer_evaluations,
)
from src.services.prospective_outcome_start_sit_evaluator_v1_service import (
    evaluate_start_sit,
    summarize_start_sit_evaluations,
)
from src.services.prospective_outcome_trade_evaluator_v1_service import (
    evaluate_trade,
    summarize_trade_evaluations,
)
from src.services.prospective_outcome_trade_finder_evaluator_v1_service import (
    evaluate_trade_finder,
    summarize_trade_finder_evaluations,
)
from src.services.prospective_outcome_waiver_evaluator_v1_service import (
    evaluate_waiver,
    summarize_waiver_evaluations,
)

# Real per-record dispatch table. TRADE_FINDER and TRADE_PACKAGE_SEARCH both
# reuse `evaluate_trade_finder` (Worker 3's own design, contract Section 1).
# DRAFT is deliberately absent -- handled by the fallback branch below.
_EVALUATORS: dict[str, Callable[[DecisionTraceRecord], Any]] = {
    "START_SIT": evaluate_start_sit,
    "WAIVER": evaluate_waiver,
    "ADD_DROP": evaluate_add_drop,
    "FAAB": evaluate_faab,
    "TRADE": evaluate_trade,
    "TRADE_FINDER": evaluate_trade_finder,
    "TRADE_PACKAGE_SEARCH": evaluate_trade_finder,
    "K_STREAMER": evaluate_k_streamer,
    "DST_STREAMER": evaluate_dst_streamer,
}


def evaluation_payload_for_record(record: DecisionTraceRecord) -> dict[str, Any]:
    """The real, per-record evaluation payload for one History UI row.

    Dispatches to the correct evaluator by `record.tool` and returns that
    evaluator's own `to_dict()` verbatim (already includes the nested base
    `evaluation` block -- `evaluationStatus`/`evaluationMetrics`/`issues` --
    plus that class's own real extra fields, e.g.
    `lineupOpportunityCostPoints` for START_SIT). DRAFT and any tool this
    cycle built no evaluator for fall back to the base
    `compute_outcome_evaluation(record).to_dict()`, wrapped in the same
    `{traceId, evaluation}` envelope shape every evaluator's own `to_dict()`
    uses, so the frontend never has to special-case the fallback shape.

    A trace whose `tool` matches a real evaluator but whose stored detail is
    malformed/legacy (a genuine data-integrity mismatch, not expected in
    practice) falls back the same way rather than raising and breaking the
    whole History page for one bad row -- disclosed here, not silently
    swallowed elsewhere.
    """

    evaluator = _EVALUATORS.get(record.tool)
    if evaluator is None:
        evaluation = compute_outcome_evaluation(record)
        return {"traceId": record.trace_id, "evaluation": evaluation.to_dict()}
    try:
        result = evaluator(record)
    except ValueError:
        evaluation = compute_outcome_evaluation(record)
        return {"traceId": record.trace_id, "evaluation": evaluation.to_dict()}
    return result.to_dict()


# Per-class summarizers, EXCLUDING the trade-finder family (handled
# separately below since it combines two real tool types into one summary).
_SUMMARIZERS: dict[str, tuple[Callable[[DecisionTraceRecord], Any], Callable[[Sequence[Any]], dict[str, Any]]]] = {
    "START_SIT": (evaluate_start_sit, summarize_start_sit_evaluations),
    "WAIVER": (evaluate_waiver, summarize_waiver_evaluations),
    "ADD_DROP": (evaluate_add_drop, summarize_add_drop_evaluations),
    "FAAB": (evaluate_faab, summarize_faab_evaluations),
    "TRADE": (evaluate_trade, summarize_trade_evaluations),
    "K_STREAMER": (evaluate_k_streamer, summarize_k_streamer_evaluations),
    "DST_STREAMER": (evaluate_dst_streamer, summarize_dst_streamer_evaluations),
}

# The real, closed set of decision classes this summary surface reports --
# matches the contract's own Section 1 table exactly (TRADE_FINDER stands in
# for both TRADE_FINDER and TRADE_PACKAGE_SEARCH; DRAFT is always
# NOT_APPLICABLE this cycle). Never silently drop a class just because its
# real sample this run is zero -- a zero-sample class still reports a real,
# honest "NOT_ENOUGH_DATA_YET" entry, never an absent key.
CLASS_SUMMARY_DECISION_TYPES: tuple[str, ...] = (
    "START_SIT",
    "WAIVER",
    "ADD_DROP",
    "FAAB",
    "TRADE",
    "TRADE_FINDER",
    "K_STREAMER",
    "DST_STREAMER",
    "DRAFT",
)


def _as_count_pairs(mapping: Any, *, key_field: str) -> list[dict[str, Any]]:
    """A real, narrow, DISCLOSED bug fix found and fixed this pass (Work
    Unit 14's own HTTP wiring, never touching any evaluator's computation):
    `desktop_facade.py`'s response envelope runs every dict KEY in the
    response through a generic snake_case/ENUM -> camelCase transform
    (`contracts.py::camel_case_key`) -- the SAME real bug class already
    disclosed and fixed for player-id dict keys
    (`_points_by_player_list` in `prospective_outcome_schema_v1_service.py`,
    e.g. a Sleeper DST team code `"NE"` mangled to `"nE"`). Worker 2/3's own
    `summarize_*_evaluations` functions build real `statusCounts`/
    `acceptanceStatusCounts`/`packageDispositionCounts` dicts KEYED BY a real
    `evaluationStatus`/`acceptanceStatus`/`packageDisposition` ENUM STRING
    (e.g. `"EVALUATED"` -> mangled to `"eVALUATED"` over HTTP) -- correct and
    fully tested in isolation (pytest never exercises the HTTP envelope), but
    never actually wired to any HTTP endpoint before this pass, so this
    mangling was never observed until this pass's real Chrome dogfood
    surfaced it live. Fixed HERE, at THIS presentation layer, by reshaping
    the mangling-prone dict into a `[{<key_field>, count}]` LIST immediately
    before it leaves this module -- the evaluator's own dict-returning
    `summarize_*` functions are NOT modified, matching the same list-not-
    dict pattern this codebase already established for exactly this bug
    class. Never a cross-class field -- always applied within one class's
    own summary only."""

    if not isinstance(mapping, dict):
        return []
    return [{key_field: key, "count": count} for key, count in mapping.items()]


def _reshape_summary_for_transport(summary: dict[str, Any]) -> dict[str, Any]:
    reshaped = dict(summary)
    if "statusCounts" in reshaped:
        reshaped["statusCounts"] = _as_count_pairs(reshaped["statusCounts"], key_field="status")
    if "acceptanceStatusCounts" in reshaped:
        reshaped["acceptanceStatusCounts"] = _as_count_pairs(reshaped["acceptanceStatusCounts"], key_field="status")
    if "packageDispositionCounts" in reshaped:
        reshaped["packageDispositionCounts"] = _as_count_pairs(reshaped["packageDispositionCounts"], key_field="disposition")
    return reshaped


def class_specific_summaries(records: Sequence[DecisionTraceRecord]) -> list[dict[str, Any]]:
    """Work Unit 14 -- one independent summary dict per real decision class,
    ordered by `CLASS_SUMMARY_DECISION_TYPES`. Never a cross-class
    leaderboard/blended score (contract Section 6) -- every value under one
    entry comes from exactly one class's own `summarize_*` function, and no
    entry here averages/ranks across classes.

    Returns a LIST (each entry already carries its own real `decisionType`
    field), not a dict keyed by decisionType -- the same real, disclosed
    reason `_as_count_pairs` above exists: a dict keyed by an arbitrary
    ENUM-like string (`"START_SIT"`, `"K_STREAMER"`, ...) gets mangled by
    the same generic HTTP camelCase-key transform. This was true from Work
    Unit 14's very first version of this function; fixed in the same pass
    that found it, before any other worker or the owner ever saw the bug
    live.
    """

    by_tool: dict[str, list[DecisionTraceRecord]] = {}
    for record in records:
        by_tool.setdefault(record.tool, []).append(record)

    summaries: dict[str, dict[str, Any]] = {}
    for decision_type, (evaluator, summarizer) in _SUMMARIZERS.items():
        tool_records = by_tool.get(decision_type, [])
        results = [evaluator(record) for record in tool_records]
        summaries[decision_type] = summarizer(results)

    trade_finder_records = list(by_tool.get("TRADE_FINDER", [])) + list(by_tool.get("TRADE_PACKAGE_SEARCH", []))
    trade_finder_results = [evaluate_trade_finder(record) for record in trade_finder_records]
    summaries["TRADE_FINDER"] = summarize_trade_finder_evaluations(trade_finder_results)

    draft_records = by_tool.get("DRAFT", [])
    summaries["DRAFT"] = {
        "decisionType": "DRAFT",
        "statusCounts": {"NOT_APPLICABLE": len(draft_records)} if draft_records else {},
        "note": (
            "DRAFT outcome evaluation is deferred to marginal_roster_utility_v2's real "
            "season-long roster-utility computation, outside this cycle's hard boundary -- "
            "never scored here, and never reported as NOT_ENOUGH_DATA_YET (a different, "
            "structural reason -- contract Section 2/8)."
        ),
    }
    return [_reshape_summary_for_transport(summaries[decision_type]) for decision_type in CLASS_SUMMARY_DECISION_TYPES]
