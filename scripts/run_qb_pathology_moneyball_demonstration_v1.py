"""QB pathology / Moneyball demonstration (section 13). Entirely SHADOW/
RESEARCH -- exercises the real shadow_numeric_authorities_service.py
functions against a synthetic benchmarking fixture (same shape used
throughout this repo's shadow-authorities tests), never real player
evidence.

Shows, with real computed numbers, on the CURRENT roster (not a
completed draft -- see the note below on why): once the owner already
has a starting QB in a 1QB league, adding a 2nd, individually
higher-Player-Score QB provides ZERO incremental starting-lineup value
(it is purely a bench player), while a comparably-ranked RB/WR/TE adds
real value (it fills a real starter slot) -- even though the QB's own
Player Score (replacement_adjusted_value) is HIGHER. This is the
Moneyball principle: an individually excellent player can be a poor
*current action*. The same comparison in a Superflex league inverts:
the 2nd QB now fills the SUPERFLEX slot and its value is fully counted.

Methodology note: an earlier draft of this demonstration used the full
look-ahead pipeline (evaluate_pick_candidates -> simulate_pick_now,
completing the rest of the draft after each forced candidate). That
diluted the effect being demonstrated -- with ~14 remaining rounds of
CPU-driven owner picks auto-filling roster gaps regardless of this one
pick, the two forced choices converged to similar final rosters. This
version isolates the actual question ("what does adding THIS ONE
player do to my CURRENT starting lineup") the same way the Team Score V2
benchmark's qb_heavy_1qb scenario already did (see
docs/codex/SHADOW_NUMERIC_AUTHORITIES_BENCHMARK_20260903.md) rather than
routing through the full-draft-completion machinery, which is the right
tool for "which of these should I pick right now, accounting for what
happens after" but not for isolating one pick's own marginal impact.

Run: python -m scripts.run_qb_pathology_moneyball_demonstration_v1
"""

from __future__ import annotations

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
    roster_composition_report,
    simulate_comparable_leagues,
    team_score,
)


def build_ranking(roster: RosterSettings, team_count: int = 12, rounds: int = 15) -> RankingResult:
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
        "fixture", "Fixture", 2026, team_count, roster,
        ScoringSettings(reception=1), DraftContext(rounds=rounds, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def manual_assets() -> list[dict[str, str]]:
    return [
        {"player_id": f"manual:{p}:{i}", "player_name": f"{p} {i}", "position": p, "team": f"T{i}"}
        for p in ("K", "DST")
        for i in range(12)
    ]


def run_scenario(label: str, roster: RosterSettings) -> None:
    ranking = build_ranking(roster)
    profile = ranking.profile
    assets = manual_assets()
    pool = _asset_pool(ranking, assets)
    adp = AdpSnapshot(profile.profile_id, "", "ppr", profile.team_count, "", "", "", (), ())
    leagues = simulate_comparable_leagues(
        profile, ranking, assets, adp, trials=30, base_seed=20260903
    )

    def roster_players(ids: list[str]) -> list[RosterPlayer]:
        return [
            RosterPlayer(
                pid, pool[pid]["position"], float(pool[pid]["replacement_adjusted_value"] or 0.0)
            )
            for pid in ids
        ]

    # Owner's roster so far, minus the pick under test.
    base_ids = ["QB-0", "RB-4", "RB-5", "WR-4", "WR-5", "TE-4"]
    value_by_id = {row.player_id: row.replacement_adjusted_value for row in ranking.rows}

    print(f"\n=== {label} ===")
    print(f"{'candidate':<8}{'player_score':>14}{'team_score_after':>18}{'starting_lineup_delta':>24}")
    baseline = team_score(base_ids, profile, ranking, assets, comparable_leagues=leagues)
    baseline_report = roster_composition_report(roster_players(base_ids), profile)
    for candidate in ("QB-18", "RB-6"):
        candidate_ids = [*base_ids, candidate]
        score = team_score(candidate_ids, profile, ranking, assets, comparable_leagues=leagues)
        report = roster_composition_report(roster_players(candidate_ids), profile)
        delta = report.starting_lineup_value - baseline_report.starting_lineup_value
        print(
            f"{candidate:<8}{value_by_id[candidate]:>14.1f}{score.percentile:>18.1f}{delta:>24.1f}"
        )
    print(
        "(baseline before this pick: "
        f"starting_lineup_value={baseline_report.starting_lineup_value:.1f}, "
        f"team_score percentile={baseline.percentile:.1f})"
    )


def main() -> None:
    one_qb = RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=6)
    superflex = RosterSettings(
        qb=1, rb=2, wr=2, te=1, flex=1, superflex=1, k=1, dst=1, bench_size=6
    )
    run_scenario("1QB league (candidate: QB-18 vs RB-6, owner already has QB-0)", one_qb)
    run_scenario(
        "Superflex league (SAME candidates: QB-18 vs RB-6, owner already has QB-0)", superflex
    )


if __name__ == "__main__":
    main()
