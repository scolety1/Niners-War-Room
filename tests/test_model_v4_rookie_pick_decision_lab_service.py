from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rookie_pick_decision_lab_service import (
    COMPARE_HEADER,
    COMPONENT_HEADER,
    NINERS_PICKS,
    ROW_HEADER,
    WARNING_HEADER,
    build_rookie_pick_decision_lab,
    write_rookie_pick_decision_lab_outputs,
)


def test_pick_decision_lab_includes_all_owned_picks_review_only() -> None:
    result = build_rookie_pick_decision_lab()
    disclosure_fields = {"source_path", "source_column", "lineage_class"}
    neutral_labels = {
        "use_pick_review",
        "hold_pick_value_context",
        "manual_decision_required",
    }

    assert {row["pick_label"] for row in result.rows} == set(NINERS_PICKS)
    assert {row["review_label"] for row in result.rows} <= neutral_labels
    assert disclosure_fields <= set(ROW_HEADER)
    assert all(disclosure_fields <= set(row) for row in result.rows)
    assert {row["source_column"] for row in result.rows} == {"pick_value_review_score"}
    assert {row["allowed_use"] for row in result.rows} == {
        "review_only_rookie_pick_decision_lab_not_final_selection"
    }
    assert all("recommendation" in str(row["blocked_use"]) for row in result.rows)
    early_pick = next(row for row in result.rows if row["pick_label"] == "2026 1.03")
    assert (
        early_pick["equivalence_guardrail"]
        == "internal_model_neighbor_only_not_one_for_one_trade_equivalent"
    )
    assert "not a claim that one pick can buy" in str(
        early_pick["trade_market_reality_context"]
    )


def test_pick_decision_lab_neutral_board_blocks_comparison_labels() -> None:
    result = build_rookie_pick_decision_lab()

    blocked_labels = {
        "review_defer_context",
        "review_value_gap",
        "review_candidate_cluster",
        "review_rookie_vs_veteran",
        "review_rookie_vs_drop_player",
        "manual_only_no_exact_model_baseline",
    }

    assert not ({row["review_label"] for row in result.rows} & blocked_labels)
    assert any(row["review_label"] == "hold_pick_value_context" for row in result.rows)
    assert any(row["review_label"] == "manual_decision_required" for row in result.rows)


def test_pick_decision_lab_has_candidate_and_compare_context() -> None:
    result = build_rookie_pick_decision_lab()
    disclosure_fields = {"source_path", "source_column", "lineage_class"}
    comparator_fields = {"comparison_mode", "comparator_key", "comparator_source_status"}

    assert result.compare_rows
    assert disclosure_fields <= set(COMPARE_HEADER)
    assert comparator_fields <= set(COMPARE_HEADER)
    assert all(disclosure_fields <= set(row) for row in result.compare_rows)
    assert all(comparator_fields <= set(row) for row in result.compare_rows)
    assert all(str(row["source_path"]) for row in result.compare_rows)
    assert all(str(row["source_column"]) for row in result.compare_rows)
    assert all(str(row["lineage_class"]).startswith("review_v4_") for row in result.compare_rows)
    assert all(str(row["comparator_key"]) for row in result.compare_rows)
    assert {row["comparator_source_status"] for row in result.compare_rows} == {
        "concrete_comparator_loaded"
    }
    assert result.component_rows
    assert result.warning_rows
    assert any(row["comparison_type"] == "rookie_candidate" for row in result.compare_rows)
    assert any(row["comparison_type"] == "startup_slot_asset" for row in result.compare_rows)
    assert any(
        row["comparison_type"] == "startup_slot_asset"
        and row["trade_market_reality_context"]
        for row in result.compare_rows
    )
    assert any(row["pick_label"] == "candidate_component_receipt" for row in result.component_rows)
    assert any(row["component_name"] == "draft_capital" for row in result.component_rows)
    assert all(str(row["manual_questions"]) for row in result.rows)


def test_pick_decision_lab_comparison_modes_require_concrete_comparators() -> None:
    result = build_rookie_pick_decision_lab()
    by_mode: dict[str, list[dict[str, object]]] = {}
    for row in result.compare_rows:
        by_mode.setdefault(str(row["comparison_mode"]), []).append(row)

    assert {"future_pick_comparison", "current_player_comparison"} <= set(by_mode)
    assert "trade_down_pick_comparison" not in by_mode
    assert all(
        row["comparison_type"] == "future_pick_defer_context"
        and str(row["asset_name"]).startswith("2027 ")
        and row["source_column"] == "future_pick_value_review_score"
        for row in by_mode["future_pick_comparison"]
    )
    assert all(
        row["comparison_type"] == "startup_slot_asset"
        and str(row["asset_name"])
        and row["source_column"] == "model_score"
        for row in by_mode["current_player_comparison"]
    )


def test_pick_decision_lab_has_structured_manual_question_fields() -> None:
    result = build_rookie_pick_decision_lab()
    fields = {
        "manual_question_rookie_profile",
        "manual_question_roster_fit",
        "manual_question_pick_value",
        "manual_question_trade_defer",
        "manual_question_source_risk",
    }

    assert all(fields <= set(row) for row in result.rows)
    assert all(all(str(row[field]) for field in fields) for row in result.rows)
    assert all(str(row["manual_questions"]) for row in result.rows)


def test_pick_decision_lab_quarantines_missing_504_baseline() -> None:
    result = build_rookie_pick_decision_lab()
    pick_504 = next(row for row in result.rows if row["pick_label"] == "2026 5.04")

    assert pick_504["pick_value_score"] == ""
    assert pick_504["pick_tier"] == "manual_only_no_exact_model_baseline"
    assert pick_504["confidence_status"] == "manual_only_no_exact_model_baseline"
    assert pick_504["review_label"] == "manual_decision_required"
    assert "no exact candidate cluster" in str(pick_504["top_rookie_candidates"])
    assert "no exact candidate cluster" in str(pick_504["nearby_startup_slot_assets"])
    assert "manual_only_no_exact_candidate_fit_context" == pick_504["candidate_fit_context"]
    assert (
        "manual_only_no_exact_lower_variance_context"
        == pick_504["lower_variance_context_candidate"]
    )
    assert "No admitted exact model baseline exists" in str(
        pick_504["manual_question_pick_value"]
    )
    assert "exact trade, draft, or cut equivalence" in str(pick_504["defer_review_context"])
    assert "pick_value_baseline_missing" in str(pick_504["warning_flags"])
    assert "manual_only_no_exact_model_baseline" in str(pick_504["warning_flags"])


def test_pick_decision_lab_avoids_market_and_final_directives() -> None:
    result = build_rookie_pick_decision_lab()
    text = " ".join(" ".join(str(value) for value in row.values()) for row in result.rows).lower()

    blocked_terms = ("adp", "fantasypros", "projection", "mock draft", "consensus")
    directives = ("draft this player", "make this pick", "trade this pick")
    assert not any(term in text for term in blocked_terms)
    assert not any(term in text for term in directives)


def test_pick_decision_lab_writes_outputs(tmp_path: Path) -> None:
    paths = write_rookie_pick_decision_lab_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["rows"]) == ROW_HEADER
    assert _header(paths["component_rows"]) == COMPONENT_HEADER
    assert _header(paths["compare_rows"]) == COMPARE_HEADER
    assert _header(paths["warnings"]) == WARNING_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith("# Rookie Pick Decision Lab")


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
