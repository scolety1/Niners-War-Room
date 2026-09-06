import src.services.decision_bundle_service_v2 as bundle_v2
from src.services.decision_bundle_service_v2 import (
    DECISION_BUNDLE_V2_VERSION,
    adp_percentile_by_player,
    build_decision_bundle_v2,
    roster_matches_historical_shape,
    scoring_format_label,
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


def _ranking(team_count: int, roster: RosterSettings) -> RankingResult:
    rows = []
    # Comfortably larger than any team_count (<=16) x rounds (<=6) used
    # below, so `simulate_comparable_leagues`'s full mock drafts never
    # exhaust the pool.
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
        "fixture", "Fixture", 2026, team_count, roster,
        ScoringSettings(reception=0.0), DraftContext(rounds=6, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _provenance():
    return build_score_provenance(
        league_profile_hash="lp", roster_state_hash="rs", available_player_hash="ap",
        universe_hash="uh", projection_model_version="proj-v1", market_snapshot_hash="mk",
        feature_set_version="fs-v1", team_score_version="ts-v1",
        championship_equity_version="ce-v1", pick_score_version="ps-v1",
        optimizer_version="opt-v1", seed=7, simulation_count=10,
        timestamp_utc="2026-09-06T00:00:00Z",
    )


def _build(team_count: int, roster: RosterSettings, *, base_seed: int = 3):
    ranking = _ranking(team_count, roster)
    profile = ranking.profile
    manual_assets: list[dict[str, str]] = []
    adp = AdpSnapshot(profile.profile_id, "", "standard", team_count, "", "", "", (), ())
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=base_seed
    )
    return build_decision_bundle_v2(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=["RB-0"],
        candidate_player_ids=["RB-1", "WR-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        player_scores={"RB-1": 88.0},
        trials=2, seasons=20, base_seed=base_seed,
    )


def test_roster_matches_historical_shape_true_only_for_exact_match() -> None:
    exact = RosterSettings(qb=1, rb=1, wr=1, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=1)
    assert roster_matches_historical_shape(exact) is True
    real_league = RosterSettings(bench_size=6)
    assert roster_matches_historical_shape(real_league) is False


def test_scoring_format_label_covers_standard_taxonomy() -> None:
    assert scoring_format_label(0.0) == "Non-PPR"
    assert scoring_format_label(0.5) == "Half-PPR"
    assert scoring_format_label(1.0) == "PPR"
    assert scoring_format_label(0.25) == "Custom"


def test_adp_percentile_by_player_is_empty_when_adp_unavailable() -> None:
    unavailable = AdpSnapshot("p", "", "standard", 12, "", "", "", (), ())
    assert adp_percentile_by_player(unavailable) == {}


def test_build_decision_bundle_v2_composes_team_score_v2_for_a_supported_league() -> None:
    result = _build(12, RosterSettings(bench_size=6))

    assert result.version == DECISION_BUNDLE_V2_VERSION
    assert result.v2_status == "OK"
    assert result.current_team_score_v2 is not None
    assert 0.0 <= result.current_team_score_v2["calibrated_score"] <= 100.0
    # A real 12-team league with a 6-man bench never matches the thin
    # historical validation shape -- must be labeled honestly, never
    # overstated as HISTORICALLY_VALIDATED.
    assert result.current_team_score_v2["evidence_level"] == (
        "TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED"
    )
    assert len(result.candidates) == 2
    for candidate in result.candidates:
        assert candidate.v2_status == "OK"
        assert candidate.team_score_v2 is not None
        assert candidate.championship_equity_v2 is not None
        assert "team_score_delta" in candidate.team_score_v2
        assert 0.0 <= candidate.championship_equity_v2["post_pick_championship_equity"] <= 1.0
    # The underlying V1 bundle is carried through completely unchanged.
    assert len(result.v1_bundle.candidates) == 2


def test_build_decision_bundle_v2_supports_every_validated_team_count() -> None:
    for team_count in (8, 10, 12, 16):
        result = _build(team_count, RosterSettings(bench_size=5), base_seed=team_count)
        assert result.v2_status == "OK", f"team_count={team_count} unexpectedly degraded"
        assert result.team_count == team_count
        assert result.current_team_score_v2["team_count"] == team_count


def test_build_decision_bundle_v2_degrades_gracefully_for_unsupported_team_count() -> None:
    result = _build(6, RosterSettings(bench_size=3))

    assert result.v2_status.startswith("DEGRADED")
    assert result.current_team_score_v2 is None
    assert result.candidates == ()
    # The V1 bundle -- Player Score / Team Score V1 / Equity V1 / Pick
    # Score / Cost of Waiting -- must remain fully intact and unaffected.
    assert len(result.v1_bundle.candidates) == 2
    assert result.v1_bundle.current_team_score.percentile is not None


def test_build_decision_bundle_v2_degrades_gracefully_when_frozen_model_is_missing(
    monkeypatch, tmp_path
) -> None:
    missing = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(bundle_v2, "_TEAM_SCORE_V2_FROZEN_MODEL_PATH", missing)

    result = _build(12, RosterSettings(bench_size=6))

    assert result.v2_status.startswith("DEGRADED")
    assert "Frozen model file missing" in result.v2_status
    assert result.current_team_score_v2 is None
    # Still never crashes -- the V1 bundle is intact.
    assert len(result.v1_bundle.candidates) == 2
