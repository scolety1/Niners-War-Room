from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_model_edge_queue_service import (
    COMPONENT_HEADER,
    ROW_HEADER,
    WARNING_HEADER,
    build_model_edge_queue,
    write_model_edge_queue_outputs,
)


def test_model_edge_queue_is_review_only_and_has_rows() -> None:
    result = build_model_edge_queue()

    assert result.rows
    assert {row["allowed_use"] for row in result.rows} == {
        "review_only_model_edge_queue_not_final_recommendation"
    }


def test_model_edge_queue_has_supported_or_source_warned_edges() -> None:
    result = build_model_edge_queue()

    assert all(
        str(row["evidence_supporting_edge"]) or str(row["source_risk"])
        for row in result.rows
    )
    assert all(str(row["human_review_question"]) for row in result.rows)


def test_model_edge_queue_classifies_expected_edge_types() -> None:
    result = build_model_edge_queue()
    classifications = {row["edge_classification"] for row in result.rows}
    weirdness = {row["weirdness_type"] for row in result.rows}

    assert "legitimate_model_edge" in classifications
    assert "source_shape_warning" in classifications
    assert "te_ranked_high_no_premium" in weirdness
    assert "qb_ranked_high_1qb" in weirdness


def test_model_edge_queue_avoids_blocked_terms() -> None:
    result = build_model_edge_queue()
    text = " ".join(" ".join(str(value) for value in row.values()) for row in result.rows)
    text += " ".join(
        " ".join(str(value) for value in row.values()) for row in result.component_rows
    )
    text = text.lower()

    blocked_terms = ("adp", "fantasypros", "projection", "mock draft", "consensus")
    assert not any(term in text for term in blocked_terms)


def test_model_edge_queue_writes_outputs(tmp_path: Path) -> None:
    paths = write_model_edge_queue_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["rows"]) == ROW_HEADER
    assert _header(paths["component_rows"]) == COMPONENT_HEADER
    assert _header(paths["warnings"]) == WARNING_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith("# Model Edge Queue")


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
