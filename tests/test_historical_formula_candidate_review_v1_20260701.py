from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_review_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "historical_formula_candidate_review_summary.md",
    "selected_candidate_plain_english_review.md",
    "candidate_formula_lineage.md",
    "candidate_inputs_and_weights_review.csv",
    "baseline_vs_candidate_metric_summary.csv",
    "validation_holdout_metric_delta_report.csv",
    "position_level_review.csv",
    "season_level_review.csv",
    "topn_startable_review.csv",
    "largest_error_improvements_sample.csv",
    "largest_error_regressions_sample.csv",
    "player_archetype_impact_review.md",
    "candidate_risk_register.md",
    "candidate_human_review_questions.md",
    "production_non_promotion_report.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "candidate_stress_test_summary.md",
    "holdout_stability_report.csv",
    "position_season_interaction_report.csv",
    "metric_tradeoff_report.md",
    "overfit_recheck_report.md",
    "leakage_recheck_report.md",
    "blocked_feature_recheck_report.md",
    "tim_review_brief.md",
    "candidate_decision_card.md",
    "candidate_metric_snapshot.csv",
    "candidate_review_checklist.md",
    "future_promotion_gate_requirements.md",
    "do_not_promote_yet_notice.md",
}


def test_required_candidate_review_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_review_decision_is_strong_review_only_not_production():
    summary = (ARTIFACT_DIR / "historical_formula_candidate_review_summary.md").read_text(
        encoding="utf-8"
    )
    card = (ARTIFACT_DIR / "candidate_decision_card.md").read_text(encoding="utf-8")
    notice = (ARTIFACT_DIR / "do_not_promote_yet_notice.md").read_text(encoding="utf-8")

    assert "REVIEW_CANDIDATE_STRONG_BUT_NOT_PRODUCTION_APPROVED" in summary
    assert "usage_opportunity_volume" in summary
    assert "no candidate is production-approved" in summary
    assert "Production-approved: no" in card
    assert "Do not promote" in notice


def test_metric_review_preserves_candidate_search_deltas():
    deltas = pd.read_csv(ARTIFACT_DIR / "validation_holdout_metric_delta_report.csv")
    by_split = deltas.set_index("split")

    assert by_split.loc["validation", "mae_delta_candidate_minus_baseline"] == -2.036621
    assert by_split.loc["holdout", "mae_delta_candidate_minus_baseline"] == -1.646492
    assert by_split.loc["holdout", "spearman_delta"] == 0.001126
    assert by_split.loc["holdout", "startable_precision_delta"] == 0.0
    assert set(deltas["review_note"]) == {"positive_mae_with_stable_rank_order"}


def test_holdout_position_and_season_stability_are_reviewed():
    position = pd.read_csv(ARTIFACT_DIR / "position_level_review.csv")
    season = pd.read_csv(ARTIFACT_DIR / "season_level_review.csv")
    holdout_stability = pd.read_csv(ARTIFACT_DIR / "holdout_stability_report.csv")

    holdout_positions = position[position["split"].eq("holdout")]
    assert len(holdout_positions) == 4
    assert holdout_positions["mae_delta_candidate_minus_baseline"].lt(0).all()

    holdout_seasons = season[season["split"].eq("holdout")]
    assert len(holdout_seasons) == 2
    assert holdout_seasons["mae_delta_candidate_minus_baseline"].lt(0).all()
    assert "PASS_NO_MATERIAL_HOLDOUT_DEGRADATION" in set(holdout_stability["stability_result"])


def test_candidate_inputs_are_allowed_review_only_primary_features():
    inputs = pd.read_csv(ARTIFACT_DIR / "candidate_inputs_and_weights_review.csv")

    assert set(inputs["input_feature"]) == {
        "prior_nwr_points",
        "prior_carries",
        "prior_receptions",
        "prior_targets",
        "prior_opportunities",
    }
    assert set(inputs["contract_status"]) == {"ALLOW_REVIEW_ONLY"}
    assert inputs["primary_pass"].all()
    assert not inputs["null_fenced"].any()
    assert not inputs["production_approved"].any()


def test_error_samples_exist_for_improvements_and_regressions():
    improvements = pd.read_csv(ARTIFACT_DIR / "largest_error_improvements_sample.csv")
    regressions = pd.read_csv(ARTIFACT_DIR / "largest_error_regressions_sample.csv")

    assert len(improvements) == 25
    assert len(regressions) == 25
    assert improvements["error_improvement"].gt(0).all()
    assert regressions["error_improvement"].lt(0).all()
    assert set(improvements["split"]).issubset({"validation", "holdout"})
    assert set(regressions["split"]).issubset({"validation", "holdout"})


def test_guardrail_reports_confirm_no_promotion_or_blocked_feature_use():
    blocked = (ARTIFACT_DIR / "blocked_feature_recheck_report.md").read_text(encoding="utf-8")
    leakage = (ARTIFACT_DIR / "leakage_recheck_report.md").read_text(encoding="utf-8")
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    non_promotion = (ARTIFACT_DIR / "production_non_promotion_report.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "routes",
        "TPRR",
        "YPRR",
        "ambiguous `rz_att`",
        "red-zone sidecars",
        "market/ADP/vendor/projection/rank fields",
        "current-only roster/status/injury/depth/schedule context",
    ]:
        assert phrase in blocked
    assert "Holdout was evaluated only after validation selection" in leakage
    assert "No formula tuning or optimization" in guardrail
    assert "No candidate is production-approved" in non_promotion
