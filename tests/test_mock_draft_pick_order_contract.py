from __future__ import annotations

import csv
from pathlib import Path

from src.services.mock_draft_pick_order_contract import validate_pick_order_contract


def test_fixture_pick_order_validates_green() -> None:
    picks = [{"overall_pick": 1}, {"overall_pick": 2}]
    mine = [{"overall_pick": 2}]

    report = validate_pick_order_contract(picks, mine)

    assert report.readiness == "GREEN"


def test_duplicate_pick_number_returns_red() -> None:
    report = validate_pick_order_contract([{"overall_pick": 1}, {"overall_pick": 1}], [])

    assert report.readiness == "RED"


def test_missing_my_picks_returns_yellow() -> None:
    report = validate_pick_order_contract([{"overall_pick": 1}], None)

    assert report.readiness == "YELLOW"


def test_my_pick_not_in_order_returns_red() -> None:
    report = validate_pick_order_contract([{"overall_pick": 1}], [{"overall_pick": 2}])

    assert report.readiness == "RED"


def test_invalid_pick_number_returns_red() -> None:
    report = validate_pick_order_contract([{"overall_pick": 0}], [])

    assert report.readiness == "RED"


def test_non_integer_pick_number_returns_red() -> None:
    report = validate_pick_order_contract([{"overall_pick": "one"}], [])

    assert report.readiness == "RED"


def test_blank_pick_rows_are_warned_not_errors() -> None:
    report = validate_pick_order_contract([{"overall_pick": ""}], [])

    assert report.readiness == "YELLOW"
    assert report.warnings


def test_adversarial_missing_pick_number_fixture_is_red() -> None:
    path = Path("tests/fixtures/mock_draft_inputs/adversarial/missing_pick_number.csv")
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))

    report = validate_pick_order_contract(rows, [])

    assert report.readiness == "RED"


def test_adversarial_my_pick_outside_order_fixture_is_red() -> None:
    path = Path("tests/fixtures/mock_draft_inputs/adversarial/my_pick_outside_pick_order.csv")
    mine = list(csv.DictReader(path.open(newline="", encoding="utf-8")))

    report = validate_pick_order_contract([{"overall_pick": 1}], mine)

    assert report.readiness == "RED"
