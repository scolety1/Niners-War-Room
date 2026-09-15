"""NWR Prospective Outcomes V1, Worker 8, Work Unit 19 -- multi-league
SCALE CHARACTERIZATION (measurement only, real execution, no fabricated
numbers).

Benchmarks the REAL `DesktopBackendFacade` (the same backend code every
Tauri desktop call goes through) across isolated, LOCAL-provider profile
sets at 5/10/25/50 leagues:

  - "attention_center_backend_fanout": the exact per-league backend reads
    `attention-center.ts`'s `fetchLeagueAttention` performs for a
    LOCAL-provider profile (Sleeper-only reads -- my roster/free agents/
    opponent rosters -- are structurally skipped for local profiles by the
    real, unmodified TypeScript; see the module docstring there), namely
    `activate_redraft_profile` -> `redraft_data_health` ->
    `redraft_league_workspace_context`, run sequentially league-by-league
    (the real architecture: exactly one active-profile pointer on the
    backend -- see attention-center.ts's own extensive comments on this).
  - "status_fanout": `activate_redraft_profile` ->
    `redraft_player_availability_status`, the PlayerAvailabilityStatus
    authority from the live-player-intelligence cycle -- real, not wired
    into any recommendation, but a real, callable endpoint whose own
    fan-out cost across leagues is measured here for real.
  - "league_switch": `activate_redraft_profile` alone, isolated.

This script NEVER touches the owner's real Sleeper leagues or real AppData
profile store -- every profile is created under a fresh temporary
`redraft_root`, using the real repo's own bundled/seeded projection
snapshot (`repo_root=REPO_ROOT`) for realistic ranking data, exactly the
same pattern `tests/test_desktop_application_api.py` already uses for
isolated redraft-mode tests.

Real, re-runnable: `python scripts/run_multi_league_scale_benchmark_v1.py`
from the repo root. Writes
`docs/codex/prospective_outcomes_v1/multi_league_scale_v1/backend_results.json`.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.application.desktop_facade import DesktopBackendFacade  # noqa: E402
from src.services.redraft_engine_v1_service import builtin_presets, create_profile  # noqa: E402

OUT_DIR = REPO_ROOT / "docs" / "codex" / "prospective_outcomes_v1" / "multi_league_scale_v1"
SCALE_SIZES = (5, 10, 25, 50)
REPS = 5
SWITCH_SAMPLES = 30


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(len(sorted_values) - 1, max(0, round((pct / 100.0) * len(sorted_values)) - 1))
    return sorted_values[idx]


def _stats(samples_seconds: list[float]) -> dict[str, float]:
    ms = sorted(v * 1000.0 for v in samples_seconds)
    return {
        "medianMs": statistics.median(ms),
        "p95Ms": _percentile(ms, 95),
        "minMs": ms[0],
        "maxMs": ms[-1],
        "reps": len(ms),
    }


def _build_isolated_store(n: int) -> tuple[tempfile.TemporaryDirectory, DesktopBackendFacade, list[str]]:
    tmp = tempfile.TemporaryDirectory(prefix=f"nwr_scale_bench_{n}_")
    store = Path(tmp.name) / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()  # seeds the bundled projection snapshot once, real, unmodified path
    presets = builtin_presets()
    profile_ids: list[str] = []
    for i in range(n):
        template = presets[i % len(presets)]
        profile = create_profile(store, template, league_name=f"Scale League {i:03d}")
        profile_ids.append(profile.profile_id)
    return tmp, facade, profile_ids


def _bench_attention_center_fanout(facade: DesktopBackendFacade, profile_ids: list[str], reps: int) -> dict[str, Any]:
    """Mirrors attention-center.ts's fetchLeagueAttention for a LOCAL
    profile: activate -> data health -> workspace context, sequential
    across every league, exactly like the real (single-active-profile)
    backend forces the real frontend orchestration to run."""
    total_samples: list[float] = []
    per_call: dict[str, list[float]] = {"activate": [], "dataHealth": [], "workspaceContext": []}
    for _ in range(reps):
        t_pass0 = time.perf_counter()
        for pid in profile_ids:
            t0 = time.perf_counter()
            facade.activate_redraft_profile(pid)
            t1 = time.perf_counter()
            facade.redraft_data_health()
            t2 = time.perf_counter()
            facade.redraft_league_workspace_context()
            t3 = time.perf_counter()
            per_call["activate"].append(t1 - t0)
            per_call["dataHealth"].append(t2 - t1)
            per_call["workspaceContext"].append(t3 - t2)
        total_samples.append(time.perf_counter() - t_pass0)
    result = {"totalPass": _stats(total_samples)}
    for key, samples in per_call.items():
        result[f"perLeagueCall_{key}"] = _stats(samples)
    return result


def _bench_status_fanout(facade: DesktopBackendFacade, profile_ids: list[str], reps: int) -> dict[str, Any]:
    total_samples: list[float] = []
    per_call_samples: list[float] = []
    for _ in range(reps):
        t_pass0 = time.perf_counter()
        for pid in profile_ids:
            facade.activate_redraft_profile(pid)
            t0 = time.perf_counter()
            facade.redraft_player_availability_status()
            per_call_samples.append(time.perf_counter() - t0)
        total_samples.append(time.perf_counter() - t_pass0)
    return {"totalPass": _stats(total_samples), "perLeagueCall": _stats(per_call_samples)}


def _bench_league_switch(facade: DesktopBackendFacade, profile_ids: list[str], samples: int) -> dict[str, Any]:
    switch_samples: list[float] = []
    for i in range(samples):
        pid = profile_ids[i % len(profile_ids)]
        t0 = time.perf_counter()
        facade.activate_redraft_profile(pid)
        switch_samples.append(time.perf_counter() - t0)
    return _stats(switch_samples)


def run(sizes: tuple[int, ...] = SCALE_SIZES, reps: int = REPS) -> dict[str, Any]:
    """Two SEPARATE passes per size, deliberately never combined in one
    run: a plain-wall-clock timing pass (no tracemalloc active), and a
    SEPARATE memory-only pass with tracemalloc active. This is a real,
    live-confirmed finding of this pass, not a stylistic choice --
    `tracemalloc.start()` measurably inflated every real call's wall time
    by roughly 5x when first tried together (dataHealth 27ms -> 138ms,
    workspaceContext 14ms -> 71ms, confirmed by a live side-by-side
    comparison; see the ledger). Reporting tracemalloc-instrumented wall
    time as "the real latency" would have been a real, avoidable
    measurement artifact -- so timing and memory are measured in isolated
    passes instead."""
    results: dict[str, Any] = {"scaleSizes": list(sizes), "reps": reps, "byLeagueCount": []}
    for n in sizes:
        # Pass 1: timing, no tracemalloc.
        tmp, facade, profile_ids = _build_isolated_store(n)
        try:
            attention_center = _bench_attention_center_fanout(facade, profile_ids, reps)
            status_fanout = _bench_status_fanout(facade, profile_ids, reps)
            league_switch = _bench_league_switch(facade, profile_ids, SWITCH_SAMPLES)
        finally:
            tmp.cleanup()

        # Pass 2: memory only, fresh store, tracemalloc active, timing from
        # this pass is NOT reported (it is the inflated figure above).
        tmp2, facade2, profile_ids2 = _build_isolated_store(n)
        try:
            tracemalloc.start()
            tracemalloc.reset_peak()
            _bench_attention_center_fanout(facade2, profile_ids2, reps=1)
            current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
            tmp2.cleanup()

        results["byLeagueCount"].append(
            {
                "leagues": n,
                "attentionCenterFanout": attention_center,
                "statusFanout": status_fanout,
                "leagueSwitch": league_switch,
                "tracemallocPeakBytes": peak_bytes,
                "tracemallocCurrentBytesAtEnd": current_bytes,
                "tracemallocMeasuredSeparatelyFromTiming": True,
            }
        )
        print(
            f"n={n:>3}  attention_center_total_median="
            f"{attention_center['totalPass']['medianMs']:.1f}ms"
            f"  status_fanout_total_median={status_fanout['totalPass']['medianMs']:.1f}ms"
            f"  switch_median={league_switch['medianMs']:.3f}ms"
            f"  tracemalloc_peak={peak_bytes / 1024:.0f}KiB (separate pass)"
        )
    return results


def _linearity_check(results: dict[str, Any]) -> dict[str, Any]:
    """A simple, honest superlinearity check: per-league cost (total /
    n) at the smallest and largest tested size. If the largest size's
    per-league cost is not meaningfully higher than the smallest's, scaling
    is linear (or better) across the tested range -- reported as a plain
    ratio, not a fitted curve (no need to overclaim precision here)."""
    rows = results["byLeagueCount"]
    if len(rows) < 2:
        return {}
    first, last = rows[0], rows[-1]
    first_per_league = first["attentionCenterFanout"]["totalPass"]["medianMs"] / first["leagues"]
    last_per_league = last["attentionCenterFanout"]["totalPass"]["medianMs"] / last["leagues"]
    return {
        "perLeagueMsAtSmallestN": {"n": first["leagues"], "msPerLeague": first_per_league},
        "perLeagueMsAtLargestN": {"n": last["leagues"], "msPerLeague": last_per_league},
        "ratio": (last_per_league / first_per_league) if first_per_league else None,
        "verdictHint": (
            "LINEAR_OR_BETTER"
            if first_per_league and (last_per_league / first_per_league) < 1.5
            else "SUPERLINEAR_SIGNAL_INVESTIGATE"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=list(SCALE_SIZES))
    parser.add_argument("--reps", type=int, default=REPS)
    args = parser.parse_args()

    results = run(tuple(args.sizes), args.reps)
    results["linearityCheck"] = _linearity_check(results)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "backend_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(json.dumps(results["linearityCheck"], indent=2))


if __name__ == "__main__":
    main()
