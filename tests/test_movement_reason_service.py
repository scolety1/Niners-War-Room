from __future__ import annotations

import pytest

from src.services.movement_reason_service import (
    classify_movement,
    movement_magnitude_bucket,
    movement_review_label,
)


def test_movement_magnitude_bucket_classifies_rank_and_value_deltas() -> None:
    assert movement_magnitude_bucket(rank_delta=0, value_delta=0) == "none"
    assert movement_magnitude_bucket(rank_delta=3, value_delta=0.4) == "small"
    assert movement_magnitude_bucket(rank_delta=15, value_delta=0.4) == "medium"
    assert movement_magnitude_bucket(rank_delta=40, value_delta=10) == "large"


def test_classify_movement_explains_known_cause_before_unknown() -> None:
    previous = {
        "player_id": "p1",
        "overall_rank": "20",
        "model_version": "v1",
        "asset_lifecycle": "year_two_nfl_bridge",
        "confidence_score": "75",
    }
    current = {
        "player_id": "p1",
        "overall_rank": "5",
        "model_version": "v1",
        "asset_lifecycle": "established_veteran",
        "confidence_score": "75",
    }

    classification = classify_movement(current, previous, rank_delta=-15)

    assert classification.movement_reason == "lifecycle_update"
    assert classification.movement_magnitude == "medium"
    assert classification.movement_review_flag is False


def test_classify_movement_flags_unknown_medium_or_large_movement() -> None:
    previous = {"player_id": "p1", "overall_rank": "50", "keeper_score": "61"}
    current = {"player_id": "p1", "overall_rank": "15", "keeper_score": "61"}

    classification = classify_movement(current, previous, rank_delta=-35)

    assert classification.movement_reason == "unknown_movement"
    assert classification.movement_magnitude == "large"
    assert classification.movement_review_flag is True
    assert movement_review_label(classification) == "review_unknown_medium_large_movement"


def test_classify_movement_uses_no_material_reason_for_tiny_changes() -> None:
    previous = {"player_id": "p1", "overall_rank": "10", "model_version": "v1"}
    current = {"player_id": "p1", "overall_rank": "10", "model_version": "v2"}

    classification = classify_movement(current, previous, rank_delta=0, value_delta=0)

    assert classification.movement_reason == "no_material_movement"
    assert classification.movement_magnitude == "none"


@pytest.mark.parametrize(
    ("previous", "current", "expected_reason"),
    [
        (
            {"player_id": "p1", "model_version": "v1"},
            {"player_id": "p1", "model_version": "v2"},
            "formula_update",
        ),
        (
            {"player_id": "p1", "outlier_review_status": "unresolved"},
            {"player_id": "p1", "outlier_review_status": "accepted"},
            "outlier_acceptance",
        ),
        (
            {"player_id": "p1", "source_gap_review_status": "unresolved"},
            {"player_id": "p1", "source_gap_review_status": "accepted"},
            "source_gap_acceptance",
        ),
        (
            {"player_id": "p1", "market_value_status": "real_imported_market"},
            {"player_id": "p1", "market_value_status": "missing_market"},
            "market_isolation",
        ),
        (
            {"player_id": "p1", "source_status": "neutral_imputation"},
            {"player_id": "p1", "source_status": "imported_real_data"},
            "source_update",
        ),
        (
            {"player_id": "p1", "warning_status": "ready"},
            {"player_id": "p1", "warning_status": "review"},
            "confidence_update",
        ),
        (
            {
                "player_id": "p1",
                "rank_audit": "sort=keeper",
                "keeper_score": "60",
                "private_lve_value": "58",
            },
            {
                "player_id": "p1",
                "rank_audit": "sort=private",
                "keeper_score": "60",
                "private_lve_value": "58",
            },
            "ranking_surface_change",
        ),
    ],
)
def test_classify_movement_reason_categories(
    previous: dict[str, str],
    current: dict[str, str],
    expected_reason: str,
) -> None:
    classification = classify_movement(current, previous, rank_delta=10)

    assert classification.movement_reason == expected_reason
