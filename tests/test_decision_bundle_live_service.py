from src.services.decision_bundle_live_service import (
    LiveDecisionBundleUnavailable,
    build_live_decision_bundle,
)
from src.services.redraft_draft_room_v1_service import AdpSnapshot
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


def _ranking(team_count: int = 6, rounds: int = 8) -> RankingResult:
    rows = []
    for position, count in (("QB", 8), ("RB", 20), ("WR", 24), ("TE", 8)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank, index + 1, f"{position}-{index}", f"{position} {index}", position,
                    "TST", 400 - rank, 0, 400 - rank, 0,
                    "HIGH" if index < 5 else "MEDIUM", 1 + (rank - 1) // 10,
                    "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-08-17", False,
                    position_tier=1 + index // 6,
                )
            )
    profile = LeagueProfile(
        "fixture", "Fixture", 2026, team_count,
        RosterSettings(k=1, dst=1, bench_size=3),
        ScoringSettings(reception=1), DraftContext(rounds=rounds, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _manual_assets() -> list[dict[str, str]]:
    return [
        {"player_id": f"manual:{p}:{i}", "player_name": f"{p} {i}", "position": p, "team": f"T{i}"}
        for p in ("K", "DST")
        for i in range(6)
    ]


def _empty_adp(profile: LeagueProfile) -> AdpSnapshot:
    return AdpSnapshot(profile.profile_id, "", "ppr", profile.team_count, "", "", "", (), ())


def _provenance():
    return build_score_provenance(
        league_profile_hash="lp", roster_state_hash="rs", available_player_hash="ap",
        universe_hash="uh", projection_model_version="proj-v1", market_snapshot_hash="mk",
        feature_set_version="fs-v1", team_score_version="ts-v1",
        championship_equity_version="ce-v1", pick_score_version="ps-v1",
        optimizer_version="opt-v1", seed=7, simulation_count=10,
        timestamp_utc="2026-09-03T12:00:00Z",
    )


def _room_state(*, owner_slot=1, picks=()):
    picks = list(picks)
    return {
        "owner_slot": owner_slot,
        "drafted": [p["player_id"] for p in picks],
        "picks": picks,
    }


def test_build_live_decision_bundle_returns_a_real_bundle_for_a_fresh_draft() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=3
    )

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=3,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    assert len(result.candidates) == 5
    assert all(c.player_score is not None for c in result.candidates)


def test_build_live_decision_bundle_respects_already_drafted_players() -> None:
    # team_count=2 snake order is [1, 2, 2, 1, 1, 2, ...]: after ONE real
    # pick by team 1, pick #2 is genuinely team 2's turn -- owner_slot=2
    # keeps this test's "it's actually your turn" precondition real,
    # matching the same guard the live decision bundle enforces.
    ranking = _ranking(team_count=2)
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=5
    )

    picks = [
        {"player_id": "RB-0", "team_slot": 1, "position": "RB", "player_name": "RB 0"},
    ]
    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=2, picks=picks),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=5,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    ids = {c.player_id for c in result.candidates}
    assert "RB-0" not in ids


def test_build_live_decision_bundle_respects_position_maximum_legality() -> None:
    # roster.qb=1 -> _roster_candidate_allowed caps QB at max(1+1, 2)=2.
    # team_count=2 order is [1,2,2,1,1,2,...]: after 4 real picks
    # (team1, team2, team2, team1 -- the owner's 2 real QB picks land at
    # positions 1 and 4), pick #5 genuinely belongs to team 1 (owner)
    # again, so this stays a real "it's your turn" case, not a skipped one.
    ranking = _ranking(team_count=2)
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=9
    )

    picks = [
        {"player_id": "QB-0", "team_slot": 1, "position": "QB", "player_name": "QB 0"},
        {"player_id": "WR-0", "team_slot": 2, "position": "WR", "player_name": "WR 0"},
        {"player_id": "WR-1", "team_slot": 2, "position": "WR", "player_name": "WR 1"},
        {"player_id": "QB-1", "team_slot": 1, "position": "QB", "player_name": "QB 1"},
    ]
    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=1, picks=picks),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=40,
        trials=2, seasons=20, base_seed=9,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    positions = {c.player_id.split("-")[0] for c in result.candidates}
    assert "QB" not in positions  # already at the QB cap of 2


def test_build_live_decision_bundle_reports_unavailable_when_owner_slot_missing() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=1
    )

    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=None),
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=1,
    )
    assert isinstance(result, LiveDecisionBundleUnavailable)
    assert "Owner slot" in result.reason


def test_build_live_decision_bundle_reports_unavailable_when_ranking_not_ready() -> None:
    profile = _ranking().profile
    unready = RankingResult(
        profile, (), (), (), "2026-08-17T00:00:00+00:00", "fixture", errors=("blocked",)
    )
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)

    result = build_live_decision_bundle(
        profile, unready, manual_assets, adp, _room_state(),
        comparable_leagues=[], provenance=_provenance(),
    )
    assert isinstance(result, LiveDecisionBundleUnavailable)
    assert "not ready" in result.reason


def test_build_live_decision_bundle_continues_the_real_room_not_an_empty_draft() -> None:
    """Regression: the look-ahead simulation (evaluate_pick_candidates ->
    simulate_pick_now) must continue from the REAL current room state, not
    silently restart an empty draft -- otherwise it can force a candidate
    that its own from-scratch simulation independently already "drafted"
    for another team, crashing with 'already drafted'. Reproduced here with
    a room that already has OTHER teams' real picks recorded (the exact
    shape that surfaced the bug in facade-level testing)."""
    ranking = _ranking(team_count=4)
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=11
    )
    # Owner drafts LAST in round 1 (slot 4), and the REAL room recorded
    # teams 1-3 making picks that DIVERGE from what a from-scratch
    # simulation's own deterministic-fallback CPU logic would independently
    # choose (e.g. team 1 taking a low-ranked player instead of the real
    # best-available QB-0) -- exactly the shape that reproduced the bug in
    # facade-level testing: without the real from_state, the simulation's
    # own from-empty CPU picks can collide with a candidate this function
    # legitimately selected from the REAL available pool.
    picks = [
        {"player_id": "TE-7", "team_slot": 1, "position": "TE", "player_name": "TE 7"},
        {"player_id": "WR-9", "team_slot": 2, "position": "WR", "player_name": "WR 9"},
        {"player_id": "RB-9", "team_slot": 3, "position": "RB", "player_name": "RB 9"},
    ]
    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=4, picks=picks),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=11,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    candidate_ids = {c.player_id for c in result.candidates}
    # Already-drafted players (by other teams) must never appear, and the
    # call must not raise -- proves the simulation is aware of the REAL
    # room's actual history, not an independently re-simulated one.
    assert candidate_ids.isdisjoint({"TE-7", "WR-9", "RB-9"})
    assert "QB-0" in candidate_ids  # the real best-available player, untouched
