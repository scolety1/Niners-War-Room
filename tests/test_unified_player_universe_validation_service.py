from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.unified_player_universe_validation_service import (
    REQUIRED_REVIEW_COLUMNS,
    validate_artifact_files,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "docs" / "hq" / "model" / "unified_player_universe_v0"


def _review() -> pd.DataFrame:
    return pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_review.csv",
        keep_default_na=False,
    )


def test_unified_player_universe_artifact_schema_validation() -> None:
    review = _review()

    assert set(REQUIRED_REVIEW_COLUMNS).issubset(review.columns)
    assert len(review) == 383


def test_unified_player_universe_enum_validation() -> None:
    report = validate_artifact_files()

    assert set(report["status"]) == {"PASS"}


def test_market_data_cannot_create_rank() -> None:
    review = _review()

    assert not review["rank_source"].str.contains("MARKET", case=False).any()
    assert review.loc[review["market_match_status"].eq("MATCHED"), "dp_market_rank"].ne("").any()


def test_rookie_rows_cannot_receive_fabricated_dynasty_rank() -> None:
    review = _review()
    rookies = review.loc[review["player_type"].isin(["ROOKIE", "PROSPECT"])]

    assert len(rookies) == 54
    assert rookies["dynasty_rank"].eq("").all()
    assert rookies["rank_source"].isin(["ROOKIE_RANK", "UNRANKED_REVIEW"]).all()


def test_duplicate_detection_report_loads() -> None:
    duplicates = pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_duplicate_review.csv",
        keep_default_na=False,
    )

    assert len(duplicates) == 15
    assert duplicates["review_status"].eq("REVIEW_NEEDED").all()
    assert duplicates["detection_type"].str.contains("appears_in_multiple_layers").any()


def test_missing_player_id_reporting() -> None:
    review = _review()
    gaps = pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_identity_gap_review.csv",
        keep_default_na=False,
    )

    assert review["player_id"].eq("").sum() == 5
    assert gaps["gap_type"].eq("missing_player_id").sum() == 5


def test_app_wiring_allowed_is_no_for_all_rows() -> None:
    review = _review()

    assert review["app_wiring_allowed"].eq("no").all()


def test_model_input_allowed_is_no_for_all_rows() -> None:
    review = _review()

    assert review["model_input_allowed"].eq("no").all()


def test_source_summary_counts_load() -> None:
    summary = pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_source_summary.csv",
        keep_default_na=False,
    )

    full_dynasty = summary.loc[summary["layer"].eq("Veteran Full Dynasty Layer")].iloc[0]
    rookies = summary.loc[summary["layer"].eq("Rookie/Prospect Layer")].iloc[0]

    assert int(full_dynasty["row_count"]) == 240
    assert int(rookies["row_count"]) == 54


def test_validation_report_loads() -> None:
    report = pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_validation_report.csv",
        keep_default_na=False,
    )

    assert not report.empty
    assert report["status"].eq("PASS").all()
