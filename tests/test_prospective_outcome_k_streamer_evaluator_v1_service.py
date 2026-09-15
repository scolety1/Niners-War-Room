from __future__ import annotations

import inspect

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_ingestion_v1_service import ingest_streamer_outcome
from src.services.prospective_outcome_k_streamer_evaluator_v1_service import (
    KStreamerEvaluatorResult,
    evaluate_k_streamer,
    summarize_k_streamer_evaluations,
)
from src.services.prospective_outcome_dst_streamer_evaluator_v1_service import evaluate_dst_streamer


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="k-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="K_STREAMER",
        engine_version="v1", data_versions={}, roster_state_player_ids=("K1", "K0"),
        free_agent_state_player_ids=None,
        recommendation={"playerName": "Recommended Kicker", "team": "SF", "ecr": 5.0, "tier": 1, "recommendation": "ADD"},
        alternatives=(), recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _record_with_k_outcome(
    *, recommended="K1", prior="K0", alternatives=("K2",), matchup_entry, tool="K_STREAMER", position="K"
) -> DecisionTraceRecord:
    detail = ingest_streamer_outcome(
        position=position, week=1, recommended_player_id=recommended, prior_roster_option_player_id=prior,
        available_alternative_ids_at_recommendation=alternatives, actual_matchup_entry=matchup_entry,
    )
    return _base_record(
        tool=tool,
        outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()},
    )


# ---------------------------------------------------------------------------
# Base metrics -- read verbatim, no re-derivation.
# ---------------------------------------------------------------------------


def test_evaluated_k_streamer_reports_real_metrics() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 20.0, "starters": ["K1"],
        "players_points": {"K1": 10.0, "K0": 4.0, "K2": 6.0},
    }
    record = _record_with_k_outcome(matchup_entry=matchup_entry)
    result = evaluate_k_streamer(record)
    assert result.evaluation.evaluation_status == "EVALUATED"
    assert result.recommended_player_actual_points == 10.0
    assert result.actual_starter_actual_points == 10.0  # owner started the recommended K
    assert result.current_option_player_id == "K0"
    assert result.current_option_actual_points == 4.0
    assert result.regret_vs_actual_starter_points == 0.0  # recommended == actual starter
    # replacement-level delta: recommended (10.0) vs the prior K0 option (4.0)
    assert result.replacement_level_delta_points == 6.0
    assert result.best_available_alternative_id == "K2"
    assert result.best_available_alternative_actual_points == 6.0


def test_replacement_level_delta_never_substitutes_for_regret() -> None:
    """The contract's explicit rule (Section 5, rule 4): a hindsight-best or
    alternate comparison is reported alongside the primary metric, never
    swapped into it."""

    matchup_entry = {
        "roster_id": 9, "points": 20.0, "starters": ["K5"],  # owner deviated to a real, available alternative
        "players_points": {"K1": 10.0, "K0": 4.0, "K5": 30.0},
    }
    record = _record_with_k_outcome(recommended="K1", prior="K0", alternatives=("K5",), matchup_entry=matchup_entry)
    result = evaluate_k_streamer(record)
    # Regret vs actual starter uses K5 (30.0), replacement delta uses K0 (4.0) --
    # two different real numbers, neither substituted for the other.
    assert result.regret_vs_actual_starter_points == 10.0 - 30.0
    assert result.replacement_level_delta_points == 10.0 - 4.0
    assert result.regret_vs_actual_starter_points != result.replacement_level_delta_points


def test_no_outcome_yet_carries_no_fabricated_numbers() -> None:
    record = _base_record()
    result = evaluate_k_streamer(record)
    assert result.evaluation.evaluation_status == "PENDING_OUTCOME"
    assert result.recommended_player_actual_points is None
    assert result.replacement_level_delta_points is None


def test_missing_actual_points_is_insufficient_decision_context() -> None:
    matchup_entry = {"roster_id": 9, "points": 0.0, "starters": [], "players_points": {}}
    record = _record_with_k_outcome(matchup_entry=matchup_entry)
    result = evaluate_k_streamer(record)
    assert result.evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"
    assert result.regret_vs_actual_starter_points is None


# ---------------------------------------------------------------------------
# Never a hindsight-best comparison, never an unavailable alternative.
# ---------------------------------------------------------------------------


def test_best_alternative_only_drawn_from_frozen_available_alternatives() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 20.0, "starters": ["K1"],
        "players_points": {"K1": 10.0, "K0": 4.0, "K2": 6.0, "K99": 999.0},  # K99 never a frozen alternative
    }
    record = _record_with_k_outcome(alternatives=("K2",), matchup_entry=matchup_entry)
    result = evaluate_k_streamer(record)
    assert result.best_available_alternative_id != "K99"
    assert result.best_available_alternative_id == "K2"


# ---------------------------------------------------------------------------
# Wrong tool / wrong position guards -- structural cross-contamination
# defense (also see the DST test file's own reverse-direction tests).
# ---------------------------------------------------------------------------


def test_wrong_tool_is_rejected() -> None:
    record = _base_record(tool="DST_STREAMER")
    with pytest.raises(ValueError):
        evaluate_k_streamer(record)


def test_a_dst_position_detail_under_the_k_streamer_tool_is_rejected() -> None:
    """A defensive second gate: even if a trace's `tool` string were
    K_STREAMER, a detail whose own `position` field says DST must never be
    silently evaluated as a K result."""

    matchup_entry = {"roster_id": 9, "points": 6.0, "starters": ["NE"], "players_points": {"NE": 6.0}}
    detail = ingest_streamer_outcome(
        position="DST", week=1, recommended_player_id="NE", prior_roster_option_player_id=None,
        available_alternative_ids_at_recommendation=(), actual_matchup_entry=matchup_entry,
    )
    record = _base_record(
        tool="K_STREAMER", outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()}
    )
    with pytest.raises(ValueError):
        evaluate_k_streamer(record)


def test_a_k_trace_evaluated_through_the_dst_evaluator_is_rejected() -> None:
    """K/DST are genuinely separate code paths -- a K_STREAMER trace passed
    to the DST evaluator function is rejected outright, never silently
    evaluated as a DST result."""

    matchup_entry = {"roster_id": 9, "points": 10.0, "starters": ["K1"], "players_points": {"K1": 10.0}}
    record = _record_with_k_outcome(matchup_entry=matchup_entry)
    with pytest.raises(ValueError):
        evaluate_dst_streamer(record)


# ---------------------------------------------------------------------------
# Real-vs-fixture data discipline: real Week 1 2026 Fantasy Gamers points
# exist for this owner's roster, but this fixture's raw ids carry no real
# position label -- a real K identity was NOT independently confirmed
# within this pass's scope (no positions crosswalk was fetched), so this
# test is honestly built from a REALISTIC, clearly-labeled FIXTURE, not
# claimed as real K data. See the DST test file for the real, position-
# unambiguous ("NE", a real Sleeper DST team code) counterpart.
# ---------------------------------------------------------------------------


def test_realistic_fixture_k_streamer_pipeline() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 8.0, "starters": ["K_REC"],
        "players_points": {"K_REC": 8.0, "K_PRIOR": 3.0, "K_ALT": 5.0},
    }
    record = _record_with_k_outcome(
        recommended="K_REC", prior="K_PRIOR", alternatives=("K_ALT",), matchup_entry=matchup_entry,
    )
    result = evaluate_k_streamer(record)
    assert result.evaluation.evaluation_status == "EVALUATED"
    assert result.regret_vs_actual_starter_points == 0.0
    assert result.replacement_level_delta_points == 5.0


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_k_streamer_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_k_streamer).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_evaluate_k_streamer_is_pure_given_the_same_inputs() -> None:
    matchup_entry = {"roster_id": 9, "points": 10.0, "starters": ["K1"], "players_points": {"K1": 10.0, "K0": 4.0}}
    record = _record_with_k_outcome(matchup_entry=matchup_entry)
    assert evaluate_k_streamer(record) == evaluate_k_streamer(record)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _evaluated_result(regret: float, replacement: float) -> KStreamerEvaluatorResult:
    matchup_entry = {"roster_id": 9, "points": 10.0, "starters": ["K1"], "players_points": {"K1": 10.0, "K0": 4.0}}
    record = _record_with_k_outcome(matchup_entry=matchup_entry)
    result = evaluate_k_streamer(record)
    object.__setattr__(result, "regret_vs_actual_starter_points", regret)
    object.__setattr__(result, "replacement_level_delta_points", replacement)
    return result


def test_summary_reports_not_enough_data_below_the_minimum_sample_size() -> None:
    results = [_evaluated_result(1.0, 2.0) for _ in range(5)]
    summary = summarize_k_streamer_evaluations(results)
    assert summary["regretVsActualStarter"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert summary["replacementLevelDelta"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"


def test_summary_computes_real_means_at_or_above_the_minimum_sample_size() -> None:
    results = [_evaluated_result(2.0, 4.0) for _ in range(20)]
    summary = summarize_k_streamer_evaluations(results)
    assert summary["regretVsActualStarter"]["summaryStatus"] == "SUMMARIZED"
    assert summary["regretVsActualStarter"]["meanRegretPoints"] == 2.0
    assert summary["replacementLevelDelta"]["meanReplacementLevelDeltaPoints"] == 4.0
