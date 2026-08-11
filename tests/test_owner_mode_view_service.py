from __future__ import annotations

from src.services.owner_mode_view_service import (
    market_decision_label,
    owner_range,
    owner_rankings_frame,
)


def test_market_decision_label_uses_five_owner_bands() -> None:
    assert market_decision_label(10, 40)[0].startswith("Potential buy")
    assert market_decision_label(10, 18)[0] == "NWR slightly higher"
    assert market_decision_label(10, 12)[0] == "Market aligned"
    assert market_decision_label(20, 10)[0] == "Market slightly higher"
    assert market_decision_label(40, 10)[0].startswith("Potential sell")
    assert market_decision_label("", 10) == ("Market data unavailable", "")


def test_owner_range_uses_research_contract_without_synthetic_numbers() -> None:
    assert owner_range(
        {
            "research_downside_signal": "Starter tier",
            "research_tier": "RESEARCH_TIER_2",
            "research_ceiling_signal": "Upper WR tier",
        }
    ) == {
        "Floor": "Starter tier",
        "Expected": "Research neighborhood 2",
        "Ceiling": "Upper WR tier",
    }
    assert set(owner_range({}).values()) == {"Not enough information"}
    assert owner_range(
        {"research_downside_signal": "0", "research_ceiling_signal": "0.634846"}
    ) == {
        "Floor": "Downside signal: 0.0%",
        "Expected": "Not enough information",
        "Ceiling": "Ceiling signal: 63.5%",
    }


def test_owner_rankings_keeps_only_current_players_and_canonical_order() -> None:
    frame = owner_rankings_frame(
        [
            {
                "asset_id": "current:b",
                "asset_type": "Current Player",
                "asset_name": "B",
                "dynasty_rank": "2",
                "market_dp_rank": "8",
            },
            {
                "asset_id": "rookie:r",
                "asset_type": "Rookie Review",
                "asset_name": "R",
                "dynasty_rank": "1",
            },
            {
                "asset_id": "current:a",
                "asset_type": "Current Player",
                "asset_name": "A",
                "dynasty_rank": "1",
                "market_dp_rank": "1",
            },
        ]
    )
    assert frame["asset_id"].tolist() == ["current:a", "current:b"]
