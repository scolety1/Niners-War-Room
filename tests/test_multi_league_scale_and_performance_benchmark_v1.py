"""NWR Prospective Outcomes V1, Worker 8, Work Units 19-20 -- hermetic
tests for the reusable benchmark scripts' own pure/isolated logic. The
real-network-dependent parts of `run_performance_characterization_v1.py`
(real Fantasy Gamers Sleeper reads) are NOT exercised here, matching every
other real-network script in this repo's own established convention (see
e.g. `scripts/build_prospective_outcome_ingestion_v1_startsit_demo.py`'s
own docstring) -- these tests instead prove the statistics helpers are
correct and that the isolated, local-only code paths (profile generation,
the scale-fanout loop against a temp store, ingestion-fixture seeding) run
end to end without touching any real league or the real AppData store.
"""

from __future__ import annotations

from pathlib import Path

from scripts.run_multi_league_scale_benchmark_v1 import (
    _bench_attention_center_fanout,
    _build_isolated_store,
    _linearity_check,
    _percentile,
    _stats,
)
from scripts.run_performance_characterization_v1 import (
    REAL_APPDATA_REDRAFT_ROOT,
    _seed_ingestion_fixture_root,
    _stats as perf_stats,
)
from src.services.in_season_decision_trace_service import load_decision_traces


def test_percentile_and_stats_are_correct_on_known_values() -> None:
    values = [0.001, 0.002, 0.003, 0.004, 0.005]  # seconds
    stats = _stats(values)
    assert stats["reps"] == 5
    assert stats["medianMs"] == 3.0
    assert stats["minMs"] == 1.0
    assert stats["maxMs"] == 5.0
    # p95 of 5 sorted values (1-indexed ceil(0.95*5)=5th) is the max.
    assert stats["p95Ms"] == 5.0


def test_percentile_handles_empty_input() -> None:
    assert _percentile([], 95) == 0.0


def test_perf_script_stats_helper_matches_scale_script_stats_helper() -> None:
    values = [0.01, 0.02, 0.03]
    assert perf_stats(values) == _stats(values)


def test_build_isolated_store_never_touches_the_real_appdata_redraft_root(tmp_path: Path) -> None:
    """The single highest-risk property of the scale-benchmark script:
    every profile it creates lives under a fresh temp directory, never
    under the real owner's AppData Redraft store. Proven by asserting the
    isolated store's resolved path never starts with the real root's own
    resolved path (a real, currently-installed real store on this machine
    included, if present)."""
    tmp, facade, profile_ids = _build_isolated_store(3)
    try:
        assert len(profile_ids) == 3
        resolved_store = facade.redraft_root.resolve()
        real_root = REAL_APPDATA_REDRAFT_ROOT.resolve()
        assert not str(resolved_store).startswith(str(real_root))
    finally:
        tmp.cleanup()


def test_attention_center_fanout_bench_runs_hermetically_against_an_isolated_store() -> None:
    tmp, facade, profile_ids = _build_isolated_store(4)
    try:
        result = _bench_attention_center_fanout(facade, profile_ids, reps=2)
        assert result["totalPass"]["reps"] == 2
        assert result["totalPass"]["medianMs"] >= 0.0
        for key in ("perLeagueCall_activate", "perLeagueCall_dataHealth", "perLeagueCall_workspaceContext"):
            assert result[key]["reps"] == 2 * len(profile_ids)
    finally:
        tmp.cleanup()


def test_linearity_check_flags_superlinear_growth() -> None:
    linear_results = {
        "byLeagueCount": [
            {"leagues": 5, "attentionCenterFanout": {"totalPass": {"medianMs": 50.0}}},
            {"leagues": 50, "attentionCenterFanout": {"totalPass": {"medianMs": 500.0}}},
        ]
    }
    assert _linearity_check(linear_results)["verdictHint"] == "LINEAR_OR_BETTER"

    superlinear_results = {
        "byLeagueCount": [
            {"leagues": 5, "attentionCenterFanout": {"totalPass": {"medianMs": 50.0}}},
            {"leagues": 50, "attentionCenterFanout": {"totalPass": {"medianMs": 5000.0}}},
        ]
    }
    assert _linearity_check(superlinear_results)["verdictHint"] == "SUPERLINEAR_SIGNAL_INVESTIGATE"


def test_seed_ingestion_fixture_root_writes_only_realistic_disclosed_fixture_traces(tmp_path: Path) -> None:
    _seed_ingestion_fixture_root(tmp_path, 4)
    total = 0
    for i in range(4):
        records = load_decision_traces(tmp_path, f"profile-{i}")
        assert len(records) == 1
        assert records[0].tool == "START_SIT"
        total += 1
    assert total == 4
