from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.services.nfl_usage_data_loader_service import blocked_fields

MODEL_INPUT_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"


@dataclass(frozen=True)
class NflUsageValidationResult:
    status: str
    validation_rows: tuple[dict[str, str], ...]
    quarantine_rows: tuple[dict[str, str], ...]


def validate_usage_rows(
    source_family: str,
    rows: list[dict[str, Any]],
    *,
    required_fields: set[str],
    allowed_fields: set[str],
    min_rows: int = 1,
    duplicate_key: tuple[str, ...] = ("season", "week", "player_id", "source_family"),
    metadata: dict[str, Any] | None = None,
) -> NflUsageValidationResult:
    reasons: list[str] = []
    fields = _fields(rows)
    missing = sorted(required_fields - set(fields))
    blocked = blocked_fields(fields)
    not_allowed = sorted(field for field in fields if field not in allowed_fields)

    if missing:
        reasons.append(f"missing_required_fields:{';'.join(missing)}")
    if blocked:
        reasons.append(f"blocked_fields_present:{';'.join(blocked)}")
    if not_allowed:
        reasons.append(f"unallowed_fields_present:{';'.join(not_allowed)}")
    if len(rows) < min_rows:
        reasons.append("row_count_collapse")
    if _duplicate_count(rows, duplicate_key) > 0:
        reasons.append("duplicate_player_week_source_rows")
    spike_fields = _null_spike_fields(rows)
    if spike_fields:
        reasons.append(f"null_spike:{';'.join(spike_fields)}")
    if _stale(metadata):
        reasons.append("stale_source_metadata")
    if not _has_license(metadata):
        reasons.append("license_attribution_missing")
    if any(str(row.get("model_input_allowed", MODEL_INPUT_ALLOWED)) != "no" for row in rows):
        reasons.append("model_permission_violation")
    if any(str(row.get("app_wiring_allowed", APP_WIRING_ALLOWED)) != "no" for row in rows):
        reasons.append("app_permission_violation")
    if any(_route_truth_overclaim(row) for row in rows):
        reasons.append("unsupported_route_truth_claim")

    status = "GREEN" if not reasons else "RED"
    validation_row = {
        "source_family": source_family,
        "validation_status": status,
        "row_count": str(len(rows)),
        "field_count": str(len(fields)),
        "reasons": "|".join(reasons),
        "model_input_allowed": MODEL_INPUT_ALLOWED,
        "app_wiring_allowed": APP_WIRING_ALLOWED,
    }
    quarantine_rows = tuple(
        {
            "source_family": source_family,
            "quarantine_status": "QUARANTINED",
            "reason": reason,
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
        for reason in reasons
    )
    return NflUsageValidationResult(
        status=status,
        validation_rows=(validation_row,),
        quarantine_rows=quarantine_rows,
    )


def validation_template_rows() -> list[dict[str, str]]:
    return [
        {
            "source_family": "core_usage",
            "validation_status": "YELLOW_TEMPLATE",
            "row_count": "0",
            "field_count": "0",
            "reasons": "live pull not run in V0 environment",
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
    ]


def quarantine_template_rows() -> list[dict[str, str]]:
    reasons = [
        "schema mismatch",
        "missing required fields",
        "blocked fields present",
        "row count collapse",
        "duplicate explosion",
        "null spike",
        "stale data",
        "license/attribution missing",
        "source unavailable",
        "raw data attempted to be committed",
        "unsupported route truth claim",
        "app/model permission violation",
    ]
    return [
        {
            "source_family": "template",
            "quarantine_status": "TEMPLATE_REASON",
            "reason": reason,
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
        }
        for reason in reasons
    ]


def _fields(rows: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            field = str(key)
            if field not in seen:
                fields.append(field)
                seen.add(field)
    return fields


def _duplicate_count(rows: list[dict[str, Any]], duplicate_key: tuple[str, ...]) -> int:
    counter = Counter(
        tuple(str(row.get(column, "")) for column in duplicate_key)
        for row in rows
        if all(column in row for column in duplicate_key)
    )
    return sum(count - 1 for count in counter.values() if count > 1)


def _null_spike_fields(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    fields = _fields(rows)
    spiked: list[str] = []
    for field in fields:
        nulls = sum(1 for row in rows if row.get(field) in ("", None))
        if nulls / len(rows) > 0.95:
            spiked.append(field)
    return spiked


def _stale(metadata: dict[str, Any] | None) -> bool:
    if not metadata or not metadata.get("source_updated_at"):
        return False
    try:
        updated = datetime.fromisoformat(str(metadata["source_updated_at"]).replace("Z", "+00:00"))
    except ValueError:
        return True
    return (datetime.now(UTC) - updated).days > int(metadata.get("max_age_days", 3700))


def _has_license(metadata: dict[str, Any] | None) -> bool:
    if not metadata:
        return True
    if metadata.get("source_family") in {"ftn_charting", "participation", "pfr_advstats"}:
        return bool(metadata.get("license")) and bool(metadata.get("attribution"))
    return True


def _route_truth_overclaim(row: dict[str, Any]) -> bool:
    label = " ".join(str(row.get(key, "")) for key in ("field_name", "field_type", "notes")).lower()
    return "true routes" in label or "true tprr" in label or "true yprr" in label
