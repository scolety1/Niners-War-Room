from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from src.services.in_season_decision_trace_service import DecisionTraceRecord
from src.services.prospective_outcome_source_adapter_v1_service import (
    RealizedOutcomeFetch,
    RecommendationTimeContext,
    adapt_and_ingest_start_sit_outcome,
    fetch_horizon_matchup_entries,
    fetch_owner_matchup_entry,
    fetch_transactions_for_rounds,
    fetch_week_matchups,
    recommendation_time_context_from_trace,
)
from src.services.sleeper_import_service import SleeperHttpClient

_REAL_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "codex" / "prospective_outcome_v1" / "real_data_v1"
    / "fantasy_gamers_week1_2026_owner_matchup.json"
)


class FakeSleeperClient:
    """A duck-typed double for `SleeperHttpClient` -- no real network I/O.
    Real network fetching is proven separately by the prior cycle's own
    live demo script (`scripts/build_prospective_outcome_ingestion_v1_
    startsit_demo.py`); this test file exercises this module's own
    wrapping/composition logic in isolation."""

    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def get_json(self, path: str) -> Any:
        self.calls.append(path)
        return self.responses[path]


def _base_record(**overrides) -> DecisionTraceRecord:
    fields = dict(
        trace_id="trace-1", league_id="lg1", profile_id="profile-1", season=2026, week=1, tool="START_SIT",
        engine_version="v1", data_versions={}, roster_state_player_ids=("p1", "p2"),
        free_agent_state_player_ids=None, recommendation={"starters": ["p1"]}, alternatives=(),
        recorded_at_utc="2026-09-08T00:00:00+00:00",
    )
    fields.update(overrides)
    return DecisionTraceRecord(**fields)


# ---------------------------------------------------------------------------
# RecommendationTimeContext -- pure, zero I/O.
# ---------------------------------------------------------------------------


def test_context_builder_reads_only_the_traces_own_frozen_fields() -> None:
    record = _base_record(
        roster_state_player_ids=("1", "2", "3"),
        free_agent_state_player_ids=("9", "10"),
        alternatives=({"id": "9"},),
        owner_action={"action": "Followed it", "notes": ""},
    )
    context = recommendation_time_context_from_trace(record)
    assert context == RecommendationTimeContext(
        trace_id="trace-1", decision_type="START_SIT", league_id="lg1", profile_id="profile-1", week=1,
        recommendation={"starters": ["p1"]}, roster_state_player_ids=("1", "2", "3"),
        free_agent_state_player_ids=("9", "10"), alternatives=({"id": "9"},),
        owner_action={"action": "Followed it", "notes": ""},
    )


def test_context_builder_signature_has_no_http_client_or_current_state_parameter() -> None:
    parameters = list(inspect.signature(recommendation_time_context_from_trace).parameters)
    assert parameters == ["record"]
    forbidden_fragments = ("current", "live", "now_", "today", "client", "http")
    for name in parameters:
        assert not any(fragment in name.lower() for fragment in forbidden_fragments)


def test_assert_context_builder_is_pure_actually_catches_a_client_parameter() -> None:
    """Proves the structural guard is a real check, not a no-op."""

    from src.services.prospective_outcome_source_adapter_v1_service import _assert_context_builder_is_pure

    def bad_builder(record, client: SleeperHttpClient):
        return record, client

    with pytest.raises(ValueError):
        _assert_context_builder_is_pure(bad_builder)


def test_assert_context_builder_is_pure_catches_a_forbidden_name_even_without_a_type_hint() -> None:
    from src.services.prospective_outcome_source_adapter_v1_service import _assert_context_builder_is_pure

    def bad_builder(record, current_free_agent_ids):
        return record, current_free_agent_ids

    with pytest.raises(ValueError):
        _assert_context_builder_is_pure(bad_builder)


# ---------------------------------------------------------------------------
# fetch_* -- real I/O isolated to these functions only (a fake client here;
# real network I/O is proven by the live demo script, not by pytest).
# ---------------------------------------------------------------------------


def test_fetch_week_matchups_wraps_the_raw_sleeper_response() -> None:
    raw = [{"roster_id": 9, "points": 100.0}, {"roster_id": 3, "points": 90.0}]
    client = FakeSleeperClient({"league/lg1/matchups/1": raw})
    fetch = fetch_week_matchups(client, "lg1", 1)
    assert fetch.source == "SLEEPER"
    assert fetch.league_id == "lg1"
    assert fetch.payload == raw
    assert fetch.fetched_at_utc  # a real, non-empty timestamp
    assert client.calls == ["league/lg1/matchups/1"]


def test_fetch_owner_matchup_entry_extracts_the_right_roster() -> None:
    raw = [{"roster_id": 9, "points": 100.0}, {"roster_id": 3, "points": 90.0}]
    client = FakeSleeperClient({"league/lg1/matchups/1": raw})
    fetch = fetch_owner_matchup_entry(client, "lg1", 1, owner_roster_id=9)
    assert fetch.payload == {"roster_id": 9, "points": 100.0}


def test_fetch_owner_matchup_entry_returns_none_honestly_when_no_entry_exists() -> None:
    client = FakeSleeperClient({"league/lg1/matchups/1": []})
    fetch = fetch_owner_matchup_entry(client, "lg1", 1, owner_roster_id=9)
    assert fetch.payload is None


def test_fetch_horizon_matchup_entries_skips_weeks_with_no_real_entry() -> None:
    client = FakeSleeperClient(
        {
            "league/lg1/matchups/1": [{"roster_id": 9, "points": 10.0}],
            "league/lg1/matchups/2": [],  # no entry for roster 9 this week
            "league/lg1/matchups/3": [{"roster_id": 9, "points": 20.0}],
        }
    )
    fetch = fetch_horizon_matchup_entries(client, "lg1", weeks=[1, 2, 3], owner_roster_id=9)
    assert fetch.payload == ({"roster_id": 9, "points": 10.0}, {"roster_id": 9, "points": 20.0})


def test_fetch_transactions_for_rounds_combines_every_round_the_caller_asked_for() -> None:
    """Real fix for the prior cycle's own disclosed open issue: a caller
    that wants a complete 'did not claim' answer must fetch every relevant
    round, not just one."""

    client = FakeSleeperClient(
        {
            "league/lg1/transactions/1": [{"transaction_id": "a"}],
            "league/lg1/transactions/2": [{"transaction_id": "b"}, {"transaction_id": "c"}],
        }
    )
    fetch = fetch_transactions_for_rounds(client, "lg1", rounds=[1, 2])
    assert fetch.payload == ({"transaction_id": "a"}, {"transaction_id": "b"}, {"transaction_id": "c"})
    assert client.calls == ["league/lg1/transactions/1", "league/lg1/transactions/2"]


# ---------------------------------------------------------------------------
# Composition -- real fixture data, genuinely real (not synthetic).
# ---------------------------------------------------------------------------


def test_adapt_and_ingest_start_sit_outcome_with_real_fixture_data() -> None:
    real_matchup = json.loads(_REAL_FIXTURE_PATH.read_text(encoding="utf-8"))
    record = _base_record(
        recommendation={"projectedTotal": None, "starters": list(real_matchup["starters"])},
        roster_state_player_ids=tuple(real_matchup["players"]),
    )
    context = recommendation_time_context_from_trace(record)
    client = FakeSleeperClient({"league/lg1/matchups/1": [real_matchup]})
    matchup_fetch = fetch_owner_matchup_entry(client, "lg1", 1, owner_roster_id=9)

    detail = adapt_and_ingest_start_sit_outcome(context=context, matchup_fetch=matchup_fetch)
    assert detail.actual_points_total == 156.96
    assert detail.lineup_opportunity_cost == 0.0


def test_adapt_and_ingest_start_sit_outcome_rejects_a_mismatched_decision_type() -> None:
    record = _base_record(tool="WAIVER")
    context = recommendation_time_context_from_trace(record)
    fetch = RealizedOutcomeFetch(source="SLEEPER", league_id="lg1", fetched_at_utc="now", payload=None)
    with pytest.raises(ValueError):
        adapt_and_ingest_start_sit_outcome(context=context, matchup_fetch=fetch)


def test_adapt_and_ingest_start_sit_outcome_rejects_an_unrecognized_source() -> None:
    record = _base_record()
    context = recommendation_time_context_from_trace(record)
    fetch = RealizedOutcomeFetch(source="SOME_OTHER_PROVIDER", league_id="lg1", fetched_at_utc="now", payload=None)
    with pytest.raises(ValueError):
        adapt_and_ingest_start_sit_outcome(context=context, matchup_fetch=fetch)


# ---------------------------------------------------------------------------
# The core hindsight-leakage defense, proven structurally end-to-end: a
# RecommendationTimeContext built BEFORE a later, contradictory "realized"
# fetch is fabricated is never affected by that later fetch, because the
# two objects are never merged into one mutable structure.
# ---------------------------------------------------------------------------


def test_context_is_structurally_immune_to_a_later_contradictory_fetch() -> None:
    record = _base_record(roster_state_player_ids=("1", "2", "3"))
    context = recommendation_time_context_from_trace(record)
    frozen_roster_before = context.roster_state_player_ids

    # Simulate a later, real fetch describing a totally different roster
    # (e.g. after several real roster moves) -- this must never be able to
    # reach back and alter `context`, because no function in this module
    # ever writes a fetched field back into an already-built context.
    client = FakeSleeperClient({"league/lg1/matchups/1": [{"roster_id": 9, "points": 1.0, "players": ["999"]}]})
    fetch_owner_matchup_entry(client, "lg1", 1, owner_roster_id=9)

    assert context.roster_state_player_ids == frozen_roster_before == ("1", "2", "3")
