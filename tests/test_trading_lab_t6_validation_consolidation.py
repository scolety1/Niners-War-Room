from __future__ import annotations

import pytest

from src.trading_lab.source_inventory import validate_artifact_text_fields


@pytest.mark.parametrize(
    ("artifact_type", "field_name", "text", "expected_code"),
    (
        (
            "research_intake",
            "research_question",
            "Buy now after source review.",
            "prohibited_advice_language",
        ),
        (
            "watchlist_note",
            "decision_status",
            "Sell now for your account.",
            "prohibited_advice_language",
        ),
        (
            "manual_lifecycle",
            "transition_reason",
            "Place order after risk review.",
            "prohibited_execution_language",
        ),
        (
            "strategy_note",
            "paper_test_design",
            "Execute when the threshold is observed.",
            "prohibited_execution_language",
        ),
        (
            "manual_review_packet",
            "source_review_summary",
            "Use broker API for the next review.",
            "prohibited_execution_language",
        ),
        (
            "blocked_work_gate",
            "approval_note",
            "Store API key in config.",
            "prohibited_broker_credential_language",
        ),
        (
            "risk_journal",
            "risk_description",
            "Use secret key to access the source.",
            "prohibited_broker_credential_language",
        ),
        (
            "paper_journal",
            "position_sizing_hypothesis",
            "Use my private brokerage export.",
            "prohibited_private_account_language",
        ),
        (
            "paper_journal",
            "position_sizing_hypothesis",
            "Based on my account balance.",
            "prohibited_private_account_language",
        ),
        (
            "strategy_note",
            "notes",
            "Auto-execute when the paper threshold is crossed.",
            "prohibited_execution_language",
        ),
        (
            "watchlist_note",
            "notes",
            "Use an automated trigger for review.",
            "prohibited_execution_language",
        ),
        (
            "manual_review_packet",
            "notes",
            "This is production investment advice.",
            "prohibited_advice_language",
        ),
        (
            "risk_journal",
            "notes",
            "Guaranteed return if the note is followed.",
            "prohibited_advice_language",
        ),
        (
            "blocked_work_gate",
            "proposal_note",
            "Start data ingestion for market data.",
            "prohibited_data_workflow_language",
        ),
        (
            "blocked_work_gate",
            "proposal_note",
            "Write generated outputs for review.",
            "prohibited_data_workflow_language",
        ),
        (
            "manual_review_packet",
            "notes",
            "Bearer abcdefghijklmnopqrstuvwxyz123456",
            "secret_like_value",
        ),
    ),
)
def test_t6_rejects_prohibited_language_across_artifacts(
    artifact_type: str,
    field_name: str,
    text: str,
    expected_code: str,
) -> None:
    issues = validate_artifact_text_fields(artifact_type, {field_name: text})

    assert expected_code in {issue.code for issue in issues}


@pytest.mark.parametrize(
    ("artifact_type", "fields"),
    (
        (
            "research_intake",
            {
                "research_question": "What public source evidence should be reviewed?",
                "paper_only_intent": "Paper-only learning goal for EXMPL.",
            },
        ),
        (
            "manual_lifecycle",
            {
                "transition_reason": "Move PAPER from source review to risk review.",
                "guardrail_check": "Manual review only with no private data.",
            },
        ),
        (
            "watchlist_note",
            {
                "hypothesis": "Paper-only hypothesis for REVIEW based on public sources.",
                "invalidation_condition": "Close if public evidence is absent.",
            },
        ),
        (
            "strategy_note",
            {
                "hypothesis": "Research question about SIM and public evidence quality.",
                "assumptions": "Manual review and no artifact files.",
            },
        ),
        (
            "risk_journal",
            {
                "risk_description": "Source interpretation may be incomplete.",
                "mitigation_note": "Require manual public-source review.",
            },
        ),
        (
            "paper_journal",
            {
                "lessons_learned": "FAKE note improved after adding an invalidation condition.",
                "status": "Closed lessons.",
            },
        ),
        (
            "manual_review_packet",
            {
                "source_review_summary": "Public source terms need manual review.",
                "next_safe_step": "Hold until attribution is clear.",
            },
        ),
    ),
)
def test_t6_accepts_safe_paper_research_language(
    artifact_type: str,
    fields: dict[str, str],
) -> None:
    assert validate_artifact_text_fields(artifact_type, fields) == ()
