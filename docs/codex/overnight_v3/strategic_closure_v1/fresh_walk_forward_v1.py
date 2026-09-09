"""NWR Overnight V3 strategic closure -- section 7, fresh walk-forward.

Preregistered contract: docs/codex/overnight_v3/NWR_STRATEGIC_CLOSURE_VALIDATION_CONTRACT.md
REFERENCE = marginal_roster_utility (live-promoted, unchanged).
CHALLENGER = marginal_roster_utility_v2 (this session's addition).

DISCLOSED METHODOLOGY / BLOCKER: the frozen historical-tuning worktree
(`work/nwr-full-historical-tuning-v1-20260904`, commit 9132f501) has a
directly reusable pluggable-strategy interface
(`draft_strategy_framework_service.make_optimizer_strategy` +
`historical_draft_replay_engine_service`) built for exactly this kind of
comparison. It was NOT used here: that worktree's `LeagueProfile`/
`RankingResult`/etc. dataclasses are a separately-diverged lineage from
this branch's own `redraft_engine_v1_service` types that
`marginal_roster_utility_v2` requires structurally, and its
`PointInTimeFeatureStore` corpus is real, governed, historical source
data this session must not touch/modify/re-derive under load in a
cross-worktree Python process on a bounded time budget. Attempting a
live cross-worktree import risked burning the remaining session on
compatibility debugging rather than delivering a real result.

Instead, this fresh walk-forward reuses THIS branch's own already-
validated real-data pipeline (the exact same nflreadpy access used for
bench_marginal_utility_study_v1.py) and extends the Test 18 replay
methodology (test18_counterfactual_replay.py) across MULTIPLE real
seasons and draft slots, with a genuine leakage-safe design: a team's
DRAFT-TIME value comes from the PRIOR season's real PPR total (a
standard, disclosed naive-projection proxy -- "what a real draft board
would roughly look like using only information available before season
S"), and the EVALUATION metric (optimal starting-lineup value) comes
from season S's own REAL outcomes -- never the same season for both,
avoiding the same-season circularity the single-season Test 18 replay
(section 5) explicitly disclosed as a simplification.

Season pairs (draft-year -> evaluation-year), all within development
seasons -- 2016/2024/2025 stay burned holdouts, never touched:
  2018 -> 2019, 2021 -> 2022, 2022 -> 2023
Draft slots evaluated: 1, 5, 10 (early/middle/late snake position).
League shape: 10-team, 1QB, PPR, roster_limits={"WR": 8} (Test 18's own
real cap), matching the real evidence this whole strategic-closure pass
is about.
"""
from __future__ import annotations

import sys
from collections import Counter

sys.path.insert(0, "C:/NWR/overnight-full-advance-v3")

import nflreadpy as nfl

from src.services.redraft_draft_room_v1_service import draft_order
from src.services.redraft_engine_v1_service import (
    DraftContext, LeagueProfile, RankingResult, RedraftRankingRow, RosterSettings, ScoringSettings,
)
from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from src.services.shadow_numeric_authorities_service import (
    marginal_roster_utility, marginal_roster_utility_v2, roster_composition_report, RosterPlayer,
)

TEAM_COUNT = 10
ROUNDS = 16
WR_MAX = 8
SLOTS = [1, 5, 10]
SEASON_PAIRS = [(2018, 2019), (2021, 2022), (2022, 2023)]


def _season_totals(season: int) -> dict[str, dict]:
    stats = nfl.load_player_stats(seasons=[season], summary_level="reg")
    stats = stats.filter((stats["season_type"] == "REG") & (stats["position"].is_in(["QB", "RB", "WR", "TE"])))
    rows = stats.select(["player_id", "player_display_name", "position", "recent_team", "fantasy_points_ppr"]).to_dicts()
    out: dict[str, dict] = {}
    for r in rows:
        out[r["player_id"]] = {
            "player_id": r["player_id"], "player_name": r["player_display_name"],
            "position": r["position"], "team": r["recent_team"] or "FA",
            "points": r["fantasy_points_ppr"] or 0.0,
        }
    return out


def build_profile(slot: int) -> LeagueProfile:
    return LeagueProfile(
        profile_id=f"walk-forward-{slot}", league_name="Fresh Walk-Forward V1", season=2026,
        team_count=TEAM_COUNT,
        # k=0/dst=0: this synthetic pool (QB/RB/WR/TE only, real 2018-2023
        # nflverse totals) has no real K/DST assets -- a mandatory K/DST
        # slot with zero legal candidates would terminate the WHOLE
        # simulated draft early via the shared `if not legal: break`,
        # contaminating every team's late-round comparison, not just the
        # owner's. Disclosed simplification, matching a prior session's
        # same real choice for an analogous reason.
        roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=9),
        scoring=ScoringSettings(reception=1.0),
        draft=DraftContext(rounds=ROUNDS, draft_slot=slot, roster_limits={"WR": WR_MAX}),
        provider="local",
    )


def build_ranking_from_draft_values(profile: LeagueProfile, draft_values: dict[str, dict]) -> RankingResult:
    caps = {"QB": 40, "RB": 90, "WR": 120, "TE": 40}
    by_pos: dict[str, list[dict]] = {}
    for r in draft_values.values():
        by_pos.setdefault(r["position"], []).append(r)
    pool: list[dict] = []
    for pos, cap in caps.items():
        ranked = sorted(by_pos.get(pos, []), key=lambda r: -r["points"])[:cap]
        pool.extend(ranked)
    pool.sort(key=lambda r: -r["points"])
    rows = tuple(
        RedraftRankingRow(
            overall_rank=i + 1, position_rank=i + 1, player_id=r["player_id"], player_name=r["player_name"],
            position=r["position"], team=r["team"], projected_points=round(r["points"], 1),
            replacement_points=0.0, replacement_adjusted_value=round(r["points"], 1), starter_gap=0.0,
            confidence="HIGH", tier=1, profile_id=profile.profile_id, profile_name=profile.league_name,
            source_status="GOVERNED", evidence_status="AVAILABLE", source_as_of="walk-forward-prior-season",
            rookie=False,
        )
        for i, r in enumerate(pool)
    )
    return RankingResult(profile=profile, rows=rows, replacement_levels=(), blocked_rows=(), generated_at_utc="walk-forward", projection_sha256="walk-forward")


def run_draft(policy: str, ranking: RankingResult, profile: LeagueProfile, owner_slot: int) -> list[str]:
    order = draft_order(profile)
    pool_by_id = {r.player_id: {"player_id": r.player_id, "position": r.position, "projected_points": r.projected_points} for r in ranking.rows}
    drafted: set[str] = set()
    rosters: dict[int, Counter] = {slot: Counter() for slot in range(1, TEAM_COUNT + 1)}
    owner_ids: list[str] = []
    for pick_number, slot in enumerate(order, start=1):
        round_number = ((pick_number - 1) // TEAM_COUNT) + 1
        if round_number > ROUNDS:
            break
        legal = [r for r in pool_by_id.values() if r["player_id"] not in drafted and evaluate_draft_pick_legality(profile, rosters[slot], r["position"]).allowed]
        if not legal:
            break
        if slot == owner_slot:
            if policy == "reference":
                scored = [(marginal_roster_utility(c["player_id"], owner_ids, profile, ranking, ()).utility, c["projected_points"], c) for c in legal]
            else:
                scored = [(marginal_roster_utility_v2(c["player_id"], owner_ids, profile, ranking, ()).utility, c["projected_points"], c) for c in legal]
            scored.sort(key=lambda t: (-t[0], -t[1]))
            pick = scored[0][2]
            owner_ids.append(pick["player_id"])
        else:
            pick = max(legal, key=lambda r: r["projected_points"])
        drafted.add(pick["player_id"])
        rosters[slot][pick["position"]] += 1
    return owner_ids


def evaluate_roster(player_ids: list[str], eval_values: dict[str, dict], draft_values: dict[str, dict], profile: LeagueProfile) -> tuple[float, dict]:
    """starting_lineup_value uses the EVAL season's real outcomes (a
    player who retired/did not play that season correctly contributes
    zero real value -- a genuine real-world walk-forward property, not a
    bug). position counts use DRAFT-TIME position (draft_values) instead
    -- position-hoarding is a question about what was actually DRAFTED,
    not about which of those picks happened to still be active the
    following season."""
    players = [
        RosterPlayer(player_id=pid, position=eval_values[pid]["position"], value=eval_values[pid]["points"])
        for pid in player_ids if pid in eval_values
    ]
    report = roster_composition_report(players, profile)
    counts = Counter(draft_values[pid]["position"] for pid in player_ids if pid in draft_values)
    return report.starting_lineup_value, dict(counts)


def main() -> None:
    results = []
    print("=== FRESH WALK-FORWARD V1: REFERENCE vs CHALLENGER (real nflverse outcomes) ===\n")
    for draft_year, eval_year in SEASON_PAIRS:
        draft_values = _season_totals(draft_year)
        eval_values = _season_totals(eval_year)
        for slot in SLOTS:
            profile = build_profile(slot)
            ranking = build_ranking_from_draft_values(profile, draft_values)
            ref_ids = run_draft("reference", ranking, profile, slot)
            chal_ids = run_draft("challenger", ranking, profile, slot)
            ref_value, ref_counts = evaluate_roster(ref_ids, eval_values, draft_values, profile)
            chal_value, chal_counts = evaluate_roster(chal_ids, eval_values, draft_values, profile)
            delta = chal_value - ref_value
            max_pos_count_ref = max(ref_counts.values()) if ref_counts else 0
            max_pos_count_chal = max(chal_counts.values()) if chal_counts else 0
            results.append({
                "draft_year": draft_year, "eval_year": eval_year, "slot": slot,
                "ref_value": ref_value, "chal_value": chal_value, "delta": delta,
                "ref_counts": ref_counts, "chal_counts": chal_counts,
                "ref_hoard": max_pos_count_ref >= 7, "chal_hoard": max_pos_count_chal >= 7,
            })
            print(
                f"draft={draft_year}->eval={eval_year} slot={slot:2d}  "
                f"REF starting-lineup-value={ref_value:7.1f} {ref_counts}  "
                f"CHAL starting-lineup-value={chal_value:7.1f} {chal_counts}  delta={delta:+7.1f}"
            )

    n = len(results)
    mean_delta = sum(r["delta"] for r in results) / n
    wins = sum(1 for r in results if r["delta"] > 0)
    losses = sum(1 for r in results if r["delta"] < 0)
    ties = n - wins - losses
    ref_hoard_rate = sum(1 for r in results if r["ref_hoard"]) / n
    chal_hoard_rate = sum(1 for r in results if r["chal_hoard"]) / n
    print(f"\n=== SUMMARY (n={n} paired observations) ===")
    print(f"mean_delta (CHALLENGER - REFERENCE starting-lineup value) = {mean_delta:+.2f}")
    print(f"CHALLENGER wins={wins}  losses={losses}  ties={ties}")
    print(f"REFERENCE position-hoarding rate (max position count >=7): {ref_hoard_rate:.1%}")
    print(f"CHALLENGER position-hoarding rate (max position count >=7): {chal_hoard_rate:.1%}")
    # Per-season means for the "no season materially regresses" gate.
    print("\nPer draft-year mean delta:")
    for draft_year, eval_year in SEASON_PAIRS:
        sub = [r for r in results if r["draft_year"] == draft_year]
        print(f"  {draft_year}->{eval_year}: mean_delta={sum(r['delta'] for r in sub)/len(sub):+.2f}  ref_mean={sum(r['ref_value'] for r in sub)/len(sub):.1f}  chal_mean={sum(r['chal_value'] for r in sub)/len(sub):.1f}")


if __name__ == "__main__":
    main()
