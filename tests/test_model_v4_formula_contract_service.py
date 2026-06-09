from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.services.model_v4_formula_contract_service import (
    ADMITTED_PROSPECT_MATRIX,
    ADMITTED_PROSPECT_PRIOR_PRIVATE_INPUTS,
    DRAFT_CAPITAL_SOURCE,
    FORMULA_ALLOWED_FIELD_REGISTRY_HEADER,
    FORMULA_BLOCKED_FIELD_REGISTRY_HEADER,
    FORMULA_LOADER_GUARD_REPORT_HEADER,
    FULL_PROSPECT_MATRIX,
    NFL_MATRIX,
    REQUIRED_MODULES,
    ROOKIE_AGE_SOURCE,
    SLEEPER_PLAYER_AGE_SOURCE,
    assert_formula_field_allowed,
    build_formula_allowed_field_registry_rows,
    build_formula_blocked_field_registry_rows,
    run_formula_loader_guard_report,
    write_formula_contract_outputs,
)


def test_phase_11a_allowed_registry_covers_required_modules() -> None:
    rows = build_formula_allowed_field_registry_rows()
    modules = {str(row["module_name"]) for row in rows}

    assert set(REQUIRED_MODULES) <= modules
    assert len(rows) > len(REQUIRED_MODULES)


def test_phase_11a_private_value_registry_has_no_market_projection_or_rank_paths() -> None:
    rows = build_formula_allowed_field_registry_rows()
    blocked_tokens = (
        "adp",
        "rank",
        "projection",
        "projected",
        "mock",
        "big_board",
        "cheatsheet",
        "consensus",
        "market_context",
    )

    private_rows = [row for row in rows if row["private_value_allowed"] is True]
    assert private_rows
    for row in private_rows:
        haystack = " ".join(
            str(row[key]).lower()
            for key in ("allowed_input_file", "allowed_lane", "allowed_field_or_json_path")
        )
        assert not any(token in haystack for token in blocked_tokens), row


def test_phase_11a_current_prospect_private_inputs_use_admitted_matrix_and_sidecars_only() -> None:
    rows = build_formula_allowed_field_registry_rows()
    prospect_prior_rows = [
        row
        for row in rows
        if row["module_name"] == "prospect_prior"
        and row["private_value_allowed"] is True
    ]

    assert prospect_prior_rows
    assert {
        str(row["allowed_input_file"]) for row in prospect_prior_rows
    } == ADMITTED_PROSPECT_PRIOR_PRIVATE_INPUTS
    assert FULL_PROSPECT_MATRIX not in {
        str(row["allowed_input_file"]) for row in rows if row["private_value_allowed"] is True
    }


def test_phase_11a_blocks_generic_json_slurping_and_bad_private_fields() -> None:
    with pytest.raises(ValueError):
        assert_formula_field_allowed(
            module_name="rb_current_value",
            allowed_input_file=NFL_MATRIX,
            allowed_lane="factual_evidence_json",
            allowed_field_or_json_path="factual_evidence_json.*",
        )

    with pytest.raises(ValueError):
        assert_formula_field_allowed(
            module_name="prospect_prior",
            allowed_input_file=FULL_PROSPECT_MATRIX,
            allowed_lane="factual_evidence_json",
            allowed_field_or_json_path="college_production_summary",
        )

    with pytest.raises(ValueError):
        assert_formula_field_allowed(
            module_name="rookie_context_review",
            allowed_input_file=ADMITTED_PROSPECT_MATRIX,
            allowed_lane="market_context_fields_json",
            allowed_field_or_json_path="rookie_adp",
        )


def test_phase_11a_allows_explicit_admitted_private_field() -> None:
    assert_formula_field_allowed(
        module_name="rb_current_value",
        allowed_input_file=NFL_MATRIX,
        allowed_lane="factual_evidence_json",
        allowed_field_or_json_path="rotowire_player_stats",
    )


def test_phase_11a_lifecycle_allows_only_explicit_age_sidecar_fields() -> None:
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

    with pytest.raises(ValueError):
        assert_formula_field_allowed(
            module_name="lifecycle_archetype",
            allowed_input_file=SLEEPER_PLAYER_AGE_SOURCE,
            allowed_lane="sleeper_player_age_csv",
            allowed_field_or_json_path="source_row",
        )


def test_phase_11a_allows_only_explicit_rookie_age_and_draft_capital_sidecars() -> None:
    assert_formula_field_allowed(
        module_name="prospect_prior",
        allowed_input_file=ROOKIE_AGE_SOURCE,
        allowed_lane="rookie_age_intake_csv",
        allowed_field_or_json_path="age_years_decimal|age_total_months",
    )
    assert_formula_field_allowed(
        module_name="prospect_prior",
        allowed_input_file=DRAFT_CAPITAL_SOURCE,
        allowed_lane="rookie_draft_capital_csv",
        allowed_field_or_json_path="round|overall_pick|draft_day",
    )

    with pytest.raises(ValueError):
        assert_formula_field_allowed(
            module_name="prospect_prior",
            allowed_input_file=ROOKIE_AGE_SOURCE,
            allowed_lane="rookie_age_intake_csv",
            allowed_field_or_json_path="source_row",
        )

    with pytest.raises(ValueError):
        assert_formula_field_allowed(
            module_name="prospect_prior",
            allowed_input_file=DRAFT_CAPITAL_SOURCE,
            allowed_lane="rookie_draft_capital_csv",
            allowed_field_or_json_path="mock_draft_rank",
        )


def test_phase_11a_blocked_registry_covers_known_hazards() -> None:
    rows = build_formula_blocked_field_registry_rows()
    patterns = {str(row["blocked_field_or_json_path"]) for row in rows}

    assert "market_context_fields_json.*" in patterns
    assert "factual_evidence_json.*" in patterns
    assert "derived_evidence_json.*" in patterns
    assert "prospect_prior_evidence_json.*" in patterns
    assert "review_only_replacement_vorp" in patterns
    assert "combine_profile_source_limited" in patterns
    assert "source_row|row_order|list_rank" in patterns
    assert "adp|rank|ranking|projection|mock|big_board|consensus" in patterns


def test_phase_11a_loader_guard_report_passes() -> None:
    rows = run_formula_loader_guard_report()

    assert rows
    assert {str(row["status"]) for row in rows} == {"pass"}
    assert {
        "generic_private_json_slurping_blocked",
        "market_projection_rank_private_value_blocked",
        "admitted_prospect_rows_require_formula_identity",
        "workout_zero_placeholders_remain_missing",
    } <= {str(row["check_name"]) for row in rows}


def test_phase_11a_outputs_write_doc_and_csvs(tmp_path: Path) -> None:
    paths = write_formula_contract_outputs(
        output_root=tmp_path / "formula_contract",
        doc_path=tmp_path / "PHASE_11A_FORMULA_CONTRACT.md",
    )

    assert _header(paths.allowed_registry) == FORMULA_ALLOWED_FIELD_REGISTRY_HEADER
    assert _header(paths.blocked_registry) == FORMULA_BLOCKED_FIELD_REGISTRY_HEADER
    assert _header(paths.guard_report) == FORMULA_LOADER_GUARD_REPORT_HEADER
    doc = paths.doc.read_text(encoding="utf-8")
    assert "Generic JSON slurping is forbidden" in doc
    assert "No private-value formula module may consume" in doc


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
