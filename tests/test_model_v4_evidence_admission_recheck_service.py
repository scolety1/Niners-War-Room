from __future__ import annotations

from pathlib import Path

from src.services.model_v4_evidence_admission_recheck_service import (
    run_evidence_admission_recheck,
    write_phase_10n_doc,
)


def test_phase_10n_recheck_passes_latest_admitted_surfaces() -> None:
    result = run_evidence_admission_recheck()

    assert result.summary["status"] == "pass"
    assert result.summary["failed_check_count"] == 0
    assert result.summary["issue_count"] == 0
    assert result.summary["admitted_current_prospect_identity_rows"] >= 200
    assert result.summary["admitted_prospect_feature_rows"] == result.summary[
        "admitted_current_prospect_identity_rows"
    ]
    assert result.summary["review_current_prospect_identity_rows"] > 0
    assert result.summary["formula_scores_calculated"] == "False"
    assert result.summary["final_rankings_calculated"] == "False"


def test_phase_10n_check_names_cover_audit_requirements() -> None:
    result = run_evidence_admission_recheck()
    check_names = {check.check_name for check in result.checks}

    assert {
        "historical_post_draft_college_evidence",
        "duplicate_entity_rows",
        "private_lane_market_leakage",
        "fake_zero_missing_evidence",
        "workout_zero_placeholder_values",
        "review_only_vorp_namespace",
        "source_limited_combine_private_value",
        "return_direct_scoring_only",
        "first_down_admitted_views_matched_only",
        "return_admitted_view_matched_only",
        "source_labels_and_receipts_present",
        "review_only_prospects_quarantined",
        "no_formula_scoring_or_rank_generation",
    }.issubset(check_names)


def test_phase_10n_doc_records_pass_status(tmp_path: Path) -> None:
    result = run_evidence_admission_recheck()
    doc_path = write_phase_10n_doc(result, doc_path=tmp_path / "phase10n.md")

    text = doc_path.read_text(encoding="utf-8")
    assert "Status: pass" in text
    assert "No formula scores or final rankings were generated." in text
    assert "Review-only current prospects remain excluded" in text
