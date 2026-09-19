"""NWR connection/update pass, Worker 2 (2026-09-19) -- regression coverage
for the owner-reported "missing projection treated as a fabricated zero"
bug and its upstream confidence-gate fix.

The core computational bug lived in `weekly_lineup_optimizer_service.
_swap_reasons` (see `tests/test_weekly_lineup_optimizer_service.py` for the
exact missing-vs-known-zero fixtures, including a reproduction of the real
Zay Flowers case). This file covers the one upstream piece that lives in
`desktop_facade.py`: `_start_sit_confidence`, a small pure function pulled
out of `redraft_weekly_lineup` specifically so this real gap could be
independently tested without needing the full live-Sleeper mock chain (this
worktree's expired projection-seed governance receipt makes a true
end-to-end `redraft_weekly_lineup` round trip infeasible here -- see
`tests/test_desktop_facade_architecture_wiring.py`'s own module docstring
for the same, already-documented constraint).

Before this pass: a swap whose DISPLACED player had a missing weekly
projection was invisible to both existing confidence counters
(`unprojected_starter_count`/`unresolved_identity_starter_count` only see
STARTERS, and the displaced player is, by definition, no longer a starter
after optimization) -- so Start/Sit could report NOMINAL confidence while
its own TOP recommendation rested on a fabricated point swing.
"""

from __future__ import annotations

from src.application.desktop_facade import _start_sit_confidence


def _confidence(**overrides):
    base = dict(
        weekly_health_freshness="LIVE",
        unprojected_starter_count=0,
        unresolved_identity_starter_count=0,
        primary_swap_delta_basis=None,
        primary_swap_bench_player=None,
    )
    base.update(overrides)
    return _start_sit_confidence(**base)


def test_nominal_when_every_signal_is_clean() -> None:
    state, basis = _confidence()
    assert state == "NOMINAL"
    assert "live weekly projection" in basis


def test_nominal_when_the_top_swap_has_a_real_known_delta() -> None:
    # A real, KNOWN delta (e.g. built against a real 0.0 kicker projection)
    # must NOT trip the new unknown-delta branch -- only a genuinely
    # missing projection should ever downgrade confidence for this reason.
    state, basis = _confidence(primary_swap_delta_basis="KNOWN", primary_swap_bench_player="Bad Weather Kicker")
    assert state == "NOMINAL"


def test_low_when_the_top_swap_has_an_unknown_missing_projection_delta() -> None:
    # The real fix under test: the owner-reported Zay Flowers case. Neither
    # `unprojected_starter_count` nor `unresolved_identity_starter_count` is
    # nonzero here (both 0, the pre-fix false-NOMINAL condition) -- only the
    # new `primary_swap_delta_basis` check catches it.
    state, basis = _confidence(
        primary_swap_delta_basis="UNKNOWN_MISSING_BENCH_PROJECTION",
        primary_swap_bench_player="Zay Flowers",
    )
    assert state == "LOW"
    assert "unknown point swing" in basis
    assert "Zay Flowers" in basis


def test_stale_projections_take_priority_over_the_unknown_delta_branch() -> None:
    state, basis = _confidence(
        weekly_health_freshness="STALE",
        primary_swap_delta_basis="UNKNOWN_MISSING_BENCH_PROJECTION",
        primary_swap_bench_player="Zay Flowers",
    )
    assert state == "LOW"
    assert "STALE" in basis


def test_unprojected_starter_count_takes_priority_over_the_unknown_delta_branch() -> None:
    state, basis = _confidence(
        unprojected_starter_count=1,
        primary_swap_delta_basis="UNKNOWN_MISSING_BENCH_PROJECTION",
        primary_swap_bench_player="Zay Flowers",
    )
    assert state == "LOW"
    assert "no usable weekly projection" in basis


def test_unresolved_identity_count_takes_priority_over_the_unknown_delta_branch() -> None:
    state, basis = _confidence(
        unresolved_identity_starter_count=1,
        primary_swap_delta_basis="UNKNOWN_MISSING_BENCH_PROJECTION",
        primary_swap_bench_player="Zay Flowers",
    )
    assert state == "LOW"
    assert "unresolved player" in basis


def test_no_swaps_at_all_never_trips_the_unknown_delta_branch() -> None:
    # `primary_swap_delta_basis=None` is the real "no swaps this week"
    # shape the caller passes -- must resolve NOMINAL, never be confused
    # with an unknown delta.
    state, basis = _confidence(primary_swap_delta_basis=None, primary_swap_bench_player=None)
    assert state == "NOMINAL"
