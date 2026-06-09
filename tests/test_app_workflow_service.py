from __future__ import annotations

from pathlib import Path

from src.services.app_workflow_service import (
    build_app_workflow_report,
    workflow_summary_row,
)
from src.services.data_pack_admission_service import DataPackAdmissionReport
from src.services.data_pack_health_service import DataPackHealthReport
from src.services.final_calibration_gate_service import (
    CalibrationGateCheck,
    FinalCalibrationGateReport,
)


def test_workflow_safe_inventory_mode_hides_decision_surfaces() -> None:
    report = build_app_workflow_report(
        _health(readiness="ready"),
        _admission("ready"),
        _calibration("blocked", passed=False),
    )
    summary = workflow_summary_row(report)

    assert report.mode == "Safe Inventory Mode"
    assert summary["mode"] == "Safe Inventory Mode"
    assert any(row["area"] == "Rosters" and row["status"] == "usable" for row in report.safe_rows)
    assert any(row["area"] == "War Board rankings" for row in report.blocked_rows)
    assert any(row["bucket"] == "Data Truth" for row in report.next_update_rows)
    assert next(row for row in report.page_rows if row["page"] == "Trade Lab")[
        "current_behavior"
    ] == "Trade inputs only."


def test_workflow_data_blocked_mode_blocks_everything() -> None:
    report = build_app_workflow_report(
        _health(readiness="blocked", error_count=1),
        _admission("blocked"),
        _calibration("blocked", passed=False),
    )

    assert report.mode == "Data Blocked"
    assert report.safe_rows[0]["status"] == "blocked"
    assert report.blocked_rows == [
        {
            "area": "All model pages",
            "why_blocked": "Import data has blocking errors.",
            "what_to_do": "Fix Import & Refresh validation errors.",
        }
    ]


def test_workflow_decision_mode_explains_final_use() -> None:
    report = build_app_workflow_report(
        _health(readiness="ready"),
        _admission("ready"),
        _calibration("ready", passed=True),
    )

    assert report.mode == "Decision Mode"
    assert not report.blocked_rows
    assert any(row["area"] == "Stats Value" for row in report.safe_rows)
    assert next(row for row in report.page_rows if row["page"] == "War Board")[
        "current_behavior"
    ] == "Primary decision board."


def test_workflow_pre_declaration_ready_does_not_wait_for_released_veterans() -> None:
    report = build_app_workflow_report(
        _health(readiness="ready"),
        _admission("ready"),
        _calibration(
            "review",
            passed=False,
            pre_declaration_passed=True,
            draft_badge="Needs Released Veterans",
        ),
    )

    assert report.mode == "Roster Declaration Review Mode"
    assert "before released veterans arrive" in report.headline
    assert any(
        row["area"] == "Rosters" and row["use"] == "Keep/drop/shop review."
        for row in report.safe_rows
    )
    assert any(
        row["area"] == "Stats Value"
        and row["use"] == "Roster-declaration review score."
        for row in report.safe_rows
    )
    assert not any(
        row["area"] == "My Team keep/drop/shop calls"
        for row in report.blocked_rows
    )
    assert any(
        row["area"] == "Final War Board rankings"
        and row["why_blocked"] == "Needs Released Veterans"
        for row in report.blocked_rows
    )
    assert next(row for row in report.page_rows if row["page"] == "War Board")[
        "current_behavior"
    ] == "Roster declaration review only."
    assert next(row for row in report.page_rows if row["page"] == "My Team")[
        "current_behavior"
    ] == "Keep/drop/shop review."


def _health(
    *,
    readiness: str,
    error_count: int = 0,
    placeholder_model_output_count: int = 0,
) -> DataPackHealthReport:
    return DataPackHealthReport(
        data_pack_path=Path("sample_data/2026_pre_declaration"),
        data_pack_name="sample",
        snapshot_date="2026-pre-draft",
        readiness=readiness,
        error_count=error_count,
        warning_count=0,
        roster_count=24,
        pick_count=20,
        league_rank_coverage_pct=100,
        placeholder_model_output_count=placeholder_model_output_count,
        coverage_rows=(),
        checks=(),
        issues=(),
    )


def _admission(decision: str) -> DataPackAdmissionReport:
    return DataPackAdmissionReport(
        candidate_path=Path("sample_data/2026_pre_declaration"),
        baseline_path=None,
        decision=decision,
        health_readiness="ready" if decision == "ready" else decision,
        diff_change_count=0,
        reasons=(),
    )


def _calibration(
    status: str,
    *,
    passed: bool,
    pre_declaration_passed: bool | None = None,
    draft_badge: str | None = None,
) -> FinalCalibrationGateReport:
    return FinalCalibrationGateReport(
        status=status,
        badge="Model Calibration Passed" if passed else "Model Calibration Blocked",
        decision_badge="Decision Ready" if passed else "Needs Data",
        passed=passed,
        blocked_count=0 if passed else 1,
        review_count=0,
        ready_count=6 if passed else 5,
        checks=(
            CalibrationGateCheck(
                gate="fixture",
                status="ready" if passed else "blocked",
                severity="info" if passed else "error",
                detail="fixture",
                next_action="fixture",
            ),
        ),
        pre_declaration_passed=(
            passed if pre_declaration_passed is None else pre_declaration_passed
        ),
        pre_declaration_badge=(
            "Roster Decisions Ready"
            if (passed if pre_declaration_passed is None else pre_declaration_passed)
            else "Roster Decisions Need Data"
        ),
        draft_passed=passed,
        draft_badge=draft_badge or ("Draft Ready" if passed else "Draft Needs Data"),
    )
