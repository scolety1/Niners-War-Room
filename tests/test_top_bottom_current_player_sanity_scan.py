import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)


def _rows() -> list[dict[str, str]]:
    with CURRENT_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _score(row: dict[str, str]) -> float | None:
    value = row.get("checkpoint_review_score") or ""
    if not value:
        return None
    return float(value)


def _ordered_rows() -> list[dict[str, str]]:
    return sorted(
        _rows(),
        key=lambda row: -999999 if _score(row) is None else _score(row),
        reverse=True,
    )


def test_top_bottom_scan_discloses_source_and_review_only_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "review_v4_current_player" in text
    assert "review_only_current_value_checkpoint" in text
    assert "do_not_use_as_final_ranking_or_roster_recommendation" in text
    assert "Suspicious does not mean wrong" not in text
    assert "do not mean wrong" in text
    assert "Do not tune formulas" in text


def test_top_bottom_scan_matches_sorted_extremes_and_counts():
    text = REPORT.read_text(encoding="utf-8")
    rows = _ordered_rows()

    assert len(_rows()) == 80
    assert sum(_score(row) is not None for row in rows) == 75
    assert sum(_score(row) is None for row in rows) == 5
    assert "Total current-player checkpoint rows: 80." in text
    assert "Rows with numeric primary score: 75." in text
    assert "Rows with blank primary score: 5." in text

    top = rows[0]
    bottom = rows[-1]
    assert top["player_name"] == "Trey McBride"
    assert f"| 1 | 61 | {top['player_name']} | TE |" in text
    assert bottom["player_name"] == "Kenyon Sadiq"
    assert "| 80 | 80 | Kenyon Sadiq | TE | NYJ | blank |" in text


def test_top_bottom_scan_includes_required_human_review_prompts():
    text = REPORT.read_text(encoding="utf-8")

    for player in [
        "Trey McBride",
        "Josh Allen",
        "Joe Burrow",
        "Jayden Daniels",
        "Keenan Allen",
        "Kaleb Johnson",
        "Jeremiyah Love",
    ]:
        assert player in text

    assert "te_near_top_overall_review" in text
    assert "one_qb_near_top_overall_review" in text
    assert "format_cap_review" in text
    assert "missing_primary_score_manual_review" in text
    assert "low_score_boundary_review" in text


def test_top_bottom_scan_does_not_use_legacy_sentinel_scores():
    text = REPORT.read_text(encoding="utf-8")

    assert "41.6097" in text
    assert "legacy active-pack `private_score`" in text
    assert "82.4" not in text
    assert "78.88" not in text
