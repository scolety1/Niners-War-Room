from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from src.services.outcome_v2_probability_validation_service import (
    build_validation_feature_frame,
    field_feasibility_rows,
    validate_probabilities,
    write_validation_artifacts,
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_outcome_v2_validation_blocks_short_five_year_fields_by_coverage() -> None:
    frame = build_validation_feature_frame()
    rows = field_feasibility_rows(frame)
    five_year_rows = [row for row in rows if row["horizon"] == "within_5y"]

    assert five_year_rows
    assert "VALIDATION_FEASIBLE" not in {
        row["feasibility_status"] for row in five_year_rows
    }


def test_outcome_v2_validation_passes_only_held_out_brier_winners() -> None:
    results, calibration_rows, bucket_rows = validate_probabilities()
    passed = [
        row for row in results if row["validation_status"] == "PASS_APP_DISPLAY_VALIDATION"
    ]
    blocked_weak = [
        row for row in results if row["validation_status"] == "BLOCKED_VALIDATION_WEAK"
    ]

    assert passed
    assert len(passed) == 22
    assert {row["horizon"] for row in passed} <= {"this_year", "next_year"}
    assert {row["field_id"] for row in blocked_weak} == {
        "RB_T6_NEXT_YEAR",
        "RB_T12_NEXT_YEAR",
    }
    assert all(float(row["model_brier"]) <= float(row["baseline_brier"]) for row in passed)
    assert calibration_rows
    assert bucket_rows


def test_extended_five_year_fields_can_enter_validation_when_coverage_is_sufficient(
    tmp_path: Path,
) -> None:
    anchor_path = tmp_path / "anchors.csv"
    season_path = tmp_path / "seasons.csv"
    pd.DataFrame(_synthetic_extended_labels()).to_csv(anchor_path, index=False)
    pd.DataFrame(_synthetic_extended_season_labels()).to_csv(season_path, index=False)

    results, _calibration_rows, _bucket_rows = validate_probabilities(
        anchor_labels_path=anchor_path,
        season_labels_path=season_path,
    )
    qb_5y = next(row for row in results if row["field_id"] == "QB_T6_WITHIN_5Y")

    assert qb_5y["feasibility_status"] == "VALIDATION_FEASIBLE"
    assert qb_5y["validation_status"] in {
        "PASS_APP_DISPLAY_VALIDATION",
        "BLOCKED_VALIDATION_WEAK",
    }
    assert qb_5y["validation_anchor_seasons"] == "2018|2019"


def test_outcome_v2_validation_uses_no_blocked_inputs() -> None:
    results, _, _ = validate_probabilities()

    assert {row["blocked_inputs_used"] for row in results} == {"false"}


def test_outcome_v2_validation_writer_creates_review_only_artifacts(tmp_path: Path) -> None:
    result = write_validation_artifacts(tmp_path)

    assert result.passed_fields == 22
    assert result.blocked_fields == 14
    for path in (
        result.validation_results_path,
        result.calibration_path,
        result.model_buckets_path,
        result.manifest_path,
    ):
        assert path.exists()

    manifest = _rows(result.manifest_path)
    assert {row["display_only"] for row in manifest} == {"true"}
    assert {row["model_use_allowed"] for row in manifest} == {"false"}
    assert {row["training_allowed"] for row in manifest} == {"false"}
    assert {row["blocked_inputs_used"] for row in manifest} == {"false"}


def _synthetic_extended_labels() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for season in range(2012, 2020):
        for index in range(20):
            player_id = f"qb-{index}"
            hit = "hit" if index < 8 else "miss"
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": f"QB {index}",
                    "position": "QB",
                    "anchor_season": season,
                    "team": "SF",
                    "this_year_top_6_hit": hit,
                    "this_year_top_12_hit": hit,
                    "this_year_top_24_hit": "not_applicable",
                    "this_year_top_36_hit": "not_applicable",
                    "next_year_top_6_hit": hit,
                    "next_year_top_12_hit": hit,
                    "next_year_top_24_hit": "not_applicable",
                    "next_year_top_36_hit": "not_applicable",
                    "within_5y_top_6_hit": hit,
                    "within_5y_top_12_hit": hit,
                    "within_5y_top_24_hit": "not_applicable",
                    "within_5y_top_36_hit": "not_applicable",
                    "this_year_window_complete": True,
                    "next_year_window_complete": True,
                    "within_5y_window_complete": True,
                    "censoring_status": "complete",
                    "approval_status": "review_only_historical_labels",
                    "model_input_allowed": "no",
                    "training_allowed": "no",
                    "app_wiring_allowed": "no",
                }
            )
    return rows


def _synthetic_extended_season_labels() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for season in range(2012, 2020):
        for index in range(20):
            rows.append(
                {
                    "player_id": f"qb-{index}",
                    "player_name": f"QB {index}",
                    "position": "QB",
                    "season": season,
                    "team": "SF",
                    "scoring_mode": "exact_verified_first_downs",
                    "fantasy_points": 300 - index,
                    "position_finish": index + 1,
                    "games_played": 17,
                    "top_6_hit": "hit" if index < 6 else "miss",
                    "top_12_hit": "hit" if index < 12 else "miss",
                    "top_24_hit": "not_applicable",
                    "top_36_hit": "not_applicable",
                    "data_quality_status": "complete_factual_player_stats",
                    "approval_status": "review_only_historical_labels",
                    "model_input_allowed": "no",
                    "training_allowed": "no",
                    "app_wiring_allowed": "no",
                }
            )
    return rows
