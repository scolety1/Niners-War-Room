from __future__ import annotations

from dataclasses import replace

import pytest

from src.models.confidence import ConfidenceInputs, confidence_score, risk_level
from src.models.keeper_scores import (
    KeeperScoreInputs,
    best_23_keepers,
    drop_candidate_score,
    forced_release_candidates,
    keeper_decision,
    keeper_pressure,
    keeper_score,
    official_top_five,
    top_five_shield_eligibility,
)
from src.models.player_scores import (
    PlayerScoreInputs,
    first_down_rate,
    first_down_rate_adjustment,
    first_down_volume_adjustment,
    private_score,
)


def test_position_private_scores_are_deterministic() -> None:
    # QB: 0.40*90 + 0.30*95 + 0.15*80 + 0.10*85 + 0.05*82
    #     + rate_adj(180/520 vs 0.31) + volume_adj(180 vs 160) - 2 = 87.65
    assert private_score(
        PlayerScoreInputs(
            position="QB",
            draft_cap=90,
            rush_profile=95,
            start_path=80,
            passing_trait=85,
            environment=82,
            first_downs=180,
            first_down_opportunities=520,
            risk_penalty=2,
        )
    ) == pytest.approx(87.65)
    # RB: 0.28*96 + 0.22*88 + 0.15*90 + 0.14*84 + 0.12*86
    #     + 0.05*72 + 0.04*76 + first-down adjustments - 5 = 84.16
    assert private_score(
        PlayerScoreInputs(
            position="RB",
            draft_cap=96,
            opportunity=88,
            production=90,
            receiving=84,
            elusiveness=86,
            size_durability=72,
            athleticism=76,
            first_downs=70,
            first_down_opportunities=260,
            risk_penalty=5,
        )
    ) == pytest.approx(84.16)
    # WR: 0.27*78 + 0.21*86 + 0.17*88 + 0.12*84 + 0.11*90
    #     + 0.05*76 + 0.03*82 + 0.04*80 + first-down adjustments - 3 = 81.16
    assert private_score(
        PlayerScoreInputs(
            position="WR",
            draft_cap=78,
            age_adj_production=86,
            target_earning_efficiency=88,
            breakout_class=84,
            film_separation=90,
            size_role=76,
            athleticism=82,
            environment=80,
            first_downs=58,
            first_down_opportunities=100,
            risk_penalty=3,
        )
    ) == pytest.approx(81.16)
    # TE: 0.23*70 + 0.22*78 + 0.17*74 + 0.12*76 + 0.11*80
    #     + 0.08*72 + 0.04*88 + 0.03*72 + first-down adjustments - 4 = 71.48
    assert private_score(
        PlayerScoreInputs(
            position="TE",
            draft_cap=70,
            receiving_production=78,
            route_role=74,
            athleticism=76,
            film_receiving=80,
            role_path=72,
            age_timeline=88,
            environment=72,
            first_downs=42,
            first_down_opportunities=82,
            risk_penalty=4,
        )
    ) == pytest.approx(71.48)


def test_first_down_helpers_are_bounded_and_position_aware() -> None:
    assert first_down_rate(60, 100) == 0.6
    assert first_down_rate(10, 0) == 0.0
    assert first_down_rate_adjustment("WR", 60, 100) == pytest.approx(0.6)
    assert first_down_volume_adjustment("WR", 60) == pytest.approx(0.3)
    assert first_down_rate_adjustment("RB", 1, 300) == -2.0
    assert first_down_volume_adjustment("RB", 200) == 1.5


def test_confidence_score_and_risk_level() -> None:
    assert confidence_score(ConfidenceInputs()) == pytest.approx(0.0)
    assert confidence_score(
        ConfidenceInputs(
            data_completeness=0.8,
            historical_cohort_size=0.6,
            market_agreement=0.9,
            model_separation=0.7,
        )
    ) == pytest.approx(0.75)
    assert risk_level(0.80) == "low"
    assert risk_level(0.60) == "medium"
    assert risk_level(0.40) == "high"


def test_missing_keeper_formula_components_do_not_use_placeholder_scores() -> None:
    player = KeeperScoreInputs(
        player_id="missing",
        player_name="Missing Inputs",
        position="WR",
        private_score=95,
        market_score=95,
        official_rank=1,
        confidence_score=0.95,
    )

    assert keeper_score(player) == pytest.approx(0.0)
    assert keeper_decision(player).confidence_score == pytest.approx(0.0)


def test_keeper_drop_and_decision_confidence_use_written_formulas() -> None:
    player = KeeperScoreInputs(
        player_id="p1",
        player_name="Starter",
        position="RB",
        private_score=88,
        market_score=84,
        official_rank=6,
        my_rank_score=90,
        confidence_score=0.75,
        long_term_private_value=88,
        next_2_year_starter_value=80,
        scarcity_bonus=70,
        trade_liquidity=84,
        age_curve=65,
        risk_adj=72,
        build_fit=90,
        roster_redundancy=40,
        decline_risk=20,
        data_completeness=0.90,
        historical_cohort_size=0.70,
        market_agreement=0.80,
        model_separation=0.60,
    )

    # KeeperScore excludes trade liquidity by policy:
    # 0.32*88 + 0.22*80 + 0.16*70 + 0.11*65 + 0.12*72 + 0.07*90 = 79.05
    assert keeper_score(player) == pytest.approx(79.05)

    # DropCandidateScore = 0.45*(100-79.05) + 0.25*(100-88)
    #                    + 0.15*40 + 0.15*20 = 21.43
    assert drop_candidate_score(player, 79.05) == pytest.approx(21.43)

    decision = keeper_decision(player)
    assert decision.drop_candidate_score == pytest.approx(21.43)
    # Confidence = 0.35*0.90 + 0.25*0.70 + 0.20*0.80 + 0.20*0.60
    assert decision.confidence_score == pytest.approx(0.77)


def test_keeper_score_ignores_extreme_trade_liquidity() -> None:
    base = KeeperScoreInputs(
        player_id="p1",
        player_name="Starter",
        position="WR",
        private_score=88,
        long_term_private_value=88,
        next_2_year_starter_value=80,
        scarcity_bonus=70,
        age_curve=65,
        risk_adj=72,
        build_fit=90,
        trade_liquidity=0,
    )
    extreme_market = replace(base, trade_liquidity=100)

    assert keeper_score(base) == keeper_score(extreme_market)


def test_keeper_drop_risk_ignores_league_rank_order() -> None:
    base = KeeperScoreInputs(
        player_id="p1",
        player_name="Starter",
        position="WR",
        private_score=88,
        long_term_private_value=88,
        next_2_year_starter_value=80,
        scarcity_bonus=70,
        age_curve=65,
        risk_adj=72,
        build_fit=90,
        official_rank=1,
    )
    low_league_rank = replace(base, official_rank=250)

    assert keeper_score(base) == keeper_score(low_league_rank)
    assert drop_candidate_score(base) == drop_candidate_score(low_league_rank)


def test_official_top_five_and_forced_release_candidates() -> None:
    players = _players()

    assert [player.player_name for player in official_top_five(players)] == [
        "Achane",
        "Lamar",
        "Chase Brown",
        "Luther Burden",
        "Brian Thomas",
    ]
    assert [player.player_name for player in forced_release_candidates(players)] == [
        "Luther Burden"
    ]


def test_official_top_five_uses_best_available_official_ranks() -> None:
    players = [
        KeeperScoreInputs("p2", "Two", "RB", 90, official_rank=2),
        KeeperScoreInputs("p6", "Six", "WR", 95, official_rank=6),
        KeeperScoreInputs("p9", "Nine", "TE", 85, official_rank=9),
    ]

    assert [player.player_name for player in official_top_five(players)] == [
        "Two",
        "Six",
        "Nine",
    ]
    assert forced_release_candidates(players) == []


def test_best_23_keepers_and_shield_eligibility() -> None:
    decisions = [
        keeper_decision(player, is_top_five_shield_eligible=True) for player in _players()
    ]

    assert len(best_23_keepers(decisions, protect_limit=3)) == 3

    forced_ids = {player.player_id for player in forced_release_candidates(_players())}
    assert top_five_shield_eligibility(_players()[0], forced_ids)
    assert not top_five_shield_eligibility(_players()[3], forced_ids)
    assert not top_five_shield_eligibility(_players()[5], forced_ids)


def test_keeper_pressure_counts_roster_and_forced_release_pressure() -> None:
    pressure = keeper_pressure("niners", "Niners", 24, 5)

    assert pressure.roster_count == 24
    assert pressure.forced_release_count == 1
    assert pressure.pressure_count == 2
    assert pressure.pressure_level == "medium"


def _players() -> list[KeeperScoreInputs]:
    return [
        _keeper_fixture("p_achane", "Achane", "RB", 91, 1, 88),
        _keeper_fixture("p_lamar", "Lamar", "QB", 89, 2, 86),
        _keeper_fixture("p_chase", "Chase Brown", "RB", 84, 3, 80),
        _keeper_fixture("p_burden", "Luther Burden", "WR", 76, 4, 68),
        _keeper_fixture("p_thomas", "Brian Thomas", "WR", 87, 5, 84),
        _keeper_fixture("p_other", "Other", "TE", 80, 6, 78),
    ]


def _keeper_fixture(
    player_id: str,
    player_name: str,
    position: str,
    private_score_value: float,
    official_rank: int,
    formula_value: float,
) -> KeeperScoreInputs:
    return KeeperScoreInputs(
        player_id,
        player_name,
        position,
        private_score_value,
        official_rank=official_rank,
        market_score=formula_value,
        long_term_private_value=formula_value,
        next_2_year_starter_value=formula_value,
        scarcity_bonus=formula_value,
        trade_liquidity=formula_value,
        age_curve=formula_value,
        risk_adj=formula_value,
        build_fit=formula_value,
        data_completeness=0.8,
        historical_cohort_size=0.8,
        market_agreement=0.8,
        model_separation=0.8,
    )
