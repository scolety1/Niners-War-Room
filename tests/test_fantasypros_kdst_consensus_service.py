from __future__ import annotations

import pytest

from src.services.fantasypros_kdst_consensus_service import (
    FANTASYPROS_AUTHORITY,
    FantasyProsConsensusClient,
    FantasyProsProviderError,
    _parse_consensus,
    provider_status,
    sleeper_free_agent_pool,
    sleeper_opponent_rosters,
    sleeper_streamer_actions,
    streamer_actions,
)


def _payload():
    return {"players": [
        {"player_id": 1, "player_name": "K One", "player_position_id": "K", "player_team_id": "AAA", "rank_ecr": 2, "tier": 1},
        {"player_id": 2, "player_name": "K Two", "player_position_id": "K", "player_team_id": "BBB", "rank_ecr": 1, "tier": 1},
    ]}


def test_status_never_exposes_or_invents_a_key() -> None:
    assert not provider_status(environ={}).configured
    assert provider_status(environ={"NWR_FANTASYPROS_API_KEY": "key"}).configured


def test_k_consensus_is_external_and_streamer_actions_follow_ecr_and_roster_state() -> None:
    rows = _parse_consensus(_payload(), season=2026, week=1, position="K")
    actions = streamer_actions(rows, rostered_provider_ids={"1"}, owner_provider_ids=set())
    assert [value["recommendation"] for value in actions] == ["ADD", "ROSTERED_ELSEWHERE"]
    assert all(value["authority"] == FANTASYPROS_AUTHORITY for value in actions)


def test_sleeper_roster_filter_requires_exact_public_identity_and_preserves_start_state() -> None:
    rows = _parse_consensus(_payload(), season=2026, week=1, position="K")
    actions, unmatched = sleeper_streamer_actions(
        rows,
        rosters=[{"owner_id": "owner", "players": ["s1"], "starters": ["s1"]}],
        players={"s1": {"full_name": "K Two", "position": "K", "team": "BBB"}},
        owner_user_id="owner",
    )
    assert actions[0]["recommendation"] == "START"
    assert actions[1]["recommendation"] == "ADD"
    assert unmatched == ()


def test_provider_rejects_other_positions_and_malformed_rows() -> None:
    with pytest.raises(FantasyProsProviderError):
        FantasyProsConsensusClient(api_key="test").consensus_rankings(season=2026, position="RB")
    with pytest.raises(FantasyProsProviderError):
        _parse_consensus({"players": [{"player_id": 1, "player_name": "Bad", "player_position_id": "DST", "rank_ecr": 1}]}, season=2026, week=0, position="K")


# --- NWR Overnight V3, Lane 2: general (all-position) free-agent pool and
# opponent-roster read, reusing the same rostered-set primitive the K/DST
# streamer already relies on.


def _rosters():
    return [
        {"owner_id": "me", "roster_id": "1", "players": ["s1"], "starters": ["s1"]},
        {"owner_id": "rival", "roster_id": "2", "players": ["s2"], "starters": []},
    ]


def _players():
    return {
        "s1": {"full_name": "Rostered WR", "position": "WR", "team": "AAA", "active": True},
        "s2": {"full_name": "Rival RB", "position": "RB", "team": "BBB", "active": True},
        "s3": {"full_name": "Free Agent TE", "position": "TE", "team": "CCC", "active": True},
        "s4": {"full_name": "Retired Guy", "position": "WR", "team": "DDD", "active": False},
        "s5": {"position": "K", "team": "", "active": True},  # no name/team -- must be skipped
    }


def _users():
    return [
        {"user_id": "me", "display_name": "Me"},
        {"user_id": "rival", "display_name": "Rival Owner", "metadata": {"team_name": "Rival's Team"}},
    ]


def test_sleeper_free_agent_pool_excludes_rostered_inactive_and_incomplete_rows() -> None:
    pool = sleeper_free_agent_pool(rosters=_rosters(), players=_players(), rankings=())
    ids = {row["sleeperPlayerId"] for row in pool}
    # s1/s2 are rostered (excluded), s4 is inactive, s5 has no name/team.
    assert ids == {"s3"}
    row = pool[0]
    assert row["playerName"] == "Free Agent TE"
    assert row["position"] == "TE"
    assert row["rosterStatus"] == "AVAILABLE"
    assert row["rankingAuthority"] == "UNRANKED"
    assert row["overallRank"] is None


def test_sleeper_free_agent_pool_attaches_real_ranking_by_identity_never_invents_one() -> None:
    rankings = [
        {"playerId": "nwr-1", "playerName": "Free Agent TE", "position": "TE", "team": "CCC",
         "overallRank": 42, "positionRank": 5, "projectedPoints": 88.0,
         "replacementAdjustedValue": 12.0, "valueLabel": "Value"},
    ]
    pool = sleeper_free_agent_pool(rosters=_rosters(), players=_players(), rankings=rankings)
    row = next(r for r in pool if r["sleeperPlayerId"] == "s3")
    assert row["playerId"] == "nwr-1"
    assert row["overallRank"] == 42
    assert row["rankingAuthority"] == "NWR REDRAFT RANKING"


def test_sleeper_free_agent_pool_rejects_malformed_players_payload() -> None:
    with pytest.raises(FantasyProsProviderError):
        sleeper_free_agent_pool(rosters=_rosters(), players=["not", "a", "mapping"], rankings=())


def test_sleeper_opponent_rosters_excludes_the_owner_and_resolves_public_identity() -> None:
    opponents = sleeper_opponent_rosters(
        rosters=_rosters(), users=_users(), players=_players(), owner_user_id="me",
    )
    assert len(opponents) == 1
    opponent = opponents[0]
    assert opponent["teamName"] == "Rival's Team"
    assert opponent["ownerUserId"] == "rival"
    assert len(opponent["players"]) == 1
    assert opponent["players"][0]["playerName"] == "Rival RB"
    assert opponent["unresolvedSleeperPlayerIds"] == []


def test_sleeper_opponent_rosters_reports_unresolved_players_without_dropping_them() -> None:
    rosters = [{"owner_id": "rival", "roster_id": "2", "players": ["missing-id"], "starters": []}]
    opponents = sleeper_opponent_rosters(
        rosters=rosters, users=_users(), players=_players(), owner_user_id="me",
    )
    assert opponents[0]["unresolvedSleeperPlayerIds"] == ["missing-id"]
    assert opponents[0]["players"] == []


def test_sleeper_opponent_rosters_rejects_malformed_rosters_payload() -> None:
    with pytest.raises(FantasyProsProviderError):
        sleeper_opponent_rosters(rosters="not a list", users=_users(), players=_players(), owner_user_id="me")
