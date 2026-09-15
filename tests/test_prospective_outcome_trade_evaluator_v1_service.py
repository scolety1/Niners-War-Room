from __future__ import annotations

import inspect

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_ingestion_v1_service import ingest_trade_outcome
from src.services.prospective_outcome_schema_v1_service import (
    TradeOutcomeDetail,
    TradeRealizedRosterOutcome,
)
from src.services.prospective_outcome_trade_evaluator_v1_service import (
    TradeEvaluatorResult,
    evaluate_trade,
    summarize_trade_evaluations,
    trade_realized_metrics_from_detail,
)

_TRADE_ACCEPTED_TXN = {
    "type": "trade",
    "status": "complete",
    "adds": {"700": 9, "701": 5},
    "drops": {"701": 9, "700": 5},
}


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trade-1", league_id="lg1", profile_id="profile-1", season=2026, week=None, tool="TRADE",
        engine_version="v1", data_versions={}, roster_state_player_ids=("701", "800"),
        free_agent_state_player_ids=None,
        recommendation={"gives": ["701"], "receives": ["700"], "netMarginalUtility": 3.0, "rosValueDelta": 5.0},
        alternatives=(), recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _record_with_trade_outcome(*, transactions, owner_action=None, horizon=None) -> DecisionTraceRecord:
    detail = ingest_trade_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9, transactions_for_period=transactions,
        gives_horizon_matchup_entries=(horizon or {}).get("gives"),
        receives_horizon_matchup_entries=(horizon or {}).get("receives"),
    )
    return _base_record(
        owner_action=owner_action,
        outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()},
    )


# ---------------------------------------------------------------------------
# THE REJECTED-TRADE GUARANTEE -- three layers.
# ---------------------------------------------------------------------------


def test_schema_post_init_refuses_a_realized_outcome_on_a_non_accepted_trade() -> None:
    """Layer 1: the schema's own __post_init__ guard, reused verbatim, never
    weakened."""

    with pytest.raises(ValueError):
        TradeOutcomeDetail(
            acceptance_status="REJECTED",
            trade_accepted=False,
            realized_roster_outcome=TradeRealizedRosterOutcome(
                horizon_weeks=4, gives_subsequent_points={}, receives_subsequent_points={}, net_subsequent_points_delta=0.0
            ),
        )


def test_rejected_trade_evaluation_status_is_not_applicable_never_evaluated() -> None:
    """Layer 2: the base OutcomeEvaluation layer (Worker 1, reused
    unchanged)."""

    record = _record_with_trade_outcome(transactions=[])  # no matching txn -> REJECTED
    result = evaluate_trade(record)
    assert result.acceptance_status == "REJECTED"
    assert result.trade_accepted is False
    assert result.evaluation.evaluation_status == "NOT_APPLICABLE"
    assert result.net_subsequent_points_delta_points is None
    assert result.gives_subsequent_points_by_player is None
    assert result.receives_subsequent_points_by_player is None


def test_rejected_trade_never_produces_a_realized_metric_at_this_evaluator_layer() -> None:
    """Layer 3: this module's own extraction never fabricates a number even
    if it read the raw dict directly (defense in depth, not merely relying
    on layers 1/2)."""

    record = _record_with_trade_outcome(transactions=[])
    detail = record.outcome["detail"]
    assert detail["realizedRosterOutcome"] is None
    metrics = trade_realized_metrics_from_detail(detail)
    assert metrics["netSubsequentPointsDeltaPoints"] is None


def test_unknown_status_trade_never_scored() -> None:
    record = _base_record(outcome={"outcome": "PENDING", "notes": "no structured detail"})
    result = evaluate_trade(record)
    assert result.evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"
    assert result.net_subsequent_points_delta_points is None


# ---------------------------------------------------------------------------
# Accepted trade -- real realized-outcome evaluation.
# ---------------------------------------------------------------------------


def test_accepted_trade_reports_real_net_delta_and_per_player_breakdown() -> None:
    horizon = {
        "gives": {"701": [{"starters": [], "players_points": {"701": 5.0}}]},
        "receives": {"700": [{"starters": ["700"], "players_points": {"700": 20.0}}]},
    }
    record = _record_with_trade_outcome(transactions=[_TRADE_ACCEPTED_TXN], horizon=horizon)
    result = evaluate_trade(record)
    assert result.acceptance_status == "ACCEPTED"
    assert result.trade_accepted is True
    assert result.evaluation.evaluation_status == "EVALUATED"
    assert result.net_subsequent_points_delta_points == 15.0
    assert result.gives_subsequent_points_by_player is not None
    assert result.receives_subsequent_points_by_player is not None
    assert result.recommended_gives_ids == ("701",)
    assert result.recommended_receives_ids == ("700",)


def test_accepted_trade_without_horizon_data_yet_is_pending_window() -> None:
    record = _record_with_trade_outcome(transactions=[_TRADE_ACCEPTED_TXN])  # no horizon supplied
    result = evaluate_trade(record)
    assert result.acceptance_status == "ACCEPTED"
    assert result.evaluation.evaluation_status == "PENDING_WINDOW"
    assert result.net_subsequent_points_delta_points is None


# ---------------------------------------------------------------------------
# Owner action is verbatim, never relabeled -- and never substitutes for the
# structurally-derived acceptance status.
# ---------------------------------------------------------------------------


def test_owner_action_is_read_verbatim_and_never_drives_acceptance() -> None:
    record = _record_with_trade_outcome(
        transactions=[], owner_action={"action": "Followed it", "notes": ""}
    )  # a real app owner-action label, no matching Sleeper trade txn
    result = evaluate_trade(record)
    assert result.owner_action_raw == "Followed it"
    # Even though the owner "followed it" (whatever that meant), the real
    # transaction log shows no completed trade -- REJECTED, never inferred
    # ACCEPTED from the owner-action label alone.
    assert result.acceptance_status == "REJECTED"
    assert result.net_subsequent_points_delta_points is None


def test_no_owner_action_recorded_is_honestly_none() -> None:
    record = _record_with_trade_outcome(transactions=[])
    result = evaluate_trade(record)
    assert result.owner_action_raw is None


# ---------------------------------------------------------------------------
# Pending outcome / wrong tool
# ---------------------------------------------------------------------------


def test_no_outcome_yet_carries_no_fabricated_numbers() -> None:
    record = _base_record()
    result = evaluate_trade(record)
    assert result.evaluation.evaluation_status == "PENDING_OUTCOME"
    assert result.acceptance_status is None
    assert result.net_subsequent_points_delta_points is None
    # The trace's own frozen recommendation is still readable even with no outcome.
    assert result.recommended_gives_ids == ("701",)
    assert result.recommended_receives_ids == ("700",)


def test_wrong_decision_type_is_rejected() -> None:
    record = _base_record(tool="WAIVER")
    with pytest.raises(ValueError):
        evaluate_trade(record)


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_trade_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_trade).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_evaluate_trade_is_pure_given_the_same_inputs() -> None:
    record = _record_with_trade_outcome(transactions=[_TRADE_ACCEPTED_TXN])
    first = evaluate_trade(record)
    second = evaluate_trade(record)
    assert first == second


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _accepted_result(delta: float) -> TradeEvaluatorResult:
    record = _record_with_trade_outcome(
        transactions=[_TRADE_ACCEPTED_TXN],
        horizon={
            "gives": {"701": [{"starters": [], "players_points": {"701": 5.0}}]},
            "receives": {"700": [{"starters": ["700"], "players_points": {"700": 5.0 + delta}}]},
        },
    )
    result = evaluate_trade(record)
    object.__setattr__(result, "net_subsequent_points_delta_points", delta)
    return result


def test_summary_reports_not_enough_data_below_the_minimum_sample_size() -> None:
    results = [_accepted_result(1.0) for _ in range(5)]
    summary = summarize_trade_evaluations(results)
    assert summary["acceptedNetSubsequentPointsDelta"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert "meanNetSubsequentPointsDeltaPoints" not in summary["acceptedNetSubsequentPointsDelta"]


def test_summary_computes_a_real_mean_at_or_above_the_minimum_sample_size() -> None:
    results = [_accepted_result(3.0) for _ in range(20)]
    summary = summarize_trade_evaluations(results)
    assert summary["acceptedNetSubsequentPointsDelta"]["summaryStatus"] == "SUMMARIZED"
    assert summary["acceptedNetSubsequentPointsDelta"]["meanNetSubsequentPointsDeltaPoints"] == 3.0


def test_summary_never_includes_a_rejected_trade_in_the_accepted_delta_sample() -> None:
    accepted = [_accepted_result(3.0) for _ in range(20)]
    rejected_record = _record_with_trade_outcome(transactions=[])
    rejected_result = evaluate_trade(rejected_record)
    summary = summarize_trade_evaluations(accepted + [rejected_result])
    assert summary["acceptedNetSubsequentPointsDelta"]["sampleSize"] == 20
    assert summary["acceptanceStatusCounts"]["REJECTED"] == 1
    assert summary["acceptanceStatusCounts"]["ACCEPTED"] == 20
