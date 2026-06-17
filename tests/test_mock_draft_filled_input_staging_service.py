from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_filled_input_staging_service import (
    REQUIRED_FILENAMES,
    STAGING_ROOT,
    staging_checks_as_dicts,
    validate_filled_input_staging,
)


def test_missing_future_staging_files_are_yellow_not_failure() -> None:
    result = validate_filled_input_staging(staging_root=Path("does/not/exist"))

    assert result.review_only is True
    assert result.full_simulation_ready is False
    assert result.summary["yellow"] == 6
    assert result.summary["red"] == 0
    assert set(result.summary["required_files"]) == set(REQUIRED_FILENAMES)
    assert result.staging_root == Path("does/not/exist")
    assert STAGING_ROOT == Path("local_exports/mock_draft/user_supplied_inputs_20260617")


def test_valid_fake_staged_headers_pass_for_required_files(tmp_path) -> None:
    (tmp_path / "post_drop_rosters.csv").write_text(
        "team_name,manager,roster_slot,player_name,position,nfl_team,input_status\n"
        "A,M,Starter,P,WR,SF,review\n",
        encoding="utf-8",
    )
    (tmp_path / "post_drop_draft_order.csv").write_text(
        "season,overall_pick,round,round_pick,pick_label,current_owner,original_owner,"
        "manager,is_niners_pick,source_status\n"
        "2026,1,1,1,1.01,A,A,M,false,review\n",
        encoding="utf-8",
    )
    (tmp_path / "team_managers.csv").write_text(
        "team_name,manager,team_key\nA,M,a\n", encoding="utf-8"
    )

    result = validate_filled_input_staging(staging_root=tmp_path)

    required = [check for check in result.checks if check.required_for_full_simulation]
    assert all(check.status == "GREEN" for check in required)
    assert result.full_simulation_ready is True


def test_invalid_staged_header_is_red() -> None:
    result = validate_filled_input_staging(
        files_by_name={
            "post_drop_rosters.csv": Path(
                "tests/fixtures/mock_draft/input_schema_validator/"
                "available_pool_valid.csv"
            )
        }
    )
    rosters = next(
        check
        for check in result.checks
        if check.file_name == "post_drop_rosters.csv"
    )
    assert rosters.status == "RED"
    assert "team_name" in rosters.missing_columns


def test_staging_checks_as_dicts_are_serializable() -> None:
    result = validate_filled_input_staging(staging_root=Path("missing"))
    rows = staging_checks_as_dicts(result)
    assert rows[0]["file_name"]
    assert "missing_columns" in rows[0]
