from __future__ import annotations

from src.services.mock_draft_market_separation_contract import validate_market_separation


def test_valid_separate_market_and_private_values_pass() -> None:
    market = [{"asset_id": "a", "market_adp_pick": "2.0"}]
    private = [{"asset_id": "a", "nwr_private_value": "70"}]

    report = validate_market_separation(market, private)

    assert report.readiness == "GREEN"
    assert report.no_rankings_created is True


def test_market_adp_inside_private_values_fails() -> None:
    report = validate_market_separation([], [{"asset_id": "a", "market_adp_pick": "2.0"}])

    assert report.readiness == "RED"


def test_private_score_inside_market_fails() -> None:
    report = validate_market_separation([{"asset_id": "a", "nwr_private_value": "70"}], [])

    assert report.readiness == "RED"


def test_merged_market_private_shape_fails() -> None:
    merged = [{"asset_id": "a", "market_adp_pick": "2.0", "nwr_private_value": "70"}]

    report = validate_market_separation(merged, merged)

    assert report.readiness == "RED"
