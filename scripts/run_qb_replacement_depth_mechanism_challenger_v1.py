"""QB replacement-depth CHALLENGER -- mechanism-only proof (section 13 follow-up).

Extends docs/codex/QB_MARGINAL_VALUE_CHALLENGER_STATUS_20260903.md, which
explains why a *real, backtested* QB replacement-baseline challenger cannot
be built this pass (it needs real per-QB projected-points magnitude from the
still-expired governed 2026 projection snapshot). This script builds the
narrower thing that IS honest to build without that data: it calls the
REAL, unmodified `calculate_replacement_levels()` production function twice
-- once with the CHAMPION's configured QB depth (roster_limits.QB=2, the
real KHA/default config) and once with a CHALLENGER's shallower depth
(roster_limits.QB=1, matching the starter-count-aware baseline the audit
found already exists elsewhere in the codebase,
`model_v4_replacement_vorp_core_service.py`'s `configured_replacement_rank`)
-- against a CLEARLY SYNTHETIC, disclosed QB points ladder, to mechanically
prove the fix direction: a shallower configured QB depth lowers replacement
points, which raises value-over-replacement for every real starter-caliber
QB. No production code is modified. No real projection data is used or
implied to be used -- every point value here is a disclosed synthetic
ladder, not a claim about any real player's real fantasy output.

This is NOT a backtest against real outcomes and is NOT registered as a
promotable challenger. It is evidence that the mechanism the audit
identified behaves the way the audit predicts, ready to be re-run against
real projection data the moment that data is lawfully available again.
"""
from __future__ import annotations

import csv
from pathlib import Path

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    ProjectionPlayer,
    ReplacementLevel,
    RosterSettings,
    ScoringSettings,
    calculate_replacement_levels,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_CSV = REPO_ROOT / "docs" / "codex" / "QB_REPLACEMENT_DEPTH_MECHANISM_CHALLENGER.csv"

# Disclosed synthetic QB points ladder (NOT real projection data): 40 QBs,
# descending by a flat 5-point step, deliberately smooth so the mechanism
# being demonstrated -- not a coincidence in the ladder's shape -- drives
# every observed difference between CHAMPION and CHALLENGER.
SYNTHETIC_QB_COUNT = 40
SYNTHETIC_QB_TOP_POINTS = 380.0
SYNTHETIC_QB_STEP = 5.0

# Deliberately isolated roster shape: QB-only starters/bench, zero required
# RB/WR/TE/K/DST, so the demonstration is not diluted by any other
# position's replacement math. Not a realistic league configuration --
# disclosed here, not silently assumed.
ISOLATED_ROSTER = RosterSettings(
    qb=1, rb=0, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=6
)
TEAM_COUNT = 16  # matches the real KHA room's team count


def synthetic_qb_pool() -> tuple[tuple[ProjectionPlayer, float], ...]:
    rows = []
    for i in range(SYNTHETIC_QB_COUNT):
        points = SYNTHETIC_QB_TOP_POINTS - SYNTHETIC_QB_STEP * i
        player = ProjectionPlayer(
            player_id=f"synthetic-qb-{i + 1:02d}",
            player_name=f"Synthetic QB {i + 1:02d}",
            position="QB",
            team="SYN",
            season=2026,
            source_status="SYNTHETIC_FIXTURE",
            evidence_status="DISCLOSED_SYNTHETIC_NOT_REAL",
        )
        rows.append((player, points))
    return tuple(rows)


def build_profile(*, profile_id: str, qb_roster_limit: int | None) -> LeagueProfile:
    roster_limits = {"QB": qb_roster_limit} if qb_roster_limit is not None else {}
    return LeagueProfile(
        profile_id=profile_id,
        league_name="QB Replacement Depth Mechanism Fixture",
        season=2026,
        team_count=TEAM_COUNT,
        roster=ISOLATED_ROSTER,
        scoring=ScoringSettings(),
        draft=DraftContext(roster_limits=roster_limits, replacement_method="expected_available"),
    )


def run() -> tuple[ReplacementLevel, ReplacementLevel, tuple[dict[str, object], ...]]:
    pool = synthetic_qb_pool()
    champion_profile = build_profile(profile_id="champion-qb-depth-2", qb_roster_limit=2)
    challenger_profile = build_profile(profile_id="challenger-qb-depth-1", qb_roster_limit=1)

    champion_levels = calculate_replacement_levels(champion_profile, pool)
    challenger_levels = calculate_replacement_levels(challenger_profile, pool)
    champion_qb = next(level for level in champion_levels if level.position == "QB")
    challenger_qb = next(level for level in challenger_levels if level.position == "QB")

    rows = []
    for player, points in pool:
        champion_vor = round(points - champion_qb.replacement_points, 4)
        challenger_vor = round(points - challenger_qb.replacement_points, 4)
        rows.append(
            {
                "player_id": player.player_id,
                "points_synthetic": points,
                "champion_replacement_points": champion_qb.replacement_points,
                "champion_vor": champion_vor,
                "challenger_replacement_points": challenger_qb.replacement_points,
                "challenger_vor": challenger_vor,
                "vor_delta_challenger_minus_champion": round(challenger_vor - champion_vor, 4),
            }
        )
    return champion_qb, challenger_qb, tuple(rows)


def main() -> None:
    champion_qb, challenger_qb, rows = run()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"CHAMPION  (roster_limits.QB=2 -> depth {TEAM_COUNT * 2}): "
        f"rostered={champion_qb.rostered_count} "
        f"replacement_points={champion_qb.replacement_points}"
    )
    print(
        f"CHALLENGER (roster_limits.QB=1 -> depth {TEAM_COUNT * 1}): "
        f"rostered={challenger_qb.rostered_count} "
        f"replacement_points={challenger_qb.replacement_points}"
    )
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
