from __future__ import annotations

from src.services.owner_mode_view_service import (
    market_decision_label,
    market_rank_gap,
    owner_availability,
    owner_range,
    owner_range_contract,
    owner_rankings_frame,
    owner_value_tier,
)


def test_market_decision_label_uses_five_owner_bands() -> None:
    assert market_decision_label(10, 40)[0] == "Potential Buy"
    assert market_decision_label(10, 18)[0] == "NWR Higher"
    assert market_decision_label(10, 12)[0] == "Aligned"
    assert market_decision_label(20, 10)[0] == "Market Higher"
    assert market_decision_label(40, 10)[0] == "Potential Sell / Caution"
    assert market_decision_label("", 10) == ("Market data unavailable", "")
    assert market_rank_gap(10, 40) == 30.0


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


def test_owner_range_contract_and_value_tier_are_explicit() -> None:
    contract = owner_range_contract(
        {
            "asset_type": "Current Player",
            "research_downside_signal": "Starter tier",
            "research_tier": "RESEARCH_TIER_2",
            "research_ceiling_signal": "Upper WR tier",
        }
    )
    assert contract["NWR Expected"] == "Research neighborhood 2"
    assert contract["Downside label"] == "Downside signal"
    assert contract["Expected label"] == "Research neighborhood"
    assert contract["Upside label"] == "Upside signal"
    assert contract["Authority"] == "Research context beside Finished V1"
    assert "Frozen Unified Research" in contract["Method"]
    assert owner_value_tier("priority candidate") == ("Tier A", "Core priority")
    assert owner_availability({}) == "Not enough information"
    assert "Injury" in owner_availability({"risk_notes": "injury_status_review_required"})
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
                "market_dp_value": "6200",
                "market_evidence_date": "2026-08-01",
                "candidate_value_band": "strong candidate",
                "value_band": "strong candidate",
                "risk": "medium",
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
    assert {"Age", "Tier", "NWR View", "NWR vs Market", "Market Date", "Risk"} <= set(
        frame.columns
    )
    assert frame.loc[frame["asset_id"].eq("current:b"), "NWR vs Market"].iloc[0] == 6.0
