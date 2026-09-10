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
