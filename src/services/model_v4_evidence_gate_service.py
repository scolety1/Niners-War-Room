from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

TEAM_STATUS_WARNING_TOKENS = (
    "team_mismatch",
    "team_mismatch_or_missing_model_team",
    "stale_team",
    "roster_status_missing",
    "roster_status_unknown",
    "roster_status_mismatch",
    "inactive_roster_status",
)
ROLE_EVIDENCE_WARNING_TOKENS = (
    "missing_role_evidence",
    "missing_or_review_route_target_snap_evidence",
    "missing_lifecycle_or_role_shape_evidence",
    "missing_route_evidence",
    "missing_snap_evidence",
    "missing_usage_evidence",
)
PARTIAL_QUARANTINED_WARNING_TOKENS = (
    "partial_or_quarantined",
    "partial_join",
    "partial_contribution",
    "partial_first_down_confidence_cap",
    "quarantined_join",
    "quarantined_contribution",
    "source_limited_evidence_cap",
)
STALE_TEAM_STATUS_BOOLEAN_FIELDS = (
    "team_mismatch",
    "team_mismatch_source_review",
    "roster_status_mismatch",
    "stale_team",
    "stale_team_cap",
)
PARTIAL_QUARANTINED_BOOLEAN_FIELDS = (
    "partial_join",
    "partial_contribution",
    "quarantined_join",
    "quarantined_contribution",
)
ROLE_EVIDENCE_STATUS_FIELDS = (
    "snap_evidence_status",
    "route_evidence_status",
    "target_evidence_status",
    "usage_evidence_status",
    "depth_chart_evidence_status",
    "role_evidence_status",
)
JOIN_CONTRIBUTION_STATUS_FIELDS = (
    "join_status",
    "source_join_status",
    "component_join_status",
    "evidence_join_status",
    "contribution_status",
    "score_contribution_status",
)
MISSING_STATUS_VALUES = {
    "",
    "missing",
    "missing_or_review",
    "not_available",
    "none",
    "quarantined",
    "review",
    "unknown",
}
ADMITTED_STATUS_VALUES = {
    "admitted",
    "available",
    "ok",
    "present",
    "reviewed",
    "verified",
}


@dataclass(frozen=True)
class ModelV4EvidenceGate:
    stale_team_or_status: bool
    missing_role_evidence: bool
    partial_or_quarantined_contribution: bool
    manual_decision_required: bool
    warning_flags: tuple[str, ...]


def model_v4_evidence_gate(row: Mapping[str, Any]) -> ModelV4EvidenceGate:
    stale_team = _has_stale_team_or_status(row)
    missing_role = _has_missing_role_evidence(row)
    partial_or_quarantined = _has_partial_or_quarantined_contribution(row)
    warnings: list[str] = []
    if stale_team:
        warnings.append("stale_team_or_status_evidence")
    if missing_role:
        warnings.append("missing_role_evidence_gate")
    if partial_or_quarantined:
        warnings.append("partial_or_quarantined_join_evidence")
    return ModelV4EvidenceGate(
        stale_team_or_status=stale_team,
        missing_role_evidence=missing_role,
        partial_or_quarantined_contribution=partial_or_quarantined,
        manual_decision_required=stale_team or missing_role or partial_or_quarantined,
        warning_flags=tuple(warnings),
    )


def _has_stale_team_or_status(row: Mapping[str, Any]) -> bool:
    warnings = _warning_tokens(row)
    if any(_contains_token(warnings, token) for token in TEAM_STATUS_WARNING_TOKENS):
        return True
    if any(_boolish(row.get(field)) for field in STALE_TEAM_STATUS_BOOLEAN_FIELDS):
        return True
    if _explicit_team_mismatch(row):
        return True
    roster_status = _normalize_status(row.get("roster_status"))
    return roster_status in {"unknown", "missing", "inactive", "ir", "out"}


def _has_missing_role_evidence(row: Mapping[str, Any]) -> bool:
    warnings = _warning_tokens(row)
    if any(_contains_token(warnings, token) for token in ROLE_EVIDENCE_WARNING_TOKENS):
        return True
    if "licensed_route_metrics_not_available" in warnings and not _has_any_role_evidence(row):
        return True
    statuses = [_normalize_status(row.get(field)) for field in ROLE_EVIDENCE_STATUS_FIELDS]
    present_statuses = [status for status in statuses if status]
    if present_statuses and all(status in MISSING_STATUS_VALUES for status in present_statuses):
        return True
    return _boolish(row.get("missing_role_evidence"))


def _has_partial_or_quarantined_contribution(row: Mapping[str, Any]) -> bool:
    warnings = _warning_tokens(row)
    if any(_contains_token(warnings, token) for token in PARTIAL_QUARANTINED_WARNING_TOKENS):
        return True
    if any("quarantined" in warning for warning in warnings):
        return True
    if any(_boolish(row.get(field)) for field in PARTIAL_QUARANTINED_BOOLEAN_FIELDS):
        return True
    statuses = [_normalize_status(row.get(field)) for field in JOIN_CONTRIBUTION_STATUS_FIELDS]
    return any(status in {"partial", "partial_join", "quarantined"} for status in statuses)


def _has_any_role_evidence(row: Mapping[str, Any]) -> bool:
    for field in ROLE_EVIDENCE_STATUS_FIELDS:
        if _normalize_status(row.get(field)) in ADMITTED_STATUS_VALUES:
            return True
    for field in ("snap_share", "route_share", "target_share", "usage_sample_size"):
        if _present(row.get(field)):
            return True
    return False


def _explicit_team_mismatch(row: Mapping[str, Any]) -> bool:
    model_team = _normalize_team(row.get("nfl_team") or row.get("model_team"))
    authoritative_team = _normalize_team(
        row.get("authoritative_team") or row.get("current_team") or row.get("roster_team")
    )
    return bool(model_team and authoritative_team and model_team != authoritative_team)


def _warning_tokens(row: Mapping[str, Any]) -> tuple[str, ...]:
    raw = row.get("warning_flags") or row.get("warnings") or row.get("warning_reasons") or ""
    if isinstance(raw, (list, tuple)):
        parts = raw
    else:
        parts = str(raw).split("|")
    return tuple(_normalize_token(part) for part in parts if _normalize_token(part))


def _contains_token(warnings: tuple[str, ...], token: str) -> bool:
    normalized = _normalize_token(token)
    return any(normalized in warning for warning in warnings)


def _normalize_status(value: object) -> str:
    return _normalize_token(value)


def _normalize_team(value: object) -> str:
    return str(value or "").strip().upper()


def _normalize_token(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _boolish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _present(value: object) -> bool:
    return value is not None and str(value).strip() != ""
