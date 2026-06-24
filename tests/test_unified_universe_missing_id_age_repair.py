from __future__ import annotations

from pathlib import Path

import pandas as pd

OUTPUT_DIR = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "hq"
    / "model"
    / "unified_player_universe_v0"
)

REPAIR_COLUMNS = {
    "player_name",
    "position",
    "source_layer",
    "player_type",
    "blocker_type",
    "original_player_id",
    "repaired_player_id",
    "original_age",
    "repaired_age",
    "age_source",
    "repair_status",
    "repair_source",
    "confidence",
    "notes",
}
REPAIR_STATUSES = {
    "REPAIRED",
    "NOT_ENOUGH_INFORMATION",
    "CONFLICT_REVIEW_NEEDED",
    "DO_NOT_REPAIR",
}


def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(OUTPUT_DIR / name, keep_default_na=False, dtype=str)


def test_missing_id_age_repair_csv_schema() -> None:
    repair = _csv("unified_player_universe_v1_missing_id_age_repair.csv")

    assert set(repair.columns) == REPAIR_COLUMNS
    assert len(repair) == 47
    assert set(repair["repair_status"]).issubset(REPAIR_STATUSES)


def test_consolidated_artifact_still_loads_after_repair() -> None:
    consolidated = _csv("unified_player_universe_v1_consolidated_review.csv")

    assert len(consolidated) == 368
    assert consolidated["age"].eq("Not enough information").sum() == 17


def test_blocker_counts_update_after_repair() -> None:
    blockers = _csv("unified_player_universe_v1_remaining_blockers.csv")

    assert len(blockers) == 271
    assert blockers["blocker_type"].eq("MISSING_PLAYER_ID").sum() == 5
    assert blockers["blocker_type"].eq("MISSING_AGE").sum() == 16
    assert blockers["blocker_type"].eq("AGE_CONFLICT_REVIEW_NEEDED").sum() == 1


def test_repair_preserves_review_only_gates() -> None:
    consolidated = _csv("unified_player_universe_v1_consolidated_review.csv")

    assert consolidated["app_wiring_allowed"].eq("no").all()
    assert consolidated["model_input_allowed"].eq("no").all()


def test_no_player_id_repair_without_approved_source() -> None:
    repair = _csv("unified_player_universe_v1_missing_id_age_repair.csv")
    player_id_repairs = repair.loc[
        repair["original_player_id"].eq("")
        & repair["repaired_player_id"].astype(str).str.strip().ne("")
    ]

    assert player_id_repairs.empty


def test_age_source_present_for_repaired_ages() -> None:
    repair = _csv("unified_player_universe_v1_missing_id_age_repair.csv")
    repaired_ages = repair.loc[
        repair["repair_status"].eq("REPAIRED")
        & repair["repaired_age"].astype(str).str.strip().ne("")
    ]

    assert not repaired_ages.empty
    assert repaired_ages["age_source"].astype(str).str.strip().ne("").all()


def test_age_conflict_rows_remain_review_needed() -> None:
    consolidated = _csv("unified_player_universe_v1_consolidated_review.csv")
    conflicts = consolidated.loc[
        consolidated["conflict_flags"].astype(str).str.contains("age_conflict_review_needed")
    ]

    assert len(conflicts) == 1
    assert conflicts["review_status"].eq("REVIEW_NEEDED").all()


def test_validation_report_and_source_summary_load_after_repair() -> None:
    report = _csv("unified_player_universe_v1_validation_report.csv")
    summary = _csv("unified_player_universe_v1_source_summary.csv")
    consolidated_row = summary.loc[summary["layer"].eq("Consolidated review output")].iloc[0]
    blockers_row = summary.loc[summary["layer"].eq("Remaining blockers output")].iloc[0]

    assert report["status"].eq("PASS").all()
    assert int(consolidated_row["age_coverage"]) == 351
    assert int(consolidated_row["review_needed_count"]) == 249
    assert int(blockers_row["row_count"]) == 271
