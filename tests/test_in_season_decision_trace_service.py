from __future__ import annotations

import pytest

from src.services.in_season_decision_trace_service import (
    DecisionTraceError,
    load_decision_traces,
    record_decision_trace,
    record_owner_action,
)


def test_records_and_reloads_a_trace_for_every_defined_tool_type(tmp_path) -> None:
    for tool in (
        "START_SIT", "WAIVER", "ADD_DROP", "FAAB", "TRADE", "K_STREAMER", "DST_STREAMER",
    ):
        record_decision_trace(
            tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool=tool,
            engine_version="v1", data_versions={"weekly_projection": "SLEEPER_WEEKLY_PROJECTIONS_V1"},
            roster_state_player_ids=["p1", "p2"], recommendation={"action": "example"},
        )
    records = load_decision_traces(tmp_path, "profile-1")
    assert len(records) == 7
    assert {record.tool for record in records} == {
        "START_SIT", "WAIVER", "ADD_DROP", "FAAB", "TRADE", "K_STREAMER", "DST_STREAMER",
    }
    assert all(record.status == "RECOMMENDED" for record in records)
    assert all(record.owner_action is None for record in records)


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
