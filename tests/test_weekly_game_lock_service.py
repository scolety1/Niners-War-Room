from __future__ import annotations

import sys
import types
from datetime import UTC, datetime

import polars as pl

from src.services.weekly_game_lock_service import compute_weekly_game_lock


def _fake_nflreadpy_module(rows: list[dict]) -> types.ModuleType:
    """A minimal fake of the one real nflreadpy surface this module calls
    (`load_schedules(seasons=...)` -> a polars DataFrame with real nflverse
    column names) -- swapped in via `sys.modules` so this test never makes
    a real network call, but exercises the real polars filter/to_dicts
    code path this service actually uses."""

    frame = pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={
            "week": pl.Int64, "game_type": pl.Utf8, "home_team": pl.Utf8,
            "away_team": pl.Utf8, "gameday": pl.Utf8, "gametime": pl.Utf8,
        }
    )
    module = types.ModuleType("nflreadpy")
    module.load_schedules = lambda seasons: frame  # noqa: ARG005
    return module


def test_locks_a_team_whose_real_kickoff_has_already_passed(monkeypatch) -> None:
    rows = [
        {
            "week": 2, "game_type": "REG", "home_team": "BUF", "away_team": "DET",
            "gameday": "2026-09-17", "gametime": "20:15",
        },
        {
            "week": 2, "game_type": "REG", "home_team": "ATL", "away_team": "CAR",
            "gameday": "2026-09-20", "gametime": "13:00",
        },
    ]
    monkeypatch.setitem(sys.modules, "nflreadpy", _fake_nflreadpy_module(rows))
    now = datetime(2026, 9, 18, 19, 0, tzinfo=UTC)  # after BUF/DET kickoff, before ATL/CAR
    result = compute_weekly_game_lock(season=2026, week=2, now=now)
    assert result.source_status == "OK"
    assert "BUF" in result.locked_teams and "DET" in result.locked_teams
    assert "ATL" not in result.locked_teams and "CAR" not in result.locked_teams
    assert "BUF" in result.kickoff_utc_by_team


def test_unavailable_on_fetch_failure_never_guesses_a_lock_state(monkeypatch) -> None:
    module = types.ModuleType("nflreadpy")

    def _boom(seasons):  # noqa: ARG001
        raise RuntimeError("network unreachable")

    module.load_schedules = _boom
    monkeypatch.setitem(sys.modules, "nflreadpy", module)
    result = compute_weekly_game_lock(season=2026, week=2)
    assert result.source_status == "UNAVAILABLE"
    assert result.locked_teams == frozenset()
    assert result.error is not None


def test_to_dict_kickoff_map_is_a_flat_list_not_a_team_keyed_dict(monkeypatch) -> None:
    """Real, live-reproduced bug caught verifying this pass against Fantasy
    Gamers' real Week 2 data: the shared desktop API camelCase JSON-key
    transform (`camel_case_key` in `src/application/contracts.py`) treats
    EVERY dict key as a schema field name and lowercases its first
    character -- so a naive `{"BUF": "...", "DET": "..."}` dict would have
    serialized over the real API as `{"bUF": "...", "dET": "..."}`,
    corrupting every team code. `to_dict()` must emit a flat
    `[{"team": ..., "kickoffUtc": ...}, ...]` list instead, which the
    transform cannot mangle (list items are values, not dict keys).
    """

    rows = [
        {
            "week": 2, "game_type": "REG", "home_team": "BUF", "away_team": "DET",
            "gameday": "2026-09-17", "gametime": "20:15",
        },
    ]
    monkeypatch.setitem(sys.modules, "nflreadpy", _fake_nflreadpy_module(rows))
    result = compute_weekly_game_lock(season=2026, week=2)
    payload = result.to_dict()
    assert isinstance(payload["kickoffUtcByTeam"], list)
    teams = {row["team"] for row in payload["kickoffUtcByTeam"]}
    assert teams == {"BUF", "DET"}


def test_missing_gametime_leaves_team_unknown_not_locked_or_unlocked(monkeypatch) -> None:
    rows = [
        {
            "week": 2, "game_type": "REG", "home_team": "SEA", "away_team": "ARI",
            "gameday": None, "gametime": None,
        },
    ]
    monkeypatch.setitem(sys.modules, "nflreadpy", _fake_nflreadpy_module(rows))
    result = compute_weekly_game_lock(season=2026, week=2)
    assert result.source_status == "OK"
    assert "SEA" not in result.locked_teams
    assert "SEA" in result.unknown_teams
