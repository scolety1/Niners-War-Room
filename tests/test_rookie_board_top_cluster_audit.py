import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md"
ROOKIE_ROWS = (
    ROOT
    / "local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv"
)


def _rows() -> list[dict[str, str]]:
    with ROOKIE_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _score(row: dict[str, str]) -> float:
    return float(row["league_format_adjusted_score"])


def test_rookie_top_cluster_report_discloses_source_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "rookie_draft_board_review_rows.csv" in text
    assert "league_format_adjusted_score" in text
    assert "prospect_private_value_review_score" in text
    assert "review_only_rookie_board_context_not_final_pick" in text
    assert "do_not_use_as_final_rookie_draft_recommendation" in text
    assert "does not change rookie weights" in text
    assert "Do not change rookie weights" in text


def test_rookie_top_cluster_report_matches_board_counts():
    text = REPORT.read_text(encoding="utf-8")
    rows = _rows()
    evidence_counts = Counter(row["evidence_status"] for row in rows)
    band_counts = Counter(row["draft_board_band"] for row in rows)
    top_20 = sorted(rows, key=_score, reverse=True)[:20]

    assert len(rows) == 210
    assert evidence_counts["draftable_review"] == 67
    assert evidence_counts["manual_scout_source_review"] == 122
    assert evidence_counts["watchlist_data_incomplete"] == 21
    assert band_counts["first_round_board_context_review"] == 10
    assert sum(_score(row) >= 50 for row in rows) == 10
    assert all(row["evidence_status"] == "draftable_review" for row in top_20)
    assert "Total rookie board rows: 210." in text
    assert "Rows with `league_format_adjusted_score` at least 50: 10." in text


def test_rookie_top_cluster_report_includes_named_rookie_anchors():
    text = REPORT.read_text(encoding="utf-8")

    for prospect in [
        "Jeremiyah Love",
        "Makai Lemon",
        "Skyler Bell",
        "Jordyn Tyson",
        "Carnell Tate",
        "Antonio Williams",
        "Daniel Sobkowicz",
    ]:
        assert prospect in text

    assert "| A69 | Jeremiyah Love | 1 | RB | 75.3111 | draftable_review |" in text
    assert "| A75 | Daniel Sobkowicz | 85 | WR | 25.2000 | watchlist_data_incomplete |" in text
    assert "reserved for low-evidence/watchlist audit" in text


def test_rookie_top_cluster_report_preserves_market_and_recommendation_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "market_context_excluded_from_private_value" in text
    assert "20 of 20" in text
    assert "market, ADP, rankings, projections, consensus, startup" in text
    assert "final rookie pick" not in text.lower()
    assert "recommendation" in text
