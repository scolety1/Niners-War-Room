from __future__ import annotations

from src.services.waiver_engine_service import WaiverCandidate, suggest_faab_bids


def _candidate() -> WaiverCandidate:
    return WaiverCandidate(
        sleeper_player_id="s-1",
        canonical_player_id="p-1",
        player_name="Positive Add, Negative Transaction",
        position="WR",
        team="DEN",
        ros_replacement_value=5.0,
        ros_overall_rank=50,
        weekly_projected_points=None,
        marginal_utility=8.0,
        becomes_starter=True,
        marginal_utility_explanation="Positive standalone add value.",
        identity_status="MATCHED",
    )


def test_nonpositive_add_drop_net_never_gets_a_positive_faab_bid() -> None:
    candidate = _candidate()

    bid = suggest_faab_bids(
        candidates=(candidate,),
        remaining_budget_dollars=73,
        total_budget_dollars=100,
        weeks_remaining=9,
        transaction_net_utility_by_sleeper_id={candidate.sleeper_player_id: -0.01},
    )[0]

    assert candidate.marginal_utility > 0
    assert bid.bid_low_dollars == 0
    assert bid.bid_high_dollars == 0
    assert bid.bid_low_pct == 0.0
    assert bid.bid_high_pct == 0.0
    assert "nonpositive add/drop value" in bid.rationale


def test_positive_legal_transaction_still_uses_real_remaining_budget() -> None:
    candidate = _candidate()

    bid = suggest_faab_bids(
        candidates=(candidate,),
        remaining_budget_dollars=37,
        total_budget_dollars=100,
        weeks_remaining=9,
        transaction_net_utility_by_sleeper_id={candidate.sleeper_player_id: 2.5},
    )[0]

    assert bid.bid_low_dollars == round(37 * bid.bid_low_pct)
    assert bid.bid_high_dollars == round(37 * bid.bid_high_pct)
    assert bid.bid_low_dollars > 0
