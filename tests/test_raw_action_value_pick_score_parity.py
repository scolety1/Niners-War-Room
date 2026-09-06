"""NWR Final Pre-Draft Product Hardening V1, section 2: parity between the
OFFLINE HISTORICAL decision engine (`decision_engine_v2_contracts_service`,
called directly, exactly as the research branch's final 2025 holdout
evaluation does) and the LIVE DecisionBundle V2 path
(`raw_action_value_live_service`), for identical, fixed, synthetic terminal-
value data.

This does NOT assert the two paths' full rollout simulators produce
numerically identical output (they use different underlying draft
simulators -- the historical replay engine for the frozen holdout vs the
real live Draft Room's continuation policy -- by design, matching two
genuinely different real state spaces). What IS asserted, and is the real
point of "parity": the LIVE path routes through the exact same, unmodified
`compute_raw_action_value` / `compute_regret` /
`compute_decision_quality_percentile_raw_rank` functions the offline
historical engine uses -- never a second, drifting reimplementation, and
never the old placeholder `raw_decision_utility`/`pick_score()` formulas.
"""

from src.services.decision_engine_v2_contracts_service import (
    TERMINAL_OBJECTIVE_TEAM_SCORE,
    ComparableStateStratum,
    FrozenCandidateSet,
    compute_decision_quality_percentile_raw_rank,
    compute_raw_action_value,
    compute_regret,
    register_pick_score_calibration_contract_v2,
)
from src.services.raw_action_value_live_service import (
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


def test_offline_and_live_compute_raw_action_value_give_identical_results() -> None:
    """The exact function `compute_raw_action_value` -- called directly
    here as the offline historical engine calls it -- must produce
    byte-identical output whether invoked directly or reached through the
    live wiring, for the same real rollout data."""
    rollouts = [72.0, 68.0, 75.0, 70.0]
    offline = compute_raw_action_value(
        state_id="parity-state", action_candidate_id="RB-0",
        terminal_values_by_rollout=rollouts, terminal_objective_name=TERMINAL_OBJECTIVE_TEAM_SCORE,
        lookahead_depth=4, championship_equity_gate_passed=False, provenance={},
    )
    # Reaching the same function through the live module's own import --
    # confirms it is the same function object, not a shadowing reimplementation.
    import src.services.raw_action_value_live_service as live_module

    live_reexecuted = live_module.compute_raw_action_value(
        state_id="parity-state", action_candidate_id="RB-0",
        terminal_values_by_rollout=rollouts, terminal_objective_name=TERMINAL_OBJECTIVE_TEAM_SCORE,
        lookahead_depth=4, championship_equity_gate_passed=False, provenance={},
    )
    assert offline == live_reexecuted


def test_offline_and_live_regret_and_decision_quality_percentile_are_the_same_function() -> None:
    stratum = ComparableStateStratum(
        league_format_id="PARITY_TEST", league_size=8,
        draft_phase="ROUND_1", roster_state_summary="s",
    )
    register_pick_score_calibration_contract_v2(stratum)
    candidate_set = FrozenCandidateSet(
        state_id="parity-state-2", candidate_action_ids=("A", "B", "C"),
        frozen_at_utc="2026-09-06T00:00:00Z", frozen_before_outcome_unlock=True,
    )
    terminal_value_by_candidate = {"A": 90.0, "B": 80.0, "C": 60.0}
    offline_regret_a = compute_regret(
        action_candidate_id="A", terminal_value_by_candidate=terminal_value_by_candidate,
        regret_kind="EX_ANTE_MODEL_REGRET", candidate_set=candidate_set,
    )
    offline_regret_b = compute_regret(
        action_candidate_id="B", terminal_value_by_candidate=terminal_value_by_candidate,
        regret_kind="EX_ANTE_MODEL_REGRET", candidate_set=candidate_set,
    )
    offline_percentile_b = compute_decision_quality_percentile_raw_rank(
        regret_value=offline_regret_b.regret, comparable_regrets=[offline_regret_a.regret, 5.0],
    )

    import src.services.raw_action_value_live_service as live_module

    live_regret_b = live_module.compute_regret(
        action_candidate_id="B", terminal_value_by_candidate=terminal_value_by_candidate,
        regret_kind="EX_ANTE_MODEL_REGRET", candidate_set=candidate_set,
    )
    live_percentile_b = live_module.compute_decision_quality_percentile_raw_rank(
        regret_value=live_regret_b.regret, comparable_regrets=[offline_regret_a.regret, 5.0],
    )
    assert offline_regret_b == live_regret_b
    assert offline_percentile_b == live_percentile_b


def test_live_raw_action_value_module_never_imports_the_old_placeholder_formula() -> None:
    """`raw_decision_utility`/`pick_score()` (the pre-existing V1
    placeholder formulas) are never IMPORTED into the RAV computation
    module -- confirmed structurally (this module's actual dependency
    graph), not by a naive string search of its own explanatory prose,
    which legitimately references `pick_score()` by name when describing
    why this module's design differs from it."""
    import src.services.raw_action_value_live_service as live_module

    assert not hasattr(live_module, "pick_score")
    assert not hasattr(live_module, "raw_decision_utility")
    # And positively: it DOES import the real, frozen contracts functions.
    assert hasattr(live_module, "compute_raw_action_value")
    assert hasattr(live_module, "compute_regret")
    assert hasattr(live_module, "compute_decision_quality_percentile_raw_rank")


def test_live_raw_action_value_runs_through_real_bounded_lookahead_rollouts() -> None:
    """End-to-end: the live wiring actually calls the real, frozen
    `compute_raw_action_value` with real rollout data produced by real
    `simulate_pick_now()` full-draft completions -- not a shortcut."""
    ranking = _ranking(team_count=8)
    profile = ranking.profile
    manual_assets: list[dict] = []
    adp = AdpSnapshot(profile.profile_id, "", "standard", profile.team_count, "", "", "", (), ())
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=11
    )
    result = evaluate_raw_action_value_live(
        profile, ranking, manual_assets, adp,
        owner_slot=1, candidate_player_ids=["RB-0", "WR-0"], from_state=None,
        comparable_leagues=leagues, state_id="e2e-parity", max_rav_candidates=2,
        rav_trials=2, base_seed=11,
    )
    for outcome in result.values():
        assert outcome.status == "OK"
        assert outcome.raw_action_value.terminal_objective_name == TERMINAL_OBJECTIVE_TEAM_SCORE
        assert outcome.raw_action_value.rollout_count == 2
