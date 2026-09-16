"""Shared, minimal pytest configuration for the whole `tests/` suite.

Currently holds exactly one thing: an autouse fixture that resets the
process-wide Sleeper player-catalog cache singleton
(`src.services.sleeper_player_catalog_cache`, shared upgrade A, NWR
full-cycle V1) before every test. That cache is intentionally
process-lifetime/cross-request in real production use (that is the whole
point of the fix it belongs to), but a real *test* suite that monkeypatches
`SleeperHttpClient.get_json` with a DIFFERENT fake player-catalog fixture
per test would otherwise leak one test's cached catalog into the next
test's assertions -- a real cross-test pollution bug this fixture exists to
prevent. Deliberately narrow: it does not touch any other cache, fixture,
or piece of shared state.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_sleeper_player_catalog_cache():
    from src.services.sleeper_player_catalog_cache import _default_cache

    _default_cache.invalidate()
    yield
    _default_cache.invalidate()
