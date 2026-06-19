from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceStatus = Literal["fixture-demo", "missing", "future-integration", "placeholder"]
IntegrationStatus = Literal["fixture-only", "not-wired", "missing-data"]

FIXTURE_DEMO_LABEL = "Fixture demo value"
REAL_NWR_NOT_WIRED_LABEL = "Real NWR integration not wired"
PUBLIC_MARKET_NOT_WIRED_LABEL = "Public fantasy market source not wired"
MANUAL_REVIEW_REQUIRED_LABEL = "Manual review required"
MISSING_DATA_LABEL = "Missing data placeholder"


@dataclass(frozen=True)
class ValueProvenance:
    source_name: str
    source_type: str
    status: SourceStatus
    last_updated_label: str
    confidence_label: str
    note: str
    is_real_integration: bool


def fixture_value_provenance(source_name: str = "Trade Lab fixture provider") -> ValueProvenance:
    return ValueProvenance(
        source_name=source_name,
        source_type="fixture",
        status="fixture-demo",
        last_updated_label="static fixture",
        confidence_label="demo only",
        note=FIXTURE_DEMO_LABEL,
        is_real_integration=False,
    )


def missing_value_provenance(source_name: str, source_type: str) -> ValueProvenance:
    return ValueProvenance(
        source_name=source_name,
        source_type=source_type,
        status="missing",
        last_updated_label="not available",
        confidence_label="missing",
        note=MISSING_DATA_LABEL,
        is_real_integration=False,
    )


def future_integration_provenance(source_name: str, source_type: str) -> ValueProvenance:
    return ValueProvenance(
        source_name=source_name,
        source_type=source_type,
        status="future-integration",
        last_updated_label="not wired",
        confidence_label="unavailable",
        note="Future integration label only; not wired.",
        is_real_integration=False,
    )


def ui_data_status_labels() -> tuple[str, ...]:
    return (
        FIXTURE_DEMO_LABEL,
        REAL_NWR_NOT_WIRED_LABEL,
        PUBLIC_MARKET_NOT_WIRED_LABEL,
        MANUAL_REVIEW_REQUIRED_LABEL,
    )
