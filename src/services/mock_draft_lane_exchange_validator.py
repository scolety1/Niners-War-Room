from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.mock_draft_input_contract import (
    READINESS_GREEN,
    READINESS_RED,
    READINESS_YELLOW,
)

DEFAULT_EXCHANGE_HUB = Path("C:/NWR_SHARED_DATA/lane_exchange")
DEFAULT_REGISTRY_PATH = Path(
    "C:/NWR_SHARED_DATA/lane_exchange_registry/lane_exchange_v0_registry.json"
)

READ_ONLY_USE = "mock_draft_read_only_validation"
MANUAL_REVIEW_USE = "draft_day_manual_review"
PRIVATE_VALUE_FORBIDDEN = "private_value_from_market"

REQUIRED_PACKAGES = (
    "rookie_hq/frozen_rookie_mock_input",
    "drop_decision/dropped_veterans",
    "drop_decision/unavailable_players",
    "league_state/pick_order",
    "league_state/nwr_picks",
    "model_value/veteran_private_values",
)
OPTIONAL_PACKAGES = ("market_behavior/display_only_market_context",)

PACKAGE_POLICIES: dict[str, dict[str, bool]] = {
    "rookie_hq/frozen_rookie_mock_input": {
        "required": True,
        "may_contain_private_value": True,
        "may_contain_market": False,
        "display_only_market": False,
    },
    "drop_decision/dropped_veterans": {
        "required": True,
        "may_contain_private_value": False,
        "may_contain_market": False,
        "display_only_market": False,
    },
    "drop_decision/unavailable_players": {
        "required": True,
        "may_contain_private_value": False,
        "may_contain_market": False,
        "display_only_market": False,
    },
    "league_state/pick_order": {
        "required": True,
        "may_contain_private_value": False,
        "may_contain_market": False,
        "display_only_market": False,
    },
    "league_state/nwr_picks": {
        "required": True,
        "may_contain_private_value": False,
        "may_contain_market": False,
        "display_only_market": False,
    },
    "model_value/veteran_private_values": {
        "required": True,
        "may_contain_private_value": True,
        "may_contain_market": False,
        "display_only_market": False,
    },
    "market_behavior/display_only_market_context": {
        "required": False,
        "may_contain_private_value": False,
        "may_contain_market": True,
        "display_only_market": True,
    },
}

REQUIRED_MANIFEST_FIELDS = frozenset(
    {
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
    }
)


@dataclass(frozen=True)
class LaneExchangePackageReport:
    package_name: str
    required: bool
    readiness: str
    latest_approved_path: str
    manifest_path: str
    data_file_path: str
    row_count_expected: int | None
    row_count_actual: int | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class LaneExchangeReadinessReport:
    readiness: str
    registry_readiness: str
    hub_root: str
    registry_path: str
    package_reports: tuple[LaneExchangePackageReport, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    no_simulations_run: bool = True
    no_files_written: bool = True
    market_policy: str = (
        "ADP/market is optional display-only opponent behavior, availability, "
        "and pick timing context; it is never NWR private value."
    )


def validate_lane_exchange_readiness(
    *,
    hub_root: str | Path = DEFAULT_EXCHANGE_HUB,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> LaneExchangeReadinessReport:
    hub = Path(hub_root)
    registry = Path(registry_path)
    registry_errors, registry_warnings = _validate_registry(registry, hub)
    registry_readiness = READINESS_RED if registry_errors else READINESS_GREEN
    package_reports = tuple(
        _validate_package(package_name, hub)
        for package_name in (*REQUIRED_PACKAGES, *OPTIONAL_PACKAGES)
    )
    readiness = _aggregate_readiness(registry_readiness, package_reports)
    errors = tuple(registry_errors)
    warnings = tuple(registry_warnings)
    return LaneExchangeReadinessReport(
        readiness=readiness,
        registry_readiness=registry_readiness,
        hub_root=str(hub),
        registry_path=str(registry),
        package_reports=package_reports,
        errors=errors,
        warnings=warnings,
    )


def _validate_registry(registry_path: Path, hub_root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not registry_path.exists():
        return [f"Registry not found: {registry_path}"], warnings
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Registry is malformed: {exc}"], warnings
    if payload.get("contract_version") != "lane_exchange_v0":
        errors.append("Registry contract_version must be lane_exchange_v0.")
    if payload.get("local_only") is not True:
        errors.append("Registry must be marked local_only=true.")
    registry_hub = payload.get("hub_root")
    if registry_hub and Path(str(registry_hub)) != hub_root:
        warnings.append(
            f"Registry hub_root {registry_hub} differs from validator hub_root {hub_root}."
        )
    consumer_packages = _mock_draft_consumer_packages(payload)
    for package_name in (*REQUIRED_PACKAGES, *OPTIONAL_PACKAGES):
        if package_name not in consumer_packages:
            errors.append(f"Registry missing Mock Draft consumer package: {package_name}.")
    return errors, warnings


def _mock_draft_consumer_packages(payload: dict[str, Any]) -> set[str]:
    packages: set[str] = set()
    lane_ownership = payload.get("lane_ownership")
    if not isinstance(lane_ownership, list):
        return packages
    for entry in lane_ownership:
        if isinstance(entry, dict) and entry.get("source_lane") == "mock_draft":
            consumer_packages = entry.get("consumer_packages")
            if isinstance(consumer_packages, list):
                packages.update(str(package) for package in consumer_packages)
    return packages


def _validate_package(package_name: str, hub_root: Path) -> LaneExchangePackageReport:
    policy = PACKAGE_POLICIES[package_name]
    required = policy["required"]
    package_root = hub_root / Path(*package_name.split("/"))
    latest_approved = package_root / "latest_approved.json"
    if not latest_approved.exists():
        readiness = READINESS_RED if required else READINESS_YELLOW
        warning_or_error = f"latest_approved.json not found: {latest_approved}"
        candidate = package_root / "latest_candidate.json"
        if candidate.exists():
            warning_or_error += " (latest_candidate exists but is not accepted)."
        return LaneExchangePackageReport(
            package_name=package_name,
            required=required,
            readiness=readiness,
            latest_approved_path=str(latest_approved),
            manifest_path="",
            data_file_path="",
            row_count_expected=None,
            row_count_actual=None,
            errors=(warning_or_error,) if required else (),
            warnings=() if required else (warning_or_error,),
        )

    try:
        manifest, manifest_path = _resolve_manifest(latest_approved, hub_root)
    except ValueError as exc:
        return _package_error(package_name, required, latest_approved, str(exc))
    errors, warnings = _validate_manifest_fields(
        manifest=manifest,
        package_name=package_name,
        manifest_path=manifest_path,
        hub_root=hub_root,
    )
    data_file_path = ""
    expected_count: int | None = None
    actual_count: int | None = None
    if not errors:
        data_errors, data_warnings, data_file_path, expected_count, actual_count = (
            _validate_data_file(manifest, manifest_path, hub_root)
        )
        errors.extend(data_errors)
        warnings.extend(data_warnings)
    readiness = READINESS_RED if errors else READINESS_GREEN
    return LaneExchangePackageReport(
        package_name=package_name,
        required=required,
        readiness=readiness,
        latest_approved_path=str(latest_approved),
        manifest_path=str(manifest_path),
        data_file_path=data_file_path,
        row_count_expected=expected_count,
        row_count_actual=actual_count,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _resolve_manifest(pointer_path: Path, hub_root: Path) -> tuple[dict[str, Any], Path]:
    try:
        payload = json.loads(pointer_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"latest_approved.json is malformed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("latest_approved.json must contain an object.")
    target = _manifest_target(payload, pointer_path)
    if target is None:
        return payload, pointer_path
    if not _is_under(target, hub_root):
        raise ValueError(f"Manifest target is outside exchange hub: {target}")
    try:
        manifest = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Snapshot manifest is malformed: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("Snapshot manifest must contain an object.")
    return manifest, target


def _manifest_target(payload: dict[str, Any], pointer_path: Path) -> Path | None:
    for key in (
        "manifest_path",
        "snapshot_manifest",
        "snapshot_manifest_path",
        "target_manifest",
    ):
        if payload.get(key):
            target = Path(str(payload[key]))
            return target if target.is_absolute() else pointer_path.parent / target
    if payload.get("snapshot_path"):
        target_dir = Path(str(payload["snapshot_path"]))
        if not target_dir.is_absolute():
            target_dir = pointer_path.parent / target_dir
        return target_dir / "manifest.json"
    return None


def _validate_manifest_fields(
    *,
    manifest: dict[str, Any],
    package_name: str,
    manifest_path: Path,
    hub_root: Path,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(REQUIRED_MANIFEST_FIELDS.difference(manifest))
    if missing:
        errors.append("Manifest missing required fields: " + ", ".join(missing) + ".")
    if manifest.get("package_name") != package_name:
        errors.append(
            f"Manifest package_name must be {package_name}; found {manifest.get('package_name')}."
        )
    if manifest.get("approval_status") != "approved":
        errors.append("Manifest approval_status must be approved.")
    allowed_use = _as_string_set(manifest.get("allowed_use"))
    approved_for = _as_string_set(manifest.get("approved_for"))
    forbidden_use = _as_string_set(manifest.get("forbidden_use"))
    if READ_ONLY_USE not in allowed_use and READ_ONLY_USE not in approved_for:
        errors.append(f"Manifest must allow or approve {READ_ONLY_USE}.")
    if READ_ONLY_USE in forbidden_use or MANUAL_REVIEW_USE in forbidden_use:
        errors.append("Manifest forbids Mock Draft read-only/manual review use.")
    policy = PACKAGE_POLICIES[package_name]
    contains_market = _bool(manifest.get("contains_market_data"))
    contains_adp = _bool(manifest.get("contains_adp"))
    contains_private = _bool(manifest.get("contains_private_value"))
    if (contains_market or contains_adp) and not policy["may_contain_market"]:
        errors.append("Non-market package contains market/ADP data.")
    if contains_private and not policy["may_contain_private_value"]:
        errors.append("Package contains private value where policy forbids it.")
    if policy["display_only_market"]:
        errors.extend(_validate_display_only_market_policy(manifest, allowed_use, forbidden_use))
    if not _is_under(manifest_path, hub_root):
        errors.append(f"Manifest path is outside exchange hub: {manifest_path}")
    if manifest_path.name == "latest_candidate.json":
        errors.append("latest_candidate.json is not accepted for draft decisions.")
    if not manifest.get("schema_version"):
        warnings.append("Manifest schema_version is empty.")
    return errors, warnings


def _validate_display_only_market_policy(
    manifest: dict[str, Any],
    allowed_use: set[str],
    forbidden_use: set[str],
) -> tuple[str, ...]:
    errors: list[str] = []
    if _bool(manifest.get("contains_private_value")):
        errors.append("Display-only market package must not contain private value.")
    allowed_text = " ".join(sorted(allowed_use)).lower()
    if not any(
        phrase in allowed_text
        for phrase in ("display", "opponent", "availability", "pick_timing", READ_ONLY_USE)
    ):
        errors.append("Market package allowed_use must be display/opponent behavior only.")
    forbidden_text = " ".join(sorted(forbidden_use)).lower()
    if PRIVATE_VALUE_FORBIDDEN not in forbidden_use and "private_value" not in forbidden_text:
        errors.append("Market package forbidden_use must block private value use.")
    return tuple(errors)


def _validate_data_file(
    manifest: dict[str, Any],
    manifest_path: Path,
    hub_root: Path,
) -> tuple[list[str], list[str], str, int | None, int | None]:
    errors: list[str] = []
    warnings: list[str] = []
    data_file = manifest.get("data_file")
    data_path = Path(str(data_file))
    if data_path.is_absolute():
        resolved_data = data_path
    else:
        resolved_data = manifest_path.parent / data_path
    if not _is_under(resolved_data, hub_root):
        errors.append(f"Data file is outside exchange hub: {resolved_data}")
        return errors, warnings, str(resolved_data), _int_or_none(manifest.get("row_count")), None
    if not resolved_data.exists():
        errors.append(f"Data file not found: {resolved_data}")
        return errors, warnings, str(resolved_data), _int_or_none(manifest.get("row_count")), None
    expected_sha = str(manifest.get("sha256") or "").strip().lower()
    if _sha256(resolved_data) != expected_sha:
        errors.append("Data file sha256 does not match manifest.")
    expected_count = _int_or_none(manifest.get("row_count"))
    actual_count = _row_count(resolved_data)
    if expected_count is None:
        errors.append("Manifest row_count must be an integer.")
    elif actual_count is None:
        warnings.append(f"Row count not feasible for file type: {resolved_data.suffix}")
    elif expected_count != actual_count:
        errors.append(
            f"Data file row_count mismatch: expected {expected_count}, found {actual_count}."
        )
    return errors, warnings, str(resolved_data), expected_count, actual_count


def _row_count(path: Path) -> int | None:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return len(payload["rows"])
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_error(
    package_name: str,
    required: bool,
    latest_approved: Path,
    error: str,
) -> LaneExchangePackageReport:
    return LaneExchangePackageReport(
        package_name=package_name,
        required=required,
        readiness=READINESS_RED,
        latest_approved_path=str(latest_approved),
        manifest_path="",
        data_file_path="",
        row_count_expected=None,
        row_count_actual=None,
        errors=(error,),
        warnings=(),
    )


def _aggregate_readiness(
    registry_readiness: str,
    package_reports: tuple[LaneExchangePackageReport, ...],
) -> str:
    if registry_readiness == READINESS_RED:
        return READINESS_RED
    for report in package_reports:
        if report.readiness == READINESS_RED:
            return READINESS_RED
    return READINESS_GREEN


def _as_string_set(value: object) -> set[str]:
    if isinstance(value, list):
        return {str(item) for item in value}
    if isinstance(value, str):
        return {value}
    return set()


def _bool(value: object) -> bool:
    return value is True or str(value).strip().lower() == "true"


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _is_under(path: Path, root: Path) -> bool:
    try:
        resolved_path = path.resolve(strict=False)
        resolved_root = root.resolve(strict=False)
    except OSError:
        return False
    return resolved_path == resolved_root or resolved_root in resolved_path.parents
