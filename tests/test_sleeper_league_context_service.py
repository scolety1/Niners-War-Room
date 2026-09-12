"""Unit tests for `sleeper_league_context_service.py` (P1-1, 2026-09-12):
automatic NFL week + matchup/standings/playoff context, all pure functions
over raw (fixture-shaped) Sleeper JSON. Covers the acceptance directive's
required edge cases: bye week, playoff-state league, non-playoff-state
league, and malformed/missing provider data (the "provider unavailable"
fallback path).
"""

from src.services.sleeper_league_context_service import (
    build_playoff_context,
    build_standings_context,
    build_week_matchup_context,
    parse_current_nfl_week,
    team_name_by_roster_id,
)

# ---------------------------------------------------------------------------
# parse_current_nfl_week
# ---------------------------------------------------------------------------


def test_parse_current_nfl_week_reads_the_real_week_field():
    assert parse_current_nfl_week({"week": 3, "season": "2026", "season_type": "regular"}) == 3


def test_parse_current_nfl_week_falls_back_to_display_week():
    assert parse_current_nfl_week({"week": None, "display_week": 5}) == 5


def test_parse_current_nfl_week_is_none_for_malformed_or_missing_data():
    assert parse_current_nfl_week(None) is None
    assert parse_current_nfl_week({}) is None
    assert parse_current_nfl_week({"week": "not-a-week"}) is None
    assert parse_current_nfl_week({"week": -1}) is None
    assert parse_current_nfl_week("not even a dict") is None


# ---------------------------------------------------------------------------
# team_name_by_roster_id
# ---------------------------------------------------------------------------

_USERS = [
    {"user_id": "u1", "display_name": "Alice", "metadata": {"team_name": "Alice's Aces"}},
    {"user_id": "u2", "display_name": "Bob", "metadata": {}},
]
_ROSTERS = [
    {"roster_id": 1, "owner_id": "u1"},
    {"roster_id": 2, "owner_id": "u2"},
]


def test_team_name_prefers_metadata_team_name_then_display_name():
    names = team_name_by_roster_id(_ROSTERS, _USERS)
    assert names[1] == "Alice's Aces"
    assert names[2] == "Bob"


def test_team_name_falls_back_to_roster_id_label_when_unresolvable():
    names = team_name_by_roster_id([{"roster_id": 9, "owner_id": "ghost"}], [])
    assert names[9] == "Roster 9"


def test_team_name_by_roster_id_handles_malformed_input_without_crashing():
    assert team_name_by_roster_id(None, None) == {}
    assert team_name_by_roster_id("not-a-list", "not-a-list") == {}


# ---------------------------------------------------------------------------
# build_week_matchup_context
# ---------------------------------------------------------------------------


def test_matchup_context_real_opponent_and_scores():
    matchups = [
        {"roster_id": 1, "matchup_id": 5, "points": 101.5},
        {"roster_id": 2, "matchup_id": 5, "points": 88.25},
    ]
    context = build_week_matchup_context(
        week=3, own_roster_id=1, matchups=matchups, team_names={1: "Me", 2: "Rival"}
    )
    assert context["hasOpponent"] is True
    assert context["ownerPoints"] == 101.5
    assert context["opponentRosterId"] == 2
    assert context["opponentTeamName"] == "Rival"
    assert context["opponentPoints"] == 88.25
    assert context["note"] is None


def test_matchup_context_bye_week_no_matchup_id():
    matchups = [{"roster_id": 1, "matchup_id": None, "points": 0}]
    context = build_week_matchup_context(
        week=3, own_roster_id=1, matchups=matchups, team_names={1: "Me"}
    )
    assert context["hasOpponent"] is False
    assert context["opponentTeamName"] is None
    assert "bye" in context["note"].lower()


def test_matchup_context_provider_unavailable_empty_list():
    context = build_week_matchup_context(week=3, own_roster_id=1, matchups=[], team_names={})
    assert context["hasOpponent"] is False
    assert context["ownerPoints"] is None
    assert "not yet available" in context["note"]


def test_matchup_context_malformed_response_never_crashes():
    context = build_week_matchup_context(
        week=3, own_roster_id=1, matchups="not-a-list", team_names={}
    )
    assert context["hasOpponent"] is False


def test_matchup_context_own_entry_missing_from_response():
    matchups = [{"roster_id": 2, "matchup_id": 5, "points": 10}]
    context = build_week_matchup_context(
        week=3, own_roster_id=1, matchups=matchups, team_names={2: "Rival"}
    )
    assert context["hasOpponent"] is False
    assert "not yet available" in context["note"]


def test_matchup_context_opponent_unresolvable():
    matchups = [{"roster_id": 1, "matchup_id": 5, "points": 10}]
    context = build_week_matchup_context(
        week=3, own_roster_id=1, matchups=matchups, team_names={}
    )
    assert context["hasOpponent"] is False
    assert "could not be resolved" in context["note"]


# ---------------------------------------------------------------------------
# build_standings_context
# ---------------------------------------------------------------------------


def test_standings_context_real_record_and_rank():
    rosters = [
        {
            "roster_id": 1,
            "settings": {"wins": 5, "losses": 2, "ties": 0, "fpts": 850, "fpts_decimal": 50,
                         "fpts_against": 700, "fpts_against_decimal": 0},
        },
        {
            "roster_id": 2,
            "settings": {"wins": 6, "losses": 1, "ties": 0, "fpts": 900, "fpts_decimal": 0,
                         "fpts_against": 650, "fpts_against_decimal": 0},
        },
    ]
    standings = build_standings_context(
        rosters=rosters, team_names={1: "Me", 2: "Rival"}, own_roster_id=1
    )
    assert standings is not None
    # Roster 2 has more wins -> ranked first.
    assert standings["rows"][0]["teamName"] == "Rival"
    assert standings["rows"][1]["teamName"] == "Me"
    assert standings["rows"][1]["pointsFor"] == 850.5
    assert standings["ownerRank"] == 2


def test_standings_context_none_for_malformed_rosters_response():
    assert build_standings_context(rosters=None, team_names={}, own_roster_id=1) is None
    assert build_standings_context(rosters=[], team_names={}, own_roster_id=1) is None


def test_standings_context_defaults_missing_settings_to_zero_not_a_crash():
    rosters = [{"roster_id": 1}]
    standings = build_standings_context(rosters=rosters, team_names={}, own_roster_id=1)
    assert standings["rows"][0]["wins"] == 0
    assert standings["rows"][0]["pointsFor"] == 0.0


# ---------------------------------------------------------------------------
# build_playoff_context
# ---------------------------------------------------------------------------


def test_playoff_context_non_playoff_state_league():
    league = {"status": "in_season", "settings": {"playoff_week_start": 15}}
    context = build_playoff_context(
        league=league, winners_bracket=[], team_names={}, own_roster_id=1, current_week=3
    )
    assert context["leagueStatus"] == "in_season"
    assert context["playoffWeekStart"] == 15
    assert context["inPlayoffs"] is False
    assert context["bracketAvailable"] is False
    assert context["bracket"] == []


def test_playoff_context_playoff_state_league_with_real_bracket():
    league = {"status": "in_season", "settings": {"playoff_week_start": 15}}
    bracket = [
        {"r": 1, "m": 1, "t1": 1, "t2": 2, "w": 1, "l": 2},
        {"r": 2, "m": 2, "t1": 1, "t2": None, "w": None, "l": None},
    ]
    context = build_playoff_context(
        league=league,
        winners_bracket=bracket,
        team_names={1: "Me", 2: "Rival"},
        own_roster_id=1,
        current_week=16,
    )
    assert context["inPlayoffs"] is True
    assert context["bracketAvailable"] is True
    round1 = context["bracket"][0]
    assert round1["team1TeamName"] == "Me"
    assert round1["team2TeamName"] == "Rival"
    assert round1["winnerTeamName"] == "Me"
    assert round1["involvesOwner"] is True


def test_playoff_context_none_when_league_document_unreadable():
    assert build_playoff_context(
        league=None, winners_bracket=[], team_names={}, own_roster_id=1, current_week=3
    ) is None


def test_playoff_context_handles_malformed_settings_without_crashing():
    context = build_playoff_context(
        league={"status": "complete"},
        winners_bracket="not-a-list",
        team_names={},
        own_roster_id=1,
        current_week=18,
    )
    assert context["playoffWeekStart"] is None
    assert context["inPlayoffs"] is False
    assert context["bracket"] == []
