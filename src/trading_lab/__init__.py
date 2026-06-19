"""Research-only Trading Lab contracts and validators."""

from src.trading_lab.source_inventory import (
    ALLOWED_SOURCE_CATEGORIES,
    ALLOWED_SOURCE_USES,
    PROHIBITED_SOURCE_CATEGORIES,
    ResearchSourceMetadata,
    ValidationIssue,
    WatchlistNote,
    assert_valid_source_metadata,
    validate_research_config,
    validate_source_metadata,
    validate_watchlist_note,
)

__all__ = [
    "ALLOWED_SOURCE_CATEGORIES",
    "ALLOWED_SOURCE_USES",
    "PROHIBITED_SOURCE_CATEGORIES",
    "ResearchSourceMetadata",
    "ValidationIssue",
    "WatchlistNote",
    "assert_valid_source_metadata",
    "validate_research_config",
    "validate_source_metadata",
    "validate_watchlist_note",
]
