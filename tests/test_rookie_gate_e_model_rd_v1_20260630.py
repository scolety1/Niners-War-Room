from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_gate_e_model_rd_v1_20260630 import (
    ALLOWED_FEATURES,
    EXPECTED_SCORING_MODE,
    FEATURE_AUDIT_COLUMNS,
    NOT_ENOUGH,
    build_feature_audit_rows,
    build_target_predictions,
    build_validation_artifacts,
    draft_capital_bucket,
    eligible_rows,
    validate_prediction_rows,
    validate_review_rows,
)

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = (
    ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_e_model_rd_v1_20260630"
    / "rookie_model_rd_validation_summary_v1.csv"
)
VALIDATION_REPORT_PATH = (
    ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_e_model_rd_v1_20260630"
    / "02_MODEL_RD_VALIDATION_REPORT.md"
)


def test_only_gate_d_allowed_features_are_used() -> None:
    assert set(ALLOWED_FEATURES) == {
        "draft_round",
        "draft_pick",
        "draft_capital_bucket",
        "draft_year",
        "rookie_class_year",
        "position",
    }

    rows = build_feature_audit_rows(ALLOWED_FEATURES)
    validate_review_rows(rows)
    assert tuple(rows[0]) == FEATURE_AUDIT_COLUMNS
    assert {row["used_as_input"] for row in rows} == {"true"}
    assert {row["allowed_by_gate_d"] for row in rows} == {"true"}


def test_draft_capital_bucket_is_derived_only_from_allowed_draft_fields() -> None:
    assert draft_capital_bucket({"draft_round": "1", "draft_pick": "8"}) == "round_1_top_10"
    assert draft_capital_bucket({"draft_round": "1", "draft_pick": "20"}) == "round_1_other"
    assert draft_capital_bucket({"draft_round": "2", "draft_pick": "40"}) == "round_2"
    assert draft_capital_bucket({"draft_round": "4", "draft_pick": "120"}) == "round_4_7"
    assert draft_capital_bucket({"draft_round": NOT_ENOUGH, "draft_pick": NOT_ENOUGH}) == (
        "not_enough_information"
    )


def test_labels_are_targets_only_and_predictions_keep_flags_closed() -> None:
    train_rows = [
        _label_row(year, "hit" if year % 2 == 0 else "miss")
        for year in range(2012, 2020)
    ]
    validation_rows = [
        _label_row(year, "hit" if year == 2021 else "miss")
        for year in range(2020, 2023)
    ]

    predictions = build_target_predictions(
        target="rookie_year_top_12_hit",
        train_rows=train_rows,
        validation_rows=validation_rows,
        validation_start=2020,
    )

    validate_prediction_rows(predictions)
    assert predictions
    assert {row["review_only"] for row in predictions} == {"true"}
    assert {row["model_use_allowed"] for row in predictions} == {"false"}
    assert {row["training_allowed"] for row in predictions} == {"false"}
    assert "rookie_year_top_12_hit" not in predictions[0]
    assert "actual_label" in predictions[0]


def test_censored_first_5y_rows_are_excluded_from_target_validation() -> None:
    rows = [
        _label_row(2020, "hit", first_5y_window_complete="true"),
        _label_row(2022, "hit", first_5y_window_complete="false"),
    ]

    eligible = eligible_rows(rows, "first_5y_top_12_hit")

    assert len(eligible) == 1
    assert eligible[0]["rookie_class_year"] == "2020"


def test_build_validation_artifacts_use_only_historical_rows() -> None:
    rows: list[dict[str, str]] = []
    for year in range(2012, 2025):
        rows.extend(
            [
                _label_row(year, "hit" if year % 3 == 0 else "miss", player_suffix="a"),
                _label_row(year, "miss", player_suffix="b"),
                _label_row(year, "hit" if year % 4 == 0 else "miss", player_suffix="c"),
                _label_row(year, "miss", player_suffix="d"),
                _label_row(year, "hit" if year % 5 == 0 else "miss", player_suffix="e"),
            ]
        )

    predictions, metrics, calibration = build_validation_artifacts(rows)

    assert predictions
    assert metrics
    assert calibration
    validate_prediction_rows(predictions)
    validate_review_rows(metrics)
    validate_review_rows(calibration)
    assert not any("current" in row["player_name"].lower() for row in predictions)


def test_tracked_summary_has_no_current_player_probabilities_or_rankings_wiring() -> None:
    rows = _summary_rows()
    metrics = {row["metric"]: row["value"] for row in rows}

    validate_review_rows(rows)
    assert metrics["current_player_predictions_created"] == "0"
    assert metrics["rankings_wiring_created"] == "0"
    assert metrics["model_use_rows"] == "0"
    assert metrics["training_use_rows"] == "0"


def test_validation_report_exists_and_declares_review_only_limits() -> None:
    text = VALIDATION_REPORT_PATH.read_text(encoding="utf-8")

    assert "review-only R&D feasibility" in text
    assert "Missing labels were excluded, not treated as misses" in text
    assert "drafted players only" in text


def test_market_adp_dynastyprocess_vendor_gmail_are_not_used() -> None:
    script_text = (
        ROOT / "scripts" / "build_rookie_gate_e_model_rd_v1_20260630.py"
    ).read_text(encoding="utf-8")

    forbidden = ("DynastyProcess", "Gmail", "RotoWire", "FantasyPros", "market_adp")
    assert not any(term in script_text for term in forbidden)


def test_shared_data_outputs_are_not_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "rookie_outcomes/model_rd_v1" not in tracked
    assert "local_exports" not in tracked


def test_lane_does_not_reference_protected_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("rookie_gate_e_model_rd" not in path for path in protected_paths)


def _summary_rows() -> list[dict[str, str]]:
    with SUMMARY_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _label_row(
    year: int,
    label: str,
    *,
    first_5y_window_complete: str = "true",
    player_suffix: str = "",
) -> dict[str, str]:
    first_3y_complete = "true" if year <= 2022 else "false"
    return {
        "nfl_player_id": f"00-fixture-{year}-{player_suffix}",
        "player_name": f"Historical Fixture {year} {player_suffix}",
        "position": "RB",
        "rookie_class_year": str(year),
        "draft_year": str(year),
        "draft_round": "2",
        "draft_pick": "45",
        "draft_capital_bucket": "round_2",
        "scoring_mode": EXPECTED_SCORING_MODE,
        "rookie_year_top_12_hit": label,
        "rookie_year_top_24_hit": label,
        "rookie_year_top_36_hit": label,
        "year_2_top_12_hit": label,
        "year_2_top_24_hit": label,
        "year_2_top_36_hit": label,
        "first_3y_top_12_hit": label,
        "first_3y_top_24_hit": label,
        "first_3y_top_36_hit": label,
        "first_5y_top_12_hit": label,
        "first_5y_top_24_hit": label,
        "first_5y_top_36_hit": label,
        "first_3y_window_complete": first_3y_complete,
        "first_5y_window_complete": first_5y_window_complete,
        "censoring_status": "complete" if first_5y_window_complete == "true" else "right_censored",
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }
