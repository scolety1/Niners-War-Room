from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_shadow_review_gate_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "shadow_review_gate_summary.md",
    "shadow_review_decision.md",
    "tim_human_review_notes_applied.md",
    "selected_redesign_metric_summary.csv",
    "baseline_vs_candidate_gate_matrix.csv",
    "remaining_cutline_case_review.md",
    "pollard_lamb_case_decision.md",
    "position_season_stability_gate_report.csv",
    "startable_topn_gate_report.csv",
    "shadow_review_packet_requirements.md",
    "blocked_production_promotion_report.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}


def test_required_shadow_review_gate_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_shadow_review_gate_decision_is_review_only_go():
    summary = (ARTIFACT_DIR / "shadow_review_gate_summary.md").read_text(
        encoding="utf-8"
    )
    decision = (ARTIFACT_DIR / "shadow_review_decision.md").read_text(
        encoding="utf-8"
    )

    assert "GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY" in summary
    assert "wr_boundary_breakout_sensitivity_guard" in summary
    assert "Decision: `GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY`" in decision
    assert "does not approve shadow app wiring" in decision


def test_selected_redesign_metrics_support_gate_without_promotion():
    metrics = pd.read_csv(ARTIFACT_DIR / "selected_redesign_metric_summary.csv")
    selected = metrics[metrics["candidate_id"].eq("wr_boundary_breakout_sensitivity_guard")]
    holdout = selected[selected["split"].eq("holdout")].iloc[0]
    review = selected[selected["split"].eq("validation_holdout")].iloc[0]

    assert holdout["mae_delta_vs_baseline"] == -1.196383
    assert holdout["spearman_delta_vs_baseline"] == 0.001089
    assert holdout["startable_precision_delta_vs_baseline"] == 0.0
    assert int(review["actual_hits_moved_below_cutline"]) == 2
    assert int(review["elite_qb_severe_regressions"]) == 1
    assert metrics["production_approved"].eq(False).all()


def test_gate_matrix_allows_packet_and_blocks_production():
    gate = pd.read_csv(ARTIFACT_DIR / "baseline_vs_candidate_gate_matrix.csv")

    assert set(gate["status"]) == {"PASS"}
    assert set(gate["decision_effect"]) == {"GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY"}
    assert gate["production_approved"].eq(False).all()
    assert "production_promotion_blocked" in set(gate["gate_question"])


def test_tim_notes_make_pollard_lamb_watchlist_not_blockers():
    notes = (ARTIFACT_DIR / "tim_human_review_notes_applied.md").read_text(
        encoding="utf-8"
    )
    cases = (ARTIFACT_DIR / "pollard_lamb_case_decision.md").read_text(
        encoding="utf-8"
    )

    assert "Pollard" in notes
    assert "acceptable and explainable" in notes
    assert "Lamb remains worth watching" in notes
    assert "not a blocker" in cases
    assert "Production promotion remains blocked" in cases


def test_packet_requirements_forbid_app_and_runtime_wiring():
    requirements = (ARTIFACT_DIR / "shadow_review_packet_requirements.md").read_text(
        encoding="utf-8"
    )
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    blocked = (ARTIFACT_DIR / "blocked_production_promotion_report.md").read_text(
        encoding="utf-8"
    )

    for phrase in [
        "Do not create app pages",
        "live preview",
        "ranking wiring",
        "production configs",
    ]:
        assert phrase in requirements
    for phrase in [
        "No production formula changes",
        "No app wiring or live preview page",
        "No candidate output is wired into NWR",
        "No production promotion is approved",
    ]:
        assert phrase in guardrail
    assert "Production promotion remains blocked" in blocked
