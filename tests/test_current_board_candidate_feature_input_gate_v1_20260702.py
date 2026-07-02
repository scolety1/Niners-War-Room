from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "current_board_candidate_feature_input_gate_v1_20260702"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "current_board_candidate_feature_input_gate_summary.md",
    "candidate_feature_input_decision.md",
    "feature_anchor_decision.md",
    "required_candidate_feature_schema.csv",
    "current_board_feature_join_report.csv",
    "missing_candidate_feature_report.csv",
    "allowed_feature_use_report.csv",
    "null_fenced_feature_policy.md",
    "blocked_input_fields_report.md",
    "candidate_shadow_rank_calculation_contract.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "current_board_candidate_feature_input_schema.csv",
    "current_board_candidate_feature_input_sample.csv",
    "current_board_candidate_feature_input_row_count_report.csv",
}


def test_required_candidate_feature_gate_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_decision_is_partial_and_rank_calculation_blocked():
    summary = (ARTIFACT_DIR / "current_board_candidate_feature_input_gate_summary.md").read_text(
        encoding="utf-8"
    )
    decision = (ARTIFACT_DIR / "candidate_feature_input_decision.md").read_text(
        encoding="utf-8"
    )
    contract = (ARTIFACT_DIR / "candidate_shadow_rank_calculation_contract.md").read_text(
        encoding="utf-8"
    )

    assert "Decision: `PARTIAL_CANDIDATE_FEATURE_INPUT_NEEDS_REVIEW`" in summary
    assert "Decision: `PARTIAL_CANDIDATE_FEATURE_INPUT_NEEDS_REVIEW`" in decision
    assert "DO_NOT_CALCULATE_RANKS_FROM_THIS_PARTIAL_EXPORT" in contract


def test_row_count_report_confirms_baseline_and_partial_export():
    report = pd.read_csv(ARTIFACT_DIR / "current_board_candidate_feature_input_row_count_report.csv")
    values = {row.metric: str(row.value) for row in report.itertuples(index=False)}

    assert values["baseline_rows"] == "370"
    assert values["candidate_feature_input_rows"] == "370"
    assert int(values["exact_feature_join_rows"]) > 0
    assert values["candidate_feature_ready_rows"] == "0"
    assert len(values["outside_export_sha256"]) == 64


def test_primary_export_sample_excludes_null_fenced_and_candidate_outputs():
    sample = pd.read_csv(ARTIFACT_DIR / "current_board_candidate_feature_input_sample.csv")
    blocked_optional = {
        "prior_offensive_snaps",
        "prior_offense_pct",
        "prior_receiving_air_yards",
        "prior_receiving_yards_after_catch",
    }

    assert blocked_optional.isdisjoint(set(sample.columns))
    assert "prior_targets" in sample.columns
    assert "prior_nwr_points" in sample.columns
    assert sample["candidate_rank_output_present"].eq(False).all()
    assert sample["production_approved"].eq(False).all()
    assert sample["app_wiring_allowed"].eq(False).all()
    assert sample["model_use_allowed"].eq(False).all()
    assert sample["source_truth_allowed"].eq(False).all()


def test_required_schema_blocks_scoring_and_games_until_safe_source_gate():
    schema = pd.read_csv(ARTIFACT_DIR / "required_candidate_feature_schema.csv")
    by_feature = {row.feature: row for row in schema.itertuples(index=False)}

    assert by_feature["prior_targets"].candidate_gate_status == "AVAILABLE_FROM_2025_USAGE_AGGREGATE"
    assert by_feature["prior_nwr_points"].candidate_gate_status == (
        "BLOCKED_CORE_USAGE_DATASET_LACKS_FULL_SCORING_COMPONENTS"
    )
    assert by_feature["prior_nwr_ppg"].candidate_gate_status == (
        "BLOCKED_CORE_USAGE_DATASET_LACKS_FULL_SCORING_COMPONENTS_AND_GAMES"
    )
    assert by_feature["prior_games"].candidate_gate_status == (
        "BLOCKED_WEEKLY_ROW_COUNT_NOT_ADMITTED_AS_GAMES"
    )


def test_join_report_uses_stable_id_and_no_fuzzy_matching():
    join = pd.read_csv(ARTIFACT_DIR / "current_board_feature_join_report.csv")

    assert join["join_key"].eq("stable_player_id_to_player_id_sleeper_exact").all()
    assert join["fuzzy_name_match_used"].eq(False).all()
    assert "EXACT_SLEEPER_MATCH_2025_USAGE" in set(join["feature_join_status"])


def test_guardrails_block_forbidden_inputs_and_missing_as_zero():
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    blocked = (ARTIFACT_DIR / "blocked_input_fields_report.md").read_text(
        encoding="utf-8"
    )
    missing = (ARTIFACT_DIR / "missing_candidate_feature_report.csv").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "No target-season outcomes were used",
        "No blocked fields are included",
        "Missing values were not forced to zero",
        "No candidate ranks were wired into NWR",
    ]:
        assert phrase in guardrail
    for phrase in [
        "Routes, TPRR, YPRR",
        "ambiguous `rz_att`",
        "Current injuries",
        "Missing-as-zero transformations",
    ]:
        assert phrase in blocked
    assert "Not enough information; do not fill missing with zero" in missing
