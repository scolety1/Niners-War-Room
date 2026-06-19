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


def test_t3_source_inventory_accepts_public_filing_example() -> None:
    source = ResearchSourceMetadata(
        source_id="sec_edgar_public_filing",
        name="SEC EDGAR public filing page",
        category="public_company_filings",
        intended_use="source_inventory",
        access_method="manual public website review",
        attribution="SEC EDGAR filing URL, form type, and filing date",
        reviewed_on="2026-06-18",
        notes="Research-only public filing source.",
    )

    assert validate_source_metadata(source) == ()


def test_t3_source_inventory_rejects_broker_export_example() -> None:
    source = ResearchSourceMetadata(
        source_id="private_brokerage_export",
        name="Private brokerage export",
        category="private_brokerage_data",
        intended_use="source_inventory",
        access_method="manual account download",
        attribution="Private account export",
    )

    assert "prohibited_source_category" in {
        issue.code for issue in validate_source_metadata(source)
    }


def test_t3_source_inventory_rejects_secret_config_example() -> None:
    issues = validate_research_config(
        {
            "source_name": "blocked token example",
            "auth": {"token": "placeholder"},
        }
    )

    assert "secret_like_field" in {issue.code for issue in issues}


def test_t3_watchlist_accepts_safe_fake_example() -> None:
    note = WatchlistNote(
        symbol="REVIEW",
        research_theme="Public filing follow-up",
        hypothesis="Paper-only question about whether a public source changes over time.",
        public_sources=("SEC EDGAR public filings",),
        risk_notes="Single-source interpretation may be incomplete.",
        paper_only=True,
        review_date="2026-06-18",
    )

    assert validate_watchlist_note(note) == ()


def test_t3_watchlist_rejects_auto_execution_example() -> None:
    note = WatchlistNote(
        symbol="SIM",
        research_theme="Invalid execution command",
        hypothesis="Auto-execute when the paper threshold is crossed.",
        public_sources=("Manual paper note",),
        risk_notes="Invalid example.",
        paper_only=True,
        review_date="2026-06-18",
    )

    assert "prohibited_execution_language" in {
        issue.code for issue in validate_watchlist_note(note)
    }


def test_t3_paper_journal_rejects_personalized_account_balance_example() -> None:
    entry = PaperJournalEntry(
        journal_id="PJ-T3-001",
        date="2026-06-18",
        symbol_or_topic="PAPER",
        asset_type="Fictional paper placeholder",
        research_question="How should invalid examples be rejected?",
        paper_action_type="Hypothetical paper observation",
        hypothetical_entry_reference="Manual public reference",
        hypothetical_exit_reference="Future manual public reference",
        position_sizing_hypothesis="Use account balance for sizing.",
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
