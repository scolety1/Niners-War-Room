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
    ranking = _ranking()
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
        profile, ranking, manual_assets, adp, _room_state(picks=picks),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=5,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    ids = {c.player_id for c in result.candidates}
    assert "RB-0" not in ids


def test_build_live_decision_bundle_respects_position_maximum_legality() -> None:
    ranking = _ranking()
    profile = ranking.profile  # roster.qb=1 -> _roster_candidate_allowed caps QB at max(1+1,2)=2
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=9
    )

    picks = [
        {"player_id": "QB-0", "team_slot": 1, "position": "QB", "player_name": "QB 0"},
        {"player_id": "QB-1", "team_slot": 1, "position": "QB", "player_name": "QB 1"},
    ]
    result = build_live_decision_bundle(
        profile, ranking, manual_assets, adp, _room_state(picks=picks),
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
