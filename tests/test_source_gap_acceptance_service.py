from __future__ import annotations

import csv
from pathlib import Path

from src.services.source_gap_acceptance_service import (
    build_source_gap_acceptance_report,
    source_gap_acceptance_lookup,
)


def test_source_gap_acceptance_requires_penalty_retained_reason_and_reviewer(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source_coverage_gap_acceptances.csv"
    _write_rows(
        path,
        [
            {
                "player_id": "p1",
                "bucket": "injury",
                "gap_type": "missing_injury_source",
                "review_status": "accepted",
                "accepted_reason": "No reliable injury export is available yet.",
                "confidence_penalty_retained": "true",
                "reviewed_by": "lsmith",
                "reviewed_at": "2026-05-10T13:00:00-06:00",
            },
            {
                "player_id": "p2",
                "bucket": "production",
                "gap_type": "",
                "review_status": "accepted",
                "accepted_reason": "",
                "confidence_penalty_retained": "false",
                "reviewed_by": "",
                "reviewed_at": "bad-date",
            },
        ],
    )

    report = build_source_gap_acceptance_report(path)

    assert ("p1", "injury") in report.accepted_keys
    assert ("p2", "production") not in report.accepted_keys
    assert len(report.invalid_rows) == 1
    errors = str(report.invalid_rows[0]["validation_errors"])
    assert "bucket must be projection, injury, or market/liquidity" in errors
    assert "confidence_penalty_retained must be true" in errors
    assert "accepted_reason is required" in errors


def test_source_gap_acceptance_supports_bucket_level_optional_acceptance(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source_coverage_gap_acceptances.csv"
    _write_rows(
        path,
        [
            {
                "player_id": "",
                "bucket": "market/liquidity",
                "gap_type": "missing_market_source",
                "review_status": "accepted",
                "accepted_reason": "Market source is intentionally excluded for now.",
                "confidence_penalty_retained": "true",
                "reviewed_by": "lsmith",
                "reviewed_at": "2026-05-10",
            }
        ],
    )

    lookup, report = source_gap_acceptance_lookup(path)

    assert report.invalid_rows == []
    assert "market" in report.accepted_global_bucket_keys
    assert lookup[("", "market")]["accepted_reason"] == (
        "Market source is intentionally excluded for now."
    )


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
