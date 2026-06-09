import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md"
ROOKIE_ROWS = (
    ROOT
    / "local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
)


def _rows() -> list[dict[str, str]]:
    with ROOKIE_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _watchlist_rows() -> list[dict[str, str]]:
    rows = _rows()
    return [
        row
        for row in rows
        if row["evidence_status"] == "watchlist_data_incomplete"
        or "watchlist" in row["draft_board_band"]
    ]


def _score(row: dict[str, str]) -> float:
    return float(row["league_format_adjusted_score"])


def test_rookie_watchlist_report_discloses_source_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "rookie_draft_board_review_rows.csv" in text
    assert "league_format_adjusted_score" in text
    assert "prospect_private_value_review_score" in text
    assert "review_only_rookie_board_context_not_final_pick" in text
    assert "do_not_use_as_final_rookie_draft_recommendation" in text
    assert "does not change rookie weights" in text
    assert "Do not change rookie weights" in text
    assert "does not promote any watchlist row into a confident pick lane" in text


def test_rookie_watchlist_report_matches_union_counts():
    text = REPORT.read_text(encoding="utf-8")
    watchlist_rows = _watchlist_rows()
    evidence_counts = Counter(row["evidence_status"] for row in watchlist_rows)
    band_counts = Counter(row["draft_board_band"] for row in watchlist_rows)

    assert len(_rows()) == 210
    assert len(watchlist_rows) == 43
    assert evidence_counts["draftable_review"] == 22
    assert evidence_counts["watchlist_data_incomplete"] == 21
    assert band_counts["watchlist_context_review"] == 22
    assert band_counts["watchlist_or_data_incomplete_context_review"] == 21
    assert sum(_score(row) >= 50 for row in watchlist_rows) == 0
    assert sum(30 <= _score(row) < 40 for row in watchlist_rows) == 1
    assert sum(20 <= _score(row) < 30 for row in watchlist_rows) == 21
    assert sum(_score(row) < 20 for row in watchlist_rows) == 21
    assert "Watchlist/data-incomplete union rows reviewed: 43." in text
    assert "50 or above: 0." in text
    assert "20 to 29.999: 21." in text


def test_rookie_watchlist_report_lists_every_union_prospect():
    text = REPORT.read_text(encoding="utf-8")

    for row in _watchlist_rows():
        assert row["prospect_name"] in text
        assert f"| {row['board_rank']} | {row['prospect_name']} |" in text


def test_rookie_watchlist_report_flags_daniel_sobkowicz_as_incomplete():
    text = REPORT.read_text(encoding="utf-8")
    daniel = next(
        row for row in _rows() if row["prospect_name"] == "Daniel Sobkowicz"
    )

    assert daniel["board_rank"] == "85"
    assert daniel["evidence_status"] == "watchlist_data_incomplete"
    assert daniel["draft_board_band"] == "watchlist_or_data_incomplete_context_review"
    assert _score(daniel) == 25.2
    assert "missing_prospect_or_college_evidence" in daniel["warning_flags"]
    assert (
        "| 85 | Daniel Sobkowicz | WR | 25.2000 | 0.84 | "
        "missing_prospect_or_college_evidence |"
    ) in text
    assert "manual-scout prompt, not a confident draft option" in text


def test_rookie_watchlist_report_preserves_market_and_blocked_use_flags():
    watchlist_rows = _watchlist_rows()

    assert all(
        row["blocked_use"] == "do_not_use_as_final_rookie_draft_recommendation"
        for row in watchlist_rows
    )
    assert all(
        "market_context_excluded_from_private_value" in row["warning_flags"]
        for row in watchlist_rows
    )
    assert all(
        "review_only_no_final_rookie_pick_recommendation" in row["warning_flags"]
        for row in watchlist_rows
    )
