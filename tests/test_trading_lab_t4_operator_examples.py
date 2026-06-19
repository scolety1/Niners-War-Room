from __future__ import annotations

from src.trading_lab.source_inventory import (
    PaperJournalEntry,
    ResearchSourceMetadata,
    WatchlistNote,
    validate_paper_journal_entry,
    validate_research_config,
    validate_source_metadata,
    validate_watchlist_note,
)


def test_t4_operator_source_review_accepts_manual_public_source() -> None:
    source = ResearchSourceMetadata(
        source_id="operator_sec_review",
        name="Operator SEC filing review",
        category="public_company_filings",
        intended_use="education_research",
        access_method="manual public website review",
        attribution="SEC EDGAR public filing URL and filing date",
        reviewed_on="2026-06-18",
        notes="Paper-only source review.",
    )

    assert validate_source_metadata(source) == ()


def test_t4_operator_source_review_rejects_broker_api_dependency() -> None:
    source = ResearchSourceMetadata(
        source_id="blocked_broker_api",
        name="Blocked broker API source",
        category="public_market_data",
        intended_use="source_inventory",
        access_method="broker API integration",
        attribution="Invalid operator example",
    )

    assert "prohibited_execution_language" in {
        issue.code for issue in validate_source_metadata(source)
    }


def test_t4_operator_rejects_broker_token_config() -> None:
    issues = validate_research_config({"broker": {"token": "placeholder"}})

    assert "secret_like_field" in {issue.code for issue in issues}


def test_t4_operator_watchlist_accepts_manual_review_language() -> None:
    note = WatchlistNote(
        symbol="REVIEW",
        research_theme="Manual review of public source quality",
        hypothesis="Paper-only hypothesis about source attribution quality.",
        public_sources=("SEC EDGAR public filing URL",),
        risk_notes="Source interpretation may be incomplete.",
        paper_only=True,
        review_date="2026-06-18",
    )

    assert validate_watchlist_note(note) == ()


def test_t4_operator_watchlist_rejects_order_language() -> None:
    note = WatchlistNote(
        symbol="FAKE",
        research_theme="Invalid operator example",
        hypothesis="Place order after manual review.",
        public_sources=("Manual paper note",),
        risk_notes="Invalid example.",
        paper_only=True,
        review_date="2026-06-18",
    )

    assert "prohibited_execution_language" in {
        issue.code for issue in validate_watchlist_note(note)
    }


def test_t4_operator_paper_journal_rejects_brokerage_balance_language() -> None:
    entry = PaperJournalEntry(
        journal_id="PJ-T4-001",
        date="2026-06-18",
        symbol_or_topic="SIM",
        asset_type="Fictional paper placeholder",
        research_question="How should operator workflow reject account data?",
        paper_action_type="Hypothetical paper observation",
        hypothetical_entry_reference="Manual public reference",
        hypothetical_exit_reference="Future manual public reference",
        position_sizing_hypothesis="Use brokerage balance for sizing.",
        risk_hypothesis="Invalid private account dependency.",
        invalidation_condition="Reject immediately.",
        outcome_review_date="2026-07-18",
        lessons_learned="Private account language must be blocked.",
        status="Rejected example",
        notes="Research-only test fixture.",
    )

    assert "prohibited_private_account_language" in {
        issue.code for issue in validate_paper_journal_entry(entry)
    }
