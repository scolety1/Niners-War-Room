from __future__ import annotations

import pytest

from src.trading_lab.source_inventory import validate_artifact_text_fields


@pytest.mark.parametrize(
    ("artifact_type", "field_name", "text", "expected_code"),
    (
        (
            "research_intake",
            "research_question",
            "Buy now after the public source is reviewed.",
            "prohibited_advice_language",
        ),
        (
            "manual_lifecycle",
            "transition_note",
            "Connect broker before moving to review.",
            "prohibited_broker_credential_language",
        ),
        (
            "watchlist_note",
            "hypothesis",
            "Place order when the manual review is done.",
            "prohibited_execution_language",
        ),
        (
            "strategy_note",
            "assumptions",
            "This has guaranteed return potential.",
            "prohibited_advice_language",
        ),
        (
            "risk_journal",
            "risk_description",
            "Risk depends on my brokerage balance.",
            "prohibited_private_account_language",
        ),
        (
            "paper_journal",
            "notes",
            "Use broker token for the next review.",
            "prohibited_broker_credential_language",
        ),
        (
            "paper_journal",
            "notes",
            "Bearer abcdefghijklmnopqrstuvwxyz123456",
            "secret_like_value",
        ),
    ),
)
def test_t5_rejects_prohibited_language_across_artifact_types(
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
                "paper_only_intent": "Paper-only learning note.",
            },
        ),
        (
            "strategy_note",
            {
                "hypothesis": "Paper-only hypothesis about public-source behavior.",
                "invalidation_notes": "Close the note if public evidence is absent.",
            },
        ),
        (
            "risk_journal",
            {
                "risk_description": "Source interpretation may be incomplete.",
                "mitigation_note": "Require manual public-source review.",
            },
        ),
    ),
)
def test_t5_accepts_safe_research_language(
    artifact_type: str,
    fields: dict[str, str],
) -> None:
    assert validate_artifact_text_fields(artifact_type, fields) == ()
