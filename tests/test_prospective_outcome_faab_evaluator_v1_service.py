from __future__ import annotations

import inspect

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_faab_evaluator_v1_service import (
    evaluate_faab,
    summarize_faab_evaluations,
)
from src.services.prospective_outcome_ingestion_v1_service import ingest_faab_outcome


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trace-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="FAAB",
        engine_version="v1", data_versions={}, roster_state_player_ids=("p1",),
        free_agent_state_player_ids=None, recommendation={"playerName": "X", "bidLowDollars": 10, "bidHighDollars": 20},
        alternatives=(), recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _record_with_faab_outcome(
    *, recommended_player_id, suggested_bid_low, suggested_bid_high, transactions_for_period=(),
    horizon_matchup_entries=(),
) -> DecisionTraceRecord:
    detail = ingest_faab_outcome(
        recommended_player_id=recommended_player_id, owner_roster_id=9, suggested_bid_low=suggested_bid_low,
        suggested_bid_high=suggested_bid_high, transactions_for_period=transactions_for_period,
        horizon_matchup_entries=horizon_matchup_entries,
    )
    return _base_record(outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()})


def test_no_outcome_recorded_yet_carries_no_fabricated_fields() -> None:
    record = _base_record()
    result = evaluate_faab(record)
    assert result.evaluation.evaluation_status == "PENDING_OUTCOME"
    assert result.player_decision_quality is None
    assert result.bid_range_calibration is None


def test_no_recommended_player_id_is_insufficient_decision_context() -> None:
    record = _record_with_faab_outcome(recommended_player_id=None, suggested_bid_low=10, suggested_bid_high=20)
    result = evaluate_faab(record)
    assert result.evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"


def test_wrong_decision_type_is_rejected() -> None:
    record = _base_record(tool="WAIVER")
    with pytest.raises(ValueError):
        evaluate_faab(record)


# ---------------------------------------------------------------------------
# THE core independence guarantee: player_decision_quality and
# bid_range_calibration are genuinely independent -- one can be good while
# the other is bad, in either direction.
# ---------------------------------------------------------------------------


def test_good_pickup_with_a_badly_calibrated_bid_range() -> None:
    # The player was won and produced real subsequent value (GOOD pickup),
    # but the suggested $10-20 range badly undershot the real $45 needed to
    # win it (BAD calibration).
    won_transaction = {
        "type": "waiver", "status": "complete", "adds": {"100": "9"}, "settings": {"waiver_bid": 45},
    }
    horizon = [{"starters": ["100"], "players_points": {"100": 22.0}}]
    record = _record_with_faab_outcome(
        recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=20,
        transactions_for_period=[won_transaction], horizon_matchup_entries=horizon,
    )
    result = evaluate_faab(record)
    assert result.player_decision_quality["subsequentPoints"] == 22.0  # GOOD
    assert result.bid_range_calibration["bidWithinSuggestedRange"] is False  # BAD
    assert result.bid_range_calibration["actualWinningBid"] == 45.0


def test_bad_pickup_with_a_well_calibrated_bid_range() -> None:
    # The suggested $10-20 range correctly matched the real $15 winning bid
    # (GOOD calibration), but the player barely produced any real subsequent
    # value once rostered (BAD pickup).
    won_transaction = {
        "type": "waiver", "status": "complete", "adds": {"100": "9"}, "settings": {"waiver_bid": 15},
    }
    horizon = [{"starters": [], "players_points": {"100": 0.5}}]
    record = _record_with_faab_outcome(
        recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=20,
        transactions_for_period=[won_transaction], horizon_matchup_entries=horizon,
    )
    result = evaluate_faab(record)
    assert result.player_decision_quality["subsequentPoints"] == 0.5  # low/BAD
    assert result.bid_range_calibration["bidWithinSuggestedRange"] is True  # GOOD
    assert result.bid_range_calibration["actualWinningBid"] == 15.0


def test_neither_axis_influences_the_others_value_when_recomputed_with_only_one_changed() -> None:
    won_transaction = {
        "type": "waiver", "status": "complete", "adds": {"100": "9"}, "settings": {"waiver_bid": 45},
    }
    horizon = [{"starters": ["100"], "players_points": {"100": 22.0}}]
    baseline = evaluate_faab(
        _record_with_faab_outcome(
            recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=20,
            transactions_for_period=[won_transaction], horizon_matchup_entries=horizon,
        )
    )
    # Widen the suggested range so calibration flips to GOOD -- quality must
    # stay byte-identical, since it never reads the bid range at all.
    widened = evaluate_faab(
        _record_with_faab_outcome(
            recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=50,
            transactions_for_period=[won_transaction], horizon_matchup_entries=horizon,
        )
    )
    assert baseline.player_decision_quality == widened.player_decision_quality
    assert baseline.bid_range_calibration != widened.bid_range_calibration
    assert baseline.bid_range_calibration["bidWithinSuggestedRange"] is False
    assert widened.bid_range_calibration["bidWithinSuggestedRange"] is True


# ---------------------------------------------------------------------------
# Never uses a hidden/pending bid, never invents opponent bid probabilities.
# ---------------------------------------------------------------------------


def test_a_pending_uncompleted_transaction_is_never_treated_as_an_observable_winning_bid() -> None:
    pending_transaction = {
        "type": "waiver", "status": "pending", "adds": {"100": "9"}, "settings": {"waiver_bid": 999},
    }
    record = _record_with_faab_outcome(
        recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=20,
        transactions_for_period=[pending_transaction],
    )
    result = evaluate_faab(record)
    assert result.bid_range_calibration["actualWinningBid"] is None
    assert result.bid_range_calibration["won"] is False


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_faab_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_faab).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_evaluate_faab_is_pure_given_the_same_inputs() -> None:
    record = _record_with_faab_outcome(recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=20)
    assert evaluate_faab(record) == evaluate_faab(record)


# ---------------------------------------------------------------------------
# Aggregation -- the two axes gated INDEPENDENTLY.
# ---------------------------------------------------------------------------


def test_summary_gates_each_axis_independently() -> None:
    won_transaction = {"type": "waiver", "status": "complete", "adds": {"100": "9"}, "settings": {"waiver_bid": 45}}
    horizon = [{"starters": ["100"], "players_points": {"100": 22.0}}]
    # 20 real quality samples (won + horizon data), but only 5 of them also
    # carry a real winning-bid observation for calibration.
    with_calibration = [
        evaluate_faab(
            _record_with_faab_outcome(
                recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=20,
                transactions_for_period=[won_transaction], horizon_matchup_entries=horizon,
            )
        )
        for _ in range(5)
    ]
    without_calibration = [
        evaluate_faab(
            _record_with_faab_outcome(
                recommended_player_id="100", suggested_bid_low=None, suggested_bid_high=None,
                transactions_for_period=[won_transaction], horizon_matchup_entries=horizon,
            )
        )
        for _ in range(15)
    ]
    summary = summarize_faab_evaluations(with_calibration + without_calibration)
    assert summary["playerDecisionQuality"]["summaryStatus"] == "SUMMARIZED"
    assert summary["playerDecisionQuality"]["sampleSize"] == 20
    assert summary["playerDecisionQuality"]["meanSubsequentPoints"] == 22.0
    assert summary["bidRangeCalibration"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert summary["bidRangeCalibration"]["sampleSize"] == 5


def test_summary_below_minimum_sample_reports_not_enough_data_on_both_axes() -> None:
    results = [
        evaluate_faab(
            _record_with_faab_outcome(recommended_player_id="100", suggested_bid_low=10, suggested_bid_high=20)
        )
        for _ in range(3)
    ]
    summary = summarize_faab_evaluations(results)
    assert summary["playerDecisionQuality"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert summary["bidRangeCalibration"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
