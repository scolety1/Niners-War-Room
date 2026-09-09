"""NWR Overnight V3 strategic closure -- section 5.

Test 18 exact counterfactual replay: REFERENCE (marginal_roster_utility,
the current fdf3bdd7 live-promoted candidate ordering signal) vs
CHALLENGER (marginal_roster_utility_v2, this session's empirically
re-derived bench-utility model) vs the real historical owner picks.

Player pool: REAL 2023 nflverse season-total PPR fantasy points (a real,
non-burned, non-2016/2024/2025 season) stand in for `replacement_adjusted_
value` -- this worktree has no governed 2026 projection snapshot
installed (disclosed, pre-existing, owner-approval-gated environment
gap), so a fabricated/synthetic value scale would not give a genuine
test of cross-positional scarcity. Real 2023 outcomes give real,
non-invented relative spacing between e.g. RB8 and WR8.

This is NOT a live production run -- it directly exercises the real
`evaluate_draft_pick_legality`, `marginal_roster_utility`, and
`marginal_roster_utility_v2` functions against a constructed board, the
same functions the live desktop app calls.
"""
from __future__ import annotations

import sys
from dataclasses import replace as dc_replace

sys.path.insert(0, "C:/NWR/overnight-full-advance-v3")

import nflreadpy as nfl

from src.services.redraft_draft_room_v1_service import AdpSnapshot, draft_order
from src.services.redraft_engine_v1_service import (
    DraftContext, LeagueProfile, RankingResult, RedraftRankingRow, RosterSettings, ScoringSettings,
)
from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from src.services.shadow_numeric_authorities_service import marginal_roster_utility, marginal_roster_utility_v2

TEAM_COUNT = 10
OWNER_SLOT = 5
ROUNDS = 16
WR_MAX = 8

ACTUAL_OWNER_PICKS = [
    ("christian-mccaffrey", "Christian McCaffrey", "RB"),
    ("trey-mcbride", "Trey McBride", "TE"),
    ("chris-olave", "Chris Olave", "WR"),
    ("zay-flowers", "Zay Flowers", "WR"),
    ("josh-jacobs", "Josh Jacobs", "RB"),
    ("matthew-stafford", "Matthew Stafford", "QB"),
    ("michael-wilson", "Michael Wilson", "WR"),
    ("wandale-robinson", "Wan'Dale Robinson", "WR"),
    ("courtland-sutton", "Courtland Sutton", "WR"),
    ("trevor-lawrence", "Trevor Lawrence", "QB"),
    ("keenan-allen", "Keenan Allen", "WR"),
    ("jakobi-meyers", "Jakobi Meyers", "WR"),
    ("jauan-jennings", "Jauan Jennings", "WR"),
]


def build_real_ranking(profile: LeagueProfile) -> RankingResult:
    stats = nfl.load_player_stats(seasons=[2023], summary_level="reg")
    stats = stats.filter((stats["season_type"] == "REG") & (stats["position"].is_in(["QB", "RB", "WR", "TE"])))
    rows_raw = stats.select(["player_id", "player_display_name", "position", "recent_team", "fantasy_points_ppr"]).to_dicts()
    caps = {"QB": 40, "RB": 90, "WR": 120, "TE": 40}
    by_pos: dict[str, list[dict]] = {}
    for r in rows_raw:
        by_pos.setdefault(r["position"], []).append(r)
    pool: list[dict] = []
    for pos, cap in caps.items():
        ranked = sorted(by_pos.get(pos, []), key=lambda r: -(r["fantasy_points_ppr"] or 0.0))[:cap]
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
    return RankingResult(profile=profile, rows=rows, replacement_levels=(), blocked_rows=(), generated_at_utc="replay", projection_sha256="replay")


def build_profile() -> LeagueProfile:
    return LeagueProfile(
        profile_id="test18-replay", league_name="Test 18 Counterfactual Replay", season=2026,
        team_count=TEAM_COUNT,
        roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=7),
        scoring=ScoringSettings(reception=1.0),
        draft=DraftContext(rounds=ROUNDS, draft_slot=OWNER_SLOT, roster_limits={"WR": WR_MAX}),
        provider="local",
    )


def best_legal_by_position_map(pool_by_id: dict, roster_counter, profile: LeagueProfile, drafted: set[str]) -> list[dict]:
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


def run_simulation(policy: str, ranking: RankingResult, profile: LeagueProfile) -> list[dict]:
    """policy in {'reference', 'challenger', 'actual'}. Opponents always
    use best-available-real-value (a real, deterministic ADP-like proxy)."""
    from collections import Counter
    order = draft_order(profile)
    rankings_by_id = {r.player_id: {"player_id": r.player_id, "player_name": r.player_name, "position": r.position, "projected_points": r.projected_points} for r in ranking.rows}
    name_index = {v["player_name"].lower().replace(".", "").replace("'", ""): v for v in rankings_by_id.values()}
    drafted: set[str] = set()
    rosters: dict[int, Counter] = {slot: Counter() for slot in range(1, TEAM_COUNT + 1)}
    owner_ids: list[str] = []
    trace: list[dict] = []
    actual_idx = 0
    for pick_number, slot in enumerate(order, start=1):
        round_number = ((pick_number - 1) // TEAM_COUNT) + 1
        if round_number > ROUNDS:
            break
        legal = best_legal_by_position_map(rankings_by_id, rosters[slot], profile, drafted)
        if not legal:
            break
        if slot == OWNER_SLOT:
            roster_before = dict(rosters[slot])
            if policy == "actual" and actual_idx < len(ACTUAL_OWNER_PICKS):
                want_name = ACTUAL_OWNER_PICKS[actual_idx][1].lower().replace(".", "").replace("'", "")
                pick = name_index.get(want_name)
                if pick is None or pick["player_id"] in drafted or not evaluate_draft_pick_legality(profile, rosters[slot], pick["position"]).allowed:
                    # Real player not in the 2023 pool (e.g. a rookie who
                    # didn't play in 2023) or already off the board in
                    # this replay's own sequence -- honestly fall back to
                    # the legal-best rather than fabricate a match.
                    pick = legal[0]
                actual_idx += 1
            elif policy == "reference":
                pick = pick_by_signal(legal, owner_ids, profile, ranking, marginal_roster_utility)
            elif policy == "challenger":
                pick = pick_by_signal(legal, owner_ids, profile, ranking, marginal_roster_utility_v2)
            else:
                pick = legal[0]
            owner_ids.append(pick["player_id"])
            trace.append({"round": round_number, "roster_before": roster_before, "pick": pick})
        else:
            pick = max(legal, key=lambda r: r["projected_points"])
        drafted.add(pick["player_id"])
        rosters[slot][pick["position"]] += 1
    return trace


def position_counts(trace: list[dict]) -> dict:
    from collections import Counter
    c = Counter(t["pick"]["position"] for t in trace)
    return dict(c)


def main() -> None:
    profile = build_profile()
    ranking = build_real_ranking(profile)
    print(f"Real 2023 player pool built: {len(ranking.rows)} rows\n")

    ref_trace = run_simulation("reference", ranking, profile)
    chal_trace = run_simulation("challenger", ranking, profile)
    actual_trace = run_simulation("actual", ranking, profile)

    print("=== ROUND-BY-ROUND: REFERENCE vs CHALLENGER vs ACTUAL ===")
    print(f"{'Rd':>3} | {'REFERENCE pick':<28} | {'CHALLENGER pick':<28} | {'ACTUAL pick':<24}")
    for i in range(max(len(ref_trace), len(chal_trace), len(actual_trace))):
        r = ref_trace[i]["pick"] if i < len(ref_trace) else None
        c = chal_trace[i]["pick"] if i < len(chal_trace) else None
        a = actual_trace[i]["pick"] if i < len(actual_trace) else None
        rs = f"{r['player_name']} ({r['position']})" if r else "-"
        cs = f"{c['player_name']} ({c['position']})" if c else "-"
        as_ = f"{a['player_name']} ({a['position']})" if a else "-"
        print(f"{i+1:>3} | {rs:<28} | {cs:<28} | {as_:<24}")

    print("\n=== FINAL POSITION COUNTS ===")
    print("REFERENCE:", position_counts(ref_trace))
    print("CHALLENGER:", position_counts(chal_trace))
    print("ACTUAL:    ", position_counts(actual_trace))

    print("\n=== ROSTER-BEFORE STATE AT KEY ROUNDS (R6-R14) ===")
    for i in range(5, min(14, len(chal_trace))):
        rb = chal_trace[i]["roster_before"]
        rp = chal_trace[i]["pick"]
        refp = ref_trace[i]["pick"] if i < len(ref_trace) else None
        print(f"R{i+1}: roster_before={rb}  CHALLENGER->{rp['player_name']}({rp['position']})  REFERENCE->{refp['player_name'] if refp else '-'}({refp['position'] if refp else '-'})")


if __name__ == "__main__":
    main()
