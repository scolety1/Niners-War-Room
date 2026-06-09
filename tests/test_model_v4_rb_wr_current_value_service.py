from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_formula_contract_service import (
    REPLACEMENT_VORP_PLAYER_ROWS,
    assert_formula_field_allowed,
)
from src.services.model_v4_rb_wr_current_value_service import (
    COMPONENT_HEADER,
    RECEIPT_HEADER,
    VALUE_HEADER,
    WARNING_HEADER,
    build_rb_wr_current_value,
    write_rb_wr_current_value_outputs,
)


def test_phase_11c_builds_review_only_rb_wr_current_value() -> None:
    result = build_rb_wr_current_value()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["market_rows_used"] == 0
    assert result.summary["projection_rows_used"] == 0
    assert result.summary["adp_rows_used"] == 0
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert len(result.value_rows) == 60
    assert {row["position"] for row in result.value_rows} == {"RB", "WR"}


def test_phase_11c_contract_explicitly_allows_vorp_anchor() -> None:
    assert_formula_field_allowed(
        module_name="rb_current_value",
        allowed_input_file=REPLACEMENT_VORP_PLAYER_ROWS,
        allowed_lane="replacement_vorp_review",
        allowed_field_or_json_path=(
            "vorp_points|positive_vorp_points|review_scoring_points|"
            "imported_rushing_first_downs|imported_receiving_first_downs|"
            "imported_first_down_points|first_down_source_status|return_source_status"
        ),
    )


def test_phase_11c_uses_components_and_receipts_without_market_inputs() -> None:
    result = build_rb_wr_current_value()
    blocked_tokens = ("adp", "projection", "projected", "mock", "big_board", "market")

    assert result.component_rows
    assert result.receipt_rows
    assert any(row["component_name"] == "vorp_anchor" for row in result.component_rows)
    assert any(
        row["feature_group"] == "replacement_vorp_review"
        for row in result.receipt_rows
    )
    for rows in (result.value_rows, result.component_rows, result.receipt_rows):
        for row in rows:
            haystack = " ".join(str(value).lower() for value in row.values())
            assert not any(token in haystack for token in blocked_tokens), row


def test_phase_11c_missing_evidence_is_blank_and_confidence_capped() -> None:
    result = build_rb_wr_current_value()
    missing_vorp_rows = [
        row for row in result.value_rows if "missing_vorp_anchor" in row["warning_flags"]
    ]

    assert missing_vorp_rows
    assert all(row["vorp_anchor_score"] == "" for row in missing_vorp_rows)
    assert all(float(row["confidence_multiplier"]) < 1.0 for row in missing_vorp_rows)


def test_phase_11c_does_not_propagate_old_review_only_vorp_context_warning() -> None:
    result = build_rb_wr_current_value()

    for row in result.value_rows:
        assert "review_only_vorp_context_excluded_from_private_value" not in str(
            row["warning_flags"]
        )
    for row in result.warning_rows:
        assert row["warning_code"] != "review_only_vorp_context_excluded_from_private_value"


def test_phase_11c_writes_sanity_fixture_warnings() -> None:
    result = build_rb_wr_current_value()
    sanity_codes = {
        row["warning_code"]
        for row in result.warning_rows
        if row["warning_type"] == "sanity_fixture"
    }

    assert "rb_wr_balance_sanity" in sanity_codes


def test_phase_11c_outputs_write_doc_and_csvs(tmp_path: Path) -> None:
    paths = write_rb_wr_current_value_outputs(
        output_root=tmp_path / "current_value",
        doc_path=tmp_path / "PHASE_11C_RB_WR_CURRENT_VALUE.md",
    )

    assert _header(paths.value_rows) == VALUE_HEADER
    assert _header(paths.component_rows) == COMPONENT_HEADER
    assert _header(paths.receipts) == RECEIPT_HEADER
    assert _header(paths.warnings) == WARNING_HEADER
    doc = paths.doc.read_text(encoding="utf-8")
    assert "review-only RB/WR current value layer" in doc
    assert "No market, projection, ADP" in doc


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
