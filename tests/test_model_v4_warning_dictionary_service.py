from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_warning_dictionary_service import (
    DICTIONARY_HEADER,
    DISPLAY_MAP_HEADER,
    build_warning_dictionary,
    write_warning_dictionary_outputs,
)


def test_warning_dictionary_builds_plain_english_rows() -> None:
    result = build_warning_dictionary()

    assert result.dictionary_rows
    assert result.display_map_rows
    assert {row["allowed_use"] for row in result.dictionary_rows} == {
        "review_only_warning_dictionary_not_final_recommendation"
    }
    assert all(str(row["plain_english_meaning"]) for row in result.dictionary_rows)
    assert all(str(row["human_review_action"]) for row in result.dictionary_rows)


def test_warning_display_groups_map_to_raw_codes() -> None:
    result = build_warning_dictionary()

    groups = {row["warning_group"] for row in result.dictionary_rows}
    mapped_groups = {row["warning_group"] for row in result.display_map_rows}
    assert groups == mapped_groups
    assert all(str(row["raw_warning_codes"]) for row in result.display_map_rows)


def test_warning_dictionary_preserves_raw_codes_and_required_groups() -> None:
    result = build_warning_dictionary()
    codes = {row["raw_warning_code"] for row in result.dictionary_rows}
    groups = {row["warning_group"] for row in result.dictionary_rows}

    assert "manual_only_no_exact_model_baseline" in codes
    assert "review_only_no_cut_keep_recommendation" in codes
    assert "Manual review required" in groups
    assert "Review-only guardrail" in groups


def test_warning_dictionary_links_codes_to_modules_and_drilldowns() -> None:
    result = build_warning_dictionary()

    assert all(str(row["primary_module"]) for row in result.dictionary_rows)
    assert all(str(row["primary_export"]) for row in result.dictionary_rows)
    assert all(str(row["receipt_or_drilldown_to_open"]) for row in result.dictionary_rows)
    assert all(str(row["example_review_question"]) for row in result.dictionary_rows)
    assert any(row["primary_module"] == "multiple_modules" for row in result.dictionary_rows)
    assert any(
        row["primary_module"] == "source_risk_heatmap" for row in result.dictionary_rows
    )
    assert any(
        row["primary_module"] == "roster_opportunity_cost"
        for row in result.dictionary_rows
    )


def test_warning_dictionary_has_no_final_recommendation_language() -> None:
    result = build_warning_dictionary()
    combined = " ".join(
        " ".join(str(value).lower() for value in row.values())
        for row in result.dictionary_rows
    )

    blocked_phrases = (
        "you should cut",
        "cut this player",
        "make this trade",
        "draft this player",
    )
    assert not any(phrase in combined for phrase in blocked_phrases)


def test_warning_dictionary_avoids_blocked_market_artifacts() -> None:
    result = build_warning_dictionary()
    combined = " ".join(
        " ".join(str(value).lower() for value in row.values())
        for row in result.dictionary_rows
    )

    blocked_terms = ("adp", "fantasypros", "mock_draft", "consensus")
    assert not any(term in combined for term in blocked_terms)


def test_warning_dictionary_writes_outputs(tmp_path: Path) -> None:
    paths = write_warning_dictionary_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["dictionary"]) == DICTIONARY_HEADER
    assert _header(paths["display_map"]) == DISPLAY_MAP_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith(
        "# Model v4.6 Warning Code Dictionary"
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
