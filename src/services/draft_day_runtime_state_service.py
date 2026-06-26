from __future__ import annotations

import csv
import json
import os
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

RuntimeState = dict[str, Any]

DEFAULT_DRAFT_ID = "draft_day_v2"
DEFAULT_RUNTIME_ROOT = Path(r"C:\NWR_SHARED_DATA\draft_runtime_state")
SCHEMA_VERSION = "draft_day_runtime_v2"
APP_VERSION = "draft_day_v2_local"
CURRENT_DRAFT_SEASON = "2026"


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    state_dir: Path
    export_dir: Path
    backup_dir: Path


@dataclass(frozen=True)
class RuntimeLoadResult:
    state: RuntimeState
    status: str
    path: Path
    warning: str
    quarantine_path: Path | None = None


@dataclass(frozen=True)
class RuntimeImportPreview:
    valid: bool
    summary: dict[str, str]
    warnings: tuple[str, ...]
    state: RuntimeState | None = None


def runtime_paths(root: Path | None = None) -> RuntimePaths:
    resolved_root = root or Path(
        os.environ.get("NWR_DRAFT_DAY_RUNTIME_ROOT", str(DEFAULT_RUNTIME_ROOT))
    )
    return RuntimePaths(
        root=resolved_root,
        state_dir=resolved_root / "state",
        export_dir=resolved_root / "exports",
        backup_dir=resolved_root / "backups",
    )


def runtime_state_path(
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
    root: Path | None = None,
) -> Path:
    paths = runtime_paths(root)
    return paths.state_dir / f"{_safe_token(draft_id)}__{_safe_token(mode)}.json"


def empty_runtime_state(
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
    source_checkpoint: str = "",
) -> RuntimeState:
    timestamp = _now()
    return {
        "schema_version": SCHEMA_VERSION,
        "draft_session_id": draft_id,
        "draft_id": draft_id,
        "mode": mode,
        "source_checkpoint": source_checkpoint,
        "source_version": "",
        "app_version": APP_VERSION,
        "created_at": timestamp,
        "updated_at": timestamp,
        "created_at_utc": timestamp,
        "updated_at_utc": timestamp,
        "current_pick": "",
        "drafted_players": [],
        "drafted_player_ids": [],
        "pick_events": [],
        "workflow_state": {"assignments": []},
        "pick_ownership_overrides": {},
        "event_log": [],
        "trade_events": [],
        "notes": [],
    }


def load_runtime_state(
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
    source_checkpoint: str = "",
    root: Path | None = None,
) -> RuntimeState:
    return load_runtime_state_with_status(
        mode=mode,
        draft_id=draft_id,
        source_checkpoint=source_checkpoint,
        root=root,
    ).state


def load_runtime_state_with_status(
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
    source_checkpoint: str = "",
    root: Path | None = None,
) -> RuntimeLoadResult:
    path = runtime_state_path(mode=mode, draft_id=draft_id, root=root)
    if not path.exists():
        state = _mark_recovery_status(
            empty_runtime_state(
                mode=mode,
                draft_id=draft_id,
                source_checkpoint=source_checkpoint,
            ),
            status="MISSING_STATE_FILE",
            warning=(
                "No local draft runtime state file exists yet. This is an empty "
                "runtime state, not a silent official reset."
            ),
        )
        return RuntimeLoadResult(
            state=state,
            status="MISSING_STATE_FILE",
            path=path,
            warning=str(state["runtime_load_warning"]),
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        quarantine_path = quarantine_corrupt_runtime_state(
            path,
            root=root,
            reason="load_failed",
        )
        state = _mark_recovery_status(
            empty_runtime_state(
                mode=mode,
                draft_id=draft_id,
                source_checkpoint=source_checkpoint,
            ),
            status="CORRUPT_STATE_QUARANTINED",
            warning=(
                "Local draft runtime state was unreadable and was quarantined. "
                "Review the quarantine backup before continuing."
            ),
            detail={"error": type(exc).__name__, "quarantine_path": str(quarantine_path)},
        )
        return RuntimeLoadResult(
            state=state,
            status="CORRUPT_STATE_QUARANTINED",
            path=path,
            warning=str(state["runtime_load_warning"]),
            quarantine_path=quarantine_path,
        )
    state = normalize_runtime_state(raw, mode=mode, draft_id=draft_id)
    return RuntimeLoadResult(
        state=_mark_recovery_status(state, status="LOADED", warning=""),
        status="LOADED",
        path=path,
        warning="",
    )


def quarantine_corrupt_runtime_state(
    path: Path,
    *,
    root: Path | None = None,
    reason: str = "corrupt",
) -> Path:
    paths = runtime_paths(root)
    quarantine_dir = paths.backup_dir / "quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _safe_token(_now().replace("+00:00", "Z"))
    quarantine_path = quarantine_dir / f"{path.stem}__{timestamp}__{_safe_token(reason)}.json"
    if path.exists():
        try:
            path.replace(quarantine_path)
        except OSError:
            quarantine_path.write_text(path.read_text(encoding="utf-8", errors="replace"))
    return quarantine_path


def load_latest_runtime_state(
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
    source_checkpoint: str = "",
    root: Path | None = None,
) -> RuntimeState:
    return load_runtime_state(
        mode=mode,
        draft_id=draft_id,
        source_checkpoint=source_checkpoint,
        root=root,
    )


def save_runtime_state(
    state: RuntimeState,
    *,
    event_type: str,
    event_detail: dict[str, Any] | None = None,
    root: Path | None = None,
    create_backup: bool = True,
) -> RuntimeState:
    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    event = build_event(event_type, event_detail or {})
    normalized["event_log"].append(event)
    if event_type in {"pick_assigned", "pick_imported", "pick_restored"}:
        normalized["pick_events"].append(
            build_pick_event(event, event_detail or {}, source=_pick_source(event_type))
        )
    timestamp = _now()
    normalized["updated_at"] = timestamp
    normalized["updated_at_utc"] = timestamp
    normalized = _sync_derived_state_fields(normalized)
    path = runtime_state_path(
        mode=str(normalized["mode"]),
        draft_id=str(normalized["draft_id"]),
        root=root,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(path, normalized)
    if create_backup:
        create_runtime_backup(normalized, root=root, reason=f"auto_{event_type}")
    return normalized


def update_workflow_state(
    state: RuntimeState,
    workflow_state: dict[str, Any],
    *,
    event_type: str,
    event_detail: dict[str, Any] | None = None,
    root: Path | None = None,
) -> RuntimeState:
    updated = deepcopy(state)
    updated["workflow_state"] = _normalize_workflow_state(workflow_state)
    return save_runtime_state(
        updated,
        event_type=event_type,
        event_detail=event_detail,
        root=root,
    )


def record_trade_event(
    state: RuntimeState,
    *,
    team_a: str = "",
    team_b: str = "",
    team_a_sends: str = "",
    team_b_sends: str = "",
    notes: str = "",
    trade_type: str = "",
    counterparty: str = "",
    sends: str = "",
    receives: str = "",
    source: str = "manual",
    status: str = "active",
    root: Path | None = None,
) -> RuntimeState:
    updated = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    if not team_a and (trade_type or counterparty or sends or receives):
        team_a = "NWR"
        team_b = counterparty
        team_a_sends = sends
        team_b_sends = receives
    team_a = team_a.strip() or "Team A"
    team_b = team_b.strip() or "Team B"
    team_a_assets = parse_trade_assets(team_a_sends)
    team_b_assets = parse_trade_assets(team_b_sends)
    trade_id = str(uuid4())
    affected_picks = [
        *[
            _affected_pick(asset, new_owner=team_b, direction=f"{team_a} sends")
            for asset in team_a_assets
        ],
        *[
            _affected_pick(asset, new_owner=team_a, direction=f"{team_b} sends")
            for asset in team_b_assets
        ],
    ]
    affected_picks = [pick for pick in affected_picks if pick]
    ownership_overrides = dict(updated.get("pick_ownership_overrides", {}))
    for affected in affected_picks:
        pick_label = str(affected.get("pick_label") or "")
        new_owner = str(affected.get("new_owner") or "")
        if pick_label and new_owner and affected.get("can_update_board"):
            ownership_overrides[pick_label] = {
                "new_owner": new_owner,
                "trade_id": trade_id,
                "source": source,
                "status": status,
            }
    trade = {
        "trade_id": trade_id,
        "timestamp": _now(),
        "recorded_at_utc": _now(),
        "team_a": team_a,
        "team_b": team_b,
        "team_a_sends": team_a_sends.strip(),
        "team_b_sends": team_b_sends.strip(),
        "team_a_assets": team_a_assets,
        "team_b_assets": team_b_assets,
        "affected_picks": affected_picks,
        "notes": notes.strip(),
        "source": source,
        "status": status,
        "trade_type": trade_type or "manual_trade",
        "counterparty": team_b,
        "sends": team_a_sends.strip(),
        "receives": team_b_sends.strip(),
        "current_year_pick_changes": [
            {
                "pick_label": str(pick.get("pick_label") or ""),
                "new_owner": str(pick.get("new_owner") or ""),
                "direction": str(pick.get("direction") or ""),
            }
            for pick in affected_picks
            if pick.get("can_update_board")
        ],
        "future_picks": [
            str(asset.get("display_label") or asset.get("raw_text") or "")
            for asset in [*team_a_assets, *team_b_assets]
            if asset.get("asset_type") == "future_pick"
        ],
        "guardrail_status": "display-only event; no trade calculator or model advice",
    }
    updated["trade_events"].append(trade)
    updated["pick_ownership_overrides"] = ownership_overrides
    return save_runtime_state(
        updated,
        event_type="trade_recorded",
        event_detail=trade,
        root=root,
    )


def reset_runtime_state(
    state: RuntimeState,
    *,
    reason: str,
    root: Path | None = None,
) -> RuntimeState:
    create_runtime_backup(state, root=root, reason="before_reset")
    reset_state = empty_runtime_state(
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
        source_checkpoint=str(state.get("source_checkpoint") or ""),
    )
    return save_runtime_state(
        reset_state,
        event_type="reset_confirmed",
        event_detail={"reason": reason},
        root=root,
    )


def reset_runtime_state_if_confirmed(
    state: RuntimeState,
    *,
    confirmed: bool,
    reason: str,
    root: Path | None = None,
) -> RuntimeState:
    if not confirmed:
        return normalize_runtime_state(
            state,
            mode=str(state.get("mode") or "draft"),
            draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
        )
    return reset_runtime_state(state, reason=reason, root=root)


def export_runtime_state(
    state: RuntimeState,
    *,
    root: Path | None = None,
) -> dict[str, Path]:
    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    normalized = _sync_derived_state_fields(normalized)
    paths = runtime_paths(root)
    paths.export_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{_safe_token(str(normalized['draft_id']))}__{_safe_token(str(normalized['mode']))}"
    json_path = paths.export_dir / f"{prefix}_draft_log.json"
    csv_path = paths.export_dir / f"{prefix}_draft_log.csv"
    md_path = paths.export_dir / f"{prefix}_draft_log.md"

    _write_json_atomic(json_path, normalized)
    rows = event_rows(normalized)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp_utc",
                "event_type",
                "summary",
                "player",
                "pick",
                "counterparty",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    md_path.write_text(markdown_export(normalized), encoding="utf-8")
    return {"json": json_path, "csv": csv_path, "markdown": md_path}


def export_runtime_state_json(state: RuntimeState) -> str:
    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    return json.dumps(_sync_derived_state_fields(normalized), indent=2, sort_keys=True)


def restore_runtime_state_from_json(
    payload: str | bytes,
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
    root: Path | None = None,
    current_state: RuntimeState | None = None,
) -> RuntimeState:
    preview = preview_runtime_state_import(payload, mode=mode, draft_id=draft_id)
    if not preview.valid or preview.state is None:
        raise ValueError("; ".join(preview.warnings) or "Invalid draft runtime JSON import.")
    if current_state is not None:
        create_runtime_backup(current_state, root=root, reason="before_import_restore")
    restored = preview.state
    restored["mode"] = mode
    restored["draft_id"] = draft_id
    restored["draft_session_id"] = draft_id
    return save_runtime_state(
        restored,
        event_type="state_restored_from_json",
        event_detail={"source": "imported_json"},
        root=root,
    )


def preview_runtime_state_import(
    payload: str | bytes,
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
) -> RuntimeImportPreview:
    try:
        text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        raw = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return RuntimeImportPreview(
            valid=False,
            summary={},
            warnings=(f"Invalid JSON import: {type(exc).__name__}",),
            state=None,
        )
    if not isinstance(raw, dict):
        return RuntimeImportPreview(
            valid=False,
            summary={},
            warnings=("Imported draft state must be a JSON object.",),
            state=None,
        )
    raw_schema = str(raw.get("schema_version") or "")
    state = normalize_runtime_state(raw, mode=mode, draft_id=draft_id)
    assignment_count = len(state["workflow_state"]["assignments"])
    trade_count = len(state["trade_events"])
    event_count = len(state["event_log"])
    warnings = [
        "Import preview only. Confirm restore before overwriting local runtime state.",
    ]
    if raw_schema and raw_schema != SCHEMA_VERSION:
        warnings.append(
            f"Schema will normalize to {SCHEMA_VERSION}; review before restoring."
        )
    return RuntimeImportPreview(
        valid=True,
        summary={
            "mode": str(state.get("mode") or mode),
            "draft_id": str(state.get("draft_id") or draft_id),
            "assignment_count": str(assignment_count),
            "trade_count": str(trade_count),
            "event_count": str(event_count),
            "updated_at": str(state.get("updated_at_utc") or state.get("updated_at") or ""),
        },
        warnings=tuple(warnings),
        state=state,
    )


def restore_runtime_state_from_json_if_confirmed(
    payload: str | bytes,
    *,
    mode: str,
    confirmed: bool,
    draft_id: str = DEFAULT_DRAFT_ID,
    current_state: RuntimeState | None = None,
    root: Path | None = None,
) -> RuntimeState:
    if not confirmed:
        return normalize_runtime_state(
            current_state or empty_runtime_state(mode=mode, draft_id=draft_id),
            mode=mode,
            draft_id=draft_id,
        )
    return restore_runtime_state_from_json(
        payload,
        mode=mode,
        draft_id=draft_id,
        current_state=current_state,
        root=root,
    )


def replay_runtime_state_from_event_log(
    events: list[dict[str, Any]],
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
) -> RuntimeState:
    replayed = empty_runtime_state(mode=mode, draft_id=draft_id)
    assignments: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("event_type") or "")
        detail = event.get("detail", {}) if isinstance(event.get("detail"), dict) else {}
        if event_type == "pick_assigned":
            assignment = _assignment_from_event_detail(detail)
            if assignment:
                assignments = [
                    row
                    for row in assignments
                    if row.get("overall_pick") != assignment.get("overall_pick")
                    and row.get("player_key") != assignment.get("player_key")
                ]
                assignments.append(assignment)
        elif event_type == "pick_removed":
            pick = _int_or_blank(detail.get("overall_pick"))
            assignments = [row for row in assignments if row.get("overall_pick") != pick]
        elif event_type == "pick_undone" and assignments:
            assignments = assignments[:-1]
        elif event_type == "trade_recorded":
            replayed = _append_trade_without_save(replayed, detail)
        elif event_type == "reset_confirmed":
            assignments = []
            replayed["trade_events"] = []
            replayed["pick_ownership_overrides"] = {}
        replayed["workflow_state"] = {"assignments": assignments}
        replayed["event_log"].append(deepcopy(event))
    return _sync_derived_state_fields(replayed)


def undo_last_trade_event(
    state: RuntimeState,
    *,
    root: Path | None = None,
) -> RuntimeState:
    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    trades = list(normalized.get("trade_events", []))
    if not trades:
        return save_runtime_state(
            normalized,
            event_type="trade_undo_noop",
            event_detail={"message": "No trade event to undo."},
            root=root,
        )
    removed = trades.pop()
    normalized["trade_events"] = trades
    normalized["pick_ownership_overrides"] = _ownership_overrides_from_trades(trades)
    return save_runtime_state(
        normalized,
        event_type="trade_undone",
        event_detail={
            "trade_id": str(removed.get("trade_id") or ""),
            "message": "Undid last trade event.",
        },
        root=root,
    )


def create_runtime_backup(
    state: RuntimeState,
    *,
    root: Path | None = None,
    reason: str = "manual",
) -> Path:
    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    normalized = _sync_derived_state_fields(normalized)
    paths = runtime_paths(root)
    paths.backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _safe_token(_now().replace("+00:00", "Z"))
    prefix = f"{_safe_token(str(normalized['draft_id']))}__{_safe_token(str(normalized['mode']))}"
    path = paths.backup_dir / f"{prefix}__{timestamp}__{_safe_token(reason)}.json"
    _write_json_atomic(path, normalized)
    return path


def normalize_runtime_state(
    raw: Any,
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
) -> RuntimeState:
    if not isinstance(raw, dict):
        return empty_runtime_state(mode=mode, draft_id=draft_id)
    created_at = str(
        raw.get("created_at") or raw.get("created_at_utc") or _now()
    )
    updated_at = str(
        raw.get("updated_at") or raw.get("updated_at_utc") or created_at
    )
    state = empty_runtime_state(
        mode=str(raw.get("mode") or mode),
        draft_id=str(raw.get("draft_session_id") or raw.get("draft_id") or draft_id),
        source_checkpoint=str(raw.get("source_checkpoint") or ""),
    )
    state["schema_version"] = SCHEMA_VERSION
    state["source_version"] = str(raw.get("source_version") or "")
    state["app_version"] = str(raw.get("app_version") or APP_VERSION)
    state["created_at"] = created_at
    state["updated_at"] = updated_at
    state["created_at_utc"] = created_at
    state["updated_at_utc"] = updated_at
    state["current_pick"] = raw.get("current_pick", "")
    state["workflow_state"] = _normalize_workflow_state(raw.get("workflow_state"))
    state["event_log"] = [
        event for event in raw.get("event_log", []) if isinstance(event, dict)
    ]
    state["pick_events"] = [
        event for event in raw.get("pick_events", []) if isinstance(event, dict)
    ]
    state["trade_events"] = [
        trade for trade in raw.get("trade_events", []) if isinstance(trade, dict)
    ]
    state["pick_ownership_overrides"] = (
        raw.get("pick_ownership_overrides")
        if isinstance(raw.get("pick_ownership_overrides"), dict)
        else {}
    )
    state["notes"] = [str(note) for note in raw.get("notes", []) if str(note).strip()]
    return _sync_derived_state_fields(state)


def apply_trade_events_to_pick_frame(
    pick_frame: pd.DataFrame,
    state: RuntimeState,
) -> pd.DataFrame:
    if pick_frame.empty:
        return pick_frame.copy()
    adjusted = pick_frame.copy()
    if "pick_label" not in adjusted.columns:
        return adjusted
    normalized_state = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    overrides = normalized_state.get("pick_ownership_overrides", {})
    if isinstance(overrides, dict) and "current_owner" in adjusted.columns:
        for pick_label, override in overrides.items():
            if not isinstance(override, dict):
                continue
            new_owner = str(override.get("new_owner") or "")
            if not new_owner:
                continue
            mask = adjusted["pick_label"].astype(str).eq(str(pick_label))
            adjusted.loc[mask, "current_owner"] = new_owner
            if "ownership_status" not in adjusted.columns:
                adjusted["ownership_status"] = ""
            adjusted.loc[mask, "ownership_status"] = "TRADE_OVERRIDE"
    for trade in normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )["trade_events"]:
        for change in trade.get("current_year_pick_changes", []):
            if not isinstance(change, dict):
                continue
            pick_label = str(change.get("pick_label") or "")
            new_owner = str(change.get("new_owner") or "")
            if not pick_label or not new_owner or "current_owner" not in adjusted.columns:
                continue
            mask = adjusted["pick_label"].astype(str).eq(pick_label)
            adjusted.loc[mask, "current_owner"] = new_owner
    return adjusted


def event_rows(state: RuntimeState) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for event in normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )["event_log"]:
        detail = event.get("detail", {}) if isinstance(event.get("detail"), dict) else {}
        rows.append(
            {
                "timestamp_utc": str(event.get("timestamp_utc") or ""),
                "event_type": str(event.get("event_type") or ""),
                "summary": event_summary(event),
                "player": str(detail.get("player") or ""),
                "pick": str(detail.get("pick_label") or detail.get("sends") or ""),
                "counterparty": str(detail.get("counterparty") or ""),
            }
        )
    return rows


def markdown_export(state: RuntimeState) -> str:
    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    lines = [
        f"# Draft Log Export - {normalized['mode']}",
        "",
        f"- Draft session ID: `{normalized['draft_session_id']}`",
        f"- Exported: `{_now()}`",
        f"- Source checkpoint: `{normalized.get('source_checkpoint', '')}`",
        "",
        "## Events",
        "",
    ]
    for event in normalized["event_log"]:
        lines.append(f"- `{event.get('timestamp_utc', '')}` {event_summary(event)}")
    lines.extend(["", "## Assignments", ""])
    for assignment in normalized["workflow_state"]["assignments"]:
        lines.append(
            f"- {assignment.get('pick_label', '')}: "
            f"{assignment.get('player', '')} ({assignment.get('position', '')})"
        )
    lines.extend(["", "## Trades", ""])
    for trade in normalized["trade_events"]:
        lines.append(
            f"- {trade.get('team_a', '')} sends {trade.get('team_a_sends', '')}; "
            f"{trade.get('team_b', '')} sends {trade.get('team_b_sends', '')}; "
            f"status {trade.get('status', '')}"
        )
    return "\n".join(lines) + "\n"


def event_summary(event: dict[str, Any]) -> str:
    event_type = str(event.get("event_type") or "")
    detail = event.get("detail", {}) if isinstance(event.get("detail"), dict) else {}
    if event_type == "pick_assigned":
        return f"Assigned {detail.get('player', 'player')} to {detail.get('pick_label', 'pick')}"
    if event_type == "pick_removed":
        return f"Removed assignment from {detail.get('pick_label', 'pick')}"
    if event_type == "pick_undone":
        return str(detail.get("message") or "Undid last pick")
    if event_type == "trade_recorded":
        return (
            f"Trade recorded: {detail.get('team_a', 'Team A')} sends "
            f"{detail.get('team_a_sends', '')}; {detail.get('team_b', 'Team B')} sends "
            f"{detail.get('team_b_sends', '')}"
        )
    if event_type == "manual_save":
        return "Draft state manually saved"
    if event_type == "backup_created":
        return "Draft state backup created"
    if event_type == "state_loaded":
        return "Latest draft state loaded"
    if event_type == "state_restored_from_json":
        return "Draft state restored from imported JSON"
    if event_type == "reset_confirmed":
        return "Draft runtime state reset"
    if event_type == "export_created":
        return "Draft log exported"
    return event_type.replace("_", " ").strip().title()


def build_event(event_type: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(uuid4()),
        "timestamp_utc": _now(),
        "event_type": event_type,
        "detail": deepcopy(detail),
    }


def current_year_pick_changes(
    *,
    sends: str,
    receives: str,
    counterparty: str,
) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for label in pick_label_mentions(sends):
        changes.append(
            {
                "pick_label": label,
                "new_owner": counterparty.strip() or "Trade Counterparty",
                "direction": "NWR sends",
            }
        )
    for label in pick_label_mentions(receives):
        changes.append(
            {
                "pick_label": label,
                "new_owner": "NWR",
                "direction": "NWR receives",
            }
        )
    return changes


def pick_label_mentions(text: str) -> list[str]:
    labels: list[str] = []
    for match in re.finditer(r"\b([1-9])\.(0?[1-9]|10|11|12)\b", text):
        round_number = int(match.group(1))
        round_pick = int(match.group(2))
        labels.append(f"{round_number}.{round_pick:02d}")
    return labels


def parse_trade_assets(text: str) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for token in _asset_tokens(text):
        asset = _parse_trade_asset_token(token)
        assets.append(asset)
    return assets


def future_pick_mentions(text: str) -> list[str]:
    return re.findall(r"\b20[2-9][0-9]\s+(?:1st|2nd|3rd|4th|5th|6th|7th)\b", text)


def build_pick_event(
    event: dict[str, Any],
    detail: dict[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    pick_label = str(detail.get("pick_label") or "")
    round_number, pick_in_round = _round_pick_from_label(pick_label)
    return {
        "event_id": str(event.get("event_id") or uuid4()),
        "timestamp": str(event.get("timestamp_utc") or _now()),
        "pick_number": _int_or_blank(detail.get("overall_pick")),
        "round": round_number,
        "pick_in_round": pick_in_round,
        "selecting_team": str(detail.get("selecting_team") or detail.get("pick_owner") or ""),
        "player_name": str(detail.get("player") or detail.get("player_name") or ""),
        "player_id": str(detail.get("player_id") or detail.get("player_key") or ""),
        "position": str(detail.get("position") or ""),
        "source": source,
        "notes": str(detail.get("notes") or ""),
    }


def _normalize_workflow_state(raw: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(raw, dict):
        return {"assignments": []}
    assignments = raw.get("assignments", [])
    if not isinstance(assignments, list):
        return {"assignments": []}
    clean = [dict(row) for row in assignments if isinstance(row, dict)]
    return {"assignments": clean}


def _sync_derived_state_fields(state: RuntimeState) -> RuntimeState:
    synced = deepcopy(state)
    assignments = synced.get("workflow_state", {}).get("assignments", [])
    if not isinstance(assignments, list):
        assignments = []
    synced["drafted_players"] = [
        {
            "player_name": str(row.get("player") or ""),
            "player_id": str(row.get("player_id") or row.get("player_key") or ""),
            "position": str(row.get("position") or ""),
            "pick_number": row.get("overall_pick", ""),
            "pick_label": str(row.get("pick_label") or ""),
        }
        for row in assignments
        if isinstance(row, dict)
    ]
    synced["drafted_player_ids"] = [
        str(row.get("player_id") or row.get("player_key") or "")
        for row in assignments
        if isinstance(row, dict) and str(row.get("player_id") or row.get("player_key") or "")
    ]
    synced["draft_session_id"] = str(
        synced.get("draft_session_id") or synced.get("draft_id") or DEFAULT_DRAFT_ID
    )
    synced["draft_id"] = synced["draft_session_id"]
    synced["schema_version"] = SCHEMA_VERSION
    synced["app_version"] = str(synced.get("app_version") or APP_VERSION)
    synced["pick_ownership_overrides"] = (
        synced.get("pick_ownership_overrides")
        if isinstance(synced.get("pick_ownership_overrides"), dict)
        else {}
    )
    return synced


def _mark_recovery_status(
    state: RuntimeState,
    *,
    status: str,
    warning: str,
    detail: dict[str, Any] | None = None,
) -> RuntimeState:
    marked = deepcopy(state)
    marked["runtime_load_status"] = status
    marked["runtime_recovery_required"] = status not in {"LOADED"}
    marked["runtime_load_warning"] = warning
    marked["runtime_load_detail"] = detail or {}
    return marked


def _assignment_from_event_detail(detail: dict[str, Any]) -> dict[str, Any] | None:
    player_name = str(detail.get("player") or detail.get("player_name") or "").strip()
    pick_label = str(detail.get("pick_label") or "").strip()
    overall_pick = _int_or_blank(detail.get("overall_pick"))
    if not player_name or overall_pick == "":
        return None
    return {
        "player_key": str(detail.get("player_key") or detail.get("player_id") or player_name),
        "overall_pick": overall_pick,
        "pick_label": pick_label,
        "pick_owner": str(detail.get("pick_owner") or detail.get("selecting_team") or ""),
        "player": player_name,
        "position": str(detail.get("position") or ""),
        "nfl_team": str(detail.get("nfl_team") or ""),
        "final_board_rank": str(detail.get("final_board_rank") or ""),
        "final_tier": str(detail.get("final_tier") or ""),
    }


def _append_trade_without_save(state: RuntimeState, trade: dict[str, Any]) -> RuntimeState:
    updated = deepcopy(state)
    updated.setdefault("trade_events", []).append(deepcopy(trade))
    updated["pick_ownership_overrides"] = _ownership_overrides_from_trades(
        updated.get("trade_events", [])
    )
    return updated


def _ownership_overrides_from_trades(trades: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    overrides: dict[str, dict[str, str]] = {}
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        trade_id = str(trade.get("trade_id") or "")
        source = str(trade.get("source") or "manual")
        status = str(trade.get("status") or "active")
        for change in trade.get("current_year_pick_changes", []):
            if not isinstance(change, dict):
                continue
            pick_label = str(change.get("pick_label") or "")
            new_owner = str(change.get("new_owner") or "")
            if not pick_label or not new_owner:
                continue
            overrides[pick_label] = {
                "new_owner": new_owner,
                "trade_id": trade_id,
                "source": source,
                "status": status,
            }
    return overrides


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(path)


def _asset_tokens(text: str) -> list[str]:
    return [
        token.strip()
        for token in re.split(r"[\n,;+]+", str(text or ""))
        if token.strip()
    ]


def _parse_trade_asset_token(token: str) -> dict[str, Any]:
    full_pick = re.fullmatch(
        r"(20[2-9][0-9])\s+([1-9])\.(0?[1-9]|10|11|12)",
        token.strip(),
        flags=re.IGNORECASE,
    )
    if full_pick:
        year = full_pick.group(1)
        round_number = int(full_pick.group(2))
        pick_in_round = int(full_pick.group(3))
        pick_label = f"{round_number}.{pick_in_round:02d}"
        return {
            "raw_text": token,
            "asset_type": "pick",
            "pick_year": year,
            "pick_label": pick_label,
            "display_label": f"{year} {pick_label}",
            "round": round_number,
            "pick_in_round": pick_in_round,
            "status": "parsed",
        }
    bare_pick = re.fullmatch(
        r"([1-9])\.(0?[1-9]|10|11|12)",
        token.strip(),
        flags=re.IGNORECASE,
    )
    if bare_pick:
        round_number = int(bare_pick.group(1))
        pick_in_round = int(bare_pick.group(2))
        pick_label = f"{round_number}.{pick_in_round:02d}"
        return {
            "raw_text": token,
            "asset_type": "pick",
            "pick_year": CURRENT_DRAFT_SEASON,
            "pick_label": pick_label,
            "display_label": f"{CURRENT_DRAFT_SEASON} {pick_label}",
            "round": round_number,
            "pick_in_round": pick_in_round,
            "status": "parsed",
        }
    future_pick = re.fullmatch(
        r"(20[2-9][0-9])\s+(1st|2nd|3rd|4th|5th|6th|7th)",
        token.strip(),
        flags=re.IGNORECASE,
    )
    if future_pick:
        year = future_pick.group(1)
        ordinal = future_pick.group(2).lower()
        return {
            "raw_text": token,
            "asset_type": "future_pick",
            "pick_year": year,
            "pick_label": f"{year} {ordinal}",
            "display_label": f"{year} {ordinal}",
            "round": _ordinal_round(ordinal),
            "pick_in_round": "",
            "status": "parsed",
        }
    return {
        "raw_text": token,
        "asset_type": "free_text",
        "pick_year": "",
        "pick_label": "",
        "display_label": token,
        "round": "",
        "pick_in_round": "",
        "status": "REVIEW_NEEDED",
    }


def _affected_pick(
    asset: dict[str, Any],
    *,
    new_owner: str,
    direction: str,
) -> dict[str, Any]:
    if asset.get("asset_type") not in {"pick", "future_pick"}:
        return {
            "raw_text": str(asset.get("raw_text") or ""),
            "new_owner": new_owner,
            "direction": direction,
            "status": "REVIEW_NEEDED",
            "can_update_board": False,
        }
    return {
        "raw_text": str(asset.get("raw_text") or ""),
        "pick_year": str(asset.get("pick_year") or ""),
        "pick_label": str(asset.get("pick_label") or ""),
        "display_label": str(asset.get("display_label") or asset.get("pick_label") or ""),
        "new_owner": new_owner,
        "direction": direction,
        "status": str(asset.get("status") or "parsed"),
        "can_update_board": asset.get("asset_type") == "pick"
        and str(asset.get("pick_year") or CURRENT_DRAFT_SEASON) == CURRENT_DRAFT_SEASON,
    }


def _pick_source(event_type: str) -> str:
    return {
        "pick_assigned": "manual",
        "pick_imported": "imported",
        "pick_restored": "restored",
    }.get(event_type, "manual")


def _round_pick_from_label(label: str) -> tuple[int | str, int | str]:
    match = re.fullmatch(r"([1-9])\.(0?[1-9]|10|11|12)", str(label or "").strip())
    if not match:
        return "", ""
    return int(match.group(1)), int(match.group(2))


def _ordinal_round(value: str) -> int | str:
    return {
        "1st": 1,
        "2nd": 2,
        "3rd": 3,
        "4th": 4,
        "5th": 5,
        "6th": 6,
        "7th": 7,
    }.get(value.lower(), "")


def _int_or_blank(value: object) -> int | str:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ""


def _safe_token(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())
    return cleaned.strip("_") or "draft"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
