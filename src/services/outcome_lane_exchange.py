from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CONTRACT_PATH = Path(
    r"C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_LANE_EXCHANGE_V0_CONTRACT.md"
)
DEFAULT_HUB_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")
DEFAULT_REGISTRY_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json"
)

OUTCOME_LANE_ID = "outcome_v1"
OUTCOME_PACKAGE_NAME = "outcome_v1/outcome_display_snapshot"
OUTCOME_SCHEMA_VERSION = "outcome_display_snapshot_v1"
OUTCOME_CANDIDATE_ALLOWED_USE = "outcome_v1_display_review_validation"
OUTCOME_CANDIDATE_FORBIDDEN_USE = (
    "draft_decision_without_approval",
    "private_value_input",
    "ranking_or_sorting_input",
)

REQUIRED_MANIFEST_FIELDS = (
    "source_lane",
    "source_repo",
    "source_branch",
    "source_head",
    "package_name",
    "schema_version",
    "data_file",
    "row_count",
    "sha256",
    "created_at",
    "approval_status",
    "approved_for",
    "allowed_use",
    "forbidden_use",
    "contains_private_value",
    "contains_market_data",
    "contains_adp",
    "notes",
)


class LaneExchangeError(ValueError):
    """Raised when a lane exchange manifest or registry fails closed."""


@dataclass(frozen=True)
class OutcomeExchangeRole:
    lane_id: str
    owned_packages: tuple[str, ...]
    consumed_packages: tuple[str, ...]
    publish_allowed: bool
    requires_explicit_approval_later: bool
    notes: str


@dataclass(frozen=True)
class ApprovedSnapshotValidation:
    package_name: str
    manifest_path: Path
    data_path: Path
    row_count: int
    sha256: str
    approval_status: str
    allowed_use: tuple[str, ...]


@dataclass(frozen=True)
class PublishedCandidateSnapshot:
    package_name: str
    snapshot_dir: Path
    manifest_path: Path
    latest_candidate_path: Path
    data_path: Path
    row_count: int
    sha256: str


def load_exchange_registry(
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    path = Path(registry_path)
    if not path.exists():
        raise LaneExchangeError(f"Missing lane exchange registry: {path}")
    with path.open(encoding="utf-8") as handle:
        registry = json.load(handle)
    if registry.get("contract_version") != "lane_exchange_v0":
        raise LaneExchangeError("Unsupported lane exchange registry version.")
    if registry.get("local_only") is not True:
        raise LaneExchangeError("Lane exchange registry must be marked local_only=true.")
    return registry


def outcome_exchange_role(registry: dict[str, Any]) -> OutcomeExchangeRole:
    entry = _lane_entry(registry, OUTCOME_LANE_ID)
    owned = tuple(
        _full_package_name(OUTCOME_LANE_ID, name) for name in entry.get("owns_packages", ())
    )
    consumed = tuple(str(name) for name in entry.get("consumer_packages", ()))
    return OutcomeExchangeRole(
        lane_id=OUTCOME_LANE_ID,
        owned_packages=owned,
        consumed_packages=consumed,
        publish_allowed=entry.get("candidate_publish_allowed") is True
        or entry.get("publish_allowed") is True,
        requires_explicit_approval_later=entry.get("requires_explicit_approval_later") is True,
        notes=str(entry.get("notes") or ""),
    )


def validate_latest_approved_snapshot(
    package_name: str,
    *,
    hub_root: str | Path = DEFAULT_HUB_ROOT,
    required_use: str | None = None,
) -> ApprovedSnapshotValidation:
    root = Path(hub_root).resolve()
    source_lane, short_name = _split_package_name(package_name)
    pointer_path = root / source_lane / short_name / "latest_approved.json"
    if not pointer_path.exists():
        raise LaneExchangeError(f"Missing latest_approved pointer: {pointer_path}")

    pointer = _read_json(pointer_path)
    manifest_path, manifest = _resolve_pointer_manifest(pointer, pointer_path, root)
    manifest_dir = manifest_path.parent
    _validate_manifest_fields(manifest)

    if manifest["package_name"] != package_name:
        raise LaneExchangeError(
            f"Manifest package mismatch: expected {package_name}, found {manifest['package_name']}"
        )
    if manifest["approval_status"] != "approved":
        raise LaneExchangeError(f"Manifest is not approved: {manifest['approval_status']}")
    allowed_use = _as_string_tuple(manifest["allowed_use"])
    if required_use and required_use not in allowed_use:
        raise LaneExchangeError(f"Manifest is not allowed for use: {required_use}")

    data_path = _resolve_under_root(manifest_dir, str(manifest["data_file"]), root)
    if not data_path.exists():
        raise LaneExchangeError(f"Manifest data file is missing: {data_path}")

    expected_sha = str(manifest["sha256"]).lower()
    actual_sha = sha256_file(data_path)
    if actual_sha != expected_sha:
        raise LaneExchangeError(f"SHA256 mismatch for {package_name}")

    expected_rows = _required_int(manifest["row_count"], "row_count")
    actual_rows = count_snapshot_rows(data_path)
    if actual_rows != expected_rows:
        raise LaneExchangeError(
            f"Row-count mismatch for {package_name}: expected {expected_rows}, found {actual_rows}"
        )

    return ApprovedSnapshotValidation(
        package_name=package_name,
        manifest_path=manifest_path,
        data_path=data_path,
        row_count=actual_rows,
        sha256=actual_sha,
        approval_status=str(manifest["approval_status"]),
        allowed_use=allowed_use,
    )


def publish_outcome_candidate_snapshot(
    source_data_file: str | Path,
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    hub_root: str | Path = DEFAULT_HUB_ROOT,
    source_repo: str = "",
    source_branch: str = "",
    source_head: str = "",
    snapshot_label: str | None = None,
    created_at: str | None = None,
    notes: str = "Outcome V1 candidate display snapshot.",
) -> PublishedCandidateSnapshot:
    registry = load_exchange_registry(registry_path)
    role = outcome_exchange_role(registry)
    if OUTCOME_PACKAGE_NAME not in role.owned_packages:
        raise LaneExchangeError("Registry does not give Outcome V1 ownership of its package.")
    if not role.publish_allowed:
        raise LaneExchangeError(
            "Registry does not explicitly allow Outcome V1 candidate publishing."
        )

    source_path = Path(source_data_file)
    if not source_path.exists():
        raise LaneExchangeError(f"Candidate source data file is missing: {source_path}")

    root = Path(hub_root).resolve()
    package_dir = root / OUTCOME_LANE_ID / "outcome_display_snapshot"
    label = snapshot_label or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ_candidate")
    snapshot_dir = package_dir / label
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    data_path = snapshot_dir / source_path.name
    shutil.copy2(source_path, data_path)
    row_count = count_snapshot_rows(data_path)
    file_hash = sha256_file(data_path)
    manifest = {
        "source_lane": OUTCOME_LANE_ID,
        "source_repo": source_repo,
        "source_branch": source_branch,
        "source_head": source_head,
        "package_name": OUTCOME_PACKAGE_NAME,
        "schema_version": OUTCOME_SCHEMA_VERSION,
        "data_file": data_path.name,
        "row_count": row_count,
        "sha256": file_hash,
        "created_at": created_at or datetime.now(UTC).isoformat(),
        "approval_status": "candidate",
        "approved_for": [],
        "allowed_use": [OUTCOME_CANDIDATE_ALLOWED_USE],
        "forbidden_use": list(OUTCOME_CANDIDATE_FORBIDDEN_USE),
        "contains_private_value": False,
        "contains_market_data": False,
        "contains_adp": False,
        "notes": notes,
    }
    manifest_path = snapshot_dir / "manifest.json"
    _write_json(manifest_path, manifest)

    latest_candidate_path = package_dir / "latest_candidate.json"
    _write_json(
        latest_candidate_path,
        {"manifest_path": _relative_manifest_path(manifest_path, root)},
    )

    return PublishedCandidateSnapshot(
        package_name=OUTCOME_PACKAGE_NAME,
        snapshot_dir=snapshot_dir,
        manifest_path=manifest_path,
        latest_candidate_path=latest_candidate_path,
        data_path=data_path,
        row_count=row_count,
        sha256=file_hash,
    )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_snapshot_rows(path: str | Path) -> int:
    snapshot_path = Path(path)
    if snapshot_path.suffix.lower() == ".csv":
        with snapshot_path.open(newline="", encoding="utf-8-sig") as handle:
            return max(sum(1 for _ in csv.reader(handle)) - 1, 0)
    with snapshot_path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def readiness_summary(
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    hub_root: str | Path = DEFAULT_HUB_ROOT,
    packages: tuple[str, ...] = (),
    required_use: str | None = None,
) -> dict[str, Any]:
    registry = load_exchange_registry(registry_path)
    role = outcome_exchange_role(registry)
    validations = []
    for package in packages:
        result = validate_latest_approved_snapshot(
            package,
            hub_root=hub_root,
            required_use=required_use,
        )
        validations.append(
            {
                "package_name": result.package_name,
                "manifest_path": str(result.manifest_path),
                "data_path": str(result.data_path),
                "row_count": result.row_count,
                "sha256": result.sha256,
                "approval_status": result.approval_status,
                "allowed_use": list(result.allowed_use),
            }
        )
    return {
        "lane": role.lane_id,
        "owned_packages": list(role.owned_packages),
        "consumed_packages": list(role.consumed_packages),
        "candidate_publish_allowed": role.publish_allowed,
        "requires_explicit_approval_later": role.requires_explicit_approval_later,
        "hub_root": str(hub_root),
        "validated_latest_approved": validations,
    }


def format_readiness_summary(summary: dict[str, Any]) -> str:
    lines = [
        "LANE=outcome_v1",
        f"owned_packages={','.join(summary['owned_packages']) or '(none)'}",
        f"consumed_packages={','.join(summary['consumed_packages']) or '(none)'}",
        f"candidate_publish_allowed={str(summary['candidate_publish_allowed']).lower()}",
        "requires_explicit_approval_later="
        f"{str(summary['requires_explicit_approval_later']).lower()}",
        f"hub_root={summary['hub_root']}",
    ]
    validations = summary["validated_latest_approved"]
    if not validations:
        lines.append("latest_approved_validations=(none requested)")
    for validation in validations:
        lines.append(
            "latest_approved_valid="
            f"{validation['package_name']} rows={validation['row_count']} "
            f"sha256={validation['sha256']}"
        )
    return "\n".join(lines)


def _lane_entry(registry: dict[str, Any], lane_id: str) -> dict[str, Any]:
    for entry in registry.get("lane_ownership", ()):
        if entry.get("source_lane") == lane_id:
            return entry
    raise LaneExchangeError(f"Lane is not registered for exchange: {lane_id}")


def _full_package_name(source_lane: str, package_name: str) -> str:
    if "/" in package_name:
        return package_name
    return f"{source_lane}/{package_name}"


def _split_package_name(package_name: str) -> tuple[str, str]:
    parts = package_name.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise LaneExchangeError(f"Package name must be source_lane/package: {package_name}")
    return parts[0], parts[1]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise LaneExchangeError(f"Malformed JSON: {path}") from exc
    if not isinstance(data, dict):
        raise LaneExchangeError(f"Expected JSON object: {path}")
    return data


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _resolve_pointer_manifest(
    pointer: dict[str, Any],
    pointer_path: Path,
    hub_root: Path,
) -> tuple[Path, dict[str, Any]]:
    if all(field in pointer for field in REQUIRED_MANIFEST_FIELDS):
        return pointer_path, pointer

    package_dir = pointer_path.parent
    for key in ("manifest_path", "target_manifest", "target_manifest_path", "snapshot_manifest"):
        value = pointer.get(key)
        if value:
            manifest_path = _resolve_pointer_path(package_dir, str(value), hub_root)
            return manifest_path, _read_json(manifest_path)

    for key in ("snapshot_path", "snapshot_dir"):
        value = pointer.get(key)
        if value:
            snapshot_dir = _resolve_pointer_path(package_dir, str(value), hub_root)
            manifest_path = snapshot_dir / "manifest.json"
            return manifest_path, _read_json(manifest_path)

    raise LaneExchangeError(f"latest_approved pointer has no manifest target: {pointer_path}")


def _validate_manifest_fields(manifest: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise LaneExchangeError(f"Manifest is missing required fields: {', '.join(missing)}")
    if not isinstance(manifest["approved_for"], list):
        raise LaneExchangeError("Manifest approved_for must be a list.")
    if not isinstance(manifest["allowed_use"], list):
        raise LaneExchangeError("Manifest allowed_use must be a list.")
    if not isinstance(manifest["forbidden_use"], list):
        raise LaneExchangeError("Manifest forbidden_use must be a list.")
    for flag in ("contains_private_value", "contains_market_data", "contains_adp"):
        if not isinstance(manifest[flag], bool):
            raise LaneExchangeError(f"Manifest {flag} must be boolean.")


def _resolve_under_root(base_dir: Path, value: str, hub_root: Path) -> Path:
    raw_path = Path(value)
    candidate = raw_path if raw_path.is_absolute() else base_dir / raw_path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(hub_root)
    except ValueError as exc:
        raise LaneExchangeError(f"Exchange path escapes hub root: {candidate}") from exc
    return resolved


def _resolve_pointer_path(package_dir: Path, value: str, hub_root: Path) -> Path:
    package_relative = _resolve_under_root(package_dir, value, hub_root)
    if package_relative.exists():
        return package_relative
    return _resolve_under_root(hub_root, value, hub_root)


def _required_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise LaneExchangeError(f"Manifest {field_name} must be an integer.") from exc
    if parsed < 0:
        raise LaneExchangeError(f"Manifest {field_name} must be non-negative.")
    return parsed


def _as_string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise LaneExchangeError("Manifest list field is malformed.")
    return tuple(str(item) for item in value)


def _relative_manifest_path(manifest_path: Path, hub_root: Path) -> str:
    return manifest_path.resolve().relative_to(hub_root).as_posix()


def build_readiness_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Outcome V1 lane exchange readiness check.",
    )
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
    parser.add_argument("--hub-root", default=str(DEFAULT_HUB_ROOT))
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        help="latest_approved package to validate, in source_lane/package form.",
    )
    parser.add_argument("--required-use", default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def run_readiness_cli(argv: list[str] | None = None) -> int:
    parser = build_readiness_arg_parser()
    args = parser.parse_args(argv)
    try:
        summary = readiness_summary(
            registry_path=args.registry,
            hub_root=args.hub_root,
            packages=tuple(args.package),
            required_use=args.required_use,
        )
    except LaneExchangeError as exc:
        print("VERDICT=RED")
        print(f"reason={exc}")
        return 1

    if args.as_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("VERDICT=GREEN")
        print(format_readiness_summary(summary))
    return 0
