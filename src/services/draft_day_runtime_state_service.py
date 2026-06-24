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
DEFAULT_RUNTIME_ROOT = Path(r"C:\NWR_SHARED_DATA\draft_day_runtime")
SCHEMA_VERSION = "draft_day_runtime_v1"


@dataclass(frozen=True)
class RuntimePaths:
    root: Path
    state_dir: Path
    export_dir: Path


def runtime_paths(root: Path | None = None) -> RuntimePaths:
    resolved_root = root or Path(
        os.environ.get("NWR_DRAFT_DAY_RUNTIME_ROOT", str(DEFAULT_RUNTIME_ROOT))
    )
    return RuntimePaths(
        root=resolved_root,
        state_dir=resolved_root / "state",
        export_dir=resolved_root / "exports",
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
    return {
        "schema_version": SCHEMA_VERSION,
        "draft_id": draft_id,
        "mode": mode,
        "source_checkpoint": source_checkpoint,
        "created_at_utc": _now(),
        "updated_at_utc": _now(),
        "workflow_state": {"assignments": []},
        "event_log": [],
        "trade_events": [],
    }


def load_runtime_state(
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
    source_checkpoint: str = "",
    root: Path | None = None,
) -> RuntimeState:
    path = runtime_state_path(mode=mode, draft_id=draft_id, root=root)
    if not path.exists():
        return empty_runtime_state(
            mode=mode,
            draft_id=draft_id,
            source_checkpoint=source_checkpoint,
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_runtime_state(
            mode=mode,
            draft_id=draft_id,
            source_checkpoint=source_checkpoint,
        )
    return normalize_runtime_state(raw, mode=mode, draft_id=draft_id)


def save_runtime_state(
    state: RuntimeState,
    *,
    event_type: str,
    event_detail: dict[str, Any] | None = None,
    root: Path | None = None,
) -> RuntimeState:
    normalized = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    event = build_event(event_type, event_detail or {})
    normalized["event_log"].append(event)
    normalized["updated_at_utc"] = _now()
    path = runtime_state_path(
        mode=str(normalized["mode"]),
        draft_id=str(normalized["draft_id"]),
        root=root,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")
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
    trade_type: str,
    counterparty: str,
    sends: str,
    receives: str,
    notes: str = "",
    root: Path | None = None,
) -> RuntimeState:
    updated = normalize_runtime_state(
        state,
        mode=str(state.get("mode") or "draft"),
        draft_id=str(state.get("draft_id") or DEFAULT_DRAFT_ID),
    )
    trade = {
        "trade_id": str(uuid4()),
        "recorded_at_utc": _now(),
        "trade_type": trade_type,
        "counterparty": counterparty.strip() or "Not enough information",
        "sends": sends.strip(),
        "receives": receives.strip(),
        "notes": notes.strip(),
        "current_year_pick_changes": current_year_pick_changes(
            sends=sends,
            receives=receives,
            counterparty=counterparty,
        ),
        "future_picks": future_pick_mentions(f"{sends} {receives}"),
        "guardrail_status": "display-only event; no trade calculator or model advice",
    }
    updated["trade_events"].append(trade)
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
    paths = runtime_paths(root)
    paths.export_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{_safe_token(str(normalized['draft_id']))}__{_safe_token(str(normalized['mode']))}"
    json_path = paths.export_dir / f"{prefix}_draft_log.json"
    csv_path = paths.export_dir / f"{prefix}_draft_log.csv"
    md_path = paths.export_dir / f"{prefix}_draft_log.md"

    json_path.write_text(json.dumps(normalized, indent=2, sort_keys=True), encoding="utf-8")
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


def normalize_runtime_state(
    raw: Any,
    *,
    mode: str,
    draft_id: str = DEFAULT_DRAFT_ID,
) -> RuntimeState:
    if not isinstance(raw, dict):
        return empty_runtime_state(mode=mode, draft_id=draft_id)
    state = empty_runtime_state(
        mode=str(raw.get("mode") or mode),
        draft_id=str(raw.get("draft_id") or draft_id),
        source_checkpoint=str(raw.get("source_checkpoint") or ""),
    )
    state["created_at_utc"] = str(raw.get("created_at_utc") or state["created_at_utc"])
    state["updated_at_utc"] = str(raw.get("updated_at_utc") or state["updated_at_utc"])
    state["workflow_state"] = _normalize_workflow_state(raw.get("workflow_state"))
    state["event_log"] = [
        event for event in raw.get("event_log", []) if isinstance(event, dict)
    ]
    state["trade_events"] = [
        trade for trade in raw.get("trade_events", []) if isinstance(trade, dict)
    ]
    return state


def apply_trade_events_to_pick_frame(
    pick_frame: pd.DataFrame,
    state: RuntimeState,
) -> pd.DataFrame:
    if pick_frame.empty:
        return pick_frame.copy()
    adjusted = pick_frame.copy()
    if "pick_label" not in adjusted.columns:
        return adjusted
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
        f"- Draft ID: `{normalized['draft_id']}`",
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
            f"- {trade.get('trade_type', '')}: send {trade.get('sends', '')}; "
            f"receive {trade.get('receives', '')}; counterparty {trade.get('counterparty', '')}"
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
            f"Trade recorded: send {detail.get('sends', '')}; "
            f"receive {detail.get('receives', '')}"
        )
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


def future_pick_mentions(text: str) -> list[str]:
    return re.findall(r"\b20[2-9][0-9]\s+(?:1st|2nd|3rd|4th|5th|6th|7th)\b", text)


def _normalize_workflow_state(raw: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(raw, dict):
        return {"assignments": []}
    assignments = raw.get("assignments", [])
    if not isinstance(assignments, list):
        return {"assignments": []}
    clean = [dict(row) for row in assignments if isinstance(row, dict)]
    return {"assignments": clean}


def _safe_token(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())
    return cleaned.strip("_") or "draft"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
