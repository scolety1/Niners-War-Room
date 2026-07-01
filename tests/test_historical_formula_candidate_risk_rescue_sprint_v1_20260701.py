from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_risk_rescue_sprint_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "candidate_risk_rescue_summary.md",
    "fixed_rescue_variant_definitions.csv",
    "validation_metric_comparison.csv",
    "holdout_metric_comparison.csv",
    "elite_qb_regression_comparison.csv",
    "cutline_regression_comparison.csv",
    "position_level_rescue_report.csv",
    "season_level_rescue_report.csv",
    "topn_startable_rescue_report.csv",
    "rescue_variant_selection_decision.md",
    "human_review_update.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}

RESCUE_VARIANTS = {
    "original_usage_opportunity_volume",
    "conservative_blend_50",
    "qb_guard_baseline_lock",
    "qb_guard_soft_blend",
    "cutline_guard_soft_blend",
    "position_specific_safe_blend",
}


def test_required_risk_rescue_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_fixed_variant_definitions_are_bounded_and_review_only():
    definitions = pd.read_csv(ARTIFACT_DIR / "fixed_rescue_variant_definitions.csv")

    assert RESCUE_VARIANTS.issubset(set(definitions["candidate_id"]))
    assert definitions["holdout_used_to_define_thresholds"].eq(False).all()
    assert definitions["target_outcomes_used_in_guard"].eq(False).all()
    assert definitions["review_only"].eq(True).all()
    assert definitions["approved_for_production_use"].eq(False).all()


def test_rescue_decision_stays_hold_with_best_partial_qb_guard():
    summary = (ARTIFACT_DIR / "candidate_risk_rescue_summary.md").read_text(encoding="utf-8")
    decision = (ARTIFACT_DIR / "rescue_variant_selection_decision.md").read_text(
        encoding="utf-8"
    )

    assert "NO_SAFE_RESCUE_HOLD" in summary
    assert "qb_guard_soft_blend" in summary
    assert "Best partial rescue: `qb_guard_soft_blend`" in decision
    assert "Keep the candidate held for human review" in decision


def test_best_partial_rescue_preserves_mae_and_reduces_elite_qb_risk():
    validation = pd.read_csv(ARTIFACT_DIR / "validation_metric_comparison.csv").set_index(
        "candidate_id"
    )
    holdout = pd.read_csv(ARTIFACT_DIR / "holdout_metric_comparison.csv").set_index(
        "candidate_id"
    )
    elite = pd.read_csv(ARTIFACT_DIR / "elite_qb_regression_comparison.csv")
    review_elite = elite[elite["split"].eq("validation_holdout")].set_index("candidate_id")

    assert validation.loc["qb_guard_soft_blend", "mae_delta_vs_baseline"] < 0
    assert holdout.loc["qb_guard_soft_blend", "mae_delta_vs_baseline"] < 0
    assert validation.loc["qb_guard_soft_blend", "startable_precision_delta_vs_baseline"] == 0
    assert holdout.loc["qb_guard_soft_blend", "startable_precision_delta_vs_baseline"] == 0
    assert (
        review_elite.loc["qb_guard_soft_blend", "severe_regression_count"]
        < review_elite.loc["original_usage_opportunity_volume", "severe_regression_count"]
    )


def test_no_rescue_solves_both_elite_qb_and_cutline_risk():
    elite = pd.read_csv(ARTIFACT_DIR / "elite_qb_regression_comparison.csv")
    cutline = pd.read_csv(ARTIFACT_DIR / "cutline_regression_comparison.csv")
    review_elite = elite[elite["split"].eq("validation_holdout")].set_index("candidate_id")
    review_cutline = cutline[cutline["split"].eq("validation_holdout")].set_index("candidate_id")

    original_elite = review_elite.loc[
        "original_usage_opportunity_volume", "severe_regression_count"
    ]
    original_cutline = review_cutline.loc[
        "original_usage_opportunity_volume", "actual_hits_moved_below_cutline"
    ]

    full_safe = []
    for candidate_id in RESCUE_VARIANTS - {"original_usage_opportunity_volume"}:
        elite_improved = review_elite.loc[candidate_id, "severe_regression_count"] < original_elite
        cutline_improved = (
            review_cutline.loc[candidate_id, "actual_hits_moved_below_cutline"]
            < original_cutline
        )
        if elite_improved and cutline_improved:
            full_safe.append(candidate_id)

    assert full_safe == ["conservative_blend_50"]

    validation = pd.read_csv(ARTIFACT_DIR / "validation_metric_comparison.csv").set_index(
        "candidate_id"
    )
    holdout = pd.read_csv(ARTIFACT_DIR / "holdout_metric_comparison.csv").set_index(
        "candidate_id"
    )
    assert validation.loc["conservative_blend_50", "startable_precision_delta_vs_baseline"] < 0
    assert holdout.loc["conservative_blend_50", "startable_precision_delta_vs_baseline"] < 0


def test_guardrail_reports_block_promotion_and_forbidden_sources():
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    notice = (ARTIFACT_DIR / "do_not_promote_notice.md").read_text(encoding="utf-8")

    for phrase in [
        "No production formula changes",
        "No production config changes",
        "No app, model, rank, service, source-truth, runtime",
        "Holdout is not used to define guard thresholds",
        "No routes, TPRR, YPRR, route proxies, ambiguous `rz_att`",
        "No candidate or rescue output is approved for production use",
    ]:
        assert phrase in guardrail
    assert "Do not promote" in notice
