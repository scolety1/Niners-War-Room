from __future__ import annotations

import pytest

from src.trading_lab.source_inventory import validate_manual_artifact_payload

VALID_PAYLOADS = {
    "research_intake": {
        "intake_id": "RI-EXMPL",
        "date": "2026-06-18",
        "research_question": "What public source should be reviewed?",
        "paper_only_intent": "Paper-only research question.",
        "status": "IDEA",
    },
    "manual_lifecycle": {
        "lifecycle_id": "LC-PAPER",
        "from_status": "IDEA",
        "to_status": "SOURCE_REVIEW",
        "transition_reason": "Manual source review is ready.",
        "guardrail_check": "No private data or execution path.",
    },
    "watchlist_note": {
        "symbol": "REVIEW",
        "research_theme": "Public source review",
        "hypothesis": "Paper-only hypothesis.",
        "public_sources": "SEC public filing",
        "risk_notes": "Source may be incomplete.",
        "paper_only": "true",
        "review_date": "2026-06-18",
    },
    "strategy_note": {
        "strategy_note_id": "SN-SIM",
        "title": "Paper strategy question",
        "research_question": "How should public evidence be reviewed?",
        "hypothesis": "Paper-only hypothesis.",
        "evidence_sources": "Public source names.",
        "risks": "Source quality risk.",
        "invalidation_conditions": "Close if evidence is absent.",
        "status": "DRAFT_RESEARCH",
    },
    "risk_journal": {
        "risk_id": "RJ-FAKE",
        "risk_category": "THESIS_RISK",
        "risk_description": "Hypothesis may be incomplete.",
        "severity": "MEDIUM",
        "probability": "UNKNOWN",
        "mitigation_note": "Manual review.",
        "status": "OPEN",
    },
    "paper_journal": {
        "journal_id": "PJ-PAPER",
        "date": "2026-06-18",
        "symbol_or_topic": "PAPER",
        "asset_type": "Fictional placeholder",
        "research_question": "What was learned?",
        "paper_action_type": "NO_ACTION_OBSERVATION",
        "hypothetical_entry_reference": "Manual reference",
        "hypothetical_exit_reference": "Manual future reference",
        "position_sizing_hypothesis": "Fixed fictional unit.",
        "risk_hypothesis": "Source may be incomplete.",
        "invalidation_condition": "Close if public evidence is absent.",
        "outcome_review_date": "2026-07-18",
        "lessons_learned": "Pending.",
        "status": "OPEN",
        "notes": "Paper-only.",
    },
    "manual_review_packet": {
        "packet_id": "MRP-EXMPL",
        "research_item_id": "RI-EXMPL",
        "artifact_type": "research_intake",
        "source_review_summary": "Public source review.",
        "prohibited_language_check": "Passed.",
        "closeout_status": "HOLD_NEEDS_REVIEW",
    },
}


@pytest.mark.parametrize("artifact_type", sorted(VALID_PAYLOADS))
def test_t7_valid_manual_artifact_payloads_are_accepted(artifact_type: str) -> None:
    assert validate_manual_artifact_payload(artifact_type, VALID_PAYLOADS[artifact_type]) == ()


@pytest.mark.parametrize("artifact_type", sorted(VALID_PAYLOADS))
def test_t7_manual_artifact_payloads_reject_prohibited_language(artifact_type: str) -> None:
    payload = {**VALID_PAYLOADS[artifact_type], "notes": "Buy now and place order."}

    issues = validate_manual_artifact_payload(artifact_type, payload)

    issue_codes = {issue.code for issue in issues}
    assert "prohibited_advice_language" in issue_codes
    assert "prohibited_execution_language" in issue_codes


def test_t7_manual_artifact_payload_requires_core_fields() -> None:
    issues = validate_manual_artifact_payload("research_intake", {"status": "IDEA"})

    assert "required" in {issue.code for issue in issues}


def test_t7_manual_artifact_payload_rejects_unknown_artifact_type() -> None:
    issues = validate_manual_artifact_payload("broker_order", {"status": "IDEA"})

    assert issues[0].code == "unknown_artifact_type"
