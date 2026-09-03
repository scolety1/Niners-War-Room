import pytest

from src.services.outcome_evaluation_framework_service import (
    OBSERVED,
    SIMULATED,
    OutcomeEvaluationError,
    kendall_tau,
    pick_level_metrics,
    player_level_metrics,
    player_rank_correlation,
    roster_level_metrics,
    season_level_metrics,
    spearman_rank_correlation,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RosterSettings,
    ScoringSettings,
)
from src.services.shadow_numeric_authorities_service import RosterPlayer


def _profile() -> LeagueProfile:
    return LeagueProfile(
        profile_id="test", league_name="Test League", season=2026, team_count=10,
        roster=RosterSettings(
            qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=5
        ),
        scoring=ScoringSettings(), draft=DraftContext(),
    )


def test_spearman_rank_correlation_is_perfect_for_identical_order() -> None:
    assert spearman_rank_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)


def test_spearman_rank_correlation_is_perfectly_negative_for_reversed_order() -> None:
    assert spearman_rank_correlation([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_returns_none_rather_than_a_fabricated_value_for_too_few_points() -> None:
    assert spearman_rank_correlation([1], [1]) is None


def test_kendall_tau_matches_hand_verified_concordant_discordant_count() -> None:
    # x is already sorted, so tau reduces to counting y's pairwise order:
    # y = [3, 1, 4, 2, 5] has 7 concordant pairs and 3 discordant pairs out
    # of C(5,2) = 10 total -- tau = (7 - 3) / 10 = 0.4 (hand-verified above,
    # not assumed from memory).
    tau = kendall_tau([1, 2, 3, 4, 5], [3, 1, 4, 2, 5])
    assert tau == pytest.approx(0.4, abs=1e-9)


def test_player_rank_correlation_prepares_both_metrics_together() -> None:
    result = player_rank_correlation([1, 2, 3], [1, 2, 3])
    assert result["spearman"] == pytest.approx(1.0)
    assert result["kendall_tau"] == pytest.approx(1.0)


def test_player_level_metrics_computes_projection_error_and_vor() -> None:
    metrics = player_level_metrics(
        player_id="P1", realized_production=220.0, projected_production=200.0,
        replacement_points=150.0,
    )
    assert metrics.projection_error == 20.0
    assert metrics.realized_value_over_replacement == 70.0


def test_player_level_metrics_never_fabricates_missing_projection_data() -> None:
    metrics = player_level_metrics(player_id="P1", realized_production=220.0)
    assert metrics.projection_error is None
    assert metrics.realized_value_over_replacement is None


def test_pick_level_metrics_computes_real_regret_against_the_true_best_alternative() -> None:
    metrics = pick_level_metrics(
        pick_number=12, selected_player_id="A", selected_realized_production=100.0,
        available_pool_realized_production={"A": 100.0, "B": 150.0, "C": 90.0},
        replacement_points=60.0,
    )
    assert metrics.best_available_player_id == "B"
    assert metrics.realized_pick_regret == 50.0
    assert metrics.replacement_loss == 40.0


def test_pick_level_metrics_make_it_back_reflects_real_next_pick_availability() -> None:
    metrics = pick_level_metrics(
        pick_number=12, selected_player_id="A", selected_realized_production=100.0,
        available_pool_realized_production={"A": 100.0, "B": 150.0},
        next_pick_available_player_ids=["B", "C"],
    )
    assert metrics.made_it_back is True

    metrics_gone = pick_level_metrics(
        pick_number=12, selected_player_id="A", selected_realized_production=100.0,
        available_pool_realized_production={"A": 100.0, "B": 150.0},
        next_pick_available_player_ids=["C"],
    )
    assert metrics_gone.made_it_back is False


def test_roster_level_metrics_reuses_the_real_composition_report() -> None:
    profile = _profile()
    roster = [
        RosterPlayer("qb1", "QB", 300.0),
        RosterPlayer("rb1", "RB", 280.0),
        RosterPlayer("rb2", "RB", 200.0),
        RosterPlayer("wr1", "WR", 260.0),
        RosterPlayer("wr2", "WR", 190.0),
        RosterPlayer("te1", "TE", 150.0),
        RosterPlayer("flex1", "RB", 120.0),
        RosterPlayer("k1", "K", 90.0),
        RosterPlayer("dst1", "DST", 80.0),
        RosterPlayer("bench1", "WR", 60.0),
    ]
    metrics = roster_level_metrics(roster, profile)
    assert metrics.roster_total_production == sum(p.value for p in roster)
    assert metrics.starter_production == metrics.optimal_legal_lineup_production
    assert metrics.roster_construction_failure_count == 0
    assert metrics.unused_redundant_value == pytest.approx(
        metrics.roster_total_production - metrics.starter_production
    )


def test_roster_level_metrics_reports_starter_holes_as_construction_failures() -> None:
    profile = _profile()
    roster = [RosterPlayer("qb1", "QB", 300.0)]  # missing RB/WR/TE/K/DST starters
    metrics = roster_level_metrics(roster, profile)
    assert metrics.roster_construction_failure_count > 0


def test_season_level_metrics_requires_an_explicit_source() -> None:
    with pytest.raises(OutcomeEvaluationError):
        season_level_metrics(
            source="MADE_UP", regular_season_strength_percentile=50.0,
            simulated_playoff_rate=None, simulated_championship_rate=None, sample_size=1,
        )


def test_season_level_metrics_refuses_to_label_simulated_rates_as_observed() -> None:
    with pytest.raises(OutcomeEvaluationError):
        season_level_metrics(
            source=OBSERVED, regular_season_strength_percentile=50.0,
            simulated_playoff_rate=0.4, simulated_championship_rate=None, sample_size=1,
        )


def test_season_level_metrics_allows_rates_when_explicitly_simulated() -> None:
    metrics = season_level_metrics(
        source=SIMULATED, regular_season_strength_percentile=72.0,
        simulated_playoff_rate=0.55, simulated_championship_rate=0.12, sample_size=2000,
    )
    assert metrics.source == SIMULATED
    assert metrics.simulated_championship_rate == 0.12
