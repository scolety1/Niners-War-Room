from __future__ import annotations

import inspect

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_ingestion_v1_service import ingest_waiver_outcome
from src.services.prospective_outcome_waiver_evaluator_v1_service import (
    WaiverEvaluatorResult,
    evaluate_waiver,
    summarize_waiver_evaluations,
)


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trace-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=("p1",),
        free_agent_state_player_ids=("100", "200"), recommendation={"topAddCanonicalId": "100"}, alternatives=(),
        recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _record_with_waiver_outcome(
    *, recommended_player_id, free_agent_state_player_ids=("100", "200"),
    transactions_for_period=(), horizon_matchup_entries=(), recommendation=None,
) -> DecisionTraceRecord:
    detail = ingest_waiver_outcome(
        recommended_player_id=recommended_player_id, owner_roster_id=9,
        transactions_for_period=transactions_for_period, horizon_matchup_entries=horizon_matchup_entries,
    )
    return _base_record(
        free_agent_state_player_ids=free_agent_state_player_ids,
        recommendation=recommendation or {"topAddCanonicalId": recommended_player_id},
        outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()},
    )


# ---------------------------------------------------------------------------
# Base evaluation reuse / INSUFFICIENT_DECISION_CONTEXT
# ---------------------------------------------------------------------------


def test_no_outcome_recorded_yet_is_pending_with_no_fabricated_fields() -> None:
    record = _base_record()
    result = evaluate_waiver(record)
    assert result.evaluation.evaluation_status == "PENDING_OUTCOME"
    assert result.claim_submitted is None
    assert result.claim_won is None
    assert result.subsequent_total_points is None


def test_no_recommended_player_id_is_insufficient_decision_context() -> None:
    record = _record_with_waiver_outcome(recommended_player_id=None)
    result = evaluate_waiver(record)
    assert result.evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"
    assert result.claim_submitted is None
    assert result.claim_won is None
    assert result.faab_paid is None


def test_wrong_decision_type_is_rejected() -> None:
    record = _base_record(tool="ADD_DROP")
    with pytest.raises(ValueError):
        evaluate_waiver(record)


# ---------------------------------------------------------------------------
# The real refinement: claimSubmitted/claimWon survive PENDING_WINDOW, since
# they are real, already-observed facts independent of the bounded-horizon
# subsequent-value window closing. Recommendation quality (was the target
# good) is kept separate from transaction execution (was it claimed/won).
# ---------------------------------------------------------------------------


def test_claim_won_but_window_pending_still_reports_the_real_claim_facts() -> None:
    transactions = [
        {"type": "waiver", "status": "complete", "adds": {"100": "9"}, "settings": {"waiver_bid": 12}}
    ]
    record = _record_with_waiver_outcome(recommended_player_id="100", transactions_for_period=transactions)
    base_status = record.outcome["detail"]  # sanity: real ingestion output
    assert base_status["claimWon"] is True
    assert base_status["subsequentTotalPoints"] is None  # no horizon data supplied

    result = evaluate_waiver(record)
    # The base OutcomeEvaluation layer blanks metrics under PENDING_WINDOW --
    # this evaluator's whole point is to NOT lose the real claim facts.
    assert result.evaluation.evaluation_status == "PENDING_WINDOW"
    assert result.claim_submitted is True
    assert result.claim_won is True
    assert result.faab_paid == 12.0
    assert result.subsequent_total_points is None  # honestly still not observed


def test_claim_never_submitted_is_a_real_observed_fact_not_a_recommendation_failure() -> None:
    record = _record_with_waiver_outcome(recommended_player_id="100", transactions_for_period=())
    result = evaluate_waiver(record)
    assert result.claim_submitted is False
    assert result.claim_won is False
    # A real False is not an "unknown" -- it is reported plainly, and stays
    # conceptually distinct from whether "100" was a genuinely good target
    # (this module makes no verdict conflating the two).
    assert result.evaluation.evaluation_status == "EVALUATED"


# ---------------------------------------------------------------------------
# Claimable at recommendation time
# ---------------------------------------------------------------------------


def test_claimable_at_recommendation_time_true_when_player_was_a_free_agent_at_recommendation() -> None:
    record = _record_with_waiver_outcome(recommended_player_id="100", free_agent_state_player_ids=("100", "200"))
    result = evaluate_waiver(record)
    assert result.claimable_at_recommendation_time is True


def test_claimable_at_recommendation_time_false_when_player_was_not_a_free_agent() -> None:
    record = _record_with_waiver_outcome(recommended_player_id="999", free_agent_state_player_ids=("100", "200"))
    result = evaluate_waiver(record)
    assert result.claimable_at_recommendation_time is False


def test_claimable_at_recommendation_time_honestly_none_when_never_recorded() -> None:
    record = _record_with_waiver_outcome(recommended_player_id="100", free_agent_state_player_ids=None)
    result = evaluate_waiver(record)
    assert result.claimable_at_recommendation_time is None
    assert any("claimableAtRecommendationTime" in issue for issue in result.issues)


def test_recommended_drop_is_none_when_the_recommendation_payload_never_carried_one() -> None:
    record = _record_with_waiver_outcome(recommended_player_id="100", recommendation={"topAddCanonicalId": "100"})
    result = evaluate_waiver(record)
    assert result.recommended_drop_player_id is None


def test_recommended_drop_is_read_when_the_recommendation_payload_carries_one() -> None:
    record = _record_with_waiver_outcome(
        recommended_player_id="100", recommendation={"topAddCanonicalId": "100", "dropPlayerId": "555"}
    )
    result = evaluate_waiver(record)
    assert result.recommended_drop_player_id == "555"


# ---------------------------------------------------------------------------
# Horizon reuse -- the preregistered 4-week window, never re-derived.
# ---------------------------------------------------------------------------


def test_horizon_weeks_matches_the_preregistered_default() -> None:
    record = _record_with_waiver_outcome(recommended_player_id="100")
    result = evaluate_waiver(record)
    assert result.horizon_weeks == 4


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_waiver_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_waiver).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_evaluate_waiver_is_pure_given_the_same_inputs() -> None:
    record = _record_with_waiver_outcome(recommended_player_id="100")
    assert evaluate_waiver(record) == evaluate_waiver(record)


# ---------------------------------------------------------------------------
# Aggregation -- claim submission / win / value gated independently.
# ---------------------------------------------------------------------------


def test_summary_below_minimum_sample_reports_not_enough_data() -> None:
    results = [evaluate_waiver(_record_with_waiver_outcome(recommended_player_id="100")) for _ in range(3)]
    summary = summarize_waiver_evaluations(results)
    assert summary["claimSubmissionRate"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert summary["claimWinRate"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert summary["subsequentValue"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"


def test_summary_computes_real_rates_once_the_minimum_sample_is_reached() -> None:
    won_transactions = [{"type": "waiver", "status": "complete", "adds": {"100": "9"}, "settings": {}}]
    horizon = [{"starters": ["100"], "players_points": {"100": 5.0}}]
    won_results = [
        evaluate_waiver(
            _record_with_waiver_outcome(
                recommended_player_id="100", transactions_for_period=won_transactions, horizon_matchup_entries=horizon,
            )
        )
        for _ in range(15)
    ]
    lost_results = [
        evaluate_waiver(_record_with_waiver_outcome(recommended_player_id="100", transactions_for_period=()))
        for _ in range(5)
    ]
    summary = summarize_waiver_evaluations(won_results + lost_results)
    assert summary["claimSubmissionRate"]["summaryStatus"] == "SUMMARIZED"
    assert summary["claimSubmissionRate"]["rate"] == 0.75  # 15/20 submitted
    assert summary["claimWinRate"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"  # only 15 SUBMITTED claims
    assert summary["subsequentValue"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"  # only 15 won claims too
