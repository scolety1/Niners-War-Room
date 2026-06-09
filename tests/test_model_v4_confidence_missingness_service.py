from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.services.model_v4_confidence_missingness_service import (
    CONFIDENCE_RECEIPT_HEADER,
    CONFIDENCE_REVIEW_HEADER,
    CONFIDENCE_WARNING_HEADER,
    MissingConfidenceCriticalFieldError,
    build_confidence_missingness_layer,
    validate_confidence_critical_fields,
    write_confidence_missingness_outputs,
)
from src.services.model_v4_formula_contract_service import (
    ADMITTED_PROSPECT_MATRIX,
    HISTORICAL_BACKTEST_MATRIX,
    NFL_MATRIX,
    SOURCE_COVERAGE_MATRIX,
    WARNING_MATRIX,
    assert_formula_field_allowed,
)


def test_phase_11f_builds_review_only_confidence_layer() -> None:
    result = build_confidence_missingness_layer()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["market_rows_used"] == 0
    assert result.summary["projection_rows_used"] == 0
    assert result.summary["generic_json_rows_used"] == 0
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert result.summary["nfl_player_rows"] == 80
    assert result.summary["current_prospect_rows"] == 211
    assert result.summary["historical_rookie_rows"] == 395
    assert len(result.review_rows) == 686


def test_phase_11f_contract_allows_only_confidence_metadata() -> None:
    for matrix in (NFL_MATRIX, ADMITTED_PROSPECT_MATRIX, HISTORICAL_BACKTEST_MATRIX):
        for lane in ("source_status_json", "receipt_pointers_json", "warning_flags"):
            assert_formula_field_allowed(
                module_name="confidence_missingness",
                allowed_input_file=matrix,
                allowed_lane=lane,
                allowed_field_or_json_path=lane,
                private_value=False,
            )
    assert_formula_field_allowed(
        module_name="confidence_missingness",
        allowed_input_file=SOURCE_COVERAGE_MATRIX,
        allowed_lane="source_coverage",
        allowed_field_or_json_path="feature_group|present|source_status|warnings",
        private_value=False,
    )
    assert_formula_field_allowed(
        module_name="confidence_missingness",
        allowed_input_file=WARNING_MATRIX,
        allowed_lane="warnings",
        allowed_field_or_json_path="warning_code|severity|warning_detail",
        private_value=False,
    )


def test_phase_11f_current_prospects_use_admitted_matrix_only() -> None:
    result = build_confidence_missingness_layer()
    prospect_rows = [
        row for row in result.review_rows if row["entity_type"] == "current_prospect"
    ]

    assert len(prospect_rows) == 211
    assert {
        row["source_matrix"] for row in prospect_rows
    } == {"admitted_prospect_current_feature_matrix"}


def test_phase_11f_formula_loader_fails_closed_when_critical_fields_absent() -> None:
    with pytest.raises(MissingConfidenceCriticalFieldError):
        validate_confidence_critical_fields(
            {
                "source_status_json": "{}",
                "receipt_pointers_json": "{}",
            },
            source_matrix="unit_test_matrix",
        )


def test_phase_11f_missing_and_source_limited_evidence_create_caps_only() -> None:
    result = build_confidence_missingness_layer()
    source_limited = [
        row for row in result.review_rows if int(row["source_limited_count"] or 0) > 0
    ]
    missing_first_down = [
        row
        for row in result.review_rows
        if "missing_or_review_first_down_evidence" in row["cap_reasons"]
    ]

    assert source_limited
    assert missing_first_down
    assert all(float(row["confidence_cap"]) <= 0.92 for row in source_limited)
    assert all(row["allowed_use"] == "review_only_confidence_cap" for row in result.review_rows)
    assert all("return_scoring" not in row["coverage_missing_groups"] for row in result.review_rows)


def test_phase_11f_receipts_stay_on_allowed_inputs() -> None:
    result = build_confidence_missingness_layer()
    allowed_inputs = {
        NFL_MATRIX,
        ADMITTED_PROSPECT_MATRIX,
        HISTORICAL_BACKTEST_MATRIX,
        SOURCE_COVERAGE_MATRIX,
        WARNING_MATRIX,
    }
    allowed_lanes = {
        "source_status_json",
        "receipt_pointers_json",
        "warning_flags",
        "source_coverage",
        "warnings",
    }

    assert result.receipt_rows
    for row in result.receipt_rows:
        assert row["allowed_input_file"] in allowed_inputs
        assert row["allowed_lane"] in allowed_lanes
        assert "context_fields_json" not in row["allowed_lane"]
        assert "market_context_fields_json" not in row["allowed_lane"]


def test_phase_11f_writes_sanity_fixture_warnings() -> None:
    result = build_confidence_missingness_layer()
    sanity_codes = {
        row["warning_code"]
        for row in result.warning_rows
        if row["warning_type"] == "sanity_fixture"
    }

    assert {
        "confidence_missingness_fail_closed_sanity",
        "missing_data_not_zero_or_average_sanity",
        "stale_season_direct_check_unavailable",
        "lifecycle_output_not_allowed_for_confidence_missingness",
    } <= sanity_codes


def test_phase_11f_outputs_write_doc_and_csvs(tmp_path: Path) -> None:
    paths = write_confidence_missingness_outputs(
        output_root=tmp_path / "current_value",
        doc_path=tmp_path / "PHASE_11F_CONFIDENCE_MISSINGNESS_LAYER.md",
    )

    assert _header(paths.review_rows) == CONFIDENCE_REVIEW_HEADER
    assert _header(paths.receipts) == CONFIDENCE_RECEIPT_HEADER
    assert _header(paths.warnings) == CONFIDENCE_WARNING_HEADER
    doc = paths.doc.read_text(encoding="utf-8")
    assert "review-only confidence caps" in doc
    assert "Missing evidence creates caps and warnings" in doc


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
