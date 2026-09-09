"""Strategic QB-hoarding replay with `roster_limits` deliberately UNCONFIGURED.

NWR Overnight V3 retry-queue follow-up (mission section 6): proves that the
canonical legality service's deliberate refusal to invent a hard QB/TE
maximum (see `redraft_roster_legality_service.py`'s own docstring) does not
turn into a real QB-hoarding pathology in practice, because the real,
promoted, live production ordering signal -- `marginal_roster_utility()`
(the same function `decision_bundle_service._candidate_sort_key` uses as its
PRIMARY sort key, see `NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md`) --
independently suppresses a 3rd+ bench QB in every 1QB league shape, using
only real, already-governed mechanics (starter-lineup displacement value +
measured bench-redundancy decay), with NO hard legal cap ever engaged.

This is a full simulated snake draft for every team (not just the owner),
using `evaluate_draft_pick_legality` as the ONLY legality gate (roster_limits
is an empty mapping -- explicitly UNKNOWN, never a fabricated platform
maximum) and `marginal_roster_utility()` as the ONLY selection signal (argmax
per legal candidate at each pick, ties broken by declared value then
player_id for determinism). This intentionally exercises the real PRIMARY
sort key directly rather than the full Monte Carlo DecisionBundle (pick_score/
cost_of_waiting/championship_equity), which are unchanged tie-breaks below
marginal_utility and are not needed to answer the question this test asks.

K/DST are represented as manual, unmodeled assets with declared value 0.0
(matching real production -- NWR has no K/DST model), so they are drafted
only when the mandatory-slot-feasibility legality gate forces them near the
end of the draft -- the same real mechanism Test 18 exercises.
"""

from __future__ import annotations

from collections import Counter

import pytest

from src.services.redraft_draft_room_v1_service import _asset_pool
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from src.services.shadow_numeric_authorities_service import marginal_roster_utility

_POSITION_POOL_SIZES = {"QB": 40, "RB": 90, "WR": 110, "TE": 40}
_MANUAL_POOL_SIZE = 40  # K and DST each


def _synthetic_ranking(*, rounds: int, superflex: int) -> RankingResult:
    rows: list[RedraftRankingRow] = []
    for position, count in _POSITION_POOL_SIZES.items():
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    overall_rank=rank,
                    position_rank=index + 1,
                    player_id=f"{position}-{index:03d}",
                    player_name=f"{position} Synthetic {index}",
                    position=position,
                    team="TST",
                    projected_points=400 - rank,
                    replacement_points=0,
                    replacement_adjusted_value=400 - rank,
                    starter_gap=0,
                    confidence="HIGH",
                    tier=1,
                    profile_id="fixture",
                    profile_name="Fixture",
                    source_status="GOVERNED",
                    evidence_status="AVAILABLE",
                    source_as_of="2026-09-09",
                    rookie=False,
                )
            )
    roster = RosterSettings(
        qb=1, rb=2, wr=2, te=1, flex=1, superflex=superflex, k=1, dst=1, bench_size=6,
    )
    profile = LeagueProfile(
        profile_id="fixture-qb-hoarding",
        league_name="Fixture QB Hoarding League",
        season=2026,
        team_count=10,  # overwritten per-shape by the caller via replace()
        roster=roster,
        scoring=ScoringSettings(reception=1.0),
        # roster_limits deliberately left as the DraftContext default (empty
        # dict) -- this is the UNKNOWN/unconfigured representation, never a
        # fabricated platform maximum.
        draft=DraftContext(rounds=rounds),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-09-09T00:00:00+00:00", "fixture")


def _manual_assets() -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    for position in ("K", "DST"):
        for index in range(_MANUAL_POOL_SIZE):
            assets.append(
                {
                    "player_id": f"{position}-{index:03d}",
                    "player_name": f"{position} Synthetic {index}",
                    "position": position,
                    "team": "TST",
                }
            )
    return assets


def _snake_order(team_count: int, round_number: int) -> range:
    return range(1, team_count + 1) if round_number % 2 else range(team_count, 0, -1)


def _run_draft(*, team_count: int, superflex: int) -> dict[int, Counter[str]]:
    roster = RosterSettings(
        qb=1, rb=2, wr=2, te=1, flex=1, superflex=superflex, k=1, dst=1, bench_size=6,
    )
    rounds = roster.qb + roster.rb + roster.wr + roster.te + roster.flex + roster.superflex + roster.k + roster.dst + roster.bench_size
    ranking = _synthetic_ranking(rounds=rounds, superflex=superflex)
    profile = LeagueProfile(
        profile_id=f"fixture-qb-hoarding-{team_count}-{'sflx' if superflex else '1qb'}",
        league_name=f"Fixture {team_count}-team {'Superflex' if superflex else '1QB'}",
        season=2026,
        team_count=team_count,
        roster=roster,
        scoring=ScoringSettings(reception=1.0),
        draft=DraftContext(rounds=rounds),  # roster_limits UNCONFIGURED (empty)
    )
    assert profile.draft.roster_limits == {}, "This test requires UNCONFIGURED roster_limits."

    manual_assets = _manual_assets()
    pool = _asset_pool(ranking, manual_assets)
    required_slots = team_count * rounds
    assert len(pool) >= required_slots, (
        f"Synthetic pool ({len(pool)}) too small for {team_count} teams x {rounds} rounds "
        f"({required_slots} picks)."
    )

    rosters: dict[int, Counter[str]] = {slot: Counter() for slot in range(1, team_count + 1)}
    roster_player_ids: dict[int, list[str]] = {slot: [] for slot in range(1, team_count + 1)}
    drafted: set[str] = set()

    for round_number in range(1, rounds + 1):
        for slot in _snake_order(team_count, round_number):
            counts = rosters[slot]
            legal_candidates = [
                asset["player_id"]
                for player_id, asset in pool.items()
                if player_id not in drafted
                and evaluate_draft_pick_legality(profile, counts, asset["position"]).allowed
            ]
            assert legal_candidates, (
                f"No legal candidate available for team {slot} in round {round_number} -- "
                "a feasible profile should never run dry before its roster is full."
            )
            current_ids = roster_player_ids[slot]
            scored = [
                (
                    marginal_roster_utility(pid, current_ids, profile, ranking, manual_assets).utility,
                    pool[pid]["replacement_adjusted_value"] or 0.0,
                    pid,
                )
                for pid in legal_candidates
            ]
            # PRIMARY key = marginal_utility, matching the real production
            # `_candidate_sort_key` (decision_bundle_service.py). Ties broken
            # by declared value then player_id purely for determinism -- this
            # test never needs the Monte Carlo pick_score/cost_of_waiting
            # tie-breaks, since marginal_utility is what item 6 is about.
            scored.sort(key=lambda row: (-row[0], -row[1], row[2]))
            pick_id = scored[0][2]
            drafted.add(pick_id)
            position = pool[pick_id]["position"]
            counts[position] += 1
            roster_player_ids[slot].append(pick_id)

    return rosters


@pytest.mark.parametrize(
    "team_count,superflex",
    [(8, 0), (10, 0), (12, 0), (16, 0), (12, 1)],
    ids=["8_team_1qb", "10_team_1qb", "12_team_1qb", "16_team_1qb", "12_team_superflex"],
)
def test_no_qb_hoarding_pathology_with_unconfigured_roster_limits(team_count: int, superflex: int) -> None:
    rosters = _run_draft(team_count=team_count, superflex=superflex)
    qb_counts = {slot: counts["QB"] for slot, counts in rosters.items()}

    # Hard-legality sanity: with roster_limits UNCONFIGURED, QB has no
    # invented ceiling here either -- this test's job is to show the
    # STRATEGIC signal alone keeps counts sane, not that legality forbids
    # more (that would defeat the point of the test).
    max_legal_qb_seen = max(qb_counts.values())
    threshold = 3 if not superflex else 4
    assert max_legal_qb_seen <= threshold, (
        f"Strategic marginal_utility ordering alone produced pathological QB hoarding "
        f"(max {max_legal_qb_seen} QBs on one roster, team_count={team_count}, "
        f"superflex={bool(superflex)}) with roster_limits left UNCONFIGURED: {qb_counts}"
    )
    # Record actual counts for the handoff report (see stdout when run with -s).
    print(
        f"\n[QB_HOARDING team_count={team_count} superflex={bool(superflex)}] "
        f"QB counts per team: {dict(sorted(qb_counts.items()))}"
    )
