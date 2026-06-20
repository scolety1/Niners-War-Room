from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LANE_ID = "trading_lab"
LANE_NAME = "Trading Lab"
OWNED_PACKAGES = ("trade_research_snapshot",)
DEFAULT_REGISTRY_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json"
)
DEFAULT_HUB_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")
LATEST_APPROVED = "latest_approved"
LATEST_CANDIDATE = "latest_candidate"

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
    """Raised when exchange material fails closed validation."""


@dataclass(frozen=True)
class LaneExchangeRole:
    lane_id: str
    owned_packages: tuple[str, ...]
    consumed_packages: tuple[str, ...]
    requires_explicit_publish_approval: bool
    notes: str


@dataclass(frozen=True)
class ManifestValidationResult:
    package_name: str
    manifest_path: Path
    snapshot_dir: Path
    data_path: Path
    row_count: int
    sha256: str
    approval_status: str
    allowed_use: tuple[str, ...]


def load_registry(registry_path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    with registry_path.open(encoding="utf-8") as handle:
        registry = json.load(handle)
    if registry.get("contract_version") != "lane_exchange_v0":
        raise LaneExchangeError("Unsupported lane exchange contract version.")
    return registry


def trading_lab_role(registry: dict[str, Any]) -> LaneExchangeRole:
    for entry in registry.get("lane_ownership", []):
        if entry.get("source_lane") == LANE_ID:
            return LaneExchangeRole(
                lane_id=LANE_ID,
                owned_packages=tuple(entry.get("owns_packages", ())),
                consumed_packages=tuple(entry.get("consumer_packages", ())),
                requires_explicit_publish_approval=bool(
                    entry.get("requires_explicit_approval_later", False)
                ),
                notes=str(entry.get("notes", "")),
            )
    raise LaneExchangeError("Trading Lab is not registered in the lane exchange registry.")


def package_id(source_lane: str, package_name: str) -> str:
    return f"{source_lane}/{package_name}"


def validate_latest_approved_manifest(
    *,
    hub_root: Path,
    source_lane: str,
    package_name: str,
    allowed_use: str | None = None,
    pointer_name: str = LATEST_APPROVED,
) -> ManifestValidationResult:
    if pointer_name == LATEST_CANDIDATE:
        raise LaneExchangeError("latest_candidate is refused for Trading Lab decisions.")
    if pointer_name != LATEST_APPROVED:
        raise LaneExchangeError("Trading Lab validates only latest_approved pointers.")

    package_dir = _safe_child(hub_root, source_lane, package_name)
    pointer_path = package_dir / f"{pointer_name}.json"
    if not pointer_path.exists():
        raise LaneExchangeError(f"Missing exchange pointer: {pointer_path}")

    pointer_payload = _load_json(pointer_path)
    manifest_path, manifest = _resolve_manifest(
        pointer_payload, pointer_path, package_dir, hub_root
    )
    snapshot_dir = manifest_path.parent
    return validate_manifest(
        manifest=manifest,
        manifest_path=manifest_path,
        snapshot_dir=snapshot_dir,
        allowed_use=allowed_use,
    )


def validate_manifest(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    snapshot_dir: Path,
    allowed_use: str | None = None,
) -> ManifestValidationResult:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise LaneExchangeError(f"Manifest missing required fields: {', '.join(missing)}")

    approval_status = str(manifest["approval_status"])
    if approval_status != "approved":
        raise LaneExchangeError(f"Manifest is not approved: {approval_status}")

    allowed_uses = tuple(str(item) for item in manifest["allowed_use"])
    if allowed_use and allowed_use not in allowed_uses:
        raise LaneExchangeError(f"Manifest not allowed for requested use: {allowed_use}")

    data_path = _safe_child(snapshot_dir, str(manifest["data_file"]))
    if not data_path.exists():
        raise LaneExchangeError(f"Manifest data file is missing: {data_path}")

    expected_hash = str(manifest["sha256"])
    actual_hash = file_sha256(data_path)
    if actual_hash != expected_hash:
        raise LaneExchangeError("Manifest sha256 does not match the referenced data file.")

    expected_rows = int(manifest["row_count"])
    actual_rows = count_rows(data_path)
    if actual_rows != expected_rows:
        raise LaneExchangeError(
            f"Manifest row count mismatch: expected {expected_rows}, found {actual_rows}."
        )

    return ManifestValidationResult(
        package_name=str(manifest["package_name"]),
        manifest_path=manifest_path,
        snapshot_dir=snapshot_dir,
        data_path=data_path,
        row_count=actual_rows,
        sha256=actual_hash,
        approval_status=approval_status,
        allowed_use=allowed_uses,
    )


def publish_trade_research_snapshot(
    *,
    hub_root: Path,
    registry: dict[str, Any],
    rows: tuple[dict[str, str], ...],
    source_repo: str,
    source_branch: str,
    source_head: str,
    explicit_publish_approval: bool = False,
    approval_status: str = "candidate",
    snapshot_label: str | None = None,
) -> Path:
    role = trading_lab_role(registry)
    if "trade_research_snapshot" not in role.owned_packages:
        raise LaneExchangeError(
            "Registry does not allow Trading Lab to own trade_research_snapshot."
        )
    if role.requires_explicit_publish_approval and not explicit_publish_approval:
        raise LaneExchangeError(
            "Trading Lab research snapshot publication needs explicit approval."
        )
    if approval_status not in {"candidate", "approved"}:
        raise LaneExchangeError(
            "Trading Lab can publish only candidate or approved research snapshots."
        )
    if not rows:
        raise LaneExchangeError("Trading Lab research snapshot rows are required.")

    snapshot_name = snapshot_label or datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    snapshot_dir = _safe_child(hub_root, LANE_ID, "trade_research_snapshot", snapshot_name)
    snapshot_dir.mkdir(parents=True, exist_ok=False)

    csv_path = snapshot_dir / "trade_research_snapshot.csv"
    fieldnames = tuple(rows[0])
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "source_lane": LANE_NAME,
        "source_repo": source_repo,
        "source_branch": source_branch,
        "source_head": source_head,
        "package_name": package_id(LANE_ID, "trade_research_snapshot"),
        "schema_version": "trading_lab_trade_research_snapshot_v0",
        "data_file": csv_path.name,
        "row_count": len(rows),
        "sha256": file_sha256(csv_path),
        "created_at": datetime.now(UTC).isoformat(),
        "approval_status": approval_status,
        "approved_for": ["manual_fantasy_trade_review"],
        "allowed_use": ["manual_fantasy_trade_review", "trade_lab_research_review"],
        "forbidden_use": [
            "automated_trade_submission",
            "external_provider_fetch",
            "private_value_contamination",
        ],
        "contains_private_value": False,
        "contains_market_data": False,
        "contains_adp": False,
        "notes": "Trading Lab-owned fantasy trade research snapshot; local-only exchange use.",
    }
    manifest_path = snapshot_dir / "manifest.json"
    _write_json(manifest_path, manifest)

    pointer_name = (
        "latest_approved.json" if approval_status == "approved" else "latest_candidate.json"
    )
    _write_json(snapshot_dir.parent / pointer_name, {"manifest_path": str(manifest_path)})
    return manifest_path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_rows(path: Path) -> int:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _resolve_manifest(
    pointer_payload: dict[str, Any],
    pointer_path: Path,
    package_dir: Path,
    hub_root: Path,
) -> tuple[Path, dict[str, Any]]:
    if all(field in pointer_payload for field in REQUIRED_MANIFEST_FIELDS):
        return pointer_path, pointer_payload

    referenced = (
        pointer_payload.get("manifest_path")
        or pointer_payload.get("target_manifest")
        or pointer_payload.get("manifest")
    )
    if referenced:
        manifest_path = _resolve_safe_path(str(referenced), package_dir, hub_root)
        return manifest_path, _load_json(manifest_path)

    snapshot_ref = pointer_payload.get("snapshot_dir") or pointer_payload.get("snapshot_path")
    if snapshot_ref:
        snapshot_dir = _resolve_safe_path(str(snapshot_ref), package_dir, hub_root)
        manifest_path = snapshot_dir / "manifest.json"
        return manifest_path, _load_json(manifest_path)

    raise LaneExchangeError("Exchange pointer does not include a manifest reference.")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise LaneExchangeError(f"Expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _safe_child(root: Path, *parts: str) -> Path:
    resolved_root = root.resolve()
    child = resolved_root.joinpath(*parts).resolve()
    if child != resolved_root and resolved_root not in child.parents:
        raise LaneExchangeError("Resolved exchange path escapes the expected root.")
    return child


def _resolve_safe_path(raw_path: str, base_dir: Path, hub_root: Path) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = base_dir / candidate
    resolved = candidate.resolve()
    resolved_hub = hub_root.resolve()
    if resolved != resolved_hub and resolved_hub not in resolved.parents:
        raise LaneExchangeError("Referenced manifest path escapes the exchange hub.")
    return resolved
