from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATE_SCHEMA_VERSION = 1
STATE_PACKAGE_SCHEMA_VERSION = 1
DEFAULT_STATE_ROOT = Path(r"C:\NWR_SHARED_DATA\development_lab_state")
STATE_ROOT_ENV_VAR = "NWR_DEVELOPMENT_LAB_STATE_ROOT"

VALID_TOOL_KEYS: tuple[str, ...] = (
    "roster_weakness_tracker",
    "future_pick_planning",
    "upcoming_draft_prep",
    "keeper_deadline_prep",
    "drop_deadline_prep",
    "trade_deadline_prep",
)


@dataclass(frozen=True)
class DevelopmentLabToolState:
    tool_key: str
    payload: dict[str, str]
    status: str
    path: Path
    saved_at_utc: str = ""
    message: str = ""


@dataclass(frozen=True)
class DevelopmentLabStateWriteResult:
    tool_key: str
    status: str
    path: Path
    backup_path: Path | None = None
    message: str = ""


@dataclass(frozen=True)
class DevelopmentLabImportPreview:
    valid: bool
    tool_key: str = ""
    payload: dict[str, str] | None = None
    saved_at_utc: str = ""
    message: str = ""


@dataclass(frozen=True)
class DevelopmentLabStatePackagePreview:
    valid: bool
    payloads: dict[str, dict[str, str]]
    tool_keys: tuple[str, ...] = ()
    exported_at_utc: str = ""
    message: str = ""


@dataclass(frozen=True)
class DevelopmentLabStatePackageImportResult:
    status: str
    imported_tool_keys: tuple[str, ...]
    backup_paths: tuple[Path, ...] = ()
    message: str = ""


def development_lab_state_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    configured = os.getenv(STATE_ROOT_ENV_VAR)
    if configured:
        return Path(configured)
    return DEFAULT_STATE_ROOT


def load_tool_state(
    tool_key: str,
    *,
    root: str | Path | None = None,
) -> DevelopmentLabToolState:
    _validate_tool_key(tool_key)
    state_path = _tool_state_path(tool_key, root=root)
    if not state_path.exists():
        return DevelopmentLabToolState(
            tool_key=tool_key,
            payload={},
            status="MISSING",
            path=state_path,
            message="No saved local lab state.",
        )
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
        payload = _clean_payload(raw.get("payload", {}))
        saved_at = str(raw.get("saved_at_utc", "") or "")
        return DevelopmentLabToolState(
            tool_key=tool_key,
            payload=payload,
            status="LOADED",
            path=state_path,
            saved_at_utc=saved_at,
            message="Saved local lab state loaded.",
        )
    except Exception as exc:
        quarantine_path = _quarantine_corrupt_state(state_path)
        return DevelopmentLabToolState(
            tool_key=tool_key,
            payload={},
            status="CORRUPT_QUARANTINED",
            path=state_path,
            message=f"Corrupt local state was quarantined at {quarantine_path.name}: {exc}",
        )


def save_tool_state(
    tool_key: str,
    payload: dict[str, Any],
    *,
    root: str | Path | None = None,
) -> DevelopmentLabStateWriteResult:
    _validate_tool_key(tool_key)
    state_path = _tool_state_path(tool_key, root=root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = _backup_existing_state(state_path)
    document = _state_document(tool_key, payload)
    _atomic_write_json(state_path, document)
    return DevelopmentLabStateWriteResult(
        tool_key=tool_key,
        status="SAVED",
        path=state_path,
        backup_path=backup_path,
        message="Saved local Development Lab state.",
    )


def reset_tool_state(
    tool_key: str,
    *,
    confirmed: bool,
    root: str | Path | None = None,
) -> DevelopmentLabStateWriteResult:
    _validate_tool_key(tool_key)
    state_path = _tool_state_path(tool_key, root=root)
    if not confirmed:
        return DevelopmentLabStateWriteResult(
            tool_key=tool_key,
            status="BLOCKED_CONFIRMATION_REQUIRED",
            path=state_path,
            message="Reset blocked until explicitly confirmed.",
        )
    backup_path = _backup_existing_state(state_path)
    if state_path.exists():
        state_path.unlink()
    return DevelopmentLabStateWriteResult(
        tool_key=tool_key,
        status="RESET",
        path=state_path,
        backup_path=backup_path,
        message="Local Development Lab state reset.",
    )


def export_tool_state_json(tool_key: str, payload: dict[str, Any]) -> str:
    _validate_tool_key(tool_key)
    return json.dumps(_state_document(tool_key, payload), indent=2, sort_keys=True)


def export_all_tool_states_json(
    *,
    root: str | Path | None = None,
) -> str:
    states = list_saved_tool_states(root=root)
    document = {
        "schema_version": STATE_PACKAGE_SCHEMA_VERSION,
        "exported_at_utc": _timestamp(),
        "tool_keys": list(VALID_TOOL_KEYS),
        "states": {
            state.tool_key: {
                "status": state.status,
                "saved_at_utc": state.saved_at_utc,
                "payload": _clean_payload(state.payload),
                "guardrail": "local_lab_notes_only_not_model_input_not_source_truth",
            }
            for state in states
        },
        "guardrail": "bulk_local_lab_notes_only_not_model_input_not_source_truth",
    }
    return json.dumps(document, indent=2, sort_keys=True)


def preview_import_tool_state(raw_json: str | bytes) -> DevelopmentLabImportPreview:
    try:
        text = raw_json.decode("utf-8-sig") if isinstance(raw_json, bytes) else raw_json
        raw = json.loads(text)
    except Exception as exc:
        return DevelopmentLabImportPreview(valid=False, message=f"Invalid JSON: {exc}")
    tool_key = str(raw.get("tool_key", "") or "")
    if tool_key not in VALID_TOOL_KEYS:
        return DevelopmentLabImportPreview(
            valid=False,
            tool_key=tool_key,
            message="Import file has an unknown Development Lab tool key.",
        )
    payload = _clean_payload(raw.get("payload", {}))
    return DevelopmentLabImportPreview(
        valid=True,
        tool_key=tool_key,
        payload=payload,
        saved_at_utc=str(raw.get("saved_at_utc", "") or ""),
        message=f"Import preview ready for {tool_key}.",
    )


def import_tool_state(
    tool_key: str,
    raw_json: str | bytes,
    *,
    confirmed: bool,
    root: str | Path | None = None,
) -> DevelopmentLabStateWriteResult:
    _validate_tool_key(tool_key)
    preview = preview_import_tool_state(raw_json)
    state_path = _tool_state_path(tool_key, root=root)
    if not preview.valid or preview.payload is None:
        return DevelopmentLabStateWriteResult(
            tool_key=tool_key,
            status="IMPORT_BLOCKED_INVALID",
            path=state_path,
            message=preview.message,
        )
    if preview.tool_key != tool_key:
        return DevelopmentLabStateWriteResult(
            tool_key=tool_key,
            status="IMPORT_BLOCKED_TOOL_MISMATCH",
            path=state_path,
            message=(
                f"Import file is for {preview.tool_key}; current page is {tool_key}."
            ),
        )
    if not confirmed:
        return DevelopmentLabStateWriteResult(
            tool_key=tool_key,
            status="IMPORT_BLOCKED_CONFIRMATION_REQUIRED",
            path=state_path,
            message="Import preview shown. Confirm overwrite before importing.",
        )
    return save_tool_state(tool_key, preview.payload, root=root)


def preview_import_all_tool_states(
    raw_json: str | bytes,
) -> DevelopmentLabStatePackagePreview:
    try:
        text = raw_json.decode("utf-8-sig") if isinstance(raw_json, bytes) else raw_json
        raw = json.loads(text)
    except Exception as exc:
        return DevelopmentLabStatePackagePreview(
            valid=False,
            payloads={},
            message=f"Invalid JSON: {exc}",
        )
    if raw.get("schema_version") != STATE_PACKAGE_SCHEMA_VERSION:
        return DevelopmentLabStatePackagePreview(
            valid=False,
            payloads={},
            message="Import package has an unsupported Development Lab schema version.",
        )
    states = raw.get("states")
    if not isinstance(states, dict):
        return DevelopmentLabStatePackagePreview(
            valid=False,
            payloads={},
            message="Import package is missing Development Lab states.",
        )
    unknown = sorted(str(tool_key) for tool_key in states if tool_key not in VALID_TOOL_KEYS)
    if unknown:
        return DevelopmentLabStatePackagePreview(
            valid=False,
            payloads={},
            tool_keys=tuple(unknown),
            message="Import package has unknown Development Lab tool keys.",
        )
    missing = [tool_key for tool_key in VALID_TOOL_KEYS if tool_key not in states]
    if missing:
        return DevelopmentLabStatePackagePreview(
            valid=False,
            payloads={},
            tool_keys=tuple(missing),
            message="Import package is missing one or more Development Lab tool keys.",
        )
    payloads: dict[str, dict[str, str]] = {}
    for tool_key in VALID_TOOL_KEYS:
        state = states.get(tool_key)
        if not isinstance(state, dict):
            return DevelopmentLabStatePackagePreview(
                valid=False,
                payloads={},
                tool_keys=(tool_key,),
                message="Import package has an invalid Development Lab state entry.",
            )
        payloads[tool_key] = _clean_payload(state.get("payload", {}))
    return DevelopmentLabStatePackagePreview(
        valid=True,
        payloads=payloads,
        tool_keys=VALID_TOOL_KEYS,
        exported_at_utc=str(raw.get("exported_at_utc", "") or ""),
        message="Bulk import preview ready.",
    )


def import_all_tool_states(
    raw_json: str | bytes,
    *,
    confirmed: bool,
    root: str | Path | None = None,
) -> DevelopmentLabStatePackageImportResult:
    preview = preview_import_all_tool_states(raw_json)
    if not preview.valid:
        return DevelopmentLabStatePackageImportResult(
            status="IMPORT_BLOCKED_INVALID",
            imported_tool_keys=(),
            message=preview.message,
        )
    if not confirmed:
        return DevelopmentLabStatePackageImportResult(
            status="IMPORT_BLOCKED_CONFIRMATION_REQUIRED",
            imported_tool_keys=(),
            message="Import preview shown. Confirm overwrite before importing all lab notes.",
        )
    backup_paths: list[Path] = []
    imported: list[str] = []
    for tool_key in VALID_TOOL_KEYS:
        result = save_tool_state(tool_key, preview.payloads[tool_key], root=root)
        imported.append(tool_key)
        if result.backup_path:
            backup_paths.append(result.backup_path)
    return DevelopmentLabStatePackageImportResult(
        status="SAVED",
        imported_tool_keys=tuple(imported),
        backup_paths=tuple(backup_paths),
        message="Imported all local Development Lab manual notes.",
    )


def list_saved_tool_states(
    *,
    root: str | Path | None = None,
) -> list[DevelopmentLabToolState]:
    return [load_tool_state(tool_key, root=root) for tool_key in VALID_TOOL_KEYS]


def _state_document(tool_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "tool_key": tool_key,
        "saved_at_utc": _timestamp(),
        "payload": _clean_payload(payload),
        "guardrail": "local_lab_notes_only_not_model_input_not_source_truth",
    }


def _tool_state_path(tool_key: str, *, root: str | Path | None = None) -> Path:
    _validate_tool_key(tool_key)
    return development_lab_state_root(root) / f"{tool_key}.json"


def _validate_tool_key(tool_key: str) -> None:
    if tool_key not in VALID_TOOL_KEYS:
        raise ValueError(f"Unknown Development Lab tool key: {tool_key}")


def _clean_payload(payload: object) -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    cleaned: dict[str, str] = {}
    for key, value in payload.items():
        clean_key = str(key or "").strip()
        if not clean_key:
            continue
        cleaned[clean_key] = str(value or "")
    return cleaned


def _backup_existing_state(state_path: Path) -> Path | None:
    if not state_path.exists():
        return None
    backup_dir = state_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{state_path.stem}_{_timestamp_for_filename()}.json"
    shutil.copy2(state_path, backup_path)
    return backup_path


def _quarantine_corrupt_state(state_path: Path) -> Path:
    quarantine_dir = state_path.parent / "corrupt"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_path = quarantine_dir / f"{state_path.stem}_{_timestamp_for_filename()}.json"
    shutil.move(str(state_path), str(quarantine_path))
    return quarantine_path


def _atomic_write_json(path: Path, document: dict[str, Any]) -> None:
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _timestamp_for_filename() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
