from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_historical_similarity_service import (
    COMPONENT_HEADER,
    ROW_HEADER,
    WARNING_HEADER,
    build_historical_similarity_engine,
    write_historical_similarity_outputs,
)


def test_historical_similarity_is_review_only_and_same_position() -> None:
    result = build_historical_similarity_engine()

    assert result.rows
    assert {row["allowed_use"] for row in result.rows} == {
        "review_only_historical_similarity_not_formula_input"
    }
    assert all("recommendation" in str(row["blocked_use"]) for row in result.rows)
    assert result.component_rows
    assert all(
        row["position"]
        == next(
            parent["position"]
            for parent in result.rows
            if parent["player_name"] == row["player_name"]
        )
        for row in result.component_rows
    )


def test_historical_similarity_missing_outcomes_are_unknown_not_misses() -> None:
    result = build_historical_similarity_engine()
    text = " ".join(str(row["historical_outcome_summary"]) for row in result.rows)

    assert "unknown=" in text
    assert any(
        "missing_outcome_unknown_not_miss" in str(row["warning_flags"])
        for row in result.rows
    )


def test_historical_similarity_flags_immature_2025_context() -> None:
    result = build_historical_similarity_engine()

    assert any(
        "includes_2025_immature_outcome_context" in str(row["warning_flags"])
        for row in result.rows
    )


def test_historical_similarity_has_component_receipts_for_each_similarity() -> None:
    result = build_historical_similarity_engine()
    component_names = {row["component_name"] for row in result.component_rows}

    assert {"production", "draft_capital"}.issubset(component_names)
    assert all(str(row["allowed_input_file"]) for row in result.component_rows)
    assert all(str(row["historical_player"]) for row in result.component_rows)


def test_historical_similarity_rows_sort_usable_comps_by_model_score() -> None:
    result = build_historical_similarity_engine()
    rows_with_comps = [row for row in result.rows if row["similarity_score"] != ""]
    rows_without_comps = [row for row in result.rows if row["similarity_score"] == ""]
    scores = [float(row["model_score"]) for row in rows_with_comps if row["model_score"] != ""]

    assert scores == sorted(scores, reverse=True)
    if rows_without_comps:
        first_missing_index = result.rows.index(rows_without_comps[0])
        assert all(row["similarity_score"] == "" for row in result.rows[first_missing_index:])


def test_historical_similarity_avoids_blocked_private_value_terms() -> None:
    result = build_historical_similarity_engine()
    row_text = " ".join(" ".join(str(value) for value in row.values()) for row in result.rows)
    component_text = " ".join(
        " ".join(str(value) for value in row.values()) for row in result.component_rows
    )
    text = f"{row_text} {component_text}".lower()

    blocked_terms = ("adp", "fantasypros", "projection", "mock draft", "consensus")
    assert not any(term in text for term in blocked_terms)


def test_historical_similarity_writes_outputs(tmp_path: Path) -> None:
    paths = write_historical_similarity_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["rows"]) == ROW_HEADER
    assert _header(paths["component_rows"]) == COMPONENT_HEADER
    assert _header(paths["warnings"]) == WARNING_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith("# Historical Similarity")


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
