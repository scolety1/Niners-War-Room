from src.services.decision_bundle_live_service import LiveDecisionBundleUnavailable
from src.services.decision_bundle_live_service_v2 import build_live_decision_bundle_v2
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


def _ranking(team_count: int = 8) -> RankingResult:
    rows = []
    for position, count in (("QB", 20), ("RB", 60), ("WR", 60), ("TE", 20)):
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
        "fixture", "Fixture", 2026, team_count, RosterSettings(bench_size=5),
        ScoringSettings(reception=0.0), DraftContext(rounds=6, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _empty_adp(profile: LeagueProfile) -> AdpSnapshot:
    return AdpSnapshot(profile.profile_id, "", "standard", profile.team_count, "", "", "", (), ())


def _provenance():
    return build_score_provenance(
        league_profile_hash="lp", roster_state_hash="rs", available_player_hash="ap",
        universe_hash="uh", projection_model_version="proj-v1", market_snapshot_hash="mk",
        feature_set_version="fs-v1", team_score_version="ts-v1",
        championship_equity_version="ce-v1", pick_score_version="ps-v1",
        optimizer_version="opt-v1", seed=7, simulation_count=10,
        timestamp_utc="2026-09-06T00:00:00Z",
    )


def _room_state(*, owner_slot=1, picks=()):
    picks = list(picks)
    return {
        "owner_slot": owner_slot,
        "drafted": [p["player_id"] for p in picks],
        "picks": picks,
    }


def test_build_live_decision_bundle_v2_returns_a_real_challenger_bundle() -> None:
    ranking = _ranking(team_count=8)
    profile = ranking.profile
    manual_assets: list[dict[str, str]] = []
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=3
    )

    result = build_live_decision_bundle_v2(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=3,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    assert result.v2_status == "OK"
    assert len(result.candidates) == 5
    assert result.current_team_score_v2 is not None
    # The underlying live V1 bundle is present and unaffected.
    assert len(result.v1_bundle.candidates) == 5


def test_build_live_decision_bundle_v2_reports_unavailable_when_owner_slot_missing() -> None:
    ranking = _ranking(team_count=8)
    profile = ranking.profile
    manual_assets: list[dict[str, str]] = []
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=1
    )

    result = build_live_decision_bundle_v2(
        profile, ranking, manual_assets, adp, _room_state(owner_slot=None),
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=1,
    )
    assert isinstance(result, LiveDecisionBundleUnavailable)
    assert "Owner slot" in result.reason


def test_build_live_decision_bundle_v2_degrades_gracefully_for_unsupported_team_count() -> None:
    # team_count=6 is real and legal for the live Draft Room, but outside
    # Team Score V2 / Championship Equity V2's validated set -- the
    # CHALLENGER layer must degrade honestly, never crash, and the V1
    # bundle underneath must remain fully populated.
    ranking = _ranking(team_count=6)
    profile = ranking.profile
    manual_assets: list[dict[str, str]] = []
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=13
    )

    result = build_live_decision_bundle_v2(
        profile, ranking, manual_assets, adp, _room_state(),
        comparable_leagues=leagues, provenance=_provenance(), max_candidates=5,
        trials=2, seasons=20, base_seed=13,
    )
    assert not isinstance(result, LiveDecisionBundleUnavailable)
    assert result.v2_status.startswith("DEGRADED")
    assert len(result.v1_bundle.candidates) == 5
