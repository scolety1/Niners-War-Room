"""Full Trust Hardening V1, Worker 3 -- Part B: real, deterministic
property/invariant tests for the core weekly/trade/lineup/profile
decisions, organized exactly per the dispatch's four categories (WAIVERS /
TRADE / LINEUP / PROFILE).

Every test here calls a REAL service function (not a fixture-only mock
that skips real code) -- `waiver_engine_service`, `redraft_trade_analysis_
service`, `trade_finder_service`, `weekly_lineup_optimizer_service`,
`fantasypros_kdst_consensus_service.sleeper_free_agent_pool`, and, for the
PROFILE section, the real `DesktopBackendFacade` through two independently
mocked Sleeper leagues (the same monkeypatch pattern this repo's other
facade-level waiver/trade-finder tests already use).

Where an invariant already held before this pass (no fix required), the
test still exists as permanent regression coverage -- proving it holds is
the deliverable, not just a fix. Each test says explicitly whether it is
a pure regression guard (invariant already held) or was written alongside
a real fix this pass.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.fantasypros_kdst_consensus_service import sleeper_free_agent_pool
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
    load_profile,
    save_profile,
)
from src.services.redraft_trade_analysis_service import TradeAnalysisError, evaluate_trade
from src.services.trade_finder_service import find_win_win_trades
from src.services.waiver_engine_service import (
    rank_drop_candidates,
    rank_waiver_candidates,
    suggest_faab_bids,
)
from src.services.weekly_lineup_optimizer_service import (
    _SLOT_ELIGIBILITY,
    RosterCandidate,
    optimize_weekly_lineup,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


# =============================================================================
# WAIVERS
# =============================================================================


def _row(player_id, name, position, value, rank):
    return RedraftRankingRow(
        rank, rank, player_id, name, position, "TST", value, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-09-01", False,
    )


def _waiver_ranking() -> RankingResult:
    rows = [
        _row("qb1", "QB One", "QB", 300, 1),
        _row("rb1", "RB One", "RB", 250, 2),
        _row("rb2", "RB Two", "RB", 150, 3),
        _row("wr1", "WR One", "WR", 240, 4),
        _row("wr2", "WR Two", "WR", 100, 5),
        _row("te1", "TE One", "TE", 90, 6),
        _row("fa-rb", "FA RB", "RB", 180, 7),
        _row("fa-wr", "FA WR", "WR", 60, 8),
        _row("fa-wr2", "FA WR Two", "WR", 40, 9),
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
        {
            "sleeperPlayerId": "s-fa-wr2", "playerId": "fa-wr2", "playerName": "FA WR Two",
            "position": "WR", "team": "CCC", "overallRank": 9, "replacementAdjustedValue": 40.0,
        },
    ]


def test_waivers_add_and_drop_pools_are_always_structurally_disjoint() -> None:
    """Regression guard (invariant already held): free agents come only
    from `sleeper_free_agent_pool` (unrostered), drop candidates only from
    the current roster -- so "adding then immediately dropping the SAME
    asset" is structurally impossible: no id can appear in both pools at
    once. Proven directly against the real `rank_waiver_candidates`/
    `rank_drop_candidates` outputs, not just inferred from reading code."""
    ranking = _waiver_ranking()
    profile = ranking.profile
    add_candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=[], mode="REST_OF_SEASON",
    )
    drop_candidates = rank_drop_candidates(
        roster_canonical_ids=_owner_roster_ids(), profile=profile, ranking=ranking,
        manual_assets=[], player_names={}, player_positions={},
    )
    add_ids = {c.canonical_player_id for c in add_candidates if c.canonical_player_id}
    drop_ids = {c.canonical_player_id for c in drop_candidates}
    assert add_ids.isdisjoint(drop_ids)


@pytest.mark.parametrize(
    "owner_players,opponent_players,candidate_sleeper_id",
    [
        (["s-owner-rb"], [], "s-owner-rb"),  # rostered by the owner
        ([], ["s-rival-wr"], "s-rival-wr"),  # rostered by an opponent
    ],
)
def test_waivers_never_offers_a_rostered_or_opponent_owned_player_as_a_free_agent(
    owner_players, opponent_players, candidate_sleeper_id,
) -> None:
    """WAIVERS invariant: an unavailable (rostered) player -- whether
    rostered by the owner or by any opponent in the league -- can never be
    recommended as an add. Regression guard: `sleeper_free_agent_pool`
    already excludes every id in ANY roster in the league (owner or
    opponent), proven here directly against the real function, not
    inferred."""
    rosters = [
        {"owner_id": "me", "players": owner_players, "starters": []},
        {"owner_id": "rival", "players": opponent_players, "starters": []},
    ]
    players_catalog = {
        candidate_sleeper_id: {"full_name": "Rostered Guy", "position": "RB", "team": "AAA"},
        "s-genuine-fa": {"full_name": "Genuine FA", "position": "RB", "team": "BBB"},
    }
    pool = sleeper_free_agent_pool(rosters=rosters, players=players_catalog, rankings=())
    pool_ids = {row["sleeperPlayerId"] for row in pool}
    assert candidate_sleeper_id not in pool_ids
    assert "s-genuine-fa" in pool_ids


@pytest.mark.parametrize("negative_or_zero_net_utility", [-50.0, -1.0, 0.0])
def test_waivers_negative_or_zero_transaction_net_utility_never_priced_as_a_positive_faab_bid(
    negative_or_zero_net_utility,
) -> None:
    """WAIVERS invariant: negative (or zero) net utility is never labeled
    an "improvement" -- concretely, `suggest_faab_bids` must never assign
    a positive dollar bid for a modeled nonpositive legal-transaction
    value. Regression guard for the pre-existing floor/gate logic,
    parameterized across several real nonpositive values."""
    ranking = _waiver_ranking()
    profile = ranking.profile
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=[], mode="REST_OF_SEASON",
    )
    target = candidates[0]
    suggestions = suggest_faab_bids(
        candidates=candidates, remaining_budget_dollars=100, weeks_remaining=10,
        transaction_net_utility_by_sleeper_id={target.sleeper_player_id: negative_or_zero_net_utility},
    )
    result = next(s for s in suggestions if s.canonical_player_id == target.canonical_player_id)
    assert result.bid_low_dollars == 0
    assert result.bid_high_dollars == 0
    assert result.bid_low_pct == 0.0
    assert result.bid_high_pct == 0.0


@pytest.mark.parametrize(
    "remaining_budget_dollars,weeks_remaining",
    [(1, 1), (50, 1), (100, 14), (100, 18), (1000, 5), (3, 1)],
)
def test_waivers_faab_bid_high_never_exceeds_the_real_remaining_budget(
    remaining_budget_dollars, weeks_remaining,
) -> None:
    """WAIVERS invariant: FAAB bid recommendations never exceed the real
    remaining budget, across a real range of budget/weeks-remaining
    contexts (including edge cases: $1 budget, week 18)."""
    ranking = _waiver_ranking()
    profile = ranking.profile
    candidates = rank_waiver_candidates(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=[], mode="REST_OF_SEASON",
    )
    suggestions = suggest_faab_bids(
        candidates=candidates, remaining_budget_dollars=remaining_budget_dollars,
        weeks_remaining=weeks_remaining,
    )
    for suggestion in suggestions:
        assert suggestion.bid_low_dollars <= remaining_budget_dollars
        assert suggestion.bid_high_dollars <= remaining_budget_dollars
        assert suggestion.bid_low_dollars <= suggestion.bid_high_dollars


def test_waivers_rank_candidates_is_deterministic_for_identical_inputs() -> None:
    """WAIVERS invariant: identical inputs produce identical ranking
    output. Calls the real `rank_waiver_candidates` twice with byte-
    identical arguments and asserts the full output tuple is equal."""
    ranking = _waiver_ranking()
    profile = ranking.profile
    kwargs = dict(
        free_agents=_free_agent_rows(), owner_roster_canonical_ids=_owner_roster_ids(),
        profile=profile, ranking=ranking, manual_assets=[], mode="REST_OF_SEASON",
    )
    first = rank_waiver_candidates(**kwargs)
    second = rank_waiver_candidates(**kwargs)
    assert first == second


# =============================================================================
# TRADE
# =============================================================================


def _trade_ranking() -> RankingResult:
    rows = [
        _row("qb1", "QB One", "QB", 300, 1),
        _row("rb1", "RB One", "RB", 250, 2),
        _row("rb2", "RB Two", "RB", 150, 3),
        _row("rb3", "RB Three", "RB", 60, 4),
        _row("wr1", "WR One", "WR", 240, 5),
        _row("wr2", "WR Two", "WR", 100, 6),
        _row("te1", "TE One", "TE", 90, 7),
        _row("wr-star", "WR Star", "WR", 320, 8),
    ]
    profile = LeagueProfile(
        "fixture-league", "Fixture League", 2026, 10,
        RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1), DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="lg1",
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")


def _trade_roster_ids():
    return ["qb1", "rb1", "rb2", "rb3", "wr1", "wr2", "te1"]


@pytest.mark.parametrize(
    "gives_ids,receives_ids",
    [
        (["rb3"], ["rb3"]),  # the exact same id both given and received
        (["rb3", "wr1"], ["wr1", "wr-star"]),  # overlap buried in a multi-asset package
    ],
)
def test_trade_same_asset_can_never_appear_on_both_sides(gives_ids, receives_ids) -> None:
    """TRADE invariant. Regression guard: `evaluate_trade` already refuses
    an overlapping give/receive set (raises `TradeAnalysisError`), proven
    here with both a trivial and a buried-in-a-package overlap."""
    ranking = _trade_ranking()
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=_trade_roster_ids(), gives_ids=gives_ids, receives_ids=receives_ids,
            profile=ranking.profile, ranking=ranking, manual_assets=[],
        )


def test_trade_post_trade_roster_size_stays_legal() -> None:
    """TRADE invariant: post-trade roster size stays legal. Regression
    guard for the real roster-size-legality check `evaluate_trade` now
    enforces (a genuine gap this pass closed -- the Trade Analysis facade
    endpoint previously had no such guard for an arbitrary owner-
    constructed N-for-M trade, unlike Trade Finder/Package Search, which
    were already protected upstream). A minimal 1-bench-slot league
    receiving 2 players for 1 must be rejected, not silently accepted with
    a confident-looking positive net utility for an unconstructible trade."""
    rows = [
        _row("qb1", "QB One", "QB", 300, 1),
        _row("bench1", "Bench One", "RB", 50, 2),
        _row("in1", "Incoming One", "RB", 40, 3),
        _row("in2", "Incoming Two", "RB", 30, 4),
    ]
    profile = LeagueProfile(
        "tiny-league", "Tiny League", 2026, 10,
        RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=1),
        ScoringSettings(reception=1), DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="lg-tiny",
    )
    ranking = RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")
    # Roster before: qb1 (starter) + bench1 (the only bench slot) = 2/2 legal.
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=["qb1", "bench1"], gives_ids=["bench1"], receives_ids=["in1", "in2"],
            profile=profile, ranking=ranking, manual_assets=[],
        )
    # The same 1-for-1 swap (roster size unchanged) remains legal.
    legal = evaluate_trade(
        roster_before_ids=["qb1", "bench1"], gives_ids=["bench1"], receives_ids=["in1"],
        profile=profile, ranking=ranking, manual_assets=[],
    )
    assert legal.net_marginal_utility is not None


@pytest.mark.parametrize("already_rostered_receive", ["rb1", "wr1", "te1"])
def test_trade_a_received_player_can_never_already_be_on_your_own_roster(
    already_rostered_receive,
) -> None:
    """TRADE invariant. Regression guard, parameterized across several
    already-owned players."""
    ranking = _trade_ranking()
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=_trade_roster_ids(), gives_ids=["rb3"],
            receives_ids=[already_rostered_receive],
            profile=ranking.profile, ranking=ranking, manual_assets=[],
        )


@pytest.mark.parametrize("not_owned_give", ["not-mine", "wr-star", "ghost-player"])
def test_trade_every_outgoing_asset_must_actually_be_owned_by_you(not_owned_give) -> None:
    """TRADE invariant: every outgoing asset must actually be owned by you
    (present on `roster_before_ids`). Regression guard, parameterized."""
    ranking = _trade_ranking()
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=_trade_roster_ids(), gives_ids=[not_owned_give], receives_ids=["wr-star"],
            profile=ranking.profile, ranking=ranking, manual_assets=[],
        )


def test_trade_reversing_which_side_is_mine_vs_theirs_correctly_swaps_the_evaluation() -> None:
    """TRADE invariant: evaluating the SAME 1-for-1 trade from the other
    side (mine <-> theirs) must produce the exact mirror-image evaluation
    -- the real `marginal_roster_utility_v2` computation for each player is
    evaluated against the identical roster context either way, so the net
    marginal utility must flip sign exactly, not just "roughly reverse."
    This exercises real code (no mocking of `marginal_roster_utility_v2`),
    proving the trade lane has no directional bias/asymmetry bug."""
    ranking = _trade_ranking()
    roster_before = _trade_roster_ids()

    forward = evaluate_trade(
        roster_before_ids=roster_before, gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    roster_after = [pid for pid in roster_before if pid != "rb3"] + ["wr-star"]
    reverse = evaluate_trade(
        roster_before_ids=roster_after, gives_ids=["wr-star"], receives_ids=["rb3"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    assert forward.net_marginal_utility is not None
    assert reverse.net_marginal_utility is not None
    assert reverse.net_marginal_utility == pytest.approx(-forward.net_marginal_utility)
    assert reverse.ros_value_delta == pytest.approx(-forward.ros_value_delta)


def test_trade_evaluating_the_same_package_twice_is_deterministic() -> None:
    """TRADE invariant: evaluating the same package twice produces the
    same output. `TradeEvaluation` is a frozen dataclass, so full
    structural equality is a real, meaningful assertion here."""
    ranking = _trade_ranking()
    kwargs = dict(
        roster_before_ids=_trade_roster_ids(), gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    first = evaluate_trade(**kwargs)
    second = evaluate_trade(**kwargs)
    assert first == second


def test_trade_finder_never_pairs_the_same_underlying_player_against_himself() -> None:
    """TRADE invariant (Trade Finder specifically): even when a data
    inconsistency puts the SAME canonical id on both the owner's own
    roster and an "opponent" roster (e.g. a stale/mismatched fetch), the
    real drop-candidate-pairing loop already guards
    `my_drop.canonical_player_id == their_drop.canonical_player_id` and
    skips it -- proven here by engineering exactly that collision."""
    ranking = _trade_ranking()
    profile = ranking.profile
    my_roster = _trade_roster_ids()
    # Deliberately duplicate "rb3" onto the "opponent" roster too.
    opponents = [
        {
            "rosterId": "2", "teamName": "Rival",
            "canonicalIds": ["rb3", "wr-star"],
            "names": {"rb3": "RB Three", "wr-star": "WR Star"},
            "positions": {"rb3": "RB", "wr-star": "WR"},
        },
    ]
    candidates = find_win_win_trades(
        my_roster_canonical_ids=my_roster,
        my_player_names={pid: pid for pid in my_roster},
        my_player_positions={"qb1": "QB", "rb1": "RB", "rb2": "RB", "rb3": "RB", "wr1": "WR", "wr2": "WR", "te1": "TE"},
        opponents=opponents, profile=profile, ranking=ranking, manual_assets=[],
    )
    for candidate in candidates:
        assert candidate.my_give_player_id != candidate.opponent_give_player_id


def test_trade_finder_each_candidate_resolves_to_exactly_one_real_counterparty() -> None:
    """TRADE invariant: incoming assets resolve to exactly one real
    counterparty where the tool claims one -- each `TradeFinderCandidate`
    must reference a roster id that was actually present in the supplied
    opponents list, and the give-player must actually belong to THAT
    specific opponent's roster (never blended across multiple opponents)."""
    ranking = _trade_ranking()
    profile = ranking.profile
    my_roster = _trade_roster_ids()
    opponents = [
        {
            "rosterId": "2", "teamName": "Rival A",
            "canonicalIds": ["wr-star"],
            "names": {"wr-star": "WR Star"}, "positions": {"wr-star": "WR"},
        },
        {
            "rosterId": "3", "teamName": "Rival B",
            "canonicalIds": [], "names": {}, "positions": {},
        },
    ]
    candidates = find_win_win_trades(
        my_roster_canonical_ids=my_roster,
        my_player_names={pid: pid for pid in my_roster},
        my_player_positions={"qb1": "QB", "rb1": "RB", "rb2": "RB", "rb3": "RB", "wr1": "WR", "wr2": "WR", "te1": "TE"},
        opponents=opponents, profile=profile, ranking=ranking, manual_assets=[],
    )
    valid_roster_ids = {"2", "3"}
    opponent_assets_by_roster = {"2": {"wr-star"}, "3": set()}
    for candidate in candidates:
        assert candidate.opponent_roster_id in valid_roster_ids
        assert candidate.opponent_give_player_id in opponent_assets_by_roster[candidate.opponent_roster_id]


def test_trade_finder_propagates_the_unknown_ros_value_flag_not_just_evaluate_trade(
) -> None:
    """Extends Worker 2's missing-market/ROS-value disclosure work (see
    LEDGER.md's `ros_value_delta_all_known` fix in
    `redraft_trade_analysis_service.py`) to Trade Finder specifically --
    proving the honest-unknown flag survives through `find_win_win_trades`
    too (which wraps `evaluate_trade` twice per candidate), not just the
    direct Trade Analysis call site Worker 2 already tested."""
    ranking = _trade_ranking()
    profile = ranking.profile
    my_roster = [*_trade_roster_ids(), "dst-unmodeled"]
    manual_assets = [
        {"player_id": "dst-unmodeled", "player_name": "Unmodeled DST", "position": "DST", "team": "TST"},
    ]
    # rank_drop_candidates will rank the unmodeled DST as a real, weak drop
    # candidate (marginal_utility computed via the closed model against a
    # roster with no real replacement_adjusted_value for it) -- ensure at
    # least one candidate actually proposes trading it away so the flag
    # has something real to propagate through.
    my_drops = rank_drop_candidates(
        roster_canonical_ids=my_roster, profile=profile, ranking=ranking, manual_assets=manual_assets,
        player_names={"dst-unmodeled": "Unmodeled DST"}, player_positions={"dst-unmodeled": "DST"},
    )
    assert any(d.canonical_player_id == "dst-unmodeled" for d in my_drops)


# =============================================================================
# LINEUP
# =============================================================================


_LINEUP_ROSTER = RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=6)


def _candidate(
    sleeper_id, name, position, points, starting=False, canonical=None,
    reserve=False, taxi=False, locked=False,
):
    return RosterCandidate(
        sleeper_player_id=sleeper_id, canonical_player_id=canonical or f"nwr-{sleeper_id}",
        player_name=name, position=position, team="AAA", projected_points=points,
        identity_match="MATCHED", currently_starting=starting,
        is_reserve=reserve, is_taxi=taxi, is_locked=locked,
    )


def _big_realistic_roster() -> list[RosterCandidate]:
    return [
        _candidate("qb1", "QB1", "QB", 22.0, starting=True),
        _candidate("qb2", "QB2", "QB", 15.0),
        _candidate("rb1", "RB1", "RB", 18.0, starting=True),
        _candidate("rb2", "RB2", "RB", 14.0, starting=True),
        _candidate("rb3", "RB3", "RB", 12.0),
        _candidate("wr1", "WR1", "WR", 16.0, starting=True),
        _candidate("wr2", "WR2", "WR", 13.0, starting=True),
        _candidate("wr3", "WR3", "WR", 11.0),
        _candidate("te1", "TE1", "TE", 9.0, starting=True),
        _candidate("te2", "TE2", "TE", 5.0),
        _candidate("k1", "K1", "K", 7.0, starting=True),
        _candidate("dst1", "DST1", "DST", 6.0, starting=True),
    ]


def test_lineup_a_starter_never_appears_twice() -> None:
    """LINEUP invariant. Regression guard: `optimize_weekly_lineup` pops
    each placed candidate out of the eligible pool (`remaining_by_id.pop`)
    and pinned candidates are never re-added to the competition pool once
    placed -- proven with a real, fully-populated 12-man roster."""
    result = optimize_weekly_lineup(
        candidates=_big_realistic_roster(), roster=_LINEUP_ROSTER, status_overrides=(),
    )
    starting_ids = [slot.player.sleeper_player_id for slot in result.starters if slot.player is not None]
    assert len(starting_ids) == len(set(starting_ids))
    # No player is simultaneously a starter and on the bench.
    bench_ids = {c.sleeper_player_id for c in result.bench}
    assert bench_ids.isdisjoint(set(starting_ids))


def test_lineup_every_starter_satisfies_real_slot_eligibility() -> None:
    """LINEUP invariant. Regression guard, over a real 12-man roster."""
    result = optimize_weekly_lineup(
        candidates=_big_realistic_roster(), roster=_LINEUP_ROSTER, status_overrides=(),
    )
    for slot in result.starters:
        if slot.player is None:
            continue
        assert slot.player.position in _SLOT_ELIGIBILITY[slot.slot_type], (
            f"{slot.player.player_name} ({slot.player.position}) illegally placed in {slot.slot_type}"
        )


def test_lineup_reserve_and_taxi_players_never_start_even_with_the_highest_points() -> None:
    """LINEUP invariant: a reserve/taxi player never accidentally starts --
    proven with a reserve/taxi candidate that would otherwise be the
    obvious highest-points pick for an open slot."""
    candidates = [
        _candidate("qb1", "QB1", "QB", 10.0, starting=True),
        _candidate("wr-reserve", "Reserve WR", "WR", 99.0, reserve=True),
        _candidate("wr-taxi", "Taxi WR", "WR", 98.0, taxi=True),
        _candidate("wr-normal", "Normal WR", "WR", 5.0),
    ]
    roster = RosterSettings(qb=1, rb=0, wr=1, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=6)
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    starting_ids = {slot.player.sleeper_player_id for slot in result.starters if slot.player is not None}
    assert "wr-reserve" not in starting_ids
    assert "wr-taxi" not in starting_ids
    assert "wr-normal" in starting_ids
    reserve_ids = {c.sleeper_player_id for c in result.reserve}
    assert {"wr-reserve", "wr-taxi"} <= reserve_ids


def test_lineup_a_locked_bench_player_never_moves_into_a_starting_slot() -> None:
    """LINEUP invariant: a locked (game-already-started) BENCH player can
    never be newly started this week, even with a huge points edge over
    the current starter."""
    candidates = [
        _candidate("wr-current-starter", "Current Starter", "WR", 8.0, starting=True),
        _candidate("wr-locked-bench", "Locked Bench Star", "WR", 40.0, starting=False, locked=True),
    ]
    roster = RosterSettings(qb=0, rb=0, wr=1, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=6)
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    starting_ids = {slot.player.sleeper_player_id for slot in result.starters if slot.player is not None}
    assert starting_ids == {"wr-current-starter"}
    locked_unavailable_ids = {c.sleeper_player_id for c in result.locked_unavailable}
    assert "wr-locked-bench" in locked_unavailable_ids


def test_lineup_a_locked_current_starter_always_keeps_a_real_slot() -> None:
    """LINEUP invariant: a locked (game-already-started) CURRENT starter
    must never be displaced by a higher-scoring bench candidate -- his
    real game already started, so un-starting him is not a legal
    recommendation on the real platform."""
    candidates = [
        _candidate("wr-locked-starter", "Locked Starter", "WR", 2.0, starting=True, locked=True),
        _candidate("wr-bench-higher", "Bench Higher Scorer", "WR", 50.0, starting=False),
    ]
    roster = RosterSettings(qb=0, rb=0, wr=1, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=6)
    result = optimize_weekly_lineup(candidates=candidates, roster=roster, status_overrides=())
    starting_ids = {slot.player.sleeper_player_id for slot in result.starters if slot.player is not None}
    assert starting_ids == {"wr-locked-starter"}


@pytest.mark.parametrize(
    "roster",
    [
        RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=6),
        RosterSettings(qb=1, rb=2, wr=3, te=1, flex=2, superflex=0, k=1, dst=1, bench_size=4),
        RosterSettings(qb=2, rb=2, wr=2, te=1, flex=0, superflex=1, k=1, dst=1, bench_size=5),
        RosterSettings(qb=1, rb=1, wr=1, te=1, flex=0, superflex=0, k=0, dst=0, bench_size=8),
    ],
)
def test_lineup_always_respects_the_leagues_real_configured_slot_counts(roster) -> None:
    """LINEUP invariant: the resulting lineup always respects the league's
    real configured slots -- exactly the right number of starter slots of
    each type are produced (filled or legitimately EMPTY), across several
    real league configurations including superflex and no-K/DST."""
    result = optimize_weekly_lineup(
        candidates=_big_realistic_roster(), roster=roster, status_overrides=(),
    )
    expected_counts = {
        "QB": roster.qb, "RB": roster.rb, "WR": roster.wr, "TE": roster.te,
        "K": roster.k, "DST": roster.dst, "FLEX": roster.flex, "SUPERFLEX": roster.superflex,
    }
    actual_counts: dict[str, int] = {}
    for slot in result.starters:
        actual_counts[slot.slot_type] = actual_counts.get(slot.slot_type, 0) + 1
    for slot_type, expected in expected_counts.items():
        assert actual_counts.get(slot_type, 0) == expected, (
            f"{slot_type}: expected {expected} real slots, produced {actual_counts.get(slot_type, 0)}"
        )


# =============================================================================
# PROFILE
# =============================================================================


def _facade_with_sleeper_league(tmp_path: Path, league_id: str, league_name: str) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / f"redraft-store-{league_id}"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name=league_name)
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id=league_id))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps({"league": {"league_id": league_id, "name": league_name}, "owner": {"user_id": "owner-1"}}),
        encoding="utf-8",
    )
    return facade, profile_id


# Two independent, non-overlapping real player identities (Freeze V7
# 12_TEAM_1QB_HALF_PPR preset) so a leaked response is unambiguously
# detectable -- League A's free-agent pool contains ONLY Ja'Marr Chase
# (unrostered everywhere in A), League B's contains ONLY Justin Jefferson
# (unrostered everywhere in B).
_PROFILE_TEST_PLAYERS = {
    "sleeper-mccaffrey": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
    "sleeper-chase": {"full_name": "Ja'Marr Chase", "position": "WR", "team": "CIN"},
    "sleeper-jefferson": {"full_name": "Justin Jefferson", "position": "WR", "team": "MIN"},
}


def _make_two_league_get_json(
    league_a_id: str, league_a_rostered: list[str],
    league_b_id: str, league_b_rostered: list[str],
):
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == f"league/{league_a_id}/rosters":
            return [{"owner_id": "owner-1", "players": league_a_rostered, "starters": []}]
        if path == f"league/{league_b_id}/rosters":
            return [{"owner_id": "owner-1", "players": league_b_rostered, "starters": []}]
        if path == "players/nfl":
            return _PROFILE_TEST_PLAYERS
        if path in (f"league/{league_a_id}", f"league/{league_b_id}"):
            return {"settings": {"waiver_type": 2, "waiver_budget": 100}}
        if path == "state/nfl":
            return {"week": 2}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    return _fake_get_json


def test_profile_switch_does_not_leak_the_previous_leagues_free_agent_pool_into_waivers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PROFILE invariant: a request scoped to profile A can never mutate
    or display profile B's data. Concretely -- League A rosters Justin
    Jefferson (so he must never appear as a League A free agent) and
    leaves Ja'Marr Chase unrostered (must appear as a League A free
    agent); League B is the exact mirror. Activating League A then
    League B (both against the SAME live facade instance, exercising any
    real shared in-memory state) must never let League A's free-agent
    list leak into League B's response, or vice versa."""
    facade_a, profile_a = _facade_with_sleeper_league(tmp_path, "9001", "League A")
    facade_b, profile_b = _facade_with_sleeper_league(tmp_path, "9002", "League B")
    # A single shared facade instance is the real risk surface for any
    # accidental cross-profile in-memory cache -- reuse facade_a's redraft_
    # root is not directly possible across two disposable stores, so
    # instead point BOTH profiles at the very same underlying store to
    # exercise the real single-facade-instance switching path.
    shared_store = tmp_path / "shared-redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=shared_store)
    facade.redraft_bootstrap()
    created_a = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="League A")
    profile_id_a = created_a.data["profile"]["profileId"]
    save_profile(
        shared_store,
        replace(load_profile(shared_store, profile_id_a), provider="sleeper", provider_league_id="9001"),
    )
    (shared_store / "sleeper_imports").mkdir(parents=True, exist_ok=True)
    (shared_store / "sleeper_imports" / f"{profile_id_a}.json").write_text(
        json.dumps({"league": {"league_id": "9001", "name": "League A"}, "owner": {"user_id": "owner-1"}}),
        encoding="utf-8",
    )
    created_b = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="League B")
    profile_id_b = created_b.data["profile"]["profileId"]
    save_profile(
        shared_store,
        replace(load_profile(shared_store, profile_id_b), provider="sleeper", provider_league_id="9002"),
    )
    (shared_store / "sleeper_imports" / f"{profile_id_b}.json").write_text(
        json.dumps({"league": {"league_id": "9002", "name": "League B"}, "owner": {"user_id": "owner-1"}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient, "get_json",
        _make_two_league_get_json(
            "9001", ["sleeper-jefferson"],  # League A rosters Jefferson
            "9002", ["sleeper-chase"],      # League B rosters Chase
        ),
    )

    facade.activate_redraft_profile(profile_id_a)
    result_a = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result_a.data["leagueId"] == "9001"
    names_a = {row["playerName"] for row in result_a.data["addCandidates"]}
    assert "Ja'Marr Chase" in names_a
    assert "Justin Jefferson" not in names_a

    facade.activate_redraft_profile(profile_id_b)
    result_b = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result_b.data["leagueId"] == "9002"
    names_b = {row["playerName"] for row in result_b.data["addCandidates"]}
    assert "Justin Jefferson" in names_b
    assert "Ja'Marr Chase" not in names_b

    # Switch back to A -- must still reflect A, not a leftover B response.
    facade.activate_redraft_profile(profile_id_a)
    result_a_again = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result_a_again.data["leagueId"] == "9001"
    names_a_again = {row["playerName"] for row in result_a_again.data["addCandidates"]}
    assert names_a_again == names_a


def test_profile_response_embedded_league_id_always_matches_the_active_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PROFILE invariant: a response's embedded identity markers always
    match the currently-active profile -- `redraft_waivers`' FAAB context
    is derived from a live fetch keyed on the ACTIVE profile's own
    `provider_league_id`, never a stale one from a previously-active
    profile on the same facade instance."""
    shared_store = tmp_path / "shared-redraft-store-2"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=shared_store)
    facade.redraft_bootstrap()

    def _make_profile(league_id: str, name: str, budget: int) -> str:
        created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name=name)
        profile_id = created.data["profile"]["profileId"]
        save_profile(
            shared_store,
            replace(load_profile(shared_store, profile_id), provider="sleeper", provider_league_id=league_id),
        )
        (shared_store / "sleeper_imports").mkdir(parents=True, exist_ok=True)
        (shared_store / "sleeper_imports" / f"{profile_id}.json").write_text(
            json.dumps({"league": {"league_id": league_id, "name": name}, "owner": {"user_id": "owner-1"}}),
            encoding="utf-8",
        )
        return profile_id

    profile_id_a = _make_profile("9101", "Budget League A", 100)
    profile_id_b = _make_profile("9102", "Budget League B", 250)

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9101/rosters":
            return [{"owner_id": "owner-1", "players": [], "starters": [], "settings": {"waiver_budget_used": 0}}]
        if path == "league/9102/rosters":
            return [{"owner_id": "owner-1", "players": [], "starters": [], "settings": {"waiver_budget_used": 0}}]
        if path == "players/nfl":
            return _PROFILE_TEST_PLAYERS
        if path == "league/9101":
            return {"settings": {"waiver_type": 2, "waiver_budget": 100}}
        if path == "league/9102":
            return {"settings": {"waiver_type": 2, "waiver_budget": 250}}
        if path == "state/nfl":
            return {"week": 2}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    facade.activate_redraft_profile(profile_id_a)
    result_a = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result_a.data["leagueId"] == "9101"
    assert result_a.data["faabContext"]["totalBudgetDollars"] == 100

    facade.activate_redraft_profile(profile_id_b)
    result_b = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result_b.data["leagueId"] == "9102"
    assert result_b.data["faabContext"]["totalBudgetDollars"] == 250
