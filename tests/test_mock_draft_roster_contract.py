from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_roster_contract import validate_roster_contract


def test_fixture_rosters_validate_green() -> None:
    rows = [
        {
            "team_id": "a",
            "team_name": "Fixture A",
            "player": "Fixture Keeper",
            "position": "WR",
            "keeper_status": "kept",
        }
    ]

    report = validate_roster_contract(rows)

    assert report.readiness == "GREEN"


def test_duplicate_kept_player_multiple_teams_returns_red() -> None:
    rows = [
        {
            "team_id": "a",
            "team_name": "A",
            "player": "Same",
            "position": "WR",
            "keeper_status": "kept",
        },
        {
            "team_id": "b",
            "team_name": "B",
            "player": "Same",
            "position": "WR",
            "keeper_status": "kept",
        },
    ]

    report = validate_roster_contract(rows)

    assert report.readiness == "RED"


def test_available_pool_overlap_with_kept_player_returns_red() -> None:
    roster = [
        {
            "team_id": "a",
            "team_name": "A",
            "player": "Same",
            "position": "WR",
            "keeper_status": "kept",
        }
    ]
    available = [{"player": "Same"}]

    report = validate_roster_contract(roster, available)

    assert report.readiness == "RED"


def test_missing_roster_input_returns_yellow() -> None:
    report = validate_roster_contract(None)

    assert report.readiness == "YELLOW"


def test_roster_contract_writes_no_files(tmp_path: Path) -> None:
    before = list(tmp_path.iterdir())
    validate_roster_contract([])
    assert list(tmp_path.iterdir()) == before
