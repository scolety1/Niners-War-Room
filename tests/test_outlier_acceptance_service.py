from __future__ import annotations

import csv
from pathlib import Path

from src.services.outlier_acceptance_service import (
    apply_outlier_acceptances,
    build_outlier_acceptance_report,
)


def test_outlier_acceptance_requires_audited_reason_reviewer_and_timestamp(
    tmp_path: Path,
) -> None:
    path = tmp_path / "model_outlier_acceptances.csv"
    _write_rows(
        path,
        [
            {
                "player_id": "p1",
                "player_name": "Player One",
                "outlier_type": "ranking_gap",
                "component": "",
                "source_feature": "",
                "review_status": "accepted",
                "accepted_reason": "Feature receipts support the unusual rank.",
                "reviewed_by": "lsmith",
                "reviewed_at": "2026-05-10T12:00:00-06:00",
            },
            {
                "player_id": "p2",
                "player_name": "Player Two",
                "outlier_type": "ranking_gap",
                "component": "",
                "source_feature": "",
                "review_status": "accepted",
                "accepted_reason": "",
                "reviewed_by": "",
                "reviewed_at": "not-a-date",
            },
        ],
    )

    report = build_outlier_acceptance_report(path)

    assert ("p1", "ranking_gap", "", "") in report.accepted_keys
    assert ("p2", "ranking_gap", "", "") not in report.accepted_keys
    assert len(report.invalid_rows) == 1
    assert "accepted_reason is required" in str(report.invalid_rows[0]["validation_errors"])
    assert "reviewed_at must be ISO 8601" in str(report.invalid_rows[0]["validation_errors"])


def test_apply_outlier_acceptances_marks_scores_as_accepted_without_changing_values(
    tmp_path: Path,
) -> None:
    path = tmp_path / "model_outlier_acceptances.csv"
    _write_rows(
        path,
        [
            {
                "player_id": "p1",
                "player_name": "Player One",
                "outlier_type": "ranking_gap",
                "component": "private_lve_value",
                "source_feature": "role_security",
                "review_status": "accepted",
                "accepted_reason": "Role data was checked manually.",
                "reviewed_by": "lsmith",
                "reviewed_at": "2026-05-10",
            }
        ],
    )
    outliers = [
        {
            "player_id": "p1",
            "player": "Player One",
            "outlier_type": "ranking_gap",
            "component": "private_lve_value",
            "source_feature": "role_security",
            "private_score": 88.0,
            "review_status": "ranking_review",
            "next_action": "Review it.",
        }
    ]

    rows, report = apply_outlier_acceptances(outliers, path)

    assert report.invalid_rows == []
    assert rows[0]["acceptance_status"] == "accepted"
    assert rows[0]["review_status"] == "accepted"
    assert rows[0]["private_score"] == 88.0
    assert rows[0]["accepted_reason"] == "Role data was checked manually."


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
