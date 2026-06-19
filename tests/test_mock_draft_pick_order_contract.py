from __future__ import annotations

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
