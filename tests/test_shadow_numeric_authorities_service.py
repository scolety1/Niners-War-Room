"""Tests for the SHADOW/RESEARCH Team Score, Championship Equity, and
Pick Score prototypes. None of this exercises or changes production
ranking -- see src/services/shadow_numeric_authorities_service.py's
module docstring.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.services.ai_intelligence_backend_service import ImpactHypothesis
from src.services.redraft_draft_room_v1_service import AdpEntry, AdpSnapshot, _asset_pool
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
    availability_adjusted_players,
    availability_discount_for_hypotheses,
    championship_equity,
    cost_of_waiting,
    explain_marginal_roster_reason,
    label_pick_decisions,
    optimal_starting_lineup_value,
    pick_score,
    roster_composition_report,
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


def _brute_force_optimal_lineup_value(players: list[RosterPlayer], profile) -> float:
    """Exhaustive reference implementation: try every legal assignment of
    players to starter slots (QB/RB/WR/TE/FLEX/SUPERFLEX) and return the
    best total value. Only tractable for small player pools -- exists
    solely to empirically check the greedy algorithm against ground
    truth, not to replace it."""
    import itertools

    slots: list[str] = (
        ["QB"] * profile.roster.qb
        + ["RB"] * profile.roster.rb
        + ["WR"] * profile.roster.wr
        + ["TE"] * profile.roster.te
        + ["FLEX"] * profile.roster.flex
        + ["SUPERFLEX"] * profile.roster.superflex
    )
    eligibility = {
        "QB": {"QB"}, "RB": {"RB"}, "WR": {"WR"}, "TE": {"TE"},
        "FLEX": {"RB", "WR", "TE"}, "SUPERFLEX": {"QB", "RB", "WR", "TE"},
    }
    best = 0.0
    for combo in itertools.permutations(players, min(len(slots), len(players))):
        total = 0.0
        valid = True
        for slot, player in zip(slots, combo, strict=False):
            if player.position not in eligibility[slot]:
                valid = False
                break
            total += player.value
        if valid:
            best = max(best, total)
    return best


@pytest.mark.parametrize("seed", range(8))
def test_optimal_starting_lineup_value_matches_brute_force_on_small_rosters(seed: int) -> None:
    # Kept deliberately tiny (8 players, 5 slots -> P(8,5) = 6,720
    # candidate assignments) so exhaustive search stays fast; correctness
    # of the exhaustive reference does not depend on pool size.
    import random as _random

    rng = _random.Random(seed)
    profile = replace(
        _ranking().profile,
        roster=RosterSettings(
            qb=1, rb=1, wr=1, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=3
        ),
    )
    positions = ["QB"] * 2 + ["RB"] * 2 + ["WR"] * 2 + ["TE"] * 2
    players = [
        RosterPlayer(f"p{i}", pos, round(rng.uniform(5.0, 100.0), 1))
        for i, pos in enumerate(positions)
    ]
    greedy = optimal_starting_lineup_value(players, profile)
    brute_force = _brute_force_optimal_lineup_value(players, profile)
    assert greedy == pytest.approx(brute_force)


def test_roster_composition_report_flags_starter_holes() -> None:
    profile = replace(
        _ranking().profile,
        roster=RosterSettings(
            qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=6
        ),
    )
    players = [RosterPlayer("qb1", "QB", 50.0), RosterPlayer("rb1", "RB", 40.0)]
    report = roster_composition_report(players, profile)
    assert "RB 1/2" in report.starter_holes
    assert "WR 0/2" in report.starter_holes
    assert "TE 0/1" in report.starter_holes
    assert "K 0/1" in report.starter_holes
    assert "DST 0/1" in report.starter_holes
    assert "QB" not in " ".join(h for h in report.starter_holes if h.startswith("QB "))


def test_roster_composition_report_computes_bench_and_redundancy() -> None:
    profile = replace(
        _ranking().profile,
        roster=RosterSettings(
            qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=2
        ),
    )
    players = [
        RosterPlayer("qb1", "QB", 50.0),
        RosterPlayer("qb2", "QB", 45.0),  # 2nd QB -- pure redundancy, no starter/flex slot uses it
        RosterPlayer("rb1", "RB", 40.0),
        RosterPlayer("rb2", "RB", 35.0),
        RosterPlayer("rb3", "RB", 30.0),  # 3rd RB -- fills FLEX
        RosterPlayer("wr1", "WR", 25.0),
        RosterPlayer("wr2", "WR", 20.0),
        RosterPlayer("te1", "TE", 10.0),
    ]
    report = roster_composition_report(players, profile)
    assert report.starter_holes == ()
    # starters: qb1, rb1, rb2, wr1, wr2, te1, + FLEX(rb3) = 50+40+35+25+20+10+30 = 210
    assert report.starting_lineup_value == pytest.approx(210.0)
    assert report.total_roster_value == pytest.approx(sum(p.value for p in players))
    # bench (2 slots, best remaining by value): qb2 (45) is the single best remaining
    assert report.bench_contingency_value == pytest.approx(45.0)
    assert report.position_redundancy["QB"] == 1  # qb2 fills nothing
    assert report.position_redundancy["RB"] == 0  # rb3 fills the FLEX slot
    assert report.position_redundancy["WR"] == 0
    assert report.position_redundancy["TE"] == 0


def test_explain_marginal_roster_reason_names_the_displaced_starter_on_a_real_upgrade() -> None:
    """NWR post-draft overnight (phase 3/21): the exact real scenario
    reproduced against the live 403 draft (Caleb Williams QB1 rostered,
    Trevor Lawrence recommended as a higher-value QB) -- this is the
    missing explanation, built from the same greedy selection Team Score
    itself already uses, not a new narrative generator."""
    ranking = _ranking()
    profile = replace(
        ranking.profile,
        roster=RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=3),
    )
    # QB-0 has the highest fixture value (rank 1); QB-1 is next-best.
    reason = explain_marginal_roster_reason("QB-1", ["QB-0"], profile, ranking, _manual_assets())
    assert reason.becomes_starter is False  # QB-0 already the better starter; QB-1 stays bench
    assert "bench" in reason.summary.lower()

    # The inverse: a genuinely BETTER QB than the current starter swaps in.
    reason2 = explain_marginal_roster_reason("QB-0", ["QB-1"], profile, ranking, _manual_assets())
    assert reason2.becomes_starter is True
    assert reason2.displaces_player_id == "QB-1"
    assert reason2.starter_value_delta > 0


def test_explain_marginal_roster_reason_fills_an_open_slot_without_displacing_anyone() -> None:
    ranking = _ranking()
    profile = replace(
        ranking.profile,
        roster=RosterSettings(qb=1, rb=0, wr=2, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=3),
    )
    reason = explain_marginal_roster_reason("WR-0", ["QB-0"], profile, ranking, _manual_assets())
    assert reason.becomes_starter is True
    assert reason.displaces_player_id is None
    assert "no one benched" in reason.summary.lower()


def test_marginal_roster_utility_decays_geometrically_for_repeated_bench_adds() -> None:
    """NWR post-draft overnight (phase 3): the QB2/QB3/QB4 diminishing-
    returns shape must emerge from real bench redundancy, not a
    hardcoded position penalty -- same decay rate (0.5 per already-
    rostered bench-redundant player) applies uniformly to any position."""
    ranking = _ranking()
    profile = replace(
        ranking.profile,
        roster=RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, superflex=0, k=0, dst=0, bench_size=5),
    )
    from src.services.shadow_numeric_authorities_service import marginal_roster_utility

    # QB-0 starts (fills the 1 real starter slot).
    r0 = marginal_roster_utility("QB-0", [], profile, ranking, _manual_assets())
    assert r0.becomes_starter is True

    # QB-1 is the first real bench backup -- full undiscounted value.
    r1 = marginal_roster_utility("QB-1", ["QB-0"], profile, ranking, _manual_assets())
    assert r1.becomes_starter is False
    assert r1.bench_redundancy_before == 0
    qb1_value = next(r for r in ranking.rows if r.player_id == "QB-1").replacement_adjusted_value
    assert r1.utility == round(qb1_value, 2)

    # QB-2 is the SECOND bench backup -- discounted to 50% of standalone value.
    r2 = marginal_roster_utility("QB-2", ["QB-0", "QB-1"], profile, ranking, _manual_assets())
    assert r2.becomes_starter is False
    assert r2.bench_redundancy_before == 1
    qb2_value = next(r for r in ranking.rows if r.player_id == "QB-2").replacement_adjusted_value
    assert r2.utility == round(qb2_value * 0.5, 2)

    # QB-3 is the THIRD bench backup -- discounted to 25%.
    r3 = marginal_roster_utility("QB-3", ["QB-0", "QB-1", "QB-2"], profile, ranking, _manual_assets())
    assert r3.bench_redundancy_before == 2
    qb3_value = next(r for r in ranking.rows if r.player_id == "QB-3").replacement_adjusted_value
    assert r3.utility == round(qb3_value * 0.25, 2)

    # Monotonically decreasing utility -- the real diminishing-returns shape.
    assert r1.utility > r2.utility > r3.utility


def test_marginal_roster_utility_te2_stays_full_value_via_flex_not_bench_decay() -> None:
    """The real, reproduced difference from QB: a 2nd TE in a league with
    an open FLEX slot becomes a real starter (FLEX-eligible), so it must
    NOT be bench-decayed the way a 2nd QB (no FLEX eligibility) is."""
    ranking = _ranking()
    profile = replace(
        ranking.profile,
        roster=RosterSettings(qb=0, rb=0, wr=0, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=5),
    )
    from src.services.shadow_numeric_authorities_service import marginal_roster_utility

    te_rows = sorted((r for r in ranking.rows if r.position == "TE"), key=lambda r: r.overall_rank)
    te0, te1 = te_rows[0], te_rows[1]
    r0 = marginal_roster_utility(te0.player_id, [], profile, ranking, _manual_assets())
    assert r0.becomes_starter is True  # fills TE1
    r1 = marginal_roster_utility(te1.player_id, [te0.player_id], profile, ranking, _manual_assets())
    assert r1.becomes_starter is True  # fills the open FLEX slot -- full value, no decay
    assert r1.utility == round(te1.replacement_adjusted_value, 2)


def test_explain_marginal_roster_reason_handles_an_unmodeled_candidate() -> None:
    ranking = _ranking()
    profile = ranking.profile
    reason = explain_marginal_roster_reason("does-not-exist", ["QB-0"], profile, ranking, _manual_assets())
    assert reason.becomes_starter is False
    assert reason.starter_value_delta == 0.0


def _hypothesis(player_id: str, *, direction: str, confidence: str) -> ImpactHypothesis:
    return ImpactHypothesis(
        hypothesis_id=f"h:{player_id}",
        subject_player_id=player_id,
        direction=direction,
        confidence=confidence,
        hypothesis_text="test hypothesis",
        evidence_event_ids=("evt-1",),
        requires_owner_review=False,
        generated_at_utc="2026-08-16T12:05:00+00:00",
    )


def test_availability_discount_zeroes_only_high_confidence_negative_hypotheses() -> None:
    assert availability_discount_for_hypotheses(
        "p1", [_hypothesis("p1", direction="NEGATIVE", confidence="HIGH")]
    ) == 0.0
    assert availability_discount_for_hypotheses(
        "p1", [_hypothesis("p1", direction="NEGATIVE", confidence="MEDIUM")]
    ) == 1.0
    assert availability_discount_for_hypotheses(
        "p1", [_hypothesis("p1", direction="UNCERTAIN", confidence="HIGH")]
    ) == 1.0
    assert availability_discount_for_hypotheses("p1", []) == 1.0
    assert availability_discount_for_hypotheses(
        "p1", [_hypothesis("p2", direction="NEGATIVE", confidence="HIGH")]
    ) == 1.0  # a hypothesis about a different player never affects this one


def test_availability_adjusted_players_zeroes_the_affected_player_only() -> None:
    players = [RosterPlayer("p1", "RB", 50.0), RosterPlayer("p2", "RB", 40.0)]
    hypotheses = [_hypothesis("p1", direction="NEGATIVE", confidence="HIGH")]
    adjusted = availability_adjusted_players(players, hypotheses)
    by_id = {p.player_id: p.value for p in adjusted}
    assert by_id["p1"] == 0.0
    assert by_id["p2"] == 40.0
    # original list is untouched (players are frozen, but confirm no aliasing surprises)
    assert players[0].value == 50.0


def test_availability_adjusted_players_is_a_no_op_with_no_hypotheses() -> None:
    players = [RosterPlayer("p1", "RB", 50.0)]
    assert availability_adjusted_players(players, []) == players


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


def test_team_score_impact_hypotheses_parameter_is_a_no_op_by_default() -> None:
    """NWR post-draft overnight (phase 6): team_score's new optional
    `impact_hypotheses` parameter defaults to `()` -- every existing
    caller must be byte-identical to before this parameter existed."""
    ranking = _ranking()
    profile = ranking.profile
    comparable = [{1: [RosterPlayer("a", "QB", 100.0)], 2: [RosterPlayer("b", "QB", 50.0)]}]
    thin_profile = replace(
        profile, roster=RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, k=0, dst=0, bench_size=0)
    )
    without_param = team_score(["QB-0"], thin_profile, ranking, _manual_assets(), comparable_leagues=comparable)
    with_default = team_score(
        ["QB-0"], thin_profile, ranking, _manual_assets(),
        comparable_leagues=comparable, impact_hypotheses=(),
    )
    assert without_param == with_default


def test_team_score_applies_a_real_high_confidence_negative_impact_hypothesis() -> None:
    """The previously fully-built-but-never-called
    availability_adjusted_players mechanism now actually reaches
    team_score when a caller opts in -- confirmed by an end-to-end drop
    in the resulting roster's simulated strength, not just the standalone
    helper functions this already had unit coverage for."""
    ranking = _ranking()
    profile = ranking.profile
    comparable = [{1: [RosterPlayer("a", "QB", 100.0)], 2: [RosterPlayer("b", "QB", 50.0)]}]
    thin_profile = replace(
        profile, roster=RosterSettings(qb=1, rb=0, wr=0, te=0, flex=0, k=0, dst=0, bench_size=0)
    )
    baseline = team_score(["QB-0"], thin_profile, ranking, _manual_assets(), comparable_leagues=comparable)
    discounted = team_score(
        ["QB-0"], thin_profile, ranking, _manual_assets(), comparable_leagues=comparable,
        impact_hypotheses=[_hypothesis("QB-0", direction="NEGATIVE", confidence="HIGH")],
    )
    assert discounted.roster_value == 0.0
    assert discounted.roster_value < baseline.roster_value
    assert discounted.percentile <= baseline.percentile


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
    # A real spread exists here -- never disclosed as a tie.
    assert all(result.tied_no_spread is False for result in scored.values())


def test_pick_score_discloses_a_genuine_tie_when_every_candidate_shares_the_same_equity() -> None:
    """Owner feedback closure (result-status taxonomy): when every
    candidate's championship_equity win_probability is identical, the
    frozen formula's own `else 50.0` branch fires for all of them --
    tied_no_spread must disclose this as a real, computed tie, not leave
    the UI to guess whether 50.0 means "unevaluated"."""
    from src.services.shadow_numeric_authorities_service import (
        ChampionshipEquityResult,
        TeamScoreResult,
    )

    def _team(percentile: float) -> TeamScoreResult:
        return TeamScoreResult(
            percentile=percentile, roster_value=100, population_size=10,
            population_mean=50, population_median=50, population_stdev=5,
        )

    def _equity() -> ChampionshipEquityResult:
        return ChampionshipEquityResult(
            win_probability=0.10, standard_error=0.01, seasons_simulated=100, league_size=10,
        )

    candidates = {"a": (_team(90.0), _equity()), "b": (_team(30.0), _equity())}
    scored = pick_score(candidates)
    assert scored["a"].relative_score == 50.0
    assert scored["b"].relative_score == 50.0
    assert scored["a"].tied_no_spread is True
    assert scored["b"].tied_no_spread is True


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


# --- Bounded look-ahead (section 12) ---


def test_simulate_pick_now_forces_the_candidate_and_completes_the_draft() -> None:
    from src.services.shadow_numeric_authorities_service import simulate_pick_now

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    final_state = simulate_pick_now(
        profile,
        ranking,
        _manual_assets(),
        adp,
        owner_slot=9,
        candidate_player_id="RB-0",
        seed=11,
    )
    assert len(final_state["picks"]) == profile.team_count * profile.draft.rounds
    owner_picks = [p for p in final_state["picks"] if p["team_slot"] == 9]
    assert any(p["player_id"] == "RB-0" for p in owner_picks)
    forced = next(p for p in owner_picks if p["player_id"] == "RB-0")
    assert forced["selection_behavior"] == "FORCED_CANDIDATE"


def test_simulate_pick_now_rejects_an_already_drafted_candidate() -> None:
    from src.services.shadow_numeric_authorities_service import simulate_pick_now

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    partial = {
        "schema_version": 1,
        "profile_id": profile.profile_id,
        "owner_slot": 9,
        "seed": 1,
        "speed": "FAST",
        "mode": "MOCK",
        "drafted": ["RB-0"],
        "picks": [
            {
                "pick_number": 1,
                "round": 1,
                "team_slot": 1,
                "player_id": "RB-0",
                "player_name": "RB 0",
                "position": "RB",
                "team": "TST",
                "actor": "CPU",
                "selection_behavior": "TEST",
                "nwr_rank": 2,
                "picked_at_utc": "",
            }
        ],
        "updated_at_utc": "",
    }
    with pytest.raises(ValueError, match="already drafted"):
        simulate_pick_now(
            profile,
            ranking,
            _manual_assets(),
            adp,
            owner_slot=9,
            candidate_player_id="RB-0",
            seed=1,
            from_state=partial,
        )


def test_evaluate_pick_candidates_ranks_a_realistic_candidate_set(tmp_path) -> None:
    from src.services.shadow_numeric_authorities_service import evaluate_pick_candidates

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    candidates = ["QB-0", "RB-0", "RB-1", "WR-0"]
    # owner_slot=1 so the owner picks first -- every candidate is
    # guaranteed still available (no CPU turn happens before pick 1).
    scored = evaluate_pick_candidates(
        profile,
        ranking,
        _manual_assets(),
        adp,
        owner_slot=1,
        candidate_player_ids=candidates,
        trials=2,
        seasons=30,
        base_seed=5,
    )
    assert set(scored.keys()) == set(candidates)
    for result in scored.values():
        assert 0.0 <= result.relative_score <= 100.0
        assert result.label == "RESEARCH_ONLY_PICK_SCORE"
    # exactly one candidate should be the strongest of this evaluated set
    assert any(r.relative_score == 100.0 for r in scored.values())


# --- Cost of Waiting V2 (section 15) ---


def _fresh_state(profile: LeagueProfile, owner_slot: int, seed: int = 1) -> dict:
    return {
        "schema_version": 1,
        "profile_id": profile.profile_id,
        "owner_slot": owner_slot,
        "seed": seed,
        "speed": "FAST",
        "mode": "MOCK",
        "drafted": [],
        "picks": [],
        "updated_at_utc": "",
    }


def test_candidate_survival_probability_reflects_how_contested_the_position_is() -> None:
    from src.services.shadow_numeric_authorities_service import candidate_survival_probability

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    state = _fresh_state(profile, owner_slot=1)
    # QB-1 is the 2nd-highest-ranked player in the whole 240-player pool --
    # if the owner takes QB-0 (rank 1) at pick 1 instead, QB-1 is very
    # likely gone by the time the 18 CPU picks (picks 2-19) finish.
    contested = candidate_survival_probability(
        profile, ranking, _manual_assets(), adp, state,
        owner_slot=1, candidate_player_id="QB-1", alternative_player_id="QB-0",
        trials=20, base_seed=1,
    )
    # TE-29 is the very last-ranked player in the pool -- essentially never
    # taken across only 18 CPU picks.
    uncontested = candidate_survival_probability(
        profile, ranking, _manual_assets(), adp, state,
        owner_slot=1, candidate_player_id="TE-29", alternative_player_id="QB-0",
        trials=20, base_seed=1,
    )
    assert 0.0 <= contested <= 1.0
    assert 0.0 <= uncontested <= 1.0
    assert uncontested > contested


def test_candidate_survival_probability_responds_to_real_opponent_position_caps() -> None:
    """Owner feedback closure (Make-It-Back sensitivity audit): the real,
    already-existing position-cap legality check (_roster_candidate_allowed
    -- a team may hold at most max(req.qb + 1, 2) = 2 QBs at the 1QB
    default) genuinely gates CPU pick behavior, not just a cosmetic
    label. A mid-tier QB drafted by NO opponent yet is a live target for
    every team still needing a starter or legal backup; the same
    candidate, once every opponent already holds their legal maximum of
    2 QBs, is structurally impossible for any of them to draft."""
    from src.services.shadow_numeric_authorities_service import candidate_survival_probability

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)

    def _state_with_opponent_qbs(qbs_per_team: int) -> dict:
        picks = []
        drafted = []
        qb_index = 3  # leave QB-0 (alternative) and QB-2 (candidate) untouched
        for team_slot in range(1, profile.team_count + 1):
            if team_slot == 1:  # owner
                continue
            for _ in range(qbs_per_team):
                pid = f"QB-{qb_index}"
                qb_index += 1
                picks.append({
                    "pick_number": len(picks) + 1, "round": 1, "team_slot": team_slot,
                    "player_id": pid, "player_name": pid, "position": "QB", "team": "TST",
                    "actor": "CPU", "selection_behavior": "FIXTURE_SETUP",
                    "nwr_rank": None, "picked_at_utc": "",
                })
                drafted.append(pid)
        return {
            "schema_version": 1, "profile_id": profile.profile_id, "owner_slot": 1,
            "seed": 1, "speed": "FAST", "mode": "MOCK", "drafted": drafted, "picks": picks,
            "updated_at_utc": "",
        }

    uncapped = candidate_survival_probability(
        profile, ranking, [], adp, _state_with_opponent_qbs(0),
        owner_slot=1, candidate_player_id="QB-2", alternative_player_id="QB-0",
        trials=40, base_seed=1,
    )
    capped = candidate_survival_probability(
        profile, ranking, [], adp, _state_with_opponent_qbs(2),
        owner_slot=1, candidate_player_id="QB-2", alternative_player_id="QB-0",
        trials=40, base_seed=1,
    )
    assert uncapped < capped
    assert capped == 1.0  # every opponent is structurally incapable of taking another QB


def test_candidate_survival_probability_responds_to_intervening_pick_count() -> None:
    """A consecutive-snake-turn owner (zero real intervening opponent
    picks between this turn and the next) must show materially higher
    survival than an owner with many intervening picks, for the exact
    same candidate/alternative/league -- the literal number of chances
    for opponents to draft the candidate away is the direct mechanism
    Make-It-Back claims to model."""
    from src.services.shadow_numeric_authorities_service import candidate_survival_probability

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)

    def _fresh(owner_slot: int) -> dict:
        return {
            "schema_version": 1, "profile_id": profile.profile_id, "owner_slot": owner_slot,
            "seed": 1, "speed": "FAST", "mode": "MOCK", "drafted": [], "picks": [],
            "updated_at_utc": "",
        }

    many_intervening = candidate_survival_probability(
        profile, ranking, [], adp, _fresh(1),
        owner_slot=1, candidate_player_id="QB-15", alternative_player_id="QB-0",
        trials=60, base_seed=1,
    )
    # Slot `team_count` picks last in round 1 and first in round 2 (snake) --
    # zero real opponent picks intervene between those two turns.
    zero_intervening = candidate_survival_probability(
        profile, ranking, [], adp, _fresh(profile.team_count),
        owner_slot=profile.team_count, candidate_player_id="QB-15", alternative_player_id="QB-0",
        trials=60, base_seed=1,
    )
    assert zero_intervening > many_intervening
    assert zero_intervening == 1.0


def test_candidate_survival_probability_seeds_and_trials_are_genuinely_consumed() -> None:
    """Owner feedback closure: 'more nominal trials should not be called
    better evidence if the code repeats the same deterministic path.'
    Verify real Monte Carlo variation actually exists -- different base
    seeds at the same trial count must be able to produce different
    survival estimates for a genuinely contested mid-tier candidate
    (not a floor/ceiling-locked one)."""
    from src.services.shadow_numeric_authorities_service import candidate_survival_probability

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    state = {
        "schema_version": 1, "profile_id": profile.profile_id, "owner_slot": 1,
        "seed": 1, "speed": "FAST", "mode": "MOCK", "drafted": [], "picks": [],
        "updated_at_utc": "",
    }
    results = {
        seed: candidate_survival_probability(
            profile, ranking, [], adp, state,
            owner_slot=1, candidate_player_id="QB-15", alternative_player_id="QB-0",
            trials=30, base_seed=seed,
        )
        for seed in (1, 999, 54321)
    }
    # At least one pair of distinct seeds must disagree -- proof the trial
    # loop is not silently repeating one deterministic outcome regardless
    # of how the seed/trial-count knobs are turned.
    assert len(set(results.values())) > 1, results


def test_candidate_survival_probability_now_responds_to_superflex_demand() -> None:
    """Owner feedback closure (Superflex disposition, repaired -- not just
    labeled): a prior pass found and disclosed that Make-It-Back's CPU
    simulation was Superflex-blind (a controlled A/B showed zero
    difference). redraft_draft_room_v1_service.py's _forced_position /
    _roster_need_adjustment / _roster_candidate_allowed now count a real
    Superflex slot as real QB demand, reusing the exact pattern already
    proven for RB/WR/TE/FLEX. This test proves the repair actually
    changed the observable, real Monte Carlo outcome -- not just the
    source code -- for a genuinely contested mid-tier QB."""
    from src.services.shadow_numeric_authorities_service import candidate_survival_probability

    ranking_1qb = _ranking(team_count=10, rounds=15)
    sflx_profile = replace(ranking_1qb.profile, roster=replace(ranking_1qb.profile.roster, superflex=1))
    ranking_sflx = replace(ranking_1qb, profile=sflx_profile)
    adp = _empty_adp(ranking_1qb.profile)

    def _fresh(profile) -> dict:
        return {
            "schema_version": 1, "profile_id": profile.profile_id, "owner_slot": 1,
            "seed": 1, "speed": "FAST", "mode": "MOCK", "drafted": [], "picks": [],
            "updated_at_utc": "",
        }

    survival_1qb = candidate_survival_probability(
        ranking_1qb.profile, ranking_1qb, [], adp, _fresh(ranking_1qb.profile),
        owner_slot=1, candidate_player_id="QB-15", alternative_player_id="QB-0",
        trials=60, base_seed=1,
    )
    survival_sflx = candidate_survival_probability(
        sflx_profile, ranking_sflx, [], adp, _fresh(sflx_profile),
        owner_slot=1, candidate_player_id="QB-15", alternative_player_id="QB-0",
        trials=60, base_seed=1,
    )
    assert survival_sflx < survival_1qb, (survival_sflx, survival_1qb)


def test_candidate_survival_probability_is_one_for_unavailable_inputs() -> None:
    from src.services.shadow_numeric_authorities_service import candidate_survival_probability

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    drafted_state = {**_fresh_state(profile, owner_slot=1), "drafted": ["QB-0"]}
    # candidate already drafted -> nothing left to lose by "waiting"
    assert (
        candidate_survival_probability(
            profile, ranking, _manual_assets(), adp, drafted_state,
            owner_slot=1, candidate_player_id="QB-0", alternative_player_id="RB-0",
            trials=5,
        )
        == 1.0
    )
    # alternative not a real asset -> degenerate-safe default, not a crash
    assert (
        candidate_survival_probability(
            profile, ranking, _manual_assets(), adp, _fresh_state(profile, owner_slot=1),
            owner_slot=1, candidate_player_id="QB-1", alternative_player_id="not-a-real-player",
            trials=5,
        )
        == 1.0
    )


def test_continuation_seeds_default_is_byte_identical_to_the_prior_behavior() -> None:
    """NWR OVERNIGHT (Team-After saturation): continuation_seeds=1 (the
    default, unchanged) must reproduce the exact prior single-seed
    behavior for every existing caller -- this asserts it directly rather
    than assuming it from the diff."""
    from src.services.shadow_numeric_authorities_service import evaluate_pick_candidates

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    candidates = ["QB-0", "QB-1", "RB-0"]
    default_call = evaluate_pick_candidates(
        profile, ranking, _manual_assets(), adp,
        owner_slot=1, candidate_player_ids=candidates, trials=2, seasons=20, base_seed=7,
    )
    explicit_one = evaluate_pick_candidates(
        profile, ranking, _manual_assets(), adp,
        owner_slot=1, candidate_player_ids=candidates, trials=2, seasons=20, base_seed=7,
        continuation_seeds=1,
    )
    assert default_call == explicit_one


def test_continuation_seeds_averages_across_real_seeds_not_just_the_first() -> None:
    """A real, direct proof this widens the sampled continuation rather
    than just relabeling the same single-seed result: with
    continuation_seeds=3, the averaged Team Score must differ from running
    any ONE of those three seeds alone (extraordinarily unlikely to be
    identical by chance across a real Monte Carlo continuation), and must
    equal the real arithmetic mean of the three per-seed values."""
    import statistics

    from src.services.shadow_numeric_authorities_service import (
        championship_equity,
        evaluate_pick_candidates,
        simulate_comparable_leagues,
        simulate_pick_now,
        team_score,
    )

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    manual_assets = _manual_assets()
    candidates = ["QB-0", "RB-0"]
    base_seed = 11
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=base_seed
    )

    averaged = evaluate_pick_candidates(
        profile, ranking, manual_assets, adp,
        owner_slot=1, candidate_player_ids=candidates, comparable_leagues=leagues,
        trials=2, seasons=20, base_seed=base_seed, continuation_seeds=3,
    )

    for candidate in candidates:
        per_seed_percentiles = []
        for offset in range(3):
            final_state = simulate_pick_now(
                profile, ranking, manual_assets, adp,
                owner_slot=1, candidate_player_id=candidate, seed=base_seed + offset,
            )
            owner_ids = [
                str(p["player_id"]) for p in final_state["picks"]
                if int(p["team_slot"]) == 1 and p.get("player_id")
            ]
            per_seed_percentiles.append(
                team_score(
                    owner_ids, profile, ranking, manual_assets, comparable_leagues=leagues
                ).percentile
            )
        expected_mean = round(statistics.fmean(per_seed_percentiles), 1)
        assert averaged[candidate].team_score_after == expected_mean
        # Real evidence this actually averaged rather than just reusing
        # seed 1 alone -- the three per-seed values are not all identical
        # (a genuine Monte Carlo continuation), so the mean provably
        # differs from at least one of them.
        assert len(set(per_seed_percentiles)) > 1, (
            "fixture produced identical results across all 3 seeds -- "
            "cannot prove averaging happened; adjust the fixture"
        )


def test_evaluate_cost_of_waiting_v2_layers_survival_onto_pick_score() -> None:
    from src.services.shadow_numeric_authorities_service import (
        evaluate_cost_of_waiting_v2,
        evaluate_pick_candidates,
    )

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    candidates = ["QB-0", "QB-1", "TE-29"]
    scored = evaluate_pick_candidates(
        profile, ranking, _manual_assets(), adp,
        owner_slot=1, candidate_player_ids=candidates, trials=2, seasons=20, base_seed=5,
    )
    v2 = evaluate_cost_of_waiting_v2(
        profile, ranking, _manual_assets(), adp,
        owner_slot=1, candidate_player_ids=candidates, pick_scores=scored,
        trials=10, base_seed=5,
    )
    assert set(v2) == set(candidates)
    for player_id, result in v2.items():
        assert result.candidate_player_id == player_id
        assert result.best_alternative_player_id in candidates
        assert result.best_alternative_player_id != player_id
        assert 0.0 <= result.survival_probability <= 1.0
        assert result.expected_cost >= 0.0
        # survival-weighting only ever shrinks (or matches) the raw V1 gap
        assert result.expected_cost <= result.value_gap + 1e-9
        assert result.label == "COST_OF_WAITING_V2 — RESEARCH (Monte Carlo survival-weighted)"


def test_evaluate_cost_of_waiting_v2_skips_candidates_with_no_alternative_to_compare() -> None:
    from src.services.shadow_numeric_authorities_service import (
        PickScoreResult,
        evaluate_cost_of_waiting_v2,
    )

    ranking = _ranking(team_count=10, rounds=15)
    profile = ranking.profile
    adp = _empty_adp(profile)
    solo_score = {
        "QB-0": PickScoreResult(
            relative_score=50.0, team_score_after=70.0, championship_equity_after=0.2,
            equity_gain=0.0, cost_of_waiting=0.0,
        )
    }
    v2 = evaluate_cost_of_waiting_v2(
        profile, ranking, _manual_assets(), adp,
        owner_slot=1, candidate_player_ids=["QB-0", "not-scored"], pick_scores=solo_score,
        trials=5,
    )
    # QB-0 has no other candidate to compare against; not-scored isn't in pick_scores
    assert v2 == {}


# --- Real draft cases (section 11): "NWR likes the player" vs "spend
# this pick" ------------------------------------------------------------


def _market_aligned_adp(ranking: RankingResult, overrides: dict[str, float]) -> AdpSnapshot:
    """An ADP snapshot where expected_pick tracks NWR's own overall_rank
    for every player except the ones in `overrides` -- i.e. an
    "efficient market" baseline with specific, deliberate divergences
    (like the real Troy Franklin case: NWR rank 91 vs. real ESPN ADP
    977.0 -- docs/codex/KHA_ANOMALY_INVESTIGATION_20260903.md section 9)
    layered on top, rather than an arbitrary market."""
    entries = tuple(
        AdpEntry(
            player_id=row.player_id, player=row.player_name, team=row.team,
            position=row.position,
            overall_adp=overrides.get(row.player_id, float(row.overall_rank)),
            expected_pick=overrides.get(row.player_id, float(row.overall_rank)),
            min_pick=None, max_pick=None, std_dev=None,
        )
        for row in ranking.rows
    )
    return AdpSnapshot(
        ranking.profile.profile_id, "benchmark", "ppr", ranking.profile.team_count,
        "2026-08-17", "2026-08-17T00:00:00+00:00", "fixture-sha", entries, (),
    )


def test_troy_franklin_shaped_case_is_waiver_watch_not_take_now() -> None:
    """Real-evidence-shaped regression: a player NWR ranks reasonably
    well (a real, positive replacement_adjusted_value -- "NWR likes this
    player") whose real market ADP places him far past any realistic
    redraft-league bench spot (the real Troy Franklin case: nwr_rank 91,
    ESPN ADP 977.0, undrafted in the real 192-pick KHA recap) must not
    be labeled a pick-now priority. A genuinely contested top pick, by
    contrast, should be. This is the exact "NWR likes player" vs. "spend
    this pick" distinction section 11 asks the system to make."""
    from src.services.shadow_numeric_authorities_service import (
        evaluate_cost_of_waiting_v2,
        evaluate_pick_candidates,
    )

    ranking = _ranking(team_count=12, rounds=15)
    profile = ranking.profile
    # WR-0 stands in for the real Troy Franklin shape: a real, ranked
    # WR (overall_rank 111 in this fixture's WR block) with an ADP so
    # deep it is effectively off the board.
    franklin_like = "WR-0"
    adp = _market_aligned_adp(ranking, overrides={franklin_like: 977.0})
    candidates = ["RB-0", "RB-1", franklin_like, "WR-5"]

    scored = evaluate_pick_candidates(
        profile, ranking, _manual_assets(), adp,
        owner_slot=1, candidate_player_ids=candidates, trials=3, seasons=30, base_seed=7,
    )
    v2 = evaluate_cost_of_waiting_v2(
        profile, ranking, _manual_assets(), adp,
        owner_slot=1, candidate_player_ids=candidates, pick_scores=scored, trials=15, base_seed=7,
    )
    adp_by_id = {pid: entry.expected_pick for pid, entry in adp.by_player_id.items()}
    labels = label_pick_decisions(
        v2, adp_expected_pick_by_id=adp_by_id, current_pick_number=1, team_count=12
    )

    # The Troy-Franklin-shaped candidate is never worth a pick right now,
    # regardless of his individually real, positive NWR value.
    assert labels[franklin_like] == "WAIVER_WATCH"
    assert v2[franklin_like].survival_probability > 0.9  # essentially guaranteed to still be there
    # RB-0 (overall rank 31, ADP matches -- a real, immediately contested
    # top pick) must be the highest-urgency candidate in this set.
    most_urgent = max(v2, key=lambda pid: v2[pid].expected_cost)
    assert labels[most_urgent] == "TAKE_NOW"
    assert most_urgent != franklin_like
