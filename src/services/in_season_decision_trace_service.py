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
"""

from __future__ import annotations

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
    if tool not in TOOL_TYPES:
        raise DecisionTraceError(f"Unknown tool type: {tool!r}. Must be one of {sorted(TOOL_TYPES)}.")
    if not league_id or not profile_id:
        raise DecisionTraceError("league_id and profile_id are required.")
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
    root: str | Path, profile_id: str, trace_id: str, *, outcome: str, notes: str = ""
) -> DecisionTraceRecord:
    """The append-only OUTCOME write path (NWR Post-UI Product V1, P1-4).

    Mirrors `record_owner_action` exactly: appends a NEW line referencing
    the same `trace_id`, never edits or backdates the original
    recommendation line. Defined as a real, usable contract even though no
    real 2026-season outcome exists yet for anything this ledger has
    recorded so far (every event recorded to date is prospective, from
    'now' forward) -- nothing calls this function in production yet, and
    that is the honest, correct state until a real observed result exists
    to append. `outcome` is intentionally a free-text/caller-defined label
    (e.g. "WON_MATCHUP", "PLAYER_STARTED_AS_RECOMMENDED") -- this module
    computes no calibration metric over it; it only stores what actually
    happened, later, as its own separate fact.
    """

    existing = {record.trace_id: record for record in load_decision_traces(root, profile_id)}
    original = existing.get(trace_id)
    if original is None:
        raise DecisionTraceError(f"No decision trace found with id {trace_id!r} for profile {profile_id!r}.")
    updated = replace(
        original,
        status="OUTCOME_RECORDED",
        outcome={"outcome": outcome, "notes": notes},
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
