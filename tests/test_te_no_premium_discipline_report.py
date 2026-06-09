import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md"
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


def test_te_no_premium_report_discloses_sources_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "review_v4_current_player" in text
    assert "niners_pick_inventory_review_rows.csv" in text
    assert "pick_value_review_score" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "do_not_use_as_pick_trade_recommendation_or_offer" in text
    assert "does not change TE\ndiscipline" in text
    assert "does not make trade, cut, keep, draft" in text


def test_te_no_premium_report_matches_te_counts_and_key_scores():
    text = REPORT.read_text(encoding="utf-8")
    tes = [row for row in _rows(CURRENT_ROWS) if row["position"] == "TE"]
    scored_tes = [row for row in tes if _score(row, "checkpoint_review_score") is not None]

    assert len(tes) == 11
    assert len(scored_tes) == 10
    assert "TE rows in current-player checkpoint: 11." in text
    assert "TE rows with numeric current score: 10." in text
    assert "TE rows with blank current score: 1." in text
    assert "TE rows with `no_premium_te` warning text: 7." in text

    by_name = {row["player_name"]: row for row in tes}
    assert float(by_name["Trey McBride"]["checkpoint_review_score"]) == 87.4776
    assert float(by_name["T.J. Hockenson"]["checkpoint_review_score"]) == 13.7788
    assert by_name["Kenyon Sadiq"]["checkpoint_review_score"] == ""
    assert "| 1 | 61 | Trey McBride | ARI | 87.4776 |" in text
    assert "| 71 | 76 | T.J. Hockenson | MIN | 13.7788 |" in text
    assert "| 80 | Kenyon Sadiq | NYJ | blank |" in text


def test_te_no_premium_report_includes_pick_context_without_trade_equivalence():
    text = REPORT.read_text(encoding="utf-8")
    picks = {row["pick_label"]: row for row in _rows(PICK_ROWS)}

    assert float(picks["2026 1.04"]["pick_value_review_score"]) == 90.4
    assert float(picks["2026 2.08"]["pick_value_review_score"]) == 58.6
    assert picks["2026 5.04"]["pick_value_review_score"] == ""
    assert "2026 1.04 at 90.4" in text
    assert "2026 2.08 at 58.6" in text
    assert "2026 5.04 pick has no exact model baseline" in text
    assert "context only" in text
    assert "trade-equivalence recommendations" in text


def test_te_no_premium_report_does_not_use_legacy_or_market_values():
    text = REPORT.read_text(encoding="utf-8")

    assert "legacy_active_pack" not in text
    assert "private_score" not in text
    assert "82.4" not in text
    assert "78.88" not in text
    assert "market, ADP, rankings, projections, consensus, startup" in text
