from __future__ import annotations

from src.services.market_influence_policy_service import (
    market_edge_classification,
    market_value_status,
    safe_market_edge_score,
)


def test_neutral_market_placeholder_is_not_usable_edge() -> None:
    row = {"market_trade_value": "50.0", "market_edge_warning": "neutral default"}

    status = market_value_status(row)
    edge = safe_market_edge_score(82.0, 50.0, status, explicit_edge="32.0")

    assert status == "neutral_market_placeholder"
    assert edge is None
    assert market_edge_classification(status, edge) == "neutral_market_placeholder"


def test_real_market_can_create_edge_without_touching_private_value() -> None:
    row = {"market_trade_value": "72.0", "market_value_status": "real_imported_market"}

    status = market_value_status(row)
    edge = safe_market_edge_score(82.0, 72.0, status)

    assert status == "real_imported_market"
    assert edge == 10.0
    assert market_edge_classification(status, edge) == "strong_positive_edge_model_higher"


def test_stale_market_is_reviewable_but_not_promoted_as_clean_edge() -> None:
    row = {
        "market_trade_value": "72.0",
        "market_source_date": "2026-01-01T00:00:00Z",
        "computed_at": "2026-05-14T00:00:00Z",
    }

    status = market_value_status(row)
    edge = safe_market_edge_score(82.0, 72.0, status)

    assert status == "stale_market"
    assert edge == 10.0
    assert market_edge_classification(status, edge) == "stale_market"
