from __future__ import annotations

from pathlib import Path

from src.services.final_calibration_gate_service import FinalCalibrationGateReport
from src.services.ranking_readiness_service import ranking_readiness_from_calibration


def test_ranking_readiness_blocks_rankings_until_calibration_passes() -> None:
    report = FinalCalibrationGateReport(
        status="blocked",
        badge="Model Calibration Blocked",
        decision_badge="Needs Data",
        passed=False,
        blocked_count=2,
        review_count=0,
        ready_count=4,
        checks=(),
    )

    readiness = ranking_readiness_from_calibration(report)

    assert readiness.review_only is True
    assert readiness.calibration_passed is False
    assert "sanity and audit gates pass" in readiness.message
    assert "money decisions" in readiness.next_action


def test_ranking_readiness_remains_review_only_during_model_v4_freeze() -> None:
    report = FinalCalibrationGateReport(
        status="ready",
        badge="Model Calibration Passed",
        decision_badge="Decision Ready",
        passed=True,
        blocked_count=0,
        review_count=0,
        ready_count=6,
        checks=(),
    )

    readiness = ranking_readiness_from_calibration(report)

    assert readiness.review_only is True
    assert readiness.calibration_passed is True
    assert readiness.calibration_status == "ready"
    assert "review-only" in readiness.message


def test_ranking_readiness_review_gate_uses_review_next_action() -> None:
    report = FinalCalibrationGateReport(
        status="review",
        badge="Model Calibration Needs Review",
        decision_badge="Calibration Needs Review",
        passed=False,
        blocked_count=0,
        review_count=2,
        ready_count=4,
        checks=(),
    )

    readiness = ranking_readiness_from_calibration(report)

    assert readiness.review_only is True
    assert "Review the remaining warning gates" in readiness.next_action
    assert "Clear blocked" not in readiness.next_action


def test_visible_pages_do_not_use_raw_recalibration_flag_for_rankings() -> None:
    app_pages = Path(__file__).resolve().parents[1] / "app" / "pages"

    offenders = [
        page.name
        for page in app_pages.glob("*.py")
        if "model_recalibration_policy().active" in page.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_review_only_decision_pages_remain_inspectable() -> None:
    app_pages = Path(__file__).resolve().parents[1] / "app" / "pages"
    inspectable_pages = [
        "02_team.py",
        "03_war_board.py",
        "04_trade_central.py",
        "06_league_intel.py",
    ]

    for page_name in inspectable_pages:
        page_text = (app_pages / page_name).read_text(encoding="utf-8")
        assert "hidden while calibration" not in page_text
        assert "st.stop()" not in page_text
