from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

REFRESH_SUCCESS = "REFRESH_SUCCESS"
PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
STALE_RETAINED_DATA = "STALE_RETAINED_DATA"
SOURCE_SKIPPED = "SOURCE_SKIPPED"
SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
SOURCE_GATED = "SOURCE_GATED"
REFRESH_FAILED = "REFRESH_FAILED"
NOT_ENOUGH_INFORMATION = "NOT_ENOUGH_INFORMATION"

FIELD_ORDER = (
    "refresh_state",
    "last_success_or_as_of",
    "retained_data_status",
    "reason_summary",
    "safe_next_action",
    "action_availability",
    "diagnostic_path",
)

STATE_LABELS = {
    REFRESH_SUCCESS: "Refresh succeeded",
    PARTIAL_SUCCESS: "Partial success",
    STALE_RETAINED_DATA: "Stale retained data",
    SOURCE_SKIPPED: "Source skipped",
    SOURCE_UNAVAILABLE: "Source unavailable",
    SOURCE_GATED: "Source gated",
    REFRESH_FAILED: "Refresh failed",
    NOT_ENOUGH_INFORMATION: "Not enough information",
}


@dataclass(frozen=True)
class RefreshRecoveryPresentation:
    subject: str
    refresh_state: str
    last_success_or_as_of: str
    retained_data_status: str
    reason_summary: str
    safe_next_action: str
    action_availability: str
    diagnostic_path: str

    def as_ordered_row(self) -> dict[str, str]:
        values = self.__dict__
        return {"subject": self.subject, **{field: values[field] for field in FIELD_ORDER}}


def build_refresh_recovery_presentations(
    records: Iterable[Mapping[str, Any]],
) -> tuple[RefreshRecoveryPresentation, ...]:
    """Map existing refresh records into passive display-only recovery guidance."""
    return tuple(_build_record(record) for record in records)


def build_run_recovery_summary(
    records: Iterable[Mapping[str, Any]], *, finished_at: str = ""
) -> RefreshRecoveryPresentation:
    rows = tuple(records)
    states = tuple(_state_for_record(row) for row in rows)
    succeeded = sum(state == REFRESH_SUCCESS for state in states)
    incomplete = len(states) - succeeded
    if succeeded and incomplete:
        state = PARTIAL_SUCCESS
    elif states and succeeded == len(states):
        state = REFRESH_SUCCESS
    elif states and all(value == SOURCE_SKIPPED for value in states):
        state = SOURCE_SKIPPED
    elif states and any(value == REFRESH_FAILED for value in states):
        state = REFRESH_FAILED
    else:
        state = NOT_ENOUGH_INFORMATION
    guidance = _guidance(state)
    return RefreshRecoveryPresentation(
        subject="Refresh run",
        refresh_state=state,
        last_success_or_as_of=_value(finished_at),
        retained_data_status="See per-source breakdown",
        reason_summary=f"{succeeded} succeeded; {incomplete} did not complete as a refresh.",
        safe_next_action=guidance[0],
        action_availability=guidance[1],
        diagnostic_path="Per-source results below",
    )


def _build_record(record: Mapping[str, Any]) -> RefreshRecoveryPresentation:
    state = _state_for_record(record)
    guidance = _guidance(state)
    retained = "Stale retained data is labeled" if state == STALE_RETAINED_DATA else (
        "Retained data status not recorded"
        if not _text(record, "freshness", "freshness_status")
        else "No stale retained-data signal recorded"
    )
    return RefreshRecoveryPresentation(
        subject=_text(record, "source_name", "source_id", "dataset_id") or "Refresh source",
        refresh_state=state,
        last_success_or_as_of=_value(
            _text(record, "last_success_at", "last_success_timestamp", "run_timestamp", "timestamp")
        ),
        retained_data_status=retained,
        reason_summary=_text(record, "user_explanation", "user_message", "last_result", "caveat")
        or "No trustworthy reason summary is recorded.",
        safe_next_action=guidance[0],
        action_availability=guidance[1],
        diagnostic_path=_text(
            record,
            "tracked_summary_path",
            "raw_cache_path",
            "status_path",
            "runner_path",
        )
        or "No existing diagnostic path recorded",
    )


def _state_for_record(record: Mapping[str, Any]) -> str:
    action = _normalized(record.get("action_type"))
    status = _normalized(record.get("status"))
    execution = _normalized(record.get("execution_status"))
    headline = _normalized(record.get("headline_status"))
    freshness = _normalized(record.get("freshness_status") or record.get("freshness"))
    policy = _normalized(record.get("source_policy_status"))

    if (
        action == "BLOCKED_MANUAL"
        or status == "BLOCKED"
        or execution == "BLOCKED_POLICY"
        or "GATED" in policy
    ):
        return SOURCE_GATED
    if action == "SKIPPED_BY_POLICY" or status == "SKIPPED" or execution == "SKIPPED":
        return SOURCE_SKIPPED
    if (
        action == "NOT_CONFIGURED"
        or status == "NOT_CONFIGURED"
        or execution == "BLOCKED_CONFIG"
        or "UNAVAILABLE" in execution
    ):
        return SOURCE_UNAVAILABLE
    if action == "FAILED" or status == "RED" or execution == "FAILED":
        return REFRESH_FAILED
    if headline == "STALE" or freshness == "STALE":
        return STALE_RETAINED_DATA
    if headline in {"PARTIAL", "PARTIAL_SUCCESS"} or execution in {"PARTIAL", "PARTIAL_SUCCESS"}:
        return PARTIAL_SUCCESS
    if (
        record.get("refreshed") is True
        or action == "REFRESHED"
        or execution in {"SUCCESS", "SUCCEEDED"}
    ):
        return REFRESH_SUCCESS
    return NOT_ENOUGH_INFORMATION


def _guidance(state: str) -> tuple[str, str]:
    return {
        REFRESH_SUCCESS: ("No recovery action is needed.", "INFORMATION_ONLY"),
        PARTIAL_SUCCESS: (
            "Review the partial-success breakdown before choosing the existing approved "
            "refresh action.",
            "AVAILABLE_ACTION",
        ),
        STALE_RETAINED_DATA: (
            "Continue only with the stale label visible, or choose the existing approved "
            "refresh action.",
            "AVAILABLE_ACTION",
        ),
        SOURCE_SKIPPED: (
            "Take no action; this source was intentionally skipped by the recorded workflow.",
            "INFORMATION_ONLY",
        ),
        SOURCE_UNAVAILABLE: (
            "Wait for source availability and review the recorded diagnostic before retrying.",
            "UNAVAILABLE_ACTION",
        ),
        SOURCE_GATED: (
            "Request source-admission review; do not bypass the recorded gate.",
            "REVIEW_LINK",
        ),
        REFRESH_FAILED: (
            "Review the recorded diagnostic, then choose the existing approved refresh "
            "action if appropriate.",
            "AVAILABLE_ACTION",
        ),
        NOT_ENOUGH_INFORMATION: (
            "Review the existing status record; no recovery action can be recommended safely.",
            "UNAVAILABLE_ACTION",
        ),
    }[state]


def _text(record: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _normalized(value: Any) -> str:
    return str(value or "").strip().upper()


def _value(value: Any) -> str:
    return str(value).strip() if value is not None and str(value).strip() else "Not recorded"
