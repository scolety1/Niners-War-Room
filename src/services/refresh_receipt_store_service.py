from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

RECEIPT_SCHEMA_VERSION = 2
RECEIPT_MAX_BYTES = 2 * 1024 * 1024
RECEIPT_MAX_ARCHIVES = 20
RECEIPT_MAX_QUARANTINE = 5
RECEIPT_MAX_RESULTS = 256

LATEST_RECEIPT_NAME = "latest_refresh_status.json"
BACKUP_RECEIPT_NAME = "latest_refresh_status.backup.json"

VALID_LATEST = "VALID_LATEST"
VALID_BACKUP = "VALID_BACKUP"
MISSING = "MISSING"
CORRUPT = "CORRUPT"
OVERSIZED = "OVERSIZED"
UNSUPPORTED_SCHEMA = "UNSUPPORTED_SCHEMA"

CURRENT_RETAINED_DATA = "CURRENT_RETAINED_DATA"
STALE_RETAINED_DATA = "STALE_RETAINED_DATA"
NO_USABLE_RETAINED_DATA = "NO_USABLE_RETAINED_DATA"
NOT_ENOUGH_INFORMATION = "NOT_ENOUGH_INFORMATION"
RETAINED_DATA_STATES = frozenset(
    {
        CURRENT_RETAINED_DATA,
        STALE_RETAINED_DATA,
        NO_USABLE_RETAINED_DATA,
        NOT_ENOUGH_INFORMATION,
    }
)

LOADER_MODES = frozenset(
    {
        "QUICK_REFRESH",
        "FULL_SAFE_REFRESH",
        "CHECK_PROTECTED_ARTIFACTS",
        "MANUAL_SOURCES_CHECKLIST",
    }
)
OVERALL_STATUSES = frozenset({"GREEN", "YELLOW", "RED"})
ACTION_TYPES = frozenset(
    {
        "REFRESHED",
        "CHECK_ONLY",
        "SKIPPED_BY_POLICY",
        "NOT_CONFIGURED",
        "BLOCKED_MANUAL",
        "FAILED",
    }
)
RESULT_STATUSES = frozenset(
    {"GREEN", "YELLOW", "RED", "SKIPPED", "NOT_CONFIGURED", "BLOCKED"}
)
EXECUTION_STATUSES = frozenset(
    {
        "",
        "succeeded",
        "failed",
        "blocked_policy",
        "blocked_config",
        "skipped",
        "success",
        "partial",
        "partial_success",
    }
)
HEADLINE_STATUSES = frozenset(
    {
        "",
        "succeeded",
        "failed",
        "blocked_policy",
        "blocked_config",
        "stale",
        "review_only",
        "review",
        "skipped",
        "unknown",
        "partial",
        "partial_success",
        "current",
        "fresh",
        "PARTIAL",
        "PARTIAL_SUCCESS",
        "CURRENT",
        "FRESH",
        "STALE",
    }
)
FRESHNESS_STATUSES = frozenset(
    {
        "",
        "current",
        "fresh",
        "stale",
        "pass",
        "review",
        "fail",
        "unknown",
        "not_applicable",
        "CURRENT",
        "FRESH",
        "STALE",
        "PASS",
        "REVIEW",
        "FAIL",
        "UNKNOWN",
        "NOT_APPLICABLE",
    }
)
IDENTITY_EXCEPTIONS = frozenset({"", "UNRESOLVED_IDENTITY"})
SOURCE_EXCEPTIONS = frozenset({"", "SOURCE_CONTRACT_EXCEPTION"})
ERROR_CATEGORIES = frozenset(
    {
        "NONE",
        "PARTIAL_SUCCESS",
        "STALE_DATA",
        "SOURCE_SKIPPED",
        "SOURCE_UNAVAILABLE",
        "SOURCE_GATED",
        "REFRESH_FAILED",
        "NOT_ENOUGH_INFORMATION",
    }
)
ERROR_SUMMARIES = {
    "NONE": "Refresh completed with no recorded receipt error.",
    "PARTIAL_SUCCESS": "Refresh completed only partially; review approved diagnostics.",
    "STALE_DATA": "Retained data is explicitly stale and requires visible caution.",
    "SOURCE_SKIPPED": "Source was intentionally skipped by the approved refresh policy.",
    "SOURCE_UNAVAILABLE": "Source was unavailable or not configured for this refresh.",
    "SOURCE_GATED": "Source remained behind an approved manual or policy gate.",
    "REFRESH_FAILED": "Refresh failed; review the existing approved local diagnostic.",
    "NOT_ENOUGH_INFORMATION": "Receipt metadata cannot establish a more specific outcome.",
}

WRITE_INPUT_FIELDS = frozenset(
    {
        "run_id",
        "started_at_utc",
        "finished_at_utc",
        "loader_mode",
        "overall_status",
        "results",
    }
)
RESULT_INPUT_FIELDS = frozenset(
    {
        "source_id",
        "source_name",
        "dataset_id",
        "source_family",
        "action_type",
        "status",
        "refreshed",
        "execution_status",
        "headline_status",
        "freshness_status",
        "retained_data_status",
        "identity_exception",
        "source_exception",
        "source_as_of_utc",
    }
)
TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "receipt_id",
        "created_at_utc",
        "refresh_action_id",
        "run_id",
        "started_at_utc",
        "finished_at_utc",
        "loader_mode",
        "overall_status",
        "status_path",
        "outcome_summary",
        "lifecycle",
        "results",
        "integrity",
    }
)
RESULT_FIELDS = frozenset(
    {
        "source_id",
        "source_name",
        "dataset_id",
        "source_family",
        "action_type",
        "status",
        "refreshed",
        "execution_status",
        "headline_status",
        "freshness_status",
        "retained_data_status",
        "latest_successful_receipt_id",
        "last_known_good_receipt_id",
        "identity_exception",
        "source_exception",
        "error_category",
        "error_summary",
        "source_as_of_utc",
    }
)
OUTCOME_FIELDS = frozenset(
    {"successful_refresh_results", "incomplete_or_non_refresh_results"}
)
LIFECYCLE_FIELDS = frozenset(
    {
        "storage_boundary",
        "latest_attempt_receipt_id",
        "last_known_good_relationship",
        "archive_retention",
        "quarantine_retention",
    }
)
INTEGRITY_FIELDS = frozenset({"algorithm", "digest"})

_RECEIPT_ID = re.compile(r"rr_[0-9a-f]{24}\Z")
_OPAQUE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z")
_SUBJECT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_FAMILY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z")
_UTC_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)\Z"
)
_WINDOWS_ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|\\\\)")
_SENSITIVE_TEXT = re.compile(
    r"(?i)(?:authorization|bearer\s+[A-Za-z0-9._~+/=-]+|api[ _-]?key|"
    r"access[ _-]?token|refresh[ _-]?token|cookie|session[ _-]?id|password|"
    r"credential|client[ _-]?secret|raw[ _-]?headers?|provider[ _-]?(?:payload|response)|"
    r"stack[ _-]?trace|traceback\s*\(most recent call last\))"
)


class DuplicateReceiptKeyError(ValueError):
    pass


@dataclass(frozen=True)
class RefreshReceiptLoadResult:
    load_status: str
    latest_path: Path
    latest_receipt: dict[str, Any] | None = None
    backup_status: str = MISSING
    backup_receipt: dict[str, Any] | None = None
    quarantine_path: Path | None = None
    detail: str = ""
    automatic_mutation_performed: bool = False
    maintenance_required: bool = False

    @property
    def has_valid_latest(self) -> bool:
        return self.load_status == VALID_LATEST and self.latest_receipt is not None

    @property
    def has_valid_backup(self) -> bool:
        return self.backup_status == VALID_BACKUP and self.backup_receipt is not None


@dataclass(frozen=True)
class RefreshReceiptWriteResult:
    committed: bool
    latest_path: Path
    archive_path: Path
    backup_path: Path | None
    quarantine_path: Path | None
    receipt_id: str
    serialized_bytes: int


@dataclass(frozen=True)
class _ValidationResult:
    status: str
    payload: dict[str, Any] | None = None
    detail: str = ""


@dataclass(frozen=True)
class _FileSnapshot:
    existed: bool
    body: bytes = b""
    atime_ns: int = 0
    mtime_ns: int = 0


def write_refresh_receipt(
    payload: dict[str, Any],
    *,
    status_root: Path,
    created_at_utc: str | None = None,
) -> RefreshReceiptWriteResult:
    """Validate a closed candidate completely, then commit the local receipt transaction."""
    created_at = created_at_utc or _utc_now()

    # First preflight is intentionally independent of existing durable state.
    provisional = _build_receipt(payload, prior_receipt=None, created_at_utc=created_at)
    _finalize_candidate(provisional)

    latest_path = status_root / LATEST_RECEIPT_NAME
    backup_path = _backup_path(latest_path)
    previous = _validate_receipt_path(latest_path)
    backup = _validate_receipt_path(backup_path)
    prior_receipt = previous.payload if previous.status == VALID_LATEST else backup.payload

    receipt = _build_receipt(
        payload,
        prior_receipt=prior_receipt,
        created_at_utc=created_at,
    )
    receipt, serialized = _finalize_candidate(receipt)
    archive_path = status_root / _archive_name(receipt)

    backup_target = backup_path if previous.status == VALID_LATEST else None
    quarantine_target = (
        _quarantine_target(latest_path, status=previous.status)
        if previous.status in {CORRUPT, OVERSIZED} and latest_path.exists()
        else None
    )
    target_bodies: list[tuple[Path, bytes]] = []
    if backup_target is not None:
        target_bodies.append((backup_target, _serialized_receipt_bytes(previous.payload or {})))
    target_bodies.append((archive_path, serialized))
    if quarantine_target is not None:
        target_bodies.append((quarantine_target, latest_path.read_bytes()))
    target_bodies.append((latest_path, serialized))

    snapshots = {target: _snapshot(target) for target, _ in target_bodies}
    prune_targets = _transaction_prune_targets(
        status_root,
        archive_path=archive_path,
        quarantine_path=quarantine_target,
    )
    snapshots.update({target: _snapshot(target) for target in prune_targets})
    staged: dict[Path, Path] = {}
    created_dirs: list[Path] = []
    try:
        for target, body in target_bodies:
            _ensure_parent(target.parent, created_dirs=created_dirs)
            staged[target] = _stage_bytes(target, body)
        for target, _ in target_bodies:
            _replace_file(staged[target], target)
        for target in prune_targets:
            target.unlink()
    except Exception:
        _rollback_targets(snapshots)
        raise
    finally:
        for temp_path in staged.values():
            temp_path.unlink(missing_ok=True)
        _remove_empty_created_dirs(created_dirs)

    return RefreshReceiptWriteResult(
        committed=True,
        latest_path=latest_path,
        archive_path=archive_path,
        backup_path=backup_target,
        quarantine_path=quarantine_target,
        receipt_id=str(receipt["receipt_id"]),
        serialized_bytes=len(serialized),
    )


def inspect_refresh_receipt(*, status_path: Path) -> RefreshReceiptLoadResult:
    """Inspect latest and backup bytes without any filesystem mutation."""
    latest = _validate_receipt_path(status_path)
    backup = _validate_receipt_path(_backup_path(status_path))
    return RefreshReceiptLoadResult(
        load_status=latest.status,
        latest_path=status_path,
        latest_receipt=latest.payload if latest.status == VALID_LATEST else None,
        backup_status=VALID_BACKUP if backup.status == VALID_LATEST else backup.status,
        backup_receipt=backup.payload if backup.status == VALID_LATEST else None,
        detail=latest.detail or _load_detail(latest.status),
        automatic_mutation_performed=False,
        maintenance_required=latest.status not in {VALID_LATEST, MISSING},
    )


def load_refresh_receipt(*, status_path: Path) -> RefreshReceiptLoadResult:
    """Compatibility name for the strictly read-only receipt inspection path."""
    return inspect_refresh_receipt(status_path=status_path)


def quarantine_invalid_refresh_receipt(
    *, status_path: Path, confirmed: bool = False
) -> Path:
    """Explicitly quarantine corrupt/oversized latest bytes after user confirmation."""
    if not confirmed:
        raise PermissionError("Receipt quarantine requires explicit confirmation.")
    validation = _validate_receipt_path(status_path)
    if validation.status not in {CORRUPT, OVERSIZED} or not status_path.exists():
        raise ValueError("Only an existing corrupt or oversized receipt can be quarantined.")
    target = _quarantine_receipt(status_path, status=validation.status)
    _prune_quarantine(status_path.parent)
    return target


def _build_receipt(
    payload: dict[str, Any],
    *,
    prior_receipt: dict[str, Any] | None,
    created_at_utc: str,
) -> dict[str, Any]:
    _validate_write_input(payload, created_at_utc=created_at_utc)
    base_results = [_project_result(row) for row in payload["results"]]
    receipt_id = _receipt_id(payload, base_results=base_results)
    results = _decorate_results(
        base_results,
        receipt_id=receipt_id,
        prior_receipt=prior_receipt,
    )
    success_count = sum(_is_success(row) for row in results)
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "created_at_utc": created_at_utc,
        "refresh_action_id": payload["run_id"],
        "run_id": payload["run_id"],
        "started_at_utc": payload["started_at_utc"],
        "finished_at_utc": payload["finished_at_utc"],
        "loader_mode": payload["loader_mode"],
        "overall_status": payload["overall_status"],
        "status_path": f"local_exports/refresh_data/{LATEST_RECEIPT_NAME}",
        "outcome_summary": {
            "successful_refresh_results": success_count,
            "incomplete_or_non_refresh_results": len(results) - success_count,
        },
        "lifecycle": {
            "storage_boundary": "local_exports/refresh_data",
            "latest_attempt_receipt_id": receipt_id,
            "last_known_good_relationship": "per_source_explicit_retention_only",
            "archive_retention": RECEIPT_MAX_ARCHIVES,
            "quarantine_retention": RECEIPT_MAX_QUARANTINE,
        },
        "results": results,
    }


def _validate_write_input(payload: Any, *, created_at_utc: Any) -> None:
    if type(payload) is not dict:
        raise ValueError("Refresh receipt input must be an exact mapping.")
    _require_exact_keys(payload, WRITE_INPUT_FIELDS, context="receipt input")
    _require_opaque_id(payload.get("run_id"), field="run_id")
    _require_timestamp(payload.get("started_at_utc"), field="started_at_utc")
    _require_timestamp(payload.get("finished_at_utc"), field="finished_at_utc")
    _require_timestamp(created_at_utc, field="created_at_utc")
    if payload.get("loader_mode") not in LOADER_MODES:
        raise ValueError("Receipt loader_mode is unsupported.")
    if payload.get("overall_status") not in OVERALL_STATUSES:
        raise ValueError("Receipt overall_status is unsupported.")
    if _parse_timestamp(payload["finished_at_utc"]) < _parse_timestamp(
        payload["started_at_utc"]
    ):
        raise ValueError("Receipt finished_at_utc precedes started_at_utc.")
    rows = payload.get("results")
    if type(rows) is not list or not 1 <= len(rows) <= RECEIPT_MAX_RESULTS:
        raise ValueError("Refresh receipt requires 1-256 result rows.")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError(f"Receipt result {index} must be an exact mapping.")
        unknown = set(row) - RESULT_INPUT_FIELDS
        if unknown:
            raise ValueError(f"Receipt result {index} has unknown keys: {sorted(unknown)}")
        for key, value in row.items():
            if type(value) in {dict, list, tuple, set}:
                raise ValueError(
                    f"Receipt result {index} field {key} contains unauthorized nested content."
                )


def _project_result(row: dict[str, Any]) -> dict[str, Any]:
    source_id = _require_identifier(row.get("source_id"), field="source_id", allow_empty=False)
    source_name = _require_text(row.get("source_name"), field="source_name", minimum=1, maximum=160)
    dataset_id = _require_identifier(
        row.get("dataset_id", ""), field="dataset_id", allow_empty=True
    )
    source_family = _require_family(row.get("source_family", ""), field="source_family")
    action_type = _require_enum(row.get("action_type"), ACTION_TYPES, field="action_type")
    status = _require_enum(row.get("status"), RESULT_STATUSES, field="status")
    refreshed = row.get("refreshed")
    if type(refreshed) is not bool:
        raise ValueError("Receipt result refreshed must be a JSON boolean.")
    if refreshed != (action_type == "REFRESHED"):
        raise ValueError("Result refreshed and action_type REFRESHED must agree exactly.")
    execution = _require_enum(
        row.get("execution_status", ""), EXECUTION_STATUSES, field="execution_status"
    )
    headline = _require_enum(
        row.get("headline_status", ""), HEADLINE_STATUSES, field="headline_status"
    )
    freshness = _require_enum(
        row.get("freshness_status", ""), FRESHNESS_STATUSES, field="freshness_status"
    )
    identity_exception = _require_enum(
        row.get("identity_exception", ""),
        IDENTITY_EXCEPTIONS,
        field="identity_exception",
    )
    source_exception = _require_enum(
        row.get("source_exception", ""), SOURCE_EXCEPTIONS, field="source_exception"
    )
    explicit_retained = row.get("retained_data_status")
    if explicit_retained is not None and explicit_retained not in RETAINED_DATA_STATES:
        raise ValueError("Receipt retained_data_status is unsupported.")
    source_as_of = row.get("source_as_of_utc")
    if source_as_of is not None:
        _require_timestamp(source_as_of, field="source_as_of_utc")

    category = _error_category(
        action_type=action_type,
        status=status,
        execution_status=execution,
        headline_status=headline,
        freshness_status=freshness,
    )
    projected = {
        "source_id": source_id,
        "source_name": source_name,
        "dataset_id": dataset_id,
        "source_family": source_family,
        "action_type": action_type,
        "status": status,
        "refreshed": refreshed,
        "execution_status": execution,
        "headline_status": headline,
        "freshness_status": freshness,
        "retained_data_status": (
            explicit_retained
            or _retained_data_status(
                freshness_status=freshness,
                headline_status=headline,
                success=_is_success(
                    {"refreshed": refreshed, "action_type": action_type, "status": status}
                ),
            )
        ),
        "latest_successful_receipt_id": "",
        "last_known_good_receipt_id": "",
        "identity_exception": identity_exception,
        "source_exception": source_exception,
        "error_category": category,
        "error_summary": ERROR_SUMMARIES[category],
        "source_as_of_utc": source_as_of,
    }
    _validate_privacy(projected)
    return projected


def _decorate_results(
    rows: list[dict[str, Any]],
    *,
    receipt_id: str,
    prior_receipt: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    prior_id = str((prior_receipt or {}).get("receipt_id") or "")
    prior_rows = {
        _subject_key(row): row
        for row in (prior_receipt or {}).get("results", [])
        if type(row) is dict and _subject_key(row)[0]
    }
    decorated: list[dict[str, Any]] = []
    for original in rows:
        row = dict(original)
        success = _is_success(row)
        prior_row = prior_rows.get(_subject_key(row))
        prior_success = bool(prior_id and prior_row and _is_success(prior_row))
        retained = row["retained_data_status"]
        row["latest_successful_receipt_id"] = (
            receipt_id if success else prior_id if prior_success else ""
        )
        row["last_known_good_receipt_id"] = (
            prior_id
            if prior_success
            and not success
            and retained in {CURRENT_RETAINED_DATA, STALE_RETAINED_DATA}
            else ""
        )
        decorated.append(row)
    return decorated


def _finalize_candidate(receipt: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    validation = _validate_receipt_document(receipt, require_integrity=False)
    if validation.status != VALID_LATEST:
        raise ValueError(f"Generated refresh receipt failed validation: {validation.detail}")
    finalized = dict(receipt)
    finalized["integrity"] = {
        "algorithm": "sha256",
        "digest": _integrity_digest(finalized),
    }
    validation = _validate_receipt_document(finalized, require_integrity=True)
    if validation.status != VALID_LATEST:
        raise ValueError(f"Generated refresh receipt failed validation: {validation.detail}")
    serialized = _serialized_receipt_bytes(finalized)
    if len(serialized) > RECEIPT_MAX_BYTES:
        raise ValueError("Generated refresh receipt exceeds the 2 MiB bound.")
    return finalized, serialized


def _validate_receipt_path(path: Path) -> _ValidationResult:
    if not path.exists():
        return _ValidationResult(MISSING, detail="Receipt file is missing.")
    try:
        if path.stat().st_size > RECEIPT_MAX_BYTES:
            return _ValidationResult(OVERSIZED, detail="Receipt exceeds the 2 MiB bound.")
        raw = path.read_bytes().decode("utf-8")
        payload = json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateReceiptKeyError) as exc:
        return _ValidationResult(CORRUPT, detail=f"Unreadable receipt: {type(exc).__name__}.")
    return _validate_receipt_document(payload, require_integrity=True)


def _validate_receipt_document(
    payload: Any, *, require_integrity: bool = True
) -> _ValidationResult:
    try:
        if type(payload) is not dict:
            raise ValueError("Receipt root must be an object.")
        schema_version = payload.get("schema_version")
        if type(schema_version) is int and schema_version != RECEIPT_SCHEMA_VERSION:
            return _ValidationResult(
                UNSUPPORTED_SCHEMA,
                detail="Receipt schema is missing or unsupported.",
            )
        expected_top = TOP_LEVEL_FIELDS if require_integrity else TOP_LEVEL_FIELDS - {"integrity"}
        _require_exact_keys(payload, expected_top, context="receipt")
        if type(schema_version) is not int:
            raise ValueError("Receipt schema_version must be an integer.")
        _require_receipt_id(payload.get("receipt_id"), field="receipt_id")
        _require_timestamp(payload.get("created_at_utc"), field="created_at_utc")
        _require_opaque_id(payload.get("refresh_action_id"), field="refresh_action_id")
        _require_opaque_id(payload.get("run_id"), field="run_id")
        if payload["refresh_action_id"] != payload["run_id"]:
            raise ValueError("Receipt action and run IDs must match.")
        _require_timestamp(payload.get("started_at_utc"), field="started_at_utc")
        _require_timestamp(payload.get("finished_at_utc"), field="finished_at_utc")
        if _parse_timestamp(payload["finished_at_utc"]) < _parse_timestamp(
            payload["started_at_utc"]
        ):
            raise ValueError("Receipt finish timestamp precedes start timestamp.")
        _require_enum(payload.get("loader_mode"), LOADER_MODES, field="loader_mode")
        _require_enum(payload.get("overall_status"), OVERALL_STATUSES, field="overall_status")
        if payload.get("status_path") != f"local_exports/refresh_data/{LATEST_RECEIPT_NAME}":
            raise ValueError("Receipt status_path is invalid.")

        results = payload.get("results")
        if type(results) is not list or not 1 <= len(results) <= RECEIPT_MAX_RESULTS:
            raise ValueError("Receipt results must contain 1-256 rows.")
        seen: set[tuple[str, str]] = set()
        for row in results:
            _validate_result_document(row)
            subject = _subject_key(row)
            if subject in seen:
                raise ValueError("Receipt source/dataset pairs must be unique.")
            seen.add(subject)

        outcome = payload.get("outcome_summary")
        if type(outcome) is not dict:
            raise ValueError("Receipt outcome_summary must be an object.")
        _require_exact_keys(outcome, OUTCOME_FIELDS, context="outcome_summary")
        for key in OUTCOME_FIELDS:
            if type(outcome.get(key)) is not int or not 0 <= outcome[key] <= RECEIPT_MAX_RESULTS:
                raise ValueError(f"Receipt outcome count {key} is invalid.")
        expected_success = sum(_is_success(row) for row in results)
        if outcome["successful_refresh_results"] != expected_success:
            raise ValueError("Receipt success count does not match results.")
        if sum(outcome.values()) != len(results):
            raise ValueError("Receipt outcome counts do not match results.")

        lifecycle = payload.get("lifecycle")
        if type(lifecycle) is not dict:
            raise ValueError("Receipt lifecycle must be an object.")
        _require_exact_keys(lifecycle, LIFECYCLE_FIELDS, context="lifecycle")
        if lifecycle.get("storage_boundary") != "local_exports/refresh_data":
            raise ValueError("Receipt storage boundary is invalid.")
        if lifecycle.get("latest_attempt_receipt_id") != payload["receipt_id"]:
            raise ValueError("Receipt lifecycle ID is invalid.")
        if lifecycle.get("last_known_good_relationship") != (
            "per_source_explicit_retention_only"
        ):
            raise ValueError("Receipt LKG relationship is invalid.")
        if type(lifecycle.get("archive_retention")) is not int or (
            lifecycle["archive_retention"] != RECEIPT_MAX_ARCHIVES
        ):
            raise ValueError("Receipt archive retention is invalid.")
        if type(lifecycle.get("quarantine_retention")) is not int or (
            lifecycle["quarantine_retention"] != RECEIPT_MAX_QUARANTINE
        ):
            raise ValueError("Receipt quarantine retention is invalid.")

        _validate_privacy(payload)
        if require_integrity:
            integrity = payload.get("integrity")
            if type(integrity) is not dict:
                raise ValueError("Receipt integrity metadata must be an object.")
            _require_exact_keys(integrity, INTEGRITY_FIELDS, context="integrity")
            if integrity.get("algorithm") != "sha256":
                raise ValueError("Receipt integrity algorithm is invalid.")
            expected = integrity.get("digest")
            if type(expected) is not str or not re.fullmatch(r"[0-9a-f]{64}", expected):
                raise ValueError("Receipt integrity digest is invalid.")
            if not hmac.compare_digest(expected, _integrity_digest(payload)):
                raise ValueError("Receipt integrity check failed.")
    except ValueError as exc:
        return _ValidationResult(CORRUPT, detail=str(exc))
    return _ValidationResult(VALID_LATEST, payload=payload)


def _validate_result_document(row: Any) -> None:
    if type(row) is not dict:
        raise ValueError("Receipt result row must be an object.")
    _require_exact_keys(row, RESULT_FIELDS, context="result")
    _require_identifier(row.get("source_id"), field="source_id", allow_empty=False)
    _require_text(row.get("source_name"), field="source_name", minimum=1, maximum=160)
    _require_identifier(row.get("dataset_id"), field="dataset_id", allow_empty=True)
    _require_family(row.get("source_family"), field="source_family")
    _require_enum(row.get("action_type"), ACTION_TYPES, field="action_type")
    _require_enum(row.get("status"), RESULT_STATUSES, field="status")
    if type(row.get("refreshed")) is not bool:
        raise ValueError("Receipt result refreshed must be a JSON boolean.")
    if row["refreshed"] != (row["action_type"] == "REFRESHED"):
        raise ValueError("Result refreshed and action_type REFRESHED must agree exactly.")
    _require_enum(row.get("execution_status"), EXECUTION_STATUSES, field="execution_status")
    _require_enum(row.get("headline_status"), HEADLINE_STATUSES, field="headline_status")
    _require_enum(row.get("freshness_status"), FRESHNESS_STATUSES, field="freshness_status")
    _require_enum(
        row.get("retained_data_status"), RETAINED_DATA_STATES, field="retained_data_status"
    )
    for key in ("latest_successful_receipt_id", "last_known_good_receipt_id"):
        value = row.get(key)
        if value != "":
            _require_receipt_id(value, field=key)
    _require_enum(
        row.get("identity_exception"), IDENTITY_EXCEPTIONS, field="identity_exception"
    )
    _require_enum(row.get("source_exception"), SOURCE_EXCEPTIONS, field="source_exception")
    category = _require_enum(
        row.get("error_category"), ERROR_CATEGORIES, field="error_category"
    )
    if row.get("error_summary") != ERROR_SUMMARIES[category]:
        raise ValueError("Receipt error summary is not the approved category text.")
    _require_text(row.get("error_summary"), field="error_summary", minimum=1, maximum=192)
    source_as_of = row.get("source_as_of_utc")
    if source_as_of is not None:
        _require_timestamp(source_as_of, field="source_as_of_utc")


def _receipt_id(payload: dict[str, Any], *, base_results: list[dict[str, Any]]) -> str:
    identity = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "run_id": payload["run_id"],
        "started_at_utc": payload["started_at_utc"],
        "finished_at_utc": payload["finished_at_utc"],
        "loader_mode": payload["loader_mode"],
        "overall_status": payload["overall_status"],
        "results": base_results,
    }
    return f"rr_{hashlib.sha256(_canonical_bytes(identity)).hexdigest()[:24]}"


def _integrity_digest(payload: dict[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if key != "integrity"}
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _serialized_receipt_bytes(payload: dict[str, Any]) -> bytes:
    return _canonical_bytes(payload) + b"\n"


def _snapshot(path: Path) -> _FileSnapshot:
    if not path.exists():
        return _FileSnapshot(False)
    stat = path.stat()
    return _FileSnapshot(
        True,
        body=path.read_bytes(),
        atime_ns=stat.st_atime_ns,
        mtime_ns=stat.st_mtime_ns,
    )


def _ensure_parent(path: Path, *, created_dirs: list[Path]) -> None:
    missing: list[Path] = []
    candidate = path
    while not candidate.exists():
        missing.append(candidate)
        candidate = candidate.parent
    path.mkdir(parents=True, exist_ok=True)
    created_dirs.extend(reversed(missing))


def _stage_bytes(target: Path, body: bytes) -> Path:
    temp_path = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        with temp_path.open("xb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def _replace_file(source: Path, target: Path) -> None:
    os.replace(source, target)


def _rollback_targets(snapshots: dict[Path, _FileSnapshot]) -> None:
    failures: list[str] = []
    for target, snapshot in reversed(tuple(snapshots.items())):
        try:
            if not snapshot.existed:
                target.unlink(missing_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temp_path = target.with_name(f".{target.name}.{uuid4().hex}.rollback.tmp")
            try:
                with temp_path.open("xb") as handle:
                    handle.write(snapshot.body)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_path, target)
                os.utime(target, ns=(snapshot.atime_ns, snapshot.mtime_ns))
            finally:
                temp_path.unlink(missing_ok=True)
        except OSError as exc:
            failures.append(f"{target}: {exc}")
    if failures:
        raise RuntimeError("Receipt rollback failed: " + "; ".join(failures))


def _remove_empty_created_dirs(created_dirs: list[Path]) -> None:
    for path in reversed(created_dirs):
        try:
            path.rmdir()
        except OSError:
            pass


def _quarantine_receipt(path: Path, *, status: str) -> Path:
    target = _quarantine_target(path, status=status)
    target.parent.mkdir(parents=True, exist_ok=True)
    os.replace(path, target)
    return target


def _quarantine_target(path: Path, *, status: str) -> Path:
    return path.parent / "quarantine" / (
        f"{path.stem}.{_filename_timestamp()}.{status.lower()}.{uuid4().hex[:8]}.json"
    )


def _prune_archives(status_root: Path) -> None:
    archives = sorted(
        (
            path
            for path in status_root.glob("*_status.json")
            if path.name != LATEST_RECEIPT_NAME and path.name[:1].isdigit()
        ),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    for path in archives[RECEIPT_MAX_ARCHIVES:]:
        path.unlink()


def _transaction_prune_targets(
    status_root: Path,
    *,
    archive_path: Path,
    quarantine_path: Path | None,
) -> tuple[Path, ...]:
    archives = sorted(
        (
            path
            for path in status_root.glob("*_status.json")
            if path.name != LATEST_RECEIPT_NAME
            and path.name[:1].isdigit()
            and path != archive_path
        ),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    archive_prune = archives[max(RECEIPT_MAX_ARCHIVES - 1, 0) :]
    quarantine_prune: list[Path] = []
    quarantine_dir = status_root / "quarantine"
    if quarantine_dir.exists():
        quarantine = sorted(
            (
                path
                for path in quarantine_dir.glob("*.json")
                if path != quarantine_path
            ),
            key=lambda path: (path.stat().st_mtime_ns, path.name),
            reverse=True,
        )
        keep = RECEIPT_MAX_QUARANTINE - (1 if quarantine_path is not None else 0)
        quarantine_prune = quarantine[max(keep, 0) :]
    return tuple((*archive_prune, *quarantine_prune))


def _prune_quarantine(status_root: Path) -> None:
    quarantine_dir = status_root / "quarantine"
    if not quarantine_dir.exists():
        return
    files = sorted(
        quarantine_dir.glob("*.json"),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
        reverse=True,
    )
    for path in files[RECEIPT_MAX_QUARANTINE:]:
        path.unlink()


def _backup_path(latest_path: Path) -> Path:
    return latest_path.parent / "backups" / BACKUP_RECEIPT_NAME


def _archive_name(receipt: dict[str, Any]) -> str:
    return f"{receipt['run_id']}_{str(receipt['loader_mode']).lower()}_status.json"


def _subject_key(row: dict[str, Any]) -> tuple[str, str]:
    return (row.get("source_id", ""), row.get("dataset_id", ""))


def _is_success(row: dict[str, Any]) -> bool:
    return (
        row.get("refreshed") is True
        and row.get("action_type") == "REFRESHED"
        and row.get("status") == "GREEN"
    )


def _retained_data_status(
    *, freshness_status: str, headline_status: str, success: bool
) -> str:
    freshness_values = {freshness_status.upper(), headline_status.upper()}
    if "STALE" in freshness_values:
        return STALE_RETAINED_DATA
    if success and freshness_values.intersection({"CURRENT", "FRESH", "PASS", "SUCCEEDED"}):
        return CURRENT_RETAINED_DATA
    return NOT_ENOUGH_INFORMATION


def _error_category(
    *,
    action_type: str,
    status: str,
    execution_status: str,
    headline_status: str,
    freshness_status: str,
) -> str:
    values = {
        "action": action_type.upper(),
        "status": status.upper(),
        "execution": execution_status.upper(),
        "headline": headline_status.upper(),
        "freshness": freshness_status.upper(),
    }
    if values["action"] == "BLOCKED_MANUAL" or values["status"] == "BLOCKED" or (
        values["execution"] == "BLOCKED_POLICY"
    ):
        return "SOURCE_GATED"
    if values["action"] == "SKIPPED_BY_POLICY" or values["status"] == "SKIPPED":
        return "SOURCE_SKIPPED"
    if values["action"] == "NOT_CONFIGURED" or values["status"] == "NOT_CONFIGURED" or (
        values["execution"] == "BLOCKED_CONFIG"
    ):
        return "SOURCE_UNAVAILABLE"
    if values["action"] == "FAILED" or values["status"] == "RED" or (
        values["execution"] == "FAILED"
    ):
        return "REFRESH_FAILED"
    if "STALE" in {values["headline"], values["freshness"]}:
        return "STALE_DATA"
    if values["headline"] in {"PARTIAL", "PARTIAL_SUCCESS"} or values[
        "execution"
    ] in {"PARTIAL", "PARTIAL_SUCCESS"}:
        return "PARTIAL_SUCCESS"
    if values["action"] == "REFRESHED" and status in {"GREEN", "YELLOW"}:
        return "NONE"
    return "NOT_ENOUGH_INFORMATION"


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], *, context: str) -> None:
    actual = set(value)
    missing = expected - actual
    unknown = actual - expected
    if missing or unknown:
        raise ValueError(
            f"Closed {context} keys are invalid; missing={_bounded_key_summary(missing)}, "
            f"unknown={_bounded_key_summary(unknown)}."
        )


def _bounded_key_summary(keys: set[str] | frozenset[str]) -> str:
    ordered = sorted(keys)
    preview = ordered[:8]
    suffix = f" (+{len(ordered) - len(preview)} more)" if len(ordered) > len(preview) else ""
    return f"{preview}{suffix}"


def _require_enum(value: Any, allowed: frozenset[str], *, field: str) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"Receipt field {field} has an unsupported value or type.")
    return value


def _require_text(
    value: Any, *, field: str, minimum: int, maximum: int
) -> str:
    if type(value) is not str or not minimum <= len(value) <= maximum:
        raise ValueError(f"Receipt field {field} length or type is invalid.")
    if value != value.strip() or any(ord(character) < 32 for character in value):
        raise ValueError(f"Receipt field {field} contains invalid whitespace/control text.")
    _validate_private_string(value, field=field)
    return value


def _require_opaque_id(value: Any, *, field: str) -> str:
    if type(value) is not str or not _OPAQUE_ID.fullmatch(value):
        raise ValueError(f"Receipt field {field} is not a valid opaque ID.")
    return value


def _require_receipt_id(value: Any, *, field: str) -> str:
    if type(value) is not str or not _RECEIPT_ID.fullmatch(value):
        raise ValueError(f"Receipt field {field} is not a valid receipt ID.")
    return value


def _require_identifier(value: Any, *, field: str, allow_empty: bool) -> str:
    if allow_empty and value == "":
        return ""
    if type(value) is not str or not _SUBJECT_ID.fullmatch(value):
        raise ValueError(f"Receipt field {field} is not a valid identifier.")
    return value


def _require_family(value: Any, *, field: str) -> str:
    if value == "":
        return ""
    if type(value) is not str or not _FAMILY_ID.fullmatch(value):
        raise ValueError(f"Receipt field {field} is not a valid identifier.")
    return value


def _require_timestamp(value: Any, *, field: str) -> str:
    if type(value) is not str or not _UTC_TIMESTAMP.fullmatch(value):
        raise ValueError(f"Receipt timestamp {field} has an invalid type or format.")
    try:
        _parse_timestamp(value)
    except ValueError as exc:
        raise ValueError(f"Receipt timestamp {field} is invalid.") from exc
    return value


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("Timestamp is not UTC.")
    return parsed


def _validate_privacy(value: Any, *, path: str = "receipt") -> None:
    if type(value) is dict:
        for key, nested in value.items():
            if type(key) is not str:
                raise ValueError(f"Receipt key at {path} must be a string.")
            if _SENSITIVE_TEXT.search(key):
                raise ValueError(f"Receipt contains prohibited private key at {path}.{key}.")
            _validate_privacy(nested, path=f"{path}.{key}")
        return
    if type(value) is list:
        for index, nested in enumerate(value):
            _validate_privacy(nested, path=f"{path}[{index}]")
        return
    if type(value) is str:
        _validate_private_string(value, field=path)
        return
    if value is None or type(value) in {bool, int}:
        return
    raise ValueError(f"Receipt contains unauthorized type at {path}.")


def _validate_private_string(value: str, *, field: str) -> None:
    if _SENSITIVE_TEXT.search(value):
        raise ValueError(f"Receipt field {field} contains prohibited private content.")
    if value.startswith("/") or _WINDOWS_ABSOLUTE_PATH.match(value):
        raise ValueError(f"Receipt field {field} contains an absolute private path.")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise DuplicateReceiptKeyError(key)
        output[key] = value
    return output


def _reject_json_constant(value: str) -> None:
    raise json.JSONDecodeError(f"Non-finite JSON number {value}", value, 0)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _filename_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _load_detail(status: str) -> str:
    return {
        VALID_LATEST: "Latest receipt validated by read-only inspection.",
        MISSING: "No latest receipt is stored; no filesystem change was made.",
        CORRUPT: (
            "Latest receipt is corrupt and cannot be trusted; no automatic quarantine "
            "was performed and explicit maintenance is required."
        ),
        OVERSIZED: (
            "Latest receipt exceeds the supported size bound; no automatic quarantine "
            "was performed and explicit maintenance is required."
        ),
        UNSUPPORTED_SCHEMA: (
            "Latest receipt schema is unsupported; no migration or filesystem change "
            "was performed and explicit maintenance is required."
        ),
    }.get(status, "Receipt state is not trustworthy; no filesystem change was made.")
