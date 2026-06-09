from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_formula_contract_service import (
    NFL_MATRIX,
    ROOKIE_AGE_SOURCE,
    SLEEPER_PLAYER_AGE_SOURCE,
    WARNING_MATRIX,
    assert_formula_field_allowed,
)
from src.services.model_v4_lifecycle_archetype_service import (
    COMPONENT_HEADER,
    RECEIPT_HEADER,
    REVIEW_HEADER,
    WARNING_HEADER,
    build_lifecycle_archetype_layer,
    write_lifecycle_archetype_outputs,
)


def test_phase_11e_builds_review_only_lifecycle_layer() -> None:
    result = build_lifecycle_archetype_layer()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["market_rows_used"] == 0
    assert result.summary["projection_rows_used"] == 0
    assert result.summary["age_rows_used"] > 0
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert len(result.review_rows) == 80
    assert {row["position"] for row in result.review_rows} == {"QB", "RB", "WR", "TE"}


def test_phase_11e_contract_allows_only_explicit_lifecycle_fields() -> None:
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=NFL_MATRIX,
        allowed_lane="row_metadata",
        allowed_field_or_json_path="position|lifecycle_expected",
    )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=NFL_MATRIX,
        allowed_lane="factual_evidence_json",
        allowed_field_or_json_path="rotowire_player_stats",
    )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=NFL_MATRIX,
        allowed_lane="derived_evidence_json",
        allowed_field_or_json_path="rotowire_role_usage",
    )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=ROOKIE_AGE_SOURCE,
        allowed_lane="player_age_intake_csv",
        allowed_field_or_json_path="age_years_decimal|age_total_months",
    )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=SLEEPER_PLAYER_AGE_SOURCE,
        allowed_lane="sleeper_player_age_csv",
        allowed_field_or_json_path="age_years_decimal|age_total_months",
    )
    assert_formula_field_allowed(
        module_name="lifecycle_archetype",
        allowed_input_file=WARNING_MATRIX,
        allowed_lane="warnings",
        allowed_field_or_json_path="warning_code|severity|warning_detail",
        private_value=False,
    )


def test_phase_11e_emits_required_position_archetypes() -> None:
    result = build_lifecycle_archetype_layer()
    archetypes = {row["role_archetype"] for row in result.review_rows}

    assert "rb_short_window_three_down_role_asset" in archetypes
    assert "wr_target_earner" in archetypes
    assert "wr_speed_dependent_field_stretcher" in archetypes
    assert "wr_possession_chain_mover" in archetypes
    assert {"qb_rushing_dependent", "qb_hybrid_rushing_passing_engine"} & archetypes
    assert "te_route_target_engine" in archetypes


def test_phase_11e_uses_admitted_age_sidecar_without_fabricating_gaps() -> None:
    result = build_lifecycle_archetype_layer()
    warning_codes = {row["warning_code"] for row in result.warning_rows}
    lamar = next(row for row in result.review_rows if row["player_name"] == "Lamar Jackson")
    bijan = next(row for row in result.review_rows if row["player_name"] == "Bijan Robinson")
    cmc = next(row for row in result.review_rows if row["player_name"] == "Christian McCaffrey")

    assert result.summary["age_rows_used"] > 0
    assert lamar["age_evidence_status"] == "matched_player_age_evidence"
    assert lamar["age_years_decimal"] != ""
    assert lamar["role_archetype"] == "qb_rushing_dependent"
    assert "qb_rushing_age_caution_active" in lamar["warning_flags"]
    assert bijan["age_evidence_status"] == "matched_player_age_evidence"
    assert "rb_age_cliff_guardrail_unavailable" not in bijan["warning_flags"]
    assert "rb_age_cliff_guardrail_active" in cmc["warning_flags"]
    assert "lifecycle_age_sidecar_sanity" in warning_codes


def test_phase_11e_components_and_receipts_stay_on_allowed_inputs() -> None:
    result = build_lifecycle_archetype_layer()
    allowed_pairs = {
        (NFL_MATRIX, "row_metadata", "position|lifecycle_expected"),
        (NFL_MATRIX, "factual_evidence_json", "rotowire_player_stats"),
        (NFL_MATRIX, "derived_evidence_json", "rotowire_role_usage"),
        (ROOKIE_AGE_SOURCE, "player_age_intake_csv", "age_years_decimal|age_total_months"),
        (
            SLEEPER_PLAYER_AGE_SOURCE,
            "sleeper_player_age_csv",
            "age_years_decimal|age_total_months",
        ),
    }
    blocked_tokens = ("adp", "projection", "projected", "mock", "big_board", "market")

    assert result.component_rows
    assert result.receipt_rows
    for row in result.component_rows:
        assert (
            row["allowed_input_file"],
            row["allowed_lane"],
            row["allowed_field_or_json_path"],
        ) in allowed_pairs
    for row in result.receipt_rows:
        assert (
            row["allowed_input_file"],
            row["allowed_lane"],
            row["allowed_field_or_json_path"],
        ) in allowed_pairs
    for rows in (result.review_rows, result.component_rows, result.receipt_rows):
        for row in rows:
            haystack = " ".join(str(value).lower() for value in row.values())
            assert not any(token in haystack for token in blocked_tokens), row


def test_phase_11e_writes_sanity_fixture_warnings() -> None:
    result = build_lifecycle_archetype_layer()
    sanity_codes = {
        row["warning_code"]
        for row in result.warning_rows
        if row["warning_type"] == "sanity_fixture"
    }

    assert {
        "lifecycle_age_sidecar_sanity",
        "rb_short_window_sanity",
        "wr_role_shape_sanity",
        "qb_rushing_age_caution_sanity",
        "te_route_requirement_sanity",
    } <= sanity_codes


def test_phase_11e_outputs_write_doc_and_csvs(tmp_path: Path) -> None:
    paths = write_lifecycle_archetype_outputs(
        output_root=tmp_path / "current_value",
        doc_path=tmp_path / "PHASE_11E_LIFECYCLE_ARCHETYPE_LAYER.md",
    )

    assert _header(paths.review_rows) == REVIEW_HEADER
    assert _header(paths.component_rows) == COMPONENT_HEADER
    assert _header(paths.receipts) == RECEIPT_HEADER
    assert _header(paths.warnings) == WARNING_HEADER
    doc = paths.doc.read_text(encoding="utf-8")
    assert "review-only lifecycle" in doc
    assert "admitted player-age sidecar" in doc


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
