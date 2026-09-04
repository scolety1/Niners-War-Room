"""Real end-to-end latency benchmark for the live DecisionBundle endpoint
(Owner Test Candidate V1, section 11).

Measures the two real costs the owner actually waits on during a live
pick: building the comparable-league Monte Carlo reference population
(cached per-profile in the real facade, but the FIRST call per profile/
universe/market combination still pays it), and computing the
DecisionBundle itself for a realistic ~10-candidate Suggestions surface.
Fixture is the same 240-player synthetic shape used throughout this
session's shadow-authorities benchmarking -- not real player evidence.

Run: python -m scripts.run_decision_bundle_latency_benchmark_v1
"""

from __future__ import annotations

import statistics
import time

from src.services.decision_bundle_live_service import build_live_decision_bundle
from src.services.redraft_draft_room_v1_service import AdpSnapshot
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import simulate_comparable_leagues

SPEED_PRESETS = {
    "FAST": {"trials": 2, "seasons": 20, "max_candidates": 8},
    "STANDARD": {"trials": 20, "seasons": 100, "max_candidates": 10},
    "DEEP": {"trials": 50, "seasons": 200, "max_candidates": 12},
}


def _synthetic_ranking(team_count: int = 12, rounds: int = 16) -> RankingResult:
    rows = []
    for position, count in (("QB", 30), ("RB", 80), ("WR", 100), ("TE", 30)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank, index + 1, f"{position}-{index}", f"{position} {index}", position,
                    "TST", 400 - rank, 0, 400 - rank, 0,
                    "HIGH" if index < 10 else "MEDIUM", 1 + (rank - 1) // 20,
                    "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-08-17", False,
                    position_tier=1 + index // 12,
                )
            )
    profile = LeagueProfile(
        "fixture", "Fixture", 2026, team_count, RosterSettings(k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1), DraftContext(rounds=rounds, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _manual_assets() -> list[dict[str, str]]:
    return [
        {"player_id": f"manual:{p}:{i}", "player_name": f"{p} {i}", "position": p, "team": f"T{i}"}
        for p in ("K", "DST") for i in range(12)
    ]


def main() -> None:
    ranking = _synthetic_ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = AdpSnapshot(profile.profile_id, "", "ppr", profile.team_count, "", "", "", (), ())
    room_state = {"owner_slot": 1, "drafted": [], "picks": []}
    provenance = build_score_provenance(
        league_profile_hash="lp", roster_state_hash="rs", available_player_hash="ap",
        universe_hash="uh", projection_model_version="v1", market_snapshot_hash="mk",
        feature_set_version="fs", team_score_version="ts", championship_equity_version="ce",
        pick_score_version="ps", optimizer_version="opt", seed=1, simulation_count=1,
        timestamp_utc="t",
    )

    for label, preset in SPEED_PRESETS.items():
        trials = preset["trials"]
        seasons = preset["seasons"]
        max_candidates = preset["max_candidates"]
        league_times: list[float] = []
        bundle_times: list[float] = []
        for run in range(3):
            start = time.perf_counter()
            leagues = simulate_comparable_leagues(
                profile, ranking, manual_assets, adp, trials=trials, base_seed=run
            )
            league_times.append(time.perf_counter() - start)
            start2 = time.perf_counter()
            build_live_decision_bundle(
                profile, ranking, manual_assets, adp, room_state, comparable_leagues=leagues,
                provenance=provenance, max_candidates=max_candidates, trials=trials,
                seasons=seasons, base_seed=run,
            )
            bundle_times.append(time.perf_counter() - start2)
        total_times = [a + b for a, b in zip(league_times, bundle_times, strict=True)]
        print(
            f"{label}: trials={trials} seasons={seasons} max_candidates={max_candidates} | "
            f"comparable_leagues p50={statistics.median(league_times):.3f}s "
            f"decision_bundle p50={statistics.median(bundle_times):.3f}s "
            f"total p50={statistics.median(total_times):.3f}s worst={max(total_times):.3f}s "
            f"(comparable_leagues is cached per-profile/universe/market in the real facade -- "
            f"this reflects only the first, uncached call)"
        )


if __name__ == "__main__":
    main()
