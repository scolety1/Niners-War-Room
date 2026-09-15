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
from src.services.waiver_engine_service import (
    FAAB_URGENCY_TIER,
    WaiverCandidate,
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


def test_pair_add_drop_computes_real_net_utility() -> None:
    ranking = _ranking()
    profile = ranking.profile
    add_candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    names = {"qb1": "QB One", "rb1": "RB One", "rb2": "RB Two", "wr1": "WR One", "wr2": "WR Two", "te1": "TE One"}
    positions = {"qb1": "QB", "rb1": "RB", "rb2": "RB", "wr1": "WR", "wr2": "WR", "te1": "TE"}
    drops = rank_drop_candidates(
        roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=_manual_assets(), player_names=names, player_positions=positions,
    )
    pairings = pair_add_drop(add_candidates=add_candidates, drop_candidates=drops, top_n=3)
    assert len(pairings) == 3
    assert pairings[0].drop is drops[0]  # always the single weakest real roster piece
    for pairing in pairings:
        if pairing.add.marginal_utility is not None and drops[0].marginal_utility is not None:
            assert pairing.net_marginal_utility == round(pairing.add.marginal_utility - drops[0].marginal_utility, 2)


def test_faab_bids_scale_with_percentile_and_never_fabricate_for_unmatched() -> None:
    ranking = _ranking()
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=_manual_assets(), mode="REST_OF_SEASON",
    )
    bids = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
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
    early = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=14)
    late = suggest_faab_bids(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=1)
    early_rb = next(b for b in early if b.canonical_player_id == "fa-rb")
    late_rb = next(b for b in late if b.canonical_player_id == "fa-rb")
    assert late_rb.bid_high_dollars <= early_rb.bid_high_dollars


def test_faab_rejects_invalid_context() -> None:
    with pytest.raises(ValueError):
        suggest_faab_bids(candidates=(), remaining_budget_dollars=-1, weeks_remaining=5)


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
