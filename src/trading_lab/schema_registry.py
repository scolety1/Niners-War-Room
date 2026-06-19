from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.source_inventory import MANUAL_ARTIFACT_REQUIRED_FIELDS

CORE_ARTIFACT_TYPES = (
    "source_inventory",
    "research_intake",
    "manual_lifecycle",
    "watchlist_note",
    "strategy_note",
    "risk_journal",
    "paper_journal",
    "manual_review_packet",
    "blocked_work_gate",
)

PROHIBITED_FIELD_NAMES = frozenset(
    {
        "api_key",
        "token",
        "secret",
        "password",
        "broker_account",
        "account_balance",
        "private_brokerage_export",
        "order_id",
        "execution_endpoint",
    }
)

ALLOWED_STATUS_BY_ARTIFACT = {
    "research_intake": (
        "IDEA",
        "SOURCE_REVIEW",
        "HOLD_NEEDS_REVIEW",
        "REJECTED_PROHIBITED",
        "READY_FOR_WATCHLIST_NOTE",
        "CLOSED_NO_ACTION",
    ),
    "manual_lifecycle": (
        "IDEA",
        "SOURCE_REVIEW",
        "WATCHLIST_NOTE",
        "RISK_REVIEW",
        "PAPER_JOURNAL_OPEN",
        "PAPER_REVIEW_DUE",
        "CLOSED_LESSONS",
        "REJECTED_PROHIBITED",
        "HOLD_NEEDS_REVIEW",
    ),
    "watchlist_note": (
        "OBSERVE",
        "NEEDS_MORE_PUBLIC_EVIDENCE",
        "READY_FOR_RISK_REVIEW",
        "HOLD_NEEDS_REVIEW",
        "CLOSED_LESSONS",
        "REJECTED_PROHIBITED",
    ),
    "strategy_note": (
        "DRAFT_RESEARCH",
        "SOURCE_REVIEW",
        "RISK_REVIEW",
        "PAPER_TEST_DESIGN_ONLY",
        "HOLD_NEEDS_REVIEW",
        "CLOSED_LESSONS",
        "REJECTED_PROHIBITED",
    ),
    "risk_journal": (
        "OPEN",
        "MITIGATED",
        "HOLD_NEEDS_REVIEW",
        "CLOSED_LESSONS",
        "REJECTED_PROHIBITED",
    ),
    "paper_journal": (
        "OPEN",
        "REVIEW_DUE",
        "REVIEWED_LESSONS_CAPTURED",
        "HOLD_NEEDS_REVIEW",
        "REJECTED_PROHIBITED",
    ),
    "manual_review_packet": (
        "ACCEPT",
        "HOLD_NEEDS_REVIEW",
        "REJECTED_PROHIBITED",
        "CLOSED_LESSONS",
    ),
    "blocked_work_gate": (
        "ALLOW_RESEARCH_ONLY",
        "HOLD_NEEDS_EXPLICIT_APPROVAL",
        "REJECT_PROHIBITED",
    ),
    "source_inventory": (
        "ACCEPT",
        "HOLD_FOR_MANUAL_REVIEW",
        "REJECT",
    ),
}


@dataclass(frozen=True)
class ArtifactSchema:
    artifact_type: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    allowed_statuses: tuple[str, ...]


SCHEMA_REGISTRY = {
    artifact_type: ArtifactSchema(
        artifact_type=artifact_type,
        required_fields=MANUAL_ARTIFACT_REQUIRED_FIELDS.get(artifact_type, ()),
        optional_fields=("notes", "operator", "review_date"),
        allowed_statuses=ALLOWED_STATUS_BY_ARTIFACT.get(artifact_type, ()),
    )
    for artifact_type in CORE_ARTIFACT_TYPES
}


def schema_for_artifact(artifact_type: str) -> ArtifactSchema | None:
    return SCHEMA_REGISTRY.get(artifact_type)


def prohibited_field_names_in(fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(field for field in fields if field.lower() in PROHIBITED_FIELD_NAMES)
