from src.services.decision_bundle_service import DECISION_BUNDLE_VERSION, build_decision_bundle
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
from src.services.shadow_numeric_authorities_service import (
    simulate_comparable_leagues,
)


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


def test_build_decision_bundle_composes_a_real_candidate_list() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=3
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=["RB-0"],
        candidate_player_ids=["RB-1", "WR-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        player_scores={"RB-1": 88.0},
        trials=2, seasons=20, base_seed=3,
    )

    assert bundle.version == DECISION_BUNDLE_VERSION
    assert len(bundle.candidates) == 2
    player_ids = {c.player_id for c in bundle.candidates}
    assert player_ids == {"RB-1", "WR-0"}
    assert bundle.latency_seconds >= 0.0
    assert bundle.provenance.bundle_hash


def test_candidates_are_sorted_best_pick_score_first() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=5
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0", "RB-1", "WR-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=5,
    )
    scores = [c.pick_score for c in bundle.candidates]
    assert scores == sorted(scores, reverse=True)


def test_a_candidate_with_no_player_score_carries_an_explicit_warning() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=9
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=9,
    )
    candidate = bundle.candidates[0]
    assert candidate.player_score is None
    assert any("Player Score" in w for w in candidate.warnings)


def test_uncertainty_is_always_a_populated_first_class_field() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=11
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=11,
    )
    assert bundle.candidates[0].uncertainty
    assert "UNCERTAINTY" in bundle.candidates[0].uncertainty


def test_cost_of_waiting_can_be_disabled_and_actions_fall_back_to_unscored() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=13
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        include_cost_of_waiting=False,
        trials=2, seasons=20, base_seed=13,
    )
    assert bundle.candidates[0].action == "UNSCORED"
    assert bundle.candidates[0].make_it_back_probability is None


def test_team_score_delta_is_after_minus_current_never_the_raw_after_value() -> None:
    """Owner-test follow-up: a real screenshot showed an implausibly large
    Team Score Delta (+96.9) for a candidate against a NON-EMPTY owner
    roster, which the owner flagged as "suspicious" and asked us to
    verify is not the bug where `post_pick_team_score` gets displayed as
    `team_score_delta`. Confirmed by direct code read
    (`decision_bundle_service.py`: `team_score_delta=round(pick.team_score_after
    - current_team.percentile, 2)`) and locked in here: with a real,
    non-empty starting roster, team_score_delta must equal
    team_score_after minus the bundle's own current_team_score.percentile
    -- never merely equal team_score_after itself (the exact "after
    displayed as delta" bug this test would catch)."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=6, base_seed=17
    )

    # A real, non-empty roster (3 players already owned) -- the exact
    # "roster is NOT empty" condition the owner's report specifically
    # called out.
    current_owner_player_ids = ["RB-0", "WR-0", "TE-0"]
    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=current_owner_player_ids,
        candidate_player_ids=["RB-1", "WR-1", "QB-0", "TE-1"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=6, seasons=20, base_seed=17,
    )
    current_percentile = bundle.current_team_score.percentile
    for candidate in bundle.candidates:
        expected_delta = round(candidate.team_score_after - current_percentile, 2)
        assert candidate.team_score_delta == expected_delta, (
            f"{candidate.player_id}: team_score_delta={candidate.team_score_delta} "
            f"but team_score_after({candidate.team_score_after}) - current({current_percentile}) "
            f"= {expected_delta}"
        )
        # The specific bug shape the owner asked us to rule out: delta
        # silently equal to the raw after-value (which would only occur
        # by mistaking one field for the other, not by real arithmetic --
        # this is a real inequality assertion, not tautological, whenever
        # current_percentile is genuinely nonzero).
        if current_percentile != 0:
            assert candidate.team_score_delta != candidate.team_score_after
