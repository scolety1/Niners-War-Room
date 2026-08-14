from __future__ import annotations

import pytest

from src.services.fantasypros_kdst_consensus_service import (
    FANTASYPROS_AUTHORITY,
    FantasyProsConsensusClient,
    FantasyProsProviderError,
    _parse_consensus,
    provider_status,
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
