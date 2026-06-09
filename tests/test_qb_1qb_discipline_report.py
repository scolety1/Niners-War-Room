import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/QB_1QB_DISCIPLINE_REPORT_20260605.md"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
PICK_ROWS = (
    ROOT
    / "local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv"
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _score(row: dict[str, str], column: str) -> float | None:
    value = row.get(column) or ""
    return float(value) if value else None


def test_qb_1qb_report_discloses_sources_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "review_v4_current_player" in text
    assert "niners_pick_inventory_review_rows.csv" in text
    assert "pick_value_review_score" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "do_not_use_as_pick_trade_recommendation_or_offer" in text
    assert "does not\nchange QB caps" in text
    assert "does not make trade, cut, keep, draft" in text


def test_qb_1qb_report_matches_qb_counts_and_key_scores():
    text = REPORT.read_text(encoding="utf-8")
    qbs = [row for row in _rows(CURRENT_ROWS) if row["position"] == "QB"]
    scored_qbs = [row for row in qbs if _score(row, "checkpoint_review_score") is not None]

    assert len(qbs) == 9
    assert len(scored_qbs) == 8
    assert "QB rows in current-player checkpoint: 9." in text
    assert "QB rows with numeric current score: 8." in text
    assert "QB rows with blank current score: 1." in text

    by_name = {row["player_name"]: row for row in qbs}
    assert float(by_name["Josh Allen"]["checkpoint_review_score"]) == 80.3133
    assert float(by_name["Jayden Daniels"]["checkpoint_review_score"]) == 8.9902
    assert by_name["Fernando Mendoza"]["checkpoint_review_score"] == ""
    assert "| 5 | 62 | Josh Allen | BUF | 80.3133 |" in text
    assert "| 74 | 78 | Jayden Daniels | WAS | 8.9902 |" in text
    assert "| 79 | Fernando Mendoza | LVR | blank |" in text


def test_qb_1qb_report_includes_pick_context_without_trade_equivalence():
    text = REPORT.read_text(encoding="utf-8")
    picks = {row["pick_label"]: row for row in _rows(PICK_ROWS)}

    assert float(picks["2026 2.08"]["pick_value_review_score"]) == 58.6
    assert picks["2026 5.04"]["pick_value_review_score"] == ""
    assert "2026 2.08 at 58.6" in text
    assert "2026 5.04 pick has no exact model baseline" in text
    assert "context only" in text
    assert "not used as a scored comparison row" in text
    assert "trade-equivalence recommendations" in text


def test_qb_1qb_report_does_not_use_legacy_or_market_values():
    text = REPORT.read_text(encoding="utf-8")

    assert "legacy active-pack value" in text
    assert "8.9902" in text
    assert "95.7" not in text
    assert "82.4" not in text
    assert "78.88" not in text
    assert "market, ADP, rankings, projections, consensus, startup" in text
