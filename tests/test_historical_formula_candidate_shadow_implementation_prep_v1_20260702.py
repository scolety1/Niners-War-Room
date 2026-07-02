from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_shadow_implementation_prep_v1_20260702"
)

REQUIRED_ARTIFACTS = {
    "preflight_state_audit.md",
    "artifact_manifest.md",
    "shadow_implementation_prep_summary.md",
    "selected_candidate_contract.md",
    "selected_candidate_formula_spec_review_only.md",
    "shadow_inputs_outputs_schema.csv",
    "baseline_vs_selected_comparison_contract.csv",
    "review_only_shadow_config_spec.md",
    "normal_rankings_unchanged_report.md",
    "blocked_production_paths_report.md",
    "pollard_lamb_watchlist_carryforward.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "shadow_sanity_audit_summary.md",
    "watchlist_policy.md",
    "elite_asset_sanity_audit.csv",
    "cutline_sanity_audit.csv",
    "top_mover_sanity_audit.csv",
    "human_review_question_list.md",
}


def test_required_shadow_implementation_prep_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_summary_keeps_candidate_review_only_and_blocks_current_board_output():
    summary = (ARTIFACT_DIR / "shadow_implementation_prep_summary.md").read_text(
        encoding="utf-8"
    )
    sanity = (ARTIFACT_DIR / "shadow_sanity_audit_summary.md").read_text(
        encoding="utf-8"
    )

    assert "wr_boundary_breakout_sensitivity_guard" in summary
    assert "YELLOW_HOLD_FOR_TIM_REVIEW" in summary
    assert "SAFE_YELLOW_BLOCKED_CURRENT_BOARD_INPUT_NOT_APPROVED" in summary
    assert "not production-approved" in summary
    assert "Final gate status: `YELLOW_HOLD_FOR_TIM_REVIEW`" in sanity


def test_selected_candidate_contract_preserves_formula_and_non_promotion():
    contract = (ARTIFACT_DIR / "selected_candidate_contract.md").read_text(
        encoding="utf-8"
    )
    spec = (ARTIFACT_DIR / "selected_candidate_formula_spec_review_only.md").read_text(
        encoding="utf-8"
    )

    assert "review only: `true`" in contract
    assert "production approved: `false`" in contract
    assert "0.80 * baseline + 0.20 * qb_guard_soft_blend" in spec
    assert "not production-approved" in spec


def test_shadow_schema_blocks_forbidden_inputs_and_runtime_uses():
    schema = pd.read_csv(ARTIFACT_DIR / "shadow_inputs_outputs_schema.csv")
    fields = set(schema["field_name"])

    assert {"prior_nwr_points", "prior_targets", "selected_candidate_score"}.issubset(
        fields
    )
    joined = " ".join(schema["blocked_use"].astype(str).str.lower())
    assert "rank wiring" in joined
    assert "hidden sort" in joined
    assert "production formula source truth" in joined


def test_baseline_vs_selected_contract_matches_gate_metrics():
    comparison = pd.read_csv(ARTIFACT_DIR / "baseline_vs_selected_comparison_contract.csv")
    by_metric = {row.metric: row for row in comparison.itertuples(index=False)}

    assert by_metric["holdout_mae_delta_vs_baseline"].selected_value == -1.196383
    assert by_metric["holdout_spearman_delta_vs_baseline"].selected_value == 0.001089
    assert by_metric["holdout_startable_precision_delta_vs_baseline"].selected_value == 0.0
    assert by_metric["actual_hits_moved_below_cutline_validation_holdout"].selected_value == 2
    assert comparison["production_approved"].eq(False).all()


def test_watchlist_carries_pollard_lamb_without_recommendation_or_app_wiring():
    cutline = pd.read_csv(ARTIFACT_DIR / "cutline_sanity_audit.csv")
    labels = dict(zip(cutline["player_name"], cutline["watchlist_label"]))
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    paths = (ARTIFACT_DIR / "blocked_production_paths_report.md").read_text(
        encoding="utf-8"
    )

    assert labels["T.Pollard"] == "EXPLAINABLE_NOT_BLOCKING"
    assert labels["C.Lamb"] == "WATCHLIST_NOT_BLOCKING"
    assert "No candidate output is wired into NWR" in guardrail
    assert "No app wiring or live preview page" in guardrail
    assert "app/" in paths
