from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "current_board_candidate_scoring_feature_completion_gate_v1_20260702"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "scoring_feature_completion_gate_summary.md",
    "scoring_feature_decision.md",
    "prior_nwr_points_derivation_report.md",
    "prior_games_derivation_report.md",
    "prior_nwr_ppg_derivation_report.md",
    "scoring_source_inventory.csv",
    "scoring_feature_schema.csv",
    "scoring_feature_join_report.csv",
    "candidate_feature_ready_row_count_report.csv",
    "missing_or_null_fenced_players_report.csv",
    "rookie_no_prior_stats_policy.md",
    "duplicate_source_row_handling_report.md",
    "candidate_shadow_rank_input_contract_v2.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "completed_candidate_feature_input_schema.csv",
    "completed_candidate_feature_input_sample.csv",
    "completed_candidate_feature_input_checksum_report.csv",
    "completed_candidate_feature_missing_reason_breakdown.csv",
}


def test_required_scoring_completion_gate_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_decision_is_partial_completion_with_null_fences():
    summary = (ARTIFACT_DIR / "scoring_feature_completion_gate_summary.md").read_text(
        encoding="utf-8"
    )
    decision = (ARTIFACT_DIR / "scoring_feature_decision.md").read_text(encoding="utf-8")

    assert "Decision: `PARTIAL_SCORING_FEATURES_COMPLETED_WITH_NULL_FENCES`" in summary
    assert "Decision: `PARTIAL_SCORING_FEATURES_COMPLETED_WITH_NULL_FENCES`" in decision
    assert "Rows without an exact 2025 REG observed-row scoring match remain null-fenced" in decision


def test_row_count_report_confirms_completed_ready_rows_and_null_fences():
    report = pd.read_csv(ARTIFACT_DIR / "candidate_feature_ready_row_count_report.csv")
    values = {row.metric: str(row.value) for row in report.itertuples(index=False)}

    assert values["current_board_rows"] == "370"
    assert values["scoring_feature_rows_generated"] == "245"
    assert values["candidate_feature_ready_count"] == "245"
    assert values["null_fenced_or_missing_count"] == "125"
    assert values["raw_2025_reg_after_exact_dedup"] == "18539"
    assert values["duplicate_keys_after_dedup"] == "0"
    assert len(values["outside_export_sha256"]) == 64


def test_scoring_schema_completes_three_required_features_review_only():
    schema = pd.read_csv(ARTIFACT_DIR / "scoring_feature_schema.csv")
    by_feature = {row.feature: row for row in schema.itertuples(index=False)}

    assert by_feature["prior_nwr_points"].status == "COMPLETED_FOR_EXACT_2025_REG_OBSERVED_ROWS"
    assert by_feature["prior_games"].status == "COMPLETED_FOR_EXACT_2025_REG_OBSERVED_ROWS"
    assert by_feature["prior_nwr_ppg"].status == "COMPLETED_WHEN_PRIOR_GAMES_GT_0"
    assert schema["review_only"].eq(True).all()
    assert schema["production_approved"].eq(False).all()


def test_completed_sample_has_scoring_features_but_no_candidate_rank_outputs_or_null_fenced_optional():
    sample = pd.read_csv(ARTIFACT_DIR / "completed_candidate_feature_input_sample.csv")
    blocked_optional = {
        "prior_offensive_snaps",
        "prior_offense_pct",
        "prior_receiving_air_yards",
        "prior_receiving_yards_after_catch",
    }
    forbidden_fragments = ("route", "tprr", "yprr", "rz_att", "red_zone", "adp", "projection")

    assert blocked_optional.isdisjoint(set(sample.columns))
    for field in ["prior_nwr_points", "prior_games", "prior_nwr_ppg"]:
        assert field in sample.columns
        assert sample[field].notna().any()
    assert sample["candidate_rank_output_present"].eq(False).all()
    assert sample["production_approved"].eq(False).all()
    assert sample["app_wiring_allowed"].eq(False).all()
    assert sample["model_use_allowed"].eq(False).all()
    assert sample["source_truth_allowed"].eq(False).all()

    normalized_columns = "|".join(sample.columns).lower()
    for fragment in forbidden_fragments:
        assert fragment not in normalized_columns


def test_scoring_join_report_uses_stable_identity_only():
    join = pd.read_csv(ARTIFACT_DIR / "scoring_feature_join_report.csv")

    assert join["join_key"].eq(
        "player_id_gsis exact after stable_player_id_to_player_id_sleeper gate"
    ).all()
    assert join["fuzzy_name_match_used"].eq(False).all()
    assert "EXACT_GSIS_SCORING_MATCH_2025_REG" in set(join["scoring_feature_status"])
    assert "NULL_FENCED_NO_2025_USAGE_FEATURE_JOIN" in set(join["scoring_feature_status"])


def test_derivation_reports_block_imported_fantasy_points_and_missing_as_zero():
    points = (ARTIFACT_DIR / "prior_nwr_points_derivation_report.md").read_text(
        encoding="utf-8"
    )
    games = (ARTIFACT_DIR / "prior_games_derivation_report.md").read_text(encoding="utf-8")
    ppg = (ARTIFACT_DIR / "prior_nwr_ppg_derivation_report.md").read_text(encoding="utf-8")
    missing = (ARTIFACT_DIR / "missing_or_null_fenced_players_report.csv").read_text(
        encoding="utf-8"
    )

    assert "Imported `fantasy_points` and `fantasy_points_ppr`" in points
    assert "No absent player was assigned zero points" in points
    assert "Players absent from the factual source remain null-fenced" in games
    assert "No no-stat player receives `0.0` PPG" in ppg
    assert "do not fill missing with zero" in missing


def test_guardrails_and_rank_contract_block_production_wiring():
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    contract = (ARTIFACT_DIR / "candidate_shadow_rank_input_contract_v2.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "No 2026 current context or target outcomes were used",
        "Missing values were not forced to zero",
        "No candidate ranks were wired into NWR",
        "No production formula/config files changed",
    ]:
        assert phrase in guardrail
    for phrase in [
        "Production rankings",
        "Hidden sort",
        "Recommendations",
        "Source-truth promotion",
        "Candidate output wiring into NWR",
    ]:
        assert phrase in contract
