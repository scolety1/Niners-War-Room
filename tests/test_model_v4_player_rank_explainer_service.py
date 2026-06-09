from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_player_rank_explainer_service import (
    COMPONENT_HEADER,
    ROW_HEADER,
    WARNING_HEADER,
    build_player_rank_explainer,
    write_player_rank_explainer_outputs,
)


def test_player_rank_explainer_covers_top_50_rookies() -> None:
    result = build_player_rank_explainer()
    rookie_rows = [
        row
        for row in result.rows
        if row["entity_type"] == "rookie_prospect" and int(str(row["rank"])) <= 50
    ]

    assert len(rookie_rows) >= 50
    assert all(str(row["short_explanation"]) for row in rookie_rows)
    assert all(str(row["manual_review_note"]) for row in rookie_rows)


def test_player_rank_explainer_default_rows_are_one_per_player_for_top_50_rookies() -> None:
    result = build_player_rank_explainer()
    top_50_rookie_names = {
        str(row["player_name"])
        for row in result.rows
        if row["entity_type"] == "rookie_prospect" and int(str(row["rank"])) <= 50
    }
    default_names = [str(row["player_name"]) for row in result.rows]

    assert top_50_rookie_names
    for name in top_50_rookie_names:
        assert default_names.count(name) == 1


def test_player_rank_explainer_preserves_collapsed_duplicate_contexts() -> None:
    result = build_player_rank_explainer()
    component_rows = [
        row
        for row in result.component_rows
        if row["entity_type"] == "alternate_context"
        and row["component_name"] == "current_player_context_preserved"
    ]

    assert component_rows
    assert any(row["player_name"] == "Jeremiyah Love" for row in component_rows)
    assert all("context" in str(row["component_weight"]) for row in component_rows)


def test_player_rank_explainer_preserves_collapsed_context_warnings() -> None:
    result = build_player_rank_explainer()
    warning_rows = [
        row
        for row in result.warning_rows
        if row["entity_type"] == "alternate_context"
    ]

    assert warning_rows
    assert any(row["player_name"] == "Jeremiyah Love" for row in warning_rows)
    assert all(
        str(row["warning_plain_english"]).startswith("Alternate current-player context:")
        for row in warning_rows
    )


def test_player_rank_explainer_is_review_only() -> None:
    result = build_player_rank_explainer()

    assert result.rows
    assert {row["allowed_use"] for row in result.rows} == {
        "review_only_rank_explainer_not_final_recommendation"
    }
    assert all("instruction" in str(row["blocked_use"]) for row in result.rows)


def test_player_rank_explainer_avoids_blocked_value_terms() -> None:
    result = build_player_rank_explainer()
    text = " ".join(" ".join(str(value) for value in row.values()) for row in result.rows)
    text = text.lower()

    blocked_terms = ("adp", "fantasypros", "projection", "mock draft", "consensus")
    assert not any(term in text for term in blocked_terms)


def test_player_rank_explainer_weird_rows_have_edge_or_source_label() -> None:
    result = build_player_rank_explainer()
    weird_rows = [
        row
        for row in result.rows
        if "Model edge" in str(row["warning_summary_plain_english"])
        or "Source warning" in str(row["warning_summary_plain_english"])
        or "day-three" in str(row["short_explanation"]).lower()
        or "No-premium" in str(row["warning_summary_plain_english"])
    ]

    assert weird_rows
    assert all(
        row["edge_or_source_label"]
        in {
            "legitimate_model_edge",
            "source_warning",
            "format_discipline_case",
            "normal_component_balance",
        }
        for row in weird_rows
    )


def test_player_rank_explainer_has_component_receipts() -> None:
    result = build_player_rank_explainer()
    explained_names = {row["player_name"] for row in result.rows[:50]}
    receipt_names = {row["player_name"] for row in result.component_rows}

    assert result.component_rows
    assert explained_names & receipt_names
    assert all(str(row["receipt_pointer"]) for row in result.component_rows[:200])


def test_player_rank_explainer_uses_plain_component_language() -> None:
    result = build_player_rank_explainer()
    text = " ".join(str(row["short_explanation"]) for row in result.rows)

    assert "confidence Cap" not in text
    assert "nFL" not in text


def test_player_rank_explainer_writes_outputs(tmp_path: Path) -> None:
    paths = write_player_rank_explainer_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["rows"]) == ROW_HEADER
    assert _header(paths["component_rows"]) == COMPONENT_HEADER
    assert _header(paths["warnings"]) == WARNING_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith("# Player Rank Explainer")


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
