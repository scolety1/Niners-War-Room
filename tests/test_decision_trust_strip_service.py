from __future__ import annotations

from src.services.decision_trust_strip_service import (
    FIELD_LABELS,
    FIELD_ORDER,
    GATED,
    IDENTITY_EXCEPTION,
    MISSING,
    NOT_ENOUGH_INFORMATION,
    SOURCE_EXCEPTION,
    STALE,
    UNAVAILABLE,
    VALID_CURRENT,
    build_decision_trust_strip,
    build_rankings_dataset_trust_strip,
    state_from_existing_status,
)


def test_canonical_field_order_and_label_mapping_are_frozen() -> None:
    strip = build_decision_trust_strip(
        {},
        surface="Player Compare",
        entity_label="Fixture Player",
        receipt_label="Existing details",
        receipt_available=False,
    )
    assert tuple(field.key for field in strip.fields) == FIELD_ORDER
    assert tuple(field.label for field in strip.fields) == tuple(
        FIELD_LABELS[key] for key in FIELD_ORDER
    )


def test_distinct_existing_statuses_do_not_collapse() -> None:
    states = {
        state_from_existing_status("GREEN_CURRENT", field="as_of_freshness"),
        state_from_existing_status("YELLOW_STALE", field="as_of_freshness"),
        state_from_existing_status("missing receipt", field="evidence_source"),
        state_from_existing_status("gated / not admitted", field="evidence_source"),
        state_from_existing_status("source unavailable", field="evidence_source"),
    }
    assert states == {VALID_CURRENT, STALE, MISSING, GATED, UNAVAILABLE}


def test_identity_and_source_exceptions_preserve_existing_caveats() -> None:
    strip = build_decision_trust_strip(
        {
            "source_status": "review-only source restriction",
            "freshness_status": "YELLOW_STALE",
            "identity_join_status": "identity review required",
            "missing_evidence": "Missing evidence: 2",
            "warnings": "source caveat: partial receipt",
        },
        surface="Player Compare",
        entity_label="Fixture Player",
        receipt_label="Existing details",
        receipt_available=True,
    )
    assert strip.field("evidence_source").state == SOURCE_EXCEPTION
    assert strip.field("as_of_freshness").state == STALE
    assert strip.field("identity_join").state == IDENTITY_EXCEPTION
    assert strip.field("missingness_completeness").state == MISSING
    assert strip.field("material_caveats").state == SOURCE_EXCEPTION
    assert strip.field("receipt_details").state == VALID_CURRENT


def test_missing_receipt_and_empty_values_remain_distinct() -> None:
    strip = build_decision_trust_strip(
        {"player_id": "admitted-id"},
        surface="Trading Lab",
        entity_label="Fixture Asset",
        receipt_label="Existing details",
        receipt_available=False,
    )
    assert strip.field("identity_join").state == VALID_CURRENT
    assert strip.field("evidence_source").state == NOT_ENOUGH_INFORMATION
    assert strip.field("receipt_details").state == UNAVAILABLE


def test_rankings_adapter_uses_passed_facts_without_calculating_new_thresholds() -> None:
    strip = build_rankings_dataset_trust_strip(
        source_available=True,
        source_label="approved.csv",
        source_hash="abc123",
        freshness_status="YELLOW_STALE",
        identity_review_rows=3,
        missing_rows=4,
        warnings=("existing warning",),
    )
    assert strip.field("evidence_source").state == VALID_CURRENT
    assert strip.field("as_of_freshness").state == STALE
    assert strip.field("identity_join").state == IDENTITY_EXCEPTION
    assert strip.field("missingness_completeness").state == MISSING
    assert "abc123" in strip.field("receipt_details").value
