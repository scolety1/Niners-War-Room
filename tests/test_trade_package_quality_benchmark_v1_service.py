from __future__ import annotations

from src.services.redraft_engine_v1_service import DraftContext, LeagueProfile, RosterSettings, ScoringSettings
from src.services.redraft_trade_analysis_service import TradeEvaluation
from src.services.trade_package_search_service import TradePackageCandidate, TradePackageSearchResult
from src.services.trade_package_quality_benchmark_v1_service import (
    NEAR_DUPLICATE_JACCARD_THRESHOLD,
    STARTER_VALUE_EPSILON,
    bench_for_bench_clutter_rate,
    check_dominance_violations,
    check_diversity,
    check_mutual_starter_gain,
    check_near_duplicates,
    check_position_need_fit,
    check_roster_consolidation_legality,
    measure_latency,
    run_trade_package_quality_benchmark,
    size_utility_distribution,
)


def _profile(**overrides) -> LeagueProfile:
    kwargs = dict(
        profile_id="fixture-league", league_name="Fixture League", season=2026, team_count=10,
        roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=0, dst=0, bench_size=6),
        scoring=ScoringSettings(reception=1), draft=DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="lg1",
    )
    kwargs.update(overrides)
    return LeagueProfile(**kwargs)


def _evaluation(
    *,
    net_marginal_utility: float | None = 10.0,
    starting_lineup_value_delta: float = 0.0,
    starter_holes_before: tuple[str, ...] = (),
    starter_holes_after: tuple[str, ...] = (),
) -> TradeEvaluation:
    return TradeEvaluation(
        gives=(), receives=(), ros_value_delta=0.0, net_marginal_utility=net_marginal_utility,
        starting_lineup_value_before=0.0, starting_lineup_value_after=starting_lineup_value_delta,
        starting_lineup_value_delta=starting_lineup_value_delta,
        bench_contingency_value_before=0.0, bench_contingency_value_after=0.0,
        starter_holes_before=starter_holes_before, starter_holes_after=starter_holes_after,
        position_redundancy_before={}, position_redundancy_after={}, risk_flags=(),
    )


def _candidate(
    *,
    opponent_roster_id: str = "2",
    shape: str = "1-for-1",
    send,
    receive,
    owner_eval: TradeEvaluation | None = None,
    opponent_eval: TradeEvaluation | None = None,
) -> TradePackageCandidate:
    return TradePackageCandidate(
        opponent_roster_id=opponent_roster_id, opponent_team_name="Rival", package_shape=shape,
        you_send=tuple(send), you_receive=tuple(receive), you_send_names=tuple(send),
        you_receive_names=tuple(receive),
        owner_evaluation=owner_eval or _evaluation(), opponent_evaluation=opponent_eval or _evaluation(),
        why_it_helps_you=(), why_it_may_fit_them=(),
    )


def _result(candidates, *, mode="FIND_WIN_WIN", packages_evaluated=None, truncated=False) -> TradePackageSearchResult:
    return TradePackageSearchResult(
        mode=mode, candidates=tuple(candidates),
        packages_evaluated=packages_evaluated if packages_evaluated is not None else len(candidates),
        opponents_searched=1, truncated=truncated,
    )


# ---------------------------------------------------------------------------
# Dimension 1 -- dominance re-verification.
# ---------------------------------------------------------------------------


def test_dominance_violation_detected_when_a_bigger_package_is_strictly_worse() -> None:
    simple = _candidate(
        shape="1-for-1", send=["a"], receive=["x"],
        owner_eval=_evaluation(net_marginal_utility=10.0), opponent_eval=_evaluation(net_marginal_utility=5.0),
    )
    worse_bigger = _candidate(
        shape="2-for-2", send=["a", "b"], receive=["x", "y"],
        owner_eval=_evaluation(net_marginal_utility=8.0), opponent_eval=_evaluation(net_marginal_utility=4.0),
    )
    violations = check_dominance_violations([simple, worse_bigger])
    assert len(violations) == 1
    assert violations[0].dominated_send == ("a", "b")


def test_no_dominance_violation_on_clean_output() -> None:
    simple = _candidate(
        shape="1-for-1", send=["a"], receive=["x"],
        owner_eval=_evaluation(net_marginal_utility=10.0), opponent_eval=_evaluation(net_marginal_utility=2.0),
    )
    better_bigger = _candidate(
        shape="2-for-2", send=["a", "b"], receive=["x", "y"],
        owner_eval=_evaluation(net_marginal_utility=15.0), opponent_eval=_evaluation(net_marginal_utility=1.0),
    )
    assert check_dominance_violations([simple, better_bigger]) == ()


def test_dominance_check_scoped_per_opponent() -> None:
    # Same values, but different opponents -- must never cross-contaminate.
    simple = _candidate(
        opponent_roster_id="2", shape="1-for-1", send=["a"], receive=["x"],
        owner_eval=_evaluation(net_marginal_utility=10.0), opponent_eval=_evaluation(net_marginal_utility=5.0),
    )
    worse_bigger_other_opponent = _candidate(
        opponent_roster_id="3", shape="2-for-2", send=["a", "b"], receive=["x", "y"],
        owner_eval=_evaluation(net_marginal_utility=8.0), opponent_eval=_evaluation(net_marginal_utility=4.0),
    )
    assert check_dominance_violations([simple, worse_bigger_other_opponent]) == ()


# ---------------------------------------------------------------------------
# Dimension 2/4 -- mutual starter gain / bench-for-bench clutter.
# ---------------------------------------------------------------------------


def test_both_sides_starter_impact_labeled_correctly() -> None:
    candidate = _candidate(
        send=["a"], receive=["x"],
        owner_eval=_evaluation(starting_lineup_value_delta=5.0),
        opponent_eval=_evaluation(starting_lineup_value_delta=3.0),
    )
    rows = check_mutual_starter_gain([candidate])
    assert rows[0].label == "BOTH_SIDES_STARTER_IMPACT"


def test_one_sided_starter_impact_labeled_correctly() -> None:
    candidate = _candidate(
        send=["a"], receive=["x"],
        owner_eval=_evaluation(starting_lineup_value_delta=5.0),
        opponent_eval=_evaluation(starting_lineup_value_delta=0.0),
    )
    rows = check_mutual_starter_gain([candidate])
    assert rows[0].label == "ONE_SIDED_STARTER_IMPACT"


def test_bench_for_bench_clutter_detected_and_rated() -> None:
    clutter = _candidate(
        send=["a"], receive=["x"],
        owner_eval=_evaluation(starting_lineup_value_delta=0.0),
        opponent_eval=_evaluation(starting_lineup_value_delta=0.1),  # below epsilon
    )
    real = _candidate(
        send=["b"], receive=["y"],
        owner_eval=_evaluation(starting_lineup_value_delta=5.0),
        opponent_eval=_evaluation(starting_lineup_value_delta=5.0),
    )
    rows = check_mutual_starter_gain([clutter, real])
    assert rows[0].label == "NEITHER_SIDE_STARTER_IMPACT"
    assert rows[1].label == "BOTH_SIDES_STARTER_IMPACT"
    assert bench_for_bench_clutter_rate(rows) == 0.5


def test_bench_for_bench_clutter_rate_is_none_on_empty_input() -> None:
    assert bench_for_bench_clutter_rate(()) is None


def test_epsilon_is_the_documented_value() -> None:
    assert STARTER_VALUE_EPSILON == 0.5


# ---------------------------------------------------------------------------
# Dimension 3 -- position-need fit.
# ---------------------------------------------------------------------------


def test_hole_fit_detects_a_real_resolved_hole() -> None:
    candidate = _candidate(
        send=["a"], receive=["x"],
        owner_eval=_evaluation(starter_holes_before=("TE 0/1", "WR 1/2"), starter_holes_after=("WR 1/2",)),
    )
    rows = check_position_need_fit([candidate])
    assert rows[0].addressed_a_real_hole is True
    assert rows[0].owner_holes_resolved == ("TE 0/1",)


def test_hole_fit_flags_no_hole_addressed_when_holes_are_unchanged() -> None:
    candidate = _candidate(
        send=["a"], receive=["x"],
        owner_eval=_evaluation(starter_holes_before=("TE 0/1",), starter_holes_after=("TE 0/1",)),
    )
    rows = check_position_need_fit([candidate])
    assert rows[0].addressed_a_real_hole is False
    assert rows[0].owner_holes_resolved == ()


# ---------------------------------------------------------------------------
# Dimension 5 -- near-duplicate packages.
# ---------------------------------------------------------------------------


def test_near_duplicate_detected_above_threshold() -> None:
    # Shares 3 of 4 total distinct players (a,x,y) vs (a,x,z) -> union={a,x,y,z}, intersection={a,x} -> 2/4=0.5
    left = _candidate(send=["a"], receive=["x", "y"])
    right = _candidate(send=["a"], receive=["x", "z"])
    pairs = check_near_duplicates([left, right])
    assert len(pairs) == 1
    assert pairs[0].jaccard_similarity == 0.5


def test_clearly_distinct_packages_are_not_flagged() -> None:
    left = _candidate(send=["a"], receive=["x"])
    right = _candidate(send=["b"], receive=["y"])
    assert check_near_duplicates([left, right]) == ()


def test_exact_duplicate_shapes_are_excluded_from_near_duplicate_reporting() -> None:
    # Structurally impossible from the real generator, but this check must
    # not double-count an exact duplicate as a "near" duplicate either.
    left = _candidate(send=["a"], receive=["x"])
    right = _candidate(send=["a"], receive=["x"])
    assert check_near_duplicates([left, right]) == ()


def test_near_duplicate_threshold_is_the_documented_value() -> None:
    assert NEAR_DUPLICATE_JACCARD_THRESHOLD == 0.5


def test_near_duplicate_check_scoped_per_opponent() -> None:
    left = _candidate(opponent_roster_id="2", send=["a"], receive=["x", "y"])
    right = _candidate(opponent_roster_id="3", send=["a"], receive=["x", "z"])
    assert check_near_duplicates([left, right]) == ()


# ---------------------------------------------------------------------------
# Dimension 6 -- size/utility distribution (diagnostic).
# ---------------------------------------------------------------------------


def test_size_utility_distribution_groups_by_shape() -> None:
    candidates = [
        _candidate(shape="1-for-1", send=["a"], receive=["x"], owner_eval=_evaluation(net_marginal_utility=10.0)),
        _candidate(shape="1-for-1", send=["b"], receive=["y"], owner_eval=_evaluation(net_marginal_utility=20.0)),
        _candidate(shape="2-for-2", send=["a", "b"], receive=["x", "y"], owner_eval=_evaluation(net_marginal_utility=30.0)),
    ]
    report = size_utility_distribution(candidates)
    assert report["1-for-1"]["count"] == 2
    assert report["1-for-1"]["meanOwnerNetUtility"] == 15.0
    assert report["2-for-2"]["count"] == 1
    assert report["2-for-2"]["meanOwnerNetUtility"] == 30.0


# ---------------------------------------------------------------------------
# Dimension 7 -- roster consolidation legality (independently re-verified).
# ---------------------------------------------------------------------------


def test_roster_consolidation_violation_detected_for_owner_over_capacity() -> None:
    profile = _profile(roster=RosterSettings(qb=1, rb=1, wr=1, te=0, flex=0, k=0, dst=0, bench_size=1))
    # total slots = 4
    candidate = _candidate(send=["a"], receive=["x", "y"])  # 1-for-2: size grows by 1
    violations = check_roster_consolidation_legality(
        [candidate], owner_roster_size_before=4, opponent_roster_size_before_by_id={"2": 4}, profile=profile,
    )
    assert len(violations) == 1
    assert violations[0].side == "OWNER"


def test_roster_consolidation_no_violation_when_sizes_stay_legal() -> None:
    profile = _profile(roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=0, dst=0, bench_size=6))
    candidate = _candidate(send=["a"], receive=["x"])  # 1-for-1: no size change
    violations = check_roster_consolidation_legality(
        [candidate], owner_roster_size_before=13, opponent_roster_size_before_by_id={"2": 13}, profile=profile,
    )
    assert violations == ()


def test_roster_consolidation_detects_opponent_side_violation_too() -> None:
    profile = _profile(roster=RosterSettings(qb=1, rb=1, wr=1, te=0, flex=0, k=0, dst=0, bench_size=1))
    candidate = _candidate(send=["a", "b"], receive=["x"])  # opponent gains a net player
    violations = check_roster_consolidation_legality(
        [candidate], owner_roster_size_before=4, opponent_roster_size_before_by_id={"2": 4}, profile=profile,
    )
    assert len(violations) == 1
    assert violations[0].side == "OPPONENT"


# ---------------------------------------------------------------------------
# Dimension 8 -- diversity.
# ---------------------------------------------------------------------------


def test_diversity_report_counts_distinct_and_recycled_players() -> None:
    candidates = [
        _candidate(send=["a"], receive=["x"]),
        _candidate(send=["a"], receive=["y"]),
        _candidate(send=["b"], receive=["z"]),
    ]
    report = check_diversity(candidates)
    assert report.total_candidates == 3
    assert report.distinct_players_used == 5  # a,x,y,b,z
    assert report.max_single_player_frequency == 2  # "a" appears twice
    assert report.most_recycled_player_id == "a"


def test_diversity_report_on_empty_input() -> None:
    report = check_diversity(())
    assert report.total_candidates == 0
    assert report.distinct_players_used == 0
    assert report.distinct_player_ratio is None
    assert report.most_recycled_player_id is None


# ---------------------------------------------------------------------------
# Dimension 9 -- latency.
# ---------------------------------------------------------------------------


def test_measure_latency_returns_a_real_nonnegative_elapsed_time() -> None:
    result, elapsed = measure_latency(lambda: sum(range(1000)))
    assert result == sum(range(1000))
    assert elapsed >= 0.0


# ---------------------------------------------------------------------------
# Top-level orchestrator.
# ---------------------------------------------------------------------------


def test_run_trade_package_quality_benchmark_composes_every_dimension() -> None:
    profile = _profile()
    candidate = _candidate(
        send=["a"], receive=["x"],
        owner_eval=_evaluation(
            net_marginal_utility=10.0, starting_lineup_value_delta=5.0,
            starter_holes_before=("TE 0/1",), starter_holes_after=(),
        ),
        opponent_eval=_evaluation(net_marginal_utility=3.0, starting_lineup_value_delta=2.0),
    )
    result = _result([candidate], mode="FIND_WIN_WIN", packages_evaluated=52, truncated=False)
    report = run_trade_package_quality_benchmark(
        result, label="test-run", owner_roster_size_before=13,
        opponent_roster_size_before_by_id={"2": 13}, profile=profile, elapsed_seconds=0.42,
    )
    assert report.label == "test-run"
    assert report.mode == "FIND_WIN_WIN"
    assert report.candidate_count == 1
    assert report.packages_evaluated == 52
    assert report.dominance_violations == ()
    assert report.starter_impact_rows[0].label == "BOTH_SIDES_STARTER_IMPACT"
    assert report.bench_for_bench_clutter_rate == 0.0
    assert report.hole_fit_rows[0].addressed_a_real_hole is True
    assert report.near_duplicate_pairs == ()
    assert "1-for-1" in report.size_utility_distribution
    assert report.roster_consolidation_violations == ()
    assert report.diversity.total_candidates == 1
    payload = report.to_dict()
    assert payload["elapsedSeconds"] == 0.42
    assert payload["mode"] == "FIND_WIN_WIN"
