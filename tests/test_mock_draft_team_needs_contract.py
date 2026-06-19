from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_team_needs_contract import validate_team_needs_contract


def test_fixture_team_needs_validate_green() -> None:
    rows = [
        {
            "team_id": "a",
            "team_name": "Fixture A",
            "position": "RB",
            "need_weight": "0.7",
            "tendency_note": "fixture",
        }
    ]

    report = validate_team_needs_contract(rows)

    assert report.readiness == "GREEN"
    assert report.opponent_behavior_only is True


def test_missing_team_id_returns_red() -> None:
    report = validate_team_needs_contract(
        [{"team_name": "A", "position": "RB", "need_weight": "0.7", "tendency_note": "x"}]
    )

    assert report.readiness == "RED"


def test_invalid_need_weight_returns_red() -> None:
    report = validate_team_needs_contract(
        [
            {
                "team_id": "a",
                "team_name": "A",
                "position": "RB",
                "need_weight": "2",
                "tendency_note": "x",
            }
        ]
    )

    assert report.readiness == "RED"


def test_opponent_tendency_cannot_be_nwr_value() -> None:
    report = validate_team_needs_contract(
        [
            {
                "team_id": "a",
                "team_name": "A",
                "position": "RB",
                "need_weight": "0.7",
                "tendency_note": "x",
                "nwr_private_value": "99",
            }
        ]
    )

    assert report.readiness == "RED"


def test_team_needs_contract_writes_no_files(tmp_path: Path) -> None:
    before = list(tmp_path.iterdir())
    validate_team_needs_contract([])
    assert list(tmp_path.iterdir()) == before
