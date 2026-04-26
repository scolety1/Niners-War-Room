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
    assert private_score(
        PlayerScoreInputs(
            position="QB",
            production_score=92,
            opportunity_score=90,
            official_rank=2,
            market_rank=4,
            rushing_score=95,
            environment_score=82,
            first_downs=180,
            first_down_opportunities=520,
            risk_penalty=2,
        )
    ) == pytest.approx(92.03)
    assert private_score(
        PlayerScoreInputs(
            position="RB",
            production_score=90,
            opportunity_score=88,
            official_rank=1,
            market_rank=3,
            age=23,
            receiving_score=84,
            environment_score=78,
            first_downs=70,
            first_down_opportunities=260,
            risk_penalty=5,
        )
    ) == pytest.approx(86.45)
    assert private_score(
        PlayerScoreInputs(
            position="WR",
            production_score=86,
            opportunity_score=82,
            official_rank=5,
            market_rank=8,
            target_earning_score=88,
            breakout_score=84,
            environment_score=80,
            first_downs=58,
            first_down_opportunities=100,
            risk_penalty=3,
        )
    ) == pytest.approx(85.79)
    assert private_score(
        PlayerScoreInputs(
            position="TE",
            production_score=78,
            opportunity_score=74,
            official_rank=40,
            market_rank=45,
            age=25,
            target_earning_score=80,
            breakout_score=76,
            environment_score=72,
            first_downs=42,
            first_down_opportunities=82,
            risk_penalty=4,
        )
    ) == pytest.approx(76.85)


def test_first_down_helpers_are_bounded_and_position_aware() -> None:
    assert first_down_rate(60, 100) == 0.6
    assert first_down_rate(10, 0) == 0.0
    assert first_down_rate_adjustment("WR", 60, 100) == pytest.approx(1.2)
    assert first_down_volume_adjustment("WR", 60) == pytest.approx(0.6)
    assert first_down_rate_adjustment("RB", 1, 300) == -4.0
    assert first_down_volume_adjustment("RB", 200) == 3.0


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


def test_official_top_five_excludes_ranks_outside_top_five() -> None:
    players = [
        KeeperScoreInputs("p2", "Two", "RB", 90, official_rank=2),
        KeeperScoreInputs("p6", "Six", "WR", 95, official_rank=6),
        KeeperScoreInputs("p9", "Nine", "TE", 85, official_rank=9),
    ]

    assert [player.player_name for player in official_top_five(players)] == ["Two"]
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
