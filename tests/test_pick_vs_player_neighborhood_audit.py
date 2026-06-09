import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md"
DECISIONS = (
    ROOT / "local_exports/model_v4/rookie_pick_decision_lab/latest/"
    "pick_decision_rows.csv"
)
COMPARE = (
    ROOT / "local_exports/model_v4/rookie_pick_decision_lab/latest/"
    "pick_decision_compare_rows.csv"
)
TARGET_PICKS = ("2026 1.03", "2026 1.04", "2026 2.04", "2026 2.08", "2026 5.04")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _decision_rows() -> dict[str, dict[str, str]]:
    return {row["pick_label"]: row for row in _rows(DECISIONS)}


def _compare_by_pick() -> dict[str, list[dict[str, str]]]:
    by_pick: dict[str, list[dict[str, str]]] = {}
    for row in _rows(COMPARE):
        by_pick.setdefault(row["pick_label"], []).append(row)
    return by_pick


def test_pick_vs_player_report_discloses_sources_and_non_goals():
    text = REPORT.read_text(encoding="utf-8")

    assert "pick_decision_rows.csv" in text
    assert "pick_decision_compare_rows.csv" in text
    assert "current_player_value_review_rows.csv" in text
    assert "rookie_draft_board_review_rows.csv" in text
    assert "asset_score" in text
    assert "score_gap_to_pick" in text
    assert "Do not change startup-slot conversion" in text
    assert "Do not change pick baselines" in text
    assert "does not change startup-slot conversion" in text


def test_pick_vs_player_report_matches_neighborhood_counts():
    text = REPORT.read_text(encoding="utf-8")
    by_pick = _compare_by_pick()

    assert set(by_pick) == set(TARGET_PICKS)
    assert sum(len(rows) for rows in by_pick.values()) == 72
    for pick in TARGET_PICKS[:4]:
        counts = Counter(row["comparison_type"] for row in by_pick[pick])
        assert len(by_pick[pick]) == 16
        assert counts["rookie_candidate"] == 8
        assert counts["startup_slot_asset"] == 8
        assert f"| {pick} |" in text

    counts_504 = Counter(row["comparison_type"] for row in by_pick["2026 5.04"])
    assert len(by_pick["2026 5.04"]) == 8
    assert counts_504["rookie_candidate"] == 8
    assert counts_504["startup_slot_asset"] == 0
    assert "| 2026 5.04 | blank | 8 | 8 | 0 |" in text


def test_pick_vs_player_report_matches_guardrails_and_elite_risk_flags():
    text = REPORT.read_text(encoding="utf-8")
    decisions = _decision_rows()
    compare_rows = _rows(COMPARE)

    assert all(
        row["allowed_use"] == "review_only_rookie_pick_decision_lab_not_final_selection"
        for row in compare_rows
    )
    assert all(
        row["blocked_use"]
        == "do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation"
        for row in compare_rows
    )
    elite_rows = [
        row
        for row in compare_rows
        if "elite_current_asset_not_single_pick_trade_equivalent"
        in row["evidence_or_risk_note"]
    ]
    assert len(elite_rows) == 14
    assert decisions["2026 1.03"]["equivalence_guardrail"] == (
        "internal_model_neighbor_only_not_one_for_one_trade_equivalent"
    )
    assert decisions["2026 1.04"]["equivalence_guardrail"] == (
        "internal_model_neighbor_only_not_one_for_one_trade_equivalent"
    )
    assert decisions["2026 2.08"]["equivalence_guardrail"] == (
        "nearby_model_value_not_trade_equivalence"
    )
    assert "Rows carrying `elite_current_asset_not_single_pick_trade_equivalent`: 14." in text


def test_pick_vs_player_report_matches_closest_neighbors():
    text = REPORT.read_text(encoding="utf-8")
    by_pick = _compare_by_pick()

    closest_expected = {
        "2026 1.03": ("Trey McBride", "-6.1224"),
        "2026 1.04": ("Trey McBride", "-2.9224"),
        "2026 2.04": ("Makai Lemon", "-2.1842"),
        "2026 2.08": ("Josh Jacobs", "-0.0613"),
    }
    for pick, (asset, gap) in closest_expected.items():
        with_gap = [row for row in by_pick[pick] if row["score_gap_to_pick"]]
        closest = min(with_gap, key=lambda row: abs(float(row["score_gap_to_pick"])))
        assert closest["asset_name"] == asset
        assert closest["score_gap_to_pick"] == gap
        assert asset in text
        assert gap in text

    pick_504_rows = by_pick["2026 5.04"]
    assert all(row["score_gap_to_pick"] == "" for row in pick_504_rows)
    assert all(
        row["asset_context"] == "late_watchlist_no_pick_baseline_review"
        for row in pick_504_rows
    )
    assert "Eli Raridon" in text
    assert "no_exact_equivalence_without_pick_baseline" in text


def test_pick_vs_player_report_records_compare_source_disclosure_gap():
    text = REPORT.read_text(encoding="utf-8")
    compare_header = set(_rows(COMPARE)[0])

    assert not {"source_path", "source_column", "lineage_class"} <= compare_header
    assert "does **not** include explicit" in text
    assert "source-disclosure gap to carry forward" in text
