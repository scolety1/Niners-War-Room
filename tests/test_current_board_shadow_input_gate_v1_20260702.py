from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "current_board_shadow_input_gate_v1_20260702"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "current_board_shadow_input_gate_summary.md",
    "approved_input_decision.md",
    "required_baseline_export_schema.csv",
    "current_board_input_source_inventory.csv",
    "safe_export_path_decision.md",
    "manual_export_contract.md",
    "blocked_input_fields_report.md",
    "candidate_shadow_join_contract.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "current_board_baseline_shadow_input_sample.csv",
    "current_board_baseline_shadow_input_schema.csv",
    "current_board_baseline_shadow_input_row_count_report.csv",
}


def test_required_current_board_shadow_input_gate_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_input_gate_decision_generated_review_only_export():
    summary = (ARTIFACT_DIR / "current_board_shadow_input_gate_summary.md").read_text(
        encoding="utf-8"
    )
    decision = (ARTIFACT_DIR / "approved_input_decision.md").read_text(encoding="utf-8")

    assert "Decision: `SAFE_EXPORT_GENERATED_REVIEW_ONLY`" in summary
    assert "Decision: `SAFE_EXPORT_GENERATED_REVIEW_ONLY`" in decision
    assert "does not create candidate formula output" in summary
    assert "Production rank source" in decision


def test_generated_sample_contains_required_baseline_fields_and_no_candidate_output():
    sample = pd.read_csv(ARTIFACT_DIR / "current_board_baseline_shadow_input_sample.csv")
    required = {
        "stable_player_id",
        "player_name",
        "position",
        "team",
        "current_baseline_rank",
        "current_baseline_position_rank",
        "warning_flags",
        "candidate_formula_output_present",
        "production_approved",
        "app_wiring_allowed",
        "model_input_allowed",
    }

    assert required.issubset(set(sample.columns))
    assert sample["candidate_formula_output_present"].eq(False).all()
    assert sample["production_approved"].eq(False).all()
    assert sample["app_wiring_allowed"].eq(False).all()
    assert sample["model_input_allowed"].eq(False).all()
    assert sample["current_baseline_rank"].notna().all()


def test_source_inventory_uses_tracked_review_artifact_and_blocks_raw_local_export():
    inventory = pd.read_csv(ARTIFACT_DIR / "current_board_input_source_inventory.csv")
    by_source = {row.source_id: row for row in inventory.itertuples(index=False)}

    assert by_source["raw_full_player_board_local_export"].decision == "DO_NOT_TRACK_RAW_LOCAL_EXPORT"
    assert by_source["unified_player_universe_review"].decision == "USED_FOR_SAFE_REVIEW_ONLY_EXPORT"
    assert by_source["outcome_v2_current_player_display"].decision == "CONTEXT_ONLY_NOT_BASELINE"


def test_row_count_report_documents_local_only_export_checksum_and_position_counts():
    report = pd.read_csv(ARTIFACT_DIR / "current_board_baseline_shadow_input_row_count_report.csv")
    values = {row.metric: str(row.value) for row in report.itertuples(index=False)}

    assert values["total_rows"] == "370"
    assert "C:\\NWR_REVIEW\\current_board_shadow_input_gate_v1_20260702" in values["outside_export_path"]
    assert len(values["outside_export_sha256"]) == 64
    assert int(values["position_rows_WR"]) > 0
    assert int(values["position_rows_RB"]) > 0


def test_guardrails_block_app_model_rank_runtime_and_forbidden_fields():
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    blocked = (ARTIFACT_DIR / "blocked_input_fields_report.md").read_text(
        encoding="utf-8"
    )
    join = (ARTIFACT_DIR / "candidate_shadow_join_contract.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "No app wiring or live preview page",
        "No production rankings behavior changes",
        "No candidate output wired into NWR",
        "No raw/shared/cache/local export/secrets files tracked",
    ]:
        assert phrase in guardrail
    for phrase in [
        "Candidate formula output or candidate rank",
        "Market, ADP, vendor, projection",
        "Routes, TPRR, YPRR",
        "ambiguous `rz_att`",
    ]:
        assert phrase in blocked
    assert "Candidate rows must not overwrite baseline ranks" in join
