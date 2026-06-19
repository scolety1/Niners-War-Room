from __future__ import annotations

import csv
from pathlib import Path

from src.services.mock_draft_available_pool_contract import validate_available_pool_contract


def test_available_pool_fixture_rows_validate_green() -> None:
    rookie = [{"asset_id": "rookie:a", "player": "Fixture Rookie A", "position": "WR"}]
    veteran = [{"asset_id": "veteran:b", "player": "Fixture Veteran B", "position": "RB"}]

    report = validate_available_pool_contract(rookie, veteran)

    assert report.readiness == "GREEN"
    assert report.no_ranked_output is True
    assert report.no_simulations_run is True


def test_duplicate_asset_ids_are_red() -> None:
    row = {"asset_id": "same", "player": "Fixture A", "position": "WR"}

    report = validate_available_pool_contract([row], [row])

    assert report.readiness == "RED"
    assert any("Duplicate asset_id" in error for error in report.errors)


def test_missing_identity_column_is_red() -> None:
    report = validate_available_pool_contract([{"asset_id": "rookie:a"}], [])

    assert report.readiness == "RED"
    assert any("missing identity" in error for error in report.errors)


def test_market_columns_do_not_become_nwr_value() -> None:
    rookie = [
        {
            "asset_id": "rookie:a",
            "player": "Fixture Rookie A",
            "position": "WR",
            "market_adp_pick": "2.0",
        }
    ]

    report = validate_available_pool_contract(rookie, [])

    assert report.readiness == "GREEN"


def test_available_pool_contract_writes_no_files(tmp_path: Path) -> None:
    before = list(tmp_path.iterdir())
    validate_available_pool_contract([], [])
    assert list(tmp_path.iterdir()) == before


def test_blank_available_pool_rows_are_warned_not_errors() -> None:
    report = validate_available_pool_contract(
        [{"asset_id": "", "player": "", "position": ""}],
        [],
    )

    assert report.readiness == "GREEN"
    assert report.warnings


def test_duplicate_asset_ids_after_trim_are_red() -> None:
    rookie = [{"asset_id": " fixture:a ", "player": "A", "position": "WR"}]
    veteran = [{"asset_id": "fixture:a", "player": "B", "position": "RB"}]

    report = validate_available_pool_contract(rookie, veteran)

    assert report.readiness == "RED"


def test_adversarial_duplicate_asset_fixture_is_red() -> None:
    path = Path("tests/fixtures/mock_draft_inputs/adversarial/duplicate_asset_id.csv")
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))

    report = validate_available_pool_contract(rows[:1], rows[1:])

    assert report.readiness == "RED"
