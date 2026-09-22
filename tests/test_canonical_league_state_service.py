"""Waiver-night hardening cycle, Worker 3 (2026-09-22): pure, synthetic-
fixture regression tests for the new provider-neutral canonical
league-state boundary (`src/services/canonical_league_state_service.py`).

No network I/O, no real Sleeper/ESPN data anywhere in this file -- every
fixture below is clearly synthetic, matching the dispatch directive's
explicit instruction to use "clearly-synthetic, clearly-labeled unit-test
fixtures for the ESPN path" and never fabricate anything that could be
mistaken for real data.
"""

from __future__ import annotations

import pytest

from src.services.canonical_league_state_service import (
    CanonicalLeagueStateError,
    build_canonical_league_state_from_espn_snapshot,
    build_canonical_league_state_from_sleeper,
)
from src.services.espn_flaim_snapshot_service import parse_espn_flaim_snapshot
from src.services.league_capability_service import (
    capabilities_from_sleeper_receipt,
)

# ---------------------------------------------------------------------------
# Sleeper builder
# ---------------------------------------------------------------------------

_SLEEPER_ROSTERS = [
    {
        "owner_id": "owner-1",
        "roster_id": "1",
        "players": ["p-starter", "p-bench", "p-reserve", "p-no-catalog"],
        "starters": ["p-starter"],
        "reserve": ["p-reserve"],
    },
    {
        "owner_id": "owner-2",
        "roster_id": "2",
        "players": ["p-rival"],
        "starters": ["p-rival"],
    },
]
_SLEEPER_PLAYERS_CATALOG = {
    "p-starter": {"full_name": "Starter Guy", "position": "RB", "team": "sf"},
    "p-bench": {"full_name": "Bench Guy", "position": "WR", "team": "kc"},
    "p-reserve": {"full_name": "Reserve Guy", "position": "TE", "team": "dal"},
    "p-rival": {"full_name": "Rival Guy", "position": "QB", "team": "buf"},
    # p-no-catalog deliberately absent.
}
_SLEEPER_RECEIPT = {
    "league": {"league_id": "9999", "name": "Synthetic League"},
    "owner": {"user_id": "owner-1"},
    "scoring_reconciliation": {"ok": True},
}


def _sleeper_capabilities():
    return capabilities_from_sleeper_receipt(_SLEEPER_RECEIPT)


def test_sleeper_builder_classifies_starter_bench_reserve_correctly() -> None:
    state = build_canonical_league_state_from_sleeper(
        league_name="Synthetic League", season=2026, team_count=2, league_id="9999",
        owner_user_id="owner-1", rosters_raw=_SLEEPER_ROSTERS,
        players_catalog=_SLEEPER_PLAYERS_CATALOG, retrieved_at_utc="2026-09-22T00:00:00Z",
        capabilities=_sleeper_capabilities(),
    )
    assert state.provider == "sleeper"
    assert state.provider_league_id == "9999"
    by_id = {p.provider_player_id: p for p in state.roster}
    assert by_id["p-starter"].slot == "STARTER"
    assert by_id["p-bench"].slot == "BENCH"
    assert by_id["p-reserve"].slot == "RESERVE"
    assert by_id["p-starter"].player_name == "Starter Guy"
    assert by_id["p-starter"].position == "RB"
    assert by_id["p-starter"].team == "SF"  # upper-cased, matching pre-existing behavior
    # Opponent rosters not requested -> None, never a guessed/partial list.
    assert state.opponent_rosters is None


def test_sleeper_builder_degrades_a_missing_catalog_entry_to_the_raw_provider_id() -> None:
    """Matches the exact pre-conversion fallback `redraft_my_roster` used
    inline: no catalog entry -> empty position/team, provider id as name."""
    state = build_canonical_league_state_from_sleeper(
        league_name="Synthetic League", season=2026, team_count=2, league_id="9999",
        owner_user_id="owner-1", rosters_raw=_SLEEPER_ROSTERS,
        players_catalog=_SLEEPER_PLAYERS_CATALOG, retrieved_at_utc="2026-09-22T00:00:00Z",
        capabilities=_sleeper_capabilities(),
    )
    by_id = {p.provider_player_id: p for p in state.roster}
    missing = by_id["p-no-catalog"]
    assert missing.position == ""
    assert missing.team == ""
    assert missing.player_name == "p-no-catalog"
    assert missing.slot == "BENCH"


def test_sleeper_builder_includes_opponent_rosters_when_requested() -> None:
    state = build_canonical_league_state_from_sleeper(
        league_name="Synthetic League", season=2026, team_count=2, league_id="9999",
        owner_user_id="owner-1", rosters_raw=_SLEEPER_ROSTERS,
        players_catalog=_SLEEPER_PLAYERS_CATALOG, retrieved_at_utc="2026-09-22T00:00:00Z",
        capabilities=_sleeper_capabilities(),
        users_raw=[
            {"user_id": "owner-1", "display_name": "Me"},
            {"user_id": "owner-2", "display_name": "Rival"},
        ],
        include_opponent_rosters=True,
    )
    assert state.opponent_rosters is not None
    assert len(state.opponent_rosters) == 1
    opponent = state.opponent_rosters[0]
    assert opponent.team_id == "2"
    assert opponent.team_name == "Rival"
    assert opponent.roster[0].provider_player_id == "p-rival"
    # The owner's own team must never appear among opponents.
    assert all(
        p.provider_player_id != "p-starter"
        for team in state.opponent_rosters
        for p in team.roster
    )


def test_sleeper_builder_rejects_a_malformed_rosters_response() -> None:
    with pytest.raises(CanonicalLeagueStateError) as excinfo:
        build_canonical_league_state_from_sleeper(
            league_name="Synthetic League", season=2026, team_count=2, league_id="9999",
            owner_user_id="owner-1", rosters_raw="not-a-list",
            players_catalog=_SLEEPER_PLAYERS_CATALOG, retrieved_at_utc="2026-09-22T00:00:00Z",
            capabilities=_sleeper_capabilities(),
        )
    assert excinfo.value.kind == "MALFORMED_ROSTERS"


def test_sleeper_builder_raises_a_specific_error_when_owner_roster_is_absent() -> None:
    with pytest.raises(CanonicalLeagueStateError) as excinfo:
        build_canonical_league_state_from_sleeper(
            league_name="Synthetic League", season=2026, team_count=2, league_id="9999",
            owner_user_id="owner-not-in-any-roster", rosters_raw=_SLEEPER_ROSTERS,
            players_catalog=_SLEEPER_PLAYERS_CATALOG, retrieved_at_utc="2026-09-22T00:00:00Z",
            capabilities=_sleeper_capabilities(),
        )
    assert excinfo.value.kind == "OWN_ROSTER_NOT_FOUND"


def test_sleeper_builder_never_fabricates_faab_available_pool_or_acquisition_state() -> None:
    """The Sleeper builder is only ever fed a rosters/players fetch -- it
    must never claim to know FAAB budget, available-player pool, or
    waiver-status/clear-time/transactions it was never given."""
    state = build_canonical_league_state_from_sleeper(
        league_name="Synthetic League", season=2026, team_count=2, league_id="9999",
        owner_user_id="owner-1", rosters_raw=_SLEEPER_ROSTERS,
        players_catalog=_SLEEPER_PLAYERS_CATALOG, retrieved_at_utc="2026-09-22T00:00:00Z",
        capabilities=_sleeper_capabilities(),
    )
    assert state.faab.source == "NOT_FETCHED_THIS_REQUEST"
    assert state.faab.is_faab_league is None
    assert state.available_player_pool is None
    assert state.available_player_pool_coverage == "NONE"
    assert state.acquisition.waiver_status_supported is False
    assert state.acquisition.waiver_clear_time_utc is None
    assert state.acquisition.recent_transactions_supported is False
    assert state.acquisition.notes  # a real, honest disclosure, not silently empty


# ---------------------------------------------------------------------------
# ESPN builder (clearly-synthetic fixture, per the dispatch directive --
# never anything that could be mistaken for real ESPN/Flaim data)
# ---------------------------------------------------------------------------

_SYNTHETIC_ESPN_SNAPSHOT_RAW = {
    "profile_id": "synthetic-test-profile",
    "provider_league_id": "SYNTHETIC-ESPN-0001",
    "league_name": "Synthetic Test ESPN League (unit test fixture, not real)",
    "season": 2026,
    "team_count": 8,
    "owner_team_id": "synthetic-team-1",
    "owner_team_name": "Synthetic Owner Team",
    "roster": [
        {
            "provider_player_id": "espn-synth-1", "player_name": "Synthetic Starter",
            "position": "RB", "team": "SYN", "slot": "STARTER",
        },
        {
            "provider_player_id": "espn-synth-2", "player_name": "Synthetic Bench",
            "position": "WR", "team": "SYN", "slot": "BENCH",
        },
        {
            "provider_player_id": "espn-synth-3", "player_name": "Synthetic Reserve",
            "position": "TE", "team": "SYN", "slot": "RESERVE",
        },
    ],
    "scoring_settings": [
        {"espn_setting_name": "synthetic_ppr", "value": 1.0, "nwr_setting": "reception"},
    ],
    "scoring_completeness": "PARTIAL",
    "available_player_pool": [
        {
            "provider_player_id": "espn-synth-fa-1", "player_name": "Synthetic Free Agent",
            "position": "QB", "team": "SYN",
        },
    ],
    "available_player_pool_coverage": "BOUNDED",
    "available_player_pool_bound_description": "Synthetic test fixture: first 1 result only.",
    "retrieved_at_utc": "2026-09-22T00:00:00Z",
    "provider_as_of_utc": None,
}


def test_espn_builder_wraps_a_real_parsed_snapshot_without_mutating_it() -> None:
    snapshot = parse_espn_flaim_snapshot(_SYNTHETIC_ESPN_SNAPSHOT_RAW)
    state = build_canonical_league_state_from_espn_snapshot(snapshot)
    assert state.provider == "espn"
    assert state.provider_league_id == "SYNTHETIC-ESPN-0001"
    assert state.league_name == _SYNTHETIC_ESPN_SNAPSHOT_RAW["league_name"]
    assert state.owner_team_id == "synthetic-team-1"
    assert len(state.roster) == 3
    by_id = {p.provider_player_id: p for p in state.roster}
    assert by_id["espn-synth-1"].slot == "STARTER"
    assert by_id["espn-synth-2"].slot == "BENCH"
    assert by_id["espn-synth-3"].slot == "RESERVE"
    assert state.scoring.completeness == "PARTIAL"
    assert state.available_player_pool is not None
    assert state.available_player_pool[0].player_name == "Synthetic Free Agent"
    assert state.available_player_pool_coverage == "BOUNDED"
    # No standings/opponent-roster modeling at all -- the schema doesn't
    # carry it, so the canonical layer must not invent it either.
    assert state.opponent_rosters is None
    assert state.retrieved_at_utc == "2026-09-22T00:00:00Z"
    assert state.source.startswith("Flaim MCP")


def test_espn_builder_never_fabricates_faab_or_acquisition_state_either() -> None:
    snapshot = parse_espn_flaim_snapshot(_SYNTHETIC_ESPN_SNAPSHOT_RAW)
    state = build_canonical_league_state_from_espn_snapshot(snapshot)
    assert state.faab.source == "UNKNOWN"
    assert state.faab.is_faab_league is None
    assert state.acquisition.waiver_status_supported is False
    assert state.acquisition.recent_transactions_supported is False


def test_espn_builder_computes_capabilities_when_not_supplied() -> None:
    snapshot = parse_espn_flaim_snapshot(_SYNTHETIC_ESPN_SNAPSHOT_RAW)
    state = build_canonical_league_state_from_espn_snapshot(snapshot)
    assert state.capabilities.has_verified_identity is True
    assert state.capabilities.has_roster_data is True
    assert state.capabilities.has_scoring_settings == "PARTIAL"


def test_both_providers_produce_the_same_canonical_shape() -> None:
    """The core architectural claim: a caller consuming `state.roster` /
    `state.provider` / `state.scoring` / etc. cannot tell, from the shape
    alone, whether the state came from Sleeper or ESPN."""
    sleeper_state = build_canonical_league_state_from_sleeper(
        league_name="Synthetic League", season=2026, team_count=2, league_id="9999",
        owner_user_id="owner-1", rosters_raw=_SLEEPER_ROSTERS,
        players_catalog=_SLEEPER_PLAYERS_CATALOG, retrieved_at_utc="2026-09-22T00:00:00Z",
        capabilities=_sleeper_capabilities(),
    )
    espn_state = build_canonical_league_state_from_espn_snapshot(
        parse_espn_flaim_snapshot(_SYNTHETIC_ESPN_SNAPSHOT_RAW)
    )
    assert type(sleeper_state) is type(espn_state)
    assert {f.name for f in sleeper_state.__dataclass_fields__.values()} == {
        f.name for f in espn_state.__dataclass_fields__.values()
    }
    for state in (sleeper_state, espn_state):
        assert state.roster and all(
            hasattr(p, "provider_player_id") and hasattr(p, "slot") for p in state.roster
        )
