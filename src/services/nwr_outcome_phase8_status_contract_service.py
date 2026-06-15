from __future__ import annotations

from dataclasses import dataclass


APPROVED_PHASE8_OUTCOME_STATUSES = (
    "internal_review_passed",
    "under_review",
    "unavailable",
)

ELIGIBLE_PHASE8_OUTCOME_HEADS = (
    "qb_t12",
    "rb_t12",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
)

EXCLUDED_PHASE8_OUTCOME_HEADS = (
    "qb_t18",
    "qb_t24",
    "rb_t24",
    "rb_t36",
    "rb_t48",
    "wr_t48",
    "qb_t6",
    "rb_t6",
    "wr_t6",
    "te_t3",
    "te_t6",
    "te_t18",
    "te_t24",
)

PHASE8_OUTCOME_STATUS_COPY = {
    "internal_review_passed": "Outcome model: internal review passed",
    "under_review": "Outcome model: under review",
    "unavailable": "Outcome model: unavailable",
}

PHASE8_OUTCOME_STATUS_HELP = {
    "internal_review_passed": "Internal review has passed for this limited non-numeric status.",
    "under_review": "Internal review is still in progress for this limited non-numeric status.",
    "unavailable": "No approved non-numeric Outcome status is available.",
}


@dataclass(frozen=True)
class Phase8OutcomeStatus:
    head: str
    status_key: str
    display_copy: str
    help_text: str
    display_scope: str = "non_numeric_status_only"
    display_only: bool = True
    released: bool = False


def build_phase8_outcome_status(
    *,
    head: str,
    status_key: str | None = None,
    strict: bool = False,
) -> Phase8OutcomeStatus:
    normalized_head = _normalize(head)
    if normalized_head not in ELIGIBLE_PHASE8_OUTCOME_HEADS:
        if strict:
            raise ValueError(f"Unsupported Phase 8 Outcome head: {head}")
        return _status(normalized_head or "unknown", "unavailable")

    normalized_status = _normalize(status_key or "unavailable")
    if normalized_status not in APPROVED_PHASE8_OUTCOME_STATUSES:
        if strict:
            raise ValueError(f"Unsupported Phase 8 Outcome status: {status_key}")
        normalized_status = "unavailable"

    return _status(normalized_head, normalized_status)


def phase8_outcome_status_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "status_key": status_key,
            "display_copy": PHASE8_OUTCOME_STATUS_COPY[status_key],
            "help_text": PHASE8_OUTCOME_STATUS_HELP[status_key],
            "display_scope": "non_numeric_status_only",
        }
        for status_key in APPROVED_PHASE8_OUTCOME_STATUSES
    ]


def phase8_outcome_head_policy_rows() -> list[dict[str, str]]:
    rows = [
        {"head": head, "policy": "eligible"}
        for head in ELIGIBLE_PHASE8_OUTCOME_HEADS
    ]
    rows.extend(
        {"head": head, "policy": "unavailable"}
        for head in EXCLUDED_PHASE8_OUTCOME_HEADS
    )
    return rows


def _status(head: str, status_key: str) -> Phase8OutcomeStatus:
    return Phase8OutcomeStatus(
        head=head,
        status_key=status_key,
        display_copy=PHASE8_OUTCOME_STATUS_COPY[status_key],
        help_text=PHASE8_OUTCOME_STATUS_HELP[status_key],
    )


def _normalize(value: str | None) -> str:
    return str(value or "").strip().lower()
