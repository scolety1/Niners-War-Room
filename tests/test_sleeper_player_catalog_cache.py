"""Real coverage for `sleeper_player_catalog_cache.py` (shared upgrade A,
NWR full-cycle V1 -- Worker 2).

Confirms, with real assertions (not code-inspection-only claims):

  1. Cold vs. warm: a cache miss performs a real fetch; a warm hit within
     the TTL performs zero real fetches and returns the SAME data.
  2. Concurrent de-duplication: N simultaneous callers needing the catalog
     at the same moment trigger exactly ONE real network fetch, not N --
     using real `threading.Thread`s and a real `threading.Barrier` to force
     genuine interleaving, plus an artificial delay inside the fake
     `get_json` to widen the race window so this isn't a timing fluke.
  3. Expiry: a TTL that has elapsed forces a real re-fetch.
  4. Provider (network) failure: a failed fetch is never cached -- the
     next call retries for real, and a failure never silently serves stale
     data as if it were fresh.
  5. Data separation: `DesktopBackendFacade._sleeper_get_json` only ever
     routes the exact `players/nfl` path through this cross-request cache;
     every other Sleeper path (rosters/users/traded_picks/drafts --
     genuinely live-changing roster/ownership/transaction/FAAB data) stays
     completely outside of it. `test_weekly_home_sleeper_fetch_caching.py`
     already independently proves rosters/users are still fetched fresh
     per-request; this file adds a direct, narrow regression test that
     nothing except the literal `players/nfl` path is ever handed to the
     catalog cache.
"""

from __future__ import annotations

import threading
import time
from typing import Any

import pytest

from src.services.sleeper_player_catalog_cache import (
    DEFAULT_TTL_SECONDS,
    SleeperPlayerCatalogCache,
    SleeperPlayerCatalogError,
    get_sleeper_player_catalog,
)

_CATALOG = {
    "1": {"full_name": "Test Player One", "position": "RB", "team": "SF"},
    "2": {"full_name": "Test Player Two", "position": "WR", "team": "KC"},
}


class _CountingClient:
    """A fake Sleeper client that counts real `get_json` calls and can
    simulate network latency and failure."""

    def __init__(
        self, *, delay_seconds: float = 0.0, fail_times: int = 0, payload: Any = None
    ) -> None:
        self.calls = 0
        self._delay_seconds = delay_seconds
        self._fail_times = fail_times
        self._payload = payload if payload is not None else _CATALOG
        self._lock = threading.Lock()

    def get_json(self, path: str) -> Any:
        with self._lock:
            self.calls += 1
            call_number = self.calls
        if self._delay_seconds:
            time.sleep(self._delay_seconds)
        if call_number <= self._fail_times:
            raise OSError(f"simulated network failure #{call_number}")
        return self._payload


def test_cold_then_warm_hit_real_measured_counts() -> None:
    """Cold: a real fetch happens. Warm: a second call within the TTL
    performs ZERO further real fetches and returns the exact same object,
    with `served_from_cache=True`."""

    cache = SleeperPlayerCatalogCache(ttl_seconds=60)
    client = _CountingClient()

    cold = cache.get(client)
    assert client.calls == 1
    assert cold.served_from_cache is False
    assert cold.players == _CATALOG

    warm = cache.get(client)
    assert client.calls == 1  # no second real fetch
    assert warm.served_from_cache is True
    assert warm.players is cold.players  # exact same cached object
    assert warm.age_seconds >= 0.0


def test_concurrent_callers_trigger_exactly_one_real_fetch() -> None:
    """The real de-duplication claim: fire 8 real threads at an empty
    cache simultaneously. Only ONE of them may actually reach the network;
    the rest must block on the shared lock and then observe the
    now-populated cache instead of fetching themselves. A real
    `time.sleep` inside the fake client widens the race window so this
    would fail if de-duplication were fake (e.g. a plain unlocked
    read-check-fetch)."""

    cache = SleeperPlayerCatalogCache(ttl_seconds=60)
    client = _CountingClient(delay_seconds=0.2)

    threads_count = 8
    barrier = threading.Barrier(threads_count)
    results: list[Any] = [None] * threads_count

    def worker(index: int) -> None:
        barrier.wait()  # force all 8 threads to call cache.get(...) at ~the same instant
        results[index] = cache.get(client)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(threads_count)]
    started_at = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.monotonic() - started_at

    # REAL measured proof: exactly one network call happened, not 8.
    assert client.calls == 1, f"expected exactly 1 real fetch for {threads_count} concurrent callers, got {client.calls}"
    # Every caller got the same real data back.
    for result in results:
        assert result is not None
        assert result.players == _CATALOG
    # If de-duplication were broken (each thread fetching independently,
    # serialized only by the GIL), 8 sequential 0.2s fetches would take
    # >= 1.6s. One real fetch plus 7 lock-waits takes roughly one fetch's
    # worth of time.
    assert elapsed < 1.0, f"expected ~1 fetch's worth of wall time, took {elapsed:.3f}s"


def test_expiry_forces_a_real_refetch() -> None:
    """A TTL that has elapsed must cause the NEXT call to perform a real
    fetch again, not silently keep serving the old value forever."""

    cache = SleeperPlayerCatalogCache(ttl_seconds=0.05)
    client = _CountingClient()

    first = cache.get(client)
    assert client.calls == 1
    assert first.served_from_cache is False

    time.sleep(0.08)  # real elapsed time past the 0.05s TTL

    second = cache.get(client)
    assert client.calls == 2  # a real second fetch happened
    assert second.served_from_cache is False


def test_force_refresh_bypasses_a_still_valid_cache() -> None:
    """An explicit refresh (`force_refresh=True`) must perform a real fetch
    even when the existing entry is still well within its TTL."""

    cache = SleeperPlayerCatalogCache(ttl_seconds=3600)
    client = _CountingClient()

    cache.get(client)
    assert client.calls == 1

    refreshed = cache.get(client, force_refresh=True)
    assert client.calls == 2
    assert refreshed.served_from_cache is False


def test_invalidate_forces_a_real_refetch() -> None:
    cache = SleeperPlayerCatalogCache(ttl_seconds=3600)
    client = _CountingClient()

    cache.get(client)
    assert client.calls == 1
    cache.invalidate()
    cache.get(client)
    assert client.calls == 2


def test_provider_failure_is_never_cached_and_raises_honestly() -> None:
    """A failed fetch must (a) propagate a real, honest error to the
    caller, (b) NOT poison the cache with the failure, and (c) let the
    VERY NEXT call retry for real (proving the cache didn't silently latch
    onto a bad state)."""

    cache = SleeperPlayerCatalogCache(ttl_seconds=3600)
    client = _CountingClient(fail_times=1)  # first call fails, second succeeds

    with pytest.raises(OSError):
        cache.get(client)
    assert client.calls == 1

    # The cache must be empty/untouched after the failure -- the next call
    # performs a real fetch (not a cache hit on garbage, not a re-raise of
    # a cached exception).
    recovered = cache.get(client)
    assert client.calls == 2
    assert recovered.served_from_cache is False
    assert recovered.players == _CATALOG


def test_provider_failure_after_a_prior_success_does_not_serve_stale_forever() -> None:
    """Once a real value is cached, if the NEXT real fetch (after
    expiry/force-refresh) fails, the caller must get an honest error --
    never a silently-served, arbitrarily-old cached value pretending to be
    current."""

    cache = SleeperPlayerCatalogCache(ttl_seconds=3600)
    good_client = _CountingClient()
    cache.get(good_client)
    assert good_client.calls == 1

    failing_client = _CountingClient(fail_times=99)
    with pytest.raises(OSError):
        cache.get(failing_client, force_refresh=True)
    # The failure must propagate -- this cache module does not fall back to
    # silently re-serving the old cached value on a forced-refresh failure.


def test_malformed_response_raises_a_typed_error_and_is_not_cached() -> None:
    cache = SleeperPlayerCatalogCache(ttl_seconds=3600)
    bad_client = _CountingClient(payload=["not", "a", "dict"])

    with pytest.raises(SleeperPlayerCatalogError):
        cache.get(bad_client)
    assert bad_client.calls == 1

    good_client = _CountingClient()
    recovered = cache.get(good_client)
    assert recovered.served_from_cache is False
    assert good_client.calls == 1


def test_default_ttl_is_bounded_and_within_sleepers_own_guidance() -> None:
    """A real, disclosed, bounded TTL -- not an unbounded "cache forever"
    default, and comfortably inside Sleeper's own documented "no more than
    once per day" guidance for this endpoint."""

    assert 0 < DEFAULT_TTL_SECONDS <= 24 * 60 * 60


def test_roster_ownership_transaction_faab_paths_never_enter_the_catalog_cache(
    tmp_path,
) -> None:
    """Regression test for the "critical scoping requirement": only the
    EXACT `players/nfl` path may ever be routed to the cross-request
    catalog cache by `DesktopBackendFacade._sleeper_get_json`. Every real
    roster/ownership/transaction/FAAB-adjacent path -- rosters, users,
    traded_picks, drafts, and the live NFL week/state endpoint -- must stay
    completely outside of it: fetched fresh on every call, never
    memoized, never touching the catalog cache's fetch counter."""

    import src.services.sleeper_player_catalog_cache as catalog_cache_module
    from pathlib import Path

    from src.application.desktop_facade import DesktopBackendFacade

    repo_root = Path(__file__).resolve().parents[1]
    facade = DesktopBackendFacade(
        repo_root=repo_root, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )
    catalog_cache_module._default_cache.invalidate()
    fetch_count_before = catalog_cache_module._default_cache.real_fetch_count

    live_changing_paths = [
        "league/9999/rosters",
        "league/9999/users",
        "league/9999/traded_picks",
        "league/9999/drafts",
        "state/nfl",
        "league/9999",  # settings (waiver_type/waiver_budget) -- FAAB-adjacent
    ]

    for path in live_changing_paths:
        client = _CountingClient(payload={"path": path})
        first = facade._sleeper_get_json(client, path)
        second = facade._sleeper_get_json(client, path)
        # Fetched twice -- never memoized cross-call for these paths.
        assert client.calls == 2, f"{path} was unexpectedly cached (only {client.calls} real fetch(es))"
        assert first == {"path": path}
        assert second == {"path": path}

    # None of the above touched the catalog cache's own fetch counter.
    assert catalog_cache_module._default_cache.real_fetch_count == fetch_count_before

    # Confirm the catalog cache is genuinely reachable through the same
    # method for its one real path, to prove this isn't merely disabled.
    catalog_client = _CountingClient()
    facade._sleeper_get_json(catalog_client, "players/nfl")
    assert catalog_cache_module._default_cache.real_fetch_count == fetch_count_before + 1
    catalog_cache_module._default_cache.invalidate()


def test_module_level_helper_uses_the_shared_singleton_by_default() -> None:
    """`get_sleeper_player_catalog` without an explicit `cache=` argument
    shares ONE process-wide cache -- proving real cross-request sharing,
    not an accidental new cache per call."""

    import src.services.sleeper_player_catalog_cache as module

    module._default_cache.invalidate()
    client = _CountingClient()

    first = get_sleeper_player_catalog(client)
    second = get_sleeper_player_catalog(client)

    assert client.calls == 1  # the second call reused the shared singleton
    assert first.players is second.players
    module._default_cache.invalidate()  # leave the singleton clean for other tests
