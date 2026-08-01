"""Governed local persistence for the NWR Personal Workspace."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1
WORKSPACE_ENV_VAR = "NWR_PERSONAL_WORKSPACE_ROOT"
DEFAULT_WORKSPACE_ROOT = Path(r"C:\NWR_SHARED_DATA\nwr_personal_workspace_v1")
STORE_NAMES = ("personal_board", "decision_journal", "saved_scenarios", "preferences")
DECISION_TYPES = {
    "trade considered",
    "trade accepted externally",
    "trade rejected externally",
    "trade counter considered",
    "draft selection",
    "draft target",
    "draft pass",
    "roster cut",
    "roster add",
    "waiver target",
    "player evaluation",
    "personal-board change",
    "custom note",
}
DECISION_STATUSES = {
    "Draft",
    "Considered",
    "Decided",
    "Completed Externally",
    "Cancelled",
    "Archived",
}
SCENARIO_TYPES = {"trading_lab", "player_compare", "draft", "asset_explorer"}
TEAM_WINDOWS = {"Contending", "Balanced", "Rebuilding", "Custom/Unspecified"}
PROHIBITED_SECRET_KEYS = {
    "password",
    "credential",
    "api_key",
    "token",
    "secret",
    "payment",
    "email",
}
PROHIBITED_RECOMMENDATION_KEYS = {
    "winner",
    "loser",
    "accept",
    "reject",
    "fair",
    "unfair",
    "automatic_counteroffer",
    "combined_score",
    "verdict",
}


class WorkspaceValidationError(ValueError):
    pass


class WorkspaceCorruptionError(WorkspaceValidationError):
    pass


class WorkspaceLockError(WorkspaceValidationError):
    pass


@dataclass(frozen=True)
class WorkspaceStore:
    name: str
    status: str
    records: tuple[dict[str, Any], ...]
    updated_at_utc: str = ""
    message: str = ""


@dataclass(frozen=True)
class WorkspaceWriteResult:
    status: str
    store: str
    record_id: str
    backup_path: Path | None = None
    message: str = ""


@dataclass(frozen=True)
class WorkspaceBackupResult:
    status: str
    path: Path | None
    file_count: int
    manifest_sha256: str = ""
    message: str = ""


@dataclass(frozen=True)
class WorkspaceRestorePreview:
    valid: bool
    backup_path: Path
    file_count: int
    message: str


@dataclass(frozen=True)
class WorkspaceMigrationResult:
    status: str
    from_version: int
    to_version: int
    backup_path: Path | None
    receipt_path: Path | None
    message: str


def workspace_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    configured = os.getenv(WORKSPACE_ENV_VAR)
    return Path(configured) if configured else DEFAULT_WORKSPACE_ROOT


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def load_store(name: str, *, root: str | Path | None = None) -> WorkspaceStore:
    _validate_store_name(name)
    path = workspace_root(root) / "stores" / f"{name}.json"
    if not path.exists():
        return WorkspaceStore(name, "MISSING", (), message="No local workspace data saved.")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
        _validate_envelope(envelope, expected_store=name)
    except (OSError, json.JSONDecodeError, WorkspaceValidationError) as exc:
        return WorkspaceStore(name, "CORRUPT", (), message=str(exc))
    records = envelope["payload"]["records"]
    return WorkspaceStore(
        name,
        "LOADED",
        tuple(_copy_record(row) for row in records),
        str(envelope.get("updated_at_utc", "")),
        "Local workspace data loaded.",
    )


def save_personal_entry(
    entry: Mapping[str, Any],
    *,
    asset_registry: Mapping[str, str],
    root: str | Path | None = None,
    now_utc: str | None = None,
) -> WorkspaceWriteResult:
    cleaned = _validate_personal_entry(entry, asset_registry=asset_registry)
    store = load_store("personal_board", root=root)
    if store.status == "CORRUPT":
        raise WorkspaceCorruptionError(store.message)
    existing = {str(row["asset_id"]): row for row in store.records}
    previous = existing.get(cleaned["asset_id"])
    timestamp = now_utc or _timestamp()
    cleaned["created_at_utc"] = (
        str(previous.get("created_at_utc", timestamp)) if previous else timestamp
    )
    cleaned["modified_at_utc"] = timestamp
    existing[cleaned["asset_id"]] = cleaned
    backup = _write_records("personal_board", existing.values(), root=root, now_utc=timestamp)
    return WorkspaceWriteResult("SAVED", "personal_board", cleaned["asset_id"], backup)


def import_personal_board(
    raw_json: str | bytes,
    *,
    asset_registry: Mapping[str, str],
    confirmed: bool,
    root: str | Path | None = None,
) -> WorkspaceWriteResult:
    if not confirmed:
        return WorkspaceWriteResult(
            "BLOCKED_CONFIRMATION_REQUIRED", "personal_board", "", message="Confirm import."
        )
    value = _parse_json(raw_json)
    if value.get("schema_version") != SCHEMA_VERSION or value.get("store") != "personal_board":
        raise WorkspaceValidationError("Unsupported Personal Board import schema.")
    rows = value.get("records")
    if not isinstance(rows, list):
        raise WorkspaceValidationError("Personal Board import requires records.")
    cleaned = [_validate_personal_entry(row, asset_registry=asset_registry) for row in rows]
    ids = [row["asset_id"] for row in cleaned]
    if len(ids) != len(set(ids)):
        raise WorkspaceValidationError("Duplicate Personal Board asset ID.")
    backup = _write_records("personal_board", cleaned, root=root)
    return WorkspaceWriteResult("IMPORTED", "personal_board", "", backup)


def export_personal_board(*, root: str | Path | None = None) -> str:
    store = load_store("personal_board", root=root)
    if store.status == "CORRUPT":
        raise WorkspaceCorruptionError(store.message)
    value = {
        "schema_version": SCHEMA_VERSION,
        "store": "personal_board",
        "records": list(store.records),
    }
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def create_decision(
    decision: Mapping[str, Any],
    *,
    asset_registry: Mapping[str, str],
    root: str | Path | None = None,
    now_utc: str | None = None,
) -> WorkspaceWriteResult:
    cleaned = _validate_decision(decision, asset_registry=asset_registry)
    store = load_store("decision_journal", root=root)
    if store.status == "CORRUPT":
        raise WorkspaceCorruptionError(store.message)
    ids = {str(row["decision_id"]) for row in store.records}
    if cleaned["decision_id"] in ids:
        raise WorkspaceValidationError("Duplicate decision ID.")
    timestamp = now_utc or _timestamp()
    cleaned["created_at_utc"] = timestamp
    cleaned["modified_at_utc"] = timestamp
    backup = _write_records(
        "decision_journal", (*store.records, cleaned), root=root, now_utc=timestamp
    )
    return WorkspaceWriteResult("SAVED", "decision_journal", cleaned["decision_id"], backup)


def update_decision(
    decision_id: str,
    updates: Mapping[str, Any],
    *,
    root: str | Path | None = None,
    now_utc: str | None = None,
) -> WorkspaceWriteResult:
    store = load_store("decision_journal", root=root)
    if store.status != "LOADED":
        raise WorkspaceValidationError("Decision Journal is unavailable.")
    records = [dict(row) for row in store.records]
    target = next((row for row in records if row["decision_id"] == decision_id), None)
    if target is None:
        raise WorkspaceValidationError("Unknown decision ID.")
    forbidden = {"decision_id", "created_at_utc", "source_snapshot", "assets"} & set(updates)
    if forbidden:
        raise WorkspaceValidationError("Decision-time source snapshot is immutable.")
    _reject_sensitive(updates)
    allowed = {
        "status",
        "follow_up_date",
        "retrospective_notes",
        "rationale",
        "expected_outcome",
        "confidence",
        "archived",
    }
    unknown = set(updates) - allowed
    if unknown:
        raise WorkspaceValidationError(f"Unknown decision update fields: {sorted(unknown)}")
    if "status" in updates and updates["status"] not in DECISION_STATUSES:
        raise WorkspaceValidationError("Unsupported decision status.")
    target.update(_copy_record(updates))
    target["modified_at_utc"] = now_utc or _timestamp()
    backup = _write_records("decision_journal", records, root=root)
    return WorkspaceWriteResult("UPDATED", "decision_journal", decision_id, backup)


def archive_decision(
    decision_id: str, *, confirmed: bool, root: str | Path | None = None
) -> WorkspaceWriteResult:
    if not confirmed:
        return WorkspaceWriteResult(
            "BLOCKED_CONFIRMATION_REQUIRED", "decision_journal", decision_id
        )
    return update_decision(decision_id, {"status": "Archived", "archived": True}, root=root)


def save_scenario(
    scenario: Mapping[str, Any],
    *,
    asset_registry: Mapping[str, str],
    root: str | Path | None = None,
    now_utc: str | None = None,
) -> WorkspaceWriteResult:
    cleaned = _validate_scenario(scenario, asset_registry=asset_registry)
    store = load_store("saved_scenarios", root=root)
    if store.status == "CORRUPT":
        raise WorkspaceCorruptionError(store.message)
    records = {str(row["scenario_id"]): dict(row) for row in store.records}
    timestamp = now_utc or _timestamp()
    old = records.get(cleaned["scenario_id"])
    cleaned["created_at_utc"] = str(old.get("created_at_utc", timestamp)) if old else timestamp
    cleaned["modified_at_utc"] = timestamp
    records[cleaned["scenario_id"]] = cleaned
    backup = _write_records("saved_scenarios", records.values(), root=root, now_utc=timestamp)
    return WorkspaceWriteResult("SAVED", "saved_scenarios", cleaned["scenario_id"], backup)


def create_workspace_backup(
    *, root: str | Path | None = None, now_utc: str | None = None
) -> WorkspaceBackupResult:
    base = workspace_root(root)
    timestamp = (now_utc or _timestamp()).replace(":", "").replace("-", "")
    target = base / "backups" / f"workspace-{timestamp}"
    stores = base / "stores"
    target.mkdir(parents=True, exist_ok=False)
    inventory: list[dict[str, Any]] = []
    for path in sorted(stores.glob("*.json")) if stores.exists() else ():
        body = path.read_bytes()
        destination = target / path.name
        destination.write_bytes(body)
        inventory.append(
            {"path": path.name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
        )
    manifest = {"schema_version": 1, "created_at_utc": now_utc or _timestamp(), "files": inventory}
    manifest_body = canonical_json_bytes(manifest)
    (target / "manifest.json").write_bytes(manifest_body)
    return WorkspaceBackupResult(
        "CREATED", target, len(inventory), hashlib.sha256(manifest_body).hexdigest()
    )


def preview_workspace_restore(path: str | Path) -> WorkspaceRestorePreview:
    backup = Path(path)
    try:
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        files = manifest["files"]
        if not isinstance(files, list):
            raise WorkspaceValidationError("Backup inventory is invalid.")
        for row in files:
            name = str(row["path"])
            if Path(name).name != name or not name.endswith(".json"):
                raise WorkspaceValidationError("Unsafe backup path.")
            body = (backup / name).read_bytes()
            if len(body) != int(row["bytes"]) or hashlib.sha256(body).hexdigest() != row["sha256"]:
                raise WorkspaceCorruptionError("Backup checksum mismatch.")
            envelope = json.loads(body)
            _validate_envelope(envelope, expected_store=name.removesuffix(".json"))
    except (OSError, KeyError, json.JSONDecodeError, WorkspaceValidationError) as exc:
        return WorkspaceRestorePreview(False, backup, 0, str(exc))
    return WorkspaceRestorePreview(True, backup, len(files), "Restore dry-run passed.")


def restore_workspace(
    path: str | Path,
    *,
    confirmed: bool,
    root: str | Path | None = None,
) -> WorkspaceBackupResult:
    preview = preview_workspace_restore(path)
    if not preview.valid:
        return WorkspaceBackupResult("BLOCKED_CORRUPT", None, 0, message=preview.message)
    if not confirmed:
        return WorkspaceBackupResult("BLOCKED_CONFIRMATION_REQUIRED", None, preview.file_count)
    base = workspace_root(root)
    safety = create_workspace_backup(root=base)
    stores = base / "stores"
    staged = base / f".restore-{uuid4().hex}"
    staged.mkdir(parents=True)
    try:
        for source in sorted(Path(path).glob("*.json")):
            if source.name == "manifest.json":
                continue
            shutil.copy2(source, staged / source.name)
        stores.mkdir(parents=True, exist_ok=True)
        for source in sorted(staged.glob("*.json")):
            os.replace(source, stores / source.name)
    except Exception:
        _restore_backup_direct(safety.path, base)
        raise
    finally:
        shutil.rmtree(staged, ignore_errors=True)
    return WorkspaceBackupResult("RESTORED", safety.path, preview.file_count)


def migrate_workspace(
    *, root: str | Path | None = None, fail_after_backup: bool = False
) -> WorkspaceMigrationResult:
    base = workspace_root(root)
    version_path = base / "workspace_schema.json"
    current = 0
    if version_path.exists():
        try:
            current = int(json.loads(version_path.read_text(encoding="utf-8"))["schema_version"])
        except Exception as exc:
            return WorkspaceMigrationResult(
                "BLOCKED_CORRUPT", 0, SCHEMA_VERSION, None, None, str(exc)
            )
    if current > SCHEMA_VERSION:
        return WorkspaceMigrationResult(
            "BLOCKED_FUTURE_VERSION",
            current,
            SCHEMA_VERSION,
            None,
            None,
            "Future schema is not writable.",
        )
    backup = create_workspace_backup(root=base)
    if backup.path is None or not preview_workspace_restore(backup.path).valid:
        return WorkspaceMigrationResult(
            "BLOCKED_BACKUP",
            current,
            SCHEMA_VERSION,
            backup.path,
            None,
            "Verified backup required.",
        )
    try:
        if fail_after_backup:
            raise RuntimeError("injected migration failure")
        base.mkdir(parents=True, exist_ok=True)
        _atomic_write(version_path, canonical_json_bytes({"schema_version": SCHEMA_VERSION}))
        receipt = (
            base / "migration_receipts" / f"v{current}-to-v{SCHEMA_VERSION}-{uuid4().hex}.json"
        )
        receipt.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(
            receipt,
            canonical_json_bytes(
                {
                    "from_version": current,
                    "to_version": SCHEMA_VERSION,
                    "backup": str(backup.path),
                    "status": "COMPLETED",
                }
            ),
        )
    except Exception as exc:
        if version_path.exists():
            version_path.unlink()
        return WorkspaceMigrationResult(
            "ROLLED_BACK", current, SCHEMA_VERSION, backup.path, None, str(exc)
        )
    return WorkspaceMigrationResult(
        "MIGRATED", current, SCHEMA_VERSION, backup.path, receipt, "Additive migration completed."
    )


def summarize_workspace(*, root: str | Path | None = None) -> dict[str, int]:
    personal = load_store("personal_board", root=root).records
    decisions = load_store("decision_journal", root=root).records
    scenarios = load_store("saved_scenarios", root=root).records
    return {
        "personal_entries": len(personal),
        "watchlist": sum(bool(row.get("watchlist")) for row in personal),
        "targets": sum(bool(row.get("target")) for row in personal),
        "avoid": sum(bool(row.get("avoid")) for row in personal),
        "open_decisions": sum(
            row.get("status") not in {"Archived", "Cancelled"} for row in decisions
        ),
        "saved_scenarios": len(scenarios),
    }


def _validate_personal_entry(
    entry: Mapping[str, Any], *, asset_registry: Mapping[str, str]
) -> dict[str, Any]:
    if not isinstance(entry, Mapping):
        raise WorkspaceValidationError("Personal Board entry must be an object.")
    required = {"asset_id", "asset_type", "source_authority_version"}
    missing = required - set(entry)
    if missing:
        raise WorkspaceValidationError(f"Missing Personal Board fields: {sorted(missing)}")
    asset_id = str(entry["asset_id"])
    asset_type = str(entry["asset_type"])
    if asset_id not in asset_registry:
        raise WorkspaceValidationError("Unknown asset ID remains blocked.")
    if asset_registry[asset_id] != asset_type:
        raise WorkspaceValidationError("Asset source type mismatch.")
    _reject_sensitive(entry)
    known = {
        "asset_id",
        "asset_type",
        "source_authority_version",
        "my_tier",
        "my_rank",
        "watchlist",
        "target",
        "avoid",
        "sleeper",
        "sell_high",
        "buy_low",
        "tags",
        "notes",
        "conviction",
        "team_window",
        "created_at_utc",
        "modified_at_utc",
        "extensions",
    }
    cleaned = {key: _copy_value(value) for key, value in entry.items() if key in known}
    extensions = (
        dict(entry.get("extensions", {})) if isinstance(entry.get("extensions"), Mapping) else {}
    )
    extensions.update({key: _copy_value(value) for key, value in entry.items() if key not in known})
    cleaned["extensions"] = extensions
    if cleaned.get("team_window", "Custom/Unspecified") not in TEAM_WINDOWS:
        raise WorkspaceValidationError("Unsupported team-window label.")
    rank = cleaned.get("my_rank")
    if rank not in (None, "") and (isinstance(rank, bool) or int(rank) < 1):
        raise WorkspaceValidationError("My Rank must be a positive ordinal.")
    cleaned["asset_id"] = asset_id
    cleaned["asset_type"] = asset_type
    return cleaned


def _validate_decision(
    decision: Mapping[str, Any], *, asset_registry: Mapping[str, str]
) -> dict[str, Any]:
    required = {"decision_id", "decision_type", "status", "assets", "source_snapshot", "rationale"}
    if required - set(decision):
        raise WorkspaceValidationError("Decision receipt is missing required fields.")
    _reject_sensitive(decision)
    if (
        decision["decision_type"] not in DECISION_TYPES
        or decision["status"] not in DECISION_STATUSES
    ):
        raise WorkspaceValidationError("Unsupported decision type or status.")
    assets = decision["assets"]
    if not isinstance(assets, list) or len(assets) != len(set(map(str, assets))):
        raise WorkspaceValidationError("Decision assets must be unique asset IDs.")
    if any(str(asset) not in asset_registry for asset in assets):
        raise WorkspaceValidationError("Decision contains an unknown asset.")
    snapshot = decision["source_snapshot"]
    if not isinstance(snapshot, Mapping):
        raise WorkspaceValidationError("Decision-time source snapshot is required.")
    _reject_recommendations(snapshot)
    return _copy_record(decision)


def _validate_scenario(
    scenario: Mapping[str, Any], *, asset_registry: Mapping[str, str]
) -> dict[str, Any]:
    required = {"scenario_id", "scenario_type", "title", "assets", "source_versions", "payload"}
    if required - set(scenario):
        raise WorkspaceValidationError("Saved scenario is missing required fields.")
    if scenario["scenario_type"] not in SCENARIO_TYPES:
        raise WorkspaceValidationError("Unsupported saved scenario type.")
    _reject_sensitive(scenario)
    _reject_recommendations(scenario)
    assets = scenario["assets"]
    if not isinstance(assets, list) or any(str(asset) not in asset_registry for asset in assets):
        raise WorkspaceValidationError("Scenario contains an unknown asset.")
    return _copy_record(scenario)


def _write_records(
    name: str, records: Any, *, root: str | Path | None, now_utc: str | None = None
) -> Path | None:
    base = workspace_root(root)
    path = base / "stores" / f"{name}.json"
    clean = sorted((_copy_record(row) for row in records), key=lambda row: _record_id(name, row))
    payload = {"records": clean}
    timestamp = now_utc or _timestamp()
    body_without_checksum = {
        "schema_version": SCHEMA_VERSION,
        "store": name,
        "updated_at_utc": timestamp,
        "payload": payload,
    }
    envelope = {
        **body_without_checksum,
        "sha256": hashlib.sha256(canonical_json_bytes(body_without_checksum)).hexdigest(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with _exclusive_lock(base):
        backup = _backup_file(path, base, timestamp)
        _atomic_write(path, canonical_json_bytes(envelope))
        verify = load_store(name, root=base)
        if verify.status != "LOADED":
            if backup:
                shutil.copy2(backup, path)
            else:
                path.unlink(missing_ok=True)
            raise WorkspaceCorruptionError(
                "Post-write verification failed; previous state restored."
            )
    return backup


def _validate_envelope(value: Any, *, expected_store: str) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise WorkspaceCorruptionError("Unsupported or corrupt workspace schema.")
    if value.get("store") != expected_store:
        raise WorkspaceCorruptionError("Workspace store identity mismatch.")
    payload = value.get("payload")
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise WorkspaceCorruptionError("Workspace payload is invalid.")
    without = {key: value[key] for key in ("schema_version", "store", "updated_at_utc", "payload")}
    expected = hashlib.sha256(canonical_json_bytes(without)).hexdigest()
    if value.get("sha256") != expected:
        raise WorkspaceCorruptionError("Workspace checksum mismatch.")


@contextmanager
def _exclusive_lock(base: Path) -> Iterator[None]:
    lock = base / ".workspace.lock"
    base.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise WorkspaceLockError("Another workspace writer is active.") from exc
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        yield
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
        lock.unlink(missing_ok=True)


def _backup_file(path: Path, base: Path, timestamp: str) -> Path | None:
    if not path.exists():
        return None
    target = base / "backups" / "before-write" / timestamp.replace(":", "") / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    if target.read_bytes() != path.read_bytes():
        raise WorkspaceCorruptionError("Backup verification failed.")
    return target


def _atomic_write(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _restore_backup_direct(path: Path | None, base: Path) -> None:
    if path is None:
        return
    stores = base / "stores"
    stores.mkdir(parents=True, exist_ok=True)
    for source in Path(path).glob("*.json"):
        shutil.copy2(source, stores / source.name)


def _parse_json(raw: str | bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkspaceValidationError("Import is not valid JSON.") from exc
    if not isinstance(value, dict):
        raise WorkspaceValidationError("Import root must be an object.")
    return value


def _reject_sensitive(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if any(secret in normalized for secret in PROHIBITED_SECRET_KEYS):
                raise WorkspaceValidationError("Sensitive credential-like fields are prohibited.")
            _reject_sensitive(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_sensitive(nested)


def _reject_recommendations(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).casefold() in PROHIBITED_RECOMMENDATION_KEYS:
                raise WorkspaceValidationError("Automatic recommendation fields are prohibited.")
            _reject_recommendations(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_recommendations(nested)


def _record_id(name: str, row: Mapping[str, Any]) -> str:
    key = {
        "personal_board": "asset_id",
        "decision_journal": "decision_id",
        "saved_scenarios": "scenario_id",
        "preferences": "preference_id",
    }[name]
    return str(row[key])


def _validate_store_name(name: str) -> None:
    if name not in STORE_NAMES:
        raise WorkspaceValidationError("Unknown workspace store.")


def _copy_record(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): _copy_value(nested) for key, nested in value.items()}


def _copy_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _copy_record(value)
    if isinstance(value, (list, tuple)):
        return [_copy_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise WorkspaceValidationError(f"Unsupported workspace value type: {type(value).__name__}")


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
