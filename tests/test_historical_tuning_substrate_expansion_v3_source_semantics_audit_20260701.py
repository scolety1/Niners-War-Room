from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
)
PARQUET = ARTIFACT_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "historical_tuning_substrate_v3_summary.md",
    "v2_source_semantics_audit_summary.md",
    "feature_zero_semantics_matrix_v3.csv",
    "field_source_lineage_matrix_v3.csv",
    "zero_pattern_audit_by_season_position_v3.csv",
    "null_fencing_decision_matrix_v3.csv",
    "legacy_zero_fill_audit_report.md",
    "source_regeneration_comparison_report.md",
    "safe_feature_allowlist_v3.csv",
    "fenced_feature_report_v3.csv",
    "feature_target_substrate_schema_v3.csv",
    "feature_target_substrate_sample_v3.csv",
    "feature_target_row_count_report_v3.csv",
    "season_position_coverage_report_v3.csv",
    "feature_coverage_report_v3.csv",
    "target_outcome_coverage_report_v3.csv",
    "identity_join_report_v3.csv",
    "missingness_semantics_report_v3.md",
    "asof_and_leakage_guardrail_report_v3.md",
    "future_tuning_readiness_report_v3.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "nwr_historical_tuning_feature_target_substrate_v3.parquet",
}

EXPECTED_FEATURES = {
    "prior_nwr_points",
    "prior_games",
    "prior_nwr_ppg",
    "prior_targets",
    "prior_carries",
    "prior_receptions",
    "prior_touches",
    "prior_opportunities",
    "prior_rushing_yards",
    "prior_receiving_yards",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
    "prior_rushing_first_downs",
    "prior_receiving_first_downs",
    "prior_passing_attempts",
    "prior_passing_completions",
    "prior_passing_yards",
    "prior_passing_td",
    "prior_interceptions",
    "prior_passing_first_downs",
    "prior_offensive_snaps",
    "prior_offense_pct",
}

NULL_FENCED_FEATURES = {
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
    "prior_offensive_snaps",
    "prior_offense_pct",
}


def test_required_v3_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_v3_substrate_preserves_v2_coverage_and_n_to_n_plus_one_lag():
    substrate = pd.read_parquet(PARQUET)

    assert len(substrate) == 5518
    assert substrate["feature_season"].min() == 2012
    assert substrate["feature_season"].max() == 2024
    assert substrate["target_season"].min() == 2013
    assert substrate["target_season"].max() == 2025
    assert (substrate["target_season"] == substrate["feature_season"] + 1).all()
    assert set(substrate["position"].unique()) == {"QB", "RB", "TE", "WR"}
    assert substrate["position"].value_counts().sort_index().to_dict() == {
        "QB": 754,
        "RB": 1429,
        "TE": 1211,
        "WR": 2124,
    }


def test_v3_identity_join_remains_gsis_based_without_unmatched_or_duplicate_rows():
    substrate = pd.read_parquet(PARQUET)
    report = pd.read_csv(ARTIFACT_DIR / "identity_join_report_v3.csv")
    metrics = dict(zip(report["metric"], report["value"]))

    assert substrate["player_id_gsis"].astype(str).str.match(r"^00-\d+$").all()
    assert not substrate.duplicated(["player_id_gsis", "feature_season", "target_season"]).any()
    assert int(metrics["canonical_rows"]) == 5518
    assert int(metrics["matched_feature_label_rows"]) == 5518
    assert int(metrics["unmatched_feature_rows"]) == 0
    assert int(metrics["unmatched_label_rows"]) == 0
    assert int(metrics["duplicate_identity_season_keys"]) == 0


def test_v3_zero_semantics_matrix_has_column_level_decisions_for_every_feature():
    matrix = pd.read_csv(ARTIFACT_DIR / "feature_zero_semantics_matrix_v3.csv")
    allowlist = pd.read_csv(ARTIFACT_DIR / "safe_feature_allowlist_v3.csv")
    fenced = pd.read_csv(ARTIFACT_DIR / "fenced_feature_report_v3.csv")

    allowed = set(matrix.loc[matrix["allowed_in_v3_review_substrate"], "feature"])
    blocked = set(matrix.loc[matrix["blocked_in_v3"], "feature"])

    assert allowed == EXPECTED_FEATURES
    assert set(allowlist["feature"]) == EXPECTED_FEATURES
    assert set(matrix.loc[matrix["null_fenced_in_v3"], "feature"]) == NULL_FENCED_FEATURES
    assert NULL_FENCED_FEATURES.issubset(set(fenced["feature"]))
    assert {
        "red_zone_targets",
        "red_zone_carries",
        "red_zone_pass_attempts",
        "ambiguous_rz_att",
        "routes_tprr_yprr_family",
    }.issubset(blocked)
    assert not matrix["zero_semantics_decision"].isna().any()
    assert not matrix["production_approved"].any()
    assert not matrix["model_use_allowed"].any()
    assert not matrix["training_allowed"].any()
    assert not matrix["source_truth_allowed"].any()


def test_v3_keeps_optional_source_null_fences_and_does_not_force_missing_to_zero():
    substrate = pd.read_parquet(PARQUET)
    null_fences = pd.read_csv(ARTIFACT_DIR / "null_fencing_decision_matrix_v3.csv")
    by_feature = null_fences.set_index("feature")

    assert substrate["prior_offensive_snaps"].isna().sum() == 811
    assert substrate["prior_offense_pct"].isna().sum() == 811
    assert substrate["prior_receiving_air_yards"].isna().sum() == 663
    assert substrate["prior_receiving_yards_after_catch"].isna().sum() == 663
    assert substrate["optional_source_null_fenced"].sum() == 1371
    for feature in NULL_FENCED_FEATURES:
        assert by_feature.loc[feature, "fence_decision"] == "KEEP_NULL_FENCE"


def test_v3_source_comparison_has_no_local_or_nflreadpy_mismatches():
    comparison = pd.read_csv(ARTIFACT_DIR / "source_regeneration_comparison_matrix_v3.csv")

    assert comparison["local_mismatch_count"].fillna(0).astype(int).sum() == 0
    direct = comparison[
        comparison["nflreadpy_comparison_status"].isin(
            ["PASS_EXACT_MATCH_ON_NON_NULL_ROWS", "MISMATCH_REVIEW_REQUIRED"]
        )
    ]
    assert len(direct) == 16
    assert direct["nflreadpy_mismatch_count"].fillna(0).astype(int).sum() == 0


def test_v3_is_review_only_and_not_approved_for_runtime_or_training_use():
    substrate = pd.read_parquet(PARQUET)

    assert substrate["review_only"].all()
    assert not substrate["v3_formula_search_allowed"].any()
    assert not substrate["v3_future_formula_tuning_viable"].any()
    for column in [
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
        "production_approved",
    ]:
        assert column in substrate.columns
        assert not substrate[column].any()


def test_forbidden_feature_families_are_absent_from_v3_canonical_columns():
    substrate = pd.read_parquet(PARQUET)
    forbidden_tokens = [
        "route",
        "tprr",
        "yprr",
        "rz_att",
        "adp",
        "market",
        "projection",
        "vendor",
        "depth",
        "injury",
        "schedule",
        "active_weeks",
        "is_active_any_week",
    ]
    forbidden_hits = [
        column
        for column in substrate.columns
        if any(token in column.lower() for token in forbidden_tokens)
    ]
    assert forbidden_hits == []


def test_v3_reports_no_formula_search_and_not_production_viable():
    summary = (ARTIFACT_DIR / "historical_tuning_substrate_v3_summary.md").read_text(
        encoding="utf-8"
    )
    readiness = (ARTIFACT_DIR / "future_tuning_readiness_report_v3.md").read_text(
        encoding="utf-8"
    )
    merge_safety = (ARTIFACT_DIR / "merge_safety_report.md").read_text(encoding="utf-8")

    assert "did not run formula search" in summary
    assert "Future formula tuning is still not production-viable" in summary
    assert "future formula tuning is still not production-viable" in readiness
    assert "MERGE_READY_REVIEW_ONLY_EVIDENCE" in merge_safety
