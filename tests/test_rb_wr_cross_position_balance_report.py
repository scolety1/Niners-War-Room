import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)


def _rows() -> list[dict[str, str]]:
    with CURRENT_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _score(row: dict[str, str]) -> float | None:
    value = row.get("checkpoint_review_score") or ""
    return float(value) if value else None


def _position_rows(position: str) -> list[dict[str, str]]:
    return [row for row in _rows() if row["position"] == position]


def test_rb_wr_balance_report_discloses_source_and_non_tuning_scope():
    text = REPORT.read_text(encoding="utf-8")

    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "review_v4_current_player" in text
    assert "review_only_current_value_checkpoint" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "does not tune RB/WR balance" in text
    assert "Do not tune RB/WR formulas" in text


def test_rb_wr_balance_report_matches_position_counts_and_bands():
    text = REPORT.read_text(encoding="utf-8")
    rb_rows = _position_rows("RB")
    wr_rows = _position_rows("WR")

    assert len(rb_rows) == 19
    assert len(wr_rows) == 41
    assert sum(_score(row) is not None for row in rb_rows) == 18
    assert sum(_score(row) is not None for row in wr_rows) == 39
    assert "| RB | 19 | 18 | 1 | 82.8329 | 3.0698 | 53.6926 | 59.6777 | 4 | 11 |" in text
    assert "| WR | 41 | 39 | 2 | 83.0486 | 16.2148 | 41.3714 | 32.3993 | 4 | 9 |" in text
    assert "| RB | 2 | 7 | 5 | 2 | 2 | 1 |" in text
    assert "| WR | 2 | 3 | 11 | 22 | 1 | 2 |" in text


def test_rb_wr_balance_report_includes_named_review_prompts():
    text = REPORT.read_text(encoding="utf-8")

    for player in [
        "Christian McCaffrey",
        "Derrick Henry",
        "Bijan Robinson",
        "Jahmyr Gibbs",
        "CeeDee Lamb",
        "Justin Jefferson",
        "Garrett Wilson",
        "Malik Nabers",
        "Kaleb Johnson",
    ]:
        assert player in text

    assert "balance prompts only" in text
    assert "They do not prove the RB/WR" in text
    assert "relationship is correct or incorrect" in text


def test_rb_wr_balance_report_excludes_legacy_and_market_values():
    text = REPORT.read_text(encoding="utf-8")

    assert "legacy_active_pack" not in text
    assert "private_score" not in text
    assert "82.4" not in text
    assert "78.88" not in text
    assert "market, ADP, rankings, projections, consensus, startup" in text
