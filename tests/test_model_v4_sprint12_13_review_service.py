from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_sprint12_13_review_service import (
    DYNASTY_REVIEW_HEADER,
    PICK_BASELINE_HEADER,
    PROSPECT_REVIEW_HEADER,
    build_sprint12_13_review_outputs,
    write_sprint12_13_review_outputs,
)

ADMITTED_PROSPECT_MATRIX = (
    "local_exports/model_v4/evidence_matrices/latest/"
    "admitted_prospect_current_feature_matrix.csv"
)
ROOKIE_AGE_SOURCE = "local_exports/model_v4/prospect_age/latest/player_age_2026.csv"
DRAFT_CAPITAL_SOURCE = (
    "local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv"
)
ROOKIE_FORMULA_REPAIR_DOC = (
    "docs/model_v4/MODEL_V4_3_3_ROOKIE_FORMULA_BALANCE_REPAIR.md"
)


def test_sprint12_13_builds_review_only_outputs() -> None:
    result = build_sprint12_13_review_outputs()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["market_rows_used_for_private_value"] == 0
    assert result.summary["projection_rows_used_for_private_value"] == 0
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert len(result.prospect_rows) == 211
    assert len(result.pick_rows) == 80
    assert len(result.dynasty_rows) == 371


def test_sprint13_uses_only_admitted_prospect_rows_for_private_value() -> None:
    result = build_sprint12_13_review_outputs()

    assert {row["allowed_use"] for row in result.prospect_rows} == {
        "review_only_prospect_private_value_not_final_rookie_board"
    }
    assert {row["entity_type"] for row in result.prospect_component_rows} == {
        "current_prospect"
    }
    assert {row["allowed_input_file"] for row in result.prospect_component_rows} == {
        ADMITTED_PROSPECT_MATRIX,
        ROOKIE_AGE_SOURCE,
        DRAFT_CAPITAL_SOURCE,
        ROOKIE_FORMULA_REPAIR_DOC,
    }
    assert not any(
        "market_context_fields_json" in str(row)
        for row in result.prospect_component_rows
    )
    age_components = [
        row
        for row in result.prospect_component_rows
        if row["component_name"] == "age_lifecycle"
    ]
    assert age_components
    assert {row["allowed_input_file"] for row in age_components} == {ROOKIE_AGE_SOURCE}
    draft_components = [
        row
        for row in result.prospect_component_rows
        if row["component_name"] == "draft_capital"
    ]
    assert draft_components
    assert {row["allowed_input_file"] for row in draft_components} == {
        DRAFT_CAPITAL_SOURCE
    }


def test_sprint13_rookie_formula_balance_guardrails_are_visible() -> None:
    result = build_sprint12_13_review_outputs()
    by_name = {row["prospect_name"]: row for row in result.prospect_rows}

    assert by_name["Carnell Tate"]["draft_capital_score"] != ""
    assert "draft_capital_anchor_warning" in by_name["Carnell Tate"][
        "rookie_formula_balance_label"
    ]
    assert by_name["Skyler Bell"]["draft_capital_score"] != ""
    assert "model_edge_weirdness" in by_name["Skyler Bell"][
        "rookie_formula_balance_label"
    ]
    assert "no_premium_te_cap_warning" in by_name["Eli Stowers"][
        "rookie_formula_balance_label"
    ]
    assert "no_premium_te_cap_warning" in by_name["Max Klare"][
        "rookie_formula_balance_label"
    ]
    assert by_name["KC Concepcion"]["draft_capital_score"] != ""
    assert by_name["Daniel Sobkowicz"]["draft_capital_score"] == ""


def test_sprint12_pick_baselines_are_review_only_heuristics() -> None:
    result = build_sprint12_13_review_outputs()
    by_key = {row["pick_asset_key"]: row for row in result.pick_rows}

    assert by_key["pick:2026:1.01"]["tier_label"] == "early_first"
    assert by_key["pick:2027:1.01"]["tier_label"] == "early_first"
    assert float(by_key["pick:2027:1.01"]["pick_value_review_score"]) >= float(
        by_key["pick:2026:1.01"]["pick_value_review_score"]
    )
    assert {row["allowed_use"] for row in result.pick_rows} == {
        "review_only_pick_value_baseline_not_trade_recommendation"
    }
    assert {row["warning_flags"] for row in result.pick_rows} == {
        "heuristic_pick_curve_requires_audit"
    }


def test_sprint12_unified_asset_table_keeps_layers_separable() -> None:
    result = build_sprint12_13_review_outputs()
    asset_types = {row["asset_type"] for row in result.dynasty_rows}
    by_name = {row["asset_name"]: row for row in result.dynasty_rows}

    assert asset_types == {"current_player", "current_prospect", "rookie_pick"}
    assert by_name["Christian McCaffrey"]["value_source_layer"] == (
        "phase_11g_current_player_value_checkpoint"
    )
    assert by_name["2026 1.01"]["value_source_layer"] == (
        "sprint_12_review_only_pick_baseline"
    )
    assert all(
        row["allowed_use"] == "review_only_unified_asset_value_not_final_ranking"
        for row in result.dynasty_rows
    )


def test_sprint12_13_sanity_warnings_are_visible() -> None:
    result = build_sprint12_13_review_outputs()
    warning_codes = {row["warning_code"] for row in result.dynasty_warning_rows}

    assert "review_only_no_final_recommendations" in warning_codes
    assert "required_asset_present" in warning_codes
    assert "heuristic_pick_curve_requires_audit" in warning_codes


def test_sprint12_13_writes_outputs_and_docs(tmp_path: Path) -> None:
    paths = write_sprint12_13_review_outputs(output_root=tmp_path)

    assert _header(paths.prospect_review_rows) == PROSPECT_REVIEW_HEADER
    assert _header(paths.pick_baselines) == PICK_BASELINE_HEADER
    assert _header(paths.dynasty_review_rows) == DYNASTY_REVIEW_HEADER
    assert "review-only asset table" in paths.sprint12_doc.read_text(
        encoding="utf-8"
    )
    assert "admitted prospect evidence" in paths.sprint13_doc.read_text(
        encoding="utf-8"
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
