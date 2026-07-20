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
from src.services.refresh_receipt_store_service import (
    CORRUPT,
    MISSING,
    OVERSIZED,
    inspect_refresh_receipt,
    quarantine_invalid_refresh_receipt,
)

LAUNCHER_VERSION = "nwr_windows_desktop_launcher_v1"
EXPECTED_APP_COMMIT = "dc399a8c2ed5d77d9802d98c215a12cbe594d7d7"
EXPECTED_APP_TREE = "e6f98339bf7172b45b78d94dfed390559856f899"
HOST = "127.0.0.1"
PORT = 8520
BACKUP_RETENTION = 5
STARTUP_TIMEOUT_SECONDS = 30.0
SHUTDOWN_TIMEOUT_SECONDS = 15.0
DATA_HEALTH_RECOVERY_CONFIRMATION = "QUARANTINE_CORRUPT_RECEIPT"
OWNERSHIP_STATES = frozenset(
    {"RUNNING", "STOP_REQUESTED", "STOPPING", "RECOVERY_REQUIRED", "STOPPED"}
)
STOP_POLL_SECONDS = 0.2
STOP_ESCALATION_SECONDS = 5.0


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
    recovery_root: Path

    @property
    def lock_path(self) -> Path:
        return self.run_root / "launcher.lock.json"

    @property
    def stop_request(self) -> Path:
        return self.run_root / "stop.request"

    @property
    def stop_guard(self) -> Path:
        return self.run_root / "stop.guard.json"

    @property
    def last_stop_receipt(self) -> Path:
        return self.run_root / "last_stop.json"

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
        recovery_root=home / "recovery" / "data-health",
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
        paths.recovery_root,
    ):
        path.mkdir(parents=True, exist_ok=True)


def legacy_refresh_root(paths: LauncherPaths) -> Path | None:
    configured = os.environ.get("NWR_LEGACY_REFRESH_ROOT", "").strip()
    if configured:
        if os.environ.get("NWR_LAUNCHER_TEST_MODE") != "1":
            raise LauncherError("Legacy refresh root overrides are test-only.")
        candidate = Path(configured).resolve()
        try:
            candidate.relative_to(paths.data_home.parent.resolve())
        except ValueError as exc:
            raise LauncherError("Synthetic legacy refresh root escapes the test boundary.") from exc
        return candidate
    return canonical_legacy_refresh_root(paths)


def canonical_legacy_refresh_root(paths: LauncherPaths) -> Path | None:
    canonical = Path(r"C:\NWR\Niners-War-Room\local_exports\refresh_data")
    return _canonical_legacy_refresh_root_from(paths, canonical)


def _canonical_legacy_refresh_root_from(
    paths: LauncherPaths, canonical: Path
) -> Path | None:
    if not canonical.exists():
        return None
    if _path_is_link(canonical):
        raise LauncherError("The canonical legacy Data Health root is a junction or link.")
    if canonical.resolve() == paths.refresh_root.resolve():
        return None
    return canonical


def migrate_legacy_refresh(paths: LauncherPaths) -> MigrationResult:
    source_root = legacy_refresh_root(paths)
    if source_root is None:
        return MigrationResult("NO_LEGACY_STATE")
    source_latest = source_root / "latest_refresh_status.json"
    if not source_latest.exists():
        backup_validation = inspect_refresh_receipt(status_path=source_latest)
        if backup_validation.has_valid_backup:
            return MigrationResult(
                "BLOCKED_VALID_LEGACY_BACKUP_REQUIRES_EXPLICIT_RECOVERY",
                source=source_root,
                detail="A valid legacy backup exists without a latest receipt.",
            )
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
        backup_validation = inspect_refresh_receipt(status_path=source_latest)
        if backup_validation.has_valid_backup:
            return MigrationResult(
                "BLOCKED_VALID_LEGACY_BACKUP_REQUIRES_EXPLICIT_RECOVERY",
                source=source_root,
                detail="A valid legacy backup exists without a latest receipt.",
            )
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


def _path_is_link(path: Path) -> bool:
    is_junction = getattr(os.path, "isjunction", lambda _path: False)
    return path.is_symlink() or bool(is_junction(path))


def _receipt_relative_allowed(relative: Path) -> bool:
    parts = relative.parts
    if parts == ("latest_refresh_status.json",):
        return True
    if parts == ("backups", "latest_refresh_status.backup.json"):
        return True
    if len(parts) == 2 and parts[0] == "quarantine" and parts[1].endswith(".json"):
        return True
    return bool(
        len(parts) == 1
        and parts[0][:1].isdigit()
        and parts[0].endswith("_status.json")
    )


def _receipt_owned_files(root: Path, *, require_latest: bool) -> tuple[Path, ...]:
    if not root.is_dir() or _path_is_link(root):
        raise LauncherError("The approved Data Health receipt root is unavailable or unsafe.")
    latest = root / "latest_refresh_status.json"
    if require_latest and (not latest.is_file() or _path_is_link(latest)):
        raise LauncherError("The approved latest Data Health receipt is unavailable or unsafe.")
    candidates = [
        path
        for path in root.glob("*_status.json")
        if path.name == latest.name
        or (path.name[:1].isdigit() and path.name.endswith("_status.json"))
    ]
    backup_dir = root / "backups"
    quarantine_dir = root / "quarantine"
    for directory in (backup_dir, quarantine_dir):
        if directory.exists() and _path_is_link(directory):
            raise LauncherError("Data Health recovery refuses a linked receipt directory.")
    backup = backup_dir / "latest_refresh_status.backup.json"
    if backup.exists():
        candidates.append(backup)
    if quarantine_dir.is_dir():
        candidates.extend(quarantine_dir.glob("*.json"))
    files: list[Path] = []
    for path in candidates:
        if not path.is_file() or _path_is_link(path):
            raise LauncherError("Data Health recovery refuses a linked or irregular receipt file.")
        relative = path.relative_to(root)
        if not _receipt_relative_allowed(relative):
            raise LauncherError("Data Health recovery found an unsupported receipt-owned path.")
        files.append(path)
    unique = {os.path.normcase(str(path.resolve())): path for path in files}
    if len(unique) != len(files) or len(files) > 27:
        raise LauncherError("Data Health receipt-owned inventory is duplicated or unbounded.")
    return tuple(sorted(files))


def _tree_regular_files(root: Path) -> tuple[Path, ...]:
    if not root.is_dir() or _path_is_link(root):
        raise LauncherError("Recovery payload root is unavailable or linked.")
    pending = [root]
    files: list[Path] = []
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                path = Path(entry.path)
                if _path_is_link(path):
                    raise LauncherError("Recovery payload contains a link or junction.")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(path)
                else:
                    raise LauncherError("Recovery payload contains an irregular entry.")
    return tuple(sorted(files))


def _recovery_manifest(root: Path, files: Iterable[Path]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at_utc": utc_timestamp(),
        "source_root": str(root),
        "scope": "canonical_refresh_receipt_store",
        "files": [
            {
                "relative_path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
    }


def validate_data_health_recovery_backup(backup: Path) -> dict[str, Any]:
    try:
        manifest = _json_document(backup / "MANIFEST.json")
        if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
            raise ValueError("unsupported Data Health recovery manifest")
        if manifest.get("scope") != "canonical_refresh_receipt_store":
            raise ValueError("Data Health recovery manifest has an unsupported scope")
        if not 1 <= len(manifest["files"]) <= 27:
            raise ValueError("Data Health recovery manifest file count is invalid")
        payload_root = backup / "payload"
        actual_files = _tree_regular_files(payload_root)
        seen: set[str] = set()
        expected: set[str] = set()
        for row in manifest["files"]:
            relative = Path(str(row["relative_path"]))
            if not _receipt_relative_allowed(relative):
                raise ValueError("Data Health recovery manifest has an unsupported receipt path")
            target = _bounded_family_target(payload_root, relative)
            key = os.path.normcase(str(target))
            if key in seen:
                raise ValueError("Data Health recovery manifest contains a duplicate path")
            seen.add(key)
            expected.add(key)
            if not target.is_file() or _path_is_link(target):
                raise ValueError("Data Health recovery receipt is unsafe or missing")
            if target.stat().st_size != int(row["bytes"]) or sha256(target) != row["sha256"]:
                raise ValueError("Data Health recovery byte validation failed")
        actual = {os.path.normcase(str(path.resolve())) for path in actual_files}
        if actual != expected:
            raise ValueError("Data Health recovery payload contains unexpected files")
        if "latest_refresh_status.json" not in {
            str(row["relative_path"]) for row in manifest["files"]
        }:
            raise ValueError("Data Health recovery payload lacks the latest receipt")
        return {"valid": True, "files": len(manifest["files"])}
    except (LauncherError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {"valid": False, "error": str(exc)}


def create_data_health_recovery_backup(paths: LauncherPaths, source_root: Path) -> Path:
    files = _receipt_owned_files(source_root, require_latest=True)
    recovery_id = f"{utc_timestamp()}__dh_recovery"
    staging = paths.recovery_root / f".{recovery_id}.staging"
    final = paths.recovery_root / recovery_id
    if staging.exists() or final.exists():
        raise LauncherError(f"Data Health recovery backup already exists: {recovery_id}")
    staging.mkdir(parents=True)
    try:
        manifest = _recovery_manifest(source_root, files)
        for source in files:
            target = _bounded_family_target(
                staging / "payload", source.relative_to(source_root)
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if target.stat().st_size != source.stat().st_size or sha256(target) != sha256(source):
                raise LauncherError("Data Health recovery backup hash mismatch.")
        _atomic_json(staging / "MANIFEST.json", manifest)
        staging.replace(final)
        if not validate_data_health_recovery_backup(final)["valid"]:
            raise LauncherError("Data Health recovery backup validation failed.")

        # Exercise the exact rollback function against an isolated destination root.
        proof = paths.recovery_root / ".rollback-proof"
        proof.mkdir(parents=True)
        try:
            restore_data_health_recovery_backup(final, proof)
            if _receipt_scope_fingerprint(proof) != _receipt_scope_fingerprint(source_root):
                raise LauncherError("Data Health recovery rollback proof failed.")
        finally:
            shutil.rmtree(proof, ignore_errors=True)
        return final
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        if final.exists() and not validate_data_health_recovery_backup(final)["valid"]:
            shutil.rmtree(final, ignore_errors=True)
        raise


def _receipt_scope_fingerprint(root: Path) -> tuple[tuple[str, int, str], ...]:
    return tuple(
        sorted(
            (
                path.relative_to(root).as_posix(),
                path.stat().st_size,
                sha256(path),
            )
            for path in _receipt_owned_files(root, require_latest=False)
        )
    )


def restore_data_health_recovery_backup(backup: Path, destination_root: Path) -> Path:
    validation = validate_data_health_recovery_backup(backup)
    if not validation["valid"]:
        raise LauncherError("Cannot restore an invalid Data Health recovery backup.")
    if destination_root.exists() and _path_is_link(destination_root):
        raise LauncherError("Data Health rollback destination is unsafe.")
    destination_root.mkdir(parents=True, exist_ok=True)
    manifest = _json_document(backup / "MANIFEST.json")
    desired = {
        Path(str(row["relative_path"])): (int(row["bytes"]), str(row["sha256"]))
        for row in manifest["files"]
    }
    for current in _receipt_owned_files(destination_root, require_latest=False):
        if current.relative_to(destination_root) not in desired:
            current.unlink()
    for relative, (expected_bytes, expected_hash) in desired.items():
        source = _bounded_family_target(backup / "payload", relative)
        target = _bounded_family_target(destination_root, relative)
        if target.exists() and _path_is_link(target):
            raise LauncherError("Data Health rollback target is unsafe.")
        target.parent.mkdir(parents=True, exist_ok=True)
        staged = target.with_name(
            f".{target.name}.rollback-{os.getpid()}-{uuid.uuid4().hex[:8]}.tmp"
        )
        try:
            shutil.copy2(source, staged)
            if staged.stat().st_size != expected_bytes or sha256(staged) != expected_hash:
                raise LauncherError("Data Health rollback staging validation failed.")
            staged.replace(target)
        finally:
            staged.unlink(missing_ok=True)
    expected = tuple(
        sorted((relative.as_posix(), size, digest) for relative, (size, digest) in desired.items())
    )
    if _receipt_scope_fingerprint(destination_root) != expected:
        raise LauncherError("Data Health rollback exact-scope validation failed.")
    return destination_root / "latest_refresh_status.json"


def recover_corrupt_data_health_receipt(
    paths: LauncherPaths, *, confirmation: str
) -> dict[str, Any]:
    source_root = canonical_legacy_refresh_root(paths)
    if source_root is None:
        raise LauncherError("No canonical legacy Data Health receipt root is available.")
    return _recover_corrupt_data_health_receipt_at_root(
        paths,
        source_root=source_root,
        confirmation=confirmation,
    )


def _recover_corrupt_data_health_receipt_at_root(
    paths: LauncherPaths, *, source_root: Path, confirmation: str
) -> dict[str, Any]:
    if confirmation != DATA_HEALTH_RECOVERY_CONFIRMATION:
        raise LauncherError(
            "Data Health recovery confirmation must exactly match "
            f"{DATA_HEALTH_RECOVERY_CONFIRMATION}."
        )
    with _maintenance_lock(paths, operation="data_health_recovery"):
        latest = source_root / "latest_refresh_status.json"
        before = inspect_refresh_receipt(status_path=latest)
        if before.load_status not in {CORRUPT, OVERSIZED} or not latest.is_file():
            raise LauncherError("Only an existing corrupt or oversized latest receipt is eligible.")
        if before.has_valid_backup:
            raise LauncherError(
                "A valid last-known-good backup exists; quarantine-only recovery is blocked "
                "pending an explicit recovery decision."
            )
        if before.backup_status != MISSING:
            raise LauncherError(
                "A secondary legacy receipt exists but is not valid; quarantine-only "
                "recovery requires a separate explicit decision."
            )
        valid_archives = []
        for candidate in _receipt_owned_files(source_root, require_latest=True):
            if candidate.parent == source_root and candidate != latest:
                candidate_result = inspect_refresh_receipt(status_path=candidate)
                if candidate_result.has_valid_latest:
                    valid_archives.append(candidate.name)
        if valid_archives:
            raise LauncherError(
                "A valid archived receipt exists; quarantine-only recovery is blocked "
                "pending an explicit recovery decision."
            )
        pre_recovery_fingerprint = _receipt_scope_fingerprint(source_root)
        latest_hash = sha256(latest)
        latest_bytes = latest.stat().st_size
        recovery_backup = create_data_health_recovery_backup(paths, source_root)
        validation = validate_data_health_recovery_backup(recovery_backup)
        if not validation["valid"]:
            raise LauncherError("Validated recovery backup is required before quarantine.")
        quarantine: Path | None = None
        try:
            quarantine = quarantine_invalid_refresh_receipt(status_path=latest, confirmed=True)
            if latest.exists() or not quarantine.is_file():
                raise LauncherError("Canonical quarantine did not produce the required state.")
            if quarantine.stat().st_size != latest_bytes or sha256(quarantine) != latest_hash:
                raise LauncherError(
                    "Quarantined receipt bytes do not match the preserved original."
                )
            after = inspect_refresh_receipt(status_path=latest)
            if after.load_status != MISSING or after.has_valid_backup:
                raise LauncherError(
                    "Data Health post-recovery state is not the expected no-receipt state."
                )
        except BaseException as exc:
            restored = restore_data_health_recovery_backup(recovery_backup, source_root)
            if (
                restored.stat().st_size != latest_bytes
                or sha256(restored) != latest_hash
                or _receipt_scope_fingerprint(source_root) != pre_recovery_fingerprint
            ):
                raise LauncherError("Data Health recovery rollback failed.") from exc
            raise LauncherError(
                "Data Health recovery verification failed; exact latest bytes were restored."
            ) from exc
        assert quarantine is not None
        return {
            "status": "QUARANTINED_NO_VALID_LKG",
            "receipt_root": str(source_root),
            "latest_status_before": before.load_status,
            "latest_status_after": after.load_status,
            "original_bytes": latest_bytes,
            "original_sha256": latest_hash,
            "recovery_backup": str(recovery_backup),
            "recovery_backup_files": validation["files"],
            "rollback_proof": True,
            "quarantine_path": str(quarantine),
            "source_refresh_executed": False,
        }


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


def _bounded_family_target(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or relative.anchor or relative.drive or relative.root:
        raise LauncherError("backup path must be strictly relative")
    if ".." in relative.parts:
        raise LauncherError("unsafe backup path")
    family_root = root.resolve()
    candidate = (family_root / relative).resolve()
    try:
        candidate.relative_to(family_root)
    except ValueError as exc:
        raise LauncherError("backup path escapes its approved family root") from exc
    return candidate


def validate_backup(snapshot: Path) -> dict[str, Any]:
    try:
        manifest = _json_document(snapshot / "MANIFEST.json")
        if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
            raise ValueError("unsupported backup manifest")
        allowed_families = {
            "draft_runtime",
            "development_lab",
            "saved_mock_drafts",
            "data_health_receipts",
        }
        seen: set[str] = set()
        for row in manifest["files"]:
            family = str(row["family"])
            if family not in allowed_families:
                raise ValueError("unsupported backup family")
            relative = Path(str(row["relative_path"]))
            family_root = snapshot / "payload" / family
            candidate = _bounded_family_target(family_root, relative)
            key = os.path.normcase(str(candidate))
            if key in seen:
                raise ValueError("duplicate backup path")
            seen.add(key)
            if not candidate.is_file() or sha256(candidate) != row["sha256"]:
                raise ValueError("backup hash mismatch")
            if family == "draft_runtime":
                if _json_document(candidate).get("schema_version") != "draft_day_runtime_v2":
                    raise ValueError("unsupported draft backup schema")
            elif family in {"development_lab", "saved_mock_drafts"}:
                if _json_document(candidate).get("schema_version") != 1:
                    raise ValueError("unsupported state backup schema")
        receipt_rows = [row for row in manifest["files"] if row["family"] == "data_health_receipts"]
        if receipt_rows:
            receipt_root = snapshot / "payload" / "data_health_receipts"
            latest = receipt_root / "latest_refresh_status.json"
            result = inspect_refresh_receipt(status_path=latest)
            if not result.has_valid_latest:
                raise ValueError("Data Health backup failed accepted receipt validation")
            backup_relative = Path("backups") / "latest_refresh_status.backup.json"
            if any(Path(str(row["relative_path"])) == backup_relative for row in receipt_rows):
                if not result.has_valid_backup:
                    raise ValueError("Data Health receipt backup failed accepted validation")
        return {
            "valid": True,
            "snapshot_id": manifest.get("snapshot_id"),
            "files": len(manifest["files"]),
        }
    except (LauncherError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
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
        target = _bounded_family_target(roots[row["family"]], Path(str(row["relative_path"])))
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
    attempted_targets: list[Path] = []
    try:
        for row in manifest["files"]:
            relative = Path(str(row["relative_path"]))
            source = _bounded_family_target(snapshot / "payload" / row["family"], relative)
            staged = _bounded_family_target(transaction / row["family"], relative)
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
            target = _bounded_family_target(roots[row["family"]], relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            attempted_targets.append(target)
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
        _restore_snapshot_without_backup(
            paths,
            str(pre_restore["snapshot_id"]),
            cleanup_targets=attempted_targets,
        )
        raise LauncherError(f"Restore rolled back after failure: {exc}") from exc
    finally:
        shutil.rmtree(transaction, ignore_errors=True)
    _prune_backups(paths.backup_root)
    return {"snapshot_id": snapshot_id, "restored": True, "changes": plan["changes"]}


def _restore_snapshot_without_backup(
    paths: LauncherPaths,
    snapshot_id: str,
    *,
    cleanup_targets: Iterable[Path] = (),
) -> None:
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
    desired_targets = {
        _bounded_family_target(roots[family], relative) for family, relative in desired
    }
    for target in cleanup_targets:
        resolved = target.resolve()
        if resolved not in desired_targets and target.is_file():
            target.unlink()
    current = validate_state(paths)
    if current.valid:
        for existing in current.files:
            family, relative = _family_for(existing, paths)
            if (family, relative) not in desired:
                existing.unlink()
    for row in manifest["files"]:
        relative = Path(str(row["relative_path"]))
        source = _bounded_family_target(snapshot / "payload" / row["family"], relative)
        target = _bounded_family_target(roots[row["family"]], relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        staged = target.with_name(f".{target.name}.rollback-{os.getpid()}")
        shutil.copy2(source, staged)
        if sha256(staged) != row["sha256"]:
            staged.unlink(missing_ok=True)
            raise LauncherError("Internal rollback staging hash mismatch.")
        staged.replace(target)
    final = validate_state(paths)
    expected = tuple(
        sorted(
            (f"{row['family']}/{row['relative_path']}", row["sha256"]) for row in manifest["files"]
        )
    )
    if not final.valid or state_fingerprint(paths) != expected:
        raise LauncherError("Internal rollback failed exact state validation.")


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


def _read_ownership(paths: LauncherPaths) -> dict[str, Any] | None:
    if not paths.lock_path.exists():
        return None
    try:
        record = _json_document(paths.lock_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise LauncherError(
            "Launcher ownership record is corrupt; evidence was preserved and no process "
            "was targeted."
        ) from exc
    required = {"launcher_version", "state", "repo_root", "data_root", "run_id", "port"}
    if (
        record.get("launcher_version") != LAUNCHER_VERSION
        or record.get("state") not in OWNERSHIP_STATES | {"STARTING", "MAINTENANCE"}
        or any(not record.get(field) for field in required)
    ):
        raise LauncherError(
            "Launcher ownership record is partial or unsupported; evidence was preserved and no "
            "process was targeted."
        )
    return record


def _write_ownership(
    paths: LauncherPaths,
    record: dict[str, Any],
    state: str,
    *,
    remaining: dict[str, Any] | None = None,
    cleanup_pending: list[str] | None = None,
) -> dict[str, Any]:
    if state not in OWNERSHIP_STATES:
        raise LauncherError(f"Unsupported launcher ownership state: {state}")
    updated = {
        **record,
        "state": state,
        "state_updated_at_utc": utc_timestamp(),
        "remaining_resources": remaining or {},
        "cleanup_pending": cleanup_pending or [],
    }
    _atomic_json(paths.lock_path, updated)
    return updated


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    staged.write_text(value, encoding="utf-8")
    staged.replace(path)


def _process_identity(pid: int) -> dict[str, Any] | None:
    if pid <= 0:
        return None
    if os.name != "nt":
        if not _pid_alive(pid):
            return None
        command_line = ""
        try:
            command_line = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(
                b"\0", b" "
            ).decode(errors="replace").strip()
        except OSError:
            if pid == os.getpid():
                command_line = subprocess.list2cmdline([sys.executable, *sys.argv])
        return {
            "pid": pid,
            "executable": str(Path(sys.executable).resolve()),
            "created": None,
            "command_line": command_line,
            "parent_pid": os.getppid() if pid == os.getpid() else None,
        }
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
        class UnicodeString(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ushort),
                ("maximum_length", ctypes.c_ushort),
                ("buffer", ctypes.c_void_p),
            ]

        required = ctypes.c_ulong()
        ctypes.windll.ntdll.NtQueryInformationProcess(
            handle, 60, None, 0, ctypes.byref(required)
        )
        if required.value <= ctypes.sizeof(UnicodeString):
            return None
        command_buffer = ctypes.create_string_buffer(required.value)
        status = ctypes.windll.ntdll.NtQueryInformationProcess(
            handle,
            60,
            command_buffer,
            required.value,
            ctypes.byref(required),
        )
        if status != 0:
            return None
        command = UnicodeString.from_buffer(command_buffer)
        command_line = ctypes.wstring_at(command.buffer, command.length // 2)
        return {
            "pid": pid,
            "executable": str(Path(buffer.value).resolve()),
            "created": created.value,
            "command_line": command_line,
            "parent_pid": _parent_pid(pid),
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
    try:
        pid = int(record.get(f"{prefix}_pid", 0))
    except (TypeError, ValueError):
        return False
    identity = _process_identity(pid)
    expected_executable = record.get(f"{prefix}_executable")
    expected_created = record.get(f"{prefix}_created")
    expected_command_line = record.get(f"{prefix}_command_line")
    return bool(
        identity
        and expected_executable
        and expected_command_line
        and os.path.normcase(str(Path(str(identity["executable"])).resolve()))
        == os.path.normcase(str(Path(str(expected_executable)).resolve()))
        and identity["created"] == expected_created
        and identity["command_line"] == expected_command_line
    )


def _identity_fields(prefix: str, identity: dict[str, Any]) -> dict[str, Any]:
    return {
        f"{prefix}_pid": identity["pid"],
        f"{prefix}_executable": identity["executable"],
        f"{prefix}_created": identity["created"],
        f"{prefix}_command_line": identity["command_line"],
        f"{prefix}_parent_pid": identity.get("parent_pid"),
    }


def _stored_identity_matches(expected: dict[str, Any]) -> bool:
    try:
        pid = int(expected.get("pid", 0))
    except (TypeError, ValueError):
        return False
    actual = _process_identity(pid)
    return bool(
        actual
        and expected.get("executable")
        and expected.get("command_line")
        and os.path.normcase(str(Path(str(actual["executable"])).resolve()))
        == os.path.normcase(str(Path(str(expected["executable"])).resolve()))
        and actual["created"] == expected.get("created")
        and actual["command_line"] == expected.get("command_line")
    )


def _process_parent_map() -> dict[int, int]:
    if os.name != "nt":
        result = subprocess.run(
            ["ps", "-eo", "pid=,ppid="],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        parents: dict[int, int] = {}
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) == 2:
                parents[int(fields[0])] = int(fields[1])
        return parents

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("size", ctypes.c_ulong),
            ("usage", ctypes.c_ulong),
            ("pid", ctypes.c_ulong),
            ("default_heap", ctypes.c_size_t),
            ("module_id", ctypes.c_ulong),
            ("threads", ctypes.c_ulong),
            ("parent_pid", ctypes.c_ulong),
            ("priority", ctypes.c_long),
            ("flags", ctypes.c_ulong),
            ("exe", ctypes.c_wchar * 260),
        ]

    snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return {}
    parents = {}
    try:
        entry = ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        present = ctypes.windll.kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while present:
            parents[int(entry.pid)] = int(entry.parent_pid)
            present = ctypes.windll.kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        ctypes.windll.kernel32.CloseHandle(snapshot)
    return parents


def _capture_descendants(root_pids: Iterable[int]) -> list[dict[str, Any]]:
    roots = {pid for pid in root_pids if pid > 0}
    parents = _process_parent_map()
    descendants: set[int] = set()
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if (
                pid not in roots
                and pid not in descendants
                and (parent in roots or parent in descendants)
            ):
                descendants.add(pid)
                changed = True
    identities = []
    for pid in sorted(descendants):
        identity = _process_identity(pid)
        if identity is not None:
            identities.append(identity)
    return identities


def _resource_snapshot(paths: LauncherPaths, record: dict[str, Any]) -> dict[str, Any]:
    owned: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    absent_registrations: list[str] = []
    for prefix in ("launcher", "streamlit"):
        try:
            pid = int(record.get(f"{prefix}_pid", 0))
        except (TypeError, ValueError):
            pid = 0
        if pid <= 0:
            if prefix == "launcher" or record.get("state") != "STARTING":
                conflicts.append({"resource": prefix, "status": "MISSING_IDENTITY"})
        elif _process_identity(pid) is None:
            pass
        elif _identity_matches(record, prefix):
            owned.append({"resource": prefix, "pid": pid})
        else:
            conflicts.append({"resource": prefix, "pid": pid, "status": "IDENTITY_MISMATCH"})

    listeners = _listener_pids()
    try:
        listener_pid = int(record.get("listener_pid", 0))
    except (TypeError, ValueError):
        listener_pid = 0
    if listener_pid in listeners:
        if _identity_matches(record, "listener"):
            owned.append({"resource": "listener", "pid": listener_pid})
        else:
            conflicts.append(
                {"resource": "listener", "pid": listener_pid, "status": "IDENTITY_MISMATCH"}
            )
    for pid in sorted(listeners - ({listener_pid} if listener_pid else set())):
        conflicts.append({"resource": "listener", "pid": pid, "status": "CHANGED_LISTENER"})

    for identity in record.get("verified_descendants", []):
        if not isinstance(identity, dict):
            conflicts.append({"resource": "descendant", "status": "PARTIAL_IDENTITY"})
            continue
        pid = int(identity.get("pid", 0))
        if _process_identity(pid) is None:
            continue
        if _stored_identity_matches(identity):
            owned.append({"resource": "descendant", "pid": pid})
        else:
            conflicts.append(
                {"resource": "descendant", "pid": pid, "status": "IDENTITY_MISMATCH"}
            )

    for registration in sorted(paths.run_root.glob("browser.*.json")):
        try:
            browser = _json_document(registration)
            pid = int(browser.get("browser_pid", 0))
            if pid <= 0:
                raise ValueError("invalid browser PID")
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            conflicts.append(
                {
                    "resource": "browser_registration",
                    "path": str(registration),
                    "status": "MALFORMED_PRESERVED",
                }
            )
            continue
        browser_descendants = browser.get("verified_descendants", [])
        descendant_conflict = False
        descendant_owned = []
        for identity in browser_descendants:
            if not isinstance(identity, dict):
                descendant_conflict = True
                continue
            descendant_pid = int(identity.get("pid", 0))
            if _process_identity(descendant_pid) is None:
                continue
            if _stored_identity_matches(identity):
                descendant_owned.append(descendant_pid)
            else:
                descendant_conflict = True
                conflicts.append(
                    {
                        "resource": "browser_descendant",
                        "pid": descendant_pid,
                        "status": "IDENTITY_MISMATCH",
                    }
                )
        if _process_identity(pid) is None:
            owned.extend(
                {"resource": "browser_descendant", "pid": descendant_pid}
                for descendant_pid in descendant_owned
            )
            if not descendant_owned and not descendant_conflict:
                absent_registrations.append(str(registration))
            continue
        expected_browser = Path(str(browser.get("expected_browser", ""))).resolve()
        approved_browsers = {candidate.resolve() for candidate in browser_candidates()}
        owned_browser = bool(
            browser.get("launcher_version") == LAUNCHER_VERSION
            and browser.get("run_id") == record.get("run_id")
            and Path(str(browser.get("data_root", ""))).resolve() == paths.data_home.resolve()
            and Path(str(browser.get("browser_profile", ""))).resolve()
            == paths.browser_profile.resolve()
            and Path(str(browser.get("repo_root", ""))).resolve() == paths.repo_root.resolve()
            and expected_browser in approved_browsers
            and _identity_matches(browser, "browser")
        )
        if owned_browser:
            owned.append({"resource": "browser", "pid": pid, "path": str(registration)})
            owned.extend(
                {"resource": "browser_descendant", "pid": descendant_pid}
                for descendant_pid in descendant_owned
            )
        else:
            conflicts.append(
                {
                    "resource": "browser",
                    "pid": pid,
                    "path": str(registration),
                    "status": "UNVERIFIED_PRESERVED",
                }
            )
    return {
        "owned": owned,
        "conflicts": conflicts,
        "absent_registrations": absent_registrations,
        "port_listeners": sorted(listeners),
    }


def _owned_healthy_instance(paths: LauncherPaths, lock: dict[str, Any]) -> bool:
    listener_pid = int(lock.get("listener_pid", 0))
    return bool(
        lock.get("state") == "RUNNING"
        and Path(str(lock.get("repo_root", ""))).resolve() == paths.repo_root.resolve()
        and Path(str(lock.get("data_root", ""))).resolve() == paths.data_home.resolve()
        and bool(lock.get("run_id"))
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
        **_identity_fields("launcher", identity),
        "repo_root": str(paths.repo_root),
        "data_root": str(paths.data_home),
        "app_commit": EXPECTED_APP_COMMIT,
        "port": PORT,
        "run_id": nonce,
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
            **_identity_fields("launcher", identity),
            "repo_root": str(paths.repo_root),
            "data_root": str(paths.data_home),
            "app_commit": EXPECTED_APP_COMMIT,
            "port": PORT,
            "run_id": (run_id := uuid.uuid4().hex),
            "lock_nonce": run_id,
            "started_at_utc": utc_timestamp(),
        }
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(initial, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        lock = _read_ownership(paths)
        if lock is None:
            raise LauncherError("Launcher ownership disappeared during lock acquisition.") from exc
        if _owned_healthy_instance(paths, lock):
            open_browser(paths)
            raise SystemExit(0) from exc
        if _identity_matches(lock, "launcher"):
            raise LauncherError(
                "A verified NWR launcher startup or shutdown is already in progress."
            ) from exc
        snapshot = _resource_snapshot(paths, lock)
        if snapshot["owned"] or snapshot["conflicts"]:
            raise LauncherError(
                "Launcher ownership requires recovery before another Start can proceed."
            ) from exc
        for registration in snapshot["absent_registrations"]:
            Path(registration).unlink(missing_ok=True)
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


def _browser_registration(paths: LauncherPaths, pid: int) -> Path:
    return paths.run_root / f"browser.{pid}.json"


def _reap_direct_browser_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5.0)
    if process.poll() is None:
        raise LauncherError("Directly created browser process did not stop.")


def _register_browser(paths: LauncherPaths, process: subprocess.Popen[Any], browser: Path) -> None:
    try:
        identity = _process_identity(process.pid)
        if identity is None:
            raise LauncherError("Could not establish launcher browser process identity.")
        ownership = _read_ownership(paths)
        if ownership is None:
            raise LauncherError(
                "Browser registration requires a durable launcher ownership record."
            )
        _atomic_json(
            _browser_registration(paths, process.pid),
            {
                "launcher_version": LAUNCHER_VERSION,
                **_identity_fields("browser", identity),
                "browser_profile": str(paths.browser_profile),
                "repo_root": str(paths.repo_root),
                "data_root": str(paths.data_home),
                "run_id": ownership["run_id"],
                "expected_browser": str(browser.resolve()),
            },
        )
    except BaseException:
        _reap_direct_browser_process(process)
        raise


def _shutdown_registered_browsers(
    paths: LauncherPaths, *, allow_force: bool = True
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    ownership = _read_ownership(paths)
    for registration in sorted(paths.run_root.glob("browser.*.json")):
        try:
            record = _json_document(registration)
            pid = int(record.get("browser_pid", 0))
            if pid <= 0:
                raise ValueError("invalid browser PID")
            expected_browser = Path(str(record.get("expected_browser", ""))).resolve()
            approved_browsers = {candidate.resolve() for candidate in browser_candidates()}
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            results.append(
                {
                    "status": "INVALID_REGISTRATION_PRESERVED",
                    "path": str(registration),
                    "detail": str(exc),
                }
            )
            continue
        stored_descendants = record.get("verified_descendants", [])
        if _process_identity(pid) is None:
            mismatched = [
                int(identity.get("pid", 0))
                for identity in stored_descendants
                if isinstance(identity, dict)
                and _process_identity(int(identity.get("pid", 0))) is not None
                and not _stored_identity_matches(identity)
            ]
            remaining = [
                identity
                for identity in stored_descendants
                if isinstance(identity, dict) and _stored_identity_matches(identity)
            ]
            if mismatched:
                results.append(
                    {
                        "pid": pid,
                        "status": "DESCENDANT_IDENTITY_CONFLICT_PRESERVED",
                        "conflicting_descendants": mismatched,
                    }
                )
                continue
            if remaining and allow_force:
                for identity in remaining:
                    descendant_record = _identity_fields("browser_descendant", identity)
                    _target_owned_tree(
                        descendant_record, "browser_descendant", allow_force=True
                    )
                remaining = [
                    identity for identity in remaining if _stored_identity_matches(identity)
                ]
            if remaining:
                results.append(
                    {
                        "pid": pid,
                        "status": "RECOVERY_REQUIRED",
                        "remaining_descendants": [int(item["pid"]) for item in remaining],
                    }
                )
                continue
            registration.unlink(missing_ok=True)
            results.append({"pid": pid, "status": "ALREADY_EXITED"})
            continue
        owned = bool(
            ownership
            and record.get("launcher_version") == LAUNCHER_VERSION
            and record.get("run_id") == ownership.get("run_id")
            and Path(str(record.get("data_root", ""))).resolve() == paths.data_home.resolve()
            and Path(str(record.get("browser_profile", ""))).resolve()
            == paths.browser_profile.resolve()
            and Path(str(record.get("repo_root", ""))).resolve() == paths.repo_root.resolve()
            and expected_browser in approved_browsers
            and Path(str(record.get("browser_executable", ""))).resolve() == expected_browser
            and _identity_matches(record, "browser")
        )
        if not owned:
            results.append({"pid": pid, "status": "STALE_OR_UNVERIFIED_PRESERVED"})
            continue
        descendants = _capture_descendants((pid,))
        record = {**record, "verified_descendants": descendants}
        _atomic_json(registration, record)
        result = subprocess.run(
            ["taskkill.exe", "/PID", str(pid), "/T"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
            creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
        )
        deadline = time.monotonic() + 5.0
        while _pid_alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        forced = False
        if _pid_alive(pid) and allow_force:
            if not _identity_matches(record, "browser"):
                results.append({"pid": pid, "status": "IDENTITY_CHANGED_BEFORE_FORCE"})
                continue
            forced = True
            subprocess.run(
                ["taskkill.exe", "/F", "/PID", str(pid), "/T"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
                check=False,
                creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
            )
        remaining_descendants = [
            int(identity["pid"]) for identity in descendants if _stored_identity_matches(identity)
        ]
        if _pid_alive(pid) or remaining_descendants:
            results.append(
                {
                    "pid": pid,
                    "status": "RECOVERY_REQUIRED",
                    "remaining_descendants": remaining_descendants,
                }
            )
            continue
        registration.unlink(missing_ok=True)
        results.append(
            {
                "pid": pid,
                "status": "STOPPED",
                "forced_cleanup": forced,
                "initial_exit_code": result.returncode,
            }
        )
    return results


def open_browser(paths: LauncherPaths) -> subprocess.Popen[Any] | None:
    if os.environ.get("NWR_LAUNCHER_NO_BROWSER") == "1":
        return None
    url = f"http://{HOST}:{PORT}/"
    for browser in browser_candidates():
        if browser.is_file():
            process = subprocess.Popen(
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
            _register_browser(paths, process, browser)
            return process
    os.startfile(url)  # type: ignore[attr-defined]
    return None


def start(paths: LauncherPaths) -> dict[str, Any]:
    ensure_directories(paths)
    verify_repository(paths)
    _acquire_lock(paths)
    try:
        stale_browser_cleanup = _shutdown_registered_browsers(paths)
    except BaseException:
        paths.lock_path.unlink(missing_ok=True)
        raise
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
    browser_cleanup: list[dict[str, Any]] = []
    try:
        process = start_streamlit(
            python,
            paths.repo_root,
            host=HOST,
            port=PORT,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
        )
        lock = _read_ownership(paths) or {}
        child_identity = _process_identity(process.pid)
        if child_identity is None:
            raise LauncherError("Could not establish Streamlit process identity.")
        lock = _write_ownership(
            paths,
            {**lock, **_identity_fields("streamlit", child_identity), "python": str(python)},
            "RUNNING",
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
        lock = _read_ownership(paths) or lock
        _atomic_json(
            paths.lock_path,
            {
                **lock,
                **_identity_fields("listener", listener_identity),
                "verified_descendants": _capture_descendants(
                    (int(lock["launcher_pid"]), process.pid)
                ),
            },
        )
        browser = open_browser(paths)
        while process.poll() is None:
            if paths.stop_request.exists() or (browser is not None and browser.poll() is not None):
                break
            time.sleep(0.25)
        shutdown = graceful_shutdown(process, timeout_seconds=SHUTDOWN_TIMEOUT_SECONDS)
        released = wait_for_port_release(HOST, PORT, timeout_seconds=5.0)
        browser_cleanup = _shutdown_registered_browsers(paths)
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
            "stale_browser_cleanup": stale_browser_cleanup,
            "browser_cleanup": browser_cleanup,
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
        try:
            browser_cleanup = _shutdown_registered_browsers(paths)
        except Exception as browser_exc:
            _append_launcher_log(paths, f"Browser cleanup failure: {browser_exc}")
        raise
    finally:
        os.environ.clear()
        os.environ.update(original_env)
        try:
            ownership = _read_ownership(paths)
            if ownership is not None and int(ownership.get("launcher_pid", 0)) == os.getpid():
                snapshot = _resource_snapshot(paths, ownership)
                non_launcher = [
                    resource
                    for resource in snapshot["owned"]
                    if resource.get("resource") != "launcher"
                ]
                if non_launcher or snapshot["conflicts"]:
                    _write_ownership(
                        paths,
                        ownership,
                        "RECOVERY_REQUIRED",
                        remaining={**snapshot, "owned": non_launcher},
                        cleanup_pending=["verified_resource_cleanup", "external_finalization"],
                    )
                else:
                    _write_ownership(
                        paths,
                        ownership,
                        "STOPPED",
                        cleanup_pending=["launcher_exit", "external_finalization"],
                    )
        except Exception as finalization_exc:
            _append_launcher_log(
                paths, f"Durable shutdown finalization failure: {finalization_exc}"
            )


def _acquire_stop_guard(paths: LauncherPaths) -> str:
    identity = _process_identity(os.getpid())
    if identity is None:
        raise LauncherError("Could not establish Stop command identity.")
    nonce = uuid.uuid4().hex
    payload = {
        "launcher_version": LAUNCHER_VERSION,
        "stop_nonce": nonce,
        **_identity_fields("stop", identity),
    }
    try:
        descriptor = os.open(paths.stop_guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        try:
            existing = _json_document(paths.stop_guard)
        except Exception as read_exc:
            raise LauncherError("Another Stop guard is unreadable; it was preserved.") from read_exc
        if _identity_matches(existing, "stop"):
            raise LauncherError("Another verified Stop command is already in progress.") from exc
        if _process_identity(int(existing.get("stop_pid", 0))) is not None:
            raise LauncherError("Stop guard identity conflict; no process was targeted.") from exc
        paths.stop_guard.unlink()
        return _acquire_stop_guard(paths)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.flush()
        os.fsync(handle.fileno())
    return nonce


def _release_stop_guard(paths: LauncherPaths, nonce: str) -> None:
    try:
        guard = _json_document(paths.stop_guard)
    except Exception:
        return
    if guard.get("stop_nonce") == nonce:
        paths.stop_guard.unlink(missing_ok=True)


def _target_owned_tree(
    record: dict[str, Any], prefix: str, *, allow_force: bool
) -> dict[str, Any]:
    pid = int(record.get(f"{prefix}_pid", 0))
    if _process_identity(pid) is None:
        return {"resource": prefix, "pid": pid, "status": "ALREADY_EXITED"}
    if not _identity_matches(record, prefix):
        raise LauncherError(f"{prefix} identity changed; unrelated PID {pid} was not targeted.")
    command = ["taskkill.exe", "/PID", str(pid), "/T"]
    result = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=10,
        check=False,
        creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
    )
    deadline = time.monotonic() + STOP_ESCALATION_SECONDS
    while _pid_alive(pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    forced = False
    if _pid_alive(pid) and allow_force:
        if not _identity_matches(record, prefix):
            raise LauncherError(
                f"{prefix} identity changed before escalation; PID {pid} was not forced."
            )
        forced = True
        subprocess.run(
            ["taskkill.exe", "/F", "/PID", str(pid), "/T"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
            creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
        )
    return {
        "resource": prefix,
        "pid": pid,
        "status": "STOPPED" if not _pid_alive(pid) else "RECOVERY_REQUIRED",
        "forced_cleanup": forced,
        "initial_exit_code": result.returncode,
    }


def _stop_snapshot_complete(snapshot: dict[str, Any]) -> bool:
    return not snapshot["owned"] and not snapshot["conflicts"]


def request_stop(paths: LauncherPaths) -> dict[str, Any]:
    ownership = _read_ownership(paths)
    if ownership is None:
        if port_is_listening(HOST, PORT) or any(paths.run_root.glob("browser.*.json")):
            raise LauncherError(
                "Launcher-owned resources cannot be proven without an ownership record; "
                "nothing was killed."
            )
        return {"status": "NOT_RUNNING", "port_released": True}
    if (
        Path(str(ownership.get("repo_root", ""))).resolve() != paths.repo_root.resolve()
        or Path(str(ownership.get("data_root", ""))).resolve() != paths.data_home.resolve()
        or int(ownership.get("port", 0)) != PORT
    ):
        raise LauncherError("Launcher ownership scope conflicts with this Stop command.")

    nonce = _acquire_stop_guard(paths)
    ready_to_delete = False
    final_payload: dict[str, Any] = {}
    try:
        ownership = _read_ownership(paths) or ownership
        if ownership.get("state") != "STOPPED":
            ownership = _write_ownership(paths, ownership, "STOP_REQUESTED")
        snapshot = _resource_snapshot(paths, ownership)
        if snapshot["conflicts"]:
            _write_ownership(
                paths,
                ownership,
                "RECOVERY_REQUIRED",
                remaining=snapshot,
                cleanup_pending=["ownership_conflict_review"],
            )
            raise LauncherError(
                "Ownership conflict blocked Stop; no unrelated process was targeted."
            )

        roots = [
            int(ownership.get(name, 0))
            for name in ("launcher_pid", "streamlit_pid")
            if int(ownership.get(name, 0)) > 0
        ]
        descendants = _capture_descendants(roots)
        ownership = _write_ownership(
            paths,
            {**ownership, "verified_descendants": descendants},
            "STOPPING",
            remaining=snapshot,
            cleanup_pending=["graceful_browser", "graceful_streamlit", "finalization"],
        )
        browser_results = _shutdown_registered_browsers(paths, allow_force=False)
        _atomic_text(paths.stop_request, utc_timestamp() + "\n")

        deadline = time.monotonic() + SHUTDOWN_TIMEOUT_SECONDS + 2
        while time.monotonic() < deadline:
            ownership = _read_ownership(paths) or ownership
            snapshot = _resource_snapshot(paths, ownership)
            if _stop_snapshot_complete(snapshot):
                break
            time.sleep(STOP_POLL_SECONDS)

        if not _stop_snapshot_complete(snapshot):
            ownership = _write_ownership(
                paths,
                ownership,
                "RECOVERY_REQUIRED",
                remaining=snapshot,
                cleanup_pending=["bounded_escalation", "finalization"],
            )
            browser_results.extend(_shutdown_registered_browsers(paths, allow_force=True))
            for prefix in ("streamlit", "launcher"):
                if int(ownership.get(f"{prefix}_pid", 0)) > 0:
                    _target_owned_tree(ownership, prefix, allow_force=True)
            deadline = time.monotonic() + STOP_ESCALATION_SECONDS
            while time.monotonic() < deadline:
                snapshot = _resource_snapshot(paths, ownership)
                if _stop_snapshot_complete(snapshot):
                    break
                time.sleep(STOP_POLL_SECONDS)

        if not _stop_snapshot_complete(snapshot):
            _write_ownership(
                paths,
                ownership,
                "RECOVERY_REQUIRED",
                remaining=snapshot,
                cleanup_pending=["verified_resource_cleanup", "finalization"],
            )
            raise LauncherError(
                "Stop failed with RECOVERY_REQUIRED; durable ownership and identity evidence "
                "remain."
            )

        for registration in snapshot["absent_registrations"]:
            Path(registration).unlink(missing_ok=True)
        ownership = _write_ownership(paths, ownership, "STOPPED")
        final_browser_results = [
            (
                {
                    **result,
                    "intermediate_status": result["status"],
                    "status": "STOPPED_AFTER_RECHECK",
                }
                if result.get("status") == "RECOVERY_REQUIRED"
                else result
            )
            for result in browser_results
        ]
        final_payload = {
            "status": "STOPPED",
            "completed_at_utc": utc_timestamp(),
            "run_id": ownership["run_id"],
            "port_released": not port_is_listening(HOST, PORT),
            "browser_cleanup": final_browser_results,
        }
        _atomic_json(paths.last_stop_receipt, final_payload)
        paths.stop_request.unlink(missing_ok=True)
        ready_to_delete = True
    finally:
        _release_stop_guard(paths, nonce)

    if ready_to_delete:
        try:
            paths.lock_path.unlink()
        except OSError as exc:
            current = _read_ownership(paths) or ownership
            _write_ownership(
                paths,
                current,
                "STOPPED",
                cleanup_pending=["ownership_record_deletion"],
            )
            raise LauncherError(
                "Shutdown completed, but ownership deletion failed; STOPPED evidence was retained."
            ) from exc
    return final_payload


def status(paths: LauncherPaths) -> dict[str, Any]:
    validation = validate_state(paths)
    ownership_error = ""
    try:
        lock = _read_ownership(paths)
    except LauncherError as exc:
        lock = None
        ownership_error = str(exc)
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
        "process_ownership": (
            "VERIFIED_RUNNING"
            if lock and _owned_healthy_instance(paths, lock)
            else (
                str(lock.get("state"))
                if lock
                else ("LOCK_PRESENT_UNVERIFIED" if paths.lock_path.exists() else "NONE")
            )
        ),
        "ownership_state": str(lock.get("state")) if lock else None,
        "ownership_error": ownership_error,
        "remaining_resources": lock.get("remaining_resources", {}) if lock else {},
        "state_validation": validation.status,
        "state_warnings": list(validation.warnings),
        "most_recent_backup": backup,
        "legacy_migration": asdict(inspect_legacy_migration(paths)),
        "junctions": junction_status(paths),
        "startup_command": list(
            build_streamlit_command(find_python(paths.repo_root), host=HOST, port=PORT)
        ),
    }


def installation_preflight(paths: LauncherPaths) -> dict[str, Any]:
    verify_repository(paths)
    validation = validate_state(paths)
    migration = inspect_legacy_migration(paths)
    junctions = junction_status(paths)
    blockers: list[str] = []
    if not validation.valid:
        blockers.append(f"persistent state is {validation.status}")
    if migration.status.startswith("BLOCKED_"):
        blockers.append(f"legacy migration is {migration.status}")
    for name, state in junctions.items():
        if state in {"WRONG_TARGET", "NON_JUNCTION_PATH"}:
            blockers.append(f"{name} junction is {state}")
    return {
        "ready": not blockers,
        "state_validation": validation.status,
        "legacy_migration": asdict(migration),
        "junctions": junctions,
        "blockers": blockers,
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
    sub.add_parser("installation-preflight")
    dry = sub.add_parser("restore-dry-run")
    dry.add_argument("snapshot_id")
    restore = sub.add_parser("restore")
    restore.add_argument("snapshot_id")
    restore.add_argument("--confirm", required=True)
    recovery = sub.add_parser("recover-data-health")
    recovery.add_argument("--confirm", required=True)
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
        elif args.command == "installation-preflight":
            payload = installation_preflight(paths)
            if not payload["ready"]:
                raise LauncherError(
                    "Installation preflight blocked: " + "; ".join(payload["blockers"])
                )
        elif args.command == "restore-dry-run":
            payload = restore_plan(paths, args.snapshot_id)
        elif args.command == "restore":
            payload = restore_backup(paths, args.snapshot_id, confirmation=args.confirm)
        elif args.command == "recover-data-health":
            ensure_directories(paths)
            payload = recover_corrupt_data_health_receipt(paths, confirmation=args.confirm)
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
