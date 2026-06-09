from __future__ import annotations

from src.services.model_v4_first_down_estimation_service import (
    build_first_down_rate_profile,
    estimate_first_downs,
)


def test_first_down_estimates_are_labeled_estimated_not_direct() -> None:
    profile = build_first_down_rate_profile()
    estimate = estimate_first_downs(
        player_name="Bijan Robinson",
        position="RB",
        metrics={"rushing_att": 100, "receiving_tar": 50, "receiving_rec": 40},
        profile=profile,
    )

    assert estimate.source_status == "estimated_from_history"
    assert "not_direct" in estimate.warning
    assert estimate.rushing_first_downs > 0
    assert estimate.receiving_first_downs > 0
    assert estimate.first_down_points > 0


def test_first_down_estimates_use_position_fallback_for_players_without_history() -> None:
    profile = build_first_down_rate_profile()
    estimate = estimate_first_downs(
        player_name="No History Rookie",
        position="WR",
        metrics={"rushing_att": 0, "receiving_tar": 100, "receiving_rec": 70},
        profile=profile,
    )

    assert estimate.source_status == "estimated_from_history"
    assert estimate.receiving_rate_source == "position_fallback"
    assert estimate.receiving_first_downs > 0
