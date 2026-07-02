from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_cutline_safe_refinement_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "cutline_safe_refinement_summary.md",
    "fixed_refinement_variant_definitions.csv",
    "validation_metric_comparison.csv",
    "holdout_metric_comparison.csv",
    "cutline_miss_comparison.csv",
    "elite_qb_regression_comparison.csv",
    "position_level_refinement_report.csv",
    "season_level_refinement_report.csv",
    "topn_startable_refinement_report.csv",
    "refinement_selection_decision.md",
    "selected_refinement_review_packet.md",
    "remaining_cutline_casebook.csv",
    "largest_remaining_regressions.csv",
    "human_review_update.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}

EXPECTED_VARIANTS = {
    "baseline_v3_prior_points",
    "original_usage_opportunity_volume",
    "qb_guard_soft_blend",
    "conservative_blend_50",
    "qb_guard_plus_cutline_blend_50",
    "qb_guard_plus_cutline_blend_65",
    "qb_guard_plus_cutline_floor",
    "rb_wr_cutline_safe_blend",
    "startable_band_blend",
}


def test_required_cutline_refinement_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_fixed_refinement_definitions_are_review_only_and_bounded():
    definitions = pd.read_csv(ARTIFACT_DIR / "fixed_refinement_variant_definitions.csv")

    assert EXPECTED_VARIANTS == set(definitions["candidate_id"])
    assert definitions["holdout_used_to_define_thresholds"].eq(False).all()
    assert definitions["holdout_used_for_selection"].eq(False).all()
    assert definitions["target_outcomes_used_in_guard"].eq(False).all()
    assert definitions["review_only"].eq(True).all()
    assert definitions["approved_for_production_use"].eq(False).all()
    assert definitions["shadow_review_approved"].eq(False).all()


def test_decision_is_partial_refinement_still_hold():
    summary = (ARTIFACT_DIR / "cutline_safe_refinement_summary.md").read_text(
        encoding="utf-8"
    )
    decision = (ARTIFACT_DIR / "refinement_selection_decision.md").read_text(
        encoding="utf-8"
    )

    assert "PARTIAL_REFINEMENT_STILL_HOLD" in summary
    assert "rb_wr_cutline_safe_blend" in summary
    assert "Result: `PARTIAL_REFINEMENT_STILL_HOLD`" in decision
    assert "No shadow-review approval" in (
        ARTIFACT_DIR / "selected_refinement_review_packet.md"
    ).read_text(encoding="utf-8")


def test_selected_partial_reduces_cutline_misses_and_keeps_elite_qb_low():
    cutline = pd.read_csv(ARTIFACT_DIR / "cutline_miss_comparison.csv")
    elite = pd.read_csv(ARTIFACT_DIR / "elite_qb_regression_comparison.csv")
    review_cutline = cutline[cutline["split"].eq("validation_holdout")].set_index(
        "candidate_id"
    )
    review_elite = elite[elite["split"].eq("validation_holdout")].set_index("candidate_id")

    assert review_cutline.loc["original_usage_opportunity_volume", "actual_hits_moved_below_cutline"] == 8
    assert review_cutline.loc["qb_guard_soft_blend", "actual_hits_moved_below_cutline"] == 8
    assert review_cutline.loc["rb_wr_cutline_safe_blend", "actual_hits_moved_below_cutline"] == 5
    assert review_elite.loc["original_usage_opportunity_volume", "severe_regression_count"] == 14
    assert review_elite.loc["qb_guard_soft_blend", "severe_regression_count"] == 1
    assert review_elite.loc["rb_wr_cutline_safe_blend", "severe_regression_count"] == 1


def test_selected_partial_preserves_mae_but_not_full_success_criteria():
    validation = pd.read_csv(ARTIFACT_DIR / "validation_metric_comparison.csv").set_index(
        "candidate_id"
    )
    holdout = pd.read_csv(ARTIFACT_DIR / "holdout_metric_comparison.csv").set_index(
        "candidate_id"
    )

    assert validation.loc["rb_wr_cutline_safe_blend", "mae_delta_vs_baseline"] < 0
    assert holdout.loc["rb_wr_cutline_safe_blend", "mae_delta_vs_baseline"] < 0
    assert holdout.loc["rb_wr_cutline_safe_blend", "spearman_delta_vs_baseline"] >= 0
    assert validation.loc["rb_wr_cutline_safe_blend", "startable_precision_delta_vs_baseline"] < 0
    assert holdout.loc["rb_wr_cutline_safe_blend", "startable_precision_delta_vs_baseline"] < 0


def test_remaining_casebooks_are_present_for_human_review():
    remaining = pd.read_csv(ARTIFACT_DIR / "remaining_cutline_casebook.csv")
    regressions = pd.read_csv(ARTIFACT_DIR / "largest_remaining_regressions.csv")

    assert len(remaining) == 5
    assert len(regressions) == 40
    assert {"player_name", "position", "target_season", "cutline"}.issubset(remaining.columns)
    assert "selected_error_delta_vs_baseline" in regressions.columns


def test_guardrail_report_blocks_promotion_and_forbidden_sources():
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    notice = (ARTIFACT_DIR / "do_not_promote_notice.md").read_text(encoding="utf-8")

    for phrase in [
        "No production formula changes",
        "No formula promotion",
        "No shadow review approval",
        "No app wiring",
        "No source-truth promotion",
        "Holdout is not used to define thresholds or select variants",
        "No routes, TPRR, YPRR, route proxies, ambiguous `rz_att`",
        "Missing values are not forced to zero",
        "No candidate/refinement output is approved for production use",
    ]:
        assert phrase in guardrail
    assert "Do not promote" in notice
