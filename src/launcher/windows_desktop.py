from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.streamlit_runtime_cycle import (
    build_streamlit_command,
    fatal_markers_in_logs,
    graceful_shutdown,
    port_is_listening,
    start_streamlit,
    wait_for_http,
    wait_for_port_release,
)
from src.services.refresh_receipt_store_service import inspect_refresh_receipt

LAUNCHER_VERSION = "nwr_windows_desktop_launcher_v1"
EXPECTED_APP_COMMIT = "dc399a8c2ed5d77d9802d98c215a12cbe594d7d7"
EXPECTED_APP_TREE = "e6f98339bf7172b45b78d94dfed390559856f899"
HOST = "127.0.0.1"
PORT = 8520
BACKUP_RETENTION = 5
STARTUP_TIMEOUT_SECONDS = 30.0
SHUTDOWN_TIMEOUT_SECONDS = 15.0


class LauncherError(RuntimeError):
    pass


@dataclass(frozen=True)
class LauncherPaths:
    repo_root: Path
    data_home: Path
    draft_root: Path
    development_lab_root: Path
    mock_draft_root: Path
    refresh_root: Path
    backup_root: Path
    logs_root: Path
    run_root: Path
    browser_profile: Path
    config_root: Path

    @property
    def lock_path(self) -> Path:
        return self.run_root / "launcher.lock.json"

    @property
    def stop_request(self) -> Path:
        return self.run_root / "stop.request"

    @property
    def last_backup_result(self) -> Path:
        return self.run_root / "last_backup.json"


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    status: str
    files: tuple[Path, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class MigrationResult:
    status: str
    source: Path | None = None
    files: int = 0
    detail: str = ""


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def local_app_data() -> Path:
    configured = os.environ.get("NWR_DATA_HOME", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    value = os.environ.get("LOCALAPPDATA", "").strip()
    if not value:
        raise LauncherError("LOCALAPPDATA is unavailable; per-user data identity is unresolved.")
    return Path(value).resolve() / "NinersWarRoom"


def launcher_paths(repo_root: Path | None = None) -> LauncherPaths:
    repo = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    home = local_app_data()
    shared = Path(os.environ.get("NWR_SHARED_DATA_ROOT", r"C:\NWR_SHARED_DATA"))
    draft = Path(
        os.environ.get(
            "NWR_DRAFT_DAY_RUNTIME_ROOT",
            str(
                shared / "draft_runtime_state"
                if (shared / "draft_runtime_state").exists()
                else home / "data" / "draft_runtime_state"
            ),
        )
    ).resolve()
    lab = Path(
        os.environ.get(
            "NWR_DEVELOPMENT_LAB_STATE_ROOT",
            str(
                shared / "development_lab_state"
                if (shared / "development_lab_state").exists()
                else home / "data" / "development_lab_state"
            ),
        )
    ).resolve()
    return LauncherPaths(
        repo_root=repo,
        data_home=home,
        draft_root=draft,
        development_lab_root=lab,
        mock_draft_root=Path(
            os.environ.get("NWR_MOCK_DRAFT_ROOT", str(home / "data" / "mock_drafts"))
        ).resolve(),
        refresh_root=Path(
            os.environ.get("NWR_REFRESH_DATA_ROOT", str(home / "data" / "refresh_data"))
        ).resolve(),
        backup_root=home / "backups",
        logs_root=home / "logs",
        run_root=home / "run",
        browser_profile=home / "browser-profile",
        config_root=home / "config",
    )


def ensure_directories(paths: LauncherPaths) -> None:
    for path in (
        paths.data_home,
        paths.draft_root,
        paths.development_lab_root,
        paths.mock_draft_root,
        paths.refresh_root,
        paths.backup_root,
        paths.logs_root,
        paths.run_root,
        paths.browser_profile,
        paths.config_root,
    ):
        path.mkdir(parents=True, exist_ok=True)


def legacy_refresh_root(paths: LauncherPaths) -> Path | None:
    configured = os.environ.get("NWR_LEGACY_REFRESH_ROOT", "").strip()
    if configured:
        return Path(configured).resolve()
    canonical = Path(r"C:\NWR\Niners-War-Room\local_exports\refresh_data")
    if canonical.exists() and canonical.resolve() != paths.refresh_root.resolve():
        return canonical.resolve()
    return None


def migrate_legacy_refresh(paths: LauncherPaths) -> MigrationResult:
    source_root = legacy_refresh_root(paths)
    if source_root is None:
        return MigrationResult("NO_LEGACY_STATE")
    source_latest = source_root / "latest_refresh_status.json"
    if not source_latest.exists():
        return MigrationResult("NO_LEGACY_STATE", source=source_root)
    target_latest = paths.refresh_root / "latest_refresh_status.json"
    source_validation = inspect_refresh_receipt(status_path=source_latest)
    if not source_validation.has_valid_latest:
        return MigrationResult(
            "BLOCKED_INVALID_LEGACY_STATE",
            source=source_root,
            detail=f"Accepted receipt validator returned {source_validation.load_status}.",
        )
    if target_latest.exists():
        target_validation = inspect_refresh_receipt(status_path=target_latest)
        if not target_validation.has_valid_latest:
            return MigrationResult(
                "BLOCKED_INVALID_TARGET_STATE",
                source=source_root,
                detail=f"Target receipt validator returned {target_validation.load_status}.",
            )
        if sha256(source_latest) != sha256(target_latest):
            return MigrationResult(
                "BLOCKED_NWR_DESKTOP_LAUNCHER_STATE_MIGRATION_CONFLICT",
                source=source_root,
                detail="Legacy and stable roots contain different valid receipts.",
            )
        return MigrationResult("ALREADY_MIGRATED", source=source_root, files=1)

    source_files = [source_latest]
    source_backup = source_root / "backups" / "latest_refresh_status.backup.json"
    if source_backup.exists() and source_validation.has_valid_backup:
        source_files.append(source_backup)
    migration_id = f"{utc_timestamp()}__legacy_refresh_source"
    backup_staging = paths.backup_root / f".{migration_id}.staging"
    backup_final = paths.backup_root / migration_id
    backup_staging.mkdir(parents=True)
    try:
        for source in source_files:
            relative = source.relative_to(source_root)
            backup_target = backup_staging / "source-bytes" / relative
            backup_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup_target)
            if sha256(source) != sha256(backup_target):
                raise LauncherError("Legacy migration backup hash mismatch.")
        _atomic_json(
            backup_staging / "MANIFEST.json",
            {
                "schema_version": 1,
                "migration_id": migration_id,
                "source": str(source_root),
                "files": [
                    {
                        "relative_path": source.relative_to(source_root).as_posix(),
                        "bytes": source.stat().st_size,
                        "sha256": sha256(source),
                    }
                    for source in source_files
                ],
            },
        )
        backup_staging.replace(backup_final)
        for source in source_files:
            relative = source.relative_to(source_root)
            target = paths.refresh_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            staged = target.with_name(f".{target.name}.migration-{os.getpid()}")
            shutil.copy2(source, staged)
            if sha256(source) != sha256(staged):
                raise LauncherError("Legacy migration target hash mismatch.")
            staged.replace(target)
        migrated_validation = inspect_refresh_receipt(status_path=target_latest)
        if not migrated_validation.has_valid_latest:
            raise LauncherError("Migrated receipt failed accepted validation.")
        return MigrationResult("MIGRATED", source=source_root, files=len(source_files))
    except BaseException:
        shutil.rmtree(backup_staging, ignore_errors=True)
        raise


def inspect_legacy_migration(paths: LauncherPaths) -> MigrationResult:
    source_root = legacy_refresh_root(paths)
    if source_root is None:
        return MigrationResult("NO_LEGACY_STATE")
    source_latest = source_root / "latest_refresh_status.json"
    if not source_latest.exists():
        return MigrationResult("NO_LEGACY_STATE", source=source_root)
    source_validation = inspect_refresh_receipt(status_path=source_latest)
    if not source_validation.has_valid_latest:
        return MigrationResult(
            "BLOCKED_INVALID_LEGACY_STATE",
            source=source_root,
            detail=f"Accepted receipt validator returned {source_validation.load_status}.",
        )
    target_latest = paths.refresh_root / "latest_refresh_status.json"
    if not target_latest.exists():
        return MigrationResult("READY_TO_MIGRATE", source=source_root, files=1)
    target_validation = inspect_refresh_receipt(status_path=target_latest)
    if not target_validation.has_valid_latest:
        return MigrationResult(
            "BLOCKED_INVALID_TARGET_STATE",
            source=source_root,
            detail=f"Target receipt validator returned {target_validation.load_status}.",
        )
    if sha256(source_latest) != sha256(target_latest):
        return MigrationResult(
            "BLOCKED_NWR_DESKTOP_LAUNCHER_STATE_MIGRATION_CONFLICT",
            source=source_root,
            detail="Legacy and stable roots contain different valid receipts.",
        )
    return MigrationResult("ALREADY_MIGRATED", source=source_root, files=1)


def runtime_environment(paths: LauncherPaths) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "NWR_DATA_HOME": str(paths.data_home),
            "NWR_DRAFT_DAY_RUNTIME_ROOT": str(paths.draft_root),
            "NWR_DEVELOPMENT_LAB_STATE_ROOT": str(paths.development_lab_root),
            "MODEL_V4_LIVE_API_ENABLED": "false",
        }
    )
    return env


def junction_status(paths: LauncherPaths) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, target in (
        ("refresh_data", paths.refresh_root),
        ("mock_drafts", paths.mock_draft_root),
    ):
        link = paths.repo_root / "local_exports" / name
        if not link.exists():
            result[name] = "MISSING"
        elif os.path.isjunction(link):
            result[name] = "VALID" if link.resolve() == target.resolve() else "WRONG_TARGET"
        else:
            result[name] = "NON_JUNCTION_PATH"
    return result


def ensure_localdata_junctions(paths: LauncherPaths) -> None:
    local_exports = paths.repo_root / "local_exports"
    local_exports.mkdir(parents=True, exist_ok=True)
    for name, target in (
        ("refresh_data", paths.refresh_root),
        ("mock_drafts", paths.mock_draft_root),
    ):
        link = local_exports / name
        target.mkdir(parents=True, exist_ok=True)
        if link.exists():
            if os.path.isjunction(link):
                if link.resolve() != target.resolve():
                    raise LauncherError(f"Junction target conflict at {link}.")
                continue
            if link.is_dir() and not any(link.iterdir()):
                link.rmdir()
            else:
                raise LauncherError(
                    "BLOCKED_NWR_DESKTOP_LAUNCHER_STATE_MIGRATION_CONFLICT: "
                    f"{link} is a populated non-junction path."
                )
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
            check=False,
            creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
        )
        if result.returncode != 0 or not os.path.isjunction(link):
            raise LauncherError(f"Could not create validated state junction at {link}.")
        if link.resolve() != target.resolve():
            raise LauncherError(f"Created junction resolved to the wrong target at {link}.")


def _json_document(path: Path) -> dict[str, Any]:
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("file exceeds the launcher validation bound")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("top-level value is not an object")
    return value


def validate_state(paths: LauncherPaths) -> ValidationResult:
    valid_files: list[Path] = []
    warnings: list[str] = []
    try:
        for path in sorted((paths.draft_root / "state").glob("*.json")):
            document = _json_document(path)
            if document.get("schema_version") != "draft_day_runtime_v2":
                raise ValueError(f"unsupported draft schema: {path.name}")
            valid_files.append(path)
        for path in sorted(paths.development_lab_root.glob("*.json")):
            document = _json_document(path)
            if document.get("schema_version") != 1:
                raise ValueError(f"unsupported Development Lab schema: {path.name}")
            valid_files.append(path)
        for path in sorted(paths.mock_draft_root.glob("*.json")):
            document = _json_document(path)
            if document.get("schema_version") != 1:
                raise ValueError(f"unsupported saved mock schema: {path.name}")
            valid_files.append(path)
        latest = paths.refresh_root / "latest_refresh_status.json"
        if latest.exists():
            result = inspect_refresh_receipt(status_path=latest)
            if not result.has_valid_latest:
                raise ValueError(f"Data Health receipt validation failed: {result.load_status}")
            valid_files.append(latest)
            backup = paths.refresh_root / "backups" / "latest_refresh_status.backup.json"
            if backup.exists() and result.has_valid_backup:
                valid_files.append(backup)
            elif backup.exists():
                warnings.append("A Data Health receipt backup exists but is not valid.")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(False, "INVALID_STATE", tuple(valid_files), (str(exc),))
    return ValidationResult(
        True, "VALID_STATE" if valid_files else "EMPTY_STATE", tuple(valid_files), tuple(warnings)
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def state_fingerprint(paths: LauncherPaths) -> tuple[tuple[str, str], ...]:
    validation = validate_state(paths)
    if not validation.valid:
        raise LauncherError("Persistent state failed fingerprint validation.")
    rows: list[tuple[str, str]] = []
    for path in validation.files:
        family, relative = _family_for(path, paths)
        rows.append((f"{family}/{relative.as_posix()}", sha256(path)))
    return tuple(sorted(rows))


def _family_for(path: Path, paths: LauncherPaths) -> tuple[str, Path]:
    candidates = (
        ("draft_runtime", paths.draft_root),
        ("development_lab", paths.development_lab_root),
        ("saved_mock_drafts", paths.mock_draft_root),
        ("data_health_receipts", paths.refresh_root),
    )
    resolved = path.resolve()
    for family, root in candidates:
        try:
            relative = resolved.relative_to(root.resolve())
            return family, relative
        except ValueError:
            continue
    raise LauncherError(f"State file is outside approved roots: {path}")


def create_backup(
    paths: LauncherPaths,
    *,
    reason: str,
    enforce_retention: bool = True,
    allow_empty_snapshot: bool = False,
) -> dict[str, Any]:
    validation = validate_state(paths)
    if not validation.valid:
        raise LauncherError("Refusing to back up invalid state: " + "; ".join(validation.warnings))
    if not validation.files and not allow_empty_snapshot:
        result = {"status": "NO_VALID_STATE", "reason": reason, "created_at_utc": utc_timestamp()}
        _atomic_json(paths.last_backup_result, result)
        return result
    snapshot_id = f"{utc_timestamp()}__{_safe_token(reason)}"
    staging = paths.backup_root / f".{snapshot_id}.staging"
    final = paths.backup_root / snapshot_id
    if staging.exists() or final.exists():
        raise LauncherError(f"Backup snapshot already exists: {snapshot_id}")
    staging.mkdir(parents=True)
    manifest_files: list[dict[str, Any]] = []
    try:
        for source in validation.files:
            family, relative = _family_for(source, paths)
            target = staging / "payload" / family / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            source_hash = sha256(source)
            if sha256(target) != source_hash:
                raise LauncherError(f"Backup byte validation failed: {source.name}")
            manifest_files.append(
                {
                    "family": family,
                    "relative_path": relative.as_posix(),
                    "bytes": source.stat().st_size,
                    "sha256": source_hash,
                }
            )
        manifest = {
            "schema_version": 1,
            "snapshot_id": snapshot_id,
            "created_at_utc": utc_timestamp(),
            "reason": reason,
            "app_commit": EXPECTED_APP_COMMIT,
            "launcher_version": LAUNCHER_VERSION,
            "files": manifest_files,
        }
        _atomic_json(staging / "MANIFEST.json", manifest)
        staging.replace(final)
        if enforce_retention:
            _prune_backups(paths.backup_root)
        result = {"status": "CREATED", "snapshot_id": snapshot_id, "files": len(manifest_files)}
        _atomic_json(paths.last_backup_result, result)
        return result
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _prune_backups(root: Path) -> None:
    snapshots = sorted(
        (p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")), reverse=True
    )
    valid = [path for path in snapshots if validate_backup(path)["valid"]]
    for path in valid[BACKUP_RETENTION:]:
        if len(valid) <= 1:
            break
        shutil.rmtree(path)


def create_manual_backup(paths: LauncherPaths) -> dict[str, Any]:
    with _maintenance_lock(paths, operation="manual_backup"):
        return create_backup(paths, reason="manual")


def validate_backup(snapshot: Path) -> dict[str, Any]:
    try:
        manifest = _json_document(snapshot / "MANIFEST.json")
        if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
            raise ValueError("unsupported backup manifest")
        for row in manifest["files"]:
            family = str(row["family"])
            relative = Path(str(row["relative_path"]))
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unsafe backup path")
            candidate = snapshot / "payload" / family / relative
            if not candidate.is_file() or sha256(candidate) != row["sha256"]:
                raise ValueError("backup hash mismatch")
        return {
            "valid": True,
            "snapshot_id": manifest.get("snapshot_id"),
            "files": len(manifest["files"]),
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {"valid": False, "error": str(exc)}


def restore_plan(paths: LauncherPaths, snapshot_id: str) -> dict[str, Any]:
    snapshot = paths.backup_root / Path(snapshot_id).name
    validation = validate_backup(snapshot)
    if not validation["valid"]:
        raise LauncherError(f"Backup is invalid: {validation.get('error', 'unknown error')}")
    manifest = _json_document(snapshot / "MANIFEST.json")
    roots = {
        "draft_runtime": paths.draft_root,
        "development_lab": paths.development_lab_root,
        "saved_mock_drafts": paths.mock_draft_root,
        "data_health_receipts": paths.refresh_root,
    }
    changes: list[dict[str, str]] = []
    for row in manifest["files"]:
        target = roots[row["family"]] / Path(row["relative_path"])
        status = (
            "UNCHANGED"
            if target.is_file() and sha256(target) == row["sha256"]
            else ("REPLACE" if target.exists() else "CREATE")
        )
        changes.append(
            {
                "family": row["family"],
                "path": row["relative_path"],
                "status": status,
                "sha256": row["sha256"],
            }
        )
    return {"snapshot_id": snapshot_id, "dry_run": True, "changes": changes}


def restore_backup(paths: LauncherPaths, snapshot_id: str, *, confirmation: str) -> dict[str, Any]:
    if confirmation != snapshot_id:
        raise LauncherError("Restore confirmation must exactly match the snapshot ID.")
    with _maintenance_lock(paths, operation="restore"):
        return _restore_backup_locked(paths, snapshot_id)


def _restore_backup_locked(paths: LauncherPaths, snapshot_id: str) -> dict[str, Any]:
    snapshot = paths.backup_root / Path(snapshot_id).name
    plan = restore_plan(paths, snapshot_id)
    # Preserve the selected source before retention can run, then defer pruning until
    # the restore has committed and passed application-boundary validation. An empty
    # manifest is still a real rollback snapshot.
    pre_restore = create_backup(
        paths,
        reason="pre_restore",
        enforce_retention=False,
        allow_empty_snapshot=True,
    )
    roots = {
        "draft_runtime": paths.draft_root,
        "development_lab": paths.development_lab_root,
        "saved_mock_drafts": paths.mock_draft_root,
        "data_health_receipts": paths.refresh_root,
    }
    manifest = _json_document(snapshot / "MANIFEST.json")
    desired = {(str(row["family"]), Path(str(row["relative_path"]))) for row in manifest["files"]}
    transaction = paths.run_root / f"restore-{uuid.uuid4().hex}.staging"
    transaction.mkdir(parents=True)
    try:
        for row in manifest["files"]:
            relative = Path(str(row["relative_path"]))
            source = snapshot / "payload" / row["family"] / relative
            staged = transaction / row["family"] / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, staged)
            if sha256(staged) != row["sha256"]:
                raise LauncherError(f"Restore staging hash mismatch: {relative}")

        current = validate_state(paths)
        if not current.valid:
            raise LauncherError(
                "Current state is invalid; exact restore cannot create rollback bytes."
            )
        for existing in current.files:
            family, relative = _family_for(existing, paths)
            if (family, relative) not in desired:
                existing.unlink()
        for row in manifest["files"]:
            relative = Path(str(row["relative_path"]))
            target = roots[row["family"]] / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            (transaction / row["family"] / relative).replace(target)
        final_validation = validate_state(paths)
        if not final_validation.valid or state_fingerprint(paths) != tuple(
            sorted(
                (f"{row['family']}/{row['relative_path']}", row["sha256"])
                for row in manifest["files"]
            )
        ):
            raise LauncherError("Restored state failed exact application-boundary validation.")
    except BaseException as exc:
        _restore_snapshot_without_backup(paths, str(pre_restore["snapshot_id"]))
        raise LauncherError(f"Restore rolled back after failure: {exc}") from exc
    finally:
        shutil.rmtree(transaction, ignore_errors=True)
    _prune_backups(paths.backup_root)
    return {"snapshot_id": snapshot_id, "restored": True, "changes": plan["changes"]}


def _restore_snapshot_without_backup(paths: LauncherPaths, snapshot_id: str) -> None:
    """Best-effort internal rollback from a snapshot created in this operation."""
    snapshot = paths.backup_root / Path(snapshot_id).name
    if not validate_backup(snapshot)["valid"]:
        raise LauncherError("Internal rollback snapshot is invalid.")
    manifest = _json_document(snapshot / "MANIFEST.json")
    roots = {
        "draft_runtime": paths.draft_root,
        "development_lab": paths.development_lab_root,
        "saved_mock_drafts": paths.mock_draft_root,
        "data_health_receipts": paths.refresh_root,
    }
    desired = {(str(row["family"]), Path(str(row["relative_path"]))) for row in manifest["files"]}
    current = validate_state(paths)
    if current.valid:
        for existing in current.files:
            family, relative = _family_for(existing, paths)
            if (family, relative) not in desired:
                existing.unlink()
    for row in manifest["files"]:
        relative = Path(str(row["relative_path"]))
        source = snapshot / "payload" / row["family"] / relative
        target = roots[row["family"]] / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        staged = target.with_name(f".{target.name}.rollback-{os.getpid()}")
        shutil.copy2(source, staged)
        if sha256(staged) != row["sha256"]:
            staged.unlink(missing_ok=True)
            raise LauncherError("Internal rollback staging hash mismatch.")
        staged.replace(target)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    staged.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    staged.replace(path)


def _safe_token(value: str) -> str:
    return (
        "".join(
            character if character.isalnum() or character in "-_" else "_" for character in value
        )[:48]
        or "manual"
    )


def find_python(repo_root: Path) -> Path:
    configured = os.environ.get("NWR_DESKTOP_PYTHON", "").strip()
    candidates = [
        Path(configured) if configured else Path("__missing__"),
        repo_root / ".venv" / "Scripts" / "python.exe",
        Path(r"C:\NWR_SHARED_DATA\tool_envs\nwr_streamlit_preview\Scripts\python.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file() and _runtime_is_supported(candidate):
            return candidate.resolve()
    raise LauncherError("No supported Python 3.12+ runtime with Streamlit is available.")


def _runtime_is_supported(python: Path) -> bool:
    result = subprocess.run(
        [
            str(python),
            "-c",
            "import streamlit,sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)",
        ],
        cwd=Path(__file__).resolve().parents[2],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=15,
        check=False,
        creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
    )
    return result.returncode == 0


def verify_repository(paths: LauncherPaths) -> None:
    if not (paths.repo_root / "app" / "main.py").is_file():
        raise LauncherError("Launcher repository is missing app/main.py.")
    result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={paths.repo_root.as_posix()}",
            "-C",
            str(paths.repo_root),
            "merge-base",
            "--is-ancestor",
            EXPECTED_APP_COMMIT,
            "HEAD",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
    )
    if result.returncode != 0:
        raise LauncherError("Repository does not descend from accepted NWR V1 RC1.")
    tree_result = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={paths.repo_root.as_posix()}",
            "-C",
            str(paths.repo_root),
            "rev-parse",
            f"{EXPECTED_APP_COMMIT}^{{tree}}",
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
    )
    if tree_result.returncode != 0 or tree_result.stdout.strip() != EXPECTED_APP_TREE:
        raise LauncherError("Accepted NWR V1 RC1 tree identity is unavailable.")


def health_ok() -> bool:
    try:
        with urllib.request.urlopen(
            f"http://{HOST}:{PORT}/_stcore/health", timeout=1.0
        ) as response:
            return response.status == 200 and b"ok" in response.read(64).lower()
    except (OSError, urllib.error.URLError):
        return False


def _read_lock(paths: LauncherPaths) -> dict[str, Any] | None:
    try:
        value = _json_document(paths.lock_path)
        return value if value.get("launcher_version") == LAUNCHER_VERSION else None
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _process_identity(pid: int) -> dict[str, Any] | None:
    if pid <= 0:
        return None
    if os.name != "nt":
        return (
            {"pid": pid, "executable": str(Path(sys.executable).resolve()), "created": None}
            if _pid_alive(pid)
            else None
        )
    query = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(query, False, pid)
    if not handle:
        return None
    try:
        size = ctypes.c_ulong(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not ctypes.windll.kernel32.QueryFullProcessImageNameW(
            handle, 0, buffer, ctypes.byref(size)
        ):
            return None
        created = ctypes.c_ulonglong()
        exited = ctypes.c_ulonglong()
        kernel = ctypes.c_ulonglong()
        user = ctypes.c_ulonglong()
        if not ctypes.windll.kernel32.GetProcessTimes(
            handle,
            ctypes.byref(created),
            ctypes.byref(exited),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            return None
        return {
            "pid": pid,
            "executable": str(Path(buffer.value).resolve()),
            "created": created.value,
        }
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _listener_pids() -> set[int]:
    result = subprocess.run(
        ["netstat.exe", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
        creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
    )
    pids: set[int] = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if (
            len(fields) >= 5
            and fields[0].upper() == "TCP"
            and fields[1].endswith(f":{PORT}")
            and fields[3].upper() == "LISTENING"
        ):
            try:
                pids.add(int(fields[4]))
            except ValueError:
                pass
    return pids


def _parent_pid(pid: int) -> int | None:
    if os.name != "nt" or pid <= 0:
        return None

    class ProcessBasicInformation(ctypes.Structure):
        _fields_ = [
            ("reserved1", ctypes.c_void_p),
            ("peb_base_address", ctypes.c_void_p),
            ("reserved2", ctypes.c_void_p * 2),
            ("unique_process_id", ctypes.c_size_t),
            ("inherited_from_unique_process_id", ctypes.c_size_t),
        ]

    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        info = ProcessBasicInformation()
        returned = ctypes.c_ulong()
        status = ctypes.windll.ntdll.NtQueryInformationProcess(
            handle,
            0,
            ctypes.byref(info),
            ctypes.sizeof(info),
            ctypes.byref(returned),
        )
        return int(info.inherited_from_unique_process_id) if status == 0 else None
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _is_descendant(pid: int, ancestor_pid: int) -> bool:
    current = pid
    seen: set[int] = set()
    for _ in range(16):
        if current == ancestor_pid:
            return True
        if current <= 0 or current in seen:
            return False
        seen.add(current)
        parent = _parent_pid(current)
        if parent is None:
            return False
        current = parent
    return False


def _identity_matches(record: dict[str, Any], prefix: str) -> bool:
    identity = _process_identity(int(record.get(f"{prefix}_pid", 0)))
    expected_executable = record.get(f"{prefix}_executable")
    expected_created = record.get(f"{prefix}_created")
    return bool(
        identity
        and expected_executable
        and Path(str(identity["executable"])).resolve() == Path(str(expected_executable)).resolve()
        and identity["created"] == expected_created
    )


def _owned_healthy_instance(paths: LauncherPaths, lock: dict[str, Any]) -> bool:
    listener_pid = int(lock.get("listener_pid", 0))
    return bool(
        lock.get("state") == "RUNNING"
        and Path(str(lock.get("repo_root", ""))).resolve() == paths.repo_root.resolve()
        and lock.get("app_commit") == EXPECTED_APP_COMMIT
        and int(lock.get("port", 0)) == PORT
        and _identity_matches(lock, "launcher")
        and _identity_matches(lock, "streamlit")
        and _identity_matches(lock, "listener")
        and listener_pid in _listener_pids()
        and _is_descendant(listener_pid, int(lock.get("streamlit_pid", 0)))
        and health_ok()
    )


@contextmanager
def _maintenance_lock(paths: LauncherPaths, *, operation: str) -> Iterable[None]:
    paths.run_root.mkdir(parents=True, exist_ok=True)
    identity = _process_identity(os.getpid())
    if identity is None:
        raise LauncherError("Could not establish maintenance process identity.")
    nonce = uuid.uuid4().hex
    try:
        descriptor = os.open(paths.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise LauncherError(
            f"{operation} requires NWR to be stopped with no launcher operation in progress."
        ) from exc
    record = {
        "launcher_version": LAUNCHER_VERSION,
        "state": "MAINTENANCE",
        "operation": operation,
        "launcher_pid": os.getpid(),
        "launcher_executable": identity["executable"],
        "launcher_created": identity["created"],
        "repo_root": str(paths.repo_root),
        "app_commit": EXPECTED_APP_COMMIT,
        "port": PORT,
        "lock_nonce": nonce,
        "started_at_utc": utc_timestamp(),
    }
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(record, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        if port_is_listening(HOST, PORT):
            raise LauncherError(
                f"{operation} requires NWR to be stopped and port {PORT} to be free."
            )
        yield
    finally:
        lock = _read_lock(paths)
        if lock and lock.get("lock_nonce") == nonce:
            paths.lock_path.unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _acquire_lock(paths: LauncherPaths) -> None:
    paths.run_root.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(paths.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        identity = _process_identity(os.getpid())
        if identity is None:
            os.close(descriptor)
            paths.lock_path.unlink(missing_ok=True)
            raise LauncherError("Could not establish launcher process identity.")
        initial = {
            "launcher_version": LAUNCHER_VERSION,
            "state": "STARTING",
            "launcher_pid": os.getpid(),
            "launcher_executable": identity["executable"],
            "launcher_created": identity["created"],
            "repo_root": str(paths.repo_root),
            "app_commit": EXPECTED_APP_COMMIT,
            "port": PORT,
            "lock_nonce": uuid.uuid4().hex,
            "started_at_utc": utc_timestamp(),
        }
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(initial, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        lock = _read_lock(paths)
        if lock and _owned_healthy_instance(paths, lock):
            open_browser(paths)
            raise SystemExit(0) from exc
        if lock and _identity_matches(lock, "launcher"):
            raise LauncherError(
                "A verified NWR launcher startup or shutdown is already in progress."
            ) from exc
        if port_is_listening(HOST, PORT):
            raise LauncherError(
                "Port 8520 is occupied and no healthy launcher-owned NWR instance can be verified."
            ) from exc
        paths.lock_path.unlink(missing_ok=True)
        return _acquire_lock(paths)


def browser_candidates() -> Iterable[Path]:
    for variable, relative in (
        ("PROGRAMFILES", r"Google\Chrome\Application\chrome.exe"),
        ("PROGRAMFILES(X86)", r"Google\Chrome\Application\chrome.exe"),
        ("LOCALAPPDATA", r"Google\Chrome\Application\chrome.exe"),
        ("PROGRAMFILES", r"Microsoft\Edge\Application\msedge.exe"),
        ("PROGRAMFILES(X86)", r"Microsoft\Edge\Application\msedge.exe"),
    ):
        root = os.environ.get(variable, "")
        if root:
            yield Path(root) / relative


def open_browser(paths: LauncherPaths) -> subprocess.Popen[Any] | None:
    if os.environ.get("NWR_LAUNCHER_NO_BROWSER") == "1":
        return None
    url = f"http://{HOST}:{PORT}/"
    for browser in browser_candidates():
        if browser.is_file():
            return subprocess.Popen(
                [
                    str(browser),
                    f"--app={url}",
                    f"--user-data-dir={paths.browser_profile}",
                    "--disable-background-mode",
                    "--disable-extensions",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
            )
    os.startfile(url)  # type: ignore[attr-defined]
    return None


def start(paths: LauncherPaths) -> dict[str, Any]:
    ensure_directories(paths)
    verify_repository(paths)
    _acquire_lock(paths)
    if port_is_listening(HOST, PORT):
        paths.lock_path.unlink(missing_ok=True)
        raise LauncherError(
            "Port 8520 is occupied by another process; nothing was killed or reused."
        )
    migration = migrate_legacy_refresh(paths)
    if migration.status.startswith("BLOCKED_"):
        paths.lock_path.unlink(missing_ok=True)
        raise LauncherError(f"{migration.status}: {migration.detail}")
    ensure_localdata_junctions(paths)
    initial_state_fingerprint = state_fingerprint(paths)
    validation = validate_state(paths)
    if not validation.valid:
        paths.lock_path.unlink(missing_ok=True)
        raise LauncherError(
            "Persistent state is invalid; startup stopped to prevent mutation: "
            + "; ".join(validation.warnings)
        )
    backup_warning = ""
    try:
        create_backup(paths, reason="pre_launch")
    except Exception as exc:
        backup_warning = f"Pre-launch backup warning: {exc}"
        _report_backup_warning(paths, backup_warning)
    python = find_python(paths.repo_root)
    stdout_log = paths.logs_root / "streamlit.stdout.log"
    stderr_log = paths.logs_root / "streamlit.stderr.log"
    original_env = os.environ.copy()
    os.environ.update(runtime_environment(paths))
    process = None
    try:
        process = start_streamlit(
            python,
            paths.repo_root,
            host=HOST,
            port=PORT,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
        )
        lock = _read_lock(paths) or {}
        child_identity = _process_identity(process.pid)
        if child_identity is None:
            raise LauncherError("Could not establish Streamlit process identity.")
        _atomic_json(
            paths.lock_path,
            {
                **lock,
                "state": "RUNNING",
                "streamlit_pid": process.pid,
                "streamlit_executable": child_identity["executable"],
                "streamlit_created": child_identity["created"],
                "python": str(python),
            },
        )
        wait_for_http(
            f"http://{HOST}:{PORT}/_stcore/health", process, timeout_seconds=STARTUP_TIMEOUT_SECONDS
        )
        listeners = _listener_pids()
        if len(listeners) != 1:
            raise LauncherError("NWR startup did not produce exactly one listener owner.")
        listener_pid = next(iter(listeners))
        if not _is_descendant(listener_pid, process.pid):
            raise LauncherError("Port 8520 listener is not owned by the launched Streamlit tree.")
        listener_identity = _process_identity(listener_pid)
        if listener_identity is None:
            raise LauncherError("Could not establish listener process identity.")
        lock = _read_lock(paths) or {}
        _atomic_json(
            paths.lock_path,
            {
                **lock,
                "listener_pid": listener_pid,
                "listener_executable": listener_identity["executable"],
                "listener_created": listener_identity["created"],
            },
        )
        browser = open_browser(paths)
        while process.poll() is None:
            if paths.stop_request.exists() or (browser is not None and browser.poll() is not None):
                break
            time.sleep(0.25)
        shutdown = graceful_shutdown(process, timeout_seconds=SHUTDOWN_TIMEOUT_SECONDS)
        released = wait_for_port_release(HOST, PORT, timeout_seconds=5.0)
        markers = fatal_markers_in_logs(stdout_log, stderr_log)
        if released and not shutdown.forced_cleanup and not markers:
            if state_fingerprint(paths) != initial_state_fingerprint:
                create_backup(paths, reason="post_clean_shutdown")
        return {
            "exit_code": shutdown.exit_code,
            "forced_cleanup": shutdown.forced_cleanup,
            "port_released": released,
            "fatal_markers": list(markers),
            "backup_warning": backup_warning,
            "migration": asdict(migration),
        }
    except BaseException as exc:
        if process is not None and process.poll() is None:
            shutdown = graceful_shutdown(process, timeout_seconds=SHUTDOWN_TIMEOUT_SECONDS)
            released = wait_for_port_release(HOST, PORT, timeout_seconds=5.0)
            _append_launcher_log(
                paths,
                "Startup failure cleanup: "
                f"{exc}; forced={shutdown.forced_cleanup}; port_released={released}",
            )
        raise
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        paths.stop_request.unlink(missing_ok=True)
        paths.lock_path.unlink(missing_ok=True)


def request_stop(paths: LauncherPaths) -> dict[str, Any]:
    lock = _read_lock(paths)
    if not lock:
        if port_is_listening(HOST, PORT):
            raise LauncherError(
                "Port 8520 is occupied, but no launcher ownership record exists; "
                "nothing was killed."
            )
        return {"status": "NOT_RUNNING"}
    if (
        not _identity_matches(lock, "launcher")
        or Path(str(lock.get("repo_root", ""))).resolve() != paths.repo_root.resolve()
    ):
        raise LauncherError(
            "Launcher ownership is stale; refusing to target an unverified process."
        )
    paths.stop_request.parent.mkdir(parents=True, exist_ok=True)
    paths.stop_request.write_text(utc_timestamp() + "\n", encoding="utf-8")
    deadline = time.monotonic() + SHUTDOWN_TIMEOUT_SECONDS + 7
    while time.monotonic() < deadline:
        if not paths.lock_path.exists() and not port_is_listening(HOST, PORT):
            return {"status": "STOPPED", "port_released": True}
        time.sleep(0.2)
    raise LauncherError("Graceful stop timed out; no unrelated process was killed.")


def status(paths: LauncherPaths) -> dict[str, Any]:
    validation = validate_state(paths)
    lock = _read_lock(paths)
    backup = None
    if paths.last_backup_result.exists():
        try:
            backup = _json_document(paths.last_backup_result)
        except Exception:
            backup = {"status": "UNREADABLE"}
    return {
        "launcher_version": LAUNCHER_VERSION,
        "app_commit": EXPECTED_APP_COMMIT,
        "data_root": str(paths.data_home),
        "backup_root": str(paths.backup_root),
        "port": PORT,
        "health_status": "HEALTHY" if health_ok() else "STOPPED",
        "process_ownership": "VERIFIED_RUNNING"
        if lock and _owned_healthy_instance(paths, lock)
        else ("LOCK_PRESENT_UNVERIFIED" if lock else "NONE"),
        "state_validation": validation.status,
        "state_warnings": list(validation.warnings),
        "most_recent_backup": backup,
        "legacy_migration": asdict(inspect_legacy_migration(paths)),
        "junctions": junction_status(paths),
        "startup_command": list(
            build_streamlit_command(find_python(paths.repo_root), host=HOST, port=PORT)
        ),
    }


def show_error(message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(0, message, "Niners War Room", 0x10)
    else:
        print(message, file=sys.stderr)


def show_warning(message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(0, message, "Niners War Room", 0x30)
    else:
        print(f"WARNING: {message}", file=sys.stderr)


def _report_backup_warning(paths: LauncherPaths, message: str) -> None:
    visible = message
    try:
        _append_launcher_log(paths, message)
    except OSError as exc:
        visible = f"{message}\n\nLauncher log could not be written: {exc}"
    show_warning(visible)


def _append_launcher_log(paths: LauncherPaths, message: str) -> None:
    paths.logs_root.mkdir(parents=True, exist_ok=True)
    with (paths.logs_root / "launcher.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{utc_timestamp()} {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Niners War Room Windows desktop launcher")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("start")
    sub.add_parser("stop")
    sub.add_parser("status")
    sub.add_parser("open-logs")
    sub.add_parser("backup")
    sub.add_parser("validate-data")
    dry = sub.add_parser("restore-dry-run")
    dry.add_argument("snapshot_id")
    restore = sub.add_parser("restore")
    restore.add_argument("snapshot_id")
    restore.add_argument("--confirm", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = launcher_paths()
    try:
        if args.command == "start":
            payload = start(paths)
        elif args.command == "stop":
            payload = request_stop(paths)
        elif args.command == "status":
            payload = status(paths)
        elif args.command == "open-logs":
            ensure_directories(paths)
            os.startfile(paths.logs_root)  # type: ignore[attr-defined]
            payload = {"opened": str(paths.logs_root)}
        elif args.command == "backup":
            ensure_directories(paths)
            payload = create_manual_backup(paths)
        elif args.command == "validate-data":
            payload = asdict(validate_state(paths))
        elif args.command == "restore-dry-run":
            payload = restore_plan(paths, args.snapshot_id)
        elif args.command == "restore":
            payload = restore_backup(paths, args.snapshot_id, confirmation=args.confirm)
        else:
            raise LauncherError(f"Unsupported command: {args.command}")
        print(json.dumps(payload, indent=2, default=str))
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        try:
            _append_launcher_log(paths, f"{args.command} failed: {exc}")
        except OSError:
            pass
        if args.command == "start":
            show_error(str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
