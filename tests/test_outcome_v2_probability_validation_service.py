from __future__ import annotations

import csv
from pathlib import Path

from src.services.outcome_v2_probability_validation_service import (
    build_validation_feature_frame,
    field_feasibility_rows,
    validate_probabilities,
    write_validation_artifacts,
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_outcome_v2_validation_blocks_all_five_year_fields() -> None:
    frame = build_validation_feature_frame()
    rows = field_feasibility_rows(frame)
    five_year_rows = [row for row in rows if row["horizon"] == "within_5y"]

    assert five_year_rows
    assert {row["feasibility_status"] for row in five_year_rows} == {
        "BLOCKED_INSUFFICIENT_COMPLETE_LABELS",
    }


def test_outcome_v2_validation_passes_only_held_out_brier_winners() -> None:
    results, calibration_rows, bucket_rows = validate_probabilities()
    passed = [
        row for row in results if row["validation_status"] == "PASS_APP_DISPLAY_VALIDATION"
    ]
    blocked_weak = [
        row for row in results if row["validation_status"] == "BLOCKED_VALIDATION_WEAK"
    ]

    assert passed
    assert len(passed) == 22
    assert {row["horizon"] for row in passed} <= {"this_year", "next_year"}
    assert {row["field_id"] for row in blocked_weak} == {
        "RB_T6_NEXT_YEAR",
        "RB_T12_NEXT_YEAR",
    }
    assert all(float(row["model_brier"]) <= float(row["baseline_brier"]) for row in passed)
    assert calibration_rows
    assert bucket_rows


def test_outcome_v2_validation_uses_no_blocked_inputs() -> None:
    results, _, _ = validate_probabilities()

    assert {row["blocked_inputs_used"] for row in results} == {"false"}


def test_outcome_v2_validation_writer_creates_review_only_artifacts(tmp_path: Path) -> None:
    result = write_validation_artifacts(tmp_path)

    assert result.passed_fields == 22
    assert result.blocked_fields == 14
    for path in (
        result.validation_results_path,
        result.calibration_path,
        result.model_buckets_path,
        result.manifest_path,
    ):
        assert path.exists()

    manifest = _rows(result.manifest_path)
    assert {row["display_only"] for row in manifest} == {"true"}
    assert {row["model_use_allowed"] for row in manifest} == {"false"}
    assert {row["training_allowed"] for row in manifest} == {"false"}
    assert {row["blocked_inputs_used"] for row in manifest} == {"false"}
