import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_dynasty_stability_retune_v1_20260702"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "dynasty_stability_retune_summary.md",
    "fixed_retune_variant_definitions.csv",
    "historical_validation_metric_comparison.csv",
    "historical_holdout_metric_comparison.csv",
    "position_level_retune_report.csv",
    "season_level_retune_report.csv",
    "topn_startable_retune_report.csv",
    "current_board_cornerstone_retune_report.csv",
    "key_player_before_after_matrix.csv",
    "cornerstone_casebook_after_retune.md",
    "market_context_not_source_truth_report.md",
    "selected_retune_decision.md",
    "usage_lens_vs_main_formula_update.md",
    "remaining_risk_report.md",
    "human_review_update.md",
    "tim_human_review_addendum.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}

EXPECTED_VARIANTS = {
    "current_guarded_candidate",
    "multi_year_production_anchor",
    "career_peak_or_ceiling_anchor",
    "young_wr_te_stability_guard",
    "cornerstone_stability_floor",
    "multi_year_plus_cornerstone_guard",
    "usage_lens_only_control",
}


def read_csv(name):
    with (ARTIFACT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_required_dynasty_stability_retune_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_retune_definitions_are_review_only_and_bounded():
    definitions = read_csv("fixed_retune_variant_definitions.csv")

    assert {row["variant_id"] for row in definitions} == EXPECTED_VARIANTS
    assert {row["review_only"] for row in definitions} == {"true"}
    assert {row["production_approved"] for row in definitions} == {"false"}
    assert {row["app_wiring_allowed"] for row in definitions} == {"false"}
    assert {row["market_source_truth_used"] for row in definitions} == {"false"}
    assert {row["player_name_exception_used"] for row in definitions} == {"false"}
    assert {row["holdout_used_for_selection"] for row in definitions} == {"false"}
    assert {row["broad_grid_search_used"] for row in definitions} == {"false"}


def test_selected_retune_decision_is_partial_hold_review_only():
    summary = (ARTIFACT_DIR / "dynasty_stability_retune_summary.md").read_text(encoding="utf-8")
    decision = (ARTIFACT_DIR / "selected_retune_decision.md").read_text(encoding="utf-8")
    addendum = (ARTIFACT_DIR / "tim_human_review_addendum.md").read_text(encoding="utf-8")
    notice = (ARTIFACT_DIR / "do_not_promote_notice.md").read_text(encoding="utf-8")

    assert "PARTIAL_DYNASTY_STABILITY_RETUNE_STILL_HOLD" in summary
    assert "multi_year_plus_cornerstone_guard" in summary
    assert "Decision label: `PARTIAL_DYNASTY_STABILITY_RETUNE_STILL_HOLD`" in decision
    assert "on HOLD" in decision
    assert "Production promotion is not approved" in decision
    assert "Main-formula readiness is not approved" in addendum
    assert "INJURY_TIMELINE_DISCOUNT_WATCHLIST" in addendum
    assert "EXPLAINABLE_WATCHLIST" in addendum
    assert "Do not recommend more broad tuning right now" in addendum
    assert "No formula candidate in this packet is production-ready or production-approved" in notice


def test_selected_retune_preserves_historical_shape_and_current_board_fences():
    validation = {row["candidate_id"]: row for row in read_csv("historical_validation_metric_comparison.csv")}
    holdout = {row["candidate_id"]: row for row in read_csv("historical_holdout_metric_comparison.csv")}
    current_board = {row["metric"]: row for row in read_csv("current_board_cornerstone_retune_report.csv")}
    key_players = {row["player_name"]: row for row in read_csv("key_player_before_after_matrix.csv")}

    selected = "multi_year_plus_cornerstone_guard"
    assert float(validation[selected]["mae_delta_vs_baseline"]) < 0
    assert float(holdout[selected]["mae_delta_vs_baseline"]) < 0
    assert float(validation[selected]["startable_precision_delta_vs_baseline"]) < 0
    assert float(holdout[selected]["startable_precision_delta_vs_baseline"]) >= 0
    assert current_board["null_fenced_rows"]["value"] == "125"
    assert key_players["Tony Pollard"]["after_retune_label"] == "SMART_CONTRARIAN_FADE"
    assert key_players["CeeDee Lamb"]["player_name_exception_used"] == "false"
