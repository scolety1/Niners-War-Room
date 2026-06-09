import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/PICK_VALUE_LADDER_AUDIT_20260605.md"
BASELINES = ROOT / "local_exports/model_v4/pick_values/latest/pick_value_baselines_review.csv"
INVENTORY = (
    ROOT / "local_exports/model_v4/pick_trade_defer/latest/"
    "niners_pick_inventory_review_rows.csv"
)
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


def _by_pick(path: Path) -> dict[str, dict[str, str]]:
    return {row["pick_label"]: row for row in _rows(path)}


def test_pick_value_ladder_report_discloses_sources_and_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "pick_value_baselines_review.csv" in text
    assert "niners_pick_inventory_review_rows.csv" in text
    assert "pick_decision_rows.csv" in text
    assert "pick_decision_compare_rows.csv" in text
    assert "pick_value_review_score" in text
    assert "pick_value_score" in text
    assert "review_only_pick_value_baseline_not_trade_recommendation" in text
    assert "review_only_pick_inventory_not_trade_recommendation" in text
    assert "review_only_rookie_pick_decision_lab_not_final_selection" in text
    assert "Do not change pick baselines" in text


def test_pick_value_ladder_report_matches_owned_pick_rows():
    text = REPORT.read_text(encoding="utf-8")
    baselines = _by_pick(BASELINES)
    inventory = _by_pick(INVENTORY)
    decisions = _by_pick(DECISIONS)
    expected_scores = {
        "2026 1.03": "93.6",
        "2026 1.04": "90.4",
        "2026 2.04": "71.4",
        "2026 2.08": "58.6",
    }

    assert set(inventory) == set(TARGET_PICKS)
    assert set(decisions) == set(TARGET_PICKS)
    for pick, expected_score in expected_scores.items():
        assert baselines[pick]["pick_value_review_score"] == expected_score
        assert inventory[pick]["pick_value_review_score"] == expected_score
        assert decisions[pick]["pick_value_score"] == expected_score
        assert inventory[pick]["baseline_match_status"] == "matched_pick_value_baseline"
        assert f"| {pick} | {expected_score} | {expected_score} |" in text

    pick_504 = inventory["2026 5.04"]
    decision_504 = decisions["2026 5.04"]
    assert "2026 5.04" not in baselines
    assert pick_504["pick_value_review_score"] == ""
    assert pick_504["baseline_match_status"] == "missing_pick_value_baseline"
    assert pick_504["tier_label"] == "manual_only_no_exact_model_baseline"
    assert decision_504["pick_value_score"] == ""
    assert decision_504["confidence_status"] == "manual_only_no_exact_model_baseline"
    assert decision_504["equivalence_guardrail"] == "no_exact_equivalence_without_pick_baseline"
    assert (
        "| 2026 5.04 | missing | blank | missing_pick_value_baseline | "
        "manual_only_no_exact_model_baseline | blank |"
    ) in text


def test_pick_value_ladder_report_matches_nearby_ladder_rows():
    text = REPORT.read_text(encoding="utf-8")
    baselines = _by_pick(BASELINES)
    expected = {
        "2026 1.01": 100.0,
        "2026 1.02": 96.8,
        "2026 1.03": 93.6,
        "2026 1.04": 90.4,
        "2026 1.05": 87.2,
        "2026 2.03": 74.6,
        "2026 2.04": 71.4,
        "2026 2.05": 68.2,
        "2026 2.07": 61.8,
        "2026 2.08": 58.6,
        "2026 2.09": 55.4,
    }

    assert [expected[pick] for pick in expected] == sorted(expected.values(), reverse=True)
    for pick, score in expected.items():
        assert float(baselines[pick]["pick_value_review_score"]) == score
        assert baselines[pick]["allowed_use"] == (
            "review_only_pick_value_baseline_not_trade_recommendation"
        )
        assert baselines[pick]["confidence_status"] == (
            "review_only_pick_baseline_no_market_input"
        )
        assert f"| {pick} | {score:.1f} |" in text

    for pick in ("2026 5.03", "2026 5.04", "2026 5.05"):
        assert pick not in baselines
        assert (
            f"| {pick} | missing | manual_only_no_exact_model_baseline | "
            "no admitted baseline row |"
        ) in text


def test_pick_value_ladder_report_matches_compare_row_counts():
    text = REPORT.read_text(encoding="utf-8")
    compare_rows = _rows(COMPARE)
    by_pick: dict[str, list[dict[str, str]]] = {}
    for row in compare_rows:
        by_pick.setdefault(row["pick_label"], []).append(row)

    for pick in TARGET_PICKS[:4]:
        counts = Counter(row["comparison_type"] for row in by_pick[pick])
        assert len(by_pick[pick]) == 16
        assert counts["rookie_candidate"] == 8
        assert counts["startup_slot_asset"] == 8
        assert sum(not row["score_gap_to_pick"] for row in by_pick[pick]) == 0
        assert f"| {pick} | 16 | 8 | 8 | 0 |" in text

    counts_504 = Counter(row["comparison_type"] for row in by_pick["2026 5.04"])
    assert len(by_pick["2026 5.04"]) == 8
    assert counts_504["rookie_candidate"] == 8
    assert counts_504["startup_slot_asset"] == 0
    assert sum(not row["score_gap_to_pick"] for row in by_pick["2026 5.04"]) == 8
    assert "| 2026 5.04 | 8 | 8 | 0 | 8 |" in text
    assert "blank `score_gap_to_pick`" in text


def test_pick_value_ladder_report_preserves_blocked_use_and_manual_only_flags():
    inventory = _by_pick(INVENTORY)
    decisions = _by_pick(DECISIONS)

    assert all(
        row["blocked_use"] == "do_not_use_as_pick_trade_recommendation_or_offer"
        for row in inventory.values()
    )
    assert all(
        row["blocked_use"]
        == "do_not_use_as_final_pick_trade_cut_keep_or_draft_recommendation"
        for row in decisions.values()
    )
    assert "pick_value_baseline_missing" in inventory["2026 5.04"]["warning_flags"]
    assert "manual_only_no_exact_model_baseline" in inventory["2026 5.04"][
        "warning_flags"
    ]
    assert "no_exact_equivalence_without_pick_baseline" in decisions["2026 5.04"][
        "warning_flags"
    ]
