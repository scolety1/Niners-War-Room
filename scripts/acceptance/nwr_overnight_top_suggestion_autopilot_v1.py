"""Real top-suggestion-autopilot acceptance test (NWR Overnight, Section 9).

Repeatedly takes the FIRST candidate the real, production
`decision_bundle_live_service.build_live_decision_bundle` returns for the
owner's own turn -- the exact same function the live Suggestions table
calls -- no separate re-implementation of "what the algorithm would pick."
Every other team uses the existing, already-tested CPU `_select_asset`
path. Uses an isolated, synthetic-but-realistic ranking so this never
touches any real saved profile or persisted state.

This is the script that found the real K/DST-never-selected defect the
forced-position-restriction fix in decision_bundle_live_service.py
addresses (see that module's own "NWR OVERNIGHT" comments) -- kept here as
reusable acceptance-matrix tooling, not a one-off throwaway.

Run: python scripts/acceptance/nwr_overnight_top_suggestion_autopilot_v1.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.services.decision_bundle_live_service import (
    LiveDecisionBundleUnavailable,
    build_live_decision_bundle,
)
from src.services.redraft_draft_room_v1_service import (
    AdpSnapshot,
    _asset_pool,
    _complete,
    _current_team,
    _record_pick,
    _select_asset,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import simulate_comparable_leagues


def build_ranking(team_count: int, rounds: int) -> RankingResult:
    rows = []
    rank = 0
    # Real, position-value-realistic ordering this time: value strictly
    # decreases within EACH position's own tier, but positions interleave
    # by realistic overall value rather than being grouped block-by-block
    # (the earlier synthetic-fixture flaw this run corrects).
    tiers = [
        ("RB", 20, 340), ("WR", 24, 335), ("RB", 20, 300), ("WR", 24, 295),
        ("TE", 12, 270), ("QB", 20, 350), ("RB", 28, 220), ("WR", 34, 215),
        ("TE", 28, 150), ("QB", 28, 200),
    ]
    seen_by_pos: dict[str, int] = {}
    for position, count, base_value in tiers:
        for _ in range(count):
            rank += 1
            idx = seen_by_pos.get(position, 0)
            seen_by_pos[position] = idx + 1
            value = max(2.0, base_value - idx * 4)
            rows.append(
                RedraftRankingRow(
                    rank, seen_by_pos[position], f"{position}-{rank}",
                    f"{position} Player {rank}", position, "TST",
                    value, 0, value, 0,
                    "HIGH" if idx < 5 else "MEDIUM", 1 + idx // 8,
                    "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-08-08", False,
                )
            )
    profile = LeagueProfile(
        "fixture", "Fixture", 2026, team_count,
        RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1, bench_size=6),
        ScoringSettings(reception=0.5), DraftContext(rounds=rounds, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-08T00:00:00Z", "fixture")


def manual_assets_for(team_count: int) -> list[dict]:
    out = []
    for i in range(max(12, team_count + 2)):
        out.append({"player_id": f"manual:K:{i}", "player_name": f"Kicker {i}", "position": "K", "team": f"T{i}"})
        out.append({"player_id": f"manual:DST:{i}", "player_name": f"Defense {i}", "position": "DST", "team": f"T{i}"})
    return out


def run_autopilot(team_count: int, owner_slot: int, seed: int) -> dict:
    profile_base = build_ranking(team_count, team_count == 10 and 16 or 15).profile
    ranking = build_ranking(team_count, profile_base.draft.rounds)
    profile = ranking.profile
    manual_assets = manual_assets_for(team_count)
    adp = AdpSnapshot(profile.profile_id, "", "half-ppr", team_count, "", "", "", (), ())
    pool = _asset_pool(ranking, manual_assets)
    leagues = simulate_comparable_leagues(profile, ranking, manual_assets, adp, trials=3, base_seed=seed)
    provenance = build_score_provenance(
        league_profile_hash="h1", roster_state_hash="h2", available_player_hash="h3",
        universe_hash="h4", projection_model_version="v1", market_snapshot_hash="h5",
        feature_set_version="fs1", team_score_version="ts1", championship_equity_version="ce1",
        pick_score_version="ps1", optimizer_version="opt1", seed=seed, simulation_count=3,
        timestamp_utc="2026-09-07T00:00:00Z",
    )
    state: dict = {
        "schema_version": 1, "profile_id": profile.profile_id, "owner_slot": owner_slot,
        "seed": seed, "speed": "FAST", "mode": "MOCK", "drafted": [], "picks": [], "updated_at_utc": "",
    }
    owner_picks = []
    unavailable_reasons = []
    while not _complete(profile, state):
        team_slot = _current_team(profile, state)
        if team_slot == owner_slot:
            result = build_live_decision_bundle(
                profile, ranking, manual_assets, adp, state,
                comparable_leagues=leagues, provenance=provenance,
                max_candidates=8, trials=3, seasons=30, base_seed=seed,
                continuation_seeds=1,  # keep this acceptance run fast; correctness already proven separately
            )
            if isinstance(result, LiveDecisionBundleUnavailable):
                unavailable_reasons.append((len(state["picks"]) + 1, result.reason))
                # Fall back to the same real CPU legality-respecting selector
                # -- an explicit, disclosed fallback, never a silent skip.
                asset, behavior = _select_asset(profile, ranking, adp, state, pool, team_slot, "CPU")
            else:
                top = result.candidates[0]
                asset = pool[top.player_id]
                behavior = "TOP_SUGGESTION_AUTOPILOT"
                owner_picks.append((top.player_id, asset.get("position"), top.pick_score))
            state = _record_pick(profile, state, asset, actor="OWNER_AUTO_TEST", behavior=behavior)
        else:
            asset, behavior = _select_asset(profile, ranking, adp, state, pool, team_slot, "CPU")
            state = _record_pick(profile, state, asset, actor="CPU", behavior=behavior)

    my_roster = [p for p in state["picks"] if p["team_slot"] == owner_slot]
    from collections import Counter
    counts = Counter(p["position"] for p in my_roster)
    player_ids = [p["player_id"] for p in my_roster]
    duplicates = len(player_ids) != len(set(player_ids))
    return {
        "team_count": team_count, "owner_slot": owner_slot, "seed": seed,
        "total_picks": len(my_roster), "counts": dict(counts),
        "k_filled": counts.get("K", 0) >= profile.roster.k,
        "dst_filled": counts.get("DST", 0) >= profile.roster.dst,
        "duplicates": duplicates,
        "unavailable_count": len(unavailable_reasons),
        "unavailable_sample": unavailable_reasons[:3],
        "owner_pick_count_via_autopilot": len(owner_picks),
        "rounds": profile.draft.rounds,
    }


if __name__ == "__main__":
    import json

    cases = [
        (10, 9, 20260907),   # the explicit owner-required ten-team slot-9 case
        (10, 1, 20260907),
        (8, 4, 20260907),
        (12, 6, 20260907),
        (16, 1, 20260907),
        (16, 16, 20260907),
        (10, 9, 4242),  # a second seed at the explicit required slot-9 case
    ]
    results = []
    for team_count, slot, seed in cases:
        r = run_autopilot(team_count, slot, seed)
        results.append(r)
        print(json.dumps(r, indent=2))
