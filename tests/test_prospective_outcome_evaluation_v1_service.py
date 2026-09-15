from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.in_season_decision_trace_service import (
    DecisionTraceRecord,
    load_decision_traces,
    record_decision_trace,
    record_outcome,
)
from src.services.prospective_outcome_evaluation_v1_service import (
    EVALUATION_STATUSES,
    EVALUATION_WINDOWS,
    MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY,
    OutcomeEvaluation,
    ProspectiveOutcomeEvaluationError,
    compute_outcome_evaluation,
)
from src.services.prospective_outcome_ingestion_v1_service import ingest_start_sit_outcome

_REAL_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "codex" / "prospective_outcome_v1" / "real_data_v1"
    / "fantasy_gamers_week1_2026_owner_matchup.json"
)


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trace-1",
        league_id="lg1",
        profile_id="profile-1",
        season=2026,
        week=1,
        tool="START_SIT",
        engine_version="v1",
        data_versions={},
        roster_state_player_ids=("p1", "p2"),
        free_agent_state_player_ids=None,
        recommendation={"starters": ["p1"]},
        alternatives=(),
        recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


# ---------------------------------------------------------------------------
# Preregistration lock -- contract Section 3's exact numbers. A future
# silent edit to EVALUATION_WINDOWS fails this test immediately.
# ---------------------------------------------------------------------------


def test_evaluation_windows_match_the_preregistered_contract_exactly() -> None:
    assert EVALUATION_WINDOWS == {
        "START_SIT": {"label": "SAME_WEEK_LOCK_TO_FINAL", "horizonWeeks": 0},
        "K_STREAMER": {"label": "SAME_WEEK", "horizonWeeks": 0},
        "DST_STREAMER": {"label": "SAME_WEEK", "horizonWeeks": 0},
        "WAIVER": {"label": "BOUNDED_HORIZON", "horizonWeeks": 4},
        "ADD_DROP": {"label": "BOUNDED_HORIZON", "horizonWeeks": 4},
        "FAAB": {"label": "BOUNDED_HORIZON", "horizonWeeks": 4},
        "TRADE": {"label": "BOUNDED_HORIZON_ACCEPTED_ONLY", "horizonWeeks": 4},
        "TRADE_FINDER": {"label": "BOUNDED_HORIZON_ACCEPTED_ONLY", "horizonWeeks": 4},
        "TRADE_PACKAGE_SEARCH": {"label": "BOUNDED_HORIZON_ACCEPTED_ONLY", "horizonWeeks": 4},
        "DRAFT": {"label": "DEFERRED_SEASON_LONG", "horizonWeeks": None},
    }


def test_min_sample_size_matches_the_frontend_constant_exactly() -> None:
    # desktop/apps/redraft/src/decision-history-format.ts::MIN_SAMPLE_SIZE_FOR_PER_CLASS_ROLLUP
    assert MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY == 20


def test_evaluation_status_set_is_exactly_the_five_frozen_members() -> None:
    assert EVALUATION_STATUSES == frozenset(
        {"PENDING_OUTCOME", "PENDING_WINDOW", "EVALUATED", "INSUFFICIENT_DECISION_CONTEXT", "NOT_APPLICABLE"}
    )


# ---------------------------------------------------------------------------
# PENDING_OUTCOME / DRAFT
# ---------------------------------------------------------------------------


def test_no_outcome_recorded_yet_is_pending_outcome_with_no_metrics() -> None:
    record = _base_record()
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "PENDING_OUTCOME"
    assert evaluation.evaluation_metrics == {}
    assert evaluation.factual_outcome is None
    assert evaluation.issues


def test_draft_is_always_not_applicable_even_with_an_outcome_recorded() -> None:
    record = _base_record(tool="DRAFT", outcome={"outcome": "PICKED", "notes": ""})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "NOT_APPLICABLE"
    assert evaluation.evaluation_metrics == {}
    assert evaluation.outcome_window_label == "DEFERRED_SEASON_LONG"
    assert evaluation.outcome_window_horizon_weeks is None


def test_legacy_outcome_with_no_structured_detail_is_insufficient_context() -> None:
    record = _base_record(outcome={"outcome": "WON_MATCHUP", "notes": "close one"})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"
    assert evaluation.evaluation_metrics == {}
    assert "structured" in evaluation.issues[0].lower()


# ---------------------------------------------------------------------------
# START_SIT -- real fixture data, reusing the prior cycle's own real-data
# proof rather than a synthetic value.
# ---------------------------------------------------------------------------


def test_start_sit_real_fixture_evaluates_with_a_real_zero_opportunity_cost() -> None:
    real_matchup = json.loads(_REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    detail = ingest_start_sit_outcome(
        week=1,
        recommendation={"projectedTotal": None, "starters": list(real_matchup["starters"])},
        roster_state_player_ids=list(real_matchup["players"]),
        actual_matchup_entry=real_matchup,
    )
    record = _base_record(
        outcome={"outcome": "STARTER_MATCHED_RECOMMENDATION", "notes": "", "detail": detail.to_detail_dict()}
    )
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "EVALUATED"
    assert evaluation.evaluation_metrics == {"lineupOpportunityCostPoints": 0.0}
    assert evaluation.issues == ()


def test_start_sit_missing_points_data_is_insufficient_context() -> None:
    detail = {
        "kind": "START_SIT_LINEUP_V1",
        "recommendedStarterIds": ["p1"],
        "actualStarterIds": ["p2"],
        "lineupOpportunityCost": None,
    }
    record = _base_record(outcome={"outcome": "STARTER_DEVIATED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"
    assert evaluation.evaluation_metrics == {}


# ---------------------------------------------------------------------------
# WAIVER -- a real False is a real, full answer (EVALUATED), never confused
# with INSUFFICIENT_DECISION_CONTEXT.
# ---------------------------------------------------------------------------


def test_waiver_claim_not_submitted_is_evaluated_not_insufficient() -> None:
    detail = {
        "kind": "WAIVER_V1", "recommendedPlayerId": "500", "claimSubmitted": False, "claimWon": False,
        "faabPaid": None, "horizonWeeks": 4, "subsequentRosterUsageWeeks": None, "subsequentTotalPoints": None,
    }
    record = _base_record(tool="WAIVER", outcome={"outcome": "CLAIM_NOT_SUBMITTED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "EVALUATED"
    assert evaluation.evaluation_metrics["claimSubmitted"] is False
    assert evaluation.evaluation_metrics["claimWon"] is False


def test_waiver_won_but_horizon_not_yet_observed_is_pending_window() -> None:
    detail = {
        "kind": "WAIVER_V1", "recommendedPlayerId": "500", "claimSubmitted": True, "claimWon": True,
        "faabPaid": 12.0, "horizonWeeks": 4, "subsequentRosterUsageWeeks": None, "subsequentTotalPoints": None,
    }
    record = _base_record(tool="WAIVER", outcome={"outcome": "CLAIM_WON", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "PENDING_WINDOW"
    assert evaluation.evaluation_metrics == {}


def test_waiver_with_no_resolved_player_id_is_insufficient_context() -> None:
    detail = {
        "kind": "WAIVER_V1", "recommendedPlayerId": None, "claimSubmitted": None, "claimWon": None,
        "faabPaid": None, "horizonWeeks": 4, "subsequentRosterUsageWeeks": None, "subsequentTotalPoints": None,
    }
    record = _base_record(tool="WAIVER", outcome={"outcome": "NO_RECOMMENDATION", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"


# ---------------------------------------------------------------------------
# FAAB -- the two axes stay genuinely separate in the evaluation layer too.
# ---------------------------------------------------------------------------


def test_faab_keeps_player_decision_quality_and_bid_calibration_separate_at_evaluation_layer() -> None:
    detail = {
        "kind": "FAAB_V1",
        "recommendedPlayerId": "500",
        "playerDecisionQuality": {"subsequentPoints": 15.0, "subsequentRosterUsageWeeks": 1, "horizonWeeks": 4},
        "bidRangeCalibration": {
            "suggestedBidLow": 5.0, "suggestedBidHigh": 10.0, "amountBid": 15.0, "won": True,
            "actualWinningBid": 15.0, "bidWithinSuggestedRange": False, "marginVsActualWinningBid": 0.0,
        },
    }
    record = _base_record(tool="FAAB", outcome={"outcome": "CLAIM_WON", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "EVALUATED"
    metrics = evaluation.evaluation_metrics
    assert set(metrics.keys()) == {"playerDecisionQuality", "bidRangeCalibration"}
    # A good pickup (real subsequent points) alongside a bad bid range
    # (out-of-range) -- the two axes genuinely disagree, and this
    # evaluation layer must preserve that disagreement, not blend it.
    assert metrics["playerDecisionQuality"]["subsequentPoints"] == 15.0
    assert metrics["bidRangeCalibration"]["bidWithinSuggestedRange"] is False


# ---------------------------------------------------------------------------
# TRADE / TRADE_FINDER -- never scores an unobserved counterfactual.
# ---------------------------------------------------------------------------


def test_rejected_trade_is_not_applicable_never_scored() -> None:
    detail = {"kind": "TRADE_V1", "acceptanceStatus": "REJECTED", "tradeAccepted": False, "realizedRosterOutcome": None}
    record = _base_record(tool="TRADE", outcome={"outcome": "REJECTED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "NOT_APPLICABLE"
    assert evaluation.evaluation_metrics == {}


def test_accepted_trade_with_realized_outcome_is_evaluated() -> None:
    detail = {
        "kind": "TRADE_V1", "acceptanceStatus": "ACCEPTED", "tradeAccepted": True,
        "realizedRosterOutcome": {
            "horizonWeeks": 4,
            "givesSubsequentPointsByPlayer": [{"playerId": "1", "points": 10.0}],
            "receivesSubsequentPointsByPlayer": [{"playerId": "2", "points": 15.0}],
            "netSubsequentPointsDelta": 5.0,
        },
    }
    record = _base_record(tool="TRADE", outcome={"outcome": "ACCEPTED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "EVALUATED"
    assert evaluation.evaluation_metrics == {"netSubsequentPointsDeltaPoints": 5.0}


def test_accepted_trade_without_horizon_data_yet_is_pending_window() -> None:
    detail = {"kind": "TRADE_V1", "acceptanceStatus": "ACCEPTED", "tradeAccepted": True, "realizedRosterOutcome": None}
    record = _base_record(tool="TRADE", outcome={"outcome": "ACCEPTED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "PENDING_WINDOW"


def test_trade_finder_unaccepted_package_is_not_applicable() -> None:
    detail = {"kind": "TRADE_FINDER_V1", "packageDisposition": "IGNORED", "linkedTradeOutcome": None}
    record = _base_record(tool="TRADE_FINDER", outcome={"outcome": "IGNORED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "NOT_APPLICABLE"


def test_trade_finder_accepted_package_reuses_trade_evaluation() -> None:
    detail = {
        "kind": "TRADE_FINDER_V1",
        "packageDisposition": "ACCEPTED",
        "linkedTradeOutcome": {
            "kind": "TRADE_V1", "acceptanceStatus": "ACCEPTED", "tradeAccepted": True,
            "realizedRosterOutcome": {
                "horizonWeeks": 4, "givesSubsequentPointsByPlayer": [], "receivesSubsequentPointsByPlayer": [],
                "netSubsequentPointsDelta": -3.5,
            },
        },
    }
    record = _base_record(tool="TRADE_FINDER", outcome={"outcome": "ACCEPTED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "EVALUATED"
    assert evaluation.evaluation_metrics == {"netSubsequentPointsDeltaPoints": -3.5}


# ---------------------------------------------------------------------------
# STREAMER -- the one new derived number, mirroring START_SIT's own formula;
# NEVER substitutes the hindsight-best alternative into it.
# ---------------------------------------------------------------------------


def test_streamer_opportunity_cost_computed_from_recommended_vs_actual_starter() -> None:
    detail = {
        "kind": "STREAMER_V1", "position": "K", "week": 3, "recommendedPlayerId": "K1",
        "recommendedPlayerActualPoints": 9.0, "actualStarterPlayerId": "K2", "actualStarterActualPoints": 4.0,
        "priorRosterOptionPlayerId": "K2", "priorRosterOptionActualPoints": 4.0,
        "availableAlternativeIdsAtRecommendation": ["K1", "K2", "K3"],
        "bestAvailableAlternativeId": "K3", "bestAvailableAlternativeActualPoints": 20.0,
    }
    record = _base_record(tool="K_STREAMER", outcome={"outcome": "DEVIATED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "EVALUATED"
    # 9.0 (recommended) - 4.0 (actually started) = 5.0 -- NEVER computed
    # against K3's real 20.0 hindsight-best points.
    assert evaluation.evaluation_metrics["streamerOpportunityCostPoints"] == 5.0
    assert evaluation.evaluation_metrics["bestAvailableAlternativeActualPoints"] == 20.0


def test_streamer_missing_actual_points_is_insufficient_context() -> None:
    detail = {
        "kind": "STREAMER_V1", "position": "DST", "week": 3, "recommendedPlayerId": "DEN",
        "recommendedPlayerActualPoints": None, "actualStarterPlayerId": "DEN", "actualStarterActualPoints": None,
        "priorRosterOptionPlayerId": None, "priorRosterOptionActualPoints": None,
        "availableAlternativeIdsAtRecommendation": [], "bestAvailableAlternativeId": None,
        "bestAvailableAlternativeActualPoints": None,
    }
    record = _base_record(tool="DST_STREAMER", outcome={"outcome": "MATCHED", "notes": "", "detail": detail})
    evaluation = compute_outcome_evaluation(record)
    assert evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"


# ---------------------------------------------------------------------------
# Structural guarantees
# ---------------------------------------------------------------------------


def test_outcome_evaluation_rejects_an_unknown_status() -> None:
    with pytest.raises(ProspectiveOutcomeEvaluationError):
        OutcomeEvaluation(
            schema_version="v1", trace_id="t", decision_type="START_SIT", league_key="p", league_id="l",
            league_snapshot_id=None, recommendation_generated_at="now", outcome_observed_at=None,
            outcome_window_label="X", outcome_window_horizon_weeks=0, outcome_source=None,
            outcome_source_as_of=None, owner_action=None, factual_outcome=None,
            evaluation_status="BOGUS_STATUS", evaluation_metrics={}, issues=(),
        )


def test_outcome_evaluation_rejects_evaluated_status_with_no_metrics() -> None:
    with pytest.raises(ProspectiveOutcomeEvaluationError):
        OutcomeEvaluation(
            schema_version="v1", trace_id="t", decision_type="START_SIT", league_key="p", league_id="l",
            league_snapshot_id=None, recommendation_generated_at="now", outcome_observed_at=None,
            outcome_window_label="X", outcome_window_horizon_weeks=0, outcome_source=None,
            outcome_source_as_of=None, owner_action=None, factual_outcome=None,
            evaluation_status="EVALUATED", evaluation_metrics={}, issues=(),
        )


def test_outcome_evaluation_rejects_a_non_evaluated_status_carrying_a_real_metric_value() -> None:
    with pytest.raises(ProspectiveOutcomeEvaluationError):
        OutcomeEvaluation(
            schema_version="v1", trace_id="t", decision_type="START_SIT", league_key="p", league_id="l",
            league_snapshot_id=None, recommendation_generated_at="now", outcome_observed_at=None,
            outcome_window_label="X", outcome_window_horizon_weeks=0, outcome_source=None,
            outcome_source_as_of=None, owner_action=None, factual_outcome=None,
            evaluation_status="PENDING_OUTCOME", evaluation_metrics={"lineupOpportunityCostPoints": 5.0},
            issues=(),
        )


def test_compute_outcome_evaluation_is_pure_and_deterministic() -> None:
    """Calling twice on the same record returns an equal value -- the
    'derived view, never a new ledger line' design (module docstring)."""

    real_matchup = json.loads(_REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    detail = ingest_start_sit_outcome(
        week=1, recommendation={"projectedTotal": None, "starters": list(real_matchup["starters"])},
        roster_state_player_ids=list(real_matchup["players"]), actual_matchup_entry=real_matchup,
    )
    record = _base_record(outcome={"outcome": "X", "notes": "", "detail": detail.to_detail_dict()})
    first = compute_outcome_evaluation(record)
    second = compute_outcome_evaluation(record)
    assert first == second
    assert first.to_dict() == second.to_dict()


def test_compute_outcome_evaluation_never_mutates_the_original_record() -> None:
    record = _base_record(outcome={"outcome": "X", "notes": "", "detail": {"kind": "START_SIT_LINEUP_V1", "lineupOpportunityCost": 1.0}})
    before = record.to_json_row()
    compute_outcome_evaluation(record)
    after = record.to_json_row()
    assert before == after


def test_compute_outcome_evaluation_signature_accepts_no_current_state_or_io_parameter() -> None:
    """Structural (not conventional) hindsight-leakage defense: the real
    function signature itself is inspected, not merely trusted from a
    docstring."""

    import inspect

    from src.services.prospective_outcome_evaluation_v1_service import compute_outcome_evaluation as fn

    parameters = list(inspect.signature(fn).parameters)
    assert parameters == ["record"]
    forbidden_fragments = ("current", "live", "now_", "today", "client", "http")
    for name in parameters:
        assert not any(fragment in name.lower() for fragment in forbidden_fragments)


def test_assert_no_current_state_parameter_actually_catches_a_violation() -> None:
    """Proves the structural guard itself is a real check, not a no-op --
    a function with a forbidden parameter name is rejected."""

    from src.services.prospective_outcome_evaluation_v1_service import _assert_no_current_state_parameter

    def bad_function(record, current_roster_player_ids):
        return record, current_roster_player_ids

    with pytest.raises(ProspectiveOutcomeEvaluationError):
        _assert_no_current_state_parameter(bad_function)


def test_outcome_evaluation_to_dict_uses_the_canonical_contract_field_names() -> None:
    record = _base_record()
    evaluation = compute_outcome_evaluation(record)
    payload = evaluation.to_dict()
    assert set(payload) == {
        "schemaVersion", "traceId", "decisionType", "leagueKey", "leagueId", "leagueSnapshotId",
        "recommendationGeneratedAt", "outcomeObservedAt", "outcomeWindow", "outcomeSource",
        "outcomeSourceAsOf", "ownerAction", "factualOutcome", "evaluationStatus", "evaluationMetrics",
        "issues",
    }
    assert payload["outcomeWindow"] == {"label": "SAME_WEEK_LOCK_TO_FINAL", "horizonWeeks": 0}


def test_provenance_fields_round_trip_from_record_outcome_into_the_evaluation(tmp_path) -> None:
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1", "p2"],
        recommendation={"starters": ["p1"]},
    )
    record_outcome(
        tmp_path, "profile-1", trace.trace_id, outcome="STARTER_MATCHED_RECOMMENDATION",
        detail={"kind": "START_SIT_LINEUP_V1", "lineupOpportunityCost": 0.0},
        outcome_source="SLEEPER", outcome_source_as_of="2026-09-14T12:00:00+00:00",
        outcome_observed_at="2026-09-13T23:00:00+00:00",
    )
    reloaded = load_decision_traces(tmp_path, "profile-1")[0]
    evaluation = compute_outcome_evaluation(reloaded)
    assert evaluation.outcome_source == "SLEEPER"
    assert evaluation.outcome_source_as_of == "2026-09-14T12:00:00+00:00"
    assert evaluation.outcome_observed_at == "2026-09-13T23:00:00+00:00"
    assert evaluation.evaluation_status == "EVALUATED"
