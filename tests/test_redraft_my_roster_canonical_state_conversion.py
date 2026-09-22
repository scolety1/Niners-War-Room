"""Waiver-night hardening cycle, Worker 3 (2026-09-22): regression tests
for `redraft_my_roster`'s conversion to source its roster from the new
`CanonicalLeagueState` boundary (`canonical_league_state_service.py`)
instead of an inline raw Sleeper rosters/players fetch+lookup.

Three things must all hold:
  1. Sleeper-still-works: real receipt-shaped fixtures produce byte-
     identical rows/ordering/leagueId to the pre-conversion behavior.
  2. Sleeper failure modes still map to the exact same FacadeError code/
     message/status as before (malformed rosters, owner roster missing,
     network failure).
  3. ESPN-still-honest: a profile with no real ESPN snapshot yet (both
     real ESPN leagues tonight, KHA/403N18th) still 409s -- now via a
     more specific code -- and a profile WITH a real, clearly-synthetic
     test snapshot now genuinely serves roster rows, proving the
     architecture is ready for real ESPN data without further code
     changes to this method.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="My Roster Canonical League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id="9999"))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "My Roster Canonical League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


def _facade_with_espn_profile(tmp_path: Path) -> tuple[DesktopBackendFacade, str, Path]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="10_TEAM_1QB_STANDARD", league_name="Synthetic ESPN League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    # Real ESPN profiles in this codebase never carry a `provider_league_
    # id` on `LeagueProfile` itself (`validate_profile` structurally
    # rejects it for a non-Sleeper provider -- matches the real, live-
    # confirmed KHA/403N18th profiles, both `provider_league_id: null`;
    # ESPN league identity lives in the snapshot instead). Only `provider`
    # flips.
    save_profile(store, replace(profile, provider="espn"))
    return facade, profile_id, store


_ROSTERS = [
    {
        "owner_id": "owner-1",
        "roster_id": "1",
        "players": ["p-starter", "p-bench"],
        "starters": ["p-starter"],
    },
    {"owner_id": "owner-2", "roster_id": "2", "players": ["p-rival"], "starters": ["p-rival"]},
]
_PLAYERS = {
    "p-starter": {"full_name": "Christian McCaffrey", "position": "RB", "team": "sf"},
    "p-bench": {"full_name": "Justin Jefferson", "position": "WR", "team": "min"},
    "p-rival": {"full_name": "Josh Allen", "position": "QB", "team": "buf"},
}


def _fake_get_json(self: Any, path: str) -> Any:
    if path == "league/9999/rosters":
        return _ROSTERS
    if path == "players/nfl":
        return _PLAYERS
    raise AssertionError(f"unexpected Sleeper GET path in test: {path}")


# ---------------------------------------------------------------------------
# 1-2. Sleeper: unregressed rows + unregressed error codes.
# ---------------------------------------------------------------------------


def test_my_roster_sleeper_rows_unregressed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    result = facade.redraft_my_roster().data
    assert result["leagueId"] == "9999"
    assert result["writeBehavior"] == "NO_SLEEPER_WRITES"
    rows = result["roster"]
    assert len(rows) == 2
    by_id = {row["sleeperPlayerId"]: row for row in rows}
    starter_row = by_id["p-starter"]
    assert starter_row["playerName"] == "Christian McCaffrey"
    assert starter_row["position"] == "RB"
    assert starter_row["team"] == "SF"
    assert starter_row["starter"] is True
    bench_row = by_id["p-bench"]
    assert bench_row["starter"] is False
    # Sort order unregressed: starters first, then position, then name.
    assert rows[0]["sleeperPlayerId"] == "p-starter"


def test_my_roster_sleeper_unmatched_identity_is_honest_not_a_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No governed ranking exists to match against by default for a fresh
    profile with no ranking loaded via bootstrap's real seed in this
    fixture's preset -- exercise the no-catalog-entry fallback path
    directly instead, since that's the one this conversion pass most
    directly touched (see `_sleeper_roster_player`'s docstring)."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _fake_get_json_with_unknown_player(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {
                    "owner_id": "owner-1", "roster_id": "1",
                    "players": ["p-starter", "p-totally-unknown"], "starters": ["p-starter"],
                },
            ]
        if path == "players/nfl":
            return _PLAYERS
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json_with_unknown_player
    )
    result = facade.redraft_my_roster().data
    by_id = {row["sleeperPlayerId"]: row for row in result["roster"]}
    unknown_row = by_id["p-totally-unknown"]
    assert unknown_row["playerName"] == "p-totally-unknown"
    assert unknown_row["position"] == ""
    assert unknown_row["team"] == ""
    assert unknown_row["canonicalPlayerId"] is None
    assert unknown_row["identityStatus"] == "UNMATCHED_IDENTITY"


def test_my_roster_sleeper_malformed_rosters_response_unregressed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _malformed(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return "not-a-list"
        if path == "players/nfl":
            return _PLAYERS
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _malformed)
    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "REDRAFT_MY_ROSTER_READ_FAILED"
    assert excinfo.value.status == 503


def test_my_roster_sleeper_owner_roster_not_found_unregressed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _no_owner_roster(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [{"owner_id": "somebody-else", "players": [], "starters": []}]
        if path == "players/nfl":
            return _PLAYERS
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _no_owner_roster)
    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "REDRAFT_MY_ROSTER_NOT_FOUND"
    assert excinfo.value.status == 409


def test_my_roster_sleeper_network_failure_unregressed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _raise_oserror(self: Any, path: str) -> Any:
        raise OSError("simulated network failure")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _raise_oserror)
    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "REDRAFT_MY_ROSTER_READ_FAILED"
    assert excinfo.value.status == 503


# ---------------------------------------------------------------------------
# 3. ESPN: honest-block without a snapshot, real service with one.
# ---------------------------------------------------------------------------


def test_my_roster_espn_without_a_snapshot_still_honestly_blocks(tmp_path: Path) -> None:
    """Both real ESPN leagues tonight (KHA, 403 N 18th) have no real
    snapshot AND no Sleeper receipt -- exactly this shape. Real finding
    from writing this test: the SHARED `_active_profile_with_capabilities`
    pre-check (step 2, unchanged, same one every other caller already
    uses) rejects this case with `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED`
    BEFORE `_resolve_canonical_league_state()`'s own ESPN-snapshot branch
    is ever reached -- since neither a receipt nor a snapshot exists,
    `has_verified_identity` is already False at step 2. This is the EXACT
    same code the pre-conversion `_active_sleeper_context()` path also
    produced for these two real profiles (Worker 2 live-confirmed this
    exact code for KHA/403N18th's `my-roster` call tonight) -- zero
    regression, not a new/different block. See
    `test_my_roster_espn_snapshot_required_when_identity_is_otherwise_
    verified` below for the (rarer, edge-case) scenario that actually
    reaches the new `ESPN_REDRAFT_SNAPSHOT_REQUIRED` code."""
    facade, _profile_id, _store = _facade_with_espn_profile(tmp_path)
    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED"
    assert excinfo.value.status == 409


def test_my_roster_espn_snapshot_required_when_identity_is_otherwise_verified(
    tmp_path: Path,
) -> None:
    """The real, narrower scenario that reaches the NEW
    `ESPN_REDRAFT_SNAPSHOT_REQUIRED` code: a profile whose capability
    check passes (verified identity via a Sleeper receipt happening to
    exist on disk for this profile id -- e.g. a stale leftover from
    switching a profile's provider) but whose provider is now `espn` and
    has no real ESPN snapshot. Confirms `_resolve_canonical_league_state`
    dispatches on `selected.provider`, not on which receipt made the
    capability check pass."""
    facade, profile_id, store = _facade_with_espn_profile(tmp_path)
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "Stale Receipt"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "ESPN_REDRAFT_SNAPSHOT_REQUIRED"
    assert excinfo.value.status == 409


def test_my_roster_espn_with_a_real_synthetic_snapshot_serves_real_rows(tmp_path: Path) -> None:
    """The architectural claim under test: once a real ESPN/Flaim snapshot
    file exists for a profile, `redraft_my_roster` serves real roster rows
    from it automatically -- with NO further code change to this method.
    The snapshot content here is a deliberately-labeled synthetic test
    fixture, never anything resembling real ESPN/Flaim data, per the
    dispatch directive."""
    facade, profile_id, store = _facade_with_espn_profile(tmp_path)
    snapshot_dir = store / "espn_flaim_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "profile_id": profile_id,
                "provider_league_id": "SYNTHETIC-ESPN-0002",
                "league_name": "Synthetic ESPN League (unit test fixture, not real)",
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
                ],
                "scoring_settings": [],
                "scoring_completeness": "PARTIAL",
                "available_player_pool": [],
                "available_player_pool_coverage": "NONE",
                "available_player_pool_bound_description": None,
                "retrieved_at_utc": "2026-09-22T00:00:00Z",
                "provider_as_of_utc": None,
            }
        ),
        encoding="utf-8",
    )

    result = facade.redraft_my_roster().data
    assert result["leagueId"] == "SYNTHETIC-ESPN-0002"
    rows = result["roster"]
    assert len(rows) == 2
    by_id = {row["sleeperPlayerId"]: row for row in rows}
    assert by_id["espn-synth-1"]["playerName"] == "Synthetic Starter"
    assert by_id["espn-synth-1"]["starter"] is True
    assert by_id["espn-synth-2"]["starter"] is False


def test_my_roster_espn_with_a_malformed_snapshot_file_is_honest_not_a_crash(
    tmp_path: Path,
) -> None:
    """Real finding: a malformed snapshot file alone, with no Sleeper
    receipt, is caught by the SAME shared capability pre-check (it
    swallows `EspnFlaimSnapshotError` into `espn_snapshot=None`, per
    `_league_capabilities_for_profile`'s own established, pre-existing
    try/except -- not something this pass changed), so this also
    surfaces as the pre-existing `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED`,
    never reaching `_resolve_canonical_league_state`'s own
    `ESPN_REDRAFT_SNAPSHOT_INVALID` handling. See the companion test
    below for the narrower scenario (verified identity via a stale
    Sleeper receipt) that actually reaches the new code. Either way: no
    crash, always a clean 409/503 FacadeError."""
    facade, profile_id, store = _facade_with_espn_profile(tmp_path)
    snapshot_dir = store / "espn_flaim_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / f"{profile_id}.json").write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED"
    assert excinfo.value.status == 409


def test_my_roster_espn_snapshot_invalid_when_identity_is_otherwise_verified(
    tmp_path: Path,
) -> None:
    """The real, narrower scenario that reaches the NEW
    `ESPN_REDRAFT_SNAPSHOT_INVALID` code: verified identity via a stale
    Sleeper receipt (same edge case as the SNAPSHOT_REQUIRED test above),
    combined with a real, present-but-malformed ESPN snapshot file for
    this profile. Confirms `_resolve_canonical_league_state` reports a
    parse failure distinctly (503, "the file exists but is broken") from
    a genuinely-absent snapshot (409, "none imported yet")."""
    facade, profile_id, store = _facade_with_espn_profile(tmp_path)
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "Stale Receipt"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    snapshot_dir = store / "espn_flaim_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / f"{profile_id}.json").write_text("{ not valid json", encoding="utf-8")

    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "ESPN_REDRAFT_SNAPSHOT_INVALID"
    assert excinfo.value.status == 503


def test_my_roster_no_active_profile_unregressed_error(tmp_path: Path) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_my_roster()
    assert excinfo.value.code == "SLEEPER_REDRAFT_PROFILE_REQUIRED"
    assert excinfo.value.status == 409
