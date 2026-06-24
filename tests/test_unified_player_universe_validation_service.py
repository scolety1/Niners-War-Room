from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.unified_player_universe_validation_service import (
    CONSOLIDATED_REVIEW_COLUMNS,
    DUPLICATE_CLASS_VALUES,
    IDENTITY_TRIAGE_COLUMNS,
    REQUIRED_REVIEW_COLUMNS,
    TRIAGE_CLASS_VALUES,
    validate_artifact_files,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "docs" / "hq" / "model" / "unified_player_universe_v0"


def _review() -> pd.DataFrame:
    return pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_review.csv",
        keep_default_na=False,
    )


def _consolidated() -> pd.DataFrame:
    return pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_consolidated_review.csv",
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
    assert duplicates["duplicate_class"].isin(DUPLICATE_CLASS_VALUES).all()
    assert duplicates["duplicate_class"].eq("MULTI_LAYER_SAME_PLAYER_EXPECTED").all()


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


def test_identity_triage_csv_schema() -> None:
    triage = pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_identity_triage.csv",
        keep_default_na=False,
    )

    assert set(IDENTITY_TRIAGE_COLUMNS).issubset(triage.columns)
    assert len(triage) == 330
    assert triage["triage_class"].isin(TRIAGE_CLASS_VALUES).all()


def test_safe_repairs_preserve_review_only_gates() -> None:
    review = _review()

    assert review["app_wiring_allowed"].eq("no").all()
    assert review["model_input_allowed"].eq("no").all()


def test_no_fabricated_ids_from_identity_triage() -> None:
    review = _review()
    triage = pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_identity_triage.csv",
        keep_default_na=False,
    )

    assert review["player_id"].eq("").sum() == 5
    assert triage.loc[triage["action_taken"].eq("APPLY_PLAYER_ID_REPAIR")].empty
    safe_repairs = triage.loc[
        triage["triage_class"].str.startswith("SAFE_REPAIR"),
        "source_used",
    ]
    assert safe_repairs.ne("").all()


def test_consolidated_artifact_schema() -> None:
    consolidated = _consolidated()

    assert set(CONSOLIDATED_REVIEW_COLUMNS).issubset(consolidated.columns)
    assert len(consolidated) == 368
    assert consolidated["consolidation_status"].eq("CONSOLIDATED").sum() == 15


def test_consolidation_preserves_app_wiring_allowed_no() -> None:
    consolidated = _consolidated()

    assert consolidated["app_wiring_allowed"].eq("no").all()


def test_consolidation_preserves_model_input_allowed_no() -> None:
    consolidated = _consolidated()

    assert consolidated["model_input_allowed"].eq("no").all()


def test_consolidated_market_fields_remain_display_only() -> None:
    consolidated = _consolidated()

    assert not consolidated["rank_source"].str.contains("MARKET", case=False).any()
    assert consolidated.loc[
        consolidated["market_match_status"].eq("MATCHED"),
        "dp_market_rank",
    ].ne("").any()


def test_consolidated_full_dynasty_rank_source_not_overwritten() -> None:
    consolidated = _consolidated()
    dynasty_rows = consolidated.loc[consolidated["dynasty_rank"].astype(str).str.strip().ne("")]

    assert not dynasty_rows.empty
    assert dynasty_rows["rank_source"].eq("FULL_DYNASTY_RANK").all()


def test_consolidated_rookies_do_not_get_fabricated_dynasty_rank() -> None:
    consolidated = _consolidated()
    rookies = consolidated.loc[consolidated["player_type"].isin(["ROOKIE", "PROSPECT"])]

    assert len(rookies) == 54
    assert rookies["dynasty_rank"].eq("").all()


def test_consolidation_conflict_rows_are_review_needed() -> None:
    consolidated = _consolidated()
    conflict_rows = consolidated.loc[consolidated["conflict_flags"].astype(str).str.strip().ne("")]

    assert conflict_rows["review_status"].eq("REVIEW_NEEDED").all()


def test_remaining_blockers_file_loads() -> None:
    blockers = pd.read_csv(
        OUTPUT_DIR / "unified_player_universe_v1_remaining_blockers.csv",
        keep_default_na=False,
    )

    assert len(blockers) == 310
    assert blockers["blocker_type"].eq("MISSING_PLAYER_ID").sum() == 5
    assert blockers["blocker_type"].eq("MISSING_AGE").sum() == 42


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
