from __future__ import annotations

import inspect

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_add_drop_evaluator_v1_service import (
    CAUSAL_ISOLATION_DISCLOSURE,
    evaluate_add_drop,
    summarize_add_drop_evaluations,
)
from src.services.prospective_outcome_ingestion_v1_service import ingest_add_drop_outcome


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trace-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="ADD_DROP",
        engine_version="v1", data_versions={}, roster_state_player_ids=("p1",),
        free_agent_state_player_ids=None, recommendation={"addPlayerId": "100", "dropPlayerId": "555"},
        alternatives=(), recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _record_with_add_drop_outcome(
    *, added_player_id, dropped_player_id, transactions_for_period=(), horizon_matchup_entries=(),
) -> DecisionTraceRecord:
    detail = ingest_add_drop_outcome(
        added_player_id=added_player_id, dropped_player_id=dropped_player_id, owner_roster_id=9,
        transactions_for_period=transactions_for_period, horizon_matchup_entries=horizon_matchup_entries,
    )
    return _base_record(outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()})


def test_no_outcome_recorded_yet_carries_no_fabricated_fields() -> None:
    record = _base_record()
    result = evaluate_add_drop(record)
    assert result.evaluation.evaluation_status == "PENDING_OUTCOME"
    assert result.added_player_id is None
    assert result.net_roster_value_points is None


def test_no_added_player_id_is_insufficient_decision_context() -> None:
    record = _record_with_add_drop_outcome(added_player_id=None, dropped_player_id=None)
    result = evaluate_add_drop(record)
    assert result.evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"
    assert result.added_player_id is None


def test_wrong_decision_type_is_rejected() -> None:
    record = _base_record(tool="FAAB")
    with pytest.raises(ValueError):
        evaluate_add_drop(record)


# ---------------------------------------------------------------------------
# PENDING_WINDOW still reports the real identity/reversal facts -- the same
# refinement pattern the WAIVER evaluator uses.
# ---------------------------------------------------------------------------


def test_pending_window_still_reports_real_identity_and_reversal_facts() -> None:
    record = _record_with_add_drop_outcome(added_player_id="100", dropped_player_id="555")
    assert record.outcome["detail"]["addedPlayerSubsequentPoints"] is None  # no horizon data supplied

    result = evaluate_add_drop(record)
    assert result.evaluation.evaluation_status == "PENDING_WINDOW"
    assert result.added_player_id == "100"
    assert result.dropped_player_id == "555"
    assert result.added_player_subsequent_points is None  # honestly still not observed


def test_dropped_player_reversal_is_a_real_observed_fact() -> None:
    readd_transaction = {"type": "waiver", "status": "complete", "adds": {"555": "9"}}
    record = _record_with_add_drop_outcome(
        added_player_id="100", dropped_player_id="555", transactions_for_period=[readd_transaction],
    )
    result = evaluate_add_drop(record)
    assert result.dropped_player_reversed is True


# ---------------------------------------------------------------------------
# Net roster value -- honestly None whenever the dropped player's subsequent
# value can't be reconstructed (always, this pass -- inherited open issue).
# ---------------------------------------------------------------------------


def test_net_roster_value_is_honestly_none_since_dropped_player_value_is_unreconstructable() -> None:
    horizon = [{"starters": ["100"], "players_points": {"100": 12.0}}]
    record = _record_with_add_drop_outcome(
        added_player_id="100", dropped_player_id="555", horizon_matchup_entries=horizon,
    )
    result = evaluate_add_drop(record)
    assert result.added_player_subsequent_points == 12.0
    assert result.dropped_player_subsequent_points is None
    assert result.net_roster_value_points is None
    assert any("netRosterValuePoints" in issue for issue in result.issues)


def test_causal_isolation_disclosure_is_always_present() -> None:
    record = _record_with_add_drop_outcome(added_player_id="100", dropped_player_id="555")
    result = evaluate_add_drop(record)
    assert CAUSAL_ISOLATION_DISCLOSURE in result.issues


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_add_drop_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_add_drop).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_evaluate_add_drop_is_pure_given_the_same_inputs() -> None:
    record = _record_with_add_drop_outcome(added_player_id="100", dropped_player_id="555")
    assert evaluate_add_drop(record) == evaluate_add_drop(record)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def test_summary_below_minimum_sample_reports_not_enough_data() -> None:
    results = [evaluate_add_drop(_record_with_add_drop_outcome(added_player_id="100", dropped_player_id="555"))
               for _ in range(4)]
    summary = summarize_add_drop_evaluations(results)
    assert summary["addedPlayerValue"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert summary["dropReversalRate"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"


def test_summary_computes_real_stats_once_the_minimum_sample_is_reached() -> None:
    horizon = [{"starters": ["100"], "players_points": {"100": 8.0}}]
    results = [
        evaluate_add_drop(
            _record_with_add_drop_outcome(added_player_id="100", dropped_player_id="555", horizon_matchup_entries=horizon)
        )
        for _ in range(20)
    ]
    summary = summarize_add_drop_evaluations(results)
    assert summary["addedPlayerValue"]["summaryStatus"] == "SUMMARIZED"
    assert summary["addedPlayerValue"]["meanAddedPlayerSubsequentPoints"] == 8.0
