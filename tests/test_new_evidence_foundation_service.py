from __future__ import annotations

import pandas as pd
import pytest

from src.services import new_evidence_foundation_service as foundation


def test_identity_authority_never_uses_name_as_join_key() -> None:
    players = pd.DataFrame(
        [
            {
                "gsis_id": "00-0001",
                "pfr_id": "ExactA00",
                "display_name": "Same Name",
                "position": "WR",
            },
            {
                "gsis_id": "00-0002",
                "pfr_id": "ExactB00",
                "display_name": "Same Name",
                "position": "WR",
            },
        ]
    )
    draft = pd.DataFrame(
        [
            {
                "pfr_player_id": "ExactA00",
                "player_name": "Different Display",
                "season": 2024,
                "round": 1,
                "pick": 10,
            }
        ]
    )
    combine = pd.DataFrame(
        [
            {
                "pfr_id": "ExactA00",
                "player_name": "Not Used",
                "season": 2024,
                "round": 1,
                "pick": 10,
            },
            {
                "player_name": "Same Name",
                "season": 2024,
                "round": 7,
                "pick": 250,
            },
        ]
    )
    tables = foundation.build_identity_tables(players, draft, combine)
    exact_combine = tables.exact[tables.exact["source_dataset"].eq("combine")]
    assert exact_combine.iloc[0]["gsis_id"] == "00-0001"
    assert exact_combine.iloc[0]["name_used_as_identity"] == "false"
    assert len(tables.unresolved) == 1
    assert list(tables.review.columns) == list(foundation.IDENTITY_COLUMNS)


def test_authoritative_unique_draft_slot_can_crosswalk_combine() -> None:
    players = pd.DataFrame(
        [{"gsis_id": "00-0001", "pfr_id": "A", "display_name": "Player A"}]
    )
    draft = pd.DataFrame(
        [{"pfr_player_id": "A", "season": 2024, "round": 2, "pick": 40}]
    )
    combine = pd.DataFrame(
        [{"season": 2024, "round": 2, "pick": 40, "player_name": "Display"}]
    )
    tables = foundation.build_identity_tables(players, draft, combine)
    row = tables.exact[tables.exact["source_dataset"].eq("combine")].iloc[0]
    assert row["identity_classification"] == (
        "EXACT_DRAFT_SLOT_WITH_AUTHORITATIVE_CROSSWALK"
    )
    assert row["gsis_id"] == "00-0001"


def test_nwr_scoring_uses_repository_scoring_contract() -> None:
    stats = pd.DataFrame(
        [
            {
                "season": 2024,
                "position": "RB",
                "passing_yards": 0,
                "rushing_yards": 100,
                "rushing_tds": 1,
                "receiving_yards": 50,
                "receiving_tds": 1,
                "rushing_first_downs": 5,
                "receiving_first_downs": 2,
                "games": 1,
            }
        ]
    )
    points = foundation.derive_nwr_points(stats)
    assert points.iloc[0] == pytest.approx(25.8)


def test_temporal_contract_fails_closed_on_future_feature() -> None:
    rows = pd.DataFrame(
        [
            {
                "feature_name": "weekly_snaps",
                "available_after": "2024-09-10",
                "prediction_boundary": "2024-09-09",
            }
        ]
    )
    with pytest.raises(foundation.TemporalLeakageError):
        foundation.validate_temporal_rows(rows)


def test_schema_contract_compares_names_types_and_rows() -> None:
    expected = [{"name": "gsis_id", "dtype": "String"}]
    foundation.validate_schema_record(
        actual_schema=expected,
        expected_schema=expected,
        actual_rows=1,
        expected_rows=1,
    )
    with pytest.raises(foundation.SourceAdmissionError):
        foundation.validate_schema_record(
            actual_schema=[{"name": "gsis_id", "dtype": "Int64"}],
            expected_schema=expected,
            actual_rows=1,
            expected_rows=1,
        )


@pytest.mark.parametrize("case", foundation.MUTATION_CASES)
def test_all_required_mutations_fail_through_contract_paths(case: str) -> None:
    error_class = foundation.exercise_mutation(case)
    assert error_class.endswith("Error")


def test_walk_forward_evaluation_is_chronological_and_deterministic() -> None:
    rows = []
    for season in range(2012, 2021):
        for index, position in enumerate(("QB", "RB", "WR", "TE")):
            rows.append(
                {
                    "season": season,
                    "position": position,
                    "draft_pick": 10 + index * 20,
                    "draft_age": 21 + index,
                    "outcome": 100 - index * 10 + (season - 2012),
                    "hit": int(index < 2),
                    "experience_class": "ROOKIE",
                }
            )
    frame = pd.DataFrame(rows)
    first = foundation.walk_forward_evaluate(
        frame,
        model_features={
            "R0": ("position",),
            "R1": ("position", "draft_pick"),
        },
        season_column="season",
        continuous_target="outcome",
        binary_target="hit",
        slice_column="experience_class",
    )
    second = foundation.walk_forward_evaluate(
        frame,
        model_features={
            "R0": ("position",),
            "R1": ("position", "draft_pick"),
        },
        season_column="season",
        continuous_target="outcome",
        binary_target="hit",
        slice_column="experience_class",
    )
    pd.testing.assert_frame_equal(first.metrics, second.metrics)
    assert first.predictions["test_season"].min() == 2015
