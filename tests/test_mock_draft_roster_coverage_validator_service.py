from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_roster_coverage_validator_service import (
    roster_coverage_issues_as_dicts,
    roster_team_summaries_as_dicts,
    validate_roster_coverage,
)

FIXTURE_DIR = Path("tests/fixtures/mock_draft/roster_coverage_validator")


def test_valid_fake_roster_coverage_is_green_for_ten_teams() -> None:
    result = validate_roster_coverage(
        FIXTURE_DIR / "post_drop_rosters_10_teams_valid.csv",
        team_managers_path=FIXTURE_DIR / "team_managers_10_teams_valid.csv",
    )

    assert result.review_only is True
    assert result.full_simulation_ready is True
    assert result.summary["team_count"] == 10
    assert result.summary["roster_rows"] == 10
    assert result.issues == ()


def test_incomplete_roster_coverage_is_yellow_not_sim_ready() -> None:
    result = validate_roster_coverage(
        FIXTURE_DIR / "post_drop_rosters_review_flags.csv"
    )

    assert result.full_simulation_ready is False
    assert result.summary["yellow_issues"] >= 1
    assert any(issue.issue_type == "team_count" for issue in result.issues)


def test_duplicate_and_missing_identity_flags_are_preserved() -> None:
    result = validate_roster_coverage(
        FIXTURE_DIR / "post_drop_rosters_review_flags.csv"
    )

    issues = {issue.issue_type: issue for issue in result.issues}
    assert issues["duplicate_player_rows"].review_flag == (
        "duplicate_player_review_required"
    )
    assert issues["missing_player_identity"].review_flag == (
        "player_identity_review_required"
    )
    assert issues["missing_lineage"].review_flag == "input_lineage_review_required"


def test_team_manager_linkage_flags_missing_roster_team(tmp_path) -> None:
    roster_file = tmp_path / "rosters.csv"
    roster_file.write_text(
        "team_name,manager,roster_slot,player_name,position,nfl_team,input_status\n"
        "Team 01,Manager 01,Starter,Player 01,QB,SF,review\n",
        encoding="utf-8",
    )
    manager_file = tmp_path / "team_managers.csv"
    manager_file.write_text(
        "team_name,manager,team_key\n"
        "Team 01,Manager 01,team_01\n"
        "Team 02,Manager 02,team_02\n",
        encoding="utf-8",
    )

    result = validate_roster_coverage(roster_file, team_managers_path=manager_file)

    assert any(issue.issue_type == "teams_missing_rosters" for issue in result.issues)
    assert result.full_simulation_ready is False


def test_roster_coverage_serializers_are_report_ready() -> None:
    result = validate_roster_coverage(
        FIXTURE_DIR / "post_drop_rosters_review_flags.csv"
    )

    issue_rows = roster_coverage_issues_as_dicts(result)
    team_rows = roster_team_summaries_as_dicts(result)
    assert issue_rows[0]["review_flag"]
    assert team_rows[0]["position_counts"]
    assert result.summary["market_policy"] == (
        "Roster coverage does not read or apply ADP/market."
    )
    assert result.summary["nwr_score_policy"] == (
        "Roster coverage does not invent numeric NWR scores."
    )
