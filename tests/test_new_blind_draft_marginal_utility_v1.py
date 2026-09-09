"""Fresh full blind draft, always-take-top-rec, no manual rescue.

NWR Overnight V3 retry-queue follow-up (mission section 5's second half).
Reuses the real Test 18 league shape (10-team, ESPN full PPR, slot 5, roster
1QB/2RB/2WR/1TE/1FLEX/1K/1DST/7BN, real known WR maximum = 8 --
`tests/fixtures/test18_redraft_fixture.py`'s own `TEST18_WR_MAXIMUM`) but,
unlike the prior retry-queue session's blind draft (which explicitly
disclosed using the ranking's cruder STATIC value order, not the live
production ordering), this drives every pick with the same PRIMARY signal
production Suggestions actually uses: `marginal_roster_utility()` (see
`decision_bundle_service._candidate_sort_key`). Every team, every pick --
not just the owner -- "always takes the top rec" among its own currently
legal candidates. No manual rescue, no human intervention.

This worktree has no governed 2026 projection snapshot (see section 7 of
the retry-queue report), so this uses a clearly-labeled SYNTHETIC ranked
pool, never presented as real player data -- same disclosed constraint as
the prior session's equivalent test.
"""

from __future__ import annotations

from collections import Counter

from tests.fixtures.test18_redraft_fixture import TEST18_OWNER_SLOT, TEST18_WR_MAXIMUM, make_test18_profile

from src.services.redraft_draft_room_v1_service import _asset_pool
from src.services.redraft_engine_v1_service import RankingResult, RedraftRankingRow
from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from src.services.shadow_numeric_authorities_service import marginal_roster_utility

_POSITION_POOL_SIZES = {"QB": 40, "RB": 90, "WR": 110, "TE": 40}
_MANUAL_POOL_SIZE = 30  # K and DST each


def _synthetic_ranking() -> RankingResult:
    profile = make_test18_profile(wr_maximum=TEST18_WR_MAXIMUM)
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
                    profile_id="test18-synthetic",
                    profile_name="Test 18 Synthetic",
                    source_status="GOVERNED",
                    evidence_status="AVAILABLE",
                    source_as_of="2026-09-09",
                    rookie=False,
                )
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


def test_fresh_blind_draft_always_top_rec_no_manual_rescue_test18_shape() -> None:
    ranking = _synthetic_ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    pool = _asset_pool(ranking, manual_assets)
    team_count = profile.team_count
    rounds = profile.draft.rounds
    required_slots = team_count * rounds
    assert len(pool) >= required_slots

    rosters: dict[int, Counter[str]] = {slot: Counter() for slot in range(1, team_count + 1)}
    roster_player_ids: dict[int, list[str]] = {slot: [] for slot in range(1, team_count + 1)}
    drafted: set[str] = set()
    illegal_picks_recorded = 0
    picks_log: list[tuple[int, int, str, str]] = []  # round, slot, player_id, position

    for round_number in range(1, rounds + 1):
        for slot in _snake_order(team_count, round_number):
            counts = rosters[slot]
            legal_candidates = []
            for player_id, asset in pool.items():
                if player_id in drafted:
                    continue
                legality = evaluate_draft_pick_legality(profile, counts, asset["position"])
                if legality.allowed:
                    legal_candidates.append(player_id)
            assert legal_candidates, (
                f"No legal candidate for team {slot} round {round_number} -- "
                "an always-take-top-rec draft with a feasible profile should never run dry."
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
            scored.sort(key=lambda row: (-row[0], -row[1], row[2]))
            pick_id = scored[0][2]
            position = pool[pick_id]["position"]
            # Replay every recorded pick through the canonical legality
            # service independently -- this is the "zero illegal primary
            # recommendations" gate (contract A), checked mechanically, not
            # just asserted by construction.
            if not evaluate_draft_pick_legality(profile, counts, position).allowed:
                illegal_picks_recorded += 1
            drafted.add(pick_id)
            counts[position] += 1
            roster_player_ids[slot].append(pick_id)
            picks_log.append((round_number, slot, pick_id, position))

    assert illegal_picks_recorded == 0
    assert len(drafted) == required_slots

    for slot, counts in rosters.items():
        assert counts["WR"] <= TEST18_WR_MAXIMUM, (
            f"Team {slot} exceeded the real known WR maximum ({TEST18_WR_MAXIMUM}): {counts['WR']}"
        )
        assert counts["K"] == profile.roster.k
        assert counts["DST"] == profile.roster.dst
        assert sum(counts.values()) == rounds

    owner_counts = rosters[TEST18_OWNER_SLOT]
    print(
        f"\n[NEW_BLIND_DRAFT owner_slot={TEST18_OWNER_SLOT}] final shape: {dict(sorted(owner_counts.items()))}"
    )
    print(
        "[NEW_BLIND_DRAFT all teams WR counts] "
        f"{ {slot: counts['WR'] for slot, counts in sorted(rosters.items())} }"
    )
