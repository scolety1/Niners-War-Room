"""Full Trust Hardening V1 (Worker 3) -- WAIVERS invariant/property tests.

Real, deterministic invariant coverage for `waiver_engine_service.py`, using
the SAME real service functions the live Waivers/Improve-Team surfaces call
(`rank_waiver_candidates`, `rank_drop_candidates`, `pair_add_drop`,
`suggest_faab_bids`) -- never a fixture-only mock that bypasses real code.

Two invariants in this dispatch are already covered by pre-existing,
passing tests and are deliberately NOT duplicated here (see the module
docstring note at the bottom for exactly which, and where):
  * "an unavailable (rostered) player can never be recommended as an add"
    -- `test_waiver_engine_service.py::
    test_a_rostered_player_can_never_be_recommended_as_a_waiver_add` (new
    this pass, a real fix + regression test, see LEDGER.md).
  * "an opponent-owned player can never be recommended" --
    `test_fantasypros_kdst_consensus_service.py::
    test_sleeper_dst_roster_entry_rostered_by_an_opponent_is_not_reported_available`
    and `test_sleeper_free_agent_pool_excludes_rostered_inactive_and_incomplete_rows`
    (pre-existing, re-run this pass, still passing -- `sleeper_free_agent_pool`
    excludes every rostered id across ALL real rosters, not just the
    caller's own).
"""

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
    FaabBidSuggestion,
    WaiverCandidate,
    pair_add_drop,
    rank_drop_candidates,
    rank_waiver_candidates,
    suggest_faab_bids,
)


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
    ]


# --- Add-then-immediately-drop the same asset cannot show net-positive utility ---

def test_add_then_immediately_drop_the_same_asset_nets_exactly_zero() -> None:
    """`marginal_roster_utility_v2` computes a candidate's value against the
    roster it would join/leave. Adding free agent `fa-rb` to the owner's
    roster, then immediately dropping that SAME player back off, must be a
    real no-op transaction -- never net-positive. Both the add-value and the
    drop-value are literally the same call
    (`marginal_roster_utility_v2("fa-rb", owner_roster, ...)`), proven here
    directly against the real function `rank_waiver_candidates`/
    `rank_drop_candidates` both call, not a re-implementation."""
    ranking = _ranking()
    profile = ranking.profile
    owner_roster = _owner_roster_ids()

    add_value = marginal_roster_utility_v2("fa-rb", owner_roster, profile, ranking, []).utility
    roster_with_fa = [*owner_roster, "fa-rb"]
    drop_candidates = rank_drop_candidates(
        roster_canonical_ids=roster_with_fa, profile=profile, ranking=ranking, manual_assets=[],
        player_names={"fa-rb": "FA RB"}, player_positions={"fa-rb": "RB"},
    )
    fa_drop = next(c for c in drop_candidates if c.canonical_player_id == "fa-rb")

    assert add_value is not None and fa_drop.marginal_utility is not None
    net = round(add_value - fa_drop.marginal_utility, 6)
    assert net == 0.0
    assert not (net > 0)


# --- Determinism ---

def test_rank_waiver_candidates_is_deterministic() -> None:
    ranking = _ranking()
    kwargs = dict(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=[], mode="REST_OF_SEASON",
    )
    first = rank_waiver_candidates(**kwargs)
    second = rank_waiver_candidates(**kwargs)
    assert first == second


def test_suggest_faab_bids_is_deterministic() -> None:
    candidates = (
        WaiverCandidate(
            sleeper_player_id="s-a", canonical_player_id="a", player_name="A", position="RB",
            team="TST", ros_replacement_value=100.0, ros_overall_rank=5, weekly_projected_points=None,
            marginal_utility=42.0, becomes_starter=True, marginal_utility_explanation="x",
            identity_status="MATCHED",
        ),
    )
    kwargs = dict(candidates=candidates, remaining_budget_dollars=100, weeks_remaining=10)
    assert suggest_faab_bids(**kwargs) == suggest_faab_bids(**kwargs)


# --- A profile switch cannot preserve the previous league's candidate list ---

def test_rank_waiver_candidates_carries_no_hidden_state_across_calls_for_a_different_profile() -> None:
    """Two consecutive calls for two structurally different leagues/rosters
    (simulating a real profile switch) must be fully independent -- no
    module-level cache/global carries a stale candidate from league A into
    league B's result. `rank_waiver_candidates` is a pure function (no
    caching decorator, no module-level mutable state); this proves that
    property holds in practice, not just by code inspection."""
    ranking_a = _ranking()
    league_a_result = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking_a.profile, ranking=ranking_a, manual_assets=[], mode="REST_OF_SEASON",
    )
    league_a_ids = {c.canonical_player_id for c in league_a_result}
    assert league_a_ids == {"fa-rb", "fa-wr"}

    # League B: entirely different canonical id space, entirely different
    # roster/free-agent pool -- a real "switch profile" simulation.
    b_rows = [
        _row("b-qb1", "B QB1", "QB", 310, 1),
        _row("b-fa-1", "B Free Agent", "RB", 210, 2),
    ]
    profile_b = LeagueProfile(
        "fixture-league-b", "Fixture League B", 2026, 8,
        RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1), DraftContext(rounds=15, draft_slot=3),
        practical_mode=True, provider="sleeper", provider_league_id="lg-b",
    )
    ranking_b = RankingResult(profile_b, tuple(b_rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")
    league_b_result = rank_waiver_candidates(
        free_agents=[
            {"sleeperPlayerId": "s-b-fa-1", "playerId": "b-fa-1", "playerName": "B Free Agent",
             "position": "RB", "team": "ZZZ", "overallRank": 2, "replacementAdjustedValue": 210.0},
        ],
        owner_roster_canonical_ids=["b-qb1"], profile=profile_b, ranking=ranking_b,
        manual_assets=[], mode="REST_OF_SEASON",
    )
    league_b_ids = {c.canonical_player_id for c in league_b_result}
    assert league_b_ids == {"b-fa-1"}
    # No cross-contamination in either direction.
    assert league_a_ids.isdisjoint(league_b_ids)
    # Re-running league A's own exact call afterward still returns exactly
    # its own real candidates -- proves league B's call left no residue.
    rerun_a = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking_a.profile, ranking=ranking_a, manual_assets=[], mode="REST_OF_SEASON",
    )
    assert {c.canonical_player_id for c in rerun_a} == league_a_ids


# --- Negative net utility is never labeled an "improvement" ---

@pytest.mark.parametrize("marginal_utility", [-50.0, -0.01, 0.0])
def test_nonpositive_marginal_utility_never_gets_a_positive_bid_or_high_starter_urgency(
    marginal_utility: float,
) -> None:
    """A candidate whose real, governed marginal utility is zero or negative
    must never receive a positive suggested bid, and must never be tagged
    HIGH (starter-upgrade) urgency -- both would misrepresent a non-
    improvement as one. `suggest_faab_bids`'s nonpositive-utility branch
    returns $0/LOW before the urgency-tier logic is ever reached; this
    proves that holds across the real boundary values, not just one."""
    candidate = WaiverCandidate(
        sleeper_player_id="s-neg", canonical_player_id="neg", player_name="Negative Value Player",
        position="RB", team="TST", ros_replacement_value=10.0, ros_overall_rank=99,
        weekly_projected_points=None, marginal_utility=marginal_utility,
        # becomes_starter True here specifically probes that even a
        # nominal "starter" flag cannot leak a HIGH urgency/positive bid
        # once the real utility itself is nonpositive.
        becomes_starter=True, marginal_utility_explanation="x", identity_status="MATCHED",
    )
    suggestion = suggest_faab_bids(
        candidates=(candidate,), remaining_budget_dollars=200, weeks_remaining=10,
    )[0]
    assert suggestion.bid_low_dollars == 0
    assert suggestion.bid_high_dollars == 0
    assert suggestion.urgency != "HIGH"


# --- FAAB bid recommendations never exceed the real remaining budget ---

@pytest.mark.parametrize("remaining_budget", [1, 2, 25, 37, 100, 250, 1000])
@pytest.mark.parametrize("weeks_remaining", [0, 1, 4, 8, 14, 17])
@pytest.mark.parametrize("marginal_utility", [0.5, 25.0, 100.0, 500.0])
def test_faab_bid_never_exceeds_the_real_remaining_budget(
    remaining_budget: int, weeks_remaining: int, marginal_utility: float,
) -> None:
    # A real percentile-of-pool spread so the pricing formula's percentile
    # term is exercised across its own real range, not just a single point.
    pool = tuple(
        WaiverCandidate(
            sleeper_player_id=f"s-{i}", canonical_player_id=f"p{i}", player_name=f"P{i}",
            position="RB", team="TST", ros_replacement_value=float(i), ros_overall_rank=i,
            weekly_projected_points=None, marginal_utility=float(i * 10), becomes_starter=(i == 4),
            marginal_utility_explanation="x", identity_status="MATCHED",
        )
        for i in range(1, 6)
    ) + (
        WaiverCandidate(
            sleeper_player_id="s-target", canonical_player_id="target", player_name="Target",
            position="RB", team="TST", ros_replacement_value=marginal_utility, ros_overall_rank=1,
            weekly_projected_points=None, marginal_utility=marginal_utility, becomes_starter=True,
            marginal_utility_explanation="x", identity_status="MATCHED",
        ),
    )
    suggestions = suggest_faab_bids(
        candidates=pool, remaining_budget_dollars=remaining_budget, weeks_remaining=weeks_remaining,
    )
    for suggestion in suggestions:
        assert suggestion.bid_low_dollars <= remaining_budget
        assert suggestion.bid_high_dollars <= remaining_budget
        assert suggestion.bid_low_dollars <= suggestion.bid_high_dollars
        assert suggestion.bid_low_dollars >= 0


# --- pair_add_drop: a paired net comparison must be a real, same-context delta ---

def test_pair_add_drop_open_slot_never_pairs_a_phantom_drop() -> None:
    ranking = _ranking()
    add_candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=ranking.profile, ranking=ranking, manual_assets=[], mode="REST_OF_SEASON",
    )
    drop_candidates = rank_drop_candidates(
        roster_canonical_ids=_owner_roster_ids(), profile=ranking.profile, ranking=ranking,
        manual_assets=[], player_names={}, player_positions={},
    )
    pairings = pair_add_drop(
        add_candidates=add_candidates, drop_candidates=drop_candidates,
        owner_roster_canonical_ids=_owner_roster_ids(), profile=ranking.profile, ranking=ranking,
        manual_assets=[], open_slot_available=True,
    )
    for pairing in pairings:
        assert pairing.drop is None
        assert pairing.drop_required is False
        assert pairing.context_label == "OPEN_ROSTER_SLOT_ADD_ONLY"
        assert pairing.net_marginal_utility == pairing.add.marginal_utility
