from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_search_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "historical_formula_candidate_search_summary.md",
    "candidate_search_scope.md",
    "baseline_formula_definition.md",
    "candidate_formula_definitions.csv",
    "candidate_formula_family_matrix.csv",
    "train_validation_holdout_split_report.csv",
    "baseline_metric_report.csv",
    "candidate_metric_report.csv",
    "validation_leaderboard.csv",
    "holdout_evaluation_report.csv",
    "position_level_metric_report.csv",
    "season_level_metric_report.csv",
    "topn_bucket_metric_report.csv",
    "candidate_selection_decision.md",
    "selected_candidate_review_packet.md",
    "null_fenced_sensitivity_report.md",
    "overfit_and_leakage_report.md",
    "blocked_feature_compliance_report.md",
    "production_non_promotion_report.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}

NULL_FENCED_FEATURES = {
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
}

FORBIDDEN_FEATURE_TOKENS = [
    "route",
    "tprr",
    "yprr",
    "rz_att",
    "red_zone",
    "adp",
    "market",
    "vendor",
    "projection",
    "rank",
    "depth",
    "injury",
    "schedule",
]


def test_required_candidate_search_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_candidate_search_uses_readiness_gate_split_counts():
    split_report = pd.read_csv(ARTIFACT_DIR / "train_validation_holdout_split_report.csv")
    split_counts = split_report.groupby("split")["rows"].sum().to_dict()

    assert split_counts == {"holdout": 890, "train": 3716, "validation": 912}
    assert not split_report["holdout_used_for_selection"].any()
    assert set(split_report["split_policy"]) == {"readiness_gate_fixed_feature_season_policy"}


def test_candidate_definitions_are_fixed_review_only_and_primary_excludes_null_fences():
    definitions = pd.read_csv(ARTIFACT_DIR / "candidate_formula_definitions.csv")

    assert len(definitions) == 9
    assert set(definitions["candidate_id"]) == {
        "baseline_v3_prior_points",
        "conservative_ppg_games_blend",
        "usage_opportunity_volume",
        "yards_first_down_production",
        "qb_td_dampened_review",
        "position_specific_interpretable_blend",
        "optional_air_yac_sensitivity",
        "optional_snap_context_sensitivity",
        "small_fixed_review_ensemble",
    }
    primary = definitions[
        definitions["primary_or_sensitivity"].isin(["primary", "primary_baseline", "secondary_review"])
    ]
    primary_feature_text = "; ".join(primary["features_used"].astype(str))
    for feature in NULL_FENCED_FEATURES:
        assert feature not in primary_feature_text
    for token in FORBIDDEN_FEATURE_TOKENS:
        assert token not in primary_feature_text.lower()
    for column in [
        "production_approved",
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
    ]:
        assert not definitions[column].any()


def test_validation_selection_and_holdout_are_separated():
    leaderboard = pd.read_csv(ARTIFACT_DIR / "validation_leaderboard.csv")
    holdout = pd.read_csv(ARTIFACT_DIR / "holdout_evaluation_report.csv")
    decision = (ARTIFACT_DIR / "candidate_selection_decision.md").read_text(encoding="utf-8")

    assert leaderboard.iloc[0]["candidate_id"] == "usage_opportunity_volume"
    assert bool(leaderboard.iloc[0]["selection_eligible"])
    assert set(holdout["candidate_id"]) == {"baseline_v3_prior_points", "usage_opportunity_volume"}
    assert holdout["holdout_evaluated_after_validation_selection"].all()
    assert "Selection source: validation metrics only" in decision
    assert "Holdout was not used for selection" in decision


def test_selected_candidate_is_review_only_and_not_production_approved():
    summary = (ARTIFACT_DIR / "historical_formula_candidate_search_summary.md").read_text(
        encoding="utf-8"
    )
    packet = (ARTIFACT_DIR / "selected_candidate_review_packet.md").read_text(encoding="utf-8")
    non_promotion = (ARTIFACT_DIR / "production_non_promotion_report.md").read_text(
        encoding="utf-8"
    )

    assert "STRONG_REVIEW_ONLY_CANDIDATE_NOT_PRODUCTION_APPROVED" in summary
    assert "No candidate is production-approved" in summary
    assert "candidate-only evidence" in packet
    assert "must not be wired into NWR" in packet
    assert "No candidate is production-approved" in non_promotion


def test_null_fenced_sensitivity_is_not_primary_and_does_not_fill_missing_zero():
    sensitivity = pd.read_csv(ARTIFACT_DIR / "null_fenced_sensitivity_report.csv")
    sensitivity_md = (ARTIFACT_DIR / "null_fenced_sensitivity_report.md").read_text(
        encoding="utf-8"
    )

    assert set(sensitivity["candidate_id"]) == {
        "optional_air_yac_sensitivity",
        "optional_snap_context_sensitivity",
    }
    assert not sensitivity["primary_pass_used"].any()
    assert sensitivity["excluded_null_fenced_rows"].gt(0).all()
    assert sensitivity["null_handling"].str.contains("not filled with zero").all()
    assert "Missing values are not filled with zero" in sensitivity_md


def test_blocked_feature_and_leakage_reports_keep_guardrails_closed():
    blocked = (ARTIFACT_DIR / "blocked_feature_compliance_report.md").read_text(encoding="utf-8")
    leakage = (ARTIFACT_DIR / "overfit_and_leakage_report.md").read_text(encoding="utf-8")
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")

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
    assert "Holdout was evaluated after validation selection" in leakage
    assert "Null-fenced fields were excluded from primary candidates" in leakage
    assert "No production formula changes" in guardrail
