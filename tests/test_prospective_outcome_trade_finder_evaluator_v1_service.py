from __future__ import annotations

import inspect

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_ingestion_v1_service import ingest_trade_finder_outcome
from src.services.prospective_outcome_trade_finder_evaluator_v1_service import (
    TradeFinderEvaluatorResult,
    evaluate_trade_finder,
    summarize_trade_finder_evaluations,
)

_TRADE_ACCEPTED_TXN = {
    "type": "trade",
    "status": "complete",
    "adds": {"700": 9, "701": 5},
    "drops": {"701": 9, "700": 5},
}


def _base_record(*, tool: str, recommendation: dict, **overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="tf-1", league_id="lg1", profile_id="profile-1", season=2026, week=None, tool=tool,
        engine_version="v1", data_versions={}, roster_state_player_ids=("701",),
        free_agent_state_player_ids=None, recommendation=recommendation, alternatives=(),
        recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _tf_record(*, disposition_action, transactions, horizon=None) -> DecisionTraceRecord:
    detail = ingest_trade_finder_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9,
        owner_action={"action": disposition_action} if disposition_action else None,
        transactions_for_period=transactions,
        gives_horizon_matchup_entries=(horizon or {}).get("gives"),
        receives_horizon_matchup_entries=(horizon or {}).get("receives"),
    )
    return _base_record(
        tool="TRADE_FINDER",
        recommendation={"myGivePlayerId": "701", "opponentGivePlayerId": "700", "opponentRosterId": 5, "myNetMarginalUtility": 3.0},
        owner_action={"action": disposition_action} if disposition_action else None,
        outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()},
    )


# ---------------------------------------------------------------------------
# Never scores an unaccepted package.
# ---------------------------------------------------------------------------


def test_ignored_package_is_not_applicable_never_scored() -> None:
    record = _tf_record(disposition_action=None, transactions=[])
    result = evaluate_trade_finder(record)
    assert result.package_disposition == "UNKNOWN"
    assert result.evaluation.evaluation_status == "NOT_APPLICABLE"
    assert result.net_subsequent_points_delta_points is None
    assert result.trade_accepted is None


def test_sent_but_not_accepted_package_is_not_applicable() -> None:
    record = _tf_record(disposition_action="SENT", transactions=[])
    result = evaluate_trade_finder(record)
    assert result.package_disposition == "SENT"
    assert result.evaluation.evaluation_status == "NOT_APPLICABLE"
    assert result.net_subsequent_points_delta_points is None


# ---------------------------------------------------------------------------
# Accepted -- reuses the Trade evaluator's own realized-outcome logic.
# ---------------------------------------------------------------------------


def test_accepted_package_reuses_trade_realized_outcome() -> None:
    horizon = {
        "gives": {"701": [{"starters": [], "players_points": {"701": 5.0}}]},
        "receives": {"700": [{"starters": ["700"], "players_points": {"700": 20.0}}]},
    }
    record = _tf_record(disposition_action=None, transactions=[_TRADE_ACCEPTED_TXN], horizon=horizon)
    result = evaluate_trade_finder(record)
    assert result.package_disposition == "ACCEPTED"
    assert result.trade_accepted is True
    assert result.evaluation.evaluation_status == "EVALUATED"
    assert result.net_subsequent_points_delta_points == 15.0


def test_accepted_package_without_horizon_data_is_pending_window() -> None:
    record = _tf_record(disposition_action=None, transactions=[_TRADE_ACCEPTED_TXN])
    result = evaluate_trade_finder(record)
    assert result.package_disposition == "ACCEPTED"
    assert result.evaluation.evaluation_status == "PENDING_WINDOW"
    assert result.net_subsequent_points_delta_points is None


# ---------------------------------------------------------------------------
# TRADE_PACKAGE_SEARCH -- real, different recommendation key names.
# ---------------------------------------------------------------------------


def test_trade_package_search_reads_yousend_youreceive_keys() -> None:
    detail = ingest_trade_finder_outcome(
        gives_ids=["701"], receives_ids=["700"], owner_roster_id=9, owner_action=None,
        transactions_for_period=[],
    )
    record = _base_record(
        tool="TRADE_PACKAGE_SEARCH",
        recommendation={"mode": "WIN_WIN", "packageShape": "1-for-1", "youSend": ["701"], "youReceive": ["700"], "opponentRosterId": 5},
        outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()},
    )
    result = evaluate_trade_finder(record)
    assert result.decision_type == "TRADE_PACKAGE_SEARCH"
    assert result.recommended_gives_ids == ("701",)
    assert result.recommended_receives_ids == ("700",)
    assert result.package_disposition == "UNKNOWN"  # no owner_action, no matching txn


def test_trade_finder_reads_singular_myGive_opponentGive_keys() -> None:
    record = _tf_record(disposition_action=None, transactions=[])
    assert record.recommendation["myGivePlayerId"] == "701"
    result = evaluate_trade_finder(record)
    assert result.decision_type == "TRADE_FINDER"
    assert result.recommended_gives_ids == ("701",)
    assert result.recommended_receives_ids == ("700",)


# ---------------------------------------------------------------------------
# No invented acceptance-probability.
# ---------------------------------------------------------------------------


def test_summary_reports_disposition_counts_only_never_a_probability_field() -> None:
    results = [
        evaluate_trade_finder(_tf_record(disposition_action="IGNORED", transactions=[])),
        evaluate_trade_finder(_tf_record(disposition_action="SENT", transactions=[])),
        evaluate_trade_finder(_tf_record(disposition_action="CONSIDERED", transactions=[])),
    ]
    summary = summarize_trade_finder_evaluations(results)
    assert summary["packageDispositionCounts"] == {"IGNORED": 1, "SENT": 1, "CONSIDERED": 1}
    # No key anywhere in the summary spells out a rate/probability/likelihood.
    forbidden_substrings = ("rate", "probability", "likelihood", "chance")
    for key in _flatten_keys(summary):
        assert not any(bad in key.lower() for bad in forbidden_substrings), key


def _flatten_keys(obj) -> list[str]:
    keys: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.append(key)
            keys.extend(_flatten_keys(value))
    return keys


def test_wrong_decision_type_is_rejected() -> None:
    record = _base_record(tool="WAIVER", recommendation={})
    with pytest.raises(ValueError):
        evaluate_trade_finder(record)


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_trade_finder_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_trade_finder).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


# ---------------------------------------------------------------------------
# Aggregation -- minimum-sample gate on the accepted-only delta.
# ---------------------------------------------------------------------------


def _accepted_result(delta: float) -> TradeFinderEvaluatorResult:
    horizon = {
        "gives": {"701": [{"starters": [], "players_points": {"701": 5.0}}]},
        "receives": {"700": [{"starters": ["700"], "players_points": {"700": 5.0 + delta}}]},
    }
    record = _tf_record(disposition_action=None, transactions=[_TRADE_ACCEPTED_TXN], horizon=horizon)
    result = evaluate_trade_finder(record)
    object.__setattr__(result, "net_subsequent_points_delta_points", delta)
    return result


def test_summary_gates_accepted_delta_by_minimum_sample_size() -> None:
    few = [_accepted_result(2.0) for _ in range(5)]
    summary_few = summarize_trade_finder_evaluations(few)
    assert summary_few["acceptedNetSubsequentPointsDelta"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"

    many = [_accepted_result(2.0) for _ in range(20)]
    summary_many = summarize_trade_finder_evaluations(many)
    assert summary_many["acceptedNetSubsequentPointsDelta"]["summaryStatus"] == "SUMMARIZED"
    assert summary_many["acceptedNetSubsequentPointsDelta"]["meanNetSubsequentPointsDeltaPoints"] == 2.0
