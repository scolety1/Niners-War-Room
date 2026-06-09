from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_roster_opportunity_cost_service import (
    COMPONENT_HEADER,
    ROW_HEADER,
    WARNING_HEADER,
    build_roster_opportunity_cost,
    write_roster_opportunity_cost_outputs,
)


def test_roster_opportunity_cost_includes_every_niners_roster_player() -> None:
    result = build_roster_opportunity_cost()
    disclosure_fields = {"source_path", "source_column", "lineage_class"}

    assert len(result.rows) == 24
    assert disclosure_fields <= set(ROW_HEADER)
    assert all(disclosure_fields <= set(row) for row in result.rows)
    assert all(str(row["source_path"]) for row in result.rows)
    assert all(str(row["source_column"]) for row in result.rows)
    assert all(str(row["lineage_class"]).startswith("review_v4_") for row in result.rows)
    assert {row["allowed_use"] for row in result.rows} == {
        "review_only_roster_opportunity_cost_not_cut_keep_recommendation"
    }
    assert all("recommendation" in str(row["blocked_use"]) for row in result.rows)
    assert {row["player_name"] for row in result.rows} >= {"Chase Brown", "Kaleb Johnson"}


def test_roster_opportunity_cost_has_pick_equivalents_and_review_labels() -> None:
    result = build_roster_opportunity_cost()

    labels = {row["opportunity_cost_label"] for row in result.rows}
    assert "expensive_to_cut" in labels
    assert "trade_context_before_cut_review" in labels
    assert all(str(row["rookie_pick_equivalent"]) for row in result.rows)
    assert not any("2027" in str(row["rookie_pick_equivalent"]) for row in result.rows)
    below_floor_rows = [
        row
        for row in result.rows
        if str(row["rookie_pick_equivalent"]).startswith("below admitted owned pick baseline floor")
    ]
    assert below_floor_rows
    assert not any(
        "manual_only_no_exact_model_baseline" in str(row["rookie_pick_equivalent"])
        for row in below_floor_rows
    )
    assert all(
        row["pick_baseline_status"] == "manual_only_no_exact_model_baseline"
        for row in below_floor_rows
    )
    assert all(
        row["pick_equivalent_confidence"] == "no_exact_model_equivalent"
        for row in below_floor_rows
    )
    assert all(
        "manual_only_no_exact_model_baseline" in str(row["pick_equivalent_warning"])
        for row in below_floor_rows
    )
    directive_phrases = ("you should cut", "cut this player", "drop this player")
    notes = " ".join(str(row["opportunity_cost_note"]).lower() for row in result.rows)
    assert not any(phrase in notes for phrase in directive_phrases)


def test_roster_opportunity_cost_components_and_warnings_are_review_only() -> None:
    result = build_roster_opportunity_cost()

    assert result.component_rows
    assert result.warning_rows
    assert all(row["allowed_use"].startswith("review_only") for row in result.component_rows)
    assert all(row["allowed_use"].startswith("review_only") for row in result.warning_rows)
    assert any(
        row["warning_code"] == "review_only_no_cut_keep_recommendation"
        for row in result.warning_rows
    )


def test_roster_opportunity_cost_does_not_use_market_terms() -> None:
    result = build_roster_opportunity_cost()
    combined = " ".join(
        str(row.get("rookie_pick_equivalent", ""))
        + " "
        + str(row.get("opportunity_cost_note", ""))
        + " "
        + str(row.get("replacement_options_nearby", ""))
        for row in result.rows
    ).lower()

    blocked_terms = ("adp", "fantasypros", "projection", "mock draft", "consensus")
    assert not any(term in combined for term in blocked_terms)


def test_roster_opportunity_cost_pick_equivalent_fields_are_split() -> None:
    result = build_roster_opportunity_cost()

    required_fields = {
        "rookie_pick_equivalent",
        "pick_baseline_status",
        "pick_equivalent_confidence",
        "pick_equivalent_warning",
    }
    assert all(required_fields <= set(row) for row in result.rows)
    assert any(
        row["pick_baseline_status"] == "matched_owned_pick_baseline"
        for row in result.rows
    )
    assert any(
        row["pick_baseline_status"] == "manual_only_no_exact_model_baseline"
        for row in result.rows
    )


def test_roster_opportunity_cost_writes_outputs(tmp_path: Path) -> None:
    paths = write_roster_opportunity_cost_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["rows"]) == ROW_HEADER
    assert _header(paths["component_rows"]) == COMPONENT_HEADER
    assert _header(paths["warnings"]) == WARNING_HEADER
    assert (
        paths["doc"].read_text(encoding="utf-8").startswith("# Roster Cut Opportunity-Cost Engine")
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
