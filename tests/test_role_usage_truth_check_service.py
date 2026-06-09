from __future__ import annotations

import csv
from pathlib import Path

from src.services.role_usage_truth_check_service import (
    build_role_usage_truth_check_report,
    write_role_usage_truth_check_report,
)


def test_role_usage_truth_check_buckets_proxy_and_flags_rank_driver(
    tmp_path: Path,
) -> None:
    receipt_path = tmp_path / "receipts.csv"
    contribution_path = tmp_path / "contributions.csv"
    _write_csv(
        receipt_path,
        (
            "player_id",
            "player_name",
            "position",
            "team",
            "feature_name",
            "source_status",
            "source_key",
            "raw_value",
            "normalized_score",
            "warning_reason",
            "imputed_flag",
            "model_usage",
        ),
        [
            {
                "player_id": "wr1",
                "player_name": "Wide Receiver",
                "position": "WR",
                "team": "SF",
                "feature_name": "route_role",
                "source_status": "manual_review",
                "source_key": "nflverse_participation_player_weekly",
                "raw_value": "50",
                "normalized_score": "50",
                "warning_reason": "missing_participation_proxy",
                "imputed_flag": "false",
                "model_usage": "private_stat_feature",
            }
        ],
    )
    _write_csv(
        contribution_path,
        (
            "player_id",
            "feature_name",
            "component_contribution",
        ),
        [
            {
                "player_id": "wr1",
                "feature_name": "route_role",
                "component_contribution": "12",
            },
            {
                "player_id": "wr1",
                "feature_name": "weighted_recent_lve_ppg_score",
                "component_contribution": "10",
            },
        ],
    )

    report = build_role_usage_truth_check_report(receipt_path, contribution_path)

    assert report.audit_rows[0]["input_truth_bucket"] == "proxy_usage"
    assert report.audit_rows[0]["rank_driver_flag"] == "role_driven_by_proxy_or_imputation"
    assert any(
        row["area"] == "role_usage_truth" and row["status"] == "review"
        for row in report.gap_report_rows
    )


def test_role_usage_truth_check_keeps_derived_usage_unflagged(tmp_path: Path) -> None:
    receipt_path = tmp_path / "receipts.csv"
    contribution_path = tmp_path / "contributions.csv"
    _write_csv(
        receipt_path,
        (
            "player_id",
            "player_name",
            "position",
            "team",
            "feature_name",
            "source_status",
            "source_key",
            "raw_value",
            "normalized_score",
            "warning_reason",
            "imputed_flag",
            "model_usage",
        ),
        [
            {
                "player_id": "rb1",
                "player_name": "Running Back",
                "position": "RB",
                "team": "DET",
                "feature_name": "workload_earning",
                "source_status": "derived_real_data",
                "source_key": "nflverse_player_stats_weekly",
                "raw_value": "87",
                "normalized_score": "87",
                "warning_reason": "missing_participation_proxy",
                "imputed_flag": "false",
                "model_usage": "private_stat_feature",
            }
        ],
    )
    _write_csv(
        contribution_path,
        ("player_id", "feature_name", "component_contribution"),
        [
            {
                "player_id": "rb1",
                "feature_name": "workload_earning",
                "component_contribution": "16",
            }
        ],
    )

    report = build_role_usage_truth_check_report(receipt_path, contribution_path)

    assert report.audit_rows[0]["input_truth_bucket"] == "derived_usage"
    assert report.audit_rows[0]["rank_driver_flag"] == ""


def test_role_usage_truth_check_writes_report_files(tmp_path: Path) -> None:
    receipt_path = tmp_path / "receipts.csv"
    contribution_path = tmp_path / "contributions.csv"
    _write_csv(
        receipt_path,
        (
            "player_id",
            "player_name",
            "position",
            "team",
            "feature_name",
            "source_status",
            "source_key",
            "raw_value",
            "normalized_score",
            "warning_reason",
            "imputed_flag",
            "model_usage",
        ),
        [
            {
                "player_id": "te1",
                "player_name": "Tight End",
                "position": "TE",
                "team": "LV",
                "feature_name": "target_earning_stability",
                "source_status": "neutral_imputation",
                "source_key": "nflverse_participation_player_weekly",
                "raw_value": "",
                "normalized_score": "50",
                "warning_reason": "missing_role_usage_features",
                "imputed_flag": "true",
                "model_usage": "private_stat_feature",
            }
        ],
    )
    _write_csv(
        contribution_path,
        ("player_id", "feature_name", "component_contribution"),
        [
            {
                "player_id": "te1",
                "feature_name": "target_earning_stability",
                "component_contribution": "8",
            }
        ],
    )
    report = build_role_usage_truth_check_report(receipt_path, contribution_path)

    paths = write_role_usage_truth_check_report(tmp_path / "out", report)

    assert paths["audit"].exists()
    assert paths["summary"].exists()
    assert paths["gap_report"].exists()


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
