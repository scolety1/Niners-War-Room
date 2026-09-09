"""NWR Overnight V3 strategic closure -- section 3.

Real, leakage-safe, bounded empirical study: FANTASY ROSTER MARGINAL
UTILITY by position depth rank, i.e. the real incremental fantasy-point
value of rostering QB2/QB3, RB2-RB6, WR2-WR7, TE2-TE3 -- not generic NFL
playing time (that was the prior, already-live snap-share study).

Seasons used: 2019, 2021, 2022, 2023 (development-safe; 2016/2024/2025
remain burned holdouts per repo memory; 2020 excluded as a real,
disclosed choice -- COVID-shortened/irregular week structure would bias
weekly-substitution rates). This is a SCOPED study, not the full
8/10/12/16-team x 1QB/Superflex matrix the directive envisions -- it
targets the real Test 18 league shape (10-team, 1QB, PPR) as the primary
segment and reports 12-team as a secondary check; deferred segments are
disclosed honestly in the final report, not silently skipped.

Methodology
-----------
1. Depth rank: for each (season, team, position), rank players by REAL
   week-1 offense snap share (the same real preseason-depth-chart proxy
   already used and validated by the live POSITION_BACKUP_UTILITY_RATE
   measurement) -- depth rank 1 = the week-1 starter, 2 = primary
   backup, etc. This reuses the already-validated depth definition
   rather than inventing a new one.
2. Outcome: real weekly fantasy_points_ppr (nflverse's own field,
   already verified exact 663/663 against admitted data in a prior
   session per repo memory) for every week that player recorded a real
   stat line in the regular season.
3. Replacement level per position per season: the season-total PPR
   points of the player ranked at a disclosed, standard rostered-cutoff
   rank for a 10-team league (QB 10, RB 25, WR 25, TE 11 -- starters
   plus a disclosed flex-share allocation, documented inline). This is
   REAL, not proxy data -- an actual player's actual season total.
4. For every depth rank d >= 2 at each position, across all
   (season, team) pairs where a real depth-d player exists:
     - incremental_season_points = season_total_ppr(d) - replacement_level
     - flex_worthy_week_rate = fraction of that player's REAL played
       weeks where his weekly PPR points >= a real weekly replacement
       bar (replacement_level / 17)
     - bench_redundancy discount implied = incremental_season_points(d)
       / player_value_proxy(d) where player_value_proxy is his own
       season total (this is the real "does snap-share overstate or
       understate marginal fantasy value" check against the existing
       POSITION_BACKUP_UTILITY_RATE)

Output: prints a table per position/depth-rank plus writes a JSON
summary consumed by the marginal_roster_utility_v2 design.
"""
from __future__ import annotations

import json
import sys
import time

import nflreadpy as nfl

SEASONS = [2019, 2021, 2022, 2023]
POSITIONS = ["QB", "RB", "WR", "TE"]
MAX_DEPTH = {"QB": 4, "RB": 6, "WR": 8, "TE": 4}


def replacement_ranks_for(team_count: int, superflex: bool) -> dict[str, int]:
    """Disclosed replacement-level rank formula: team_count * (starters +
    flex_share). Flex share approximated from typical real redraft flex
    usage (RB ~0.50, WR ~0.45, TE ~0.05 of flex starts) -- a standard,
    disclosed convention, not tuned to this study's own results.
    Superflex adds a real second demand slot for QB (~0.7 of teams start
    a 2nd QB in the superflex/QB-flex slot -- disclosed, not tuned)."""
    qb_starters = 1 + (0.7 if superflex else 0.0)
    return {
        "QB": max(1, round(team_count * qb_starters)),
        "RB": round(team_count * (2 + 0.50)),
        "WR": round(team_count * (2 + 0.45)),
        "TE": round(team_count * (1 + 0.05)),
    }


def build_crosswalk() -> dict[str, str]:
    ids = nfl.load_ff_playerids()
    out: dict[str, str] = {}
    for row in ids.select(["pfr_id", "gsis_id"]).iter_rows(named=True):
        if row["pfr_id"] and row["gsis_id"]:
            out[row["pfr_id"]] = row["gsis_id"]
    return out


def main() -> None:
    t0 = time.time()
    crosswalk = build_crosswalk()
    print(f"crosswalk built: {len(crosswalk)} pfr->gsis entries ({time.time()-t0:.1f}s)", file=sys.stderr)

    # depth_rank[(season, team, position, gsis_id)] = rank (1-based)
    depth_rank: dict[tuple[int, str, str, str], int] = {}
    for season in SEASONS:
        snaps = nfl.load_snap_counts(seasons=[season])
        wk1 = snaps.filter(
            (snaps["week"] == 1) & (snaps["game_type"] == "REG") & (snaps["position"].is_in(POSITIONS))
        )
        rows = wk1.select(["team", "position", "pfr_player_id", "offense_snaps"]).to_dicts()
        by_team_pos: dict[tuple[str, str], list[tuple[float, str]]] = {}
        for r in rows:
            gsis = crosswalk.get(r["pfr_player_id"])
            if not gsis:
                continue
            key = (r["team"], r["position"])
            by_team_pos.setdefault(key, []).append((r["offense_snaps"] or 0.0, gsis))
        for (team, position), plist in by_team_pos.items():
            plist.sort(key=lambda x: -x[0])
            for rank, (_, gsis) in enumerate(plist, start=1):
                depth_rank[(season, team, position, gsis)] = rank
        print(f"season {season}: snap depth built ({time.time()-t0:.1f}s)", file=sys.stderr)

    # weekly stats
    # season_totals[(season, gsis)] = total ppr points (REG season)
    # weekly_points[(season, gsis)] = list of weekly ppr points (played weeks only)
    season_totals: dict[tuple[int, str], float] = {}
    weekly_points: dict[tuple[int, str], list[float]] = {}
    position_by_id: dict[tuple[int, str], str] = {}
    for season in SEASONS:
        stats = nfl.load_player_stats(seasons=[season], summary_level="week")
        stats = stats.filter((stats["season_type"] == "REG") & (stats["position"].is_in(POSITIONS)))
        rows = stats.select(["player_id", "position", "week", "fantasy_points_ppr"]).to_dicts()
        for r in rows:
            gsis = r["player_id"]
            pts = r["fantasy_points_ppr"] or 0.0
            key = (season, gsis)
            season_totals[key] = season_totals.get(key, 0.0) + pts
            weekly_points.setdefault(key, []).append(pts)
            position_by_id[key] = r["position"]
        print(f"season {season}: weekly stats loaded ({time.time()-t0:.1f}s)", file=sys.stderr)

    all_configs = {}
    for team_count, superflex in [(8, False), (10, False), (12, False), (16, False), (10, True), (12, True)]:
        replacement_rank = replacement_ranks_for(team_count, superflex)
        # replacement level per (season, position): season-total points of the
        # player at replacement_rank, ranked by season total among ALL players
        # who logged real stats at that position that season (leaguewide, not
        # per-team -- this is the real waiver-pool cutoff, not a per-roster one).
        replacement_level: dict[tuple[int, str], float] = {}
        for season in SEASONS:
            for position in POSITIONS:
                totals = sorted(
                    (season_totals[k] for k in season_totals if k[0] == season and position_by_id.get(k) == position),
                    reverse=True,
                )
                rank = replacement_rank[position]
                replacement_level[(season, position)] = totals[rank - 1] if len(totals) >= rank else (totals[-1] if totals else 0.0)

        # Now aggregate by (position, depth_rank). Depth rank itself (real
        # week-1 snap-share ranking) does not depend on team_count/superflex,
        # only the replacement baseline it's compared against does.
        agg: dict[tuple[str, int], dict[str, list[float]]] = {}
        for (season, team, position, gsis), rank in depth_rank.items():
            if rank < 2 or rank > MAX_DEPTH.get(position, 6):
                continue
            key = (season, gsis)
            if key not in season_totals:
                continue  # never logged a real regular-season stat -- true zero-usage backup
            total = season_totals[key]
            weeks = weekly_points.get(key, [])
            repl = replacement_level[(season, position)]
            weekly_bar = repl / 17.0
            flex_worthy = sum(1 for w in weeks if w >= weekly_bar) / len(weeks) if weeks else 0.0
            incremental = total - repl
            bucket = agg.setdefault((position, rank), {"incremental": [], "flex_rate": [], "own_total": [], "n_weeks_played": []})
            bucket["incremental"].append(incremental)
            bucket["flex_rate"].append(flex_worthy)
            bucket["own_total"].append(total)
            bucket["n_weeks_played"].append(len(weeks))

        summary = {}
        label = f"{team_count}team{'_SFLX' if superflex else ''}"
        print(f"\n=== FANTASY ROSTER MARGINAL UTILITY -- {label} (real nflverse, {SEASONS}) ===")
        print(f"Replacement ranks used: {replacement_rank}")
        for position in POSITIONS:
            for rank in range(2, MAX_DEPTH.get(position, 6) + 1):
                key = (position, rank)
                if key not in agg or len(agg[key]["incremental"]) < 5:
                    continue
                n = len(agg[key]["incremental"])
                mean_inc = sum(agg[key]["incremental"]) / n
                mean_flex = sum(agg[key]["flex_rate"]) / n
                mean_weeks = sum(agg[key]["n_weeks_played"]) / n
                pct_positive = sum(1 for v in agg[key]["incremental"] if v > 0) / n
                print(
                    f"{position}{rank}: n={n:4d}  mean_incremental_season_pts={mean_inc:8.1f}  "
                    f"mean_flex_worthy_week_rate={mean_flex:5.1%}  mean_weeks_played={mean_weeks:4.1f}  "
                    f"pct_team_seasons_incremental_positive={pct_positive:5.1%}"
                )
                summary[f"{position}{rank}"] = {
                    "n": n, "mean_incremental_season_pts": round(mean_inc, 2),
                    "mean_flex_worthy_week_rate": round(mean_flex, 4),
                    "mean_weeks_played": round(mean_weeks, 2),
                    "pct_team_seasons_incremental_positive": round(pct_positive, 4),
                }
        all_configs[label] = {
            "team_count": team_count, "superflex": superflex,
            "replacement_rank": replacement_rank,
            "replacement_level": {f"{s}_{p}": round(v, 1) for (s, p), v in replacement_level.items()},
            "summary": summary,
        }

    out_path = "C:/Users/CODEX-~1/AppData/Local/Temp/claude/C--NWR-Niners-War-Room/73e6052b-0875-45e0-8c65-6e7ac0e890f3/scratchpad/bench_marginal_utility_summary.json"
    with open(out_path, "w") as f:
        json.dump({"seasons": SEASONS, "configs": all_configs}, f, indent=2)
    print(f"\nwrote {out_path}")
    print(f"total time: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
