"""Benchmark and exercise Team Score V2 / Championship Equity V2 / Pick
Score / the look-ahead optimizer across realistic league formats and
roster scenarios (sections 7-10 of the remaining-overnight-runway
directive).

Entirely SHADOW/RESEARCH -- exercises
src/services/shadow_numeric_authorities_service.py, which remains
unimported by desktop_facade.py and every frontend page. The synthetic
240-player ranking fixture here (QB/RB/WR/TE 30/80/100/30, the same
shape used throughout this repo's shadow-authorities test suite) is
explicitly a benchmarking fixture, not real player evidence -- it exists
to exercise the engine's latency/stability/behavior, not to produce a
claim about any real player.

Run: python scripts/run_shadow_numeric_authorities_benchmark_v1.py
Writes:
  docs/codex/TEAM_SCORE_CHAMPIONSHIP_EQUITY_BENCHMARK_V1.csv
  docs/codex/PICK_SCORE_EXAMPLES_V1.csv
  docs/codex/LOOK_AHEAD_OPTIMIZER_BENCHMARK_V1.csv
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

from src.services.ai_intelligence_backend_service import ImpactHypothesis
from src.services.redraft_draft_room_v1_service import AdpSnapshot, _asset_pool
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    availability_adjusted_players,
    championship_equity,
    evaluate_pick_candidates,
    roster_composition_report,
    simulate_comparable_leagues,
    simulate_pick_now,
    team_score,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "docs" / "codex"


def build_ranking(
    team_count: int, rounds: int, *, roster: RosterSettings | None = None
) -> RankingResult:
    rows: list[RedraftRankingRow] = []
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
        "fixture", "Fixture", 2026, team_count,
        roster or RosterSettings(k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1), DraftContext(rounds=rounds, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def manual_assets() -> list[dict[str, str]]:
    return [
        {"player_id": f"manual:{p}:{i}", "player_name": f"{p} {i}", "position": p, "team": f"T{i}"}
        for p in ("K", "DST")
        for i in range(12)
    ]


def empty_adp(profile: LeagueProfile) -> AdpSnapshot:
    return AdpSnapshot(profile.profile_id, "", "ppr", profile.team_count, "", "", "", (), ())


# --- Roster scenarios --------------------------------------------------

def _players(pool: dict, ids: list[str]) -> list[RosterPlayer]:
    out = []
    for player_id in ids:
        asset = pool[player_id]
        value = float(asset["replacement_adjusted_value"] or 0.0)
        out.append(RosterPlayer(player_id, asset["position"], value))
    return out


def roster_scenarios(pool: dict) -> dict[str, list[RosterPlayer]]:
    return {
        "star_heavy_thin_bench": _players(
            pool, ["QB-0", "RB-0", "RB-1", "WR-0", "WR-1", "TE-0", "RB-2"]
        ),
        "balanced": _players(
            pool,
            ["QB-4", "RB-4", "RB-5", "WR-4", "WR-5", "TE-4", "RB-6",
             "QB-14", "RB-14", "WR-14", "WR-15", "TE-14"],
        ),
        "qb_heavy_1qb": _players(
            pool, ["QB-0", "QB-1", "QB-2", "RB-5", "RB-6", "WR-5", "WR-6", "TE-5"]
        ),
        "rb_heavy": _players(
            pool, ["QB-8", "RB-0", "RB-1", "RB-2", "RB-3", "RB-4", "WR-8", "TE-8"]
        ),
        "wr_heavy": _players(
            pool, ["QB-8", "RB-8", "WR-0", "WR-1", "WR-2", "WR-3", "WR-4", "TE-8"]
        ),
        "missing_te": _players(
            pool, ["QB-3", "RB-3", "RB-4", "WR-3", "WR-4", "RB-30", "QB-15"]
        ),
        "injury_risk_heavy": _players(
            pool, ["QB-0", "RB-0", "RB-1", "WR-0", "WR-1", "TE-0"]
        ),
    }


def injury_hypotheses_for(scenario: list[RosterPlayer]) -> list[ImpactHypothesis]:
    # Flag the top 2 players in the "injury_risk_heavy" scenario as
    # HIGH-confidence NEGATIVE -- exercises availability_adjusted_players
    # against a real (if synthetic) roster.
    flagged = sorted(scenario, key=lambda p: -p.value)[:2]
    return [
        ImpactHypothesis(
            hypothesis_id=f"bench:{p.player_id}", subject_player_id=p.player_id,
            direction="NEGATIVE", confidence="HIGH",
            hypothesis_text=f"{p.player_id} flagged HIGH/NEGATIVE for benchmark exercise.",
            evidence_event_ids=("bench-evt",), requires_owner_review=False,
            generated_at_utc="2026-09-03T00:00:00+00:00",
        )
        for p in flagged
    ]


# --- Team Score / Championship Equity benchmark -------------------------

def run_team_score_benchmark() -> list[dict]:
    profiles = {
        "10T_1QB": build_ranking(10, 15),
        "12T_1QB": build_ranking(12, 15),
        "16T_1QB_KHA_LIKE": build_ranking(16, 16),
        "12T_SUPERFLEX": build_ranking(
            12, 15,
            roster=RosterSettings(
                qb=1, rb=2, wr=2, te=1, flex=1, superflex=1, k=1, dst=1, bench_size=6
            ),
        ),
        "12T_MULTI_FLEX": build_ranking(
            12, 15,
            roster=RosterSettings(
                qb=1, rb=2, wr=2, te=1, flex=2, superflex=0, k=1, dst=1, bench_size=6
            ),
        ),
    }
    rows: list[dict] = []
    for profile_name, ranking in profiles.items():
        profile = ranking.profile
        adp = empty_adp(profile)
        assets = manual_assets()
        pool = _asset_pool(ranking, assets)

        sim_start = time.perf_counter()
        leagues = simulate_comparable_leagues(
            profile, ranking, assets, adp, trials=30, base_seed=20260903
        )
        sim_elapsed_ms = (time.perf_counter() - sim_start) * 1000

        # Determinism check: re-running with the same seed must reproduce
        # the identical population (not just a similar one).
        leagues_repeat = simulate_comparable_leagues(
            profile, ranking, assets, adp, trials=30, base_seed=20260903
        )
        deterministic = leagues == leagues_repeat

        scenarios = roster_scenarios(pool)
        for scenario_name, roster in scenarios.items():
            adjusted_roster = roster
            note = ""
            if scenario_name == "injury_risk_heavy":
                hypotheses = injury_hypotheses_for(roster)
                adjusted_roster = availability_adjusted_players(roster, hypotheses)
                note = f"availability-discounted {len(hypotheses)} player(s)"

            composition = roster_composition_report(adjusted_roster, profile)
            player_ids = [p.player_id for p in adjusted_roster]

            score_start = time.perf_counter()
            score = team_score(player_ids, profile, ranking, assets, comparable_leagues=leagues)
            score_elapsed_ms = (time.perf_counter() - score_start) * 1000

            # Determinism check for team_score itself against the same population.
            score_repeat = team_score(
                player_ids, profile, ranking, assets, comparable_leagues=leagues
            )
            score_deterministic = score == score_repeat

            rows.append(
                {
                    "profile": profile_name,
                    "team_count": profile.team_count,
                    "scenario": scenario_name,
                    "starter_holes": "; ".join(composition.starter_holes) or "none",
                    "starting_lineup_value": composition.starting_lineup_value,
                    "bench_contingency_value": composition.bench_contingency_value,
                    "total_roster_value": composition.total_roster_value,
                    "team_score_percentile": score.percentile,
                    "population_size": score.population_size,
                    "population_mean": score.population_mean,
                    "population_stdev": score.population_stdev,
                    "simulate_comparable_leagues_ms": round(sim_elapsed_ms, 1),
                    "team_score_ms": round(score_elapsed_ms, 2),
                    "population_deterministic_same_seed": deterministic,
                    "team_score_deterministic_same_population": score_deterministic,
                    "note": note,
                }
            )
        print(
            f"[team-score] {profile_name}: sim={sim_elapsed_ms:.1f}ms "
            f"deterministic={deterministic}"
        )
    return rows


def run_championship_equity_sensitivity() -> list[dict]:
    ranking = build_ranking(12, 15)
    profile = ranking.profile
    adp = empty_adp(profile)
    assets = manual_assets()
    pool = _asset_pool(ranking, assets)
    leagues = simulate_comparable_leagues(profile, ranking, assets, adp, trials=10, base_seed=1)
    league = leagues[0]
    target_ids = [p.player_id for p in roster_scenarios(pool)["balanced"]]

    rows: list[dict] = []
    for seasons in (50, 200, 500):
        start = time.perf_counter()
        result = championship_equity(
            target_ids, profile, ranking, assets,
            comparable_league=league, target_team_slot=1, seasons=seasons, base_seed=1,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        rows.append(
            {
                "dimension": "seasons_simulated",
                "value": seasons,
                "win_probability": result.win_probability,
                "standard_error": result.standard_error,
                "latency_ms": round(elapsed_ms, 1),
            }
        )
        print(
            f"[champ-equity] seasons={seasons}: p={result.win_probability:.3f} "
            f"se={result.standard_error:.4f} {elapsed_ms:.1f}ms"
        )

    for seed in (1, 2, 3):
        result = championship_equity(
            target_ids, profile, ranking, assets,
            comparable_league=league, target_team_slot=1, seasons=200, base_seed=seed,
        )
        rows.append(
            {
                "dimension": "seed",
                "value": seed,
                "win_probability": result.win_probability,
                "standard_error": result.standard_error,
                "latency_ms": "",
            }
        )
    return rows


# --- Pick Score examples --------------------------------------------------

def run_pick_score_examples() -> list[dict]:
    scenarios = {
        "16T_PPR_KHA_LIKE": build_ranking(16, 16),
        "10T_PPR": build_ranking(10, 15),
        "12T_PPR": build_ranking(12, 15),
        "12T_SUPERFLEX": build_ranking(
            12, 15,
            roster=RosterSettings(
                qb=1, rb=2, wr=2, te=1, flex=1, superflex=1, k=1, dst=1, bench_size=6
            ),
        ),
    }
    rows: list[dict] = []
    for scenario_name, ranking in scenarios.items():
        profile = ranking.profile
        adp = empty_adp(profile)
        assets = manual_assets()
        candidates = [
            "QB-0", "QB-1", "RB-0", "RB-1", "RB-2", "WR-0", "WR-1", "WR-2", "TE-0", "TE-1",
        ]
        start = time.perf_counter()
        scored = evaluate_pick_candidates(
            profile, ranking, assets, adp, owner_slot=1, candidate_player_ids=candidates,
            trials=5, seasons=50, base_seed=20260903,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        ranked = sorted(scored.items(), key=lambda item: -item[1].relative_score)
        for rank, (player_id, result) in enumerate(ranked, start=1):
            rows.append(
                {
                    "scenario": scenario_name,
                    "rank": rank,
                    "player_id": player_id,
                    "pick_score": result.relative_score,
                    "team_score_after": result.team_score_after,
                    "championship_equity_after": result.championship_equity_after,
                    "equity_gain": result.equity_gain,
                    "cost_of_waiting": result.cost_of_waiting,
                    "evaluation_latency_ms": round(elapsed_ms, 1) if rank == 1 else "",
                }
            )
        print(f"[pick-score] {scenario_name}: {len(candidates)} candidates in {elapsed_ms:.1f}ms")
    return rows


# --- Look-ahead optimizer benchmark ---------------------------------------

def run_look_ahead_benchmark() -> list[dict]:
    rows: list[dict] = []
    for team_count, rounds in ((10, 15), (12, 15), (16, 16)):
        ranking = build_ranking(team_count, rounds)
        profile = ranking.profile
        adp = empty_adp(profile)
        assets = manual_assets()
        for candidate_count in (5, 10):
            candidates = [f"RB-{i}" for i in range(candidate_count)]
            start = time.perf_counter()
            simulate_pick_now(
                profile, ranking, assets, adp,
                owner_slot=1, candidate_player_id=candidates[0], seed=1,
            )
            single_forced_ms = (time.perf_counter() - start) * 1000

            start = time.perf_counter()
            evaluate_pick_candidates(
                profile, ranking, assets, adp, owner_slot=1, candidate_player_ids=candidates,
                trials=3, seasons=30, base_seed=1,
            )
            full_eval_ms = (time.perf_counter() - start) * 1000

            rows.append(
                {
                    "team_count": team_count,
                    "rounds": rounds,
                    "candidate_count": candidate_count,
                    "single_forced_draft_completion_ms": round(single_forced_ms, 1),
                    "full_evaluate_pick_candidates_ms": round(full_eval_ms, 1),
                    "under_2s_interactive_target": full_eval_ms < 2000,
                }
            )
            print(
                f"[optimizer] {team_count}T candidates={candidate_count}: "
                f"single={single_forced_ms:.1f}ms full={full_eval_ms:.1f}ms"
            )
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")


def main() -> None:
    overall_start = time.perf_counter()
    team_score_rows = run_team_score_benchmark()
    equity_rows = run_championship_equity_sensitivity()
    pick_score_rows = run_pick_score_examples()
    optimizer_rows = run_look_ahead_benchmark()

    _write_csv(OUT_DIR / "TEAM_SCORE_CHAMPIONSHIP_EQUITY_BENCHMARK_V1.csv", team_score_rows)
    _write_csv(OUT_DIR / "CHAMPIONSHIP_EQUITY_SENSITIVITY_V1.csv", equity_rows)
    _write_csv(OUT_DIR / "PICK_SCORE_EXAMPLES_V1.csv", pick_score_rows)
    _write_csv(OUT_DIR / "LOOK_AHEAD_OPTIMIZER_BENCHMARK_V1.csv", optimizer_rows)

    total_elapsed = time.perf_counter() - overall_start
    print(f"\nTotal benchmark wall time: {total_elapsed:.1f}s")
    slow = [r for r in optimizer_rows if not r["under_2s_interactive_target"]]
    if slow:
        print(
            f"WARNING: {len(slow)} optimizer configuration(s) exceeded the "
            "2s interactive target:"
        )
        for row in slow:
            print(f"  {row}")
    else:
        print("All optimizer configurations stayed under the 2s interactive target.")


if __name__ == "__main__":
    main()
