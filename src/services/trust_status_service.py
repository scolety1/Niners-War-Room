from __future__ import annotations

from dataclasses import dataclass

from src.services.data_pack_health_service import DataPackHealthReport
from src.services.model_recalibration_service import (
    model_recalibration_policy,
    model_v4_rebuild_freeze_active,
)


@dataclass(frozen=True)
class TrustStatus:
    status: str
    severity: str
    title: str
    message: str
    next_action: str


def trust_status_from_health(
    health: DataPackHealthReport,
    *,
    calibration_passed: bool = False,
) -> TrustStatus:
    recalibration = model_recalibration_policy()
    if health.error_count > 0 or health.readiness == "blocked":
        return TrustStatus(
            status="blocked",
            severity="error",
            title="Blocked",
            message=(
                "This pack has a data issue that can break league-rank, roster, "
                "pick, or model safety."
            ),
            next_action="Fix Import Review errors before using any decision page.",
        )
    if health.placeholder_model_output_count > 0:
        return TrustStatus(
            status="inventory_only",
            severity="info",
            title="Inventory Only",
            message=(
                "Rosters, picks, and league-rank top-five lists can be reviewed, "
                "but keeper, drop, trade, and release recommendations are not "
                "decision-safe because the selected pack still uses placeholder "
                "model outputs."
            ),
            next_action=(
                "Collect source data, normalize veteran features, generate real "
                "model outputs, then rebuild or select the scored pack."
            ),
        )
    if recalibration.active and (model_v4_rebuild_freeze_active() or not calibration_passed):
        return TrustStatus(
            status=recalibration.status,
            severity="warning",
            title=recalibration.title,
            message=recalibration.message,
            next_action=recalibration.next_action,
        )
    if health.readiness == "review":
        return TrustStatus(
            status="review_only",
            severity="warning",
            title="Review Only",
            message=(
                "The pack loads and scored outputs exist, but at least one coverage, "
                "source, warning, or diff item needs human review."
            ),
            next_action=(
                "Use Import Review to clear the listed review items before draft "
                "decisions."
            ),
        )
    return TrustStatus(
        status="decision_ready",
        severity="success",
        title="Decision Ready",
        message=(
            "The selected pack has no blocking issues, real model outputs, and "
            "passes the current readiness and calibration contract."
        ),
        next_action=(
            "Use War Board as the main decision surface, with Team and League Intel "
            "as checks."
        ),
    )


def trust_status_row(
    health: DataPackHealthReport,
    *,
    calibration_passed: bool = False,
) -> dict[str, object]:
    trust = trust_status_from_health(health, calibration_passed=calibration_passed)
    return {
        "trust_status": trust.status,
        "title": trust.title,
        "message": trust.message,
        "next_action": trust.next_action,
    }
