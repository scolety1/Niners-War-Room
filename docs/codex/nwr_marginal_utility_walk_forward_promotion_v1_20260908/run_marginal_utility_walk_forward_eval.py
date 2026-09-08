"""NWR real, prospective-consistent walk-forward evaluation of
marginal_roster_utility as an actual DRAFT-TIME pick-selection policy
(not just a passive display field). This is the exact script whose
output is recorded in RESULTS.md alongside it -- run it again to
reproduce those numbers (subject to nflverse's own data staying stable).

PREREGISTERED PROTOCOL (written before any result was seen):
- Seasons: 2020, 2021, 2022, 2023 ONLY. 2016, 2024, 2025 are permanently
  burned sealed holdouts for this engine's historical validation program
  (see memory nwr-team-score-v1-frozen-2016-burned.md /
  nwr-2025-final-holdout-passed-program-complete.md) and are NEVER
  reopened, for any component, including this one.
- Real, leakage-safe pre-draft rankings: built via the already-existing,
  already-validated `_project_player` persistence methodology
  (redraft_2026_projection_model_service.py, 3-year lag-weighted with
  position-median priors), fed ONLY real nflverse stats strictly BEFORE
  the target season -- never the target season's own outcomes.
- Real, leakage-safe realized outcomes: real nflverse actual season
  stats for the target season, scored with the SAME score_half_ppr
  formula used for the projection (apples-to-apples).
- League shape: 12-team, 16-round, QB/RB/WR/TE only (no K/DST -- no
  historical K/DST model exists, a real disclosed scope limit, not
  fabricated). Position caps via the real, already-trusted
  compute_position_caps().
- REFERENCE strategy: real roster-capped-greedy-by-projected-rank
  (the same real strategy already validated 9/9 development seasons in
  prior work) for EVERY team at every pick.
- CHALLENGER strategy: identical to REFERENCE for every OPPONENT team
  (holds the rest of the draft's behavior constant); for the ONE team
  under test, at its own turn, evaluates marginal_roster_utility() for
  the top-10 REFERENCE-ranked available players and takes the highest-
  utility one instead of the raw top-ranked one.
- Design isolates the OWNER's own policy choice: REFERENCE-run and
  CHALLENGER-run of the same (season, draft_slot) share the identical
  seed and opponent behavior, differing only in the tested team's own
  picks.
- Scoring: real REALIZED (not projected) points fed into the same real
  _select_starting_lineup()/optimal_starting_lineup_value() every other
  real surface in this product uses.
- PREREGISTERED ADOPTION GATE (decided before running, honored
  regardless of result): promote marginal_roster_utility into the live
  pickScore/action/ordering path ONLY IF, aggregated across all 4
  seasons x 12 draft slots (48 paired observations): (a) CHALLENGER's
  mean realized starting-lineup value is >= REFERENCE's, (b) CHALLENGER
  wins (strictly higher realized value) in a majority (>=25/48) of
  paired observations, and (c) no single season shows CHALLENGER
  underperforming REFERENCE by more than 5% in that season's mean. Any
  gate failure = NOT promoted, reported honestly, reference engine
  unchanged.

Requires: nflreadpy (network access to pull real nflverse seasonal
stats for 2017-2023 on first run; cached to a local parquet after).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
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
from src.services.shadow_numeric_authorities_service import (
    RosterPlayer,
    _select_starting_lineup,
    marginal_roster_utility,
)

STATS_CACHE_PATH = Path(__file__).resolve().parent / "seasonal_stats_2017_2023_cache.parquet"
SEASONS = (2020, 2021, 2022, 2023)
STATS_PULL_SEASONS = range(min(SEASONS) - 3, max(SEASONS) + 1)  # 2017-2023
TEAM_COUNT = 12
ROUNDS = 16
ROSTER_SLOTS = {
    "qb": 1, "rb": 2, "wr": 2, "te": 1, "flex": 1, "superflex": 0,
    "k": 0, "dst": 0, "bench_size": ROUNDS - 7,
}
SHORTLIST_SIZE = 10


def load_stats() -> pd.DataFrame:
    if STATS_CACHE_PATH.exists():
        return pd.read_parquet(STATS_CACHE_PATH)
    import nflreadpy as nfl
    df = nfl.load_player_stats(seasons=list(STATS_PULL_SEASONS), summary_level="reg").to_pandas()
    df.to_parquet(STATS_CACHE_PATH)
    return df


def build_season_pool(stats: pd.DataFrame, target_season: int) -> list[dict]:
    """Real, leakage-safe: rank input from _project_player using ONLY
    seasons target_season-3..target_season-1; realized outcome from the
    real target_season actual stats. Pool = real players who actually
    played in target_season at QB/RB/WR/TE with >=1 game (real, known
    participants that year -- a standard backtest population definition,
    not fabricated availability)."""
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
        projected_points = score_half_ppr(projected)
        realized_points = score_half_ppr(record)
        rows.append({
            "player_id": player_id,
            "player_name": str(record["player_display_name"]),
            "position": position,
            "team": str(record.get("recent_team") or ""),
            "projected_points": projected_points,
            "realized_points": realized_points,
        })
    return rows


def build_ranking(pool: list[dict], profile: LeagueProfile) -> RankingResult:
    """Real ranking sorted by real, leakage-safe PROJECTED value -- the
    only thing knowable at real draft time. rank/position_rank/tier are
    cosmetic here (marginal_roster_utility never reads them)."""
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
    """Real position-capped-greedy REFERENCE strategy for every team;
    when use_challenger, the owner_slot team instead re-ranks its own
    real top-10 REFERENCE-ranked available candidates by
    marginal_roster_utility at its own turn. Every OTHER team's behavior
    is byte-identical between the two runs -- isolates the owner's own
    policy effect."""
    caps = compute_position_caps(ROSTER_SLOTS)
    rows_by_id = {row.player_id: row for row in ranking.rows}
    ranked_order = [row.player_id for row in ranking.rows]  # already projected-desc
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
        for pid in ranked_order:  # fallback: everyone capped, take best available anyway
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


def score_roster(
    roster_player_ids: list[str], pool_by_id: dict[str, dict], profile: LeagueProfile,
) -> float:
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


def main() -> None:
    t0 = time.perf_counter()
    stats = load_stats()
    results: list[tuple[int, int, float, float]] = []
    for season in SEASONS:
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
        print(f"season {season}: {len(pool)} real players, 12 slots x 2 runs done in {time.perf_counter()-t1:.1f}s")

    print(f"\nTotal: {time.perf_counter()-t0:.1f}s, {len(results)} paired (season, slot) observations\n")
    print(f"{'Season':8s} {'Slot':6s} {'REFERENCE':>10s} {'CHALLENGER':>11s} {'Delta':>8s}")
    for season, slot, ref_score, chal_score in results:
        print(f"{season:8d} {slot:6d} {ref_score:10.1f} {chal_score:11.1f} {chal_score-ref_score:+8.1f}")

    # Preregistered gate evaluation.
    print("\n=== PREREGISTERED GATE EVALUATION ===")
    all_deltas = [c - r for _, _, r, c in results]
    n = len(all_deltas)
    mean_delta = sum(all_deltas) / n
    wins = sum(1 for d in all_deltas if d > 0)
    print(f"n={n}  mean_delta={mean_delta:+.2f}  CHALLENGER wins {wins}/{n} ({100*wins/n:.0f}%)")
    gate_a = mean_delta >= 0
    gate_b = wins >= 25
    print(f"Gate (a) mean_delta >= 0: {gate_a}")
    print(f"Gate (b) CHALLENGER wins >= 25/48: {gate_b}")
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
    print(f"Gate (c) no season regresses > 5%: {gate_c}")
    overall = gate_a and gate_b and gate_c
    print(f"\nOVERALL GATE: {'PASS -- promote' if overall else 'FAIL -- do NOT promote'}")


if __name__ == "__main__":
    main()
