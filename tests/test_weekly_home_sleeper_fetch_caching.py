"""NWR Post-Closure Fix V1 (Worker E, latency profiling): regression +
exact-equivalence coverage for the per-request Sleeper GET cache added to
`DesktopBackendFacade`.

Real cProfile evidence (recorded in
docs/codex/post_ui_v1/NWR_POST_CLOSURE_LEDGER_V1.md) showed
`redraft_weekly_home_actions` issuing 11 separate live `SleeperHttpClient.
get_json` network round trips within ONE request -- `redraft_weekly_lineup`,
`redraft_waivers`, `redraft_trade_finder`, `redraft_kdst_streamer`, and
`redraft_free_agents` each independently re-fetch the SAME
`league/{id}/rosters` and `players/nfl` payloads (and `redraft_trade_finder`
also fetches `league/{id}/users`). That accounted for ~11s of a real ~13s
run -- almost entirely redundant identical GETs, not algorithmic work.

The fix is a thread-local, OPT-IN cache (`_sleeper_fetch_cache_local`,
`_sleeper_get_json`) that `redraft_weekly_home_actions` turns on only for
the duration of its own five sub-calls, then always turns back off. This
file proves, with real assertions rather than just code reading:

  1. The cache is a pure pass-through (identical to calling
     `client.get_json` directly) when it is not active -- i.e. every OTHER
     caller of these five methods is completely unaffected.
  2. When active, a distinct URL is fetched from the network only ONCE no
     matter how many sub-calls ask for it, and every asker gets back the
     SAME object.
  3. `redraft_weekly_home_actions` end-to-end actually wires this in: the
     real fake-Sleeper-backed run below fetches `league/9999/rosters` and
     `players/nfl` exactly once each (not five times), while a directly
     comparable standalone call to one of the five sub-methods (outside of
     `redraft_weekly_home_actions`) still fetches fresh every time -- so
     the optimization's blast radius is provably confined to the one
     method it targets.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import load_profile, save_profile
from src.services.sleeper_import_service import SleeperHttpClient

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_sleeper_get_json_is_a_pure_pass_through_when_the_cache_is_inactive(
    tmp_path: Path,
) -> None:
    """Outside of `redraft_weekly_home_actions`, `_sleeper_fetch_cache_local.
    cache` is `None` -- `_sleeper_get_json` must behave EXACTLY like calling
    `client.get_json` directly: one real call per invocation, no
    memoization, byte-identical to the pre-change code path."""

    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )
    assert getattr(facade._sleeper_fetch_cache_local, "cache", None) is None

    calls: list[str] = []

    class _CountingClient:
        def get_json(self, path: str) -> Any:
            calls.append(path)
            return {"path": path, "call_number": len(calls)}

    client = _CountingClient()
    first = facade._sleeper_get_json(client, "players/nfl")
    second = facade._sleeper_get_json(client, "players/nfl")

    assert calls == ["players/nfl", "players/nfl"]  # fetched twice, never cached
    assert first == {"path": "players/nfl", "call_number": 1}
    assert second == {"path": "players/nfl", "call_number": 2}


def test_sleeper_get_json_dedupes_within_an_active_cache_scope(tmp_path: Path) -> None:
    """When a caller opts the cache in (exactly what `redraft_weekly_home_
    actions` does around its own five sub-calls), repeated requests for the
    SAME path are served from the first real fetch -- a different path is
    still fetched fresh."""

    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )

    calls: list[str] = []

    class _CountingClient:
        def get_json(self, path: str) -> Any:
            calls.append(path)
            return {"path": path, "call_number": len(calls)}

    client = _CountingClient()
    facade._sleeper_fetch_cache_local.cache = {}
    try:
        a1 = facade._sleeper_get_json(client, "league/9999/rosters")
        a2 = facade._sleeper_get_json(client, "league/9999/rosters")
        b1 = facade._sleeper_get_json(client, "players/nfl")
    finally:
        facade._sleeper_fetch_cache_local.cache = None

    assert calls == ["league/9999/rosters", "players/nfl"]  # rosters fetched once, not twice
    assert a1 is a2  # the exact same cached object, not merely equal
    assert a1 != b1

    # The scope really is torn down afterward -- a call right after the
    # `finally` above must hit the network again, exactly like before this
    # change.
    a3 = facade._sleeper_get_json(client, "league/9999/rosters")
    assert calls == ["league/9999/rosters", "players/nfl", "league/9999/rosters"]
    assert a3 is not a1


def test_cache_scope_is_thread_local_not_shared_across_concurrent_requests(
    tmp_path: Path,
) -> None:
    """`DesktopApiServer` is a real `ThreadingHTTPServer`
    (src/desktop_api/server.py) -- the SAME `DesktopBackendFacade` instance
    is shared across concurrently-handled requests. A bare instance
    attribute cache would let one in-flight request's cache leak into (or
    get wiped by) another's `finally` reset. This proves the real
    `threading.local()` scoping holds under actual concurrent threads: two
    threads each turn the cache on, do some work, and tear it back down --
    neither thread ever observes the other's cache object."""

    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )
    observed: dict[str, list[int]] = {"a": [], "b": []}
    barrier = threading.Barrier(2)

    def worker(name: str) -> None:
        facade._sleeper_fetch_cache_local.cache = {}
        barrier.wait()  # force real interleaving between the two threads
        for _ in range(20):
            cache = facade._sleeper_fetch_cache_local.cache
            observed[name].append(id(cache) if cache is not None else -1)
            time.sleep(0)  # yield, encouraging the GIL to switch threads
        facade._sleeper_fetch_cache_local.cache = None

    t1 = threading.Thread(target=worker, args=("a",))
    t2 = threading.Thread(target=worker, args=("b",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Each thread saw ONLY its own cache object throughout -- never `None`
    # (never wiped by the other thread's `finally`) and never the other
    # thread's `id()` (never leaked/shared).
    assert -1 not in observed["a"]
    assert -1 not in observed["b"]
    assert len(set(observed["a"])) == 1
    assert len(set(observed["b"])) == 1
    assert set(observed["a"]) != set(observed["b"])

    # And the scope is clean afterward for the next real request.
    assert getattr(facade._sleeper_fetch_cache_local, "cache", None) is None


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()  # installs the real governed seed into this fresh store
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Weekly Home Fetch-Caching League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id="9999"))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps({"league": {"league_id": "9999"}, "owner": {"user_id": "owner-1"}}),
        encoding="utf-8",
    )
    return facade, profile_id


_ROSTERS = [
    {"owner_id": "owner-1", "players": ["me-1", "me-2"], "starters": ["me-1"]},
    {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
]
_USERS = [
    {"user_id": "owner-1", "display_name": "Me"},
    {"user_id": "owner-2", "display_name": "Rival"},
]
_PLAYERS = {
    "me-1": {"full_name": "Roster Player One", "position": "RB", "team": "SF"},
    "me-2": {"full_name": "Roster Player Two", "position": "WR", "team": "KC"},
    "rival-1": {"full_name": "Rival Player One", "position": "WR", "team": "BUF"},
    # A REAL identity from the repo's bundled governed ranking (Freeze V7,
    # `12_TEAM_1QB_HALF_PPR` preset) -- not on either roster fixture above,
    # so `sleeper_free_agent_pool` reports it a free agent that actually
    # MATCHES a real canonical ranking row (a genuine non-None marginal
    # utility). An unmatched-identity free agent is deliberately avoided
    # here: it is orthogonal to this file's caching claim and trips a
    # separate, pre-existing, out-of-scope formatting edge case in
    # `redraft_waivers` (`f"...{top_add.marginal_utility:.1f}"` when the
    # single best add candidate is genuinely UNMATCHED) that this pass does
    # not touch.
    "fa-1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
}


def _fake_get_json_counting(call_log: list[str]):
    def _fake_get_json(self: Any, path: str) -> Any:
        call_log.append(path)
        if path == "league/9999/rosters":
            return _ROSTERS
        if path == "league/9999/users":
            return _USERS
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            # NWR Waiver Night V1 (Worker 3, Work Unit 6): `redraft_waivers`
            # now also reads real league settings (waiver_type/waiver_budget)
            # for the new `faabContext` field -- through the SAME cached
            # `_sleeper_get_json` wrapper as rosters/players, so it is
            # expected to be dedup'd inside a composed weekly-home call just
            # like they are.
            return {"settings": {"waiver_type": 1, "waiver_budget": 100}}
        # Weekly projections (a DIFFERENT endpoint, already covered by its
        # own disk TTL cache in weekly_projection_provider_service.py, and
        # deliberately untouched by this pass) -- let it fail honestly so
        # START_SIT degrades to "unavailable" rather than asserting on a
        # path this test does not need to model in full.
        if path.startswith("projections/nfl/"):
            raise AssertionError("no real weekly-projection fixture in this test")
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    return _fake_get_json


def test_weekly_home_actions_fetches_rosters_and_players_exactly_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    call_log: list[str] = []
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json_counting(call_log)
    )

    result = facade.redraft_weekly_home_actions(week=1).data

    rosters_calls = [path for path in call_log if path == "league/9999/rosters"]
    players_calls = [path for path in call_log if path == "players/nfl"]
    users_calls = [path for path in call_log if path == "league/9999/users"]

    # Real, profiled bottleneck: five sub-calls used to each independently
    # re-fetch rosters/players (2 of the 5 also fetch `users`... actually
    # only trade_finder does). Before this fix, `rosters_calls`/
    # `players_calls` would read 5 each (one per sub-call) instead of 1.
    assert rosters_calls == ["league/9999/rosters"]
    assert players_calls == ["players/nfl"]
    # Only `redraft_trade_finder` ever asks for `users` -- exactly once,
    # same as before this change (nothing to dedupe against).
    assert users_calls == ["league/9999/users"]

    # The cache scope is torn down after the call returns -- proven by
    # observing a standalone sub-call fetch fresh again right after.
    call_log.clear()
    facade.redraft_free_agents()
    assert call_log.count("league/9999/rosters") == 1
    assert call_log.count("players/nfl") == 1

    # The real response is still well-formed and reflects the real fixture
    # roster/free-agent data -- caching changed nothing about the content,
    # only how many times it was fetched.
    assert result["writeBehavior"] == "NO_SLEEPER_WRITES"
    assert result["freeAgents"]["freeAgents"]
    free_agent_names = {row["playerName"] for row in result["freeAgents"]["freeAgents"]}
    assert "Christian McCaffrey" in free_agent_names


def test_standalone_sub_calls_outside_weekly_home_still_fetch_fresh_every_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every one of the five sub-methods, called on its own (the normal,
    everyday way a real owner opens Waivers or Trade Finder directly, NOT
    via Weekly Home), must be completely unaffected by this change -- a
    fresh, real fetch every single call, exactly as before."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    call_log: list[str] = []
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json_counting(call_log)
    )

    facade.redraft_free_agents()
    facade.redraft_free_agents()
    facade.redraft_trade_finder()

    assert call_log.count("league/9999/rosters") == 3  # once per call, never deduped
    assert call_log.count("players/nfl") == 3
    assert call_log.count("league/9999/users") == 1
