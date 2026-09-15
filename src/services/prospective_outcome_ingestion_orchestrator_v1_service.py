"""Prospective Outcomes V1 -- Work Unit 12: AUTOMATIC OUTCOME INGESTION
ORCHESTRATION.

The single most important open item flagged by all three prior workers
this cycle (LEDGER.md, every worker's own "Open Issues" section): nothing
in this codebase automatically CALLS any of the 8 `evaluate_*` functions or
the ingestion functions. This module is that real, repeatable, idempotent
orchestrator -- reusing, never duplicating, every piece the prior three
workers already built:

- `in_season_decision_trace_service.load_decision_traces`/`record_outcome`
  (the ledger itself).
- `prospective_outcome_evaluation_v1_service.EVALUATION_WINDOWS`/
  `compute_outcome_evaluation` (the frozen, preregistered windows -- NEVER
  re-derived here).
- `prospective_outcome_source_adapter_v1_service`
  (`recommendation_time_context_from_trace`/`fetch_owner_matchup_entry`/
  `adapt_and_ingest_start_sit_outcome`) -- the one real, worked, network-
  fetching composition function from Worker 1.
- `prospective_outcome_ingestion_v1_service`'s pure `ingest_*_outcome`
  functions (Worker 1/prior cycle) -- called directly for the identity-
  unresolved classes (see below), exactly the same functions every
  evaluator already builds on.
- The 8 per-class `evaluate_*` functions (Workers 2/3) -- called on the
  freshly-updated record immediately after an outcome append, so a real
  evaluation is computed and exposed in this run's own report the same
  pass it was ingested.

=== WHAT THIS ORCHESTRATOR ACTUALLY DOES PER TRACE, HONESTLY SCOPED ===

Real per-tool identity resolution is genuinely incomplete in this
codebase (Worker 1's Open Issue 3, sharpened by Worker 3's own live-call-
site findings, both unchanged coming into this pass):

- **START_SIT** is the ONE class whose real, live call site
  (`weekly_lineup_optimizer_service` via `desktop_facade.py`) already
  records raw Sleeper player ids directly (`recommendation.starters`).
  This is the ONE class this orchestrator gives a REAL, FULL pipeline: a
  real `fetch_owner_matchup_entry` call, `adapt_and_ingest_start_sit_
  outcome`, a real `record_outcome(..., outcome_source="SLEEPER", ...)`
  append, then `evaluate_start_sit` on the result.
- **WAIVER** records `topAddCanonicalId` (NWR's own ranking-id space, not
  a Sleeper id) and **FAAB** records only `playerName` (no id at all) --
  confirmed by reading `desktop_facade.py`'s real call sites directly this
  pass (same discipline Worker 3 used for TRADE/K/DST). **K_STREAMER/
  DST_STREAMER** record only `playerName`/`team`, never a Sleeper id
  (Worker 3's own confirmed finding, unchanged). **ADD_DROP** has NO live
  call site in this codebase at all (Worker 2/3's own confirmed finding).
  None of these five classes' real recommendation-time identity can be
  honestly resolved to a Sleeper id without building a brand-new identity-
  resolution crosswalk (`resolve_roster_canonical_ids` + a fresh players-
  catalog/ranking-rows fetch) -- explicitly out of THIS pass's scope, per
  the governing directive's own "reuse the existing source adapters ...
  and evaluators" framing (not "build new identity resolution"). For these
  five, once their window has genuinely matured, this orchestrator records
  a REAL, EXPLICIT `INSUFFICIENT_DECISION_CONTEXT` outcome (via the SAME
  `ingest_*_outcome` function every evaluator already trusts, called with
  the player id argument(s) honestly `None`) -- never silently skipped,
  never confused with "not yet processed." See the governing directive's
  own item 6.
- **TRADE / TRADE_FINDER / TRADE_PACKAGE_SEARCH** record `week=None` at
  their real, live call sites (confirmed by reading `desktop_facade.py`
  this pass) -- there is no real week number this orchestrator could
  anchor a 4-week bounded-horizon maturity check to without inventing one.
  Rather than fabricate a week, this orchestrator leaves every trade-family
  trace GENUINELY UNTOUCHED this pass (`SKIP_WINDOW_UNDETERMINABLE`) -- a
  real, disclosed open issue (Section "open issues" below), not a silent
  gap.
- **DRAFT** is always skipped (`SKIP_DEFERRED_DRAFT`) -- deferred for the
  whole cycle, contract Section 2, unchanged hard boundary.

=== IDEMPOTENCY, THE CORE DESIGN GUARANTEE ===

`plan_ingestion_action` checks `record.outcome is not None` FIRST, before
any maturity/identity logic -- a trace that already carries a real,
previously-recorded outcome (from THIS orchestrator or from any other real
caller) is always `SKIP_ALREADY_PROCESSED`, unconditionally. Since
`record_outcome` is the ONLY thing that ever sets `record.outcome`, and
this orchestrator only ever calls it for traces it just planned to
process, running `run_ingestion` twice against the SAME trace store is
guaranteed to make real ledger writes on the FIRST run only -- the second
run's own `plan_ingestion_action` call for every one of those traces
immediately returns `SKIP_ALREADY_PROCESSED` before touching the network or
the ledger again. Proven for real (not just argued) in
`tests/test_prospective_outcome_ingestion_orchestrator_v1_service.py`'s own
`test_running_ingestion_twice_produces_byte_identical_ledger_state` --
byte-for-byte file comparison, not just "no crash."

=== HINDSIGHT SAFETY ===

`plan_ingestion_action` is PURE (no network, no "current" parameter beyond
the one real, named `current_nfl_week` int the caller must supply --
itself a real, dated fact from `GET /state/nfl`, structurally distinct from
a "current roster"/"current free agents" read the contract's hindsight
rules forbid). All real network I/O lives only in `run_ingestion`'s own
dispatch to `execute_plan_item`, mirroring the exact same "type/function
separation makes the boundary visible" discipline
`prospective_outcome_source_adapter_v1_service.py` already established.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from src.services.in_season_decision_trace_service import (
    DecisionTraceRecord,
    load_decision_traces,
    record_outcome,
)
from src.services.prospective_outcome_add_drop_evaluator_v1_service import evaluate_add_drop
from src.services.prospective_outcome_dst_streamer_evaluator_v1_service import evaluate_dst_streamer
from src.services.prospective_outcome_evaluation_v1_service import EVALUATION_WINDOWS
from src.services.prospective_outcome_faab_evaluator_v1_service import evaluate_faab
from src.services.prospective_outcome_ingestion_v1_service import (
    ingest_add_drop_outcome,
    ingest_faab_outcome,
    ingest_streamer_outcome,
    ingest_waiver_outcome,
)
from src.services.prospective_outcome_k_streamer_evaluator_v1_service import evaluate_k_streamer
from src.services.prospective_outcome_source_adapter_v1_service import (
    adapt_and_ingest_start_sit_outcome,
    fetch_owner_matchup_entry,
    recommendation_time_context_from_trace,
)
from src.services.prospective_outcome_start_sit_evaluator_v1_service import evaluate_start_sit
from src.services.prospective_outcome_waiver_evaluator_v1_service import evaluate_waiver
from src.services.sleeper_import_service import SleeperHttpClient

SCHEMA_VERSION = "prospective_outcome_ingestion_orchestrator_v1"

# ---------------------------------------------------------------------------
# A closed, frozen set of real planning actions -- adding a new one is a
# deliberate, named code change, never a silent new string.
# ---------------------------------------------------------------------------

ACTION_SKIP_ALREADY_PROCESSED = "SKIP_ALREADY_PROCESSED"
ACTION_SKIP_DEFERRED_DRAFT = "SKIP_DEFERRED_DRAFT"
ACTION_SKIP_WINDOW_UNDETERMINABLE = "SKIP_WINDOW_UNDETERMINABLE"
ACTION_SKIP_IMMATURE_WINDOW = "SKIP_IMMATURE_WINDOW"
ACTION_SKIP_OWNER_ROSTER_UNKNOWN = "SKIP_OWNER_ROSTER_UNKNOWN"
ACTION_PROCESS_FULL_START_SIT = "PROCESS_FULL_START_SIT"
ACTION_PROCESS_INSUFFICIENT_CONTEXT = "PROCESS_INSUFFICIENT_CONTEXT"

PLAN_ACTIONS = frozenset(
    {
        ACTION_SKIP_ALREADY_PROCESSED,
        ACTION_SKIP_DEFERRED_DRAFT,
        ACTION_SKIP_WINDOW_UNDETERMINABLE,
        ACTION_SKIP_IMMATURE_WINDOW,
        ACTION_SKIP_OWNER_ROSTER_UNKNOWN,
        ACTION_PROCESS_FULL_START_SIT,
        ACTION_PROCESS_INSUFFICIENT_CONTEXT,
    }
)

# Tools this orchestrator can produce a real, explicit
# INSUFFICIENT_DECISION_CONTEXT outcome for, once matured -- see module
# docstring for exactly why each one's real identity cannot be resolved
# this pass.
_INSUFFICIENT_CONTEXT_TOOLS = frozenset({"WAIVER", "FAAB", "ADD_DROP", "K_STREAMER", "DST_STREAMER"})

_EVALUATOR_BY_TOOL = {
    "START_SIT": evaluate_start_sit,
    "WAIVER": evaluate_waiver,
    "ADD_DROP": evaluate_add_drop,
    "FAAB": evaluate_faab,
    "K_STREAMER": evaluate_k_streamer,
    "DST_STREAMER": evaluate_dst_streamer,
}


class ProspectiveOutcomeIngestionOrchestratorError(ValueError):
    pass


@dataclass(frozen=True)
class IngestionPlanItem:
    trace_id: str
    tool: str
    league_id: str
    profile_id: str
    week: int | None
    action: str
    reason: str

    def __post_init__(self) -> None:
        if self.action not in PLAN_ACTIONS:
            raise ProspectiveOutcomeIngestionOrchestratorError(f"Unknown plan action: {self.action!r}.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "tool": self.tool,
            "leagueId": self.league_id,
            "profileId": self.profile_id,
            "week": self.week,
            "action": self.action,
            "reason": self.reason,
        }


def plan_ingestion_action(
    record: DecisionTraceRecord,
    *,
    current_nfl_week: int,
    owner_roster_id_by_league: Mapping[str, Any],
) -> IngestionPlanItem:
    """PURE. Decides WHAT to do with one already-loaded trace -- never
    itself fetches or writes anything. See module docstring for the exact
    per-tool reasoning; nothing here re-derives a preregistered window
    (`EVALUATION_WINDOWS`, imported verbatim from Worker 1's frozen
    module)."""

    def _item(action: str, reason: str) -> IngestionPlanItem:
        return IngestionPlanItem(
            trace_id=record.trace_id, tool=record.tool, league_id=record.league_id,
            profile_id=record.profile_id, week=record.week, action=action, reason=reason,
        )

    if record.tool == "DRAFT":
        return _item(
            ACTION_SKIP_DEFERRED_DRAFT,
            "DRAFT outcome evaluation is deferred for this entire cycle (contract Section 2) -- never "
            "processed by this orchestrator.",
        )

    # Idempotency gate -- checked BEFORE anything else, unconditionally.
    # A trace that already carries a real outcome (from this orchestrator
    # or any other real caller) is never revisited.
    if record.outcome is not None:
        return _item(ACTION_SKIP_ALREADY_PROCESSED, "This trace already has a real outcome recorded.")

    window = EVALUATION_WINDOWS.get(record.tool)
    if window is None or window.get("horizonWeeks") is None:
        return _item(
            ACTION_SKIP_WINDOW_UNDETERMINABLE,
            f"No preregistered, numeric evaluation window exists for tool {record.tool!r}.",
        )

    if record.week is None:
        # TRADE / TRADE_FINDER / TRADE_PACKAGE_SEARCH's real live call
        # sites record week=None -- there is no real week number to anchor
        # a bounded-horizon maturity check to. Never fabricated.
        return _item(
            ACTION_SKIP_WINDOW_UNDETERMINABLE,
            f"Tool {record.tool!r} recorded week=None -- this orchestrator cannot honestly determine "
            "window maturity without a real recommendation-time week to anchor the horizon to (a real, "
            "disclosed open issue -- see the module docstring).",
        )

    horizon_weeks = int(window["horizonWeeks"])
    matured = current_nfl_week > (record.week + horizon_weeks)
    if not matured:
        return _item(
            ACTION_SKIP_IMMATURE_WINDOW,
            f"Window {window['label']!r} (horizon {horizon_weeks} weeks from week {record.week}) has not "
            f"genuinely matured yet -- current NFL week is {current_nfl_week}.",
        )

    if record.tool == "START_SIT":
        owner_roster_id = owner_roster_id_by_league.get(record.league_id)
        if owner_roster_id is None:
            return _item(
                ACTION_SKIP_OWNER_ROSTER_UNKNOWN,
                f"No owner_roster_id was supplied for league {record.league_id!r} -- this is an "
                "orchestration-configuration gap, not a decision-context gap, so this trace is left "
                "genuinely untouched (PENDING_OUTCOME) rather than marked INSUFFICIENT_DECISION_CONTEXT.",
            )
        return _item(ACTION_PROCESS_FULL_START_SIT, "Real Sleeper matchup data can be fetched and ingested.")

    if record.tool in _INSUFFICIENT_CONTEXT_TOOLS:
        return _item(
            ACTION_PROCESS_INSUFFICIENT_CONTEXT,
            f"Tool {record.tool!r}'s real recommendation-time identity cannot be resolved to a Sleeper "
            "player id from the trace's own frozen fields alone (see module docstring) -- recorded as a "
            "real, explicit INSUFFICIENT_DECISION_CONTEXT outcome now that the window has matured.",
        )

    return _item(
        ACTION_SKIP_WINDOW_UNDETERMINABLE, f"No real ingestion path is wired for tool {record.tool!r} yet."
    )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _build_insufficient_context_detail(record: DecisionTraceRecord) -> dict[str, Any]:
    """Reuses the SAME pure `ingest_*_outcome` functions every evaluator
    already trusts -- called with the player id argument(s) honestly
    `None`, which is exactly the input shape each of these functions
    already documents/handles (see
    `prospective_outcome_ingestion_v1_service.py`). `owner_roster_id=None`
    is always safe here: every one of these functions only reads
    `owner_roster_id` inside a branch gated on the player id being
    non-`None`, which never happens on this path."""

    recommendation = record.recommendation or {}
    if record.tool == "WAIVER":
        return ingest_waiver_outcome(
            recommended_player_id=None, owner_roster_id=None, transactions_for_period=(),
        ).to_detail_dict()
    if record.tool == "FAAB":
        def _num(value: Any) -> float | None:
            return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None

        return ingest_faab_outcome(
            recommended_player_id=None, owner_roster_id=None,
            suggested_bid_low=_num(recommendation.get("bidLowDollars")),
            suggested_bid_high=_num(recommendation.get("bidHighDollars")),
            transactions_for_period=(),
        ).to_detail_dict()
    if record.tool == "ADD_DROP":
        return ingest_add_drop_outcome(
            added_player_id=None, dropped_player_id=None, owner_roster_id=None, transactions_for_period=(),
        ).to_detail_dict()
    if record.tool in ("K_STREAMER", "DST_STREAMER"):
        position = "K" if record.tool == "K_STREAMER" else "DST"
        return ingest_streamer_outcome(
            position=position, week=record.week, recommended_player_id=None,
            prior_roster_option_player_id=None, available_alternative_ids_at_recommendation=(),
            actual_matchup_entry=None,
        ).to_detail_dict()
    raise ProspectiveOutcomeIngestionOrchestratorError(
        f"No insufficient-context detail builder is wired for tool {record.tool!r}."
    )


@dataclass(frozen=True)
class ExecutedIngestionResult:
    trace_id: str
    tool: str
    action: str
    outcome_label: str
    evaluation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "tool": self.tool,
            "action": self.action,
            "outcomeLabel": self.outcome_label,
            "evaluation": self.evaluation,
        }


def execute_plan_item(
    item: IngestionPlanItem,
    record: DecisionTraceRecord,
    *,
    root: str | Path,
    client: SleeperHttpClient | None = None,
    owner_roster_id_by_league: Mapping[str, Any] | None = None,
) -> ExecutedIngestionResult:
    """Performs the REAL work for one PROCESS_* plan item: a real network
    fetch (START_SIT only) or none at all (insufficient-context path), a
    real `record_outcome` append, then a real per-class `evaluate_*` call
    on the freshly-updated record -- computing and exposing the evaluation
    the SAME pass it was ingested (directive item 4). Only ever called for
    an `IngestionPlanItem` whose `action` is one of the two `PROCESS_*`
    members -- any other action is a caller error."""

    if item.action == ACTION_PROCESS_FULL_START_SIT:
        if client is None:
            raise ProspectiveOutcomeIngestionOrchestratorError(
                "A real SleeperHttpClient is required to process a START_SIT trace."
            )
        owner_roster_id = (owner_roster_id_by_league or {}).get(record.league_id)
        if owner_roster_id is None:
            raise ProspectiveOutcomeIngestionOrchestratorError(
                f"No owner_roster_id supplied for league {record.league_id!r} -- plan_ingestion_action "
                "should never have chosen PROCESS_FULL_START_SIT without one."
            )
        context = recommendation_time_context_from_trace(record)
        matchup_fetch = fetch_owner_matchup_entry(client, record.league_id, record.week, owner_roster_id)
        detail = adapt_and_ingest_start_sit_outcome(context=context, matchup_fetch=matchup_fetch)
        outcome_label = (
            "STARTER_MATCHED_RECOMMENDATION" if not detail.recommended_only_ids else "STARTER_DEVIATED"
        )
        updated = record_outcome(
            root, record.profile_id, record.trace_id,
            outcome=outcome_label,
            detail=detail.to_detail_dict(),
            outcome_source=matchup_fetch.source,
            outcome_source_as_of=matchup_fetch.fetched_at_utc,
            outcome_observed_at=matchup_fetch.fetched_at_utc,
        )
        evaluation = evaluate_start_sit(updated, matchup_fetch=matchup_fetch).to_dict()
        return ExecutedIngestionResult(
            trace_id=record.trace_id, tool="START_SIT", action=item.action,
            outcome_label=outcome_label, evaluation=evaluation,
        )

    if item.action == ACTION_PROCESS_INSUFFICIENT_CONTEXT:
        detail = _build_insufficient_context_detail(record)
        updated = record_outcome(
            root, record.profile_id, record.trace_id,
            outcome="INSUFFICIENT_DECISION_CONTEXT",
            notes=item.reason,
            detail=detail,
        )
        evaluator = _EVALUATOR_BY_TOOL[record.tool]
        evaluation = evaluator(updated).to_dict()
        return ExecutedIngestionResult(
            trace_id=record.trace_id, tool=record.tool, action=item.action,
            outcome_label="INSUFFICIENT_DECISION_CONTEXT", evaluation=evaluation,
        )

    raise ProspectiveOutcomeIngestionOrchestratorError(f"execute_plan_item does not handle action {item.action!r}.")


@dataclass(frozen=True)
class IngestionRunReport:
    schema_version: str
    generated_at_utc: str
    current_nfl_week: int
    counts_by_action: dict[str, int]
    processed: tuple[dict[str, Any], ...]
    skipped: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "generatedAtUtc": self.generated_at_utc,
            "currentNflWeek": self.current_nfl_week,
            "countsByAction": dict(self.counts_by_action),
            "processed": list(self.processed),
            "skipped": list(self.skipped),
        }


def _discover_profile_ids(root: str | Path) -> tuple[str, ...]:
    trace_dir = Path(root) / "decision_traces"
    if not trace_dir.is_dir():
        return ()
    return tuple(sorted(path.stem for path in trace_dir.glob("*.jsonl")))


def run_ingestion(
    root: str | Path,
    *,
    profile_ids: tuple[str, ...] | None = None,
    client: SleeperHttpClient | None = None,
    current_nfl_week: int | None = None,
    owner_roster_id_by_league: Mapping[str, Any] | None = None,
) -> IngestionRunReport:
    """The real, callable, idempotent entry point (directive Work Unit 12).
    Safe to call repeatedly against the SAME `root` -- see module docstring
    for the idempotency guarantee's exact mechanism.

    `owner_roster_id_by_league`: a real, caller-supplied `{league_id:
    roster_id}` mapping -- resolving this generically (from a profile's own
    stored Sleeper identity) would require reading profile/league-workspace
    state this pass deliberately does not reach into (out of scope; see
    open issues). Defaults to `{}` (every START_SIT trace becomes
    `SKIP_OWNER_ROSTER_UNKNOWN` until a real mapping is supplied).
    """

    owner_roster_id_by_league = dict(owner_roster_id_by_league or {})
    resolved_client = client or SleeperHttpClient()
    if current_nfl_week is None:
        state = resolved_client.get_json("state/nfl")
        from src.services.sleeper_league_context_service import parse_current_nfl_week

        parsed_week = parse_current_nfl_week(state)
        if parsed_week is None:
            raise ProspectiveOutcomeIngestionOrchestratorError(
                "Could not determine the real current NFL week from GET /state/nfl -- refusing to guess "
                "a maturity boundary."
            )
        current_nfl_week = parsed_week

    resolved_profile_ids = profile_ids if profile_ids is not None else _discover_profile_ids(root)

    processed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    counts: dict[str, int] = {}

    for profile_id in resolved_profile_ids:
        for record in load_decision_traces(root, profile_id):
            item = plan_ingestion_action(
                record, current_nfl_week=current_nfl_week, owner_roster_id_by_league=owner_roster_id_by_league,
            )
            counts[item.action] = counts.get(item.action, 0) + 1

            if item.action in (ACTION_PROCESS_FULL_START_SIT, ACTION_PROCESS_INSUFFICIENT_CONTEXT):
                result = execute_plan_item(
                    item, record, root=root, client=resolved_client,
                    owner_roster_id_by_league=owner_roster_id_by_league,
                )
                processed.append(result.to_dict())
            else:
                skipped.append(item.to_dict())

    return IngestionRunReport(
        schema_version=SCHEMA_VERSION,
        generated_at_utc=_now_iso(),
        current_nfl_week=current_nfl_week,
        counts_by_action=counts,
        processed=tuple(processed),
        skipped=tuple(skipped),
    )


# ---------------------------------------------------------------------------
# Structural hindsight-leakage defense, same pattern as every other module
# this cycle -- asserted at import time, not only promised in prose.
# ---------------------------------------------------------------------------

_FORBIDDEN_PARAMETER_NAME_FRAGMENTS = ("current_roster", "current_free_agent", "live_roster", "now_roster")


def _assert_plan_function_is_safe(function: Any) -> None:
    for name in inspect.signature(function).parameters:
        lowered = name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_PARAMETER_NAME_FRAGMENTS):
            raise ProspectiveOutcomeIngestionOrchestratorError(
                f"{function.__qualname__} accepts a parameter named {name!r}, matching a forbidden "
                "'current state' naming pattern."
            )


_assert_plan_function_is_safe(plan_ingestion_action)
