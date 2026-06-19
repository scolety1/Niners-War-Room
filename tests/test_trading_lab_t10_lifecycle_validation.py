from __future__ import annotations

from src.trading_lab.schema_registry import is_valid_lifecycle_transition
from src.trading_lab.source_inventory import validate_lifecycle_transition


def test_t10_valid_transition_is_accepted() -> None:
    assert validate_lifecycle_transition("IDEA", "SOURCE_REVIEW", "Manual review.") == ()
    assert is_valid_lifecycle_transition("IDEA", "SOURCE_REVIEW")


def test_t10_invalid_transition_is_rejected() -> None:
    issues = validate_lifecycle_transition("IDEA", "PAPER_JOURNAL_OPEN", "Too soon.")

    assert "invalid_lifecycle_transition" in {issue.code for issue in issues}


def test_t10_transition_to_real_order_placement_is_rejected() -> None:
    issues = validate_lifecycle_transition(
        "RISK_REVIEW", "PAPER_JOURNAL_OPEN", "Place order after review."
    )

    assert "prohibited_execution_language" in {issue.code for issue in issues}


def test_t10_broker_api_credential_transition_is_rejected() -> None:
    issues = validate_lifecycle_transition(
        "SOURCE_REVIEW", "WATCHLIST_NOTE", "Connect broker with API key."
    )

    issue_codes = {issue.code for issue in issues}
    assert "prohibited_broker_credential_language" in issue_codes


def test_t10_auto_execution_transition_is_rejected() -> None:
    issues = validate_lifecycle_transition(
        "WATCHLIST_NOTE", "RISK_REVIEW", "Auto-execute when threshold appears."
    )

    assert "prohibited_execution_language" in {issue.code for issue in issues}


def test_t10_private_account_transition_is_rejected() -> None:
    issues = validate_lifecycle_transition(
        "SOURCE_REVIEW", "WATCHLIST_NOTE", "Use account balance."
    )

    assert "prohibited_private_account_language" in {issue.code for issue in issues}
