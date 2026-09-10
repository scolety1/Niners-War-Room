"""NWR Overnight V3 strategic-model-validation resume, section 7.

Blind draft battery: REFERENCE (marginal_roster_utility) vs CHALLENGER
(marginal_roster_utility_v2) across 5 league shapes, same opponent
policy/draft order/player pool per shape (deterministic -- no v3, not
built this pass, see section 4 finding). Directly generalizes the prior
pass's own `test18_counterfactual_replay.py` mechanism (real 2023
nflverse season-total PPR pool standing in for `replacement_adjusted_
value` -- same disclosed, pre-existing governed-2026-snapshot gap noted
there) to more shapes rather than re-deriving a new methodology.
"""
from __future__ import annotations

import json
import sys
from collections import Counter

sys.path.insert(0, "C:/NWR/overnight-full-advance-v3")

import nflreadpy as nfl

from src.services.redraft_draft_room_v1_service import draft_order
from src.services.redraft_engine_v1_service import (
    DraftContext, LeagueProfile, RankingResult, RedraftRankingRow, RosterSettings, ScoringSettings,
)
from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from src.services.shadow_numeric_authorities_service import marginal_roster_utility, marginal_roster_utility_v2

SHAPES = [
    {
        "key": "10PPR_slot5", "team_count": 10, "owner_slot": 5, "rounds": 16,
        "roster": RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=7),
        "roster_limits": {"WR": 8},
    },
    {
        "key": "8_1QB", "team_count": 8, "owner_slot": 4, "rounds": 16,
        "roster": RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=7),
        "roster_limits": {},
    },
    {
        "key": "12_1QB", "team_count": 12, "owner_slot": 6, "rounds": 16,
        "roster": RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=7),
        "roster_limits": {},
    },
    {
        "key": "16_1QB", "team_count": 16, "owner_slot": 8, "rounds": 16,
        "roster": RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=7),
        "roster_limits": {},
    },
    {
        "key": "12_Superflex", "team_count": 12, "owner_slot": 6, "rounds": 16,
        "roster": RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=1, k=1, dst=1, bench_size=6),
        "roster_limits": {},
    },
]

CAPS = {"QB": 60, "RB": 160, "WR": 220, "TE": 60}


def build_real_ranking(profile: LeagueProfile, raw_by_pos: dict[str, list[dict]]) -> RankingResult:
    pool: list[dict] = []
    for pos, cap in CAPS.items():
        ranked = sorted(raw_by_pos.get(pos, []), key=lambda r: -(r["fantasy_points_ppr"] or 0.0))[:cap]
        pool.extend(ranked)
    pool.sort(key=lambda r: -(r["fantasy_points_ppr"] or 0.0))
    rows = tuple(
        RedraftRankingRow(
            overall_rank=i + 1, position_rank=i + 1, player_id=r["player_id"],
            player_name=r["player_display_name"], position=r["position"], team=r["recent_team"] or "FA",
            projected_points=round(r["fantasy_points_ppr"] or 0.0, 1), replacement_points=0.0,
            replacement_adjusted_value=round(r["fantasy_points_ppr"] or 0.0, 1), starter_gap=0.0,
            confidence="HIGH", tier=1, profile_id=profile.profile_id, profile_name=profile.league_name,
            source_status="GOVERNED", evidence_status="AVAILABLE", source_as_of="2023-real-season-total",
            rookie=False,
        )
        for i, r in enumerate(pool)
    )
    return RankingResult(profile=profile, rows=rows, replacement_levels=(), blocked_rows=(), generated_at_utc="battery", projection_sha256="battery")


def build_profile(shape: dict) -> LeagueProfile:
    return LeagueProfile(
        profile_id=f"battery-{shape['key']}", league_name=f"Blind Battery {shape['key']}", season=2026,
        team_count=shape["team_count"], roster=shape["roster"], scoring=ScoringSettings(reception=1.0),
        draft=DraftContext(rounds=shape["rounds"], draft_slot=shape["owner_slot"], roster_limits=shape["roster_limits"]),
        provider="local",
    )


def best_legal(pool_by_id: dict, roster_counter, profile: LeagueProfile, drafted: set[str]) -> list[dict]:
    return [
        r for r in pool_by_id.values()
        if r["player_id"] not in drafted and evaluate_draft_pick_legality(profile, roster_counter, r["position"]).allowed
    ]


def pick_by_signal(candidates: list[dict], current_ids: list[str], profile: LeagueProfile, ranking: RankingResult, signal_fn) -> dict | None:
    if not candidates:
        return None
    scored = []
    for c in candidates:
        result = signal_fn(c["player_id"], current_ids, profile, ranking, ())
        scored.append((result.utility, c["projected_points"], c))
    scored.sort(key=lambda t: (-t[0], -t[1]))
    return scored[0][2]


def run_simulation(policy: str, ranking: RankingResult, profile: LeagueProfile, shape: dict) -> dict:
    team_count = shape["team_count"]
    owner_slot = shape["owner_slot"]
    rounds = shape["rounds"]
    order = draft_order(profile)
    rankings_by_id = {r.player_id: {"player_id": r.player_id, "player_name": r.player_name, "position": r.position, "projected_points": r.projected_points} for r in ranking.rows}
    drafted: set[str] = set()
    rosters: dict[int, Counter] = {slot: Counter() for slot in range(1, team_count + 1)}
    owner_ids: list[str] = []
    illegal_recommendations = 0
    for pick_number, slot in enumerate(order, start=1):
        round_number = ((pick_number - 1) // team_count) + 1
        if round_number > rounds:
            break
        legal = best_legal(rankings_by_id, rosters[slot], profile, drafted)
        if not legal:
            break
        if slot == owner_slot:
            signal_fn = marginal_roster_utility if policy == "reference" else marginal_roster_utility_v2
            pick = pick_by_signal(legal, owner_ids, profile, ranking, signal_fn)
            # Independent legality re-verification of the recommended pick
            # (gate 4): recompute legality fresh, never trust the filter
            # that produced `legal` without re-checking.
            if not evaluate_draft_pick_legality(profile, rosters[slot], pick["position"]).allowed:
                illegal_recommendations += 1
            owner_ids.append(pick["player_id"])
        else:
            pick = max(legal, key=lambda r: r["projected_points"])
        drafted.add(pick["player_id"])
        rosters[slot][pick["position"]] += 1
    counts = Counter()
    for pid in owner_ids:
        counts[rankings_by_id[pid]["position"]] += 1
    kdst_complete = counts.get("K", 0) >= shape["roster"].k and counts.get("DST", 0) >= shape["roster"].dst
    return {
        "policy": policy, "n_picks": len(owner_ids), "position_counts": dict(counts),
        "illegal_recommendations": illegal_recommendations, "kdst_complete": kdst_complete,
        "max_single_position": max(counts.values()) if counts else 0,
    }


def main() -> int:
    print("Loading real 2023 nflverse season-total stats (shared across all shapes)...")
    stats = nfl.load_player_stats(seasons=[2023], summary_level="reg")
    stats = stats.filter((stats["season_type"] == "REG") & (stats["position"].is_in(["QB", "RB", "WR", "TE"])))
    rows_raw = stats.select(["player_id", "player_display_name", "position", "recent_team", "fantasy_points_ppr"]).to_dicts()
    raw_by_pos: dict[str, list[dict]] = {}
    for r in rows_raw:
        raw_by_pos.setdefault(r["position"], []).append(r)
    print(f"Loaded {len(rows_raw)} real player-season rows.\n")

    results = []
    for shape in SHAPES:
        profile = build_profile(shape)
        ranking = build_real_ranking(profile, raw_by_pos)
        ref = run_simulation("reference", ranking, profile, shape)
        chal = run_simulation("challenger", ranking, profile, shape)
        print(f"=== {shape['key']} (team_count={shape['team_count']}, slot={shape['owner_slot']}, "
              f"superflex={shape['roster'].superflex}) ===")
        print("  REFERENCE :", ref)
        print("  CHALLENGER:", chal)
        results.append({"shape": shape["key"], "reference": ref, "challenger": chal})

    out = {"results": results}
    with open("docs/codex/overnight_v3/harness_v1/blind_draft_battery_v1_report.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nWrote blind_draft_battery_v1_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
