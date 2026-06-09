from __future__ import annotations

from src.services.model_audit_worklist_service import build_model_audit_worklist


def test_model_audit_worklist_prioritizes_gate_and_source_blockers() -> None:
    report = build_model_audit_worklist(
        "sample_data/2026_pre_declaration",
        veteran_model_dir="sample_data/veteran_model_v1",
    )

    assert not report.issues
    assert report.rows
    assert report.rows[0]["priority"] == "blocker"
    assert {row["area"] for row in report.rows} >= {
        "calibration_gate",
        "source_coverage",
        "ranking_outlier",
    }


def test_model_audit_worklist_summary_counts_rows_by_area() -> None:
    report = build_model_audit_worklist(
        "sample_data/2026_pre_declaration",
        veteran_model_dir="sample_data/veteran_model_v1",
    )

    summary_lookup = {row["area"]: row for row in report.summary_rows}

    assert summary_lookup["source_coverage"]["blockers"] > 0
    assert summary_lookup["ranking_outlier"]["items"] > 0
