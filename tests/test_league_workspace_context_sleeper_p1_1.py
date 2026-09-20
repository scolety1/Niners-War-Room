"""Facade-level wiring tests for P1-1 (automatic NFL week + matchup/
standings/playoff context on `LeagueWorkspaceContext`), 2026-09-12.

Follows the exact same mock-Sleeper pattern already established by
`test_desktop_facade_architecture_wiring.py::
test_kdst_streamer_response_carries_trace_ids_and_league_snapshot_id`
(a local profile, re-saved as `provider="sleeper"`, with a hand-written
`sleeper_imports/<id>.json` receipt, and `SleeperHttpClient.get_json`
monkeypatched to a path-dispatching fake) -- fixture-shaped data, not a
real network call, disclosed here as such.

Covers the acceptance directive's required scenarios: a bye-week/no-
matchup edge case, a playoff-state league, a non-playoff-state league,
league switching (context must not leak between leagues), and
provider-unavailable fallback (falls back to manual/null gracefully).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_sleeper_profile(store: Path, facade: DesktopBackendFacade, *, league_id: str, owner_user_id: str, league_name: str) -> str:
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name=league_name)
    profile_id = created.data["profile"]["profileId"]
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id=league_id))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": league_id, "name": league_name},
                "owner": {"user_id": owner_user_id},
            }
        ),
        encoding="utf-8",
    )
    return profile_id


def _fresh_facade(tmp_path: Path) -> tuple[DesktopBackendFacade, Path]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    return facade, store


_ROSTERS_9999 = [
    {"owner_id": "owner-1", "roster_id": 1, "players": ["p-1"],
     "settings": {"wins": 5, "losses": 2, "ties": 0, "fpts": 800, "fpts_decimal": 0,
                  "fpts_against": 700, "fpts_against_decimal": 0}},
    {"owner_id": "owner-2", "roster_id": 2, "players": ["p-2"],
     "settings": {"wins": 6, "losses": 1, "ties": 0, "fpts": 900, "fpts_decimal": 0,
                  "fpts_against": 650, "fpts_against_decimal": 0}},
]
_USERS_9999 = [
    {"user_id": "owner-1", "display_name": "Owner One", "metadata": {"team_name": "Team One"}},
    {"user_id": "owner-2", "display_name": "Owner Two", "metadata": {"team_name": "Team Two"}},
]


def test_current_week_populated_from_real_sleeper_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, store = _fresh_facade(tmp_path)
    profile_id = _make_sleeper_profile(store, facade, league_id="9999", owner_user_id="owner-1", league_name="League A")
    facade.activate_redraft_profile(profile_id)

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "state/nfl":
            return {"week": 4, "season": "2026", "season_type": "regular", "display_week": 4}
        if path == "league/9999/rosters":
            return _ROSTERS_9999
        if path == "league/9999/users":
            return _USERS_9999
        if path == "league/9999/matchups/4":
            return [
                {"roster_id": 1, "matchup_id": 10, "points": 105.2},
                {"roster_id": 2, "matchup_id": 10, "points": 98.4},
            ]
        if path == "league/9999":
            return {"status": "in_season", "settings": {"playoff_week_start": 15}}
        if path == "league/9999/winners_bracket":
            return []
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    context = facade.redraft_league_workspace_context().data
    assert context["currentWeek"] == 4
    assert not any("not automatically sourced" in issue for issue in context["issues"])

    # Matchup context: real opponent + scores.
    assert context["matchup"]["hasOpponent"] is True
    assert context["matchup"]["opponentTeamName"] == "Team Two"
    assert context["matchup"]["ownerPoints"] == 105.2
    assert context["matchup"]["opponentPoints"] == 98.4

    # Standings context: Team Two (6-1) ranks ahead of the owner (5-2).
    assert context["standings"]["rows"][0]["teamName"] == "Team Two"
    assert context["standings"]["ownerRank"] == 2

    # Non-playoff-state league: real settings, honestly not-yet-in-playoffs.
    assert context["playoff"]["leagueStatus"] == "in_season"
    assert context["playoff"]["inPlayoffs"] is False
    assert context["playoff"]["bracketAvailable"] is False


def test_bye_week_edge_case_no_opponent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, store = _fresh_facade(tmp_path)
    profile_id = _make_sleeper_profile(store, facade, league_id="9999", owner_user_id="owner-1", league_name="League A")
    facade.activate_redraft_profile(profile_id)

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "state/nfl":
            return {"week": 4}
        if path == "league/9999/rosters":
            return _ROSTERS_9999
        if path == "league/9999/users":
            return _USERS_9999
        if path == "league/9999/matchups/4":
            # Only the owner has an entry, with no matchup_id -- a bye week.
            return [{"roster_id": 1, "matchup_id": None, "points": 0}]
        if path == "league/9999":
            return {"status": "in_season", "settings": {"playoff_week_start": 15}}
        if path == "league/9999/winners_bracket":
            return []
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    context = facade.redraft_league_workspace_context().data
    assert context["currentWeek"] == 4
    assert context["matchup"]["hasOpponent"] is False
    assert "bye" in context["matchup"]["note"].lower()


def test_playoff_state_league_with_real_bracket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, store = _fresh_facade(tmp_path)
    profile_id = _make_sleeper_profile(store, facade, league_id="9999", owner_user_id="owner-1", league_name="League A")
    facade.activate_redraft_profile(profile_id)

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "state/nfl":
            return {"week": 16}
        if path == "league/9999/rosters":
            return _ROSTERS_9999
        if path == "league/9999/users":
            return _USERS_9999
        if path == "league/9999/matchups/16":
            return [
                {"roster_id": 1, "matchup_id": 1, "points": 110.0},
                {"roster_id": 2, "matchup_id": 1, "points": 95.0},
            ]
        if path == "league/9999":
            return {"status": "in_season", "settings": {"playoff_week_start": 15}}
        if path == "league/9999/winners_bracket":
            return [{"r": 1, "m": 1, "t1": 1, "t2": 2, "w": None, "l": None}]
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    context = facade.redraft_league_workspace_context().data
    assert context["playoff"]["inPlayoffs"] is True
    assert context["playoff"]["bracketAvailable"] is True
    assert context["playoff"]["bracket"][0]["team1TeamName"] == "Team One"
    assert context["playoff"]["bracket"][0]["involvesOwner"] is True


def test_provider_unavailable_falls_back_to_null_without_crashing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, store = _fresh_facade(tmp_path)
    profile_id = _make_sleeper_profile(store, facade, league_id="9999", owner_user_id="owner-1", league_name="League A")
    facade.activate_redraft_profile(profile_id)

    def _fake_get_json(self: Any, path: str) -> Any:
        raise OSError("simulated network failure")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    context = facade.redraft_league_workspace_context().data
    assert context["currentWeek"] is None
    assert context["matchup"] is None
    assert context["standings"] is None
    assert context["playoff"] is None
    assert any("Current NFL week could not be read from Sleeper" in issue for issue in context["issues"])


def test_local_non_sleeper_profile_has_no_provider_week_and_says_so(tmp_path: Path) -> None:
    facade, store = _fresh_facade(tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="Local League")
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)

    context = facade.redraft_league_workspace_context().data
    assert context["currentWeek"] is None
    assert context["matchup"] is None
    assert context["standings"] is None
    assert context["playoff"] is None
    assert any("not automatically sourced" in issue for issue in context["issues"])


def test_league_switch_does_not_leak_context_between_leagues(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, store = _fresh_facade(tmp_path)
    profile_a = _make_sleeper_profile(store, facade, league_id="9999", owner_user_id="owner-1", league_name="League A")
    profile_b = _make_sleeper_profile(store, facade, league_id="8888", owner_user_id="owner-9", league_name="League B")

    rosters_b = [
        {"owner_id": "owner-9", "roster_id": 1, "players": [],
         "settings": {"wins": 1, "losses": 6, "ties": 0, "fpts": 500, "fpts_decimal": 0,
                      "fpts_against": 800, "fpts_against_decimal": 0}},
        {"owner_id": "owner-10", "roster_id": 2, "players": [],
         "settings": {"wins": 6, "losses": 1, "ties": 0, "fpts": 900, "fpts_decimal": 0,
                      "fpts_against": 600, "fpts_against_decimal": 0}},
    ]
    users_b = [
        {"user_id": "owner-9", "display_name": "Owner Nine", "metadata": {"team_name": "League B Mine"}},
        {"user_id": "owner-10", "display_name": "Owner Ten", "metadata": {"team_name": "League B Rival"}},
    ]

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "state/nfl":
            return {"week": 4}
        if path == "league/9999/rosters":
            return _ROSTERS_9999
        if path == "league/9999/users":
            return _USERS_9999
        if path == "league/9999/matchups/4":
            return [
                {"roster_id": 1, "matchup_id": 10, "points": 105.2},
                {"roster_id": 2, "matchup_id": 10, "points": 98.4},
            ]
        if path == "league/9999":
            return {"status": "in_season", "settings": {"playoff_week_start": 15}}
        if path == "league/9999/winners_bracket":
            return []
        if path == "league/8888/rosters":
            return rosters_b
        if path == "league/8888/users":
            return users_b
        if path == "league/8888/matchups/4":
            return [
                {"roster_id": 1, "matchup_id": 20, "points": 55.0},
                {"roster_id": 2, "matchup_id": 20, "points": 130.0},
            ]
        if path == "league/8888":
            return {"status": "in_season", "settings": {"playoff_week_start": 15}}
        if path == "league/8888/winners_bracket":
            return []
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    facade.activate_redraft_profile(profile_a)
    context_a = facade.redraft_league_workspace_context().data
    assert context_a["profileId"] == profile_a
    assert context_a["matchup"]["opponentTeamName"] == "Team Two"
    assert context_a["standings"]["rows"][0]["teamName"] == "Team Two"

    facade.activate_redraft_profile(profile_b)
    context_b = facade.redraft_league_workspace_context().data
    assert context_b["profileId"] == profile_b
    # Real, distinct data for League B -- nothing from League A leaked through.
    assert context_b["matchup"]["opponentTeamName"] == "League B Rival"
    assert context_b["matchup"]["ownerPoints"] == 55.0
    assert context_b["standings"]["rows"][0]["teamName"] == "League B Rival"
    assert context_b["standings"]["ownerRank"] == 2
    assert context_a["leagueSnapshotId"] != context_b["leagueSnapshotId"]
