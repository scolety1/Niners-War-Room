"""Automatic NFL week + matchup/standings/playoff context (P1-1, 2026-09-12).

Closes a real, previously-disclosed gap: `redraft_league_workspace_context`
always passed `current_week=None` to `LeagueWorkspaceContext`
(`league_workspace_context_service.py`), and `league_lifecycle_service.py`'s
own module docstring recorded "this repository has no live NFL-calendar/
season signal (no wrapper around Sleeper's `GET /v1/state/nfl` or
equivalent exists anywhere in `src/services`, confirmed by search)". This
module is that wrapper -- plus the matchup/standings/playoff-bracket
context built on top of it.

Every function here is a PURE function over already-fetched Sleeper JSON
(the facade performs the actual HTTP reads, same division of labor as
`fantasypros_kdst_consensus_service.sleeper_opponent_rosters`). Nothing here
infers, estimates, or simulates a fact Sleeper does not directly return --
a malformed/missing/empty response always degrades to `None` or an honest
"unavailable" note, never a fabricated value. The one derived field
(`inPlayoffs`) is a plain week >= playoff_week_start comparison over two
raw Sleeper-sourced integers, not a prediction or a simulation.

Team-name resolution (`team_name_by_roster_id`) intentionally mirrors the
exact precedent already established by `sleeper_opponent_rosters`
(`metadata.team_name` -> `display_name` -> `username` -> `f"Roster {id}"`)
so this pass introduces no second, drifting team-identity rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# NFL weeks realistically run 1-18 (regular season) with the postseason
# folded into the same numbering by Sleeper; a small extra margin (22) is
# tolerated for a stale/unusual provider value without accepting garbage
# (e.g. a negative number or a string that isn't a plain integer).
_MIN_PLAUSIBLE_WEEK = 1
_MAX_PLAUSIBLE_WEEK = 22


def _as_plausible_week(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().lstrip("-").isdigit():
        parsed = int(value.strip())
    else:
        return None
    if _MIN_PLAUSIBLE_WEEK <= parsed <= _MAX_PLAUSIBLE_WEEK:
        return parsed
    return None


def parse_current_nfl_week(state: Any) -> int | None:
    """Extract the current NFL week from a raw Sleeper `GET /state/nfl`
    response. Prefers `week` (the raw current week); falls back to
    `display_week` (Sleeper's own "what to show the user" field) only if
    `week` is missing/malformed. Returns None -- never a guess -- for any
    response shape that isn't a real, plausible week number."""

    if not isinstance(state, Mapping):
        return None
    for key in ("week", "display_week"):
        parsed = _as_plausible_week(state.get(key))
        if parsed is not None:
            return parsed
    return None


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def _safe_points(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def team_name_by_roster_id(rosters: Any, users: Any) -> dict[Any, str]:
    """Same team-identity precedent as `sleeper_opponent_rosters`, reused
    here so matchup/standings/playoff context never invents a second team-
    naming rule."""

    if not isinstance(rosters, list):
        return {}
    user_by_id: dict[str, Mapping[str, Any]] = {}
    if isinstance(users, list):
        for user in users:
            if isinstance(user, Mapping):
                user_by_id[str(user.get("user_id") or "")] = user
    names: dict[Any, str] = {}
    for roster in rosters:
        if not isinstance(roster, Mapping):
            continue
        roster_id = roster.get("roster_id")
        owner_id = str(roster.get("owner_id") or "")
        user = user_by_id.get(owner_id, {})
        metadata = user.get("metadata") if isinstance(user.get("metadata"), Mapping) else {}
        team_name = str(
            metadata.get("team_name")
            or user.get("display_name")
            or user.get("username")
            or f"Roster {roster_id}"
        ).strip()
        names[roster_id] = team_name or f"Roster {roster_id}"
    return names


def _unavailable_matchup(week: int, note: str, owner_points: float | None = None) -> dict[str, Any]:
    return {
        "week": week,
        "hasOpponent": False,
        "ownerPoints": owner_points,
        "opponentRosterId": None,
        "opponentTeamName": None,
        "opponentPoints": None,
        "note": note,
    }


def build_week_matchup_context(
    *,
    week: int,
    own_roster_id: Any,
    matchups: Any,
    team_names: Mapping[Any, str],
) -> dict[str, Any]:
    """The owner's own matchup for `week`, from a raw Sleeper
    `GET /league/{id}/matchups/{week}` response. Handles every honest
    degraded shape without crashing or fabricating an opponent:
    - No data at all yet (empty/malformed list): "unavailable" note.
    - A bye week (owner's entry has no `matchup_id`): "bye week" note,
      the owner's own points (if scored) still shown.
    - An opponent that can't be resolved (odd data, not a real Sleeper
      shape): "could not be resolved" note.
    """

    if not isinstance(matchups, list) or not matchups:
        return _unavailable_matchup(week, "Matchup data is not yet available for this week.")
    own_entry = next(
        (
            entry
            for entry in matchups
            if isinstance(entry, Mapping) and entry.get("roster_id") == own_roster_id
        ),
        None,
    )
    if own_entry is None:
        return _unavailable_matchup(week, "Matchup data is not yet available for this week.")
    owner_points = _safe_points(own_entry.get("points"))
    matchup_id = own_entry.get("matchup_id")
    if matchup_id is None:
        return _unavailable_matchup(
            week, "Bye week -- no opponent is scheduled this week.", owner_points
        )
    opponent_entry = next(
        (
            entry
            for entry in matchups
            if isinstance(entry, Mapping)
            and entry.get("matchup_id") == matchup_id
            and entry.get("roster_id") != own_roster_id
        ),
        None,
    )
    if opponent_entry is None:
        return _unavailable_matchup(
            week, "Opponent could not be resolved for this week.", owner_points
        )
    opponent_roster_id = opponent_entry.get("roster_id")
    return {
        "week": week,
        "hasOpponent": True,
        "ownerPoints": owner_points,
        "opponentRosterId": opponent_roster_id,
        "opponentTeamName": team_names.get(opponent_roster_id) or f"Roster {opponent_roster_id}",
        "opponentPoints": _safe_points(opponent_entry.get("points")),
        "note": None,
    }


def build_standings_context(
    *,
    rosters: Any,
    team_names: Mapping[Any, str],
    own_roster_id: Any,
) -> dict[str, Any] | None:
    """Real record/points-for standings, derived entirely from each
    roster's own `settings` block on a raw Sleeper `GET /league/{id}/
    rosters` response -- no simulated finish, no playoff-odds projection.
    Sort is wins (ties counted as half a win) desc, then points-for desc,
    the same convention Sleeper's own standings view uses. Returns None
    (not a fabricated empty table) when the rosters response itself is
    missing/malformed."""

    if not isinstance(rosters, list) or not rosters:
        return None
    rows: list[dict[str, Any]] = []
    for roster in rosters:
        if not isinstance(roster, Mapping):
            continue
        roster_id = roster.get("roster_id")
        settings = roster.get("settings") if isinstance(roster.get("settings"), Mapping) else {}
        wins = _safe_int(settings.get("wins"))
        losses = _safe_int(settings.get("losses"))
        ties = _safe_int(settings.get("ties"))
        points_for = _safe_float(settings.get("fpts")) + _safe_float(settings.get("fpts_decimal")) / 100.0
        points_against = (
            _safe_float(settings.get("fpts_against"))
            + _safe_float(settings.get("fpts_against_decimal")) / 100.0
        )
        rows.append(
            {
                "rosterId": roster_id,
                "teamName": team_names.get(roster_id) or f"Roster {roster_id}",
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "pointsFor": round(points_for, 2),
                "pointsAgainst": round(points_against, 2),
                "isOwner": roster_id == own_roster_id,
            }
        )
    if not rows:
        return None
    rows.sort(key=lambda row: (-(row["wins"] * 2 + row["ties"]), -row["pointsFor"]))
    owner_rank = next((index + 1 for index, row in enumerate(rows) if row["isOwner"]), None)
    return {"rows": rows, "ownerRank": owner_rank}


def build_playoff_context(
    *,
    league: Any,
    winners_bracket: Any,
    team_names: Mapping[Any, str],
    own_roster_id: Any,
    current_week: int | None,
) -> dict[str, Any] | None:
    """Raw league status + playoff bracket, from a raw Sleeper
    `GET /league/{id}` response and (once Sleeper has generated one)
    `GET /league/{id}/winners_bracket`. `inPlayoffs` is a plain
    `current_week >= playoff_week_start` comparison over two raw
    provider-sourced integers -- not a prediction. `bracket` is empty
    (never fabricated) for a non-playoff-state league or one where
    Sleeper has not generated the bracket yet; `bracketAvailable` makes
    that distinction explicit for the UI. Returns None only when the
    league document itself could not be read at all."""

    if not isinstance(league, Mapping):
        return None
    league_status = str(league.get("status") or "").strip() or None
    settings = league.get("settings") if isinstance(league.get("settings"), Mapping) else {}
    playoff_week_start = _as_plausible_week(settings.get("playoff_week_start"))
    in_playoffs = bool(
        current_week is not None
        and playoff_week_start is not None
        and current_week >= playoff_week_start
    )
    bracket: list[dict[str, Any]] = []
    if isinstance(winners_bracket, list):
        for entry in winners_bracket:
            if not isinstance(entry, Mapping):
                continue
            team1_id = entry.get("t1")
            team2_id = entry.get("t2")
            winner_id = entry.get("w")
            bracket.append(
                {
                    "round": entry.get("r"),
                    "team1RosterId": team1_id,
                    "team1TeamName": team_names.get(team1_id) if team1_id is not None else None,
                    "team2RosterId": team2_id,
                    "team2TeamName": team_names.get(team2_id) if team2_id is not None else None,
                    "winnerRosterId": winner_id,
                    "winnerTeamName": team_names.get(winner_id) if winner_id is not None else None,
                    "involvesOwner": own_roster_id in (team1_id, team2_id),
                }
            )
    return {
        "leagueStatus": league_status,
        "playoffWeekStart": playoff_week_start,
        "inPlayoffs": in_playoffs,
        "bracketAvailable": bool(bracket),
        "bracket": bracket,
    }
