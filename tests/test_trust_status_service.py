from __future__ import annotations

from pathlib import Path

from src.services.data_pack_health_service import DataPackHealthReport
from src.services.trust_status_service import trust_status_from_health, trust_status_row


def test_trust_status_blocks_data_errors() -> None:
    trust = trust_status_from_health(_health(readiness="blocked", error_count=1))

    assert trust.status == "blocked"
    assert trust.severity == "error"
    assert "Import Review" in trust.next_action


def test_trust_status_marks_placeholders_as_inventory_only() -> None:
    trust = trust_status_from_health(
        _health(readiness="review", placeholder_model_output_count=3)
    )

    assert trust.status == "inventory_only"
    assert trust.severity == "info"
    assert "placeholder model outputs" in trust.message
    assert "Collect source data" in trust.next_action


def test_trust_status_marks_review_without_placeholders() -> None:
    trust = trust_status_from_health(_health(readiness="review", warning_count=1))

    assert trust.status == "model_recalibration"
    assert trust.severity == "warning"


def test_trust_status_marks_scored_pack_as_recalibration_review_only() -> None:
    health = _health(readiness="ready")
    trust = trust_status_from_health(health)

    assert trust.status == "model_recalibration"
    assert trust.severity == "warning"
    assert "review-only" in trust.message
    assert trust_status_row(health)["trust_status"] == "model_recalibration"


def test_trust_status_stays_review_only_during_model_v4_rebuild_freeze() -> None:
    health = _health(readiness="ready")
    trust = trust_status_from_health(health, calibration_passed=True)

    assert trust.status == "model_recalibration"
    assert trust.severity == "warning"
    assert "review-only" in trust.message
    assert (
        trust_status_row(health, calibration_passed=True)["trust_status"]
        == "model_recalibration"
    )


def _health(
    *,
    readiness: str,
    error_count: int = 0,
    warning_count: int = 0,
    placeholder_model_output_count: int = 0,
) -> DataPackHealthReport:
    return DataPackHealthReport(
        data_pack_path=Path("sample_data/2026_pre_declaration"),
        data_pack_name="sample",
        snapshot_date="2026-pre-draft",
        readiness=readiness,
        error_count=error_count,
        warning_count=warning_count,
        roster_count=10,
        pick_count=5,
        league_rank_coverage_pct=100,
        placeholder_model_output_count=placeholder_model_output_count,
        coverage_rows=(),
        checks=(),
        issues=(),
    )
