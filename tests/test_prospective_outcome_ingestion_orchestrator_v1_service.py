from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from src.services.in_season_decision_trace_service import (
    load_decision_traces,
    record_decision_trace,
)
from src.services.prospective_outcome_ingestion_orchestrator_v1_service import (
    ACTION_PROCESS_FULL_START_SIT,
    ACTION_PROCESS_INSUFFICIENT_CONTEXT,
    ACTION_SKIP_ALREADY_PROCESSED,
    ACTION_SKIP_DEFERRED_DRAFT,
    ACTION_SKIP_IMMATURE_WINDOW,
    ACTION_SKIP_OWNER_ROSTER_UNKNOWN,
    ACTION_SKIP_WINDOW_UNDETERMINABLE,
    ProspectiveOutcomeIngestionOrchestratorError,
    _assert_plan_function_is_safe,
    execute_plan_item,
    plan_ingestion_action,
    run_ingestion,
)

REAL_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "codex" / "prospective_outcome_v1" / "real_data_v1"
    / "fantasy_gamers_week1_2026_owner_matchup.json"
)
LEAGUE_ID = "1312983576827920384"
OWNER_ROSTER_ID = 9


class FakeSleeperClient:
    """Same duck-typed double the prior cycle's own source-adapter tests
    use -- no real network I/O. Raises on any unexpected path, so a test
    can structurally prove "zero network calls happened" for the
    insufficient-context path."""

    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[str] = []

    def get_json(self, path: str) -> Any:
        self.calls.append(path)
        if path not in self.responses:
            raise AssertionError(f"Unexpected real network call attempted: {path!r}")
        return self.responses[path]


# ---------------------------------------------------------------------------
# plan_ingestion_action -- pure, no I/O.
# ---------------------------------------------------------------------------


def test_draft_trace_is_always_deferred(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=None,
        tool="DRAFT", engine_version="v1", data_versions={},
        roster_state_player_ids=[], recommendation={},
    )
    item = plan_ingestion_action(trace, current_nfl_week=99, owner_roster_id_by_league={})
    assert item.action == ACTION_SKIP_DEFERRED_DRAFT


def test_trade_family_week_none_is_window_undeterminable(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=None,
        tool="TRADE", engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"gives": ["p1"], "receives": ["p2"]},
    )
    item = plan_ingestion_action(trace, current_nfl_week=99, owner_roster_id_by_league={})
    assert item.action == ACTION_SKIP_WINDOW_UNDETERMINABLE


def test_immature_start_sit_window_is_untouched(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=2,
        tool="START_SIT", engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"starters": ["p1"]},
    )
    # SAME_WEEK, horizon 0 -- matured requires current_nfl_week > week.
    item = plan_ingestion_action(
        trace, current_nfl_week=2, owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )
    assert item.action == ACTION_SKIP_IMMATURE_WINDOW


def test_matured_start_sit_without_owner_roster_id_is_a_config_gap_not_insufficient_context(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool="START_SIT", engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"starters": ["p1"]},
    )
    item = plan_ingestion_action(trace, current_nfl_week=2, owner_roster_id_by_league={})
    assert item.action == ACTION_SKIP_OWNER_ROSTER_UNKNOWN


def test_matured_start_sit_with_owner_roster_id_is_processed(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool="START_SIT", engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"starters": ["p1"]},
    )
    item = plan_ingestion_action(
        trace, current_nfl_week=2, owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )
    assert item.action == ACTION_PROCESS_FULL_START_SIT


@pytest.mark.parametrize("tool", ["WAIVER", "FAAB", "ADD_DROP", "K_STREAMER", "DST_STREAMER"])
def test_matured_identity_unresolved_classes_become_insufficient_context(tmp_path, tool):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool=tool, engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"playerName": "Someone"},
    )
    # BOUNDED_HORIZON, 4 weeks -- matured requires current_nfl_week > week + 4.
    item = plan_ingestion_action(trace, current_nfl_week=6, owner_roster_id_by_league={})
    assert item.action == ACTION_PROCESS_INSUFFICIENT_CONTEXT


@pytest.mark.parametrize("tool", ["WAIVER", "FAAB", "ADD_DROP"])
def test_immature_bounded_horizon_classes_stay_untouched(tmp_path, tool):
    # BOUNDED_HORIZON, 4 weeks -- week=1 matures only once current_nfl_week
    # > 5; week=5 is still immature.
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool=tool, engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"playerName": "Someone"},
    )
    item = plan_ingestion_action(trace, current_nfl_week=5, owner_roster_id_by_league={})
    assert item.action == ACTION_SKIP_IMMATURE_WINDOW


@pytest.mark.parametrize("tool", ["K_STREAMER", "DST_STREAMER"])
def test_immature_same_week_streamer_classes_stay_untouched(tmp_path, tool):
    # SAME_WEEK, horizon 0 -- matures only once current_nfl_week > week; the
    # trace's own recommendation week is not yet "over" while they're equal.
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=3,
        tool=tool, engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"playerName": "Someone"},
    )
    item = plan_ingestion_action(trace, current_nfl_week=3, owner_roster_id_by_league={})
    assert item.action == ACTION_SKIP_IMMATURE_WINDOW


def test_already_has_outcome_is_skipped_even_if_matured(tmp_path):
    from src.services.in_season_decision_trace_service import record_outcome

    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool="WAIVER", engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"topAddCanonicalId": "c1"},
    )
    updated = record_outcome(tmp_path, "profile-1", trace.trace_id, outcome="SOME_REAL_OUTCOME")
    item = plan_ingestion_action(updated, current_nfl_week=99, owner_roster_id_by_league={})
    assert item.action == ACTION_SKIP_ALREADY_PROCESSED


# ---------------------------------------------------------------------------
# Full real pipeline -- START_SIT against the SAME real, committed Week 1
# 2026 Fantasy Gamers fixture the prior cycle's own tests already use.
# ---------------------------------------------------------------------------


def test_run_ingestion_processes_a_real_start_sit_trace_end_to_end(tmp_path):
    real_matchup = json.loads(REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    record_decision_trace(
        tmp_path, "fantasy-gamers-profile", league_id=LEAGUE_ID, season=2026, week=1,
        tool="START_SIT", engine_version="weekly_lineup_optimizer_service-v1", data_versions={},
        roster_state_player_ids=list(real_matchup["players"]),
        # Mechanism-demonstration baseline (matches the prior cycle's own
        # documented precedent): recommends the real actual starters.
        recommendation={"projectedTotal": None, "starters": list(real_matchup["starters"])},
    )
    client = FakeSleeperClient({f"league/{LEAGUE_ID}/matchups/1": [real_matchup]})

    report = run_ingestion(
        tmp_path, client=client, current_nfl_week=2,
        owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )

    assert report.counts_by_action[ACTION_PROCESS_FULL_START_SIT] == 1
    assert len(report.processed) == 1
    processed = report.processed[0]
    base_evaluation = processed["evaluation"]["evaluation"]
    assert base_evaluation["evaluationStatus"] == "EVALUATED"
    assert base_evaluation["evaluationMetrics"]["lineupOpportunityCostPoints"] == 0.0

    reloaded = load_decision_traces(tmp_path, "fantasy-gamers-profile")
    assert len(reloaded) == 1
    assert reloaded[0].outcome is not None
    assert reloaded[0].outcome["detail"]["kind"] == "START_SIT_LINEUP_V1"
    assert reloaded[0].outcome["source"] == "SLEEPER"


def test_run_ingestion_never_fetches_network_for_insufficient_context_path(tmp_path):
    record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool="WAIVER", engine_version="waiver_engine_service-v1", data_versions={},
        roster_state_player_ids=["p1"],
        # The real, confirmed live payload shape -- a canonical ranking id,
        # never a Sleeper id.
        recommendation={"topAdd": "Some Player", "topAddCanonicalId": "canonical-123"},
    )
    client = FakeSleeperClient({})  # any get_json call raises -- see FakeSleeperClient

    report = run_ingestion(tmp_path, client=client, current_nfl_week=6, owner_roster_id_by_league={})

    assert client.calls == []  # a real, structural proof: zero network calls were made
    assert report.counts_by_action[ACTION_PROCESS_INSUFFICIENT_CONTEXT] == 1
    processed = report.processed[0]
    assert processed["outcomeLabel"] == "INSUFFICIENT_DECISION_CONTEXT"
    assert processed["evaluation"]["evaluation"]["evaluationStatus"] == "INSUFFICIENT_DECISION_CONTEXT"

    reloaded = load_decision_traces(tmp_path, "profile-1")[0]
    assert reloaded.outcome["outcome"] == "INSUFFICIENT_DECISION_CONTEXT"
    assert reloaded.outcome["detail"]["recommendedPlayerId"] is None


def test_immature_events_are_genuinely_untouched(tmp_path):
    record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=5,
        tool="WAIVER", engine_version="waiver_engine_service-v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"topAddCanonicalId": "c1"},
    )
    client = FakeSleeperClient({})
    report = run_ingestion(tmp_path, client=client, current_nfl_week=6, owner_roster_id_by_league={})

    assert client.calls == []
    assert report.counts_by_action.get(ACTION_SKIP_IMMATURE_WINDOW) == 1
    assert report.processed == ()

    reloaded = load_decision_traces(tmp_path, "profile-1")[0]
    assert reloaded.outcome is None  # genuinely untouched -- no ledger write at all


# ---------------------------------------------------------------------------
# Idempotency -- the directive's own required proof: running ingestion
# twice on the same trace store must not create duplicate outcome events,
# and the resulting ledger content must be PROVABLY unchanged by the
# second run (not just "no crash").
# ---------------------------------------------------------------------------


def test_running_ingestion_twice_produces_byte_identical_ledger_state(tmp_path):
    real_matchup = json.loads(REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    record_decision_trace(
        tmp_path, "profile-mixed", league_id=LEAGUE_ID, season=2026, week=1,
        tool="START_SIT", engine_version="weekly_lineup_optimizer_service-v1", data_versions={},
        roster_state_player_ids=list(real_matchup["players"]),
        recommendation={"projectedTotal": None, "starters": list(real_matchup["starters"])},
    )
    record_decision_trace(
        tmp_path, "profile-mixed", league_id=LEAGUE_ID, season=2026, week=1,
        tool="WAIVER", engine_version="waiver_engine_service-v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"topAddCanonicalId": "c1"},
    )
    record_decision_trace(
        tmp_path, "profile-mixed", league_id=LEAGUE_ID, season=2026, week=5,
        tool="FAAB", engine_version="waiver_engine_service-v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"playerName": "Bench Guy"},
    )  # deliberately immature at current_nfl_week=2 (horizon needs week>9)

    ledger_path = tmp_path / "decision_traces" / "profile-mixed.jsonl"

    client_1 = FakeSleeperClient({f"league/{LEAGUE_ID}/matchups/1": [real_matchup]})
    report_1 = run_ingestion(
        tmp_path, client=client_1, current_nfl_week=6, owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )
    assert report_1.counts_by_action.get(ACTION_PROCESS_FULL_START_SIT) == 1
    assert report_1.counts_by_action.get(ACTION_PROCESS_INSUFFICIENT_CONTEXT) == 1
    assert report_1.counts_by_action.get(ACTION_SKIP_IMMATURE_WINDOW) == 1

    lines_after_first_run = ledger_path.read_text(encoding="utf-8")
    records_after_first_run = load_decision_traces(tmp_path, "profile-mixed")
    assert len(records_after_first_run) == 3  # 3 distinct trace_ids, not duplicated

    # Second run: same root, same (poisoned-on-unexpected-call) client --
    # any real network call this time proves a real bug (re-fetching data
    # for an already-processed trace).
    client_2 = FakeSleeperClient({})
    report_2 = run_ingestion(
        tmp_path, client=client_2, current_nfl_week=6, owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )

    assert client_2.calls == []  # zero real network calls on the second run
    assert report_2.processed == ()  # nothing new was ingested
    assert report_2.counts_by_action.get(ACTION_SKIP_ALREADY_PROCESSED) == 2
    assert report_2.counts_by_action.get(ACTION_SKIP_IMMATURE_WINDOW) == 1

    lines_after_second_run = ledger_path.read_text(encoding="utf-8")
    records_after_second_run = load_decision_traces(tmp_path, "profile-mixed")

    # The REAL, provable assertion: byte-for-byte identical raw ledger
    # content, not merely "the same number of records."
    assert lines_after_first_run == lines_after_second_run
    assert records_after_first_run == records_after_second_run


# ---------------------------------------------------------------------------
# execute_plan_item -- direct misuse guards.
# ---------------------------------------------------------------------------


def test_execute_plan_item_rejects_a_skip_action(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=None,
        tool="DRAFT", engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
    )
    item = plan_ingestion_action(trace, current_nfl_week=99, owner_roster_id_by_league={})
    with pytest.raises(ProspectiveOutcomeIngestionOrchestratorError):
        execute_plan_item(item, trace, root=tmp_path)


def test_execute_plan_item_start_sit_requires_owner_roster_id(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool="START_SIT", engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"starters": ["p1"]},
    )
    item = plan_ingestion_action(
        trace, current_nfl_week=2, owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )
    with pytest.raises(ProspectiveOutcomeIngestionOrchestratorError):
        execute_plan_item(item, trace, root=tmp_path, client=FakeSleeperClient({}), owner_roster_id_by_league={})


# ---------------------------------------------------------------------------
# Hindsight-leakage defense -- structural, not just promised.
# ---------------------------------------------------------------------------


def test_plan_ingestion_action_signature_accepts_no_current_state_parameter():
    forbidden = ("current_roster", "current_free_agent", "live_roster", "now_roster")
    for name in inspect.signature(plan_ingestion_action).parameters:
        assert not any(fragment in name.lower() for fragment in forbidden)


def test_assert_plan_function_is_safe_actually_catches_a_violation():
    def bad_function(current_roster_ids, week):
        return None

    with pytest.raises(ProspectiveOutcomeIngestionOrchestratorError):
        _assert_plan_function_is_safe(bad_function)


def test_plan_ingestion_action_is_pure_and_deterministic(tmp_path):
    trace = record_decision_trace(
        tmp_path, "profile-1", league_id=LEAGUE_ID, season=2026, week=1,
        tool="START_SIT", engine_version="v1", data_versions={},
        roster_state_player_ids=["p1"], recommendation={"starters": ["p1"]},
    )
    first = plan_ingestion_action(
        trace, current_nfl_week=2, owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )
    second = plan_ingestion_action(
        trace, current_nfl_week=2, owner_roster_id_by_league={LEAGUE_ID: OWNER_ROSTER_ID},
    )
    assert first == second


# ---------------------------------------------------------------------------
# Hard boundary -- never imports a forbidden module.
# ---------------------------------------------------------------------------


def test_module_never_imports_hard_boundary_dependencies():
    from src.services import prospective_outcome_ingestion_orchestrator_v1_service as orchestrator_module

    import_lines = [
        line.strip()
        for line in inspect.getsource(orchestrator_module).splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]
    for forbidden in (
        "marginal_roster_utility_v2",
        "shadow_numeric_authorities_service",
        "league_workspace_context_service",
        "lifecycle_resolver",
        "player_availability_status",
    ):
        assert not any(forbidden in line.lower() for line in import_lines)
