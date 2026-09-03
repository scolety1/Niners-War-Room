"""Tests for the SHADOW/RESEARCH Team Score, Championship Equity, and
Pick Score prototypes. None of this exercises or changes production
ranking -- see src/services/shadow_numeric_authorities_service.py's
module docstring.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.services.redraft_draft_room_v1_service import _asset_pool
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.shadow_numeric_authorities_service import (
    ChampionshipEquityAssumptions,
    RosterPlayer,
    championship_equity,
    cost_of_waiting,
    optimal_starting_lineup_value,
    pick_score,
    simulate_comparable_leagues,
    team_score,
)


def _ranking(team_count: int = 10, rounds: int = 15) -> RankingResult:
    rows: list[RedraftRankingRow] = []
    for position, count in (("QB", 30), ("RB", 80), ("WR", 100), ("TE", 30)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank,
                    index + 1,
                    f"{position}-{index}",
                    f"{position} {index}",
                    position,
                    "TST",
                    400 - rank,
                    0,
                    400 - rank,
                    0,
                    "HIGH" if index < 10 else "MEDIUM",
                    1 + (rank - 1) // 20,
                    "fixture",
                    "Fixture",
                    "GOVERNED",
                    "AVAILABLE",
                    "2026-08-17",
                    False,
                    position_tier=1 + index // 12,
                )
            )
    profile = LeagueProfile(
        "fixture-league",
        "Fixture League",
        2026,
        team_count,
        RosterSettings(k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1),
        DraftContext(rounds=rounds, draft_slot=9),
        practical_mode=True,
        provider="sleeper",
        provider_league_id="1312983576827920384",
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _manual_assets() -> list[dict[str, str]]:
    return [
        {
            "player_id": f"manual:{position}:{index}",
            "player_name": f"{position} {index}",
            "position": position,
            "team": f"T{index}",
        }
        for position in ("K", "DST")
        for index in range(12)
    ]


def _empty_adp(profile: LeagueProfile):
    from src.services.redraft_draft_room_v1_service import AdpSnapshot

    return AdpSnapshot(profile.profile_id, "", "ppr", profile.team_count, "", "", "", (), ())


def test_optimal_starting_lineup_value_fills_required_slots_then_flex_with_the_best_remaining() -> (
    None
):
    profile = _ranking().profile  # qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1
    players = [
        RosterPlayer("qb1", "QB", 50.0),
        RosterPlayer("qb2", "QB", 10.0),  # bench QB, never starts (qb=1)
        RosterPlayer("rb1", "RB", 40.0),
        RosterPlayer("rb2", "RB", 30.0),
        RosterPlayer("rb3", "RB", 25.0),  # best remaining RB/WR/TE -> FLEX
        RosterPlayer("wr1", "WR", 35.0),
        RosterPlayer("wr2", "WR", 20.0),
        RosterPlayer("te1", "TE", 15.0),
        RosterPlayer("k1", "K", 0.0),
        RosterPlayer("dst1", "DST", 0.0),
    ]
    value = optimal_starting_lineup_value(players, profile)
    # QB1 + RB1 + RB2 + WR1 + WR2 + TE1 + FLEX(RB3) + K + DST
    expected = 50 + 40 + 30 + 35 + 20 + 15 + 25 + 0 + 0
    assert value == expected


def test_optimal_starting_lineup_value_handles_superflex() -> None:
    profile = replace(
        _ranking().profile,
        roster=RosterSettings(
            qb=1, rb=1, wr=1, te=1, flex=0, superflex=1, k=0, dst=0, bench_size=6
        ),
    )
    players = [
        RosterPlayer("qb1", "QB", 60.0),
        RosterPlayer("qb2", "QB", 55.0),  # best remaining eligible for superflex
        RosterPlayer("rb1", "RB", 30.0),
        RosterPlayer("wr1", "WR", 25.0),
        RosterPlayer("te1", "TE", 10.0),
    ]
    value = optimal_starting_lineup_value(players, profile)
    assert value == 60 + 30 + 25 + 10 + 55


def test_team_score_percentile_is_consistent_with_a_synthetic_population() -> None:
    ranking = _ranking()
    profile = ranking.profile
    pool = _asset_pool(ranking, _manual_assets())
    # A synthetic 3-league population where we know the exact value distribution.
    comparable = [
        {
            1: [RosterPlayer("a", "QB", v) for v in [100.0]],
            2: [RosterPlayer("b", "QB", v) for v in [50.0]],
        }
    ]
    # Sidestep optimal_starting_lineup_value's slot filtering by using a
    # profile with qb=1 and nothing else required, so both single-QB
    # "rosters" score exactly their QB's value.
    thin_profile = replace(
        profile, roster=RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, k=0, dst=0, bench_size=0)
    )
    result = team_score(
        ["QB-0"], thin_profile, ranking, _manual_assets(), comparable_leagues=comparable
    )
    assert result.population_size == 2
    # QB-0 is rank 1 overall -> highest possible replacement_adjusted_value
    # in this fixture, so it must exceed both synthetic comparables (100, 50).
    assert result.percentile == 100.0
    assert result.label == "TEAM SCORE — RESEARCH"
    assert pool  # sanity: pool actually built


def test_team_score_from_a_real_simulated_population_is_a_real_percentile(tmp_path) -> None:
    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, _manual_assets(), adp, trials=3, base_seed=1
    )
    assert len(leagues) == 3
    assert all(len(league) == profile.team_count for league in leagues)
    # The single best possible roster (top starters by rank) must land at
    # or near the top of a real simulated population, not an arbitrary
    # fixed number.
    best_possible_ids = [
        "QB-0",
        "RB-0",
        "RB-1",
        "WR-0",
        "WR-1",
        "TE-0",
        "RB-2",
        "manual:K:0",
        "manual:DST:0",
    ]
    best_result = team_score(
        best_possible_ids, profile, ranking, _manual_assets(), comparable_leagues=leagues
    )
    assert best_result.percentile >= 50.0
    assert 0.0 <= best_result.percentile <= 100.0
    assert best_result.population_size == 10 * 3


def test_championship_equity_returns_a_bounded_probability_with_monte_carlo_error(tmp_path) -> None:
    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    leagues = simulate_comparable_leagues(
        profile, ranking, _manual_assets(), adp, trials=1, base_seed=7
    )
    league = leagues[0]
    target_ids = [player.player_id for player in league[1]]
    result = championship_equity(
        target_ids,
        profile,
        ranking,
        _manual_assets(),
        comparable_league=league,
        target_team_slot=1,
        seasons=50,
        base_seed=7,
    )
    assert 0.0 <= result.win_probability <= 1.0
    assert result.standard_error >= 0.0
    assert result.seasons_simulated == 50
    assert result.league_size == profile.team_count
    assert result.label == "CHAMPIONSHIP EQUITY — SIMULATED RESEARCH"


def test_championship_equity_strong_roster_beats_weak_roster_in_expectation() -> None:
    """Not a calibration claim -- just a sanity check that plugging in a
    much stronger roster increases simulated win probability relative to
    a much weaker one, holding the rest of the league fixed. Uses real
    ranked player IDs for the target (target_player_ids resolves through
    the real asset pool, unlike the fixed-value RosterPlayer objects used
    for the other three teams below)."""
    ranking = _ranking(team_count=4, rounds=1)
    profile = replace(
        ranking.profile,
        team_count=4,
        roster=RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, k=0, dst=0, bench_size=0),
    )
    # QB-0 (rank 1, value 399) vs TE-29 (rank 240, value 160) in this fixture.
    other_teams = {
        2: [RosterPlayer("weak_b", "QB", 10.0)],
        3: [RosterPlayer("weak_c", "QB", 10.0)],
        4: [RosterPlayer("weak_d", "QB", 10.0)],
    }
    strong_result = championship_equity(
        ["QB-0"],
        profile,
        ranking,
        _manual_assets(),
        comparable_league={**other_teams, 1: []},
        target_team_slot=1,
        seasons=200,
        base_seed=3,
    )
    weak_result = championship_equity(
        ["TE-29"],
        profile,
        ranking,
        _manual_assets(),
        comparable_league={**other_teams, 1: []},
        target_team_slot=1,
        seasons=200,
        base_seed=3,
    )
    assert strong_result.win_probability > weak_result.win_probability


def test_pick_score_ranks_candidates_relative_to_each_other_only() -> None:
    from src.services.shadow_numeric_authorities_service import (
        ChampionshipEquityResult,
        TeamScoreResult,
    )

    candidates = {
        "best": (
            TeamScoreResult(
                percentile=90.0,
                roster_value=100,
                population_size=10,
                population_mean=50,
                population_median=50,
                population_stdev=5,
            ),
            ChampionshipEquityResult(
                win_probability=0.30, standard_error=0.01, seasons_simulated=100, league_size=10
            ),
        ),
        "middle": (
            TeamScoreResult(
                percentile=60.0,
                roster_value=80,
                population_size=10,
                population_mean=50,
                population_median=50,
                population_stdev=5,
            ),
            ChampionshipEquityResult(
                win_probability=0.15, standard_error=0.01, seasons_simulated=100, league_size=10
            ),
        ),
        "worst": (
            TeamScoreResult(
                percentile=30.0,
                roster_value=60,
                population_size=10,
                population_mean=50,
                population_median=50,
                population_stdev=5,
            ),
            ChampionshipEquityResult(
                win_probability=0.05, standard_error=0.01, seasons_simulated=100, league_size=10
            ),
        ),
    }
    scored = pick_score(candidates)
    assert scored["best"].relative_score == 100.0
    assert scored["worst"].relative_score == 0.0
    assert 0.0 < scored["middle"].relative_score < 100.0
    assert scored["best"].label == "RESEARCH_ONLY_PICK_SCORE"
    # cost_of_waiting for the best candidate is its edge over the next-best alternative
    assert scored["best"].cost_of_waiting == pytest.approx(90.0 - 60.0)
    assert scored["worst"].cost_of_waiting == 0.0  # not the best -> no positive edge to lose


def test_pick_score_handles_a_single_candidate_without_dividing_by_zero() -> None:
    from src.services.shadow_numeric_authorities_service import (
        ChampionshipEquityResult,
        TeamScoreResult,
    )

    only = {
        "solo": (
            TeamScoreResult(
                percentile=70.0,
                roster_value=80,
                population_size=10,
                population_mean=50,
                population_median=50,
                population_stdev=5,
            ),
            ChampionshipEquityResult(
                win_probability=0.2, standard_error=0.01, seasons_simulated=100, league_size=10
            ),
        ),
    }
    scored = pick_score(only)
    assert scored["solo"].relative_score == 50.0  # no spread -> defined midpoint, not a crash


def test_cost_of_waiting_is_nonnegative_and_zero_when_already_the_best() -> None:
    assert cost_of_waiting(80.0, 60.0) == 20.0
    assert cost_of_waiting(60.0, 80.0) == 0.0  # never negative


def test_champ_equity_assumptions_are_disclosed_not_silent() -> None:
    assumptions = ChampionshipEquityAssumptions()
    assert assumptions.regular_season_weeks > 0
    assert "disclosed simplifying" in assumptions.note
