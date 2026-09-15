"""In-Season Decision Trace (NWR Overnight V3, Lane 18).

Built regardless of which in-season engines are currently live/blocked, per
the governing directive -- the schema exists now so every future
recommendation (including ones from tools this session left BLOCKED, e.g.
none currently, or a future engine) has one real, consistent record shape
to log into from day one.

Append-only JSON-lines ledger, one file per Redraft profile
(`<root>/decision_traces/<profile_id>.jsonl`), mirroring this repo's
existing per-profile file convention (`draft_boards/<profile_id>.json`).
Append-only, never rewritten in place: recording an owner action or a real
outcome writes a NEW line referencing the same `trace_id` rather than
mutating the original recommendation line -- the original recommendation is
permanent, unedited history; `load_decision_traces` reconstructs the latest
state per `trace_id` by folding lines in file order (last write wins).

Explicitly NO future-outcome field at recommendation-TIME (e.g. no
"actual points scored," "was this correct," or any hindsight field) --
only `owner_action` (what the owner actually did) and `outcome` (a real,
observed result) are ever added, and strictly AFTER the recommendation, via
their own separate append calls (`record_owner_action` /
`record_outcome`), only ever to a NEW line, never backdated into the
original. A freshly recorded recommendation's own JSON row carries neither
key at all (see `to_json_row` -- both are omitted, not merely null, until a
real append actually happens), so no consumer of the raw row can mistake an
empty placeholder for "no outcome yet exists as a concept."

NWR Post-UI Product V1 (P1-4, Prospective Recommendation Ledger): extends
this same append-only ledger rather than building a second, parallel trace
system --
- `TOOL_TYPES` gains `TRADE_FINDER`, `TRADE_PACKAGE_SEARCH`, and `DRAFT`
  (alongside the seven tool types this module already covered). The first
  two close a real, found bug: `desktop_facade.py`'s Trade Finder and
  Worker 6/7's new Trade Package Search call sites already called
  `record_decision_trace(tool="TRADE_FINDER" / "TRADE_PACKAGE_SEARCH", ...)`
  today, but neither string was a member of the old `TOOL_TYPES` set --
  every such call silently raised `DecisionTraceError`, caught by the
  facade's own best-effort wrapper (`_record_decision_trace_safe`), so
  BOTH tools have been recording zero real traces in production despite
  looking fully wired. `DRAFT` is added to the schema per the governing
  directive so the shape exists for a future draft-side wiring pass; this
  pass does not itself add a live `DRAFT` call site (draft recommendation
  logic is explicitly out of this pass's hard boundary).
- Two new, additive, optional fields on every record: `league_snapshot_id`
  (the same `LeagueSnapshot` identity every migrated tool's own
  `DecisionResultEnvelope` already computes -- so a trace can be tied back
  to the exact rules/roster/week state it was generated from) and
  `status_versions` (a small, honest fingerprint of the
  `PlayerAvailabilityStatus` authority in effect when the recommendation
  was generated -- never a semantic version number where none exists).
  Both default to `None`/`{}` for full backward compatibility with every
  existing caller/row.
- `record_outcome`: the append-only OUTCOME write path the governing
  directive asks be defined even if nothing calls it yet (no real 2026
  season outcome exists for anything recorded so far). Mirrors
  `record_owner_action` exactly -- appends a NEW line, never mutates the
  original recommendation line, never backdates a value into it.

NWR Post-UI Product V1 (Closure Worker C, verification pass): a real
pathological-duplication bug was FOUND and fixed here, not merely checked
for. Every facade call site above is reached from a plain `useAsync`
page-mount/dependency-change effect on the frontend (Weekly Home, Lineup,
Waivers/Improve Team, Trade Finder, Find Trades), never gated behind an
explicit "record this" button -- so a page refresh, a route remount, or
even React StrictMode's dev-mode double-invoke calls the SAME facade
method (and therefore `record_decision_trace`) again for the exact same
underlying recommendation, with no code path that previously prevented a
brand-new ledger line (and a brand-new random `trace_id`) every single
time. `record_decision_trace` now recognizes an immediate repeat of the
SAME recommendation (identical tool/week/roster-state/free-agent-state/
recommendation/alternatives content, for the same league) recorded within
`DEDUP_WINDOW_SECONDS` and returns the EXISTING record instead of
appending a duplicate line -- idempotent, not lossy: any genuinely
different content (a different top add, a different lineup swap, a
different trade package -- the real, deterministic output of a changed
roster/week/data state) still always gets a new line immediately, and an
identical recommendation recorded again AFTER the window has elapsed also
still gets a new line (this ledger does not silently collapse a
legitimately time-separated "still recommended" event into its
predecessor -- only a same-instant refresh/remount storm is collapsed).
No historical line is ever deleted, edited, or backdated to implement
this -- see `record_decision_trace`'s own docstring below.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

TOOL_TYPES = frozenset(
    {
        "START_SIT", "WAIVER", "ADD_DROP", "FAAB", "TRADE", "K_STREAMER", "DST_STREAMER",
        "TRADE_FINDER", "TRADE_PACKAGE_SEARCH", "DRAFT",
    }
)

# NWR Post-UI Product V1 (Closure Worker C): how long a freshly-computed
# recommendation with IDENTICAL content to the most recent recorded trace
# for the same (league, tool, week) is treated as a duplicate of that same
# recorded event rather than a new one. Sized to comfortably absorb a
# refresh/remount storm (a slow reload, a React StrictMode double-invoke, a
# few quick back-and-forth page visits) while staying far short of a
# realistic "the owner came back later and the recommendation genuinely
# hasn't changed yet" gap, which this ledger deliberately still records as
# its own new event once the window has elapsed.
DEDUP_WINDOW_SECONDS = 300


def _content_fingerprint(
    *,
    tool: str,
    week: int | None,
    roster_state_player_ids: Sequence[str],
    free_agent_state_player_ids: Sequence[str] | None,
    recommendation: Mapping[str, Any],
    alternatives: Sequence[Mapping[str, Any]],
) -> str:
    """A stable hash of everything that makes a recommendation event
    genuinely distinct -- deliberately EXCLUDES `trace_id`/`recorded_at_utc`
    (always fresh) and `league_snapshot_id`/`status_versions`/
    `engine_version`/`data_versions` (provenance metadata about HOW the
    recommendation was computed, not WHAT was recommended -- two identical
    recommendations computed a few seconds apart on an unchanged roster
    would otherwise never match on `league_snapshot_id`/timest-derived
    fields alone). `roster_state_player_ids`/`free_agent_state_player_ids`
    are sorted before hashing since they are set-like roster membership,
    not an intentionally-ordered sequence -- the same real roster read
    twice must fingerprint identically even if dict/set iteration order
    ever differs between the two reads."""

    payload = {
        "tool": tool,
        "week": week,
        "roster_state_player_ids": sorted(str(value) for value in roster_state_player_ids),
        "free_agent_state_player_ids": (
            sorted(str(value) for value in free_agent_state_player_ids)
            if free_agent_state_player_ids is not None
            else None
        ),
        "recommendation": recommendation,
        "alternatives": list(alternatives),
    }
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class DecisionTraceError(ValueError):
    pass


@dataclass(frozen=True)
class DecisionTraceRecord:
    trace_id: str
    league_id: str
    profile_id: str
    season: int
    week: int | None
    tool: str
    engine_version: str
    data_versions: dict[str, str]
    roster_state_player_ids: tuple[str, ...]
    free_agent_state_player_ids: tuple[str, ...] | None
    recommendation: dict[str, Any]
    alternatives: tuple[dict[str, Any], ...]
    recorded_at_utc: str
    status: str = "RECOMMENDED"
    owner_action: dict[str, Any] | None = None
    owner_action_recorded_at_utc: str | None = None
    # NWR Post-UI Product V1 (P1-4): additive-only, default-backward-
    # compatible fields -- every pre-existing call site/row that doesn't
    # know about these still round-trips byte-for-byte the same otherwise.
    league_snapshot_id: str | None = None
    status_versions: dict[str, str] = field(default_factory=dict)
    outcome: dict[str, Any] | None = None
    outcome_recorded_at_utc: str | None = None

    def to_json_row(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "trace_id": self.trace_id,
            "league_id": self.league_id,
            "profile_id": self.profile_id,
            "season": self.season,
            "week": self.week,
            "tool": self.tool,
            "engine_version": self.engine_version,
            "data_versions": self.data_versions,
            "league_snapshot_id": self.league_snapshot_id,
            "status_versions": dict(self.status_versions),
            "roster_state_player_ids": list(self.roster_state_player_ids),
            "free_agent_state_player_ids": (
                list(self.free_agent_state_player_ids)
                if self.free_agent_state_player_ids is not None
                else None
            ),
            "recommendation": self.recommendation,
            "alternatives": list(self.alternatives),
            "recorded_at_utc": self.recorded_at_utc,
            "status": self.status,
            "owner_action": self.owner_action,
            "owner_action_recorded_at_utc": self.owner_action_recorded_at_utc,
        }
        # Deliberately omitted (not even a null placeholder) until a real
        # `record_outcome` append actually happens -- see the module
        # docstring and `test_no_future_outcome_field_exists_on_the_record_
        # shape`: a freshly recorded recommendation must carry no
        # outcome-shaped key at all, not just a falsy one.
        if self.outcome is not None:
            row["outcome"] = self.outcome
            row["outcome_recorded_at_utc"] = self.outcome_recorded_at_utc
        return row


def _trace_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "decision_traces" / f"{profile_id}.jsonl"


def record_decision_trace(
    root: str | Path,
    profile_id: str,
    *,
    league_id: str,
    season: int,
    week: int | None,
    tool: str,
    engine_version: str,
    data_versions: Mapping[str, str],
    roster_state_player_ids: Sequence[str],
    recommendation: Mapping[str, Any],
    free_agent_state_player_ids: Sequence[str] | None = None,
    alternatives: Sequence[Mapping[str, Any]] = (),
    league_snapshot_id: str | None = None,
    status_versions: Mapping[str, str] | None = None,
) -> DecisionTraceRecord:
    """Appends a new RECOMMENDED line to the ledger -- UNLESS the most
    recently recorded trace for this exact (league_id, tool, week) already
    carries byte-identical recommendation content (see
    `_content_fingerprint`) AND was recorded within `DEDUP_WINDOW_SECONDS`
    of now, in which case that EXISTING record is returned as-is and no new
    line is written. NWR Post-UI Product V1 (Closure Worker C): a real,
    found fix for pathological page-refresh/remount duplication -- see the
    module docstring. Never deletes, edits, or backdates any existing line;
    a genuinely new recommendation (different content, or the same content
    recorded again after the window elapses) is always appended as its own
    new event, exactly as before this fix."""

    if tool not in TOOL_TYPES:
        raise DecisionTraceError(f"Unknown tool type: {tool!r}. Must be one of {sorted(TOOL_TYPES)}.")
    if not league_id or not profile_id:
        raise DecisionTraceError("league_id and profile_id are required.")

    now = datetime.now(UTC)
    fingerprint = _content_fingerprint(
        tool=tool, week=week, roster_state_player_ids=roster_state_player_ids,
        free_agent_state_player_ids=free_agent_state_player_ids,
        recommendation=recommendation, alternatives=alternatives,
    )
    same_scope = [
        existing
        for existing in load_decision_traces(root, profile_id, tool=tool)
        # Explicit `== week` (not relying on `load_decision_traces`'s own
        # `week` filter, which treats `week=None` as "no week filter at
        # all" -- some tools, e.g. WAIVER, legitimately record BOTH a
        # week-scoped (THIS_WEEK) and a week-agnostic (REST_OF_SEASON,
        # `week=None`) trace for the same league, and this dedup check must
        # only ever compare like-for-like.
        if existing.league_id == league_id and existing.week == week
    ]
    if same_scope:
        most_recent = max(same_scope, key=lambda existing: existing.recorded_at_utc)
        try:
            most_recent_at = datetime.fromisoformat(most_recent.recorded_at_utc)
        except ValueError:
            most_recent_at = None
        if most_recent_at is not None and abs((now - most_recent_at).total_seconds()) <= DEDUP_WINDOW_SECONDS:
            existing_fingerprint = _content_fingerprint(
                tool=most_recent.tool, week=most_recent.week,
                roster_state_player_ids=most_recent.roster_state_player_ids,
                free_agent_state_player_ids=most_recent.free_agent_state_player_ids,
                recommendation=most_recent.recommendation, alternatives=most_recent.alternatives,
            )
            if existing_fingerprint == fingerprint:
                return most_recent

    record = DecisionTraceRecord(
        trace_id=str(uuid4()),
        league_id=league_id,
        profile_id=profile_id,
        season=season,
        week=week,
        tool=tool,
        engine_version=engine_version,
        data_versions=dict(data_versions),
        roster_state_player_ids=tuple(roster_state_player_ids),
        free_agent_state_player_ids=(
            tuple(free_agent_state_player_ids) if free_agent_state_player_ids is not None else None
        ),
        recommendation=dict(recommendation),
        alternatives=tuple(dict(item) for item in alternatives),
        recorded_at_utc=datetime.now(UTC).isoformat(),
        league_snapshot_id=league_snapshot_id,
        status_versions=dict(status_versions) if status_versions is not None else {},
    )
    path = _trace_path(root, profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_json_row(), sort_keys=True))
        handle.write("\n")
    return record


def record_owner_action(
    root: str | Path, profile_id: str, trace_id: str, *, action: str, notes: str = ""
) -> DecisionTraceRecord:
    """Appends a NEW line updating one existing trace with the owner's real,
    already-taken action -- never edits the original recommendation line,
    never records a predicted/hypothetical future outcome."""

    existing = {record.trace_id: record for record in load_decision_traces(root, profile_id)}
    original = existing.get(trace_id)
    if original is None:
        raise DecisionTraceError(f"No decision trace found with id {trace_id!r} for profile {profile_id!r}.")
    updated = replace(
        original,
        # If a real outcome was somehow already recorded before this owner-
        # action append (an unusual order, but not impossible), the record's
        # status stays at the further-along "OUTCOME_RECORDED" stage rather
        # than regressing -- status always reflects the LATEST lifecycle
        # stage this trace has genuinely reached.
        status="OUTCOME_RECORDED" if original.outcome is not None else "OWNER_ACTION_RECORDED",
        owner_action={"action": action, "notes": notes},
        owner_action_recorded_at_utc=datetime.now(UTC).isoformat(),
    )
    path = _trace_path(root, profile_id)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(updated.to_json_row(), sort_keys=True))
        handle.write("\n")
    return updated


def record_outcome(
    root: str | Path,
    profile_id: str,
    trace_id: str,
    *,
    outcome: str,
    notes: str = "",
    detail: Mapping[str, Any] | None = None,
    outcome_source: str | None = None,
    outcome_source_as_of: str | None = None,
    outcome_observed_at: str | None = None,
) -> DecisionTraceRecord:
    """The append-only OUTCOME write path (NWR Post-UI Product V1, P1-4).

    Mirrors `record_owner_action` exactly: appends a NEW line referencing
    the same `trace_id`, never edits or backdates the original
    recommendation line. `outcome` stays a free-text/caller-defined summary
    label (e.g. "WON_MATCHUP", "PLAYER_STARTED_AS_RECOMMENDED") for
    backward compatibility with every existing caller -- this module still
    computes no calibration metric over it.

    NWR Prospective Outcome V1: `detail` is the OPTIONAL,
    decision-type-specific structured payload (see
    `prospective_outcome_schema_v1_service.py` -- one distinct dataclass
    per decision type, e.g. `StartSitOutcomeDetail`/`WaiverOutcomeDetail`/
    `FaabOutcomeDetail`, deliberately NOT one generic accuracy score).
    Callers pass `detail=<schema>.to_detail_dict()`. Omitted (`None`, the
    default) for full backward compatibility: no `detail` key is added to
    the stored outcome payload at all when absent, so every pre-existing
    caller/row/test that only ever passed `outcome`/`notes` round-trips
    byte-for-byte the same as before this change.

    NWR Prospective Outcomes V1 (Work Unit 1, canonical outcome event
    contract): three further OPTIONAL provenance fields, each additive and
    independently omittable, matching the exact same backward-compatible
    pattern `detail` already established -- none is added to the stored
    payload at all unless the caller actually supplies it, so any call that
    predates this pass (or that still only wants `outcome`/`notes`/`detail`)
    round-trips byte-for-byte identically:
    - `outcome_source`: a short, real provenance tag naming WHERE the
      factual outcome data came from (e.g. "SLEEPER") -- never a guess,
      never defaulted to a value the caller didn't actually supply.
    - `outcome_source_as_of`: a real ISO-8601 UTC timestamp for WHEN the
      source data this outcome was computed from was actually fetched
      (distinct from `outcome_recorded_at_utc`, which is when THIS ledger
      append happened -- the source fetch may have occurred earlier, e.g.
      inside an orchestration job).
    - `outcome_observed_at`: a real ISO-8601 UTC timestamp for WHEN the
      real-world event itself became observable (e.g. a week's games
      finished, a waiver period closed) -- distinct from both of the above.
    See `prospective_outcome_evaluation_v1_service.py` (the canonical
    single-event outcome-evaluation contract this pass builds on top of
    this ledger) for how these three fields are consumed.
    """

    existing = {record.trace_id: record for record in load_decision_traces(root, profile_id)}
    original = existing.get(trace_id)
    if original is None:
        raise DecisionTraceError(f"No decision trace found with id {trace_id!r} for profile {profile_id!r}.")
    outcome_payload: dict[str, Any] = {"outcome": outcome, "notes": notes}
    if detail is not None:
        outcome_payload["detail"] = dict(detail)
    if outcome_source is not None:
        outcome_payload["source"] = outcome_source
    if outcome_source_as_of is not None:
        outcome_payload["sourceAsOf"] = outcome_source_as_of
    if outcome_observed_at is not None:
        outcome_payload["observedAt"] = outcome_observed_at
    updated = replace(
        original,
        status="OUTCOME_RECORDED",
        outcome=outcome_payload,
        outcome_recorded_at_utc=datetime.now(UTC).isoformat(),
    )
    path = _trace_path(root, profile_id)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(updated.to_json_row(), sort_keys=True))
        handle.write("\n")
    return updated


def load_decision_traces(
    root: str | Path,
    profile_id: str,
    *,
    tool: str | None = None,
    week: int | None = None,
) -> tuple[DecisionTraceRecord, ...]:
    path = _trace_path(root, profile_id)
    if not path.is_file():
        return ()
    latest_by_id: dict[str, DecisionTraceRecord] = {}
    order: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue  # a malformed line never crashes the whole ledger read
        trace_id = str(row.get("trace_id") or "")
        if not trace_id:
            continue
        if trace_id not in latest_by_id:
            order.append(trace_id)
        latest_by_id[trace_id] = DecisionTraceRecord(
            trace_id=trace_id,
            league_id=str(row.get("league_id") or ""),
            profile_id=str(row.get("profile_id") or ""),
            season=int(row.get("season") or 0),
            week=row.get("week"),
            tool=str(row.get("tool") or ""),
            engine_version=str(row.get("engine_version") or ""),
            data_versions=dict(row.get("data_versions") or {}),
            roster_state_player_ids=tuple(row.get("roster_state_player_ids") or ()),
            free_agent_state_player_ids=(
                tuple(row["free_agent_state_player_ids"])
                if row.get("free_agent_state_player_ids") is not None
                else None
            ),
            recommendation=dict(row.get("recommendation") or {}),
            alternatives=tuple(row.get("alternatives") or ()),
            recorded_at_utc=str(row.get("recorded_at_utc") or ""),
            status=str(row.get("status") or "RECOMMENDED"),
            owner_action=row.get("owner_action"),
            owner_action_recorded_at_utc=row.get("owner_action_recorded_at_utc"),
            league_snapshot_id=row.get("league_snapshot_id"),
            status_versions=dict(row.get("status_versions") or {}),
            outcome=row.get("outcome"),
            outcome_recorded_at_utc=row.get("outcome_recorded_at_utc"),
        )
    records = [latest_by_id[trace_id] for trace_id in order]
    if tool is not None:
        records = [record for record in records if record.tool == tool]
    if week is not None:
        records = [record for record in records if record.week == week]
    return tuple(records)
