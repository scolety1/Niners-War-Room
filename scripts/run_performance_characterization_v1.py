"""NWR Prospective Outcomes V1, Worker 8, Work Unit 20 -- PERFORMANCE
CHARACTERIZATION (measurement only, real execution, no fabricated numbers).

Real, measured median/P95 timings for: cold startup, league open, Home,
Lineup, Improve Team, Trade Finder, Trade Package Search, Player Drawer
first/warm lookup, Draft refresh, History (V3), and outcome ingestion.

SAFETY (read this before editing):
  - The real, owner AppData Redraft store
    (`~/AppData/Local/com.ninerswarroom.redraft/state/redraft`) is READ
    (copied) but never written. `DesktopBackendFacade.activate_redraft_profile`
    performs a real local write (`active_profile.json`) -- this script
    therefore ALWAYS constructs the facade against a `shutil.copytree`
    COPY of the real store under a temp directory, never the real path
    itself, so the owner's real active-profile pointer is never touched.
  - The real "Fantasy Gamers" Sleeper league (id `1312983576827920384`) is
    read via the copy's own already-saved `provider=sleeper` profile
    (`4c5f04762921420595e4d8c7cda76582`) -- every resulting network call is
    a plain, public, keyless Sleeper GET (rosters/users/players/matchups),
    the same real, read-only surface every other script in this cycle
    uses. No write-capable Sleeper endpoint exists anywhere in this
    codebase (confirmed by every prior worker; unchanged this pass).
  - Outcome ingestion is measured against a FRESH, ISOLATED, throwaway root
    (never the real store, copied or otherwise) seeded with realistic
    fixture traces built the same way
    `tests/test_prospective_outcome_ingestion_orchestrator_v1_service.py`
    already does (`record_decision_trace` with hand-built recommendation
    payloads) -- so ingestion's own real local writes land only in that
    throwaway root.

Real, re-runnable: `python scripts/run_performance_characterization_v1.py`
from the repo root (needs live internet for the Sleeper GETs; falls back to
skipping real-league surfaces with a clear message if the real profile
copy/Sleeper reads are unavailable). Writes
`docs/codex/prospective_outcomes_v1/performance_characterization_v1/results.json`.
"""

from __future__ import annotations

import json
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.application.desktop_facade import DesktopBackendFacade, FacadeError  # noqa: E402
from src.services.in_season_decision_trace_service import record_decision_trace  # noqa: E402
from src.services.prospective_outcome_ingestion_orchestrator_v1_service import (  # noqa: E402
    run_ingestion,
)
from src.services.sleeper_import_service import SleeperHttpClient  # noqa: E402

REAL_APPDATA_REDRAFT_ROOT = Path.home() / "AppData" / "Local" / "com.ninerswarroom.redraft" / "state" / "redraft"
REAL_PROFILE_ID = "4c5f04762921420595e4d8c7cda76582"  # "Fantasy Gamers", provider=sleeper
REAL_LEAGUE_ID = "1312983576827920384"
REAL_OWNER_ROSTER_ID = 9

OUT_DIR = REPO_ROOT / "docs" / "codex" / "prospective_outcomes_v1" / "performance_characterization_v1"
REPS = 5
COLD_START_REPS = 3


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


def _time_calls(fn, reps: int = REPS) -> dict[str, Any]:
    samples: list[float] = []
    error: str | None = None
    for _ in range(reps):
        t0 = time.perf_counter()
        try:
            fn()
        except FacadeError as exc:
            error = f"{exc.code}: {exc}"
            break
        samples.append(time.perf_counter() - t0)
    if error:
        return {"error": error, "reps": len(samples)}
    return _stats(samples)


def bench_cold_startup() -> dict[str, Any]:
    """Real Python-process cold start: subprocess so imports are genuinely
    cold every rep (unlike an in-process repeat, which would reuse Python's
    module cache). This measures the backend's own cold-start cost -- the
    dominant, directly-measurable component of "time until the app can
    serve its first real request." The Tauri shell's own native-window/
    webview launch time is NOT measured here (this environment cannot
    reliably drive/screenshot a native Tauri window -- a disclosed,
    inherited limitation from prior sessions, not attempted here)."""
    code = (
        "import sys, tempfile, time\n"
        f"sys.path.insert(0, r'{REPO_ROOT}')\n"
        "t0 = time.perf_counter()\n"
        "from src.application.desktop_facade import DesktopBackendFacade\n"
        "from pathlib import Path\n"
        "with tempfile.TemporaryDirectory() as td:\n"
        f"    facade = DesktopBackendFacade(repo_root=Path(r'{REPO_ROOT}'), mode='redraft', redraft_root=Path(td) / 'store')\n"
        "    facade.redraft_bootstrap()\n"
        "print(time.perf_counter() - t0)\n"
    )
    samples: list[float] = []
    for _ in range(COLD_START_REPS):
        t0 = time.perf_counter()
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
        wall = time.perf_counter() - t0
        samples.append(wall)
    return {
        "wallClockIncludingInterpreterStartup": _stats(samples),
        "note": "subprocess wall time = interpreter startup + import + facade construction + first bootstrap "
        "(seeds the bundled projection snapshot into a fresh isolated store); does not include the Tauri "
        "native shell/webview launch, which this environment cannot reliably drive.",
    }


def _prepare_real_league_copy() -> tuple[tempfile.TemporaryDirectory | None, DesktopBackendFacade | None, str | None]:
    if not REAL_APPDATA_REDRAFT_ROOT.is_dir():
        return None, None, "Real AppData Redraft store not found on this machine; real-league surfaces skipped."
    profile_path = REAL_APPDATA_REDRAFT_ROOT / "profiles" / f"{REAL_PROFILE_ID}.json"
    if not profile_path.is_file():
        return None, None, "Real Fantasy Gamers profile not found in the real store; real-league surfaces skipped."
    tmp = tempfile.TemporaryDirectory(prefix="nwr_perf_bench_real_copy_")
    copy_root = Path(tmp.name) / "redraft"
    shutil.copytree(REAL_APPDATA_REDRAFT_ROOT, copy_root)
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=copy_root)
    facade.activate_redraft_profile(REAL_PROFILE_ID)  # writes only to the COPY
    return tmp, facade, None


def _real_current_week() -> int:
    try:
        with urlopen("https://api.sleeper.app/v1/state/nfl", timeout=15) as response:
            state = json.loads(response.read().decode("utf-8"))
        week = int(state.get("week") or 1)
        return max(1, min(18, week))
    except Exception:
        return 1


def bench_real_league_surfaces() -> dict[str, Any]:
    tmp, facade, error = _prepare_real_league_copy()
    if error:
        return {"skipped": True, "reason": error}
    assert facade is not None
    try:
        week = _real_current_week()
        out: dict[str, Any] = {"realLeagueId": REAL_LEAGUE_ID, "currentNflWeek": week}

        out["leagueOpen"] = _time_calls(lambda: facade.activate_redraft_profile(REAL_PROFILE_ID))
        out["home"] = _time_calls(lambda: facade.redraft_weekly_home_actions(week=week))
        out["lineup"] = _time_calls(lambda: facade.redraft_weekly_lineup(week=week))
        out["improveTeam_waivers"] = _time_calls(lambda: facade.redraft_waivers(mode="REST_OF_SEASON"))
        out["improveTeam_kdstStreamer"] = _time_calls(lambda: facade.redraft_kdst_streamer(week=week))
        out["tradeFinder"] = _time_calls(lambda: facade.redraft_trade_finder())
        out["tradePackageSearch_findWinWin"] = _time_calls(
            lambda: facade.redraft_trade_package_search(mode="FIND_WIN_WIN")
        )
        out["historyV3"] = _time_calls(lambda: facade.redraft_decision_trace_history())

        # Draft refresh (Draft Room's "Refresh FFC ADP" button) -- real
        # external network fetch + a real local write, both landing only in
        # the isolated COPY. Measured separately (1 rep only): repeated
        # identical ADP refreshes are not representative of real usage (an
        # owner refreshes occasionally, not in a tight loop), and hammering
        # the real FFC ADP endpoint repeatedly is inconsiderate.
        t0 = time.perf_counter()
        try:
            facade.refresh_redraft_adp(profile_id=REAL_PROFILE_ID)
            out["draftRefreshAdp"] = {"singleCallMs": (time.perf_counter() - t0) * 1000.0, "reps": 1}
        except FacadeError as exc:
            out["draftRefreshAdp"] = {"error": f"{exc.code}: {exc}", "reps": 0}

        # Player Drawer: confirmed by reading `player-detail-state.ts` this
        # pass -- there is NO dedicated backend call for opening the
        # drawer (identity is caller-supplied, status is a lookup against
        # the already-fetched PlayerAvailabilityStatus list). "First open"
        # therefore costs whatever loading `redraftPlayerAvailabilityStatus`
        # once costs (amortized across every surface, not drawer-specific);
        # "warm open" is a plain in-memory array lookup, effectively free.
        # Measured here as the one real backend read the drawer's status
        # lookup actually depends on.
        out["playerDrawerBackingStatusRead_firstOpen"] = _time_calls(
            lambda: facade.redraft_player_availability_status(), reps=1
        )
        out["playerDrawerBackingStatusRead_warmOpen"] = _time_calls(
            facade.redraft_player_availability_status, reps=REPS
        )
        out["playerDrawerNote"] = (
            "No dedicated backend endpoint exists for opening the Player Drawer (confirmed by reading "
            "player-detail-state.ts/player-detail-drawer.tsx this pass) -- identity is caller-supplied and "
            "status is an in-memory lookup against the already-loaded PlayerAvailabilityStatus list. The "
            "numbers above are for that one shared backing read, not a drawer-specific call."
        )
        return out
    finally:
        if tmp is not None:
            tmp.cleanup()


def _seed_ingestion_fixture_root(root: Path, n_traces: int) -> None:
    """Realistic-fixture traces (never real recommendations), same
    construction pattern already established and tested in
    `tests/test_prospective_outcome_ingestion_orchestrator_v1_service.py`
    -- reused here for timing purposes only, not duplicated as new
    production logic."""
    for i in range(n_traces):
        # A mix matching real production shape: some matured START_SIT
        # (will do real, network-fetching work), some immature/deferred
        # (will short-circuit quickly) -- both real code paths.
        week = 1 if i % 2 == 0 else 2
        record_decision_trace(
            root, f"profile-{i}", league_id=REAL_LEAGUE_ID, season=2026, week=week,
            tool="START_SIT", engine_version="v1", data_versions={},
            roster_state_player_ids=["4046", "4098"], recommendation={"starters": ["4046"]},
        )


def bench_outcome_ingestion() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for n in (0, 5, 20):
        with tempfile.TemporaryDirectory(prefix=f"nwr_ingestion_bench_{n}_") as td:
            root = Path(td)
            _seed_ingestion_fixture_root(root, n)
            client = SleeperHttpClient()
            t0 = time.perf_counter()
            report = run_ingestion(
                root, client=client, current_nfl_week=2,
                owner_roster_id_by_league={REAL_LEAGUE_ID: REAL_OWNER_ROSTER_ID},
            )
            elapsed = time.perf_counter() - t0
            out[f"traces_{n}"] = {
                "singleRunMs": elapsed * 1000.0,
                "countsByAction": dict(report.counts_by_action),
            }
    return out


def main() -> None:
    results: dict[str, Any] = {}
    print("Benchmarking cold startup...")
    results["coldStartup"] = bench_cold_startup()
    print("Benchmarking real Fantasy Gamers league surfaces (isolated copy, read-only Sleeper GETs)...")
    results["realLeagueSurfaces"] = bench_real_league_surfaces()
    print("Benchmarking outcome ingestion orchestrator...")
    results["outcomeIngestion"] = bench_outcome_ingestion()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
