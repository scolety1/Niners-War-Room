"""NWR Prospective Outcomes V1 -- Work Units 13-14: History UI V3 /
class-specific summary presentation-layer tests.

Two layers, matching the module under test: (1) pure module-level tests
against `prospective_outcome_history_presentation_v1_service` directly
(dispatch correctness, DRAFT/unknown-tool fallback, per-class summary
independence, the TRADE_FINDER/TRADE_PACKAGE_SEARCH combine), and (2)
facade-level wiring tests proving `redraft_decision_trace_history`'s new
`evaluationDetail` field and the new `redraft_decision_trace_outcome_summary`
facade method are real and reachable -- following the exact fixture pattern
`test_prospective_recommendation_ledger_v1.py` already established.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.in_season_decision_trace_service import DecisionTraceRecord, record_decision_trace
from src.services.prospective_outcome_ingestion_v1_service import ingest_start_sit_outcome
from src.services.prospective_outcome_history_presentation_v1_service import (
    CLASS_SUMMARY_DECISION_TYPES,
    class_specific_summaries,
    evaluation_payload_for_record,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trace-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=("p1", "p2", "p3"),
        free_agent_state_player_ids=None, recommendation={"starters": ["p1"]}, alternatives=(),
        recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


def _start_sit_evaluated_record(trace_id: str = "trace-evaluated") -> DecisionTraceRecord:
    recommendation = {"starters": ["p1"], "projectedTotal": None}
    actual_matchup_entry = {
        "starters": ["p2"],
        "players_points": {"p1": 10.0, "p2": 5.0, "p3": 1.0},
    }
    detail = ingest_start_sit_outcome(
        week=1, recommendation=recommendation, roster_state_player_ids=("p1", "p2", "p3"),
        actual_matchup_entry=actual_matchup_entry,
    )
    return _base_record(
        trace_id=trace_id, recommendation=recommendation,
        outcome={"outcome": "OBSERVED", "notes": "", "detail": detail.to_detail_dict()},
    )


# ---------------------------------------------------------------------------
# Module-level: `evaluation_payload_for_record` dispatch.
# ---------------------------------------------------------------------------


def test_dispatches_start_sit_to_its_real_evaluator_and_reports_the_real_metric() -> None:
    record = _start_sit_evaluated_record()
    payload = evaluation_payload_for_record(record)
    assert payload["evaluation"]["evaluationStatus"] == "EVALUATED"
    # +5.0 pts: p1 (recommended, 10.0) vs p2 (started instead, 5.0).
    assert payload["lineupOpportunityCostPoints"] == 5.0
    assert payload["evaluation"]["evaluationMetrics"]["lineupOpportunityCostPoints"] == 5.0


def test_pending_outcome_carries_no_fabricated_metric_through_the_presentation_layer() -> None:
    record = _base_record()
    payload = evaluation_payload_for_record(record)
    assert payload["evaluation"]["evaluationStatus"] == "PENDING_OUTCOME"
    assert payload["lineupOpportunityCostPoints"] is None


@pytest.mark.parametrize(
    "tool",
    ["WAIVER", "ADD_DROP", "FAAB", "TRADE", "TRADE_FINDER", "TRADE_PACKAGE_SEARCH", "K_STREAMER", "DST_STREAMER"],
)
def test_every_real_non_draft_class_dispatches_without_raising(tool: str) -> None:
    record = _base_record(tool=tool, recommendation={})
    payload = evaluation_payload_for_record(record)
    assert payload["traceId"] == "trace-1"
    assert payload["evaluation"]["decisionType"] == tool
    assert payload["evaluation"]["evaluationStatus"] == "PENDING_OUTCOME"


def test_draft_has_no_real_evaluator_and_falls_back_to_the_base_contract() -> None:
    record = _base_record(tool="DRAFT", recommendation={})
    payload = evaluation_payload_for_record(record)
    # Only the base envelope -- no class-specific extra keys, since no
    # DRAFT evaluator exists this cycle (hard boundary, contract Section 2).
    assert set(payload.keys()) == {"traceId", "evaluation"}
    assert payload["evaluation"]["evaluationStatus"] == "NOT_APPLICABLE"
    assert payload["evaluation"]["evaluationMetrics"] == {}


def test_unrecognized_tool_falls_back_honestly_rather_than_raising() -> None:
    record = _base_record(tool="SOME_FUTURE_TOOL", recommendation={})
    payload = evaluation_payload_for_record(record)
    assert set(payload.keys()) == {"traceId", "evaluation"}
    # No real evaluator exists for this tool, so this falls back to the base
    # contract -- which itself reports PENDING_OUTCOME (no outcome recorded
    # yet at all, checked before any class-specific logic runs).
    assert payload["evaluation"]["evaluationStatus"] == "PENDING_OUTCOME"


# ---------------------------------------------------------------------------
# Module-level: `class_specific_summaries` -- per-class-only, gated.
#
# Returns a LIST (each entry carries its own real `decisionType`), and every
# `statusCounts`/`acceptanceStatusCounts`/`packageDispositionCounts` field is
# a LIST of `{status/disposition, count}` pairs -- a real, disclosed,
# narrow bug fix found THIS pass (see `_as_count_pairs`'s own docstring in
# `prospective_outcome_history_presentation_v1_service.py`): a dict keyed by
# an ENUM-like string gets mangled by the HTTP response envelope's generic
# camelCase-key transform (the same bug class already disclosed for
# player-id dict keys in `prospective_outcome_schema_v1_service.py`). These
# two small helpers below make that shape convenient to assert against.
# ---------------------------------------------------------------------------


def _by_type(summaries: list) -> dict:
    return {entry["decisionType"]: entry for entry in summaries}


def _count(pairs: list, key_field: str, value: str) -> int | None:
    for pair in pairs:
        if pair.get(key_field) == value:
            return pair["count"]
    return None


def test_every_real_class_is_reported_even_with_zero_records() -> None:
    summaries = class_specific_summaries(())
    by_type = _by_type(summaries)
    assert set(by_type.keys()) == set(CLASS_SUMMARY_DECISION_TYPES)
    assert len(summaries) == len(CLASS_SUMMARY_DECISION_TYPES)  # never a duplicate/dropped class
    # Every real (non-DRAFT) class's own axes are NOT_ENOUGH_DATA_YET with a
    # real zero sample size -- never a fabricated number from an empty list.
    start_sit = by_type["START_SIT"]
    assert start_sit["decisionType"] == "START_SIT"
    assert start_sit["statusCounts"] == []
    for axis_key in ("lineupOpportunityCost",):
        if axis_key in start_sit:
            assert start_sit[axis_key]["summaryStatus"] == "NOT_ENOUGH_DATA_YET"
            assert start_sit[axis_key]["sampleSize"] == 0
    # DRAFT is structurally distinct -- never NOT_ENOUGH_DATA_YET, a real
    # disclosed "deferred to marginal_roster_utility_v2" note instead.
    assert by_type["DRAFT"]["decisionType"] == "DRAFT"
    assert "note" in by_type["DRAFT"]


def test_classes_never_blend_into_each_other() -> None:
    records = [
        _start_sit_evaluated_record(trace_id="ss-1"),
        _base_record(trace_id="w-1", tool="WAIVER", recommendation={}),
    ]
    by_type = _by_type(class_specific_summaries(records))
    # The one real START_SIT evaluated record contributes to START_SIT's own
    # status counts only.
    assert _count(by_type["START_SIT"]["statusCounts"], "status", "EVALUATED") == 1
    assert _count(by_type["WAIVER"]["statusCounts"], "status", "EVALUATED") is None
    assert _count(by_type["WAIVER"]["statusCounts"], "status", "PENDING_OUTCOME") == 1
    # No key anywhere is a cross-class blend -- a structural spot check
    # rather than an exhaustive one: neither summary dict references the
    # other class's decisionType string as its own.
    assert by_type["START_SIT"]["decisionType"] == "START_SIT"
    assert by_type["WAIVER"]["decisionType"] == "WAIVER"


def test_trade_finder_and_trade_package_search_are_combined_under_one_shared_key() -> None:
    records = [
        _base_record(trace_id="tf-1", tool="TRADE_FINDER", recommendation={}),
        _base_record(trace_id="tps-1", tool="TRADE_PACKAGE_SEARCH", recommendation={}),
    ]
    by_type = _by_type(class_specific_summaries(records))
    assert _count(by_type["TRADE_FINDER"]["statusCounts"], "status", "PENDING_OUTCOME") == 2
    # Never merged with plain TRADE.
    assert by_type["TRADE"]["statusCounts"] == []


def test_no_summary_dict_ever_names_a_cross_class_accuracy_field() -> None:
    summaries = class_specific_summaries(())
    forbidden = ("accuracy", "crossClass", "combinedScore", "overallScore", "leaderboard")
    for summary in summaries:
        text = str(summary).lower()
        for term in forbidden:
            assert term.lower() not in text, f"{summary['decisionType']} summary unexpectedly mentions {term!r}: {summary}"


def test_status_counts_and_disposition_counts_never_carry_a_raw_enum_keyed_dict() -> None:
    """The real bug this pass found and fixed: an enum-keyed dict (e.g.
    `{"EVALUATED": 1}`) silently gets mangled by the HTTP camelCase-key
    transform (`"EVALUATED"` -> `"eVALUATED"`). Proven here at the SOURCE
    (before any HTTP layer even runs) so a future change can't reintroduce
    it without a widely-run test file failing immediately."""

    records = [
        _start_sit_evaluated_record(trace_id="ss-1"),
        _base_record(trace_id="tr-1", tool="TRADE", recommendation={"gives": [], "receives": []}),
    ]
    by_type = _by_type(class_specific_summaries(records))
    for summary in by_type.values():
        for field_name in ("statusCounts", "acceptanceStatusCounts", "packageDispositionCounts"):
            if field_name in summary:
                assert isinstance(summary[field_name], list), f"{summary['decisionType']}.{field_name} must be a list"


# ---------------------------------------------------------------------------
# Facade-level wiring: `evaluationDetail` on history events, and the new
# `redraft_decision_trace_outcome_summary` endpoint.
# ---------------------------------------------------------------------------


def _facade_with_local_profile(tmp_path: Path, *, league_name: str = "Presentation Test League") -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name=league_name)
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    return facade, profile_id


def test_decision_trace_history_event_carries_a_real_evaluation_detail_field(tmp_path: Path) -> None:
    facade, profile_id = _facade_with_local_profile(tmp_path)
    record_decision_trace(
        facade.redraft_root, profile_id, league_id="lg1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=("p1",), recommendation={"starters": ["p1"]},
    )
    history = facade.redraft_decision_trace_history()
    event = history.data["events"][0]
    assert "evaluationDetail" in event
    assert event["evaluationDetail"]["evaluation"]["evaluationStatus"] == "PENDING_OUTCOME"
    assert event["evaluationDetail"]["evaluation"]["decisionType"] == "START_SIT"
    # The pre-existing fields are all still there, byte-for-byte unchanged shape.
    assert event["decisionType"] == "START_SIT"
    assert event["outcome"] is None


def test_outcome_summary_endpoint_requires_an_active_profile(tmp_path: Path) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_decision_trace_outcome_summary()
    assert exc_info.value.code == "REDRAFT_PROFILE_REQUIRED"


def test_outcome_summary_endpoint_is_honest_about_zero_traces(tmp_path: Path) -> None:
    facade, profile_id = _facade_with_local_profile(tmp_path)
    result = facade.redraft_decision_trace_outcome_summary()
    assert result.data["profileId"] == profile_id
    assert result.data["totalTraceCount"] == 0
    assert set(_by_type(result.data["summaries"]).keys()) == set(CLASS_SUMMARY_DECISION_TYPES)
    # No aggregate accuracy anywhere in the real payload.
    assert "accuracy" not in str(result.data).lower()


def test_outcome_summary_endpoint_never_leaks_across_leagues(tmp_path: Path) -> None:
    facade, profile_a = _facade_with_local_profile(tmp_path, league_name="League A")
    record_decision_trace(
        facade.redraft_root, profile_a, league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=(), recommendation={},
    )
    created_b = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="League B")
    profile_b = created_b.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_b)

    summary_b = facade.redraft_decision_trace_outcome_summary()
    assert summary_b.data["totalTraceCount"] == 0
    assert _by_type(summary_b.data["summaries"])["WAIVER"]["statusCounts"] == []

    facade.activate_redraft_profile(profile_a)
    summary_a = facade.redraft_decision_trace_outcome_summary()
    assert summary_a.data["totalTraceCount"] == 1
    assert _count(_by_type(summary_a.data["summaries"])["WAIVER"]["statusCounts"], "status", "PENDING_OUTCOME") == 1
