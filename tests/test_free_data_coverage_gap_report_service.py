from __future__ import annotations

from pathlib import Path

import src.services.free_data_coverage_gap_report_service as gap_service
from src.services.free_data_coverage_gap_report_service import (
    build_free_data_coverage_gap_report,
    write_free_data_coverage_gap_report,
)
from src.services.free_data_import_coverage_service import FreeDataImportCoverageReport
from src.services.source_coverage_audit_service import SourceCoverageAuditReport


def test_gap_report_separates_gap_classes(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gap_service, "build_source_coverage_audit", _source_report_fixture)
    monkeypatch.setattr(
        gap_service,
        "build_free_data_import_coverage_matrix",
        _free_data_report_fixture,
    )

    report = build_free_data_coverage_gap_report(tmp_path)
    categories = {
        (row["category"], row["bucket"]): row
        for row in report.category_rows
    }
    unavailable = {row["feature_bucket"]: row for row in report.unavailable_free_source_rows}

    assert categories[("critical_data_available", "production")]["players"] == 1
    assert categories[("critical_data_missing", "role/usage")]["players"] == 1
    assert categories[("optional_data_missing", "projections")]["players"] == 1
    assert unavailable["projection"]["paid_or_manual_candidate"].startswith("paid/free")
    assert report.review_only_status is True


def test_missing_critical_fields_show_imputation_and_block(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gap_service, "build_source_coverage_audit", _source_report_fixture)
    monkeypatch.setattr(
        gap_service,
        "build_free_data_import_coverage_matrix",
        _free_data_report_fixture,
    )

    report = build_free_data_coverage_gap_report(tmp_path)
    row = report.missing_critical_field_rows[0]

    assert row["affected_feature"] == "role_security"
    assert row["affected_player"] == "Receiver One"
    assert row["model_currently_imputes"] is True
    assert row["confidence_impact"] == 6.0
    assert row["blocks_decision_ready"] is True
    assert row["free_source_support"] == "partial_free_import"


def test_gap_report_recommendations_keep_rankings_review_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gap_service, "build_source_coverage_audit", _source_report_fixture)
    monkeypatch.setattr(
        gap_service,
        "build_free_data_import_coverage_matrix",
        _free_data_report_fixture,
    )

    report = build_free_data_coverage_gap_report(tmp_path)
    recommendations = {
        row["recommendation_type"]: row["recommendation"]
        for row in report.recommendation_rows
    }

    assert "Free data is enough" in recommendations["what_free_data_is_enough_for"]
    assert "cannot fully solve" in recommendations["what_free_data_cannot_solve"]
    assert "Keep rankings review-only" in recommendations["decision_ready_effect"]


def test_gap_report_export_writes_expected_files(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gap_service, "build_source_coverage_audit", _source_report_fixture)
    monkeypatch.setattr(
        gap_service,
        "build_free_data_import_coverage_matrix",
        _free_data_report_fixture,
    )
    report = build_free_data_coverage_gap_report(tmp_path)

    paths = write_free_data_coverage_gap_report(tmp_path / "export", report)

    assert set(paths) == {
        "category_report",
        "missing_critical_fields",
        "unavailable_free_sources",
        "recommendations",
        "source_coverage_summary",
        "free_data_summary",
    }
    assert paths["missing_critical_fields"].exists()


def _source_report_fixture(*args, **kwargs) -> SourceCoverageAuditReport:
    _ = args, kwargs
    bucket_rows = [
        _bucket_row(
            player="Receiver One",
            bucket="production",
            coverage_class="critical",
            coverage_pct=100,
            confidence_penalty=0,
            real_features="target_earning",
            missing_features="",
            imputed_features="",
            decision_effect="no_gap",
        ),
        _bucket_row(
            player="Receiver One",
            bucket="role/usage",
            coverage_class="critical",
            coverage_pct=50,
            confidence_penalty=6,
            real_features="",
            missing_features="",
            imputed_features="role_security",
            decision_effect="blocks_decision_trust",
        ),
        _bucket_row(
            player="Runner One",
            bucket="projections",
            coverage_class="review",
            coverage_pct=0,
            confidence_penalty=10,
            real_features="",
            missing_features="lve_projection_value",
            imputed_features="",
            decision_effect="confidence_penalty_review_needed",
        ),
    ]
    return SourceCoverageAuditReport(
        player_rows=[],
        bucket_rows=bucket_rows,
        feature_rows=[],
        summary_rows=[{"summary_type": "bucket", "name": "production"}],
        missing_critical_rows=[bucket_rows[1]],
        review_gap_rows=[bucket_rows[2]],
        accepted_review_gap_rows=[],
        invalid_gap_acceptance_rows=[],
        gap_acceptance_summary_rows=[],
        players=["Receiver One", "Runner One"],
        buckets=["production", "role/usage", "projections"],
        statuses=[],
        issues=[],
        source_root="fixture",
    )


def _free_data_report_fixture(*args, **kwargs) -> FreeDataImportCoverageReport:
    _ = args, kwargs
    return FreeDataImportCoverageReport(
        coverage_rows=(
            _free_row("production", "direct_free_import", "ready", "Direct stats."),
            _free_row("role/usage", "partial_free_import", "review", "Route proxy limits."),
            _free_row("projection", "external_csv_required", "external_required", "Needs CSV."),
        ),
        field_rows=(),
        adapter_rows=(),
        summary_rows=[{"support_status": "direct_free_import"}],
        issues=(),
        raw_import_status="ready",
        raw_import_root="fixture",
    )


def _bucket_row(
    *,
    player: str,
    bucket: str,
    coverage_class: str,
    coverage_pct: float,
    confidence_penalty: float,
    real_features: str,
    missing_features: str,
    imputed_features: str,
    decision_effect: str,
) -> dict[str, object]:
    return {
        "player_id": player.lower().replace(" ", "_"),
        "player": player,
        "position": "WR",
        "team": "Niners",
        "bucket": bucket,
        "coverage_class": coverage_class,
        "critical_bucket": coverage_class == "critical",
        "review_bucket": coverage_class == "review",
        "decision_blocking_bucket": coverage_class == "critical",
        "bucket_status": "ready" if coverage_pct >= 90 else "review" if coverage_pct else "missing",
        "coverage_pct": coverage_pct,
        "confidence_penalty": confidence_penalty,
        "decision_effect": decision_effect,
        "gap_acceptance_status": "not_allowed" if coverage_class == "critical" else "review_needed",
        "gap_acceptance_reason": "",
        "confidence_penalty_retained": "",
        "gap_review_owner": "",
        "gap_reviewed_at": "",
        "next_action": "fixture next action",
        "expected_features": real_features or missing_features or imputed_features,
        "real_features": real_features,
        "imputed_features": imputed_features,
        "missing_features": missing_features,
        "real_feature_count": 1 if real_features else 0,
        "imputed_feature_count": 1 if imputed_features else 0,
        "missing_feature_count": 1 if missing_features else 0,
    }


def _free_row(
    bucket: str,
    support_status: str,
    validation_status: str,
    limitations: str,
) -> dict[str, object]:
    return {
        "feature_bucket": bucket,
        "support_status": support_status,
        "support_level": "direct" if support_status == "direct_free_import" else "partial",
        "validation_status": validation_status,
        "required_fields": "field_a|field_b",
        "limitations": limitations,
        "model_usage": "fixture usage",
        "next_action": "fixture action",
    }
