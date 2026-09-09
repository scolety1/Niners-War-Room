from src.services.raw_action_value_live_service import (
    DEFAULT_MAX_RAV_CANDIDATES,
    evaluate_raw_action_value_live,
)
from src.services.redraft_draft_room_v1_service import AdpSnapshot, draft_order
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


def test_mixed_position_candidates_deep_in_a_draft_do_not_collapse_to_identical_values() -> None:
    """Regression fixture for a real bug found and fixed via the owner's own
    live testing (real "Fantasy Gamers" league, round 4+): 8 real, materially
    different candidates (QB/RB/WR, different NWR ranks and ADPs) all
    returned the exact same Raw Action Value / Team Score / Pick Score --
    "not credible candidate-specific evaluation" in the owner's own words.

    Root cause, traced: `simulate_pick_now()`'s full-draft-completion
    rollout produces genuinely different, but similarly-strong, terminal
    rosters for different forced candidates deep in a draft (the market/CPU
    continuation policy "fills in" comparably either way) -- and
    `team_score()`'s PERCENTILE (bucketed against only a ~20-roster
    comparable-league population at the FAST preset) is far too coarse to
    tell those genuinely-different real rosters apart, collapsing them onto
    the same bucket. Fixed by using the real, continuous, un-bucketed
    `.roster_value` as the RAV terminal value instead of `.percentile` --
    this test reproduces the exact structural conditions (an existing
    partial roster, several mixed-position candidates simultaneously) and
    asserts real, non-identical expected_terminal_value output."""
    ranking = _ranking(team_count=10)
    profile = ranking.profile
    manual_assets: list[dict] = []
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=42
    )
    # An owner roster already several picks deep, matching the real
    # scenario this bug was found in (round 4+, not a fresh empty roster).
    owner_picks = {
        1: ("RB-10", "RB"),
        20: ("WR-15", "WR"),
        21: ("TE-2", "TE"),
    }
    picks = []
    opponent_index = 20
    for pick_number, team_slot in enumerate(draft_order(profile)[:39], start=1):
        if pick_number in owner_picks:
            player_id, position = owner_picks[pick_number]
        else:
            player_id, position = f"WR-{opponent_index}", "WR"
            opponent_index += 1
        picks.append(
            {
                "pick_number": pick_number,
                "player_id": player_id,
                "team_slot": team_slot,
                "position": position,
                "player_name": player_id,
            }
        )
    from_state = {
        "schema_version": 1,
        "profile_id": profile.profile_id,
        "owner_slot": 1,
        "seed": 42,
        "speed": "FAST",
        "mode": "MOCK",
        "drafted": [pick["player_id"] for pick in picks],
        "picks": picks,
        "updated_at_utc": "",
    }
    mixed_candidates = ["QB-0", "QB-1", "RB-11", "WR-16", "QB-2", "RB-12", "WR-17", "RB-13"]

    result = evaluate_raw_action_value_live(
        profile, ranking, manual_assets, adp,
        owner_slot=1, candidate_player_ids=mixed_candidates,
        from_state=from_state, comparable_leagues=leagues, state_id="deep-draft-mixed-position",
        max_rav_candidates=8, rav_trials=2, base_seed=42,
    )

    ok_outcomes = [o for o in result.values() if o.status == "OK"]
    assert len(ok_outcomes) >= 4, "expected most/all candidates to evaluate successfully"
    terminal_values = [o.raw_action_value.expected_terminal_value for o in ok_outcomes]
    # The real bug: every candidate collapsed to the exact same value. The
    # fix must produce genuine spread -- not necessarily every value
    # distinct, but not a single flat value across every candidate.
    assert len(set(terminal_values)) > 1, (
        f"all {len(terminal_values)} candidates collapsed to identical terminal values "
        f"{terminal_values} -- this is the exact real saturation bug, not fixed"
    )
    # Regret must likewise show real spread, not a flat 0 (or flat anything)
    # for every candidate.
    regrets = [o.expected_regret for o in ok_outcomes]
    assert len(set(regrets)) > 1, f"regret collapsed to a single value across candidates: {regrets}"
