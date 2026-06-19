from __future__ import annotations

from src.trading_lab.source_inventory import (
    PaperJournalEntry,
    validate_paper_journal_entry,
)


def _valid_entry(**overrides: str) -> PaperJournalEntry:
    values = {
        "journal_id": "PJ-EXMPL-001",
        "date": "2026-06-18",
        "symbol_or_topic": "EXMPL",
        "asset_type": "Fictional equity placeholder",
        "research_question": "How would a public filing note behave in paper review?",
        "paper_action_type": "Hypothetical paper observation",
        "hypothetical_entry_reference": "Manual public closing reference",
        "hypothetical_exit_reference": "Future manual public closing reference",
        "position_sizing_hypothesis": "Fixed fictional paper unit",
        "risk_hypothesis": "Public evidence may contradict the hypothesis",
        "invalidation_condition": "Close if no public source supports the note",
        "outcome_review_date": "2026-07-18",
        "lessons_learned": "Pending paper review",
        "status": "Open paper note",
        "notes": "Research-only and paper-only.",
    }
    values.update(overrides)
    return PaperJournalEntry(**values)


def test_paper_journal_entry_accepts_valid_paper_only_note() -> None:
    assert validate_paper_journal_entry(_valid_entry()) == ()


def test_paper_journal_entry_blocks_execution_language() -> None:
    issues = validate_paper_journal_entry(
        _valid_entry(notes="Auto-execute if price crosses the paper level.")
    )

    assert "prohibited_execution_language" in {issue.code for issue in issues}


def test_paper_journal_entry_blocks_private_account_language() -> None:
    issues = validate_paper_journal_entry(
        _valid_entry(position_sizing_hypothesis="Use brokerage balance for sizing.")
    )

    assert "prohibited_private_account_language" in {issue.code for issue in issues}


def test_paper_journal_entry_blocks_secret_like_values() -> None:
    issues = validate_paper_journal_entry(
        _valid_entry(notes="Bearer abcdefghijklmnopqrstuvwxyz123456")
    )

    assert "secret_like_value" in {issue.code for issue in issues}


def test_paper_journal_entry_requires_iso_dates() -> None:
    issues = validate_paper_journal_entry(_valid_entry(date="06/18/2026"))

    assert ("date", "invalid_date") in {(issue.field, issue.code) for issue in issues}
