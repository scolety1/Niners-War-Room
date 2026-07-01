from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_promotion_gate_prep_v1_20260701"
)

REQUIRED_ARTIFACTS = {
    "artifact_manifest.md",
    "candidate_promotion_gate_prep_summary.md",
    "candidate_evidence_consolidation.md",
    "candidate_metric_tradeoff_matrix.csv",
    "position_cutline_impact_report.csv",
    "startable_bucket_tradeoff_report.csv",
    "season_stability_report.csv",
    "largest_regression_casebook.csv",
    "largest_improvement_casebook.csv",
    "player_archetype_impact_report.csv",
    "candidate_failure_mode_report.md",
    "candidate_strengths_report.md",
    "shadow_review_requirements.md",
    "human_review_checklist.md",
    "advance_hold_reject_decision_card.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
}

CASEBOOK_COLUMNS = {
    "player_id",
    "player_name",
    "position",
    "feature_season",
    "target_season",
    "baseline_error",
    "candidate_error",
    "error_delta",
    "baseline_score_or_rank_proxy",
    "candidate_score_or_rank_proxy",
    "actual_target",
    "startable_bucket",
    "top_bucket",
    "archetype_label",
    "short_review_note",
}


def test_required_gate_prep_artifacts_exist_and_are_nonempty():
    missing = [name for name in REQUIRED_ARTIFACTS if not (ARTIFACT_DIR / name).exists()]
    assert missing == []

    empty = [name for name in REQUIRED_ARTIFACTS if (ARTIFACT_DIR / name).stat().st_size == 0]
    assert empty == []


def test_gate_decision_is_hold_for_human_review_only():
    summary = (ARTIFACT_DIR / "candidate_promotion_gate_prep_summary.md").read_text(
        encoding="utf-8"
    )
    decision = (ARTIFACT_DIR / "advance_hold_reject_decision_card.md").read_text(
        encoding="utf-8"
    )
    notice = (ARTIFACT_DIR / "do_not_promote_notice.md").read_text(encoding="utf-8")

    assert "HOLD_FOR_HUMAN_REVIEW" in summary
    assert "Advance to shadow-review prep now: no" in decision
    assert "Reject now: no" in decision
    assert "Do not promote `usage_opportunity_volume`" in notice


def test_metric_tradeoff_matrix_preserves_core_candidate_review_evidence():
    matrix = pd.read_csv(ARTIFACT_DIR / "candidate_metric_tradeoff_matrix.csv")
    aggregate = matrix[
        matrix["evidence_scope"].eq("aggregate")
        & matrix["split"].eq("holdout")
        & matrix["metric"].eq("mae")
    ].iloc[0]

    assert aggregate["delta_candidate_minus_baseline"] == -1.646492
    assert "SUPPORTS_CANDIDATE" in set(matrix["gate_assessment"])
    assert "REVIEW_RISK" in set(matrix["gate_assessment"])


def test_casebooks_have_required_columns_and_expected_directions():
    regressions = pd.read_csv(ARTIFACT_DIR / "largest_regression_casebook.csv")
    improvements = pd.read_csv(ARTIFACT_DIR / "largest_improvement_casebook.csv")

    assert CASEBOOK_COLUMNS.issubset(regressions.columns)
    assert CASEBOOK_COLUMNS.issubset(improvements.columns)
    assert len(regressions) == 40
    assert len(improvements) == 40
    assert regressions["error_delta"].gt(0).all()
    assert improvements["error_delta"].lt(0).all()
    assert regressions["short_review_note"].str.len().gt(0).all()
    assert improvements["short_review_note"].str.len().gt(0).all()


def test_cutline_and_bucket_reports_identify_human_review_risk():
    cutline = pd.read_csv(ARTIFACT_DIR / "position_cutline_impact_report.csv")
    buckets = pd.read_csv(ARTIFACT_DIR / "startable_bucket_tradeoff_report.csv")

    assert not cutline.empty
    assert {"crossed_in_count", "crossed_out_count", "actual_hits_crossed_out"}.issubset(
        cutline.columns
    )
    assert cutline["crossed_out_count"].ge(0).all()
    assert buckets["gate_assessment"].isin({"PASS_OR_WATCH", "HUMAN_REVIEW_REQUIRED"}).all()
    assert buckets["gate_assessment"].eq("HUMAN_REVIEW_REQUIRED").any()


def test_guardrail_report_blocks_promotion_and_forbidden_feature_families():
    guardrail = (ARTIFACT_DIR / "guardrail_report.md").read_text(encoding="utf-8")
    merge_safety = (ARTIFACT_DIR / "merge_safety_report.md").read_text(encoding="utf-8")

    for phrase in [
        "No production formula changes",
        "No formula tuning, optimization, or formula search",
        "No app wiring",
        "No rankings, recommendations, or hidden sort changes",
        "No source-truth promotion",
        "No runtime behavior changes",
        "No routes, TPRR, YPRR, route proxies, red-zone sidecars, or ambiguous `rz_att`",
        "Null-fenced fields remain excluded",
    ]:
        assert phrase in guardrail

    assert "Expected changed paths" in merge_safety
