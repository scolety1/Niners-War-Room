from __future__ import annotations

import pytest

from src.models.rookie_scores import (
    ModelMode,
    Position,
    RookieInput,
    feature_score,
    score_rookie,
    veteran_opportunity_adjustment,
    weighted_average,
)


def test_weighted_average_clamps_and_handles_missing_values() -> None:
    assert weighted_average({"a": 120, "b": None}, {"a": 1, "b": 1}) == 75
    assert weighted_average({}, {}) == 50
    assert feature_score(None) == 50
    assert feature_score(-10) == 0
    assert feature_score(110) == 100


@pytest.mark.parametrize(
    ("position", "internal", "benchmark", "expected"),
    [
        (Position.QB, 90, 72, 3),
        (Position.QB, 20, 72, -14),
        (Position.RB, 90, 70, 5),
        (Position.WR, 40, 72, -10),
        (Position.TE, 90, 66, 3),
        (Position.TE, 20, 66, -12),
    ],
)
def test_veteran_adjustment_respects_position_caps(
    position: Position,
    internal: float,
    benchmark: float,
    expected: float,
) -> None:
    assert veteran_opportunity_adjustment(position, internal, benchmark) == expected


def test_landing_spot_does_not_change_main_prospect_score() -> None:
    base = _rookie(
        Position.WR,
        {
            "draft_capital": 80,
            "target_earning": 82,
            "efficiency_dominance": 84,
            "age_trajectory": 76,
            "chain_moving": 75,
        },
        opportunity=20,
        benchmark=72,
    )
    better_landing_spot = _rookie(
        Position.WR,
        base.features,
        opportunity=95,
        benchmark=72,
    )

    assert score_rookie(base).main_prospect_score == score_rookie(
        better_landing_spot
    ).main_prospect_score
    assert score_rookie(base).rookie_opportunity_score != score_rookie(
        better_landing_spot
    ).rookie_opportunity_score


def test_missing_core_features_reduce_confidence_and_cap_score() -> None:
    score = score_rookie(
        _rookie(
            Position.WR,
            {
                "draft_capital": 92,
                "target_earning": None,
                "efficiency_dominance": None,
                "age_trajectory": None,
                "chain_moving": 88,
            },
            opportunity=85,
            benchmark=72,
        )
    )

    assert score.missing_data_penalty == 10
    assert score.confidence_score < 55
    assert score.final_decision_score <= 68
    assert "low_confidence" in score.risk_flags


def test_non_elite_pocket_qb_is_suppressed_but_elite_rusher_clears_gate() -> None:
    pocket = score_rookie(
        _rookie(
            Position.QB,
            {
                "draft_capital": 88,
                "rushing_profile": 25,
                "passing_efficiency": 84,
                "sack_avoidance": 80,
                "age_trajectory": 75,
            },
            opportunity=90,
            benchmark=72,
        )
    )
    elite = score_rookie(
        _rookie(
            Position.QB,
            {
                "draft_capital": 92,
                "rushing_profile": 95,
                "passing_efficiency": 86,
                "sack_avoidance": 72,
                "age_trajectory": 82,
            },
            opportunity=85,
            benchmark=72,
        )
    )

    assert pocket.gate_applied == "qb_structural_penalty"
    assert pocket.gate_adjustment == -8
    assert "pocket_qb_only" in pocket.risk_flags
    assert elite.gate_applied == "qb_elite_exempt"
    assert elite.exceptional_profile_flag is True
    assert elite.do_not_draft_before_pick == 4


def test_day3_te_is_suppressed_but_exceptional_te_clears_gate() -> None:
    day3 = score_rookie(
        _rookie(
            Position.TE,
            {
                "draft_capital": 38,
                "receiving_efficiency": 68,
                "route_role": 55,
                "production_volume": 62,
                "athletic_size": 77,
                "age_trajectory": 70,
            },
            opportunity=42,
            benchmark=66,
        )
    )
    elite = score_rookie(
        _rookie(
            Position.TE,
            {
                "draft_capital": 88,
                "receiving_efficiency": 90,
                "route_role": 87,
                "production_volume": 82,
                "athletic_size": 81,
                "age_trajectory": 80,
            },
            opportunity=78,
            benchmark=66,
        )
    )

    assert day3.gate_applied == "te_day3_penalty"
    assert day3.do_not_draft_before_pick >= 31
    assert elite.gate_applied == "te_elite_exempt"
    assert elite.do_not_draft_before_pick == 11


def _rookie(
    position: Position,
    features,
    *,
    opportunity: float,
    benchmark: float,
) -> RookieInput:
    return RookieInput(
        player_id="fixture",
        player_name="Fixture",
        position=position,
        class_year=2026,
        model_mode=ModelMode.POST_DRAFT,
        source_snapshot_id="test",
        source_name="test",
        source_date="2026-05-05",
        features=features,
        rookie_opportunity_score=opportunity,
        veteran_benchmark_score=benchmark,
    )
