from __future__ import annotations

import pytest

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.shadow_numeric_authorities_service import marginal_roster_utility_v2
from src.services.waiver_engine_service import (
    FAAB_URGENCY_TIER,
    WaiverCandidate,
    describe_unmatched_roster_players,
    pair_add_drop,
    rank_drop_candidates,
    rank_waiver_candidates,
    resolve_roster_canonical_ids,
    suggest_faab_bids,
)
from src.services.weekly_projection_service import WeeklyProjectionRow


def _row(player_id, name, position, value, rank):
    return RedraftRankingRow(
        rank, rank, player_id, name, position, "TST", value, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-09-01", False,
    )


def _ranking() -> RankingResult:
    rows = [
        _row("qb1", "QB One", "QB", 300, 1),
        _row("rb1", "RB One", "RB", 250, 2),
        _row("rb2", "RB Two", "RB", 150, 3),
        _row("wr1", "WR One", "WR", 240, 4),
        _row("wr2", "WR Two", "WR", 100, 5),
        _row("te1", "TE One", "TE", 90, 6),
        # Free agents (not on any roster in these tests)
        _row("fa-rb", "FA RB", "RB", 180, 7),
        _row("fa-wr", "FA WR", "WR", 60, 8),
    ]
    profile = LeagueProfile(
        "fixture-league", "Fixture League", 2026, 10,
        RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1), DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="lg1",
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")


def _manual_assets():
    return []


def _owner_roster_ids():
    return ["qb1", "rb1", "rb2", "wr1", "wr2", "te1"]


def _free_agent_rows():
    return [
        {
            "sleeperPlayerId": "s-fa-rb", "playerId": "fa-rb", "playerName": "FA RB",
            "position": "RB", "team": "AAA", "overallRank": 7, "replacementAdjustedValue": 180.0,
        },
        {
            "sleeperPlayerId": "s-fa-wr", "playerId": "fa-wr", "playerName": "FA WR",
            "position": "WR", "team": "BBB", "overallRank": 8, "replacementAdjustedValue": 60.0,
        },
        {
            "sleeperPlayerId": "s-unmatched", "playerId": "", "playerName": "Unmatched Guy",
            "position": "TE", "team": "CCC", "overallRank": None, "replacementAdjustedValue": None,
        },
    ]


def test_rest_of_season_mode_ranks_by_real_marginal_utility_and_reports_unmatched() -> None:
    ranking = _ranking()
    profile = ranking.profile
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    assert len(candidates) == 3
    by_id = {c.sleeper_player_id: c for c in candidates}
    assert by_id["s-unmatched"].identity_status == "UNMATCHED_IDENTITY"
    assert by_id["s-unmatched"].marginal_utility is None
    # matched candidates must rank ahead of the unmatched one (never guessed a value)
    matched_positions = [i for i, c in enumerate(candidates) if c.identity_status == "MATCHED"]
    unmatched_position = next(i for i, c in enumerate(candidates) if c.identity_status == "UNMATCHED_IDENTITY")
    assert all(pos < unmatched_position for pos in matched_positions)


def test_this_week_mode_requires_real_weekly_data_or_raises() -> None:
    ranking = _ranking()
    with pytest.raises(ValueError):
        rank_waiver_candidates(
            free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
            profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="THIS_WEEK",
        )


def test_this_week_mode_uses_real_weekly_points_as_tiebreak() -> None:
    ranking = _ranking()
    weekly = {
        "s-fa-rb": WeeklyProjectionRow(
            canonical_player_id="fa-rb", sleeper_player_id="s-fa-rb", player_name="FA RB",
            position="RB", team="AAA", week=1, season=2026, season_type="regular", league_id="lg1",
            source="SLEEPER_WEEKLY_PROJECTIONS_V1", source_as_of="x", projected_points=11.0,
            scoring_context="NWR_LEAGUE_SCORING", raw_stats={}, identity_match="MATCHED", gp=1.0,
        ),
    }
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="THIS_WEEK",
        weekly_projections_by_sleeper_id=weekly,
    )
    fa_rb = next(c for c in candidates if c.sleeper_player_id == "s-fa-rb")
    assert fa_rb.weekly_projected_points == 11.0
    fa_wr = next(c for c in candidates if c.sleeper_player_id == "s-fa-wr")
    assert fa_wr.weekly_projected_points is None  # honestly missing, not fabricated


# NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix) -- governing
# brief's regression fixture 7: "utilities 10 vs 9 and weekly points 1 vs 20
# sort the 1-point player first in THIS_WEEK (buggy). A season-derived
# becomesStarter value is unchanged by weekly projections (buggy). Fix must
# sort by real weekly-usable gain and recompute becomesStarter from a real
# weekly evaluation." This fixture's own two real free agents (`fa-rb`,
# `fa-wr`) have real, computed season marginal utilities of 180.0 and 60.0
# respectively (fa-rb strictly higher) -- the same qualitative shape as the
# brief's illustrative "10 vs 9" -- with weekly points set to 1.0 vs 20.0 to
# match the brief's own numbers exactly.
def _this_week_weekly_rows() -> dict[str, WeeklyProjectionRow]:
    return {
        "s-fa-rb": WeeklyProjectionRow(
            canonical_player_id="fa-rb", sleeper_player_id="s-fa-rb", player_name="FA RB",
            position="RB", team="AAA", week=1, season=2026, season_type="regular", league_id="lg1",
            source="SLEEPER_WEEKLY_PROJECTIONS_V1", source_as_of="x", projected_points=1.0,
            scoring_context="NWR_LEAGUE_SCORING", raw_stats={}, identity_match="MATCHED", gp=1.0,
        ),
        "s-fa-wr": WeeklyProjectionRow(
            canonical_player_id="fa-wr", sleeper_player_id="s-fa-wr", player_name="FA WR",
            position="WR", team="BBB", week=1, season=2026, season_type="regular", league_id="lg1",
            source="SLEEPER_WEEKLY_PROJECTIONS_V1", source_as_of="x", projected_points=20.0,
            scoring_context="NWR_LEAGUE_SCORING", raw_stats={}, identity_match="MATCHED", gp=1.0,
        ),
    }


def test_regression_fixture_7a_this_week_without_a_real_impact_map_falls_back_to_season_utility_ordering() -> None:
    """The exact buggy ordering the brief's fixture reproduced is still a
    real, reachable, HONEST fallback path (never fabricated) when the
    caller has not computed a real weekly-lineup-gain evaluation --
    `rank_waiver_candidates`'s own docstring discloses this. The next test
    (7b) proves the real fix once the facade's real evaluation is
    supplied."""
    ranking = _ranking()
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="THIS_WEEK",
        weekly_projections_by_sleeper_id=_this_week_weekly_rows(),
        # No `this_week_impact_by_sleeper_id` -- the pre-W5-fix code path.
    )
    fa_rb = next(c for c in candidates if c.sleeper_player_id == "s-fa-rb")
    fa_wr = next(c for c in candidates if c.sleeper_player_id == "s-fa-wr")
    assert fa_rb.marginal_utility == 180.0
    assert fa_wr.marginal_utility == 60.0
    assert fa_rb.weekly_projected_points == 1.0
    assert fa_wr.weekly_projected_points == 20.0
    # Buggy-documented ordering: season utility dominates -- the real
    # 1-point fa-rb still sorts ahead of the real 20-point fa-wr.
    order = [c.sleeper_player_id for c in candidates]
    assert order.index("s-fa-rb") < order.index("s-fa-wr")


def test_regression_fixture_7b_this_week_with_a_real_impact_map_sorts_by_actual_usable_lineup_gain() -> None:
    """The real fix: once a real, evaluated weekly-lineup-gain map is
    supplied (as the facade now computes via `weekly_lineup_optimizer_
    service.simulate_this_week_add_drop`), THIS_WEEK ranking is PRIMARILY
    ordered by real usable gain, not season marginal utility -- the
    lower-season-utility, higher-weekly-points fa-wr now correctly sorts
    ahead of fa-rb."""
    from src.services.weekly_lineup_optimizer_service import ThisWeekAddDropImpact

    ranking = _ranking()
    impact_map = {
        # fa-rb: real season utility 180.0, but a REAL weekly evaluation
        # says he does not crack the actual starting lineup this week
        # (e.g. every real RB/FLEX slot is already better-occupied) --
        # near-zero real usable gain.
        "s-fa-rb": ThisWeekAddDropImpact(
            baseline_projected_total=100.0, after_projected_total=100.5, gain=0.5, becomes_starter=False
        ),
        # fa-wr: real season utility only 60.0, but a REAL weekly
        # evaluation says he DOES start this week and meaningfully
        # improves the real lineup total.
        "s-fa-wr": ThisWeekAddDropImpact(
            baseline_projected_total=100.0, after_projected_total=115.0, gain=15.0, becomes_starter=True
        ),
    }
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="THIS_WEEK",
        weekly_projections_by_sleeper_id=_this_week_weekly_rows(),
        this_week_impact_by_sleeper_id=impact_map,
    )
    order = [c.sleeper_player_id for c in candidates]
    # THE FIX: fa-wr (real gain 15.0) now sorts strictly ahead of fa-rb
    # (real gain 0.5), reversing the buggy fixture-7a ordering above even
    # though fa-rb still has the higher SEASON utility.
    assert order.index("s-fa-wr") < order.index("s-fa-rb")

    fa_rb = next(c for c in candidates if c.sleeper_player_id == "s-fa-rb")
    fa_wr = next(c for c in candidates if c.sleeper_player_id == "s-fa-wr")
    assert fa_rb.this_week_lineup_gain == 0.5
    assert fa_wr.this_week_lineup_gain == 15.0
    # THE FIX for the second half of fixture 7: `this_week_becomes_starter`
    # is the real, independently-recomputed weekly answer, genuinely
    # different from (and never silently defaulted to) the season-long
    # `becomes_starter` flag both these candidates share (both `True` under
    # the season model -- see the real values printed by
    # `marginal_roster_utility_v2` for this exact fixture).
    assert fa_rb.becomes_starter is True  # unchanged season-long flag
    assert fa_rb.this_week_becomes_starter is False  # real, independently recomputed
    assert fa_rb.this_week_evaluated is True
    assert fa_wr.this_week_becomes_starter is True
    assert fa_wr.this_week_evaluated is True


def test_regression_fixture_7c_a_candidate_outside_the_impact_map_is_honestly_not_evaluated_never_defaulted() -> None:
    """`this_week_becomes_starter`/`this_week_lineup_gain` must be `None`
    -- never silently reused from the season-long flag -- for a real
    candidate this pass did not evaluate (e.g. outside a bounded shortlist)
    even when a real impact map was supplied for OTHER candidates."""
    ranking = _ranking()
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="THIS_WEEK",
        weekly_projections_by_sleeper_id=_this_week_weekly_rows(),
        this_week_impact_by_sleeper_id={},  # supplied, but genuinely empty this pass
    )
    fa_rb = next(c for c in candidates if c.sleeper_player_id == "s-fa-rb")
    assert fa_rb.this_week_evaluated is False
    assert fa_rb.this_week_becomes_starter is None
    assert fa_rb.this_week_lineup_gain is None
    # `becomes_starter` (the season-long flag) is untouched and still real.
    assert fa_rb.becomes_starter is True


def test_drop_candidates_ranked_weakest_first_by_real_marginal_utility() -> None:
    ranking = _ranking()
    names = {"qb1": "QB One", "rb1": "RB One", "rb2": "RB Two", "wr1": "WR One", "wr2": "WR Two", "te1": "TE One"}
    positions = {"qb1": "QB", "rb1": "RB", "rb2": "RB", "wr1": "WR", "wr2": "WR", "te1": "TE"}
    drops = rank_drop_candidates(
        roster_canonical_ids=_owner_roster_ids(), profile=ranking.profile, ranking=ranking,
        manual_assets=_manual_assets(), player_names=names, player_positions=positions,
    )
    assert len(drops) == 6
    utilities = [d.marginal_utility for d in drops if d.marginal_utility is not None]
    assert utilities == sorted(utilities)  # ascending, weakest first


_PAIR_NAMES = {"qb1": "QB One", "rb1": "RB One", "rb2": "RB Two", "wr1": "WR One", "wr2": "WR Two", "te1": "TE One"}
_PAIR_POSITIONS = {"qb1": "QB", "rb1": "RB", "rb2": "RB", "wr1": "WR", "wr2": "WR", "te1": "TE"}


def test_pair_add_drop_computes_real_net_utility_in_the_same_context() -> None:
    """Waiver Night V1, Section 4 fix: the add's value and the drop's value
    must be measured against the SAME roster (the roster with the drop
    already removed), or their difference is meaningless. Before the fix,
    `net_marginal_utility` subtracted the drop's post-drop-roster value from
    the add's ORIGINAL-roster value -- two different reference rosters."""
    ranking = _ranking()
    profile = ranking.profile
    add_candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    drops = rank_drop_candidates(
        roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=_manual_assets(), player_names=_PAIR_NAMES, player_positions=_PAIR_POSITIONS,
    )
    pairings = pair_add_drop(
        add_candidates=add_candidates, drop_candidates=drops,
        owner_roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=_manual_assets(), top_n=3,
    )
    assert len(pairings) == 3
    weakest_drop = drops[0]
    roster_after_drop = [pid for pid in _owner_roster_ids() if pid != weakest_drop.canonical_player_id]
    assert pairings[0].drop is weakest_drop  # always the single weakest real roster piece
    for pairing in pairings:
        assert pairing.drop_required is True
        assert pairing.context_label == "SAME_CONTEXT_MARGINAL_COMPARISON"
        # The add's ORIGINAL-roster value is preserved for transparency, but
        # is no longer what the net is computed from.
        assert pairing.add_utility_vs_original_roster == pairing.add.marginal_utility
        if pairing.add.canonical_player_id and pairing.add.marginal_utility is not None:
            expected_after_drop = marginal_roster_utility_v2(
                pairing.add.canonical_player_id, roster_after_drop, profile, ranking, _manual_assets()
            ).utility
            assert pairing.add_utility_vs_post_drop_roster == expected_after_drop
            assert pairing.drop_utility_vs_post_drop_roster == weakest_drop.marginal_utility
            assert pairing.net_marginal_utility == round(expected_after_drop - weakest_drop.marginal_utility, 2)


def test_pair_add_drop_same_context_fix_genuinely_changes_the_number_when_bench_depth_is_position_scarce() -> None:
    """Concrete, deliberately constructed evidence the mismatch was real and
    the fix actually matters (not just theoretically different): in the
    small 6-player fixture above, every rostered player fills a real
    starter/FLEX slot (7 required, 6 rostered), so removing any one of them
    from context doesn't change any OTHER candidate's bench-depth rate --
    the old and new formulas happen to agree there. This fixture instead
    puts a real bench WR behind a real starter WR, so a free-agent WR add's
    own real bench-depth rate (`FANTASY_BENCH_UTILITY_RATE[10]["WR"]`,
    unmodified/read-only) genuinely differs depending on whether the
    existing bench WR is still on the roster when the add is evaluated --
    exactly the real-world case the directive was concerned about."""
    rows = (
        _row("wr-starter", "WR Starter", "WR", 200.0, 1),
        _row("wr-bench-a", "WR Bench A", "WR", 80.0, 2),
        _row("wr-bench-b", "WR Bench B", "WR", 50.0, 3),
        _row("wr-free-agent", "WR Free Agent", "WR", 70.0, 4),
    )
    profile = LeagueProfile(
        "fixture-league-2", "Fixture League 2", 2026, 10,
        RosterSettings(qb=0, rb=0, wr=1, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=5),
        ScoringSettings(reception=1), DraftContext(rounds=6, draft_slot=1),
        practical_mode=True, provider="sleeper", provider_league_id="lg2",
    )
    ranking = RankingResult(profile, rows, (), (), "2026-09-01T00:00:00+00:00", "fixture-2")
    owner_roster_ids = ["wr-starter", "wr-bench-a", "wr-bench-b"]
    add_candidates = rank_waiver_candidates(
        free_agents=[{
            "sleeperPlayerId": "s-wr-fa", "playerId": "wr-free-agent", "playerName": "WR Free Agent",
            "position": "WR", "team": "ZZZ", "overallRank": 4, "replacementAdjustedValue": 70.0,
        }],
        owner_roster_canonical_ids=owner_roster_ids, profile=profile, ranking=ranking,
        manual_assets=[], mode="REST_OF_SEASON",
    )
    drops = rank_drop_candidates(
        roster_canonical_ids=owner_roster_ids, profile=profile, ranking=ranking, manual_assets=[],
        player_names={"wr-starter": "WR Starter", "wr-bench-a": "WR Bench A", "wr-bench-b": "WR Bench B"},
        player_positions={"wr-starter": "WR", "wr-bench-a": "WR", "wr-bench-b": "WR"},
    )
    weakest_drop = drops[0]
    assert weakest_drop.canonical_player_id == "wr-bench-b"  # the real weakest bench WR

    pairings = pair_add_drop(
        add_candidates=add_candidates, drop_candidates=drops, owner_roster_canonical_ids=owner_roster_ids,
        profile=profile, ranking=ranking, manual_assets=[], top_n=1,
    )
    pairing = pairings[0]
    old_formula_net = round(pairing.add.marginal_utility - weakest_drop.marginal_utility, 2)
    # Real, reproduced evidence the mismatch mattered: the old
    # mismatched-context formula (-3.15) and the new same-context formula
    # (+6.86) don't just differ numerically -- they disagree on SIGN, which
    # could flip whether this pairing looks like a good idea at all.
    assert old_formula_net == -3.15
    assert pairing.net_marginal_utility == 6.86
    assert pairing.net_marginal_utility != old_formula_net
    # Dropping the existing weakest bench WR moves the free agent from real
    # bench depth rank 3 (redundancy 2) to depth rank 2 (redundancy 1) -- a
    # real, higher flex-worthy rate, so the add is worth MORE in the
    # post-drop context than in the original roster's context.
    assert pairing.add_utility_vs_post_drop_roster > pairing.add_utility_vs_original_roster


def test_pair_add_drop_open_slot_available_produces_add_only_pairings() -> None:
    """Section 4 open-slot handling: a real, verified open roster slot means
    no drop is forced -- `drop` is `None`, never a fabricated pairing."""
    ranking = _ranking()
    profile = ranking.profile
    add_candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    drops = rank_drop_candidates(
        roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=_manual_assets(), player_names=_PAIR_NAMES, player_positions=_PAIR_POSITIONS,
    )
    pairings = pair_add_drop(
        add_candidates=add_candidates, drop_candidates=drops,
        owner_roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=_manual_assets(), open_slot_available=True, top_n=3,
    )
    assert len(pairings) == 3
    for pairing in pairings:
        assert pairing.drop is None
        assert pairing.drop_required is False
        assert pairing.context_label == "OPEN_ROSTER_SLOT_ADD_ONLY"
        assert pairing.net_marginal_utility == pairing.add.marginal_utility


@pytest.mark.parametrize("open_slot_available", [False, None])
def test_pair_add_drop_no_open_slot_or_unverified_keeps_the_conservative_forced_drop(
    open_slot_available: bool | None,
) -> None:
    """`False` (verified full roster) and `None` (unverifiable) both take
    the SAME conservative path: keep suggesting the real weakest drop
    rather than ever silently assuming an open slot exists."""
    ranking = _ranking()
    profile = ranking.profile
    add_candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    drops = rank_drop_candidates(
        roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=_manual_assets(), player_names=_PAIR_NAMES, player_positions=_PAIR_POSITIONS,
    )
    pairings = pair_add_drop(
        add_candidates=add_candidates, drop_candidates=drops,
        owner_roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=_manual_assets(), open_slot_available=open_slot_available, top_n=3,
    )
    for pairing in pairings:
        assert pairing.drop is drops[0]
        assert pairing.drop_required is True
        assert pairing.context_label == "SAME_CONTEXT_MARGINAL_COMPARISON"


def test_faab_bids_scale_with_percentile_and_never_fabricate_for_unmatched() -> None:
    ranking = _ranking()
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14, total_budget_dollars=100)
    by_id = {b.canonical_player_id: b for b in bids if b.canonical_player_id}
    unmatched_bid = next(b for b in bids if b.canonical_player_id == "")
    assert unmatched_bid.bid_low_dollars == 0 and unmatched_bid.bid_high_dollars == 0
    # The higher real marginal-utility candidate must get a >= bid range than the lower one.
    fa_rb_bid = by_id["fa-rb"]
    fa_wr_bid = by_id["fa-wr"]
    assert fa_rb_bid.bid_high_dollars >= fa_wr_bid.bid_high_dollars
    for bid in bids:
        assert 0 <= bid.bid_low_dollars <= bid.bid_high_dollars <= 100


def test_faab_bids_taper_late_in_season() -> None:
    ranking = _ranking()
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    early = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14, total_budget_dollars=100)
    late = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=1, total_budget_dollars=100)
    early_rb = next(b for b in early if b.canonical_player_id == "fa-rb")
    late_rb = next(b for b in late if b.canonical_player_id == "fa-rb")
    assert late_rb.bid_high_dollars <= early_rb.bid_high_dollars


def test_faab_rejects_invalid_context() -> None:
    with pytest.raises(ValueError):
        suggest_faab_bids(candidates=(), remaining_budget_dollars=-1, weeks_remaining=5, total_budget_dollars=100)


def _candidate(canonical_id, marginal_utility, becomes_starter) -> WaiverCandidate:
    return WaiverCandidate(
        sleeper_player_id=f"s-{canonical_id}", canonical_player_id=canonical_id,
        player_name=canonical_id, position="RB", team="TST",
        ros_replacement_value=1.0, ros_overall_rank=1, weekly_projected_points=None,
        marginal_utility=marginal_utility, becomes_starter=becomes_starter,
        marginal_utility_explanation="fixture", identity_status="MATCHED",
    )


def test_faab_urgency_uses_the_shared_contracts_high_medium_low_scale() -> None:
    """Regression test for the real, previously-shipping bug where this
    module emitted STARTER_UPGRADE/BENCH_DEPTH/LOW_VALUE while the shared
    contract (`contracts/src/index.ts`'s `faabUrgency` field) and the
    frontend's `FAAB_URGENCY_TONE`/`FAAB_URGENCY_RANK` lookup tables (both
    in the desktop app) only ever recognized HIGH/MEDIUM/LOW -- every real
    urgency badge fell through to a fallback tone and the FAAB tab's
    urgency sort silently did nothing. This test would have caught that
    directly: it asserts the exact contract-facing string values, not just
    that *some* string is present."""

    candidates = (
        _candidate("starter", 5.0, True),
        _candidate("bench", 2.0, False),
        _candidate("low", -1.0, False),
    )
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    by_id = {bid.canonical_player_id: bid for bid in bids}
    assert by_id["starter"].urgency == "HIGH"
    assert by_id["bench"].urgency == "MEDIUM"
    assert by_id["low"].urgency == "LOW"
    # Every real suggestion must use one of the exact 3 contract-facing
    # values -- never the old internal STARTER_UPGRADE/BENCH_DEPTH/LOW_VALUE
    # vocabulary, and never anything else.
    for bid in bids:
        assert bid.urgency in {"HIGH", "MEDIUM", "LOW"}


def test_faab_urgency_tier_maps_every_internal_reason_onto_the_contract_scale() -> None:
    assert FAAB_URGENCY_TIER == {
        "STARTER_UPGRADE": "HIGH",
        "BENCH_DEPTH": "MEDIUM",
        "LOW_VALUE": "LOW",
    }


def test_faab_urgency_for_unmatched_identity_is_the_contracts_low_value() -> None:
    unmatched = WaiverCandidate(
        sleeper_player_id="s-unmatched", canonical_player_id="", player_name="Unmatched",
        position="RB", team="TST", ros_replacement_value=None, ros_overall_rank=None,
        weekly_projected_points=None, marginal_utility=None, becomes_starter=False,
        marginal_utility_explanation="MARGINAL_UTILITY_UNAVAILABLE_UNMATCHED_IDENTITY",
        identity_status="UNMATCHED_IDENTITY",
    )
    bids = suggest_faab_bids(candidates=(unmatched,), remaining_budget_dollars=100, weeks_remaining=14)
    assert bids[0].urgency == "LOW"


def test_resolve_roster_canonical_ids_matches_and_reports_unmatched() -> None:
    ranking_rows = [
        {"playerId": "qb1", "playerName": "QB One", "position": "QB", "team": "AAA"},
        {"playerId": "rb1", "playerName": "RB One", "position": "RB", "team": "AAA"},
    ]
    players_catalog = {
        "s1": {"full_name": "QB One", "position": "QB", "team": "AAA"},
        "s2": {"full_name": "RB One", "position": "RB", "team": "AAA"},
        "s3": {"full_name": "Nobody Matches", "position": "WR", "team": "ZZZ"},
    }
    resolved = resolve_roster_canonical_ids(
        roster_sleeper_player_ids=["s1", "s2", "s3"], players_catalog=players_catalog,
        ranking_rows=ranking_rows,
    )
    assert resolved.canonical_player_ids == ("qb1", "rb1")
    assert resolved.unmatched_sleeper_player_ids == ("s3",)
    assert resolved.player_names_by_canonical_id["qb1"] == "QB One"


# ---------------------------------------------------------------------------
# NWR Full Cycle V1 (Worker 7): "Unresolved roster Sleeper IDs" investigation.
#
# Live-observed on a real Fantasy Gamers roster: "Unresolved roster Sleeper
# IDs: 3451, NE". Investigated against the already-documented Waiver Night
# V1 finding (docs/codex/waiver_night_v1/LEDGER.md, Work Unit 7): both are
# real, catalog-known entries (a K and a DST) whose position simply has zero
# rows in NWR's governed ranking BY DESIGN, not a genuine identity failure.
# `describe_unmatched_roster_players` never changes which ids are matched --
# it only explains the already-computed unmatched list.
# ---------------------------------------------------------------------------


def test_describe_unmatched_roster_players_labels_a_real_kicker_as_out_of_scope() -> None:
    players_catalog = {
        "3451": {"full_name": "Ka'imi Fairbairn", "position": "K", "team": "HOU"},
    }
    described = describe_unmatched_roster_players(["3451"], players_catalog)
    assert len(described) == 1
    item = described[0]
    assert item.sleeper_id == "3451"
    assert item.label == "Ka'imi Fairbairn (K)"
    assert item.category == "OUT_OF_RANKED_MODEL_SCOPE"
    assert "not a bug" not in item.reason.lower()  # honest reason text, not a meta-comment
    assert "governed ranking" in item.reason.lower()


def test_describe_unmatched_roster_players_labels_a_real_team_defense_as_out_of_scope() -> None:
    players_catalog = {
        "NE": {"position": "DEF", "team": "NE"},
    }
    described = describe_unmatched_roster_players(["NE"], players_catalog)
    assert len(described) == 1
    item = described[0]
    assert item.sleeper_id == "NE"
    assert item.label == "NE D/ST (DST)"
    assert item.category == "OUT_OF_RANKED_MODEL_SCOPE"


def test_describe_unmatched_roster_players_flags_a_genuinely_unknown_id() -> None:
    described = describe_unmatched_roster_players(["ghost-id"], {})
    assert len(described) == 1
    item = described[0]
    assert item.sleeper_id == "ghost-id"
    assert item.label == "ghost-id"
    assert item.category == "UNKNOWN_TO_CATALOG"
    assert "no entry" in item.reason.lower()


def test_describe_unmatched_roster_players_flags_a_catalog_known_non_kdst_mismatch_differently() -> None:
    """A skill-position player with a catalog entry that still didn't match
    any governed ranking row (e.g. a genuine identity-join gap) must be
    labeled distinctly from the K/DST scope-boundary case -- never silently
    lumped in with "this is fine by design."""

    players_catalog = {
        "s9": {"full_name": "Some Wideout", "position": "WR", "team": "ZZZ"},
    }
    described = describe_unmatched_roster_players(["s9"], players_catalog)
    assert described[0].category == "UNKNOWN_TO_CATALOG"
    assert described[0].label == "Some Wideout (WR)"


def test_describe_unmatched_roster_players_preserves_order_and_empty_input() -> None:
    assert describe_unmatched_roster_players([], {}) == ()
    players_catalog = {
        "3451": {"full_name": "Ka'imi Fairbairn", "position": "K", "team": "HOU"},
        "NE": {"position": "DEF", "team": "NE"},
    }
    described = describe_unmatched_roster_players(["3451", "NE"], players_catalog)
    assert [item.sleeper_id for item in described] == ["3451", "NE"]


# ---------------------------------------------------------------------------
# NWR Waiver Night V1 (Worker 2): nonpositive-bid gate/floor regression tests.
#
# Bug this section guards against (reproduced live before this fix, against
# the real Fantasy Gamers league's real free-agent pool: real players
# C.J. Stroud (marginal_utility 0.0) and Cooper Kupp (marginal_utility
# -0.26) both received a fabricated positive bid, $28-47 and $28-46
# respectively, purely because `suggest_faab_bids`' percentile/base_low/
# base_high math had no floor at marginal_utility <= 0 -- `base_low = 0.02
# + 0.28 * percentile` is never 0 even at percentile 0). The fix adds a
# gate immediately after percentile is computed: any MATCHED candidate
# with `marginal_utility <= 0` gets a $0/$0 result with a rationale
# distinct from the pre-existing UNMATCHED_IDENTITY $0 case. The
# positive-utility pricing formula itself (percentile -> base_low/
# base_high -> urgency multiplier -> season taper -> dollars) is completely
# untouched for any candidate whose real marginal utility is > 0.
# ---------------------------------------------------------------------------


def test_zero_utility_never_gets_a_positive_bid() -> None:
    candidates = (_candidate("zero", 0.0, False),)
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    bid = bids[0]
    assert bid.bid_low_dollars == 0 and bid.bid_high_dollars == 0
    assert bid.bid_low_pct == 0.0 and bid.bid_high_pct == 0.0
    assert bid.urgency == "LOW"
    assert "modeled nonpositive value" in bid.rationale.lower()


def test_negative_utility_never_gets_a_positive_bid() -> None:
    candidates = (_candidate("neg", -5.0, False),)
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    bid = bids[0]
    assert bid.bid_low_dollars == 0 and bid.bid_high_dollars == 0
    assert bid.bid_low_pct == 0.0 and bid.bid_high_pct == 0.0
    assert bid.urgency == "LOW"


def test_a_negative_utility_candidate_never_gets_a_positive_bid_even_when_it_ranks_first() -> None:
    """The real bug: even a MILDLY negative candidate could out-rank other
    (more negative) candidates in the pool and receive a non-trivial
    percentile -- which the pre-fix formula's `0.02 +` floor turned into a
    positive dollar bid regardless. The gate must fire on the SIGN of the
    utility, not on its rank within the pool."""

    candidates = (_candidate("least_bad", -0.1, False), _candidate("worse", -8.0, False))
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    by_id = {b.canonical_player_id: b for b in bids}
    # least_bad ranks #1 in this 2-candidate pool (percentile 1.0) -- pre-fix
    # this alone was enough to produce a large positive bid.
    assert by_id["least_bad"].percentile_in_pool == 1.0
    assert by_id["least_bad"].bid_low_dollars == 0 and by_id["least_bad"].bid_high_dollars == 0
    assert by_id["worse"].bid_low_dollars == 0 and by_id["worse"].bid_high_dollars == 0


def test_unmatched_identity_never_gets_a_positive_bid() -> None:
    unmatched = WaiverCandidate(
        sleeper_player_id="s-unmatched", canonical_player_id="", player_name="Unmatched",
        position="RB", team="TST", ros_replacement_value=None, ros_overall_rank=None,
        weekly_projected_points=None, marginal_utility=None, becomes_starter=False,
        marginal_utility_explanation="MARGINAL_UTILITY_UNAVAILABLE_UNMATCHED_IDENTITY",
        identity_status="UNMATCHED_IDENTITY",
    )
    bids = suggest_faab_bids(candidates=(unmatched,), remaining_budget_dollars=100, weeks_remaining=14)
    bid = bids[0]
    assert bid.bid_low_dollars == 0 and bid.bid_high_dollars == 0


def test_unmatched_identity_and_nonpositive_utility_read_as_two_different_reasons() -> None:
    """Both are $0, but the directive requires the COPY to distinguish
    'unknown identity' (no signal was ever computed) from 'modeled
    nonpositive value' (a real signal was computed and says not to pay) --
    the two must not collapse into one generic 'no bid' message."""

    unmatched = WaiverCandidate(
        sleeper_player_id="s-u", canonical_player_id="", player_name="Unmatched",
        position="RB", team="TST", ros_replacement_value=None, ros_overall_rank=None,
        weekly_projected_points=None, marginal_utility=None, becomes_starter=False,
        marginal_utility_explanation="MARGINAL_UTILITY_UNAVAILABLE_UNMATCHED_IDENTITY",
        identity_status="UNMATCHED_IDENTITY",
    )
    nonpositive = _candidate("zero_case", 0.0, False)
    bids = suggest_faab_bids(candidates=(unmatched, nonpositive), remaining_budget_dollars=100, weeks_remaining=14)
    by_id = {b.canonical_player_id: b for b in bids}
    unmatched_rationale = by_id[""].rationale.lower()
    nonpositive_rationale = by_id["zero_case"].rationale.lower()
    assert unmatched_rationale != nonpositive_rationale
    assert "identity" in unmatched_rationale
    assert "identity" not in nonpositive_rationale
    assert "modeled" in nonpositive_rationale
    # Neither copy claims the player has no value -- a $0 result must not be
    # read as "this player is worthless."
    assert "does not mean" in unmatched_rationale
    assert "does not mean" in nonpositive_rationale


def test_all_zero_pool_produces_zero_positive_bids_anywhere() -> None:
    candidates = tuple(_candidate(f"z{i}", 0.0, False) for i in range(5))
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    assert len(bids) == 5
    for bid in bids:
        assert bid.bid_low_dollars == 0 and bid.bid_high_dollars == 0


def test_all_negative_pool_produces_zero_positive_bids_anywhere() -> None:
    candidates = tuple(_candidate(f"n{i}", -float(i + 1), False) for i in range(5))
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    assert len(bids) == 5
    for bid in bids:
        assert bid.bid_low_dollars == 0 and bid.bid_high_dollars == 0


def test_mixed_pool_only_positive_utility_candidates_get_a_positive_bid() -> None:
    candidates = (
        _candidate("pos_high", 25.4, True),
        _candidate("pos_mid", 9.72, False),
        _candidate("zero_case", 0.0, False),
        _candidate("neg_case", -5.0, False),
    )
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    by_id = {b.canonical_player_id: b for b in bids}
    assert by_id["pos_high"].bid_low_dollars > 0
    assert by_id["pos_mid"].bid_low_dollars > 0
    assert by_id["zero_case"].bid_low_dollars == 0 and by_id["zero_case"].bid_high_dollars == 0
    assert by_id["neg_case"].bid_low_dollars == 0 and by_id["neg_case"].bid_high_dollars == 0


# ---------------------------------------------------------------------------
# Positive-utility pricing FORMULA characterization tests -- these document
# the existing, UNCHANGED formula's real behavior (per the directive: do
# NOT redesign the curve). They exist so a future worker has a real,
# reproducible baseline before touching this formula, not to lock in any
# claim that the behavior below is ideal.
# ---------------------------------------------------------------------------


def test_characterize_tiny_positive_utility_can_still_price_like_the_pool_leader() -> None:
    """A real formula quirk, not a bug: because pricing is PERCENTILE-of-
    pool (not an absolute-utility curve, which the directive forbids
    inventing), a barely-positive candidate (0.01) that happens to be the
    strongest value in a weak pool prices identically to a much larger
    positive value would in that same slot. Pool composition, not the raw
    utility magnitude, drives the percentile."""

    candidates = (_candidate("tiny", 0.01, False), _candidate("zero", 0.0, False))
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    by_id = {b.canonical_player_id: b for b in bids}
    assert by_id["tiny"].percentile_in_pool == 1.0
    assert by_id["tiny"].bid_low_dollars > 0
    assert by_id["zero"].bid_low_dollars == 0


def test_characterize_tied_utility_values_get_identical_bids_and_top_percentile() -> None:
    """Real, observed tie behavior: `utilities.index(...)` returns the
    FIRST index for a repeated value, so every candidate sharing the same
    marginal_utility gets the SAME rank -> the SAME percentile -> the SAME
    bid range. There is no secondary tiebreak inside this formula (unlike
    `rank_waiver_candidates`' own sort_key, which does have one)."""

    candidates = (_candidate("a", 5.0, False), _candidate("b", 5.0, False), _candidate("c", 5.0, False))
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    percentiles = {b.percentile_in_pool for b in bids}
    dollar_ranges = {(b.bid_low_dollars, b.bid_high_dollars) for b in bids}
    assert percentiles == {1.0}
    assert len(dollar_ranges) == 1


def test_characterize_pool_composition_sensitivity() -> None:
    """Real, observed sensitivity: the SAME candidate (marginal_utility
    5.0) prices very differently depending on which other real candidates
    are in the pool passed to this SAME call -- there is no absolute
    dollar value independent of the pool, by design (percentile-relative,
    not a fixed lookup table)."""

    mid_small_pool = (_candidate("mid", 5.0, False), _candidate("weak", 1.0, False))
    mid_large_pool = (
        _candidate("mid", 5.0, False), _candidate("weak", 1.0, False),
        _candidate("s1", 20.0, False), _candidate("s2", 15.0, False), _candidate("s3", 10.0, False),
    )
    bids_small = suggest_faab_bids(candidates=mid_small_pool, remaining_budget_dollars=100, weeks_remaining=14)
    bids_large = suggest_faab_bids(candidates=mid_large_pool, remaining_budget_dollars=100, weeks_remaining=14)
    mid_small = next(b for b in bids_small if b.canonical_player_id == "mid")
    mid_large = next(b for b in bids_large if b.canonical_player_id == "mid")
    assert mid_small.percentile_in_pool == 1.0
    assert mid_large.percentile_in_pool < mid_small.percentile_in_pool
    assert mid_large.bid_high_dollars < mid_small.bid_high_dollars


def test_characterize_remaining_budget_sensitivity_is_linear_at_fixed_percent() -> None:
    """Real, observed behavior: the PERCENT range for a fixed candidate/
    pool/weeks-remaining is stable across remaining budget -- only the
    resulting dollar amount scales, linearly, with `remaining_budget_dollars`."""

    candidates = (_candidate("x", 5.0, True),)
    results = {
        budget: suggest_faab_bids(candidates=candidates, remaining_budget_dollars=budget, weeks_remaining=14)[0]
        for budget in (10, 50, 100, 200)
    }
    pct_pairs = {(bid.bid_low_pct, bid.bid_high_pct) for bid in results.values()}
    assert len(pct_pairs) == 1  # percent range unchanged across budgets
    assert results[200].bid_high_dollars == 2 * results[100].bid_high_dollars
    assert results[50].bid_high_dollars == round(results[100].bid_high_dollars / 2)


def test_characterize_late_season_taper_has_a_floor_not_a_ramp_to_zero() -> None:
    """Real, observed behavior: `season_taper = min(1.0, max(0.35,
    weeks_remaining / 14.0))` means the bid range shrinks as weeks_remaining
    drops, but never below 35% of its full-season value -- and that floor
    is reached at week <= ~4.9, so weeks_remaining of 4, 2, 1, and 0 all
    produce the IDENTICAL clamped range, not a further ramp toward zero."""

    candidates = (_candidate("y", 5.0, True),)
    by_weeks = {
        weeks: suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=weeks)[0]
        for weeks in (14, 8, 4, 2, 1, 0)
    }
    assert by_weeks[8].bid_high_dollars < by_weeks[14].bid_high_dollars
    assert by_weeks[4].bid_high_dollars < by_weeks[8].bid_high_dollars
    # Floor reached at/below week 4 -- 4, 2, 1, 0 are all identical.
    assert by_weeks[4].bid_high_dollars == by_weeks[2].bid_high_dollars == by_weeks[1].bid_high_dollars == by_weeks[0].bid_high_dollars
    assert by_weeks[4].bid_low_dollars > 0  # a real bench-depth candidate still gets SOME positive range, just tapered
