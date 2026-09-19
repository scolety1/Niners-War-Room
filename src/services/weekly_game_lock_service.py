"""Real, live game-kickoff/lock-state lookup for the weekly lineup optimizer
(NWR Sunday Readiness overnight cycle, Worker 2, section 2 / W2).

Narrow and deliberately scoped: this module answers exactly one question --
"has this NFL team's game for the given week already kicked off (as of
now)?" -- so the optimizer can pin an already-locked starter and exclude an
already-locked bench player from a new, illegal start. It does NOT touch,
extend, or depend on `injury_availability_context_service.py`, which
explicitly and deliberately gates OFF next-game/opponent/bye display on the
Injury/Availability surface pending a separate "lane-specific activation
review" (see that module's own docstring, ~L161-174). That gate governs a
DIFFERENT surface (player injury/availability display) and is intentionally
left untouched here -- this module's own output is a plain kickoff/lock
fact for the weekly LINEUP surface only, nothing about injury status, no
next-game/opponent/bye display anywhere.

Source: `nflreadpy.load_schedules(seasons=[season])` -- the SAME real,
already-registered nflverse dataset `nflverse_refresh_health_service.py`
already lists (`load_schedules()` / columns `game_id`/`home_team`/
`away_team`/`game_type`). Confirmed LIVE this pass (real 2026 week 2 pull,
2026-09-18 ~19:31 Mountain): real columns also include `gameday` (date,
e.g. "2026-09-20") and `gametime` (Eastern Time local kickoff, e.g.
"13:00") -- both genuinely present and usable for a real kickoff
timestamp, not assumed from the brief. `gametime` is the NFL's own
broadcast-schedule convention, always Eastern Time regardless of the
game's actual venue timezone (nflverse's well-known convention; not
independently re-verified against a second source this pass). Real spot
check this pass: Week 2's Thursday game (2026-09-17 20:15 ET) correctly
computed as already-locked as of this pass's real wall-clock time
(2026-09-18 evening Mountain); Week 2's Sunday games (2026-09-20) correctly
computed as not yet locked.

Honest limits, disclosed, not silently papered over:
  * A fetch failure returns `source_status="UNAVAILABLE"` with an EMPTY
    locked-team set -- never a guess that a team is or isn't locked. A
    caller with no real lock data available must treat every player as
    NOT locked (i.e. behave exactly as it did before this module existed),
    never invent a false lock or a false all-clear.
  * Postponements/reschedules are only as current as this fetch's own
    `nflverse_schedules` snapshot -- no separate live delay feed exists in
    this codebase. A `gametime`/`gameday` cell that is null/missing for a
    real scheduled game leaves that team in `unknown_teams` (not locked,
    not unlocked) rather than guessed either way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

GAME_LOCK_SOURCE = "NFLVERSE_SCHEDULES_V1"
_SCHEDULE_TZ = ZoneInfo("America/New_York")  # nflverse's own `gametime` convention, confirmed this pass


@dataclass(frozen=True)
class WeeklyGameLockResult:
    season: int
    week: int
    season_type: str
    source: str
    source_status: str  # OK | UNAVAILABLE
    fetched_at: str
    locked_teams: frozenset[str] = field(default_factory=frozenset)
    kickoff_utc_by_team: dict[str, str] = field(default_factory=dict)
    unknown_teams: frozenset[str] = field(default_factory=frozenset)
    issues: tuple[str, ...] = ()
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "season": self.season,
            "week": self.week,
            "seasonType": self.season_type,
            "source": self.source,
            "sourceStatus": self.source_status,
            "fetchedAt": self.fetched_at,
            "lockedTeams": sorted(self.locked_teams),
            # A flat list of {team, kickoffUtc}, NOT a dict keyed by team
            # code -- the shared desktop API camelCase JSON-key transform
            # (`camel_case_key` / `public_json_value` in
            # `src/application/contracts.py`) treats every dict key as a
            # schema field name and lowercases its first character (e.g.
            # "BUF" -> "bUF"), a real, live-reproduced corruption of this
            # exact field caught this pass against Fantasy Gamers' real
            # Week 2 data. Same established fix pattern this codebase
            # already uses for other arbitrary-string-keyed maps (see
            # `desktop_facade.py`'s K/DST `positions` flattening).
            "kickoffUtcByTeam": [
                {"team": team, "kickoffUtc": kickoff} for team, kickoff in sorted(self.kickoff_utc_by_team.items())
            ],
            "unknownTeams": sorted(self.unknown_teams),
            "issues": list(self.issues),
            "error": self.error,
        }


_GAME_TYPE_FILTER: dict[str, object] = {
    "regular": "REG",
    "pre": "PRE",
    "post": frozenset({"WC", "DIV", "CON", "SB"}),
}


def unavailable_weekly_game_lock_result(
    *, season: int, week: int, season_type: str, fetched_at: datetime, issue: str, error: str | None = None
) -> WeeklyGameLockResult:
    return WeeklyGameLockResult(
        season=season, week=week, season_type=season_type, source=GAME_LOCK_SOURCE,
        source_status="UNAVAILABLE", fetched_at=fetched_at.isoformat(), issues=(issue,), error=error,
    )


def compute_weekly_game_lock(
    *, season: int, week: int, season_type: str = "regular", now: datetime | None = None
) -> WeeklyGameLockResult:
    """Real, live nflverse schedule pull -> which teams' games (this real
    season/week) have already kicked off as of `now` (defaults to real
    wall-clock UTC). Read-only; never writes anything; never raises -- a
    fetch/parse failure is returned as an honest UNAVAILABLE result so a
    caller can degrade to "no real lock data this pass" instead of
    crashing the whole weekly-lineup request over a best-effort input.
    """

    fetched_at = (now or datetime.now(UTC)).astimezone(UTC)
    try:
        import nflreadpy as nfl  # local import -- same lazy pattern other nflverse-consuming services in this repo use
    except Exception as exc:  # noqa: BLE001 - honest, surfaced failure
        return unavailable_weekly_game_lock_result(
            season=season, week=week, season_type=season_type, fetched_at=fetched_at,
            issue="nflreadpy is not importable in this environment.", error=str(exc),
        )
    try:
        frame = nfl.load_schedules(seasons=[season])
        wanted = _GAME_TYPE_FILTER.get(season_type, "REG")
        rows = frame.filter(frame["week"] == week)
        if isinstance(wanted, frozenset):
            rows = rows.filter(rows["game_type"].is_in(list(wanted)))
        else:
            rows = rows.filter(rows["game_type"] == wanted)
        records = rows.to_dicts()
    except Exception as exc:  # noqa: BLE001 - real network/parsing failure, surfaced honestly
        return unavailable_weekly_game_lock_result(
            season=season, week=week, season_type=season_type, fetched_at=fetched_at,
            issue="nflverse schedules fetch failed.", error=str(exc),
        )

    locked: set[str] = set()
    unknown: set[str] = set()
    kickoff_by_team: dict[str, str] = {}
    issues: list[str] = []
    for record in records:
        home = str(record.get("home_team") or "").upper().strip()
        away = str(record.get("away_team") or "").upper().strip()
        gameday = record.get("gameday")
        gametime = record.get("gametime")
        if not gameday or not gametime:
            for team in (home, away):
                if team:
                    unknown.add(team)
            continue
        try:
            naive = datetime.strptime(f"{gameday} {gametime}", "%Y-%m-%d %H:%M")
            kickoff_utc = naive.replace(tzinfo=_SCHEDULE_TZ).astimezone(UTC)
        except ValueError:
            issues.append(f"Unparseable kickoff for {away}@{home}: {gameday!r} {gametime!r}.")
            for team in (home, away):
                if team:
                    unknown.add(team)
            continue
        for team in (home, away):
            if not team:
                continue
            kickoff_by_team[team] = kickoff_utc.isoformat()
            if kickoff_utc <= fetched_at:
                locked.add(team)
    if not records:
        issues.append(f"No real nflverse schedule rows found for season={season} week={week}.")
    return WeeklyGameLockResult(
        season=season, week=week, season_type=season_type, source=GAME_LOCK_SOURCE,
        source_status="OK", fetched_at=fetched_at.isoformat(),
        locked_teams=frozenset(locked), kickoff_utc_by_team=kickoff_by_team,
        unknown_teams=frozenset(unknown), issues=tuple(issues),
    )
