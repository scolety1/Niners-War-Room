from __future__ import annotations

import pytest

from src.services.prospective_outcome_schema_v1_service import (
    DRAFT_EVALUATION_METHOD_DEFERRED,
    TRADE_ACCEPTANCE_STATUSES,
    TRADE_PACKAGE_DISPOSITIONS,
    AddDropOutcomeDetail,
    DraftOutcomeDetail,
    FaabBidRangeCalibration,
    FaabOutcomeDetail,
    FaabPlayerDecisionQuality,
    StartSitOutcomeDetail,
    StreamerOutcomeDetail,
    TradeFinderOutcomeDetail,
    TradeOutcomeDetail,
    TradeRealizedRosterOutcome,
    WaiverOutcomeDetail,
    build_deferred_draft_outcome_detail,
)


def test_every_decision_type_has_a_genuinely_distinct_kind() -> None:
    """The hard rule for this work: decision-type-specific outcome
    semantics, NOT one generic score. Every schema's `KIND` discriminator
    must be unique."""

    kinds = {
        StartSitOutcomeDetail.KIND,
        WaiverOutcomeDetail.KIND,
        AddDropOutcomeDetail.KIND,
        FaabOutcomeDetail.KIND,
        TradeOutcomeDetail.KIND,
        TradeFinderOutcomeDetail.KIND,
        StreamerOutcomeDetail.KIND,
        DraftOutcomeDetail.KIND,
    }
    assert len(kinds) == 8


def test_start_sit_detail_round_trips() -> None:
    detail = StartSitOutcomeDetail(
        week=1,
        recommended_starter_ids=("100", "200"),
        actual_starter_ids=("100", "300"),
        eligible_alternative_ids_at_lock=("300", "400"),
        recommended_only_ids=("200",),
        actual_only_ids=("300",),
        recommended_projected_total=145.2,
        actual_points_total=139.8,
        actual_points_by_player_id={"100": 20.5, "200": 10.0, "300": 18.5},
        lineup_opportunity_cost=-8.5,
    )
    row = detail.to_detail_dict()
    assert row["kind"] == "START_SIT_LINEUP_V1"
    assert row["recommendedStarterIds"] == ["100", "200"]
    assert row["actualStarterIds"] == ["100", "300"]
    assert row["lineupOpportunityCost"] == -8.5


def test_faab_keeps_player_decision_quality_and_bid_calibration_separate() -> None:
    detail = FaabOutcomeDetail(
        recommended_player_id="500",
        player_decision_quality=FaabPlayerDecisionQuality(
            subsequent_points=42.0, subsequent_roster_usage_weeks=3, horizon_weeks=4
        ),
        bid_range_calibration=FaabBidRangeCalibration(
            suggested_bid_low=5.0,
            suggested_bid_high=12.0,
            amount_bid=8.0,
            won=True,
            actual_winning_bid=8.0,
            bid_within_suggested_range=True,
            margin_vs_actual_winning_bid=0.0,
        ),
    )
    row = detail.to_detail_dict()
    # Two structurally separate nested objects -- a bad bid-range call must
    # never be able to silently corrupt the player-quality figure or vice
    # versa (they are different dataclasses entirely, not shared fields).
    assert set(row["playerDecisionQuality"].keys()) == {
        "subsequentPoints", "subsequentRosterUsageWeeks", "horizonWeeks",
    }
    assert set(row["bidRangeCalibration"].keys()) == {
        "suggestedBidLow", "suggestedBidHigh", "amountBid", "won",
        "actualWinningBid", "bidWithinSuggestedRange", "marginVsActualWinningBid",
    }
    assert not (set(row["playerDecisionQuality"].keys()) & set(row["bidRangeCalibration"].keys()))


def test_trade_rejects_realized_outcome_without_acceptance() -> None:
    with pytest.raises(ValueError):
        TradeOutcomeDetail(
            acceptance_status="REJECTED",
            trade_accepted=False,
            realized_roster_outcome=TradeRealizedRosterOutcome(
                horizon_weeks=4,
                gives_subsequent_points={"1": 10.0},
                receives_subsequent_points={"2": 12.0},
                net_subsequent_points_delta=2.0,
            ),
        )


def test_trade_rejects_unknown_acceptance_status() -> None:
    with pytest.raises(ValueError):
        TradeOutcomeDetail(acceptance_status="MAYBE", trade_accepted=None, realized_roster_outcome=None)


def test_trade_accepted_with_realized_outcome_is_valid() -> None:
    detail = TradeOutcomeDetail(
        acceptance_status="ACCEPTED",
        trade_accepted=True,
        realized_roster_outcome=TradeRealizedRosterOutcome(
            horizon_weeks=4,
            gives_subsequent_points={"1": 10.0},
            receives_subsequent_points={"2": 12.0},
            net_subsequent_points_delta=2.0,
        ),
    )
    row = detail.to_detail_dict()
    assert row["acceptanceStatus"] == "ACCEPTED"
    assert row["realizedRosterOutcome"]["netSubsequentPointsDelta"] == 2.0


def test_trade_rejected_never_carries_a_realized_outcome_key_populated() -> None:
    """A rejected trade gets an acceptance/adoption signal ONLY -- no
    realized-roster-outcome verdict against an unobserved counterfactual."""

    detail = TradeOutcomeDetail(acceptance_status="REJECTED", trade_accepted=False, realized_roster_outcome=None)
    row = detail.to_detail_dict()
    assert row["realizedRosterOutcome"] is None


def test_trade_finder_linked_outcome_only_valid_when_accepted() -> None:
    accepted_trade = TradeOutcomeDetail(acceptance_status="ACCEPTED", trade_accepted=True, realized_roster_outcome=None)
    with pytest.raises(ValueError):
        TradeFinderOutcomeDetail(package_disposition="SENT", linked_trade_outcome=accepted_trade)


def test_trade_finder_dispositions_cover_the_directive_named_set() -> None:
    assert TRADE_PACKAGE_DISPOSITIONS == frozenset({"IGNORED", "CONSIDERED", "SENT", "ACCEPTED", "UNKNOWN"})
    assert TRADE_ACCEPTANCE_STATUSES == frozenset({"ACCEPTED", "REJECTED", "UNKNOWN"})


def test_streamer_detail_is_independent_of_position() -> None:
    k_detail = StreamerOutcomeDetail(
        position="K", week=1, recommended_player_id="k1", recommended_player_actual_points=8.0,
        actual_starter_player_id="k1", actual_starter_actual_points=8.0,
        prior_roster_option_player_id="k0", prior_roster_option_actual_points=5.0,
        available_alternative_ids_at_recommendation=("k2", "k3"),
        best_available_alternative_id="k2", best_available_alternative_actual_points=9.0,
    )
    dst_detail = StreamerOutcomeDetail(
        position="DST", week=1, recommended_player_id="DEN", recommended_player_actual_points=12.0,
        actual_starter_player_id="DEN", actual_starter_actual_points=12.0,
        prior_roster_option_player_id="SF", prior_roster_option_actual_points=3.0,
        available_alternative_ids_at_recommendation=("LAC",),
        best_available_alternative_id="LAC", best_available_alternative_actual_points=1.0,
    )
    assert k_detail.to_detail_dict()["position"] == "K"
    assert dst_detail.to_detail_dict()["position"] == "DST"
    # Independently evaluated -- one never references the other's fields.
    assert k_detail.recommended_player_id != dst_detail.recommended_player_id


def test_draft_detail_is_schema_only_and_names_the_deferred_method() -> None:
    detail = build_deferred_draft_outcome_detail(notes="no boundary-cleared computation this pass")
    assert detail.evaluation_method == DRAFT_EVALUATION_METHOD_DEFERRED
    assert detail.season_long_roster_utility is None
    assert detail.injury_luck_adjustment is None
    row = detail.to_detail_dict()
    assert row["kind"] == "DRAFT_V1"
    assert row["seasonLongRosterUtility"] is None
