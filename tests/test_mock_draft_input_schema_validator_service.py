from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_input_schema_validator_service import (
    validate_mock_draft_input_schemas,
    validation_rows_as_dicts,
)

FIXTURE_ROOT = Path("tests/fixtures/mock_draft/input_schema_validator")


def _valid_files() -> dict[str, Path]:
    return {
        "post_drop_rosters": FIXTURE_ROOT / "post_drop_rosters_valid.csv",
        "draft_order": FIXTURE_ROOT / "draft_order_valid.csv",
        "team_managers": FIXTURE_ROOT / "team_managers_valid.csv",
        "dropped_veterans": FIXTURE_ROOT / "dropped_veterans_valid.csv",
        "available_pool": FIXTURE_ROOT / "available_pool_valid.csv",
        "market_timing": FIXTURE_ROOT / "market_timing_valid.csv",
        "nwr_veteran_guidance": FIXTURE_ROOT / "nwr_veteran_guidance_valid.csv",
    }


def test_fake_valid_schemas_pass_without_real_market_data() -> None:
    result = validate_mock_draft_input_schemas(_valid_files())

    assert result.review_only is True
    assert result.phase1_can_proceed is True
    assert result.full_simulation_blocked is False
    assert result.summary["green_rows"] == 7
    assert result.summary["red_rows"] == 0
    assert "No numeric NWR score is invented" in result.summary["nwr_score_policy"]


def test_missing_required_inputs_block_full_simulation_not_phase1() -> None:
    files = _valid_files()
    files["post_drop_rosters"] = None

    result = validate_mock_draft_input_schemas(files)
    rows = {row.group_name: row for row in result.rows}

    assert result.phase1_can_proceed is True
    assert result.full_simulation_blocked is True
    assert rows["post_drop_rosters"].status == "RED"
    assert rows["post_drop_rosters"].required_for_full_simulation is True


def test_missing_optional_adp_is_yellow_not_red() -> None:
    files = _valid_files()
    files["market_timing"] = None

    result = validate_mock_draft_input_schemas(files)
    rows = {row.group_name: row for row in result.rows}

    assert result.full_simulation_blocked is False
    assert rows["market_timing"].status == "YELLOW"
    assert rows["market_timing"].required_for_full_simulation is False


def test_disallowed_market_contamination_fields_are_flagged() -> None:
    files = _valid_files()
    files["market_timing"] = FIXTURE_ROOT / "market_timing_invalid_contamination.csv"

    result = validate_mock_draft_input_schemas(files)
    rows = {row.group_name: row for row in result.rows}

    assert rows["market_timing"].status == "RED"
    assert rows["market_timing"].required_for_full_simulation is False
    assert "hidden_sort_key" in rows["market_timing"].disallowed_columns
    assert "nwr_quality_score" in rows["market_timing"].disallowed_columns
    assert result.full_simulation_blocked is False
    assert "behavior-only" in result.summary["market_policy"]


def test_validation_rows_as_dicts_are_review_outputs() -> None:
    result = validate_mock_draft_input_schemas(_valid_files())
    rows = validation_rows_as_dicts(result)

    assert rows
    assert rows[0]["group_name"]
    assert "disallowed_columns" in rows[0]
