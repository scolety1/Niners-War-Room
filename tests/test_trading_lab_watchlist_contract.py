from __future__ import annotations

from src.trading_lab.source_inventory import WatchlistNote, validate_watchlist_note


def test_watchlist_note_accepts_paper_only_public_source_note() -> None:
    note = WatchlistNote(
        symbol="ABC",
        research_theme="Public filing revenue trend observation",
        hypothesis="Paper-only review of whether reported revenue trend merits follow-up.",
        public_sources=("https://example.test/public-filing",),
        risk_notes="Observation may be incomplete without broader market context.",
        paper_only=True,
        review_date="2026-06-18",
    )

    assert validate_watchlist_note(note) == ()


def test_watchlist_note_requires_paper_only_flag() -> None:
    note = WatchlistNote(
        symbol="ABC",
        research_theme="Public news review",
        hypothesis="Research note only.",
        public_sources=("https://example.test/public-news",),
        risk_notes="No private account data.",
        paper_only=False,
        review_date="2026-06-18",
    )

    issues = validate_watchlist_note(note)

    assert {issue.code for issue in issues} == {"paper_only_required"}


def test_watchlist_note_blocks_order_language() -> None:
    note = WatchlistNote(
        symbol="ABC",
        research_theme="Public news review",
        hypothesis="Use broker order endpoint after the note is reviewed.",
        public_sources=("https://example.test/public-news",),
        risk_notes="No private account data.",
        paper_only=True,
        review_date="2026-06-18",
    )

    issues = validate_watchlist_note(note)

    assert "prohibited_execution_language" in {issue.code for issue in issues}
