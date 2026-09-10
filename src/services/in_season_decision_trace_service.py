"""In-Season Decision Trace (NWR Overnight V3, Lane 18).

Built regardless of which in-season engines are currently live/blocked, per
the governing directive -- the schema exists now so every future
recommendation (including ones from tools this session left BLOCKED, e.g.
none currently, or a future engine) has one real, consistent record shape
to log into from day one.

Append-only JSON-lines ledger, one file per Redraft profile
(`<root>/decision_traces/<profile_id>.jsonl`), mirroring this repo's
existing per-profile file convention (`draft_boards/<profile_id>.json`).
Append-only, never rewritten in place: recording an owner action writes a
NEW line referencing the same `trace_id` rather than mutating the original
recommendation line -- the original recommendation is permanent, unedited
history; `load_decision_traces` reconstructs the latest state per
`trace_id` by folding lines in file order (last write wins).

Explicitly NO future-outcome field at recommendation time (e.g. no
"actual points scored," "was this correct," or any hindsight field) --
only `owner_action` (what the owner actually did, recorded strictly AFTER
the recommendation, via a separate call) is ever added, and only to a NEW
line, never backdated into the original.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

TOOL_TYPES = frozenset(
    {"START_SIT", "WAIVER", "ADD_DROP", "FAAB", "TRADE", "K_STREAMER", "DST_STREAMER"}
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

    def to_json_row(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "league_id": self.league_id,
            "profile_id": self.profile_id,
            "season": self.season,
            "week": self.week,
            "tool": self.tool,
            "engine_version": self.engine_version,
            "data_versions": self.data_versions,
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
        status="OWNER_ACTION_RECORDED",
        owner_action={"action": action, "notes": notes},
        owner_action_recorded_at_utc=datetime.now(UTC).isoformat(),
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
        )
    records = [latest_by_id[trace_id] for trace_id in order]
    if tool is not None:
        records = [record for record in records if record.tool == tool]
    if week is not None:
        records = [record for record in records if record.week == week]
    return tuple(records)
