from __future__ import annotations

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
    assert confidence_score(
        ConfidenceInputs(
            data_completeness=0.8,
            source_count=3,
            rank_age_days=30,
            projection_variance=0.2,
        )
    ) == pytest.approx(0.778)
    assert risk_level(0.80) == "low"
    assert risk_level(0.60) == "medium"
    assert risk_level(0.40) == "high"


def test_keeper_and_drop_scores_use_separate_signals() -> None:
    player = KeeperScoreInputs(
        player_id="p1",
        player_name="Starter",
        position="RB",
        private_score=88,
        market_score=84,
        official_rank=6,
        my_rank_score=90,
        confidence_score=0.75,
    )

    assert keeper_score(player) == pytest.approx(91.51)
    assert drop_candidate_score(91.51) == pytest.approx(8.49)
    assert drop_candidate_score(91.51, is_forced_release_candidate=True) == pytest.approx(26.49)


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
        KeeperScoreInputs("p_achane", "Achane", "RB", 91, official_rank=1, market_score=90),
        KeeperScoreInputs("p_lamar", "Lamar", "QB", 89, official_rank=2, market_score=88),
        KeeperScoreInputs("p_chase", "Chase Brown", "RB", 84, official_rank=3, market_score=82),
        KeeperScoreInputs("p_burden", "Luther Burden", "WR", 76, official_rank=4, market_score=78),
        KeeperScoreInputs("p_thomas", "Brian Thomas", "WR", 87, official_rank=5, market_score=89),
        KeeperScoreInputs("p_other", "Other", "TE", 80, official_rank=6, market_score=81),
    ]
