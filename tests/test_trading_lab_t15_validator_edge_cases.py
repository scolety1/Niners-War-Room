from src.trading_lab import (
    FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL,
    classify_future_phase_request,
    validate_artifact_text_fields,
    validate_future_phase_request,
    validate_manual_artifact_payload,
    validate_research_config,
)


def issue_codes(issues):
    return {issue.code for issue in issues}


def test_mixed_case_punctuation_broker_api_order_and_secret_terms_rejected() -> None:
    issues = validate_artifact_text_fields(
        "strategy_note",
        {
            "note": "Do not add BroKer/API support, PlaCe-Order steps, or API-Key text.",
        },
    )

    codes = issue_codes(issues)

    assert "prohibited_execution_language" in codes
    assert "prohibited_broker_credential_language" in codes


def test_nested_manual_artifact_values_are_rejected() -> None:
    payload = {
        "strategy_note_id": "STRAT-FAKE-001",
        "title": "Nested fake note",
        "research_question": "What evidence would change this paper-only view?",
        "hypothesis": {"unsafe": "Auto-execute if PAPER crosses a threshold."},
        "evidence_sources": ["Manual source review"],
        "risks": ["Execution drift"],
        "invalidation_conditions": "Manual invalidation only",
        "status": "draft",
    }

    issues = validate_manual_artifact_payload("strategy_note", payload)

    assert "prohibited_execution_language" in issue_codes(issues)


def test_nested_research_config_list_values_are_rejected() -> None:
    config = {
        "review_steps": [
            "manual source review",
            {"unsafe": "Store Bearer abcdefghijklmnopqrstuvwxyz123456"},
        ]
    }

    issues = validate_research_config(config)

    assert "secret_like_value" in issue_codes(issues)


def test_safe_fake_research_language_is_accepted() -> None:
    issues = validate_artifact_text_fields(
        "risk_journal",
        {
            "risk": "Review whether the EXMPL thesis depends on one public source.",
            "mitigation": "Schedule manual review and record paper-only lessons learned.",
        },
    )

    assert issues == ()


def test_empty_required_values_are_rejected() -> None:
    issues = validate_manual_artifact_payload(
        "research_intake",
        {
            "intake_id": "INTAKE-FAKE-001",
            "date": "",
            "research_question": "   ",
            "paper_only_intent": "yes",
            "status": "draft",
        },
    )

    assert "required" in issue_codes(issues)


def test_unsupported_artifact_type_is_rejected() -> None:
    issues = validate_manual_artifact_payload("execution_ticket", {"id": "FAKE"})

    assert issue_codes(issues) == {"unknown_artifact_type"}


def test_ambiguous_future_implementation_request_is_held() -> None:
    request = "Prepare a future implementation outline for possible simulation tooling."

    assert classify_future_phase_request(request) == FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL
    assert validate_future_phase_request(request)[0].code == "hold_needs_explicit_approval"


def test_future_data_ingestion_request_is_held() -> None:
    request = "Discuss data-ingestion requirements for a later approved phase."

    assert classify_future_phase_request(request) == FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL
    assert validate_future_phase_request(request)[0].code == "hold_needs_explicit_approval"
