from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from src.services.in_season_decision_trace_service import (
    DEDUP_WINDOW_SECONDS,
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


# ---------------------------------------------------------------------------
# NWR Post-UI Product V1 (Closure Worker C): a real, found pathological-
# duplication bug -- every facade call site that records a trace is reached
# from a plain page-mount/dependency-change frontend effect (Weekly Home,
# Lineup, Waivers, Trade Finder, Find Trades), never gated behind an
# explicit "record this" button, so a page refresh/remount previously wrote
# a brand-new ledger line (and a brand-new random trace_id) for the exact
# same underlying recommendation every single time. These tests cover the
# fix's actual semantics: dedupe an immediate identical repeat, but never
# lose a genuinely distinct event.
# ---------------------------------------------------------------------------


def test_repeated_identical_recommendation_within_window_is_deduped(tmp_path) -> None:
    first = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={"mode": "REST_OF_SEASON"},
        roster_state_player_ids=["p1", "p2"], free_agent_state_player_ids=["fa1"],
        recommendation={"topAdd": "FA X", "topAddCanonicalId": "00-1"},
        alternatives=[{"playerName": "FA Y"}],
    )
    second = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        # engine_version/data_versions deliberately differ here -- these are
        # provenance-about-HOW-computed fields, not part of what makes a
        # recommendation event distinct, so they must never defeat the
        # dedup match on their own.
        engine_version="v2", data_versions={"mode": "REST_OF_SEASON", "extra": "x"},
        roster_state_player_ids=["p1", "p2"], free_agent_state_player_ids=["fa1"],
        recommendation={"topAdd": "FA X", "topAddCanonicalId": "00-1"},
        alternatives=[{"playerName": "FA Y"}],
    )
    assert second.trace_id == first.trace_id  # the existing record, not a new one

    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1  # no duplicate line was ever written

    reloaded = load_decision_traces(tmp_path, "profile-1")
    assert len(reloaded) == 1


def test_repeated_call_with_different_recommendation_content_is_not_deduped(tmp_path) -> None:
    first = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA X"},
    )
    second = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        # A genuinely different top add -- the real underlying roster/data
        # state changed, so this MUST be its own new event even though it
        # arrives an instant later.
        recommendation={"topAdd": "FA Z"},
    )
    assert second.trace_id != first.trace_id

    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2


def test_repeated_identical_recommendation_scoped_per_league_tool_week(tmp_path) -> None:
    """The exact same recommendation content for a DIFFERENT league, tool,
    or week is never deduped against an unrelated scope."""

    kwargs = dict(
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA X"},
    )
    record_decision_trace(tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER", **kwargs)
    record_decision_trace(tmp_path, "profile-1", league_id="lg2", season=2026, week=1, tool="WAIVER", **kwargs)
    record_decision_trace(tmp_path, "profile-1", league_id="lg1", season=2026, week=2, tool="WAIVER", **kwargs)
    record_decision_trace(tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="TRADE_FINDER", **kwargs)

    reloaded = load_decision_traces(tmp_path, "profile-1")
    assert len(reloaded) == 4  # every one of these is a genuinely distinct scope


def test_repeated_identical_recommendation_across_different_weeks_is_not_confused(tmp_path) -> None:
    """A WAIVER trace legitimately records BOTH a week-scoped (THIS_WEEK)
    and a week-agnostic (REST_OF_SEASON, week=None) event for the same
    league -- the dedup check must compare like-for-like on `week`, not
    accidentally collapse or cross-contaminate the two."""

    this_week = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA X"},
    )
    ros = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=None, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA X"},  # identical content, but a different week scope
    )
    assert ros.trace_id != this_week.trace_id

    # A second, later REST_OF_SEASON call with identical content DOES dedupe
    # against the REST_OF_SEASON one specifically, not the THIS_WEEK one.
    ros_again = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=None, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA X"},
    )
    assert ros_again.trace_id == ros.trace_id
    assert len(load_decision_traces(tmp_path, "profile-1")) == 2


def test_repeated_identical_recommendation_after_window_elapses_is_not_deduped(tmp_path) -> None:
    first = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA X"},
    )
    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    # Backdate the just-written line's own timestamp past the dedup window
    # -- simulates a real "the owner came back later and it's still the
    # same recommendation" gap without mocking the clock. This ledger
    # deliberately still records that as its own new event.
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    row = json.loads(lines[0])
    row["recorded_at_utc"] = (
        datetime.now(UTC) - timedelta(seconds=DEDUP_WINDOW_SECONDS + 60)
    ).isoformat()
    path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    second = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA X"},
    )
    assert second.trace_id != first.trace_id

    lines_after = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines_after) == 2


def test_alternating_content_never_loses_a_genuinely_distinct_event(tmp_path) -> None:
    """A -> B -> A again, all within the dedup window: since dedup only
    ever compares against the single MOST RECENT record in scope, the
    third call (content A) does NOT match the second (content B) and is
    correctly recorded as its own new event -- this ledger never
    incorrectly merges a genuine revert/oscillation into an earlier line
    just because the content happens to repeat."""

    a1 = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA A"},
    )
    b = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA B"},
    )
    a2 = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"topAdd": "FA A"},
    )
    assert len({a1.trace_id, b.trace_id, a2.trace_id}) == 3
    assert len(load_decision_traces(tmp_path, "profile-1")) == 3


# ---------------------------------------------------------------------------
# NWR Prospective Outcome V1: `record_outcome`'s new optional `detail`
# payload (decision-type-specific structured outcome fields, built by
# prospective_outcome_schema_v1_service.py) -- append-only and backward-
# compatible with every pre-existing caller that never passes it.
# ---------------------------------------------------------------------------


def test_record_outcome_without_detail_is_byte_identical_to_pre_existing_behavior(tmp_path) -> None:
    """Backward compatibility: omitting `detail` must produce the exact
    same outcome payload shape as before this pass -- no stray `detail`
    key, not even a null one."""

    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"add": "FA X"},
    )
    updated = record_outcome(tmp_path, "profile-1", record.trace_id, outcome="WON_MATCHUP", notes="close one")
    assert updated.outcome == {"outcome": "WON_MATCHUP", "notes": "close one"}
    assert "detail" not in updated.outcome


def test_record_outcome_with_detail_appends_a_new_line_never_mutates_the_original(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1", "p2"],
        recommendation={"projectedTotal": 100.0, "starters": ["p1"]},
    )
    detail = {
        "kind": "START_SIT_LINEUP_V1",
        "recommendedStarterIds": ["p1"],
        "actualStarterIds": ["p1"],
        "lineupOpportunityCost": 0.0,
    }
    updated = record_outcome(
        tmp_path, "profile-1", record.trace_id, outcome="STARTER_MATCHED_RECOMMENDATION", detail=detail,
    )
    assert updated.outcome["detail"] == detail
    assert updated.outcome["detail"] is not detail  # a defensive copy, not the same live object

    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2  # original recommendation line untouched, one new line appended
    original_row = json.loads(lines[0])
    assert "outcome" not in original_row  # the original recommendation line never gains an outcome key
    assert original_row["recommendation"] == {"projectedTotal": 100.0, "starters": ["p1"]}

    reloaded = load_decision_traces(tmp_path, "profile-1")
    assert len(reloaded) == 1  # latest-state-per-trace-id folding, not duplicated
    assert reloaded[0].outcome["detail"] == detail
    assert reloaded[0].recommendation == {"projectedTotal": 100.0, "starters": ["p1"]}  # preserved verbatim


# NWR Prospective Outcomes V1 (Work Unit 1, canonical outcome event
# contract): three further additive, independently omittable provenance
# fields on `record_outcome` -- `outcome_source`/`outcome_source_as_of`/
# `outcome_observed_at`. Same backward-compatible pattern `detail` already
# established.


def test_record_outcome_without_provenance_fields_is_still_byte_identical(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="WAIVER",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"add": "FA X"},
    )
    updated = record_outcome(tmp_path, "profile-1", record.trace_id, outcome="WON_MATCHUP", notes="close one")
    assert updated.outcome == {"outcome": "WON_MATCHUP", "notes": "close one"}
    assert "source" not in updated.outcome
    assert "sourceAsOf" not in updated.outcome
    assert "observedAt" not in updated.outcome


def test_record_outcome_with_provenance_fields_stores_only_the_ones_supplied(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"starters": ["p1"]},
    )
    updated = record_outcome(
        tmp_path, "profile-1", record.trace_id, outcome="STARTER_MATCHED_RECOMMENDATION",
        outcome_source="SLEEPER", outcome_source_as_of="2026-09-14T12:00:00+00:00",
    )
    assert updated.outcome["source"] == "SLEEPER"
    assert updated.outcome["sourceAsOf"] == "2026-09-14T12:00:00+00:00"
    assert "observedAt" not in updated.outcome  # not supplied -- honestly absent, not a null placeholder

    reloaded = load_decision_traces(tmp_path, "profile-1")[0]
    assert reloaded.outcome["source"] == "SLEEPER"
    assert reloaded.outcome["sourceAsOf"] == "2026-09-14T12:00:00+00:00"


def test_record_outcome_provenance_never_touches_the_original_recommendation_line(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"],
        recommendation={"starters": ["p1"]},
    )
    record_outcome(
        tmp_path, "profile-1", record.trace_id, outcome="X",
        outcome_source="SLEEPER", outcome_source_as_of="now", outcome_observed_at="now",
    )
    path = tmp_path / "decision_traces" / "profile-1.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    original_row = json.loads(lines[0])
    assert "outcome" not in original_row


def test_record_outcome_detail_round_trips_through_a_file_reload(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="FAAB",
        engine_version="v1", data_versions={}, roster_state_player_ids=["p1"], recommendation={},
    )
    detail = {
        "kind": "FAAB_V1",
        "recommendedPlayerId": "500",
        "playerDecisionQuality": {"subsequentPoints": 15.0, "subsequentRosterUsageWeeks": 1, "horizonWeeks": 4},
        "bidRangeCalibration": {
            "suggestedBidLow": 5.0, "suggestedBidHigh": 10.0, "amountBid": 8.0, "won": True,
            "actualWinningBid": 8.0, "bidWithinSuggestedRange": True, "marginVsActualWinningBid": 0.0,
        },
    }
    record_outcome(tmp_path, "profile-1", record.trace_id, outcome="CLAIM_WON", detail=detail)
    reloaded = load_decision_traces(tmp_path, "profile-1")[0]
    assert reloaded.outcome["detail"] == detail
    assert reloaded.status == "OUTCOME_RECORDED"


def test_no_future_outcome_field_exists_on_the_record_shape(tmp_path) -> None:
    record = record_decision_trace(
        tmp_path, "profile-1", league_id="lg1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=[], recommendation={},
    )
    row = record.to_json_row()
    forbidden = {"actual_points", "was_correct", "outcome", "result_vs_prediction"}
    assert not (forbidden & set(row.keys()))
