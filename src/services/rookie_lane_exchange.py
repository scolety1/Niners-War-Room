"""Rookie HQ lane exchange publisher and validator.

This module is intentionally lane-local. It gives Rookie HQ a safe way to publish
owned exchange packages without wiring exchange data into the production app.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOKIE_SOURCE_LANE = "rookie_hq"
ROOKIE_REPO_NAME = "Niners-War-Room-rookies"
ROOKIE_OWNED_PACKAGE_SLUGS = frozenset({"frozen_rookie_mock_input"})
DEFAULT_EXCHANGE_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")

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


class RookieLaneExchangeError(ValueError):
    """Base error for Rookie lane exchange validation failures."""


class PackageOwnershipError(RookieLaneExchangeError):
    """Raised when Rookie attempts to publish a package owned by another lane."""


class ManifestValidationError(RookieLaneExchangeError):
    """Raised when an exchange manifest is missing or inconsistent."""


@dataclass(frozen=True)
class NormalizedPackageName:
    source_lane: str
    package_slug: str

    @property
    def full_name(self) -> str:
        return f"{self.source_lane}/{self.package_slug}"


@dataclass(frozen=True)
class LaneExchangePublishResult:
    snapshot_dir: Path
    data_path: Path
    manifest_path: Path
    pointer_path: Path
    approved_pointer_path: Path | None
    manifest: dict[str, Any]


def normalize_package_name(package_name: str) -> NormalizedPackageName:
    """Return a canonical source-lane/package name pair."""
    cleaned = package_name.strip().replace("\\", "/")
    if not cleaned:
        raise PackageOwnershipError("Package name is required.")

    parts = [part for part in cleaned.split("/") if part]
    if len(parts) == 1:
        return NormalizedPackageName(source_lane=ROOKIE_SOURCE_LANE, package_slug=parts[0])
    if len(parts) == 2:
        return NormalizedPackageName(source_lane=parts[0], package_slug=parts[1])
    raise PackageOwnershipError(f"Invalid package name: {package_name!r}")


def require_rookie_owned_package(package_name: str) -> NormalizedPackageName:
    """Refuse to publish any package not owned by Rookie HQ."""
    normalized = normalize_package_name(package_name)
    if normalized.source_lane != ROOKIE_SOURCE_LANE:
        raise PackageOwnershipError(
            f"Rookie HQ cannot publish package from lane {normalized.source_lane!r}."
        )
    if normalized.package_slug not in ROOKIE_OWNED_PACKAGE_SLUGS:
        raise PackageOwnershipError(
            f"Rookie HQ does not own package {normalized.full_name!r}."
        )
    return normalized


def compute_sha256(path: str | Path) -> str:
    """Compute a SHA256 digest for a file."""
    file_path = Path(path)
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_row_count(path: str | Path) -> int:
    """Compute row_count where feasible for CSV/JSON exchange payloads."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            row_total = sum(1 for _ in csv.reader(handle))
        return max(row_total - 1, 0)

    if suffix == ".json":
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            for value in payload.values():
                if isinstance(value, list):
                    return len(value)
        raise ManifestValidationError(
            f"Cannot compute row_count for JSON payload shape in {file_path}."
        )

    raise ManifestValidationError(f"Cannot compute row_count for {file_path.suffix!r} files.")


def build_rookie_exchange_manifest(
    *,
    data_path: str | Path,
    package_name: str,
    schema_version: str,
    source_branch: str,
    source_head: str,
    source_repo: str = ROOKIE_REPO_NAME,
    approval_status: str = "candidate",
    approved_for: list[str] | None = None,
    allowed_use: list[str] | None = None,
    forbidden_use: list[str] | None = None,
    contains_private_value: bool = False,
    contains_market_data: bool = False,
    contains_adp: bool = False,
    notes: str = "",
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build and validate a Rookie-owned exchange manifest for a copied data file."""
    normalized = require_rookie_owned_package(package_name)
    file_path = Path(data_path)
    if approval_status not in {"candidate", "approved"}:
        raise ManifestValidationError("approval_status must be 'candidate' or 'approved'.")

    manifest: dict[str, Any] = {
        "source_lane": ROOKIE_SOURCE_LANE,
        "source_repo": source_repo,
        "source_branch": source_branch,
        "source_head": source_head,
        "package_name": normalized.full_name,
        "schema_version": schema_version,
        "data_file": file_path.name,
        "row_count": compute_row_count(file_path),
        "sha256": compute_sha256(file_path),
        "created_at": created_at or datetime.now(UTC).isoformat(),
        "approval_status": approval_status,
        "approved_for": approved_for or [],
        "allowed_use": allowed_use
        or [
            "manual Rookie HQ exchange validation",
            "approved downstream lane intake after manifest checks",
        ],
        "forbidden_use": forbidden_use
        or [
            "production app wiring",
            "formula/order/score changes",
            "simulation or tuning without explicit approval",
        ],
        "contains_private_value": contains_private_value,
        "contains_market_data": contains_market_data,
        "contains_adp": contains_adp,
        "notes": notes,
    }
    validate_manifest(manifest, snapshot_dir=file_path.parent, enforce_rookie_owned=True)
    return manifest


def validate_manifest(
    manifest: dict[str, Any],
    *,
    snapshot_dir: str | Path | None = None,
    require_approved: bool = False,
    enforce_rookie_owned: bool = False,
) -> None:
    """Validate required manifest fields and optional payload integrity checks."""
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise ManifestValidationError(f"Manifest missing required fields: {', '.join(missing)}")

    if enforce_rookie_owned:
        require_rookie_owned_package(str(manifest["package_name"]))

    approval_status = manifest["approval_status"]
    if approval_status not in {"candidate", "approved"}:
        raise ManifestValidationError("Manifest approval_status must be candidate or approved.")
    if require_approved and approval_status != "approved":
        raise ManifestValidationError("Manifest is not approved for approved-pointer intake.")

    for field in ("contains_private_value", "contains_market_data", "contains_adp"):
        if not isinstance(manifest[field], bool):
            raise ManifestValidationError(f"Manifest field {field} must be boolean.")
    for field in ("approved_for", "allowed_use", "forbidden_use"):
        if not isinstance(manifest[field], list):
            raise ManifestValidationError(f"Manifest field {field} must be a list.")

    row_count = manifest["row_count"]
    if not isinstance(row_count, int) or row_count < 0:
        raise ManifestValidationError("Manifest row_count must be a non-negative integer.")

    if snapshot_dir is not None:
        data_path = Path(snapshot_dir) / str(manifest["data_file"])
        if not data_path.is_file():
            raise ManifestValidationError(f"Manifest data_file is missing: {data_path}")
        actual_sha256 = compute_sha256(data_path)
        if actual_sha256 != manifest["sha256"]:
            raise ManifestValidationError("Manifest sha256 does not match data_file.")
        actual_row_count = compute_row_count(data_path)
        if actual_row_count != row_count:
            raise ManifestValidationError("Manifest row_count does not match data_file.")


def publish_rookie_exchange_snapshot(
    *,
    data_file: str | Path,
    package_name: str = "rookie_hq/frozen_rookie_mock_input",
    exchange_root: str | Path = DEFAULT_EXCHANGE_ROOT,
    schema_version: str = "rookie_frozen_mock_input_v1",
    snapshot_label: str | None = None,
    approve: bool = False,
    source_branch: str,
    source_head: str,
    source_repo: str = ROOKIE_REPO_NAME,
    notes: str = "",
) -> LaneExchangePublishResult:
    """Publish a Rookie-owned snapshot to latest_candidate or latest_approved."""
    normalized = require_rookie_owned_package(package_name)
    source_data = Path(data_file)
    if not source_data.is_file():
        raise FileNotFoundError(f"Data file not found: {source_data}")

    label = snapshot_label or datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    package_root = Path(exchange_root) / normalized.source_lane / normalized.package_slug
    snapshot_dir = package_root / label
    if snapshot_dir.exists():
        raise FileExistsError(f"Snapshot already exists: {snapshot_dir}")
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    copied_data_path = snapshot_dir / source_data.name
    shutil.copy2(source_data, copied_data_path)
    approval_status = "approved" if approve else "candidate"
    manifest = build_rookie_exchange_manifest(
        data_path=copied_data_path,
        package_name=normalized.full_name,
        schema_version=schema_version,
        source_branch=source_branch,
        source_head=source_head,
        source_repo=source_repo,
        approval_status=approval_status,
        notes=notes,
    )
    manifest["snapshot_label"] = label
    manifest["snapshot_dir"] = str(snapshot_dir)

    manifest_path = snapshot_dir / "manifest.json"
    write_json(manifest_path, manifest)

    candidate_pointer_path = package_root / "latest_candidate.json"
    pointer_manifest = {**manifest, "manifest_path": str(manifest_path)}
    write_json(candidate_pointer_path, pointer_manifest)

    approved_pointer_path: Path | None = None
    if approve:
        approved_pointer_path = package_root / "latest_approved.json"
        write_json(approved_pointer_path, pointer_manifest)

    return LaneExchangePublishResult(
        snapshot_dir=snapshot_dir,
        data_path=copied_data_path,
        manifest_path=manifest_path,
        pointer_path=candidate_pointer_path,
        approved_pointer_path=approved_pointer_path,
        manifest=manifest,
    )


def read_exchange_pointer(
    *,
    exchange_root: str | Path,
    source_lane: str,
    package_slug: str,
    pointer_name: str = "latest_approved.json",
    require_approved: bool = True,
) -> dict[str, Any]:
    """Read and validate an exchange pointer, including approved external packages."""
    pointer_path = Path(exchange_root) / source_lane / package_slug / pointer_name
    with pointer_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    manifest_path_value = manifest.get("manifest_path")
    snapshot_dir_value = manifest.get("snapshot_dir")
    if manifest_path_value:
        snapshot_dir = Path(manifest_path_value).parent
    elif snapshot_dir_value:
        snapshot_dir = Path(str(snapshot_dir_value))
    else:
        snapshot_dir = None
    validate_manifest(
        manifest,
        snapshot_dir=snapshot_dir,
        require_approved=require_approved,
        enforce_rookie_owned=False,
    )
    return manifest


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    """Write stable, human-readable JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
