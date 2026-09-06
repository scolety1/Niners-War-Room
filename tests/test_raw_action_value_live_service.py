from src.services.raw_action_value_live_service import (
    DEFAULT_MAX_RAV_CANDIDATES,
    evaluate_raw_action_value_live,
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
        ScoringSettings(reception=0.0), DraftContext(rounds=4, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _empty_adp(profile: LeagueProfile) -> AdpSnapshot:
    return AdpSnapshot(profile.profile_id, "", "standard", profile.team_count, "", "", "", (), ())


def test_evaluate_raw_action_value_live_returns_real_values_for_each_candidate() -> None:
    ranking = _ranking(team_count=8)
    profile = ranking.profile
    manual_assets: list[dict] = []
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=3
    )

    result = evaluate_raw_action_value_live(
        profile, ranking, manual_assets, adp,
        owner_slot=1, candidate_player_ids=["RB-0", "RB-1", "WR-0"],
        from_state=None, comparable_leagues=leagues, state_id="test-state-1",
        max_rav_candidates=3, rav_trials=2, base_seed=3,
    )

    assert set(result.keys()) == {"RB-0", "RB-1", "WR-0"}
    for outcome in result.values():
        assert outcome.status == "OK", outcome.status
        assert outcome.raw_action_value is not None
        assert outcome.rollout_count == 2
        assert len(outcome.terminal_values_by_rollout) == 2
        assert outcome.expected_regret is not None
        assert outcome.expected_regret >= 0.0
        assert outcome.decision_quality_percentile is not None
        assert 0.0 <= outcome.decision_quality_percentile <= 100.0

    # Regret is 0 for whichever candidate has the best raw_action_value.
    best = max(result.values(), key=lambda o: o.raw_action_value.expected_terminal_value)
    assert best.expected_regret == 0.0


def test_evaluate_raw_action_value_live_respects_top_n_limit() -> None:
    ranking = _ranking(team_count=8)
    profile = ranking.profile
    manual_assets: list[dict] = []
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=5
    )

    candidates = ["RB-0", "RB-1", "WR-0", "WR-1", "TE-0", "QB-0", "RB-2"]
    result = evaluate_raw_action_value_live(
        profile, ranking, manual_assets, adp,
        owner_slot=1, candidate_player_ids=candidates,
        from_state=None, comparable_leagues=leagues, state_id="test-state-2",
        max_rav_candidates=3, rav_trials=2, base_seed=5,
    )
    assert len(result) == 3
    assert set(result.keys()) == set(candidates[:3])


def test_evaluate_raw_action_value_live_returns_empty_for_no_candidates() -> None:
    ranking = _ranking(team_count=8)
    profile = ranking.profile
    manual_assets: list[dict] = []
    adp = _empty_adp(profile)
    result = evaluate_raw_action_value_live(
        profile, ranking, manual_assets, adp,
        owner_slot=1, candidate_player_ids=[], from_state=None,
        comparable_leagues=[], state_id="test-state-3",
    )
    assert result == {}


def test_default_max_rav_candidates_is_small_for_cost_control() -> None:
    assert DEFAULT_MAX_RAV_CANDIDATES <= 8
