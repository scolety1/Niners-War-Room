from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_ingestion_v1_service import ingest_streamer_outcome
from src.services.prospective_outcome_dst_streamer_evaluator_v1_service import (
    DstStreamerEvaluatorResult,
    evaluate_dst_streamer,
    summarize_dst_streamer_evaluations,
)
from src.services.prospective_outcome_k_streamer_evaluator_v1_service import evaluate_k_streamer

_REAL_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "codex" / "prospective_outcome_v1" / "real_data_v1"
    / "fantasy_gamers_week1_2026_owner_matchup.json"
)


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="dst-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="DST_STREAMER",
        engine_version="v1", data_versions={}, roster_state_player_ids=("NE", "SF"),
        free_agent_state_player_ids=None,
        recommendation={"playerName": "New England", "team": "NE", "ecr": 5.0, "tier": 1, "recommendation": "ADD"},
        alternatives=(), recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _record_with_dst_outcome(
    *, recommended="NE", prior="SF", alternatives=("BUF",), matchup_entry, tool="DST_STREAMER", position="DST"
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


def test_evaluated_dst_streamer_reports_real_metrics() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 20.0, "starters": ["NE"],
        "players_points": {"NE": 12.0, "SF": 2.0, "BUF": 8.0},
    }
    record = _record_with_dst_outcome(matchup_entry=matchup_entry)
    result = evaluate_dst_streamer(record)
    assert result.evaluation.evaluation_status == "EVALUATED"
    assert result.recommended_player_actual_points == 12.0
    assert result.actual_starter_actual_points == 12.0
    assert result.current_option_player_id == "SF"
    assert result.current_option_actual_points == 2.0
    assert result.regret_vs_actual_starter_points == 0.0
    assert result.replacement_level_delta_points == 10.0
    assert result.best_available_alternative_id == "BUF"


def test_replacement_level_delta_never_substitutes_for_regret() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 20.0, "starters": ["KC"],  # owner deviated to a real, available alternative
        "players_points": {"NE": 12.0, "SF": 2.0, "KC": 25.0},
    }
    record = _record_with_dst_outcome(recommended="NE", prior="SF", alternatives=("KC",), matchup_entry=matchup_entry)
    result = evaluate_dst_streamer(record)
    assert result.regret_vs_actual_starter_points == 12.0 - 25.0
    assert result.replacement_level_delta_points == 12.0 - 2.0
    assert result.regret_vs_actual_starter_points != result.replacement_level_delta_points


def test_no_outcome_yet_carries_no_fabricated_numbers() -> None:
    record = _base_record()
    result = evaluate_dst_streamer(record)
    assert result.evaluation.evaluation_status == "PENDING_OUTCOME"
    assert result.replacement_level_delta_points is None


# ---------------------------------------------------------------------------
# Cross-contamination guards (reverse direction of the K test file).
# ---------------------------------------------------------------------------


def test_wrong_tool_is_rejected() -> None:
    record = _base_record(tool="K_STREAMER")
    with pytest.raises(ValueError):
        evaluate_dst_streamer(record)


def test_a_k_position_detail_under_the_dst_streamer_tool_is_rejected() -> None:
    matchup_entry = {"roster_id": 9, "points": 10.0, "starters": ["K1"], "players_points": {"K1": 10.0}}
    detail = ingest_streamer_outcome(
        position="K", week=1, recommended_player_id="K1", prior_roster_option_player_id=None,
        available_alternative_ids_at_recommendation=(), actual_matchup_entry=matchup_entry,
    )
    record = _base_record(
        tool="DST_STREAMER", outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()}
    )
    with pytest.raises(ValueError):
        evaluate_dst_streamer(record)


def test_a_dst_trace_evaluated_through_the_k_evaluator_is_rejected() -> None:
    matchup_entry = {"roster_id": 9, "points": 6.0, "starters": ["NE"], "players_points": {"NE": 6.0}}
    record = _record_with_dst_outcome(matchup_entry=matchup_entry)
    with pytest.raises(ValueError):
        evaluate_k_streamer(record)


def test_k_and_dst_evaluators_are_independent_modules_not_a_shared_function() -> None:
    """Structural proof, not just behavioral: the two evaluate_* callables
    come from two different modules and are two different function
    objects -- neither wraps or calls the other."""

    import src.services.prospective_outcome_k_streamer_evaluator_v1_service as k_module
    import src.services.prospective_outcome_dst_streamer_evaluator_v1_service as dst_module

    assert k_module.__name__ != dst_module.__name__
    assert evaluate_k_streamer.__module__ != evaluate_dst_streamer.__module__
    k_source = inspect.getsource(k_module)
    dst_source = inspect.getsource(dst_module)
    assert "evaluate_dst_streamer" not in k_source
    assert "evaluate_k_streamer" not in dst_source


# ---------------------------------------------------------------------------
# Real data: the real, committed Week 1 2026 Fantasy Gamers fixture. "NE" is
# a real Sleeper DST team-code id (unambiguous, per the schema module's own
# documented precedent) -- a real, non-fabricated real DST exercise.
# ---------------------------------------------------------------------------


def test_real_fixture_produces_a_real_zero_regret_dst_result() -> None:
    real_matchup = json.loads(_REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "NE" in real_matchup["starters"]  # real, confirmed DST starter that week
    record = _record_with_dst_outcome(
        recommended="NE", prior=None, alternatives=(), matchup_entry=real_matchup,
    )
    result = evaluate_dst_streamer(record)
    assert result.evaluation.evaluation_status == "EVALUATED"
    assert result.recommended_player_actual_points == real_matchup["players_points"]["NE"]
    assert result.actual_starter_actual_points == real_matchup["players_points"]["NE"]
    assert result.regret_vs_actual_starter_points == 0.0


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_dst_streamer_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_dst_streamer).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_evaluate_dst_streamer_is_pure_given_the_same_inputs() -> None:
    matchup_entry = {"roster_id": 9, "points": 12.0, "starters": ["NE"], "players_points": {"NE": 12.0, "SF": 2.0}}
    record = _record_with_dst_outcome(matchup_entry=matchup_entry)
    assert evaluate_dst_streamer(record) == evaluate_dst_streamer(record)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _evaluated_result(regret: float, replacement: float) -> DstStreamerEvaluatorResult:
    matchup_entry = {"roster_id": 9, "points": 12.0, "starters": ["NE"], "players_points": {"NE": 12.0, "SF": 2.0}}
    record = _record_with_dst_outcome(matchup_entry=matchup_entry)
    result = evaluate_dst_streamer(record)
    object.__setattr__(result, "regret_vs_actual_starter_points", regret)
    object.__setattr__(result, "replacement_level_delta_points", replacement)
    return result


def test_summary_reports_not_enough_data_below_the_minimum_sample_size() -> None:
    results = [_evaluated_result(1.0, 2.0) for _ in range(5)]
    summary = summarize_dst_streamer_evaluations(results)
    assert summary["regretVsActualStarter"]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"


def test_summary_computes_real_means_at_or_above_the_minimum_sample_size() -> None:
    results = [_evaluated_result(2.0, 4.0) for _ in range(20)]
    summary = summarize_dst_streamer_evaluations(results)
    assert summary["regretVsActualStarter"]["summaryStatus"] == "SUMMARIZED"
    assert summary["regretVsActualStarter"]["meanRegretPoints"] == 2.0
    assert summary["replacementLevelDelta"]["meanReplacementLevelDeltaPoints"] == 4.0
