from __future__ import annotations

import json

import pytest

from src.services.in_season_decision_trace_service import (
    TOOL_TYPES,
    DecisionTraceError,
    load_decision_traces,
    record_decision_trace,
    record_outcome,
    record_owner_action,
)

ALL_TOOL_TYPES = (
    "START_SIT", "WAIVER", "ADD_DROP", "FAAB", "TRADE", "K_STREAMER", "DST_STREAMER",
    # NWR Post-UI Product V1 (P1-4): added to close a real bug -- desktop_facade.py
    # already called record_decision_trace with these two tool strings, but
    # neither was in TOOL_TYPES, so every such call silently raised
    # DecisionTraceError (caught by the facade's own best-effort wrapper).
    "TRADE_FINDER", "TRADE_PACKAGE_SEARCH",
    # DRAFT: schema-only this pass -- no live call site yet (draft
    # recommendation logic is out of this pass's hard boundary).
    "DRAFT",
)


def test_tool_types_constant_matches_the_full_expected_set() -> None:
    assert TOOL_TYPES == frozenset(ALL_TOOL_TYPES)


def test_records_and_reloads_a_trace_for_every_defined_tool_type(tmp_path) -> None:
    for tool in ALL_TOOL_TYPES:
        record_decision_trace(
            tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool=tool,
            engine_version="v1", data_versions={"weekly_projection": "SLEEPER_WEEKLY_PROJECTIONS_V1"},
            roster_state_player_ids=["p1", "p2"], recommendation={"action": "example"},
        )
    records = load_decision_traces(tmp_path, "profile-1")
    assert len(records) == len(ALL_TOOL_TYPES)
    assert {record.tool for record in records} == set(ALL_TOOL_TYPES)
    assert all(record.status == "RECOMMENDED" for record in records)
    assert all(record.owner_action is None for record in records)


def test_league_snapshot_id_and_status_versions_round_trip(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"add": "FA X"}, league_snapshot_id="snap-abc123",
        status_versions={"playerAvailabilityStatusAuthority": "MANUAL_VERIFIED_OVERRIDE"},
    )
    assert record.league_snapshot_id == "snap-abc123"
    assert record.status_versions == {"playerAvailabilityStatusAuthority": "MANUAL_VERIFIED_OVERRIDE"}

    reloaded = load_decision_traces(tmp_path, "profile-1")[0]
    assert reloaded.league_snapshot_id == "snap-abc123"
    assert reloaded.status_versions == {"playerAvailabilityStatusAuthority": "MANUAL_VERIFIED_OVERRIDE"}


def test_league_snapshot_id_and_status_versions_default_to_backward_compatible_values(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"], recommendation={},
    )
    assert record.league_snapshot_id is None
    assert record.status_versions == {}
    row = record.to_json_row()
    assert row["league_snapshot_id"] is None
    assert row["status_versions"] == {}


def test_rejects_unknown_tool_type(tmp_path) -> None:
    with pytest.raises(DecisionTraceError):
        record_decision_trace(
            tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="NOT_A_REAL_TOOL",
            engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
        )


def test_owner_action_appends_a_new_line_never_mutates_the_original(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"add": "FA X"},
    )
    updated = record_owner_action(tmp_path, "profile-1", record.trace_id, action="ADDED", notes="took it")
    assert updated.status == "OWNER_ACTION_RECORDED"
    assert updated.owner_action == {"action": "ADDED", "notes": "took it"}

    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2  # original recommendation line is untouched, a new line was appended

    reloaded = load_decision_traces(tmp_path, "profile-1")
    assert len(reloaded) == 1  # latest-state-per-trace-id folding, not duplicated
    assert reloaded[0].status == "OWNER_ACTION_RECORDED"
    assert reloaded[0].recommendation == {"add": "FA X"}  # original recommendation preserved


def test_owner_action_on_unknown_trace_id_raises(tmp_path) -> None:
    with pytest.raises(DecisionTraceError):
        record_owner_action(tmp_path, "profile-1", "does-not-exist", action="ADDED")


def test_outcome_appends_a_new_line_never_mutates_the_original(tmp_path) -> None:
    """NWR Post-UI Product V1 (P1-4): the append-only OUTCOME write path --
    real and callable even though nothing in production calls it yet (no
    real 2026-season outcome exists for anything recorded so far)."""

    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"add": "FA X"},
    )
    updated = record_outcome(tmp_path, "profile-1", record.trace_id, outcome="WON_MATCHUP", notes="close one")
    assert updated.status == "OUTCOME_RECORDED"
    assert updated.outcome == {"outcome": "WON_MATCHUP", "notes": "close one"}
    assert updated.outcome_recorded_at_utc

    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2  # original recommendation line is untouched, a new line was appended
    original_row = json.loads(lines[0])
    assert "outcome" not in original_row  # never backdated into the original

    reloaded = load_decision_traces(tmp_path, "profile-1")
    assert len(reloaded) == 1  # latest-state-per-trace-id folding, not duplicated
    assert reloaded[0].status == "OUTCOME_RECORDED"
    assert reloaded[0].recommendation == {"add": "FA X"}  # original recommendation preserved


def test_outcome_after_owner_action_preserves_both_facts(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"], recommendation={"add": "FA X"},
    )
    record_owner_action(tmp_path, "profile-1", record.trace_id, action="ADDED", notes="took it")
    updated = record_outcome(tmp_path, "profile-1", record.trace_id, outcome="WON_MATCHUP")
    assert updated.status == "OUTCOME_RECORDED"
    assert updated.owner_action == {"action": "ADDED", "notes": "took it"}  # preserved, not dropped
    assert updated.outcome == {"outcome": "WON_MATCHUP", "notes": ""}


def test_owner_action_recorded_after_outcome_does_not_regress_status(tmp_path) -> None:
    """An unusual order (outcome recorded before an owner-action append),
    but status must reflect the LATEST real lifecycle stage reached, never
    regress backward."""

    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"], recommendation={},
    )
    record_outcome(tmp_path, "profile-1", record.trace_id, outcome="WON_MATCHUP")
    updated = record_owner_action(tmp_path, "profile-1", record.trace_id, action="ADDED")
    assert updated.status == "OUTCOME_RECORDED"
    assert updated.owner_action == {"action": "ADDED", "notes": ""}


def test_outcome_on_unknown_trace_id_raises(tmp_path) -> None:
    with pytest.raises(DecisionTraceError):
        record_outcome(tmp_path, "profile-1", "does-not-exist", outcome="WON_MATCHUP")


def test_filters_by_tool_and_week(tmp_path) -> None:
    record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
    )
    record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=2, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
    )
    record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="TRADE",
        engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
    )
    assert len(load_decision_traces(tmp_path, "profile-1", tool="WAIVER")) == 2
    assert len(load_decision_traces(tmp_path, "profile-1", tool="WAIVER", week=1)) == 1
    assert len(load_decision_traces(tmp_path, "profile-1", tool="TRADE")) == 1


def test_missing_ledger_file_returns_empty_not_an_error(tmp_path) -> None:
    assert load_decision_traces(tmp_path, "no-such-profile") == ()


def test_malformed_line_does_not_crash_the_whole_ledger_read(tmp_path) -> None:
    record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
    )
    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not valid json at all\n")
    records = load_decision_traces(tmp_path, "profile-1")
    assert len(records) == 1


def test_no_future_outcome_field_exists_on_the_record_shape(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
    )
    row = record.to_json_row()
    forbidden = {"actual_points", "was_correct", "outcome", "result_vs_prediction"}
    assert not (forbidden & set(row.keys()))
