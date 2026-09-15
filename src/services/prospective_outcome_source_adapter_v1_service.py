"""Prospective Outcomes V1 -- outcome SOURCE ADAPTERS (Work Unit 2).

The missing piece between (a) the existing append-only decision-trace
ledger (`in_season_decision_trace_service.py`) and (b) the existing pure
ingestion functions (`prospective_outcome_ingestion_v1_service.py`): a
real, reusable module that (1) reads a trace's own already-recorded,
frozen fields into an explicit `RecommendationTimeContext`, and (2)
performs the REAL network fetch of after-the-fact Sleeper data into an
explicit `RealizedOutcomeFetch` -- reusing the exact same
`SleeperHttpClient`/`api.sleeper.app` access every other real call site in
this codebase already uses (`sleeper_import_service.py`,
`desktop_facade.py`'s many `sleeper.get_json(...)` call sites,
`league/{id}/matchups/{week}` / `league/{id}/transactions/{round}` --
the same real, public, keyless, read-only endpoints the prior cycle's own
ingestion module docstring already named). **No new projection source is
built here** -- this module is entirely a thin, typed wrapper around
`SleeperHttpClient.get_json`, never a second data provider.

=== THE CORE HINDSIGHT-LEAKAGE DEFENSE (contract Section 5) ===

This module makes the recommendation-time/realized-outcome separation
STRUCTURALLY hard to violate, not merely documented, via two independent
mechanisms:

1. **Type separation.** `RecommendationTimeContext` and
   `RealizedOutcomeFetch` are two distinct frozen dataclasses with
   disjoint field sets. `recommendation_time_context_from_trace` (builds
   the former) takes ONLY a `DecisionTraceRecord` and performs NO network
   I/O -- there is no `SleeperHttpClient` parameter anywhere in its
   signature, so it is structurally IMPOSSIBLE for it to read fresh
   "current" data even by mistake. Every `fetch_*` function (builds the
   latter) REQUIRES an explicit `client: SleeperHttpClient` parameter --
   naming and typing that makes it immediately visually obvious, at every
   call site, which functions perform real I/O and which don't. A
   structural test below (`test_context_builder_signature_has_no_http_
   client_or_current_state_parameter`) asserts this by introspection, not
   convention.
2. **One-directional composition.** The one `adapt_and_ingest_*` function
   this pass ships (`adapt_and_ingest_start_sit_outcome`, the one decision
   type with real, live-verified data per the prior cycle) accepts a
   `RecommendationTimeContext` and a `RealizedOutcomeFetch` as two
   SEPARATE parameters and passes each one's own fields into the
   untouched `prospective_outcome_ingestion_v1_service` functions
   unchanged -- there is no step where a `RealizedOutcomeFetch` field
   could silently overwrite or "refresh" a `RecommendationTimeContext`
   field, because the two objects are never merged into one mutable
   structure; they are read from independently, once, at the ingestion
   call boundary.

This module performs real network I/O in its `fetch_*` functions ONLY --
`RecommendationTimeContext` construction and `adapt_and_ingest_*` remain
pure over already-fetched/already-loaded data, matching the ingestion
module's own "pure function" precedent.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_ingestion_v1_service import ingest_start_sit_outcome
from src.services.prospective_outcome_schema_v1_service import StartSitOutcomeDetail
from src.services.sleeper_import_service import SleeperHttpClient

SLEEPER_SOURCE_NAME = "SLEEPER"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# RECOMMENDATION-TIME DATA -- what was knowable when the recommendation was
# made. Built ONLY from a trace's own already-recorded, frozen fields.
# ZERO network I/O. ZERO "current"/"live" parameter of any kind.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecommendationTimeContext:
    trace_id: str
    decision_type: str
    league_id: str
    profile_id: str
    week: int | None
    recommendation: dict[str, Any]
    roster_state_player_ids: tuple[str, ...]
    free_agent_state_player_ids: tuple[str, ...] | None
    alternatives: tuple[dict[str, Any], ...]
    owner_action: dict[str, Any] | None


def recommendation_time_context_from_trace(record: DecisionTraceRecord) -> RecommendationTimeContext:
    """PURE. Reads ONLY `record`'s own already-recorded, frozen fields --
    the same fields the prior cycle's ingestion module already treats as
    the sole source of "what was known/eligible/recommended at the time"
    (see that module's own docstring). No network access, no "current"
    roster/free-agent read of any kind."""

    return RecommendationTimeContext(
        trace_id=record.trace_id,
        decision_type=record.tool,
        league_id=record.league_id,
        profile_id=record.profile_id,
        week=record.week,
        recommendation=dict(record.recommendation),
        roster_state_player_ids=tuple(record.roster_state_player_ids),
        free_agent_state_player_ids=(
            tuple(record.free_agent_state_player_ids)
            if record.free_agent_state_player_ids is not None
            else None
        ),
        alternatives=tuple(record.alternatives),
        owner_action=record.owner_action,
    )


# ---------------------------------------------------------------------------
# REALIZED OUTCOME DATA -- what factually happened later. Real network I/O
# lives ONLY in this section, via the same real, already-wired
# `SleeperHttpClient` every other call site in this codebase already uses.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RealizedOutcomeFetch:
    """One real, dated fetch of after-the-fact Sleeper data. `payload`'s
    shape depends on which `fetch_*` function produced it (documented on
    each function below) -- always genuinely real, already-fetched JSON,
    never a projection/estimate this module invents."""

    source: str
    league_id: str
    fetched_at_utc: str
    payload: Any


def fetch_week_matchups(client: SleeperHttpClient, league_id: str, week: int) -> RealizedOutcomeFetch:
    """`payload`: the raw list from `GET /league/{id}/matchups/{week}` --
    every roster's entry for that week, real, after that week's games have
    at least started (Sleeper populates `players_points` progressively as
    games are played)."""

    payload = client.get_json(f"league/{league_id}/matchups/{week}")
    return RealizedOutcomeFetch(
        source=SLEEPER_SOURCE_NAME, league_id=league_id, fetched_at_utc=_now_iso(), payload=payload
    )


def fetch_owner_matchup_entry(
    client: SleeperHttpClient, league_id: str, week: int, owner_roster_id: Any
) -> RealizedOutcomeFetch:
    """`payload`: ONE roster's own entry from that week's real matchups
    (or `None` if that roster has no entry yet -- an honest "not
    available," never fabricated). Reuses `fetch_week_matchups` rather
    than a second HTTP call pattern."""

    all_matchups = fetch_week_matchups(client, league_id, week)
    entries = all_matchups.payload if isinstance(all_matchups.payload, list) else []
    owner_entry = next(
        (
            entry
            for entry in entries
            if isinstance(entry, Mapping) and entry.get("roster_id") == owner_roster_id
        ),
        None,
    )
    return RealizedOutcomeFetch(
        source=SLEEPER_SOURCE_NAME,
        league_id=league_id,
        fetched_at_utc=all_matchups.fetched_at_utc,
        payload=owner_entry,
    )


def fetch_horizon_matchup_entries(
    client: SleeperHttpClient, league_id: str, weeks: Sequence[int], owner_roster_id: Any
) -> RealizedOutcomeFetch:
    """`payload`: a real list of this roster's own matchup entries across
    `weeks` (skipping any week with no real entry yet), the exact shape
    `ingest_waiver_outcome`/`ingest_add_drop_outcome`/`ingest_trade_outcome`
    already expect for their `horizon_matchup_entries` parameter."""

    entries: list[Mapping[str, Any]] = []
    for week in weeks:
        fetch = fetch_owner_matchup_entry(client, league_id, week, owner_roster_id)
        if isinstance(fetch.payload, Mapping):
            entries.append(fetch.payload)
    return RealizedOutcomeFetch(
        source=SLEEPER_SOURCE_NAME, league_id=league_id, fetched_at_utc=_now_iso(), payload=tuple(entries)
    )


def fetch_transactions_for_rounds(
    client: SleeperHttpClient, league_id: str, rounds: Sequence[int]
) -> RealizedOutcomeFetch:
    """`payload`: the real, COMBINED transaction list across every round in
    `rounds` -- `GET /league/{id}/transactions/{round}`, called once per
    round and concatenated. Addresses the prior cycle's own disclosed open
    issue (`WaiverOutcomeDetail`/`FaabOutcomeDetail`'s `claim_submitted=
    False`/`won=False` "are only as complete as the transactions_for_period
    the caller supplies"): a caller that wants a real, complete "did not
    claim" answer must fetch every relevant round, which this function
    does directly rather than leaving it to yet another ad hoc loop at
    each call site."""

    combined: list[Any] = []
    for round_number in rounds:
        round_transactions = client.get_json(f"league/{league_id}/transactions/{round_number}")
        if isinstance(round_transactions, list):
            combined.extend(round_transactions)
    return RealizedOutcomeFetch(
        source=SLEEPER_SOURCE_NAME, league_id=league_id, fetched_at_utc=_now_iso(), payload=tuple(combined)
    )


# ---------------------------------------------------------------------------
# Composition -- glues a RecommendationTimeContext and a RealizedOutcomeFetch
# together at the ingestion boundary ONLY. Each decision-type's ingestion
# function (untouched, from the prior cycle) still receives its
# recommendation-time fields and its realized-outcome fields as two
# genuinely separate argument groups -- see the module docstring's
# "one-directional composition" guarantee.
# ---------------------------------------------------------------------------


def adapt_and_ingest_start_sit_outcome(
    *, context: RecommendationTimeContext, matchup_fetch: RealizedOutcomeFetch
) -> StartSitOutcomeDetail:
    """The one concrete, worked adapter this pass ships (START_SIT is the
    one decision type with real, live-verified Week 1 2026 data, per the
    prior cycle -- see `docs/codex/prospective_outcome_v1/
    startsit_ingestion_demo_v1/summary.json`). Structurally the same
    recommendation-time/realized-outcome separation the demo script proved
    ad hoc, now a real, reusable, typed function."""

    if context.decision_type != "START_SIT":
        raise ValueError(
            f"adapt_and_ingest_start_sit_outcome requires a START_SIT context, got {context.decision_type!r}."
        )
    if matchup_fetch.source != SLEEPER_SOURCE_NAME:
        raise ValueError(f"Unrecognized realized-outcome source: {matchup_fetch.source!r}.")
    return ingest_start_sit_outcome(
        week=context.week,
        recommendation=context.recommendation,
        roster_state_player_ids=context.roster_state_player_ids,
        actual_matchup_entry=matchup_fetch.payload,
    )


# ---------------------------------------------------------------------------
# Structural hindsight-leakage defense: assert, at import time, that the
# pure context-builder's signature carries neither an HTTP-client
# parameter nor a "current state" parameter of any kind. Mirrors
# `prospective_outcome_evaluation_v1_service._assert_no_current_state_
# parameter` -- the same defense applied at this module's own boundary.
# ---------------------------------------------------------------------------

_FORBIDDEN_PARAMETER_NAME_FRAGMENTS = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")


def _assert_context_builder_is_pure(function: Any) -> None:
    parameters = inspect.signature(function).parameters
    for name, param in parameters.items():
        lowered = name.lower()
        if any(fragment in lowered for fragment in _FORBIDDEN_PARAMETER_NAME_FRAGMENTS):
            raise ValueError(
                f"{function.__qualname__} accepts a parameter named {name!r}, matching a forbidden "
                "'current state' naming pattern."
            )
        annotation = param.annotation
        if annotation is SleeperHttpClient or annotation == "SleeperHttpClient":
            raise ValueError(
                f"{function.__qualname__} accepts a SleeperHttpClient parameter -- the recommendation-"
                "time context builder must never perform network I/O."
            )


_assert_context_builder_is_pure(recommendation_time_context_from_trace)
