from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.services.final_calibration_gate_service import (
    FinalCalibrationGateReport,
    build_final_calibration_gate,
)
from src.services.model_recalibration_service import (
    model_recalibration_policy,
    rankings_are_review_only,
)


@dataclass(frozen=True)
class RankingReadinessReport:
    review_only: bool
    calibration_passed: bool
    calibration_status: str
    calibration_badge: str
    blocked_count: int
    review_count: int
    ready_count: int
    message: str
    next_action: str
    calibration_report: FinalCalibrationGateReport


def build_ranking_readiness(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
    identity_source_root: str | Path | None = None,
) -> RankingReadinessReport:
    calibration = build_final_calibration_gate(
        data_pack_path,
        veteran_model_dir=veteran_model_dir,
        identity_source_root=identity_source_root,
    )
    return ranking_readiness_from_calibration(calibration)


def ranking_readiness_from_calibration(
    calibration: FinalCalibrationGateReport,
) -> RankingReadinessReport:
    policy = model_recalibration_policy()
    review_only = rankings_are_review_only(calibration_passed=calibration.passed)
    if review_only:
        message = (
            f"{policy.title}: rankings are review-only until the final sanity and "
            f"audit gates pass. Current gate: {calibration.badge.lower()}."
        )
        if calibration.blocked_count > 0:
            next_action = (
                "Clear blocked source coverage, identity, sanity fixture, outlier, "
                "rookie replay, and UI smoke checks before using rankings for money decisions."
            )
        elif calibration.review_count > 0:
            next_action = (
                "Review the remaining warning gates and player receipts before using "
                "rankings for money decisions."
            )
        else:
            next_action = (
                "Keep rankings review-only until the recalibration policy is explicitly "
                "turned off after audit signoff."
            )
    else:
        message = "Ranking calibration gate passed; rankings may use decision-ready labels."
        next_action = "Keep source snapshots frozen unless you intentionally refresh."
    return RankingReadinessReport(
        review_only=review_only,
        calibration_passed=calibration.passed,
        calibration_status=calibration.status,
        calibration_badge=calibration.badge,
        blocked_count=calibration.blocked_count,
        review_count=calibration.review_count,
        ready_count=calibration.ready_count,
        message=message,
        next_action=next_action,
        calibration_report=calibration,
    )
