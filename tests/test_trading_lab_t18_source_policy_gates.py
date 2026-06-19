from src.trading_lab import (
    SOURCE_POLICY_ACCEPT_PUBLIC_MANUAL_REFERENCE,
    SOURCE_POLICY_HOLD_NEEDS_REVIEW,
    SOURCE_POLICY_REJECT_PROHIBITED,
    classify_source_policy_payload,
    validate_source_policy_payload,
)


def test_public_source_policy_payload_is_accepted() -> None:
    payload = {
        "source_name": "FRED public economic data reference",
        "public_private_status": "public manual reference",
        "license_terms_review_status": "reviewed for manual citation",
        "approved_use": "paper-only research notes",
    }

    assert classify_source_policy_payload(payload) == SOURCE_POLICY_ACCEPT_PUBLIC_MANUAL_REFERENCE
    assert validate_source_policy_payload(payload) == ()


def test_unclear_license_source_policy_payload_is_held() -> None:
    payload = {
        "source_name": "Example public page",
        "license_terms_review_status": "license unclear",
        "redistribution_storage_notes": "review required",
    }

    assert classify_source_policy_payload(payload) == SOURCE_POLICY_HOLD_NEEDS_REVIEW
    assert validate_source_policy_payload(payload)[0].code == "hold_source_policy_review"


def test_private_brokerage_export_source_policy_payload_is_rejected() -> None:
    payload = {
        "source_name": "private brokerage export",
        "sensitivity": "private brokerage account balance",
    }

    assert classify_source_policy_payload(payload) == SOURCE_POLICY_REJECT_PROHIBITED
    assert (
        validate_source_policy_payload(payload)[0].code
        == "reject_prohibited_source_policy"
    )


def test_credential_source_policy_payload_is_rejected() -> None:
    payload = {
        "source_name": "broker credential source",
        "notes": "requires API key or broker token",
    }

    assert classify_source_policy_payload(payload) == SOURCE_POLICY_REJECT_PROHIBITED


def test_paid_private_dump_source_policy_payload_is_held() -> None:
    payload = {
        "source_name": "paid data vendor file",
        "public_private_status": "paid data private data dump",
    }

    assert classify_source_policy_payload(payload) == SOURCE_POLICY_HOLD_NEEDS_REVIEW
