"""Research-only Trading Lab contracts and validators."""

from src.trading_lab.source_inventory import (
    ALLOWED_SOURCE_CATEGORIES,
    ALLOWED_SOURCE_USES,
    MANUAL_ARTIFACT_REQUIRED_FIELDS,
    PAPER_JOURNAL_REQUIRED_FIELDS,
    PROHIBITED_SOURCE_CATEGORIES,
    PaperJournalEntry,
    ResearchSourceMetadata,
    ValidationIssue,
    WatchlistNote,
    assert_valid_source_metadata,
    validate_artifact_text_fields,
    validate_manual_artifact_payload,
    validate_paper_journal_entry,
    validate_research_config,
    validate_source_metadata,
    validate_watchlist_note,
)

__all__ = [
    "ALLOWED_SOURCE_CATEGORIES",
    "ALLOWED_SOURCE_USES",
    "MANUAL_ARTIFACT_REQUIRED_FIELDS",
    "PROHIBITED_SOURCE_CATEGORIES",
    "PAPER_JOURNAL_REQUIRED_FIELDS",
    "PaperJournalEntry",
    "ResearchSourceMetadata",
    "ValidationIssue",
    "WatchlistNote",
    "assert_valid_source_metadata",
    "validate_artifact_text_fields",
    "validate_manual_artifact_payload",
    "validate_paper_journal_entry",
    "validate_research_config",
    "validate_source_metadata",
    "validate_watchlist_note",
]
