from __future__ import annotations

from dataclasses import dataclass

MODEL_RECALIBRATION_ACTIVE = True
MODEL_RECALIBRATION_STATUS = "model_recalibration"
MODEL_V4_REBUILD_FREEZE_ACTIVE = True


@dataclass(frozen=True)
class ModelRecalibrationPolicy:
    active: bool
    status: str
    title: str
    message: str
    next_action: str
    review_label: str


def model_recalibration_policy() -> ModelRecalibrationPolicy:
    return ModelRecalibrationPolicy(
        active=MODEL_RECALIBRATION_ACTIVE,
        status=MODEL_RECALIBRATION_STATUS,
        title="Model Under Recalibration",
        message=(
            "Current rankings are review-only while the scoring model is audited. "
            "Roster, league-rank, pick, and import data remain usable for inspection; "
            "official released veterans are a draft-room input, not a prerequisite "
            "for pre-declaration drop/shop review."
        ),
        next_action=(
            "Use rankings only as audit prompts until ranking receipts, sanity fixtures, "
            "and calibration gates pass."
        ),
        review_label="rankings_review_only",
    )


def rankings_are_review_only(*, calibration_passed: bool = False) -> bool:
    if MODEL_V4_REBUILD_FREEZE_ACTIVE:
        return True
    if calibration_passed:
        return False
    return model_recalibration_policy().active


def model_v4_rebuild_freeze_active() -> bool:
    return MODEL_V4_REBUILD_FREEZE_ACTIVE
