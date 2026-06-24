from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "docs" / "hq" / "model" / "unified_player_universe_v0"

CONSOLIDATED_REVIEW_PATH = OUTPUT_DIR / "unified_player_universe_v1_consolidated_review.csv"
REMAINING_BLOCKERS_PATH = OUTPUT_DIR / "unified_player_universe_v1_remaining_blockers.csv"
CONSOLIDATION_DECISIONS_PATH = OUTPUT_DIR / "unified_player_universe_v1_consolidation_decisions.csv"
SOURCE_SUMMARY_PATH = OUTPUT_DIR / "unified_player_universe_v1_source_summary.csv"
VALIDATION_REPORT_PATH = OUTPUT_DIR / "unified_player_universe_v1_validation_report.csv"

NOT_ENOUGH_INFORMATION = "Not enough information"
REVIEW_TABLE_COLUMNS = [
    "player_name",
    "position",
    "nfl_team",
    "player_type",
    "age",
    "age_source",
    "player_id",
    "rank_source",
    "dynasty_rank",
    "rookie_rank",
    "frozen_baseline_rank",
    "candidate_rank",
    "unified_display_rank",
    "review_status",
    "data_quality_status",
    "manual_review_flag",
    "caveats",
    "source_layers",
]
BLOCKER_TABLE_COLUMNS = [
    "blocker_type",
    "player_name",
    "position",
    "source_layer",
    "prevents_app_wiring",
    "recommended_action",
    "detail",
]
CONSOLIDATION_TABLE_COLUMNS = [
    "duplicate_group_id",
    "player_name",
    "position",
    "source_layers",
    "decision",
    "confidence",
    "conflicts",
    "action_taken",
    "notes",
]


@dataclass(frozen=True)
class UnifiedUniverseReviewData:
    consolidated: pd.DataFrame
    blockers: pd.DataFrame
    consolidation_decisions: pd.DataFrame
    source_summary: pd.DataFrame
    validation_report: pd.DataFrame
    summary: dict[str, object]


def load_unified_universe_review_data(
    output_dir: Path = OUTPUT_DIR,
) -> UnifiedUniverseReviewData:
    consolidated = _read_csv(output_dir / CONSOLIDATED_REVIEW_PATH.name)
    blockers = _read_csv(output_dir / REMAINING_BLOCKERS_PATH.name)
    decisions = _read_csv(output_dir / CONSOLIDATION_DECISIONS_PATH.name)
    source_summary = _read_csv(output_dir / SOURCE_SUMMARY_PATH.name)
    validation_report = _read_csv(output_dir / VALIDATION_REPORT_PATH.name)
    return UnifiedUniverseReviewData(
        consolidated=consolidated,
        blockers=blockers,
        consolidation_decisions=decisions,
        source_summary=source_summary,
        validation_report=validation_report,
        summary=build_summary_counts(consolidated, blockers),
    )


def build_summary_counts(
    consolidated: pd.DataFrame,
    blockers: pd.DataFrame,
) -> dict[str, object]:
    blocker_counts = _value_counts(blockers, "blocker_type")
    return {
        "consolidated_row_count": int(len(consolidated)),
        "veteran_count": int(consolidated["player_type"].astype(str).eq("VETERAN").sum()),
        "rookie_prospect_count": int(
            consolidated["player_type"].astype(str).isin(["ROOKIE", "PROSPECT"]).sum()
        ),
        "pdf_fa_count": int(consolidated["player_type"].astype(str).eq("PDF_FA").sum()),
        "blocker_count": int(len(blockers)),
        "missing_player_id_count": int(blocker_counts.get("MISSING_PLAYER_ID", 0)),
        "missing_age_count": int(blocker_counts.get("MISSING_AGE", 0)),
        "review_needed_count": int(
            consolidated["review_status"].astype(str).eq("REVIEW_NEEDED").sum()
        ),
        "app_wiring_allowed": _all_no(consolidated, "app_wiring_allowed"),
        "model_input_allowed": _all_no(consolidated, "model_input_allowed"),
    }


def filter_review_table(
    consolidated: pd.DataFrame,
    *,
    player_types: list[str] | None = None,
    source_layers: list[str] | None = None,
    positions: list[str] | None = None,
    review_statuses: list[str] | None = None,
    missing_player_id: str = "All",
    missing_age: str = "All",
    market_statuses: list[str] | None = None,
    outcome_statuses: list[str] | None = None,
    manual_review_flags: list[str] | None = None,
) -> pd.DataFrame:
    frame = consolidated.copy()
    frame = _filter_in(frame, "player_type", player_types)
    frame = _filter_contains_any(frame, "source_layers", source_layers)
    frame = _filter_in(frame, "position", positions)
    frame = _filter_in(frame, "review_status", review_statuses)
    frame = _filter_in(frame, "market_match_status", market_statuses)
    frame = _filter_in(frame, "outcome_status", outcome_statuses)
    frame = _filter_in(frame, "manual_review_flag", manual_review_flags)
    if missing_player_id == "Missing only":
        frame = frame.loc[frame["player_id"].astype(str).str.strip().eq("")]
    elif missing_player_id == "Has player_id":
        frame = frame.loc[frame["player_id"].astype(str).str.strip().ne("")]
    if missing_age == "Missing only":
        frame = frame.loc[frame["age"].astype(str).eq(NOT_ENOUGH_INFORMATION)]
    elif missing_age == "Has age":
        frame = frame.loc[frame["age"].astype(str).ne(NOT_ENOUGH_INFORMATION)]
    return frame.reset_index(drop=True)


def filter_blockers(
    blockers: pd.DataFrame,
    *,
    blocker_types: list[str] | None = None,
) -> pd.DataFrame:
    return _filter_in(blockers.copy(), "blocker_type", blocker_types).reset_index(drop=True)


def table_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    existing = [column for column in columns if column in frame.columns]
    return frame.loc[:, existing].copy()


def options_for(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame.columns:
        return []
    values: set[str] = set()
    for value in frame[column].astype(str).tolist():
        for part in value.split(";"):
            cleaned = part.strip()
            if cleaned:
                values.add(cleaned)
    return sorted(values)


def export_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False)


def _value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame[column].value_counts().items()}


def _all_no(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return "missing"
    return "no" if frame[column].astype(str).str.lower().eq("no").all() else "mixed"


def _filter_in(
    frame: pd.DataFrame,
    column: str,
    selected: list[str] | None,
) -> pd.DataFrame:
    if not selected or column not in frame.columns:
        return frame
    return frame.loc[frame[column].astype(str).isin(selected)]


def _filter_contains_any(
    frame: pd.DataFrame,
    column: str,
    selected: list[str] | None,
) -> pd.DataFrame:
    if not selected or column not in frame.columns:
        return frame
    mask = frame[column].astype(str).map(
        lambda value: any(_contains_layer(value, layer) for layer in selected)
    )
    return frame.loc[mask]


def _contains_layer(value: str, layer: str) -> bool:
    return layer in {part.strip() for part in value.split(";")}
