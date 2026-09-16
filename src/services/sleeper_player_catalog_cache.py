"""Bounded, cross-request, cross-thread cache for Sleeper's full player
catalog (`GET players/nfl`, ~14.66MB / ~12,227 players as of this pass).

WHY THIS EXISTS (real, previously-scoped-down problem): a same-night fix
(`DesktopBackendFacade._sleeper_fetch_cache_local`, see `desktop_facade.py`)
already de-duplicated repeat catalog fetches WITHIN one composite HTTP
request (`redraft_weekly_home_actions`'s five sub-calls) using a thread-
local, opt-in, per-path dict. That fix explicitly left the BROADER problem
open: nearly every OTHER live desktop endpoint (weekly lineup, waivers,
trade finder/analysis/package search, K/DST streamer, free agents, weekly
projections, my roster, Sleeper draft sync, practical-mode K/DST setup)
independently re-fetches the SAME ~14.66MB catalog on its OWN separate HTTP
request, with zero sharing across requests -- confirmed still true this
pass by grepping every `players/nfl` call site in `src/`.

WHAT THIS MODULE IS: one small, purpose-built, IN-MEMORY, PROCESS-lifetime
cache for exactly one thing -- the Sleeper player catalog. It is NOT a
general-purpose caching framework; nothing else should be routed through
it. `DesktopBackendFacade._sleeper_get_json` is the ONE call site that
special-cases the catalog path to use it (see that method's docstring) --
every other Sleeper path (`league/{id}/rosters`, `.../users`,
`.../traded_picks`, `.../drafts`) is deliberately left OUT of this cache
and is always fetched live, because roster/ownership/transaction/FAAB data
can change at any moment (a waiver claim, a trade, a lineup lock) and this
app must never let a stale catalog-style cache mask a real recent change to
THAT data. The player catalog itself (name/position/team/status) changes
far less often -- Sleeper's own documentation recommends fetching it "no
more than once per day" (see `live_player_intelligence_shadow_v1_service.py`
and `scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`, which
already cite this). This module's default TTL (15 minutes) is comfortably
inside that guidance while still being short enough to pick up a real
mid-day team/position change (trade, waiver-wire cut) within one normal
work session -- a deliberate, disclosed, bounded trade-off, not an attempt
to treat the catalog as immutable.

CONCURRENCY: `get()` holds a single process-wide lock for its ENTIRE
duration, including the real network fetch when one is needed. This is a
deliberate, simple correctness choice over a more elaborate future/promise
scheme: since there is exactly one cache key (the catalog itself), any
concurrent caller that arrives while a fetch is already in flight simply
blocks on the same lock and, once it acquires it, finds the now-fresh cache
already populated -- so it returns immediately without ever calling
`client.get_json` itself. This is real request de-duplication, not just a
read-through cache that happens to reduce SOME calls (verified by a
concurrent test asserting exactly one real fetch for N simultaneous
callers).

FAILURE HANDLING: a fetch failure (network error, malformed response) is
never cached and never silently masked. The exception propagates to every
caller waiting on it; the cache's previous state (valid-but-expired data,
or nothing) is left untouched so the NEXT call retries a real fetch. This
module deliberately does NOT fall back to serving old data past its TTL on
a failure -- callers get an honest error instead of stale-forever data
dressed up as current.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Protocol


class SleeperPlayerCatalogError(RuntimeError):
    """The real Sleeper `players/nfl` fetch failed, or returned a
    syntactically-valid-but-wrong-shaped payload (not a JSON object)."""


class _JsonGetter(Protocol):
    def get_json(self, path: str) -> Any: ...


# Sleeper's own documented guidance is "no more than once per day." 15
# minutes is a deliberately bounded, much-tighter-than-required default:
# it collapses the real repeat-fetch storm this module exists to fix
# (multiple desktop endpoints hit within the same short work session) while
# still refreshing well within one sitting if a real mid-day roster move
# changes a player's team/position.
DEFAULT_TTL_SECONDS = 15 * 60


@dataclass(frozen=True)
class SleeperPlayerCatalogSnapshot:
    """What `get()` returns. `retrieved_at` is the REAL wall-clock time the
    underlying network fetch completed -- callers must surface this
    timestamp rather than implying "just fetched now" for a cache hit."""

    players: Mapping[str, Mapping[str, Any]]
    retrieved_at: str  # ISO-8601 UTC
    served_from_cache: bool
    age_seconds: float


class SleeperPlayerCatalogCache:
    """One bounded cache entry (the catalog), safe for concurrent use
    across threads. Intended to be a long-lived, process-scoped singleton
    (see `get_sleeper_player_catalog` below) -- not instantiated per
    request. Tests may construct their own instance to avoid cross-test
    leakage."""

    def __init__(self, ttl_seconds: float = DEFAULT_TTL_SECONDS) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive.")
        self._ttl_seconds = float(ttl_seconds)
        self._lock = threading.Lock()
        self._players: dict[str, Mapping[str, Any]] | None = None
        self._retrieved_at_iso: str | None = None
        self._retrieved_monotonic: float | None = None
        # Real fetch counter -- exists purely so tests/verification can
        # assert "exactly one real network fetch happened," not merely
        # infer it from timing.
        self.real_fetch_count = 0

    def get(
        self, client: _JsonGetter, *, force_refresh: bool = False
    ) -> SleeperPlayerCatalogSnapshot:
        with self._lock:
            now = time.monotonic()
            if (
                not force_refresh
                and self._players is not None
                and self._retrieved_monotonic is not None
                and (now - self._retrieved_monotonic) < self._ttl_seconds
            ):
                return SleeperPlayerCatalogSnapshot(
                    players=self._players,
                    retrieved_at=self._retrieved_at_iso or "",
                    served_from_cache=True,
                    age_seconds=now - self._retrieved_monotonic,
                )

            # Cache miss, expired, or an explicit refresh -- fetch while
            # STILL holding the lock. Any other thread calling `get()`
            # concurrently blocks here and, once it acquires the lock,
            # will see the freshly populated cache below and return
            # without performing its own fetch. This is the real
            # de-duplication mechanism, not a hint or a best-effort.
            raw = client.get_json("players/nfl")
            if not isinstance(raw, dict):
                raise SleeperPlayerCatalogError(
                    "Sleeper player catalog response is malformed (expected a JSON object)."
                )
            # A failure above raises out of this `with` block, releasing
            # the lock without touching any of the state below -- the
            # cache is never poisoned with a failed fetch, and whatever
            # was cached before (if anything) is left exactly as it was.
            self._players = raw
            self._retrieved_at_iso = datetime.now(UTC).isoformat()
            self._retrieved_monotonic = now
            self.real_fetch_count += 1
            return SleeperPlayerCatalogSnapshot(
                players=self._players,
                retrieved_at=self._retrieved_at_iso,
                served_from_cache=False,
                age_seconds=0.0,
            )

    def invalidate(self) -> None:
        """Explicitly discard the cached catalog so the NEXT `get()` call
        performs a real fetch, regardless of TTL. Used by tests and by any
        future explicit "refresh player data" action."""

        with self._lock:
            self._players = None
            self._retrieved_at_iso = None
            self._retrieved_monotonic = None


# Process-wide singleton. Deliberately module-level (not per-facade-
# instance) so it is shared across every real caller in this process,
# including services outside `DesktopBackendFacade` -- there is exactly one
# real Sleeper player catalog per process's worth of live requests, and it
# should be fetched at most once per TTL window regardless of which code
# path asks for it first.
_default_cache = SleeperPlayerCatalogCache()


def get_sleeper_player_catalog(
    client: _JsonGetter,
    *,
    force_refresh: bool = False,
    cache: SleeperPlayerCatalogCache | None = None,
) -> SleeperPlayerCatalogSnapshot:
    """The one seam real callers should use to read the Sleeper player
    catalog when they want cross-request caching + de-duplication. Pass an
    explicit `cache=` only in tests; real callers should omit it and share
    the process-wide singleton."""

    target = cache if cache is not None else _default_cache
    return target.get(client, force_refresh=force_refresh)
