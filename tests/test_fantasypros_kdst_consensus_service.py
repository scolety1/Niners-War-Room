from __future__ import annotations

import pytest

from src.services.fantasypros_kdst_consensus_service import (
    FANTASYPROS_AUTHORITY,
    FantasyProsConsensusClient,
    FantasyProsProviderError,
    _identity,
    _parse_consensus,
    provider_status,
    sleeper_free_agent_pool,
    sleeper_opponent_rosters,
    sleeper_streamer_actions,
    streamer_actions,
)
from src.services.team_code_alias_service import TEAM_CODE_ALIASES, normalize_team_code


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


def test_sleeper_dst_roster_entries_with_no_full_name_still_resolve_as_rostered() -> None:
    # Real Sleeper DST catalog shape (confirmed against a live Sleeper
    # players/nfl pull): DST entries never carry full_name/search_full_name,
    # only first_name/last_name holding the city and team name separately
    # (e.g. "Jacksonville" / "Jaguars"). FantasyPros' own consensus rows
    # report DST player_name as that same full team name -- confirmed live
    # in the running app UI ("Jacksonville Jaguars"), not a placeholder like
    # "JAX D/ST". player_team_id is the real FantasyPros K/DST consensus
    # code for Jacksonville ("JAC", reconfirmed live against the real
    # FantasyPros API this pass -- never "JAX") -- deliberately NOT "JAX"
    # here, since Sleeper's own real catalog for this same franchise
    # reports "JAX". This is the real JAC/JAX alias case.
    payload = {"players": [
        {"player_id": 1, "player_name": "Jacksonville Jaguars", "player_position_id": "DST", "player_team_id": "JAC", "rank_ecr": 1, "tier": 1},
        {"player_id": 2, "player_name": "Los Angeles Chargers", "player_position_id": "DST", "player_team_id": "LAC", "rank_ecr": 2, "tier": 1},
        {"player_id": 3, "player_name": "Houston Texans", "player_position_id": "DST", "player_team_id": "HOU", "rank_ecr": 3, "tier": 1},
    ]}
    rows = _parse_consensus(payload, season=2026, week=1, position="DST")
    actions, unmatched = sleeper_streamer_actions(
        rows,
        rosters=[
            {"owner_id": "owner", "players": ["s1"], "starters": ["s1"]},
            {"owner_id": "rival", "players": ["s2"], "starters": ["s2"]},
        ],
        # Deliberately omitting full_name/search_full_name here is the whole
        # point of this test -- that is the real Sleeper DST shape.
        players={
            "s1": {"first_name": "Jacksonville", "last_name": "Jaguars", "position": "DST", "team": "JAX"},
            "s2": {"first_name": "Los Angeles", "last_name": "Chargers", "position": "DST", "team": "LAC"},
        },
        owner_user_id="owner",
    )
    assert not unmatched, "A real DST roster entry with no full_name must still resolve to a known provider id."
    by_ecr = {value["ecr"]: value["recommendation"] for value in actions}
    assert by_ecr[1] == "START"               # Jacksonville: owner's own real starter
    assert by_ecr[2] == "ROSTERED_ELSEWHERE"  # LA Chargers: a rival's real starter -- must NOT show AVAILABLE once fixed
    assert by_ecr[3] == "ADD"                 # Houston: genuinely unrostered by anyone


def test_sleeper_dst_roster_entry_rostered_by_an_opponent_is_not_reported_available() -> None:
    payload = {"players": [
        {"player_id": 1, "player_name": "Houston Texans", "player_position_id": "DST", "player_team_id": "HOU", "rank_ecr": 1, "tier": 1},
    ]}
    rows = _parse_consensus(payload, season=2026, week=1, position="DST")
    actions, unmatched = sleeper_streamer_actions(
        rows,
        rosters=[{"owner_id": "someone_else", "players": ["s1"], "starters": ["s1"]}],
        players={"s1": {"first_name": "Houston", "last_name": "Texans", "position": "DST", "team": "HOU"}},
        owner_user_id="owner",
    )
    assert not unmatched
    assert actions[0]["recommendation"] == "ROSTERED_ELSEWHERE"
    assert actions[0]["rosterStatus"] == "ROSTERED"


def test_sleeper_k_roster_matching_is_unaffected_by_the_dst_full_name_fallback() -> None:
    # Regression guard: the new DST-only fallback branch must not change K's
    # existing, already-correct matching path (Sleeper K catalog entries
    # always carry a real full_name).
    rows = _parse_consensus(_payload(), season=2026, week=1, position="K")
    actions, unmatched = sleeper_streamer_actions(
        rows,
        rosters=[{"owner_id": "owner", "players": ["s1"], "starters": ["s1"]}],
        players={"s1": {"full_name": "K Two", "position": "K", "team": "BBB"}},
        owner_user_id="owner",
    )
    assert unmatched == ()
    assert actions[0]["recommendation"] == "START"
    assert actions[1]["recommendation"] == "ADD"


def test_identity_boundary_resolves_fantasypros_jac_against_sleeper_jax() -> None:
    # The exact canonical-boundary fix: FantasyPros' real K/DST consensus
    # API reports Jacksonville as "JAC" (reconfirmed live this pass);
    # Sleeper's real catalog reports it as "JAX". _identity() is the
    # shared boundary both sides feed through -- it must produce the SAME
    # key for both spellings of the same real franchise.
    assert _identity("Jacksonville Jaguars", "DST", "JAC") == _identity(
        "Jacksonville Jaguars", "DST", "JAX"
    )


def test_identity_boundary_leaves_ordinary_team_codes_unaffected() -> None:
    # Codes that need no aliasing must resolve identically before and
    # after normalization -- the alias table must not perturb the common
    # case.
    for team in ("HOU", "SF", "KC", "BUF", "PHI", "DET"):
        assert _identity("Some Team", "DST", team) == (
            "someteam",
            "DST",
            team,
        )


def test_normalize_team_code_covers_known_fantasypros_sleeper_aliases_and_passes_through_unknowns() -> None:
    # JAC/JAX reconfirmed live this pass against the real FantasyPros
    # K/DST consensus API and the real Sleeper players/nfl catalog. The
    # rest are carried over from other already-tested FantasyPros-facing
    # modules in this codebase (real, established aliases -- not
    # reconfirmed against THIS endpoint this pass, since it only ever
    # returns its own top-10 ranked rows per query and none of the
    # queried weeks/positions happened to include one of these teams).
    assert normalize_team_code("JAC") == "JAX"
    assert normalize_team_code("LA") == "LAR"
    assert normalize_team_code("STL") == "LAR"
    assert normalize_team_code("SD") == "LAC"
    assert normalize_team_code("OAK") == "LV"
    assert normalize_team_code("WSH") == "WAS"
    assert normalize_team_code("ARZ") == "ARI"
    # A code with no known alias passes through unchanged -- never
    # guessed, never invented.
    assert normalize_team_code("SF") == "SF"
    assert normalize_team_code("hou") == "HOU"
    assert normalize_team_code(None) == ""
    assert normalize_team_code("  jax  ") == "JAX"


def test_team_code_alias_table_never_maps_a_code_to_itself_pointlessly() -> None:
    # Sanity guard on the shared table itself: every key must be a real
    # alias (map to something different), not a no-op entry.
    for source, canonical in TEAM_CODE_ALIASES.items():
        assert source != canonical


def test_sleeper_k_roster_matching_is_unaffected_by_team_code_normalization() -> None:
    # K-regression, at the alias-table level specifically: an ordinary K
    # team code that needs no aliasing must resolve exactly as before.
    rows = _parse_consensus(_payload(), season=2026, week=1, position="K")
    actions, unmatched = sleeper_streamer_actions(
        rows,
        rosters=[{"owner_id": "owner", "players": ["s1"], "starters": ["s1"]}],
        players={"s1": {"full_name": "K Two", "position": "K", "team": "BBB"}},
        owner_user_id="owner",
    )
    assert unmatched == ()
    assert actions[0]["recommendation"] == "START"


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
