from src.services.decision_bundle_service import (
    DECISION_BUNDLE_VERSION,
    CandidateBundle,
    _candidate_sort_key,
    build_decision_bundle,
)
from src.services.metric_status_contract_service import COMPUTATION_STATES
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


def test_build_decision_bundle_computes_marginal_utility_and_orders_by_it() -> None:
    """PROMOTION (real, preregistered walk-forward evaluation, see
    docs/codex/NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md):
    build_decision_bundle now computes a real marginal_utility for every
    candidate and the returned bundle.candidates is already in
    marginal-utility-primary order -- not merely computed-but-unused."""
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
        candidate_player_ids=["RB-1", "RB-2", "WR-0", "QB-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=3,
    )

    for candidate in bundle.candidates:
        assert candidate.marginal_utility is not None
    assert list(bundle.candidates) == sorted(bundle.candidates, key=_candidate_sort_key)


def test_candidates_happen_to_come_out_pick_score_descending_in_this_simple_fixture() -> None:
    """NOTE (post-promotion): the real PRIMARY sort key is now
    marginal_utility, not pick_score (see the _candidate_sort_key tests
    below) -- this fixture's empty current_owner_player_ids means every
    real candidate becomes a starter, so marginal_utility here tracks
    the same underlying value ranking pick_score does, and the two
    happen to agree. This is a real, expected consequence for an empty-
    roster scenario, not a guarantee pick_score itself drives order --
    see test_candidate_sort_key_orders_by_marginal_utility_first for the
    real counterexample where they disagree."""
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


def test_every_candidate_carries_a_populated_metric_status_for_every_covered_metric() -> None:
    """Owner feedback closure (shared cross-metric result-status contract):
    every CandidateBundle must carry a real MetricStatus for every metric
    this bundle covers, keyed exactly as the JSON payload keys it."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=21
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0", "RB-1"],
        comparable_leagues=leagues, provenance=_provenance(),
        player_scores={"RB-1": 88.0},
        trials=2, seasons=20, base_seed=21,
    )
    expected_keys = {
        "playerScore", "teamScore", "championshipEquity",
        "costOfWaiting", "makeItBack", "pickScore",
    }
    for candidate in bundle.candidates:
        assert set(candidate.metric_status) == expected_keys
        for status in candidate.metric_status.values():
            assert status.computation_state in COMPUTATION_STATES
            # No metric status is ever left with an unpopulated freshness/
            # domain fact -- the "evidence" axis is never silently blank.
            assert status.validation_domain
            assert status.source_freshness


def test_a_missing_player_score_is_missing_input_never_a_coerced_zero() -> None:
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=23
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=23,
    )
    candidate = bundle.candidates[0]
    status = candidate.metric_status["playerScore"]
    assert candidate.player_score is None
    assert status.computation_state == "MISSING_INPUT"
    assert status.genuine_zero is False


def test_pick_score_status_carries_the_real_tied_no_spread_flag_not_a_separate_fact() -> None:
    """The shared contract must not duplicate/contradict the existing,
    already-tested tied_no_spread disclosure -- it labels the exact same
    fact, not a second independently-derived one."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=29
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0", "RB-1", "WR-0"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=29,
    )
    for candidate in bundle.candidates:
        assert (
            candidate.metric_status["pickScore"].tied_no_spread
            == candidate.pick_score_tied_no_spread
        )


def test_result_can_be_evaluated_and_tied_and_the_axes_stay_independent() -> None:
    """A result being EVALUATED, genuinely tied, and resting on a given
    source freshness are three separate facts -- none of them may be forced
    into a single mutually-exclusive label."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=31
    )

    bundle = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0", "RB-1"],
        comparable_leagues=leagues, provenance=_provenance(),
        trials=2, seasons=20, base_seed=31,
    )
    for candidate in bundle.candidates:
        pick_status = candidate.metric_status["pickScore"]
        assert pick_status.computation_state == "EVALUATED"
        # tied_no_spread and source_freshness are populated independently of
        # computation_state -- being EVALUATED never blanks out the other axes.
        assert pick_status.tied_no_spread in (True, False)
        assert pick_status.source_freshness


def test_cost_of_waiting_discloses_whether_it_used_the_full_v2_evaluation() -> None:
    """A real, previously-silent evidence-quality distinction: cost_of_waiting
    falls back to the plainer Pick-Score-embedded estimate whenever the
    richer per-candidate V2 evaluation is disabled for this bundle -- now
    disclosed via data_coverage instead of looking identical either way."""
    ranking = _ranking()
    profile = ranking.profile
    manual_assets = _manual_assets()
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=37
    )

    # evaluate_cost_of_waiting_v2 needs at least one OTHER evaluated
    # candidate to compare against (its own documented skip condition), so
    # this fixture uses two real candidates -- a single-candidate fixture
    # would legitimately fall back for both runs and prove nothing.
    bundle_with_v2 = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0", "RB-1"],
        comparable_leagues=leagues, provenance=_provenance(),
        include_cost_of_waiting=True,
        trials=2, seasons=20, base_seed=37,
    )
    bundle_without_v2 = build_decision_bundle(
        profile=profile, ranking=ranking, manual_assets=manual_assets, adp=adp,
        owner_slot=1, current_owner_player_ids=[],
        candidate_player_ids=["RB-0", "RB-1"],
        comparable_leagues=leagues, provenance=_provenance(),
        include_cost_of_waiting=False,
        trials=2, seasons=20, base_seed=37,
    )
    with_v2_coverage = bundle_with_v2.candidates[0].metric_status["costOfWaiting"].data_coverage
    without_v2_coverage = (
        bundle_without_v2.candidates[0].metric_status["costOfWaiting"].data_coverage
    )
    assert with_v2_coverage != without_v2_coverage
    assert "Full" in with_v2_coverage
    assert "Fallback" in without_v2_coverage


# --- _candidate_sort_key: real, deterministic ordering -- PROMOTED to
# marginal_utility-primary (real, preregistered walk-forward evaluation,
# see docs/codex/NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md),
# with pick_score / raw_decision_utility / player_id as real tie-breaks
# --------------------------------------------------------------------


def _candidate(
    player_id: str,
    pick_score: float,
    raw_decision_utility: float,
    marginal_utility: float | None = None,
) -> CandidateBundle:
    return CandidateBundle(
        player_id=player_id, player_score=None, team_score_after=0.0, team_score_delta=0.0,
        championship_equity_after=0.0, equity_gain=0.0, cost_of_waiting=0.0,
        make_it_back_probability=None, make_it_back_trials=None,
        raw_decision_utility=raw_decision_utility, team_score_utility_component=0.0,
        equity_utility_component=0.0, pick_score=pick_score, pick_score_tied_no_spread=False,
        action="WAIT", warnings=(), uncertainty="", marginal_utility=marginal_utility,
    )


def test_candidate_sort_key_orders_by_marginal_utility_first() -> None:
    """PROMOTION: marginal_utility is now the primary sort key -- a
    candidate with a real, materially lower pick_score but a higher
    marginal_utility must still be recommended first."""
    high_utility_low_pick_score = _candidate("A", pick_score=20.0, raw_decision_utility=1.0, marginal_utility=90.0)
    low_utility_high_pick_score = _candidate("B", pick_score=80.0, raw_decision_utility=99.0, marginal_utility=10.0)
    ordered = sorted([low_utility_high_pick_score, high_utility_low_pick_score], key=_candidate_sort_key)
    assert ordered == [high_utility_low_pick_score, low_utility_high_pick_score]


def test_candidate_sort_key_falls_back_to_pick_score_when_marginal_utility_ties() -> None:
    a = _candidate("A", pick_score=80.0, raw_decision_utility=1.0, marginal_utility=50.0)
    b = _candidate("B", pick_score=20.0, raw_decision_utility=99.0, marginal_utility=50.0)
    assert sorted([b, a], key=_candidate_sort_key) == [a, b]


def test_candidate_sort_key_with_no_marginal_utility_falls_back_to_the_old_real_order() -> None:
    """A candidate this couldn't be computed for (should not happen in
    practice, but never assumed) sorts strictly last relative to any
    candidate that DOES have one -- a real computation gap is visible in
    ordering, never silently defaulted to 0 or crashed on."""
    has_utility = _candidate("A", pick_score=1.0, raw_decision_utility=1.0, marginal_utility=5.0)
    no_utility = _candidate("B", pick_score=99.0, raw_decision_utility=99.0, marginal_utility=None)
    assert sorted([no_utility, has_utility], key=_candidate_sort_key) == [has_utility, no_utility]


def test_candidate_sort_key_breaks_a_real_pick_score_tie_by_raw_decision_utility() -> None:
    """The real, disclosed scenario this closes: pick_score is a lossy,
    per-call 0-100 normalization -- two candidates can land on the exact
    same pick_score while still differing in the real, full-precision
    signal it was compressed from. Both candidates here also tie on
    marginal_utility (the real primary key), isolating this tie-break.
    The higher raw_decision_utility must win the tie, not whatever order
    the candidates happened to be built in."""
    tied_low_utility = _candidate("A", pick_score=50.0, raw_decision_utility=1.5, marginal_utility=10.0)
    tied_high_utility = _candidate("B", pick_score=50.0, raw_decision_utility=3.2, marginal_utility=10.0)
    # Deliberately built in the "wrong" order -- proves the sort itself
    # does the work, not accidental input ordering.
    ordered = sorted([tied_low_utility, tied_high_utility], key=_candidate_sort_key)
    assert ordered == [tied_high_utility, tied_low_utility]


def test_candidate_sort_key_breaks_a_full_double_tie_deterministically_by_player_id() -> None:
    """When every real signal agrees (genuine multi-way tie), the sort
    still resolves to one deterministic order (player_id) rather than
    leaving it to Python's stable-sort input-order accident -- proven by
    sorting the same two candidates in both possible input orders and
    getting the identical result either way."""
    a = _candidate("AAA", pick_score=50.0, raw_decision_utility=2.0, marginal_utility=10.0)
    b = _candidate("BBB", pick_score=50.0, raw_decision_utility=2.0, marginal_utility=10.0)
    assert sorted([a, b], key=_candidate_sort_key) == [a, b]
    assert sorted([b, a], key=_candidate_sort_key) == [a, b]
    assert sorted([b, a], key=_candidate_sort_key) == [a, b]
