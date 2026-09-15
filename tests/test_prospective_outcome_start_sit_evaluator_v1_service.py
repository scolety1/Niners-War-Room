from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_ingestion_v1_service import ingest_start_sit_outcome
from src.services.prospective_outcome_source_adapter_v1_service import RealizedOutcomeFetch
from src.services.prospective_outcome_start_sit_evaluator_v1_service import (
    StartSitEvaluatorResult,
    evaluate_start_sit,
    summarize_start_sit_evaluations,
)

_REAL_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "codex" / "prospective_outcome_v1" / "real_data_v1"
    / "fantasy_gamers_week1_2026_owner_matchup.json"
)


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trace-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=("p1", "p2", "p3"),
        free_agent_state_player_ids=None, recommendation={"starters": ["p1"]}, alternatives=(),
        recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _record_with_start_sit_outcome(
    *, roster_state_player_ids, recommended_starters, actual_matchup_entry
) -> DecisionTraceRecord:
    recommendation = {"starters": recommended_starters, "projectedTotal": None}
    detail = ingest_start_sit_outcome(
        week=1, recommendation=recommendation, roster_state_player_ids=roster_state_player_ids,
        actual_matchup_entry=actual_matchup_entry,
    )
    return _base_record(
        roster_state_player_ids=tuple(roster_state_player_ids), recommendation=recommendation,
        outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()},
    )


# ---------------------------------------------------------------------------
# The base OutcomeEvaluation contract is reused, never bypassed.
# ---------------------------------------------------------------------------


def test_no_outcome_recorded_yet_carries_no_fabricated_numbers() -> None:
    record = _base_record()
    result = evaluate_start_sit(record)
    assert result.evaluation.evaluation_status == "PENDING_OUTCOME"
    assert result.lineup_opportunity_cost_points is None
    assert result.recommended_player_realized_points is None
    assert result.owner_selected_player_realized_points is None
    assert result.best_legal_alternative_player_id is None


def test_insufficient_decision_context_is_never_a_fabricated_regret_number() -> None:
    record = _base_record(outcome={"outcome": "WON", "notes": "no structured detail"})
    result = evaluate_start_sit(record)
    assert result.evaluation.evaluation_status == "INSUFFICIENT_DECISION_CONTEXT"
    assert result.lineup_opportunity_cost_points is None
    assert result.best_legal_alternative_player_id is None
    assert result.best_legal_alternative_actual_points is None
    assert result.issues  # a real, honest disclosure, not silence


def test_wrong_decision_type_is_rejected() -> None:
    record = _base_record(tool="WAIVER")
    with pytest.raises(ValueError):
        evaluate_start_sit(record)


# ---------------------------------------------------------------------------
# Realized-points decomposition -- pure arithmetic over already-stored data.
# ---------------------------------------------------------------------------


def test_realized_points_decomposition_matches_the_stored_opportunity_cost() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 40.0, "starters": ["A", "C"],
        "players_points": {"A": 10.0, "B": 5.0, "C": 30.0},
    }
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=["A", "B", "C"], recommended_starters=["A", "B"],
        actual_matchup_entry=matchup_entry,
    )
    result = evaluate_start_sit(record)
    assert result.evaluation.evaluation_status == "EVALUATED"
    # Recommended-only (B, benched by owner) realized 5.0; owner-only (C,
    # started instead) realized 30.0 -- opportunity cost = 5 - 30 = -25.
    assert result.recommended_player_realized_points == 5.0
    assert result.owner_selected_player_realized_points == 30.0
    assert result.lineup_opportunity_cost_points == -25.0
    assert result.recommended_player_realized_points - result.owner_selected_player_realized_points == (
        result.lineup_opportunity_cost_points
    )


# ---------------------------------------------------------------------------
# Best-legal-alternative -- the core "regret vs. legal recommendation-time
# alternatives" guarantee: never a player who wasn't rostered at lock time.
# ---------------------------------------------------------------------------


def test_best_legal_alternative_ignores_a_player_not_rostered_at_recommendation_time() -> None:
    # D scored the most of anyone in the raw matchup payload, but D was NOT
    # on roster_state_player_ids at lock time (e.g. acquired later, or
    # simply never on this roster) -- it must never be treated as a legal
    # alternative, no matter how well it scored.
    matchup_entry = {
        "roster_id": 9, "points": 10.0, "starters": ["A"],
        "players_points": {"A": 10.0, "B": 4.0, "C": 6.0, "D": 99.0},
    }
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=["A", "B", "C"], recommended_starters=["A"],
        actual_matchup_entry=matchup_entry,
    )
    detail = record.outcome["detail"]
    assert "D" not in detail["eligibleAlternativeIdsAtLock"]

    result = evaluate_start_sit(
        record,
        matchup_fetch=RealizedOutcomeFetch(source="SLEEPER", league_id="lg1", fetched_at_utc="now", payload=matchup_entry),
    )
    assert result.best_legal_alternative_player_id in ("B", "C")
    assert result.best_legal_alternative_actual_points == 6.0  # C, the best of the two LEGAL bench options
    assert result.best_legal_alternative_player_id != "D"


def test_best_legal_alternative_excludes_players_already_used_by_either_lineup() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 20.0, "starters": ["A", "C"],
        "players_points": {"A": 10.0, "B": 3.0, "C": 20.0},
    }
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=["A", "B", "C"], recommended_starters=["A", "B"],
        actual_matchup_entry=matchup_entry,
    )
    result = evaluate_start_sit(
        record,
        matchup_fetch=RealizedOutcomeFetch(source="SLEEPER", league_id="lg1", fetched_at_utc="now", payload=matchup_entry),
    )
    # C was already actually started (owner's real deviation) -- it is not
    # a "held in reserve, unused" alternative, so it must not double-count
    # as the best untapped bench option.
    assert result.best_legal_alternative_player_id is None or result.best_legal_alternative_player_id != "C"


def test_no_matchup_fetch_supplied_leaves_best_alternative_honestly_none_with_an_issue() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 10.0, "starters": ["A"],
        "players_points": {"A": 10.0, "B": 4.0, "C": 6.0},
    }
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=["A", "B", "C"], recommended_starters=["A"], actual_matchup_entry=matchup_entry,
    )
    result = evaluate_start_sit(record)  # no matchup_fetch
    assert result.best_legal_alternative_player_id is None
    assert result.best_legal_alternative_actual_points is None
    assert any("bestLegalAlternative" in issue for issue in result.issues)
    # The primary metric is still real and unaffected.
    assert result.lineup_opportunity_cost_points is not None


# ---------------------------------------------------------------------------
# Purity / hindsight-leakage
# ---------------------------------------------------------------------------


def test_evaluate_start_sit_signature_accepts_no_current_state_parameter() -> None:
    forbidden = ("current", "live", "now_", "today", "latest_roster", "latest_free_agent")
    for name in inspect.signature(evaluate_start_sit).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_evaluate_start_sit_is_pure_given_the_same_inputs() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 10.0, "starters": ["A"],
        "players_points": {"A": 10.0, "B": 4.0, "C": 6.0},
    }
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=["A", "B", "C"], recommended_starters=["A"], actual_matchup_entry=matchup_entry,
    )
    fetch = RealizedOutcomeFetch(source="SLEEPER", league_id="lg1", fetched_at_utc="now", payload=matchup_entry)
    first = evaluate_start_sit(record, matchup_fetch=fetch)
    second = evaluate_start_sit(record, matchup_fetch=fetch)
    assert first == second


def test_a_later_contradictory_matchup_fetch_never_reaches_back_into_an_already_returned_result() -> None:
    matchup_entry = {
        "roster_id": 9, "points": 10.0, "starters": ["A"],
        "players_points": {"A": 10.0, "B": 4.0, "C": 6.0},
    }
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=["A", "B", "C"], recommended_starters=["A"], actual_matchup_entry=matchup_entry,
    )
    fetch = RealizedOutcomeFetch(source="SLEEPER", league_id="lg1", fetched_at_utc="now", payload=matchup_entry)
    earlier_result = evaluate_start_sit(record, matchup_fetch=fetch)
    frozen_alt_points = earlier_result.best_legal_alternative_actual_points

    # A later, contradictory "current" fetch is built (simulating a real
    # roster move / a corrected re-fetch happening afterward) -- this must
    # never retroactively alter `earlier_result`, since results are frozen
    # dataclasses and no function mutates a previously-returned one.
    later_fetch = RealizedOutcomeFetch(
        source="SLEEPER", league_id="lg1", fetched_at_utc="later",
        payload={"roster_id": 9, "points": 999.0, "starters": ["Z"], "players_points": {"Z": 999.0}},
    )
    evaluate_start_sit(record, matchup_fetch=later_fetch)  # a fresh, independent call

    assert earlier_result.best_legal_alternative_actual_points == frozen_alt_points == 6.0


# ---------------------------------------------------------------------------
# Real fixture data (the same real, committed Week 1 2026 Fantasy Gamers
# fixture Worker 1 already used -- reused, not re-pulled).
# ---------------------------------------------------------------------------


def test_real_fixture_produces_a_real_zero_regret_since_actual_matched_recommendation() -> None:
    real_matchup = json.loads(_REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    # Mechanism-demonstration baseline, same as Worker 1/the prior cycle's
    # own real demo script: recommend exactly what was actually started, so
    # the real opportunity cost is a real, verified zero.
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=list(real_matchup["players"]),
        recommended_starters=list(real_matchup["starters"]),
        actual_matchup_entry=real_matchup,
    )
    fetch = RealizedOutcomeFetch(source="SLEEPER", league_id="1312983576827920384", fetched_at_utc="now", payload=real_matchup)
    result = evaluate_start_sit(record, matchup_fetch=fetch)
    assert result.evaluation.evaluation_status == "EVALUATED"
    assert result.lineup_opportunity_cost_points == 0.0
    # Real bench players existed (players - starters); best-legal-alternative
    # is computed for real from real players_points.
    bench = set(real_matchup["players"]) - set(real_matchup["starters"])
    assert bench  # the real roster genuinely had bench players
    assert result.best_legal_alternative_player_id in bench
    expected_best = max(bench, key=lambda pid: real_matchup["players_points"][pid])
    assert result.best_legal_alternative_actual_points == real_matchup["players_points"][expected_best]


# ---------------------------------------------------------------------------
# Aggregation -- gated by the contract's own minimum-sample rule.
# ---------------------------------------------------------------------------


def _evaluated_result(cost: float) -> StartSitEvaluatorResult:
    matchup_entry = {"roster_id": 9, "points": 10.0, "starters": ["A"], "players_points": {"A": 10.0}}
    record = _record_with_start_sit_outcome(
        roster_state_player_ids=["A"], recommended_starters=["A"], actual_matchup_entry=matchup_entry,
    )
    result = evaluate_start_sit(record)
    # Force a known opportunity cost via a fresh record for determinism.
    object.__setattr__(result, "lineup_opportunity_cost_points", cost)
    return result


def test_summary_reports_not_enough_data_below_the_minimum_sample_size() -> None:
    results = [_evaluated_result(1.0) for _ in range(5)]
    summary = summarize_start_sit_evaluations(results)
    assert summary["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
    assert "meanLineupOpportunityCostPoints" not in summary


def test_summary_computes_a_real_mean_at_or_above_the_minimum_sample_size() -> None:
    results = [_evaluated_result(2.0) for _ in range(20)]
    summary = summarize_start_sit_evaluations(results)
    assert summary["summaryStatus"] == "SUMMARIZED"
    assert summary["meanLineupOpportunityCostPoints"] == 2.0
    assert summary["evaluatedSampleSize"] == 20
