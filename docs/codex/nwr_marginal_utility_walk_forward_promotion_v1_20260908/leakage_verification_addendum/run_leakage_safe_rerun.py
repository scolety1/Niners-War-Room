"""NWR marginal_roster_utility walk-forward evaluation V2 -- LEAKAGE-
SAFE rerun, per owner directive (2026-09-08 addendum to the V1
promotion evaluation in the parent directory).

Two real, verified corrections vs the V1 run
(../RUN_OUTPUT.txt / ../../NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md):

1. TEMPORAL LEAKAGE (owner-flagged, confirmed real): V1 used the single
   fixed POSITION_BACKUP_UTILITY_RATE constant (nflverse 2022-2024) for
   ALL FOUR evaluation seasons (2020/2021/2022/2023) -- for 2020/2021
   this uses information from 1-4 YEARS in the future; for 2022/2023 it
   partially overlaps but still includes real future seasons (2023/2024
   relative to 2022; 2024 relative to 2023). Fixed here: for each
   evaluation season S, POSITION_BACKUP_UTILITY_RATE is derived ONLY
   from real nflverse snap-count data in the 3 seasons STRICTLY BEFORE
   S (S-3..S-1), via a temporary, in-process monkeypatch of the module
   constant -- the shipped, live source file
   (shadow_numeric_authorities_service.py) is NOT modified by this
   script (it was separately, permanently corrected in the source file
   itself, using the freshest real non-leaky window relative to today).

2. A SEPARATE, independently-verified real bug found while rebuilding
   these per-fold rates: the ORIGINAL live POSITION_BACKUP_UTILITY_RATE
   ["QB"] constant (0.125) did NOT match the real, reproducible output
   of its own cited source script (historical_backup_utility_v2.py) run
   verbatim, which gives QB=0.545 (n=22) -- RB/WR/TE (0.542/0.979/0.729)
   DID match exactly. Root cause: the script computes
   ever_rate = ever_started / n_players (a real, per-position
   CONDITIONAL rate); for RB/WR/TE, n_players is ~96 (virtually every
   team has a real RB2/WR2/TE2), so this coincides with a population-
   wide rate, but for QB, n_players is only 22 (most teams' real backup
   QB logs ZERO week-1 offensive snaps and never enters the ranked pool
   at all) -- 0.125 = 12/96 (using the OTHER positions' population size
   as QB's own denominator, a real, verified arithmetic error), not
   12/22=0.545 (QB's own real denominator, the same formula RB/WR/TE
   actually use). This script uses the mathematically consistent,
   same-formula-for-every-position CONDITIONAL rate throughout.

Same preregistered simulation structure, gates, and league shape as V1
-- unchanged, per the owner's explicit instruction not to alter gates
after seeing a result. Requires network access (nflreadpy) for the
snap-share rate windows; the player-stats cache from the parent
directory is reused for the projection/outcome side.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import nflreadpy as nfl
import polars as pl

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from src.services.redraft_2026_projection_model_service import (
    MODEL_POSITIONS,
    _project_player,
    _projection_priors,
    score_half_ppr,
)
from src.services.draft_strategy_framework_service import compute_position_caps
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
import src.services.shadow_numeric_authorities_service as shadow_service
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    _select_starting_lineup,
    marginal_roster_utility,
)

STATS_CACHE_PATH = Path(__file__).resolve().parents[1] / "seasonal_stats_2017_2023_cache.parquet"
SEASONS = (2020, 2021, 2022, 2023)
TEAM_COUNT = 12
ROUNDS = 16
ROSTER_SLOTS = {
    "qb": 1, "rb": 2, "wr": 2, "te": 1, "flex": 1, "superflex": 0,
    "k": 0, "dst": 0, "bench_size": ROUNDS - 7,
}
SHORTLIST_SIZE = 10
BACKUP_POSITIONS = ["QB", "RB", "WR", "TE"]


def load_stats() -> pd.DataFrame:
    return pd.read_parquet(STATS_CACHE_PATH)


def compute_backup_utility_rate(window_seasons: list[int]) -> dict[str, float]:
    """Real methodology, verbatim from historical_backup_utility_v2.py --
    week-1 depth rank, later-week starter-level (>=60% snap) usage,
    CONDITIONAL on the real n_players who logged a real week-1 snap at
    that depth (the same formula for every position, no special-cased
    denominator)."""
    df = nfl.load_snap_counts(seasons=window_seasons)
    df = df.filter(pl.col("position").is_in(BACKUP_POSITIONS))
    week1 = df.filter(pl.col("week") == 1)
    week1 = week1.with_columns(
        pl.col("offense_snaps").rank(method="ordinal", descending=True)
        .over(["season", "team", "position"]).alias("week1_depth_rank")
    )
    week1_ids = week1.select(["season", "team", "position", "pfr_player_id", "player", "week1_depth_rank"])
    rates: dict[str, float] = {}
    for position in BACKUP_POSITIONS:
        pos_ids = week1_ids.filter(pl.col("position") == position)
        depth_players = pos_ids.filter(pl.col("week1_depth_rank") == 2)
        n_players = depth_players.select(["season", "team", "pfr_player_id"]).unique().shape[0]
        later_weeks = df.filter(pl.col("week") >= 2).join(
            depth_players.select(["season", "team", "pfr_player_id"]),
            on=["season", "team", "pfr_player_id"], how="inner",
        )
        later_weeks = later_weeks.filter(pl.col("offense_snaps") > 0)
        ever_started = later_weeks.filter(pl.col("offense_pct") >= 0.60) \
            .select(["season", "team", "pfr_player_id"]).unique().shape[0]
        rates[position] = round(ever_started / n_players, 4) if n_players else 0.5
    return rates


def build_season_pool(stats: pd.DataFrame, target_season: int) -> list[dict]:
    history = stats[stats["season"].between(target_season - 3, target_season - 1)].copy()
    actual = stats[
        stats["season"].eq(target_season)
        & stats["position"].isin(MODEL_POSITIONS)
        & (stats["games"].fillna(0) >= 1)
    ].copy()
    actual = actual.sort_values("games", ascending=False).drop_duplicates("player_id")

    priors_by_position = {
        position: _projection_priors(history, target_season, position)
        for position in MODEL_POSITIONS
    }
    rows = []
    for record in actual.to_dict("records"):
        player_id = str(record["player_id"])
        position = str(record["position"])
        player_history = history[history["player_id"].eq(player_id)]
        projected = _project_player(
            player_history, history, target_season=target_season,
            player_id=player_id, player_name=str(record["player_display_name"]),
            position=position, team=str(record.get("recent_team") or ""),
            priors=priors_by_position.get(position),
        )
        rows.append({
            "player_id": player_id,
            "player_name": str(record["player_display_name"]),
            "position": position,
            "team": str(record.get("recent_team") or ""),
            "projected_points": score_half_ppr(projected),
            "realized_points": score_half_ppr(record),
        })
    return rows


def build_ranking(pool: list[dict], profile: LeagueProfile) -> RankingResult:
    ordered = sorted(pool, key=lambda r: -r["projected_points"])
    rows = []
    pos_rank_counters: dict[str, int] = {}
    for index, r in enumerate(ordered, start=1):
        pos_rank_counters[r["position"]] = pos_rank_counters.get(r["position"], 0) + 1
        rows.append(RedraftRankingRow(
            index, pos_rank_counters[r["position"]], r["player_id"], r["player_name"],
            r["position"], r["team"], r["projected_points"], 0.0, r["projected_points"], 0.0,
            "MEDIUM", 1 + (index - 1) // 20, "walkforward", "Walk-Forward", "GOVERNED",
            "AVAILABLE", "historical", False, position_tier=1 + (index - 1) // 12,
        ))
    return RankingResult(profile, tuple(rows), (), (), "historical", "walkforward")


def draft_order(team_count: int, rounds: int) -> tuple[int, ...]:
    order: list[int] = []
    for round_number in range(1, rounds + 1):
        slots = range(1, team_count + 1)
        order.extend(slots if round_number % 2 else reversed(tuple(slots)))
    return tuple(order)


def simulate_draft(
    ranking: RankingResult, profile: LeagueProfile, *, owner_slot: int, use_challenger: bool,
) -> list[str]:
    caps = compute_position_caps(ROSTER_SLOTS)
    rows_by_id = {row.player_id: row for row in ranking.rows}
    ranked_order = [row.player_id for row in ranking.rows]
    drafted: set[str] = set()
    rosters: dict[int, list[str]] = {slot: [] for slot in range(1, TEAM_COUNT + 1)}
    order = draft_order(TEAM_COUNT, ROUNDS)

    def reference_pick(team_slot: int) -> str | None:
        counts: dict[str, int] = {}
        for pid in rosters[team_slot]:
            counts[rows_by_id[pid].position] = counts.get(rows_by_id[pid].position, 0) + 1
        for pid in ranked_order:
            if pid in drafted:
                continue
            position = rows_by_id[pid].position
            cap = caps.get(position)
            if cap is not None and counts.get(position, 0) >= cap:
                continue
            return pid
        for pid in ranked_order:
            if pid not in drafted:
                return pid
        return None

    for team_slot in order:
        if use_challenger and team_slot == owner_slot:
            shortlist: list[str] = []
            counts: dict[str, int] = {}
            for pid in rosters[team_slot]:
                counts[rows_by_id[pid].position] = counts.get(rows_by_id[pid].position, 0) + 1
            for pid in ranked_order:
                if pid in drafted:
                    continue
                position = rows_by_id[pid].position
                cap = caps.get(position)
                if cap is not None and counts.get(position, 0) >= cap:
                    continue
                shortlist.append(pid)
                if len(shortlist) >= SHORTLIST_SIZE:
                    break
            if shortlist:
                best_pid, best_utility = None, None
                for pid in shortlist:
                    result = marginal_roster_utility(
                        pid, tuple(rosters[team_slot]), profile, ranking, (),
                    )
                    if best_utility is None or result.utility > best_utility:
                        best_pid, best_utility = pid, result.utility
                pick = best_pid
            else:
                pick = reference_pick(team_slot)
        else:
            pick = reference_pick(team_slot)
        if pick is None:
            continue
        drafted.add(pick)
        rosters[team_slot].append(pick)
    return rosters[owner_slot]


def score_roster(roster_player_ids, pool_by_id, profile) -> float:
    players = [
        RosterPlayer(pid, pool_by_id[pid]["position"], pool_by_id[pid]["realized_points"])
        for pid in roster_player_ids
    ]
    starters, _holes = _select_starting_lineup(players, profile)
    return round(sum(p.value for p in starters), 2)


def build_profile(season: int) -> LeagueProfile:
    return LeagueProfile(
        "walkforward", "Walk-Forward League", season, TEAM_COUNT,
        RosterSettings(
            qb=ROSTER_SLOTS["qb"], rb=ROSTER_SLOTS["rb"], wr=ROSTER_SLOTS["wr"],
            te=ROSTER_SLOTS["te"], flex=ROSTER_SLOTS["flex"], superflex=ROSTER_SLOTS["superflex"],
            k=ROSTER_SLOTS["k"], dst=ROSTER_SLOTS["dst"], bench_size=ROSTER_SLOTS["bench_size"],
        ),
        ScoringSettings(reception=0.5), DraftContext(rounds=ROUNDS),
    )


def print_gate_report(label: str, results: list[tuple[int, int, float, float]]) -> bool:
    print(f"\n=== {label}: PREREGISTERED GATE EVALUATION (unchanged gates) ===")
    all_deltas = [c - r for _, _, r, c in results]
    n = len(all_deltas)
    mean_delta = sum(all_deltas) / n
    sorted_deltas = sorted(all_deltas)
    median_delta = sorted_deltas[n // 2] if n % 2 else \
        (sorted_deltas[n // 2 - 1] + sorted_deltas[n // 2]) / 2
    wins = sum(1 for d in all_deltas if d > 0)
    largest_pos = max(results, key=lambda row: row[3] - row[2])
    largest_neg = min(results, key=lambda row: row[3] - row[2])
    print(f"n={n}  mean_delta={mean_delta:+.2f}  median_delta={median_delta:+.2f}  "
          f"CHALLENGER wins {wins}/{n} ({100*wins/n:.0f}%)")
    print(f"largest positive: season={largest_pos[0]} slot={largest_pos[1]} delta={largest_pos[3]-largest_pos[2]:+.1f}")
    print(f"largest negative: season={largest_neg[0]} slot={largest_neg[1]} delta={largest_neg[3]-largest_neg[2]:+.1f}")
    gate_a = mean_delta >= 0
    gate_b = wins >= 25
    gate_c = True
    for season in SEASONS:
        season_rows = [(r, c) for s, _, r, c in results if s == season]
        ref_mean = sum(r for r, c in season_rows) / len(season_rows)
        chal_mean = sum(c for r, c in season_rows) / len(season_rows)
        pct = (chal_mean - ref_mean) / ref_mean * 100 if ref_mean else 0.0
        ok = pct >= -5.0
        gate_c = gate_c and ok
        print(f"  season {season}: REFERENCE mean={ref_mean:.1f} CHALLENGER mean={chal_mean:.1f} "
              f"delta={pct:+.1f}%  {'OK' if ok else 'FAIL (regression > 5%)'}")
    overall = gate_a and gate_b and gate_c
    print(f"Gate (a) mean>=0: {gate_a}  Gate (b) wins>=25/48: {gate_b}  Gate (c) no season <-5%: {gate_c}")
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    filtered = [row for row in results if row != largest_pos]
    fd = [c - r for _, _, r, c in filtered]
    print(f"  (robustness, largest positive outlier removed: n={len(fd)} mean={sum(fd)/len(fd):+.2f} "
          f"wins={sum(1 for d in fd if d>0)}/{len(fd)})")
    return overall


def main() -> None:
    stats = load_stats()

    print("Computing leakage-safe POSITION_BACKUP_UTILITY_RATE per fold (strictly prior 3-year window)...")
    fold_rates: dict[int, dict[str, float]] = {}
    for season in SEASONS:
        window = [season - 3, season - 2, season - 1]
        rates = compute_backup_utility_rate(window)
        fold_rates[season] = rates
        print(f"  eval_season={season} rate_window={window} rates={rates}")

    original_rate = dict(shadow_service.POSITION_BACKUP_UTILITY_RATE)

    def run_all(label: str, rate_for_season) -> list[tuple[int, int, float, float]]:
        results: list[tuple[int, int, float, float]] = []
        for season in SEASONS:
            shadow_service.POSITION_BACKUP_UTILITY_RATE.clear()
            shadow_service.POSITION_BACKUP_UTILITY_RATE.update(rate_for_season(season))
            profile = build_profile(season)
            pool = build_season_pool(stats, season)
            pool_by_id = {r["player_id"]: r for r in pool}
            ranking = build_ranking(pool, profile)
            t1 = time.perf_counter()
            for slot in range(1, TEAM_COUNT + 1):
                ref_roster = simulate_draft(ranking, profile, owner_slot=slot, use_challenger=False)
                chal_roster = simulate_draft(ranking, profile, owner_slot=slot, use_challenger=True)
                ref_score = score_roster(ref_roster, pool_by_id, profile)
                chal_score = score_roster(chal_roster, pool_by_id, profile)
                results.append((season, slot, ref_score, chal_score))
            print(f"  [{label}] season {season} done in {time.perf_counter()-t1:.1f}s "
                  f"(rate used: {shadow_service.POSITION_BACKUP_UTILITY_RATE})")
        return results

    try:
        results_leakage_safe = run_all("LEAKAGE-SAFE", lambda season: fold_rates[season])
    finally:
        shadow_service.POSITION_BACKUP_UTILITY_RATE.clear()
        shadow_service.POSITION_BACKUP_UTILITY_RATE.update(original_rate)

    print("\n\n########## FINAL REPORT ##########")
    print("\nLeakage-safe per-fold rates used:")
    for season in SEASONS:
        print(f"  {season}: window={[season-3,season-2,season-1]} rates={fold_rates[season]}")

    print_gate_report("LEAKAGE-SAFE", results_leakage_safe)


if __name__ == "__main__":
    main()
