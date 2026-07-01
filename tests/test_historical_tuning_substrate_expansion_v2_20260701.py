from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "docs" / "hq" / "experiments" / "historical_tuning_substrate_expansion_v2_20260701"
PARQUET = ARTIFACT_DIR / "nwr_historical_tuning_feature_target_substrate_v2.parquet"


REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "historical_tuning_substrate_v2_summary.md",
    "runtime_restoration_report.md",
    "nflreadpy_or_nflverse_dependency_decision.md",
    "available_historical_sources_inventory_v2.csv",
    "feature_generation_path_report.md",
    "feature_target_substrate_schema_v2.csv",
    "feature_target_substrate_sample_v2.csv",
    "feature_target_row_count_report_v2.csv",
    "season_position_coverage_report_v2.csv",
    "feature_coverage_report_v2.csv",
    "target_outcome_coverage_report_v2.csv",
    "identity_join_report_v2.csv",
    "missingness_semantics_report_v2.md",
    "legacy_zero_fill_replacement_or_fencing_report.md",
    "asof_and_leakage_guardrail_report_v2.md",
    "expanded_historical_data_decision_v2.md",
    "blocked_or_deferred_sources_report_v2.md",
    "future_tuning_readiness_report_v2.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "nwr_historical_tuning_feature_target_substrate_v2.parquet",
}

EXPECTED_SAFE_FEATURES = {
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


def test_required_v2_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert not missing

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert not empty


def test_v2_substrate_expands_v1_and_keeps_n_to_n_plus_one_lag():
    substrate = pd.read_parquet(PARQUET)

    assert len(substrate) == 5518
    assert len(substrate) - 3108 == 2410
    assert substrate["feature_season"].min() == 2012
    assert substrate["feature_season"].max() == 2024
    assert substrate["target_season"].min() == 2013
    assert substrate["target_season"].max() == 2025
    assert (substrate["target_season"] == substrate["feature_season"] + 1).all()
    assert set(substrate["position"].unique()) == {"QB", "RB", "TE", "WR"}


def test_v2_identity_join_is_gsis_based_without_duplicates_or_unmatched_rows():
    substrate = pd.read_parquet(PARQUET)
    report = pd.read_csv(ARTIFACT_DIR / "identity_join_report_v2.csv")
    metrics = dict(zip(report["metric"], report["value"]))

    assert substrate["player_id_gsis"].astype(str).str.match(r"^00-\d+$").all()
    assert not substrate.duplicated(["player_id_gsis", "feature_season", "target_season"]).any()
    assert int(metrics["matched_feature_label_rows"]) == 5518
    assert int(metrics["unmatched_feature_rows"]) == 0
    assert int(metrics["unmatched_label_rows"]) == 0
    assert int(metrics["duplicate_identity_season_keys"]) == 0


def test_v2_null_fences_optional_source_legacy_zero_fields():
    substrate = pd.read_parquet(PARQUET)

    assert substrate["prior_offensive_snaps"].isna().sum() == 811
    assert substrate["prior_offense_pct"].isna().sum() == 811
    assert substrate["prior_receiving_air_yards"].isna().sum() == 663
    assert substrate["prior_receiving_yards_after_catch"].isna().sum() == 663
    assert substrate["optional_source_null_fenced"].sum() == 1371


def test_v2_is_review_only_and_not_approved_for_runtime_or_training_use():
    substrate = pd.read_parquet(PARQUET)

    assert substrate["review_only"].all()
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


def test_forbidden_feature_families_are_absent_from_v2_canonical_columns():
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


def test_schema_marks_expected_safe_lagged_features_and_fences():
    schema = pd.read_csv(ARTIFACT_DIR / "feature_target_substrate_schema_v2.csv")
    feature_columns = set(schema.loc[schema["role"] == "safe_lagged_feature", "column_name"])

    assert feature_columns == EXPECTED_SAFE_FEATURES
    fenced = dict(zip(schema["column_name"], schema["null_fenced_by"]))
    assert fenced["prior_offensive_snaps"] == "snap_pct_missing"
    assert fenced["prior_offense_pct"] == "snap_pct_missing"
    assert fenced["prior_receiving_air_yards"] == "air_yards_missing"
    assert fenced["prior_receiving_yards_after_catch"] == "air_yards_missing"
    assert not schema["production_approved"].any()
    assert not schema["model_use_allowed"].any()
    assert not schema["training_allowed"].any()
    assert not schema["source_truth_allowed"].any()


def test_v2_reports_runtime_restored_but_no_formula_search_or_production_readiness():
    runtime = (ARTIFACT_DIR / "runtime_restoration_report.md").read_text(encoding="utf-8")
    summary = (ARTIFACT_DIR / "historical_tuning_substrate_v2_summary.md").read_text(encoding="utf-8")
    handoff = (ARTIFACT_DIR / "next_phase_handoff.md").read_text(encoding="utf-8")

    assert "GREEN for local artifact generation" in runtime
    assert "did not run formula search" in summary
    assert "Future formula tuning is still not production-viable" in summary
    assert "V3 should not be a formula search" in handoff
