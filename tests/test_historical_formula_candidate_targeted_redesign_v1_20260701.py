from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_targeted_redesign_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "targeted_redesign_summary.md",
    "fixed_redesign_variant_definitions.csv",
    "validation_metric_comparison.csv",
    "holdout_metric_comparison.csv",
    "cutline_miss_comparison.csv",
    "remaining_5_case_resolution_report.csv",
    "elite_qb_regression_comparison.csv",
    "position_level_redesign_report.csv",
    "season_level_redesign_report.csv",
    "topn_startable_redesign_report.csv",
    "targeted_redesign_selection_decision.md",
    "selected_redesign_review_packet.md",
    "remaining_concern_casebook.csv",
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
    "rb_wr_cutline_safe_blend",
    "conservative_blend_50",
    "current_best_rb_wr_cutline_safe_blend",
    "premium_cutline_floor_v1",
    "premium_cutline_floor_v2_tighter",
    "high_prior_volume_boundary_guard",
    "wr_boundary_breakout_sensitivity_guard",
    "hybrid_qb_plus_premium_cutline_guard",
    "conservative_human_review_variant",
}


def test_required_targeted_redesign_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_fixed_redesign_definitions_are_review_only_and_bounded():
    definitions = pd.read_csv(ARTIFACT_DIR / "fixed_redesign_variant_definitions.csv")

    assert EXPECTED_VARIANTS == set(definitions["candidate_id"])
    assert definitions["holdout_used_to_define_thresholds"].eq(False).all()
    assert definitions["holdout_used_for_selection"].eq(False).all()
    assert definitions["target_outcomes_used_in_guard"].eq(False).all()
    assert definitions["player_specific_exception_used"].eq(False).all()
    assert definitions["review_only"].eq(True).all()
    assert definitions["approved_for_production_use"].eq(False).all()
    assert definitions["shadow_review_approved"].eq(False).all()


def test_decision_is_targeted_redesign_for_human_review_only():
    summary = (ARTIFACT_DIR / "targeted_redesign_summary.md").read_text(
        encoding="utf-8"
    )
    decision = (ARTIFACT_DIR / "targeted_redesign_selection_decision.md").read_text(
        encoding="utf-8"
    )
    packet = (ARTIFACT_DIR / "selected_redesign_review_packet.md").read_text(
        encoding="utf-8"
    )

    assert "TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY" in summary
    assert "wr_boundary_breakout_sensitivity_guard" in summary
    assert "Decision label: `TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY`" in decision
    assert "No shadow-review approval is granted" in packet


def test_selected_redesign_reduces_cutline_misses_and_keeps_elite_qb_low():
    cutline = pd.read_csv(ARTIFACT_DIR / "cutline_miss_comparison.csv")
    elite = pd.read_csv(ARTIFACT_DIR / "elite_qb_regression_comparison.csv")
    review_cutline = cutline[cutline["split"].eq("validation_holdout")].set_index(
        "candidate_id"
    )
    review_elite = elite[elite["split"].eq("validation_holdout")].set_index("candidate_id")

    assert review_cutline.loc["original_usage_opportunity_volume", "actual_hits_moved_below_cutline"] == 8
    assert review_cutline.loc["qb_guard_soft_blend", "actual_hits_moved_below_cutline"] == 8
    assert review_cutline.loc["rb_wr_cutline_safe_blend", "actual_hits_moved_below_cutline"] == 5
    assert review_cutline.loc["wr_boundary_breakout_sensitivity_guard", "actual_hits_moved_below_cutline"] == 2
    assert review_elite.loc["original_usage_opportunity_volume", "severe_regression_count"] == 14
    assert review_elite.loc["qb_guard_soft_blend", "severe_regression_count"] == 1
    assert review_elite.loc["wr_boundary_breakout_sensitivity_guard", "severe_regression_count"] == 1


def test_selected_redesign_preserves_required_metric_shape():
    validation = pd.read_csv(ARTIFACT_DIR / "validation_metric_comparison.csv").set_index(
        "candidate_id"
    )
    holdout = pd.read_csv(ARTIFACT_DIR / "holdout_metric_comparison.csv").set_index(
        "candidate_id"
    )
    candidate_id = "wr_boundary_breakout_sensitivity_guard"

    assert validation.loc[candidate_id, "mae_delta_vs_baseline"] < -1.0
    assert holdout.loc[candidate_id, "mae_delta_vs_baseline"] < -1.0
    assert holdout.loc[candidate_id, "spearman_delta_vs_baseline"] >= 0
    assert validation.loc[candidate_id, "startable_precision_delta_vs_baseline"] == 0
    assert holdout.loc[candidate_id, "startable_precision_delta_vs_baseline"] == 0


def test_remaining_five_resolution_report_is_general_and_not_player_specific():
    resolution = pd.read_csv(ARTIFACT_DIR / "remaining_5_case_resolution_report.csv")
    remaining = pd.read_csv(ARTIFACT_DIR / "remaining_concern_casebook.csv")

    assert len(resolution) == 5
    assert resolution["resolved_by_selected_redesign"].sum() == 3
    assert set(remaining["player_name"]) == {"T.Pollard", "C.Lamb"}
    assert resolution["guard_uses_target_outcomes"].eq(False).all()
    assert resolution["player_specific_exception_used"].eq(False).all()


def test_guardrail_report_blocks_promotion_and_forbidden_sources():
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    notice = (ARTIFACT_DIR / "do_not_promote_notice.md").read_text(encoding="utf-8")

    for phrase in [
        "No production formula changes",
        "No formula promotion",
        "No shadow review approval",
        "No app wiring",
        "No source-truth promotion",
        "No player-specific exceptions are used",
        "Holdout is not used to define thresholds or select variants",
        "No routes, TPRR, YPRR, route proxies, ambiguous `rz_att`",
        "Missing values are not forced to zero",
        "No redesign output is approved for production use",
    ]:
        assert phrase in guardrail
    assert "Do not promote" in notice
