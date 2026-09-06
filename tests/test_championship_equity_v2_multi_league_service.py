"""Unit tests for the frozen Championship Equity V2 live service --
uses a small synthetic frozen-model fixture (not the real multi-MB
frozen artifact) to test the pure arithmetic/evidence-labeling logic
in isolation, matching this codebase's established pattern for
service-level unit tests separate from full-corpus integration checks.
"""

from __future__ import annotations

import sys

import pytest

sys.path.insert(0, ".")

from src.services.championship_equity_v2_multi_league_service import (
    ChampionshipEquityV2Error,
    compute_championship_equity_v2,
    evaluate_candidate_equity,
    evidence_level_for,
)

SYNTHETIC_FROZEN_MODEL = {
    "feature_names": ["projected_win_probability", "team_score_v2_calibrated", "team_count"],
    "feature_means": {
        "projected_win_probability": 0.1, "team_score_v2_calibrated": 50.0, "team_count": 11.5,
    },
    "feature_stdevs": {
        "projected_win_probability": 0.05, "team_score_v2_calibrated": 20.0, "team_count": 3.0,
    },
    "weights": {
        "projected_win_probability": 0.03, "team_score_v2_calibrated": 0.02, "team_count": -0.005,
    },
    "intercept": 0.1,
    "calibration_by_team_count": {
        "8": {"slope": 1.0, "intercept": 0.0},
        "12": {"slope": 1.0, "intercept": 0.0},
    },
}


def test_compute_rejects_unsupported_team_count() -> None:
    with pytest.raises(ChampionshipEquityV2Error):
        compute_championship_equity_v2(
            projected_win_probability=0.1, team_score_v2_calibrated=50.0,
            team_count=6, frozen_model=SYNTHETIC_FROZEN_MODEL,
        )


def test_compute_is_clamped_to_valid_probability_range() -> None:
    result = compute_championship_equity_v2(
        projected_win_probability=0.9, team_score_v2_calibrated=100.0,
        team_count=8, frozen_model=SYNTHETIC_FROZEN_MODEL,
    )
    assert 0.0 <= result <= 1.0


def test_higher_team_score_never_decreases_equity_given_frozen_positive_weight() -> None:
    low = compute_championship_equity_v2(
        projected_win_probability=0.1, team_score_v2_calibrated=30.0,
        team_count=12, frozen_model=SYNTHETIC_FROZEN_MODEL,
    )
    high = compute_championship_equity_v2(
        projected_win_probability=0.1, team_score_v2_calibrated=70.0,
        team_count=12, frozen_model=SYNTHETIC_FROZEN_MODEL,
    )
    assert high > low


def test_evidence_level_historically_validated_for_supported_team_count() -> None:
    assert evidence_level_for(
        team_count=12, scoring_format="Non-PPR", roster_matches_historical_shape=True,
    ) == "HISTORICALLY_VALIDATED"


def test_evidence_level_unsupported_for_unknown_team_count() -> None:
    assert evidence_level_for(
        team_count=14, scoring_format="Non-PPR", roster_matches_historical_shape=True,
    ) == "UNSUPPORTED"


def test_evidence_level_transport_supported_for_ppr() -> None:
    assert evidence_level_for(
        team_count=12, scoring_format="PPR", roster_matches_historical_shape=True,
    ) == "TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED"


def test_evaluate_candidate_equity_returns_current_post_delta_and_both_evidence_fields() -> None:
    result = evaluate_candidate_equity(
        current_projected_win_probability=0.08, post_pick_projected_win_probability=0.12,
        current_team_score_v2=40.0, post_pick_team_score_v2=55.0,
        candidate_player_id="player_x", team_count=12, frozen_model=SYNTHETIC_FROZEN_MODEL,
    )
    assert result["candidate_player_id"] == "player_x"
    assert result["post_pick_championship_equity"] > result["current_championship_equity"]
    assert result["championship_equity_delta"] == pytest.approx(
        result["post_pick_championship_equity"] - result["current_championship_equity"]
    )
    assert "ranking_evidence" in result
    assert "calibration_evidence" in result
    assert "NOT DECISIVE" in result["ranking_evidence"]
    assert "DECISIVE" in result["calibration_evidence"]
    assert result["evidence_level"] == "HISTORICALLY_VALIDATED"


def test_evaluate_candidate_equity_is_deterministic() -> None:
    kwargs = dict(
        current_projected_win_probability=0.08, post_pick_projected_win_probability=0.12,
        current_team_score_v2=40.0, post_pick_team_score_v2=55.0,
        candidate_player_id="player_x", team_count=8, frozen_model=SYNTHETIC_FROZEN_MODEL,
    )
    assert evaluate_candidate_equity(**kwargs) == evaluate_candidate_equity(**kwargs)
