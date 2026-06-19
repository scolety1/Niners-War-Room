from __future__ import annotations

from src.trading_lab.source_inventory import validate_manual_review_packet


def _valid_packet(**overrides: object) -> dict[str, object]:
    packet: dict[str, object] = {
        "packet_id": "MRP-EXMPL",
        "intake_section": {"summary": "Paper-only research question for EXMPL."},
        "source_review_section": {"summary": "Public source review only."},
        "watchlist_section": {"summary": "Paper-only watchlist note."},
        "risk_review_section": {"summary": "Source quality risk reviewed."},
        "paper_journal_section": {"summary": "Manual paper journal review."},
        "closeout_section": {"summary": "Closed lessons with no advice."},
    }
    packet.update(overrides)
    return packet


def test_t9_valid_manual_review_packet_is_accepted() -> None:
    assert validate_manual_review_packet(_valid_packet()) == ()


def test_t9_packet_with_broker_token_is_rejected() -> None:
    issues = validate_manual_review_packet(
        _valid_packet(source_review_section={"summary": "Use broker token."})
    )

    assert "prohibited_broker_credential_language" in {issue.code for issue in issues}


def test_t9_packet_with_order_language_is_rejected() -> None:
    issues = validate_manual_review_packet(
        _valid_packet(closeout_section={"summary": "Place order after review."})
    )

    assert "prohibited_execution_language" in {issue.code for issue in issues}


def test_t9_packet_with_private_account_balance_is_rejected() -> None:
    issues = validate_manual_review_packet(
        _valid_packet(risk_review_section={"summary": "Use account balance."})
    )

    assert "prohibited_private_account_language" in {issue.code for issue in issues}


def test_t9_packet_with_data_ingestion_output_request_is_rejected() -> None:
    issues = validate_manual_review_packet(
        _valid_packet(paper_journal_section={"summary": "Start data ingestion."})
    )

    assert "prohibited_data_workflow_language" in {issue.code for issue in issues}


def test_t9_incomplete_packet_returns_hold() -> None:
    issues = validate_manual_review_packet({"packet_id": "MRP-HOLD"})

    assert "hold_missing_packet_section" in {issue.code for issue in issues}
