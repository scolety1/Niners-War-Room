from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

NOT_ENOUGH_INFORMATION = "Not enough information"
AS_OF_SEASON = 2026
PRIOR_SEASON = 2025

INJURY_RAW_PATH = Path(
    r"C:\NWR_SHARED_DATA\injury_context\nflreadpy_injuries_review_only_2012_2025.csv"
)
OUTCOME_DISPLAY_PATH = Path(
    "docs/hq/outcomes/outcome_v2_horizon_20260630/outcome_v2_current_player_display.csv"
)
SEASON_LABEL_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended"
    r"\outcome_v2_extended_season_outcome_labels.csv"
)
SHARED_OUTPUT_ROOT = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\injury_context_flags_v0"
)
ENHANCED_OUTCOME_DISPLAY_PATH = Path(
    "docs/hq/outcomes/outcome_v2_horizon_20260630"
    "/outcome_v2_current_player_display_with_injury_context.csv"
)

FLAGS_FILENAME = "injury_context_flags_v0.csv"
MANIFEST_FILENAME = "injury_context_flags_v0_manifest.csv"
COVERAGE_FILENAME = "injury_context_flags_v0_coverage_summary.csv"

MATERIAL_ACTIVE_MIN_GAMES = 8
MATERIAL_ACTIVE_MIN_POINTS = 100.0
MATERIAL_ACTIVE_MAX_FINISH = 36

INJURY_FLAG_COLUMNS = [
    "injury_context_available",
    "most_recent_injury_context_season",
    "prior_season_injury_context_available",
    "prior_season_injury_report_weeks",
    "prior_season_out_or_doubtful_weeks",
    "prior_season_questionable_weeks",
    "missed_prior_season_context_flag",
    "limited_recent_sample",
    "last_materially_active_season",
    "seasons_since_material_activity",
    "availability_caveat",
    "not_enough_information_reason",
    "injury_context_source_status",
    "injury_context_review_only",
    "injury_used_as_model_input",
    "medical_projection_made",
]

FORBIDDEN_MEDICAL_COLUMNS = (
    "injury_risk_score",
    "medical_risk",
    "recovery_probability",
    "comeback_probability",
    "acl_recovery_projection",
    "achilles_recovery_projection",
    "rank_adjustment",
)


@dataclass(frozen=True)
class InjuryContextFlagsResult:
    output_root: Path
    flags_path: Path
    manifest_path: Path
    coverage_path: Path
    enhanced_artifact_path: Path
    flag_rows: int
    enhanced_rows: int
    prior_season_context_rows: int
    missing_feature_rows: int
    rookie_out_of_scope_rows: int
    sha256: str


def load_injury_context_flags_sources(
    *,
    injury_raw_path: str | Path = INJURY_RAW_PATH,
    outcome_display_path: str | Path = OUTCOME_DISPLAY_PATH,
    season_label_path: str | Path = SEASON_LABEL_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = [Path(injury_raw_path), Path(outcome_display_path), Path(season_label_path)]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Injury Context Flags V0 inputs: {missing}")
    return (
        pd.read_csv(injury_raw_path, dtype=str).fillna(""),
        pd.read_csv(outcome_display_path, dtype=str).fillna(""),
        pd.read_csv(season_label_path, dtype=str).fillna(""),
    )


def normalize_injury_context(injury_rows: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        injury_rows,
        {
            "season",
            "week",
            "team",
            "gsis_id",
            "position",
            "full_name",
            "report_status",
            "practice_status",
        },
        "injury_rows",
    )
    frame = injury_rows.copy().fillna("")
    frame["season"] = pd.to_numeric(frame["season"], errors="coerce")
    frame["week"] = pd.to_numeric(frame["week"], errors="coerce")
    frame = frame.dropna(subset=["season", "week", "gsis_id"])
    frame["season"] = frame["season"].astype(int)
    frame["week"] = frame["week"].astype(int)
    frame["gsis_id"] = _text_series(frame, "gsis_id")
    frame["report_status_normalized"] = _text_series(frame, "report_status").str.lower()

    rows: list[dict[str, Any]] = []
    for (gsis_id, season), group in frame.groupby(["gsis_id", "season"], dropna=False):
        status = group["report_status_normalized"]
        out_mask = status.eq("out")
        doubtful_mask = status.eq("doubtful")
        questionable_mask = status.eq("questionable")
        out_or_doubtful = out_mask | doubtful_mask
        rows.append(
            {
                "gsis_id": str(gsis_id),
                "season": int(season),
                "player_name": _first_text(group, "full_name"),
                "position": _first_text(group, "position"),
                "team": _first_text(group, "team"),
                "injury_report_weeks": _distinct_week_count(group),
                "out_report_weeks": _distinct_week_count(group.loc[out_mask]),
                "doubtful_report_weeks": _distinct_week_count(group.loc[doubtful_mask]),
                "out_or_doubtful_weeks": _distinct_week_count(group.loc[out_or_doubtful]),
                "questionable_report_weeks": _distinct_week_count(
                    group.loc[questionable_mask]
                ),
                "injury_context_available": "true",
                "injury_context_source_status": "review_only_nflreadpy_injury_context",
                "medical_projection_made": "false",
            }
        )
    summary = pd.DataFrame(rows)
    if summary.empty:
        return pd.DataFrame(
            columns=[
                "gsis_id",
                "season",
                "player_name",
                "position",
                "team",
                "injury_report_weeks",
                "out_report_weeks",
                "doubtful_report_weeks",
                "out_or_doubtful_weeks",
                "questionable_report_weeks",
                "injury_context_available",
                "injury_context_source_status",
                "medical_projection_made",
            ]
        )
    return summary.sort_values(["gsis_id", "season"]).reset_index(drop=True)


def build_injury_context_flags(
    outcome_display: pd.DataFrame,
    season_injury_context: pd.DataFrame,
    season_labels: pd.DataFrame,
) -> pd.DataFrame:
    _require_columns(
        outcome_display,
        {
            "nwr_player_id",
            "gsis_id",
            "player_name",
            "position",
            "eligibility_status",
            "feature_coverage_status",
            "availability_context_status",
            "caveat_summary",
        },
        "outcome_display",
    )
    _require_columns(
        season_injury_context,
        {
            "gsis_id",
            "season",
            "injury_report_weeks",
            "out_or_doubtful_weeks",
            "questionable_report_weeks",
        },
        "season_injury_context",
    )
    material_lookup = _material_activity_lookup(season_labels)
    injury_lookup = {
        (str(row.gsis_id), int(row.season)): row
        for row in season_injury_context.itertuples(index=False)
    }
    most_recent_injury = _most_recent_injury_lookup(season_injury_context)

    rows: list[dict[str, Any]] = []
    for player in outcome_display.itertuples(index=False):
        gsis_id = str(getattr(player, "gsis_id", "") or "").strip()
        eligibility = str(getattr(player, "eligibility_status", ""))
        feature_status = str(getattr(player, "feature_coverage_status", ""))
        prior = injury_lookup.get((gsis_id, PRIOR_SEASON))
        material = _last_material_activity(
            gsis_id=gsis_id,
            eligibility_status=eligibility,
            feature_coverage_status=feature_status,
            material_lookup=material_lookup,
        )
        row = {
            "nwr_player_id": str(getattr(player, "nwr_player_id", "")),
            "sleeper_id": str(getattr(player, "sleeper_id", "")),
            "gsis_id": gsis_id,
            "player_name": str(getattr(player, "player_name", "")),
            "position": str(getattr(player, "position", "")),
            "team": str(getattr(player, "team", "")),
            "eligibility_status": eligibility,
            "feature_coverage_status": feature_status,
            "injury_context_available": (
                "true" if gsis_id in most_recent_injury else NOT_ENOUGH_INFORMATION
            ),
            "most_recent_injury_context_season": most_recent_injury.get(
                gsis_id,
                NOT_ENOUGH_INFORMATION,
            ),
            "prior_season_injury_context_available": (
                "true" if prior is not None else NOT_ENOUGH_INFORMATION
            ),
            "prior_season_injury_report_weeks": _context_count(prior, "injury_report_weeks"),
            "prior_season_out_or_doubtful_weeks": _context_count(
                prior,
                "out_or_doubtful_weeks",
            ),
            "prior_season_questionable_weeks": _context_count(
                prior,
                "questionable_report_weeks",
            ),
            "last_materially_active_season": material,
            "seasons_since_material_activity": _seasons_since(material),
            "injury_context_source_status": "review_only_nflreadpy_injury_context",
            "injury_context_review_only": "true",
            "injury_used_as_model_input": "false",
            "medical_projection_made": "false",
        }
        row["limited_recent_sample"] = _limited_recent_sample_status(
            eligibility,
            material,
        )
        row["missed_prior_season_context_flag"] = _missed_prior_context_flag(
            eligibility,
            prior,
        )
        row["availability_caveat"] = _availability_caveat(row)
        row["not_enough_information_reason"] = _not_enough_information_reason(row)
        rows.append(row)
    return pd.DataFrame(rows, columns=_flag_output_columns())


def build_enhanced_outcome_display_artifact(
    outcome_display: pd.DataFrame,
    injury_flags: pd.DataFrame,
) -> pd.DataFrame:
    _require_columns(outcome_display, {"nwr_player_id", "gsis_id"}, "outcome_display")
    _require_columns(
        injury_flags,
        {"nwr_player_id", "gsis_id", *INJURY_FLAG_COLUMNS},
        "injury_flags",
    )
    original = outcome_display.copy()
    flags = injury_flags[["nwr_player_id", "gsis_id", *INJURY_FLAG_COLUMNS]].copy()
    merged = original.merge(
        flags,
        on=["nwr_player_id", "gsis_id"],
        how="left",
        validate="one_to_one",
    )
    for column in INJURY_FLAG_COLUMNS:
        if column not in merged.columns:
            merged[column] = NOT_ENOUGH_INFORMATION
        merged[column] = merged[column].fillna(NOT_ENOUGH_INFORMATION).astype(str)
    _validate_no_probability_changes(original, merged)
    _validate_no_forbidden_medical_columns(merged)
    return merged


def write_injury_context_flags_v0_artifacts(
    *,
    output_root: str | Path = SHARED_OUTPUT_ROOT,
    enhanced_artifact_path: str | Path = ENHANCED_OUTCOME_DISPLAY_PATH,
    injury_raw_path: str | Path = INJURY_RAW_PATH,
    outcome_display_path: str | Path = OUTCOME_DISPLAY_PATH,
    season_label_path: str | Path = SEASON_LABEL_PATH,
) -> InjuryContextFlagsResult:
    injury_rows, outcome_display, season_labels = load_injury_context_flags_sources(
        injury_raw_path=injury_raw_path,
        outcome_display_path=outcome_display_path,
        season_label_path=season_label_path,
    )
    season_injury_context = normalize_injury_context(injury_rows)
    flags = build_injury_context_flags(outcome_display, season_injury_context, season_labels)
    enhanced = build_enhanced_outcome_display_artifact(outcome_display, flags)

    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    flags_path = output / FLAGS_FILENAME
    manifest_path = output / MANIFEST_FILENAME
    coverage_path = output / COVERAGE_FILENAME
    enhanced_path = Path(enhanced_artifact_path)
    enhanced_path.parent.mkdir(parents=True, exist_ok=True)

    flags.to_csv(flags_path, index=False, quoting=csv.QUOTE_MINIMAL)
    enhanced.to_csv(enhanced_path, index=False, quoting=csv.QUOTE_MINIMAL)
    coverage_rows = _coverage_summary_rows(
        injury_rows=injury_rows,
        season_injury_context=season_injury_context,
        flags=flags,
        enhanced=enhanced,
    )
    _write_csv(coverage_path, coverage_rows)
    _write_csv(
        manifest_path,
        _manifest_rows(
            injury_raw_path=Path(injury_raw_path),
            outcome_display_path=Path(outcome_display_path),
            season_label_path=Path(season_label_path),
            flags_path=flags_path,
            coverage_path=coverage_path,
            enhanced_path=enhanced_path,
            injury_rows=injury_rows,
            flags=flags,
            enhanced=enhanced,
        ),
    )
    return InjuryContextFlagsResult(
        output_root=output,
        flags_path=flags_path,
        manifest_path=manifest_path,
        coverage_path=coverage_path,
        enhanced_artifact_path=enhanced_path,
        flag_rows=len(flags),
        enhanced_rows=len(enhanced),
        prior_season_context_rows=int(
            flags["prior_season_injury_context_available"].eq("true").sum()
        ),
        missing_feature_rows=int(
            flags["eligibility_status"].eq("missing_current_feature_coverage").sum()
        ),
        rookie_out_of_scope_rows=int(
            flags["eligibility_status"].eq("out_of_scope_rookie_or_prospect").sum()
        ),
        sha256=_sha256(enhanced_path),
    )


def _material_activity_lookup(season_labels: pd.DataFrame) -> dict[str, int]:
    _require_columns(
        season_labels,
        {"player_id", "season", "fantasy_points", "position_finish", "games_played"},
        "season_labels",
    )
    frame = season_labels.copy()
    frame["season"] = pd.to_numeric(frame["season"], errors="coerce")
    frame["fantasy_points"] = pd.to_numeric(frame["fantasy_points"], errors="coerce")
    frame["position_finish"] = pd.to_numeric(frame["position_finish"], errors="coerce")
    frame["games_played"] = pd.to_numeric(frame["games_played"], errors="coerce")
    material = frame[
        (frame["games_played"] >= MATERIAL_ACTIVE_MIN_GAMES)
        | (frame["fantasy_points"] >= MATERIAL_ACTIVE_MIN_POINTS)
        | (frame["position_finish"] <= MATERIAL_ACTIVE_MAX_FINISH)
    ].copy()
    lookup: dict[str, int] = {}
    for player_id, group in material.groupby("player_id"):
        seasons = pd.to_numeric(group["season"], errors="coerce").dropna()
        if not seasons.empty:
            lookup[str(player_id)] = int(seasons.max())
    return lookup


def _last_material_activity(
    *,
    gsis_id: str,
    eligibility_status: str,
    feature_coverage_status: str,
    material_lookup: dict[str, int],
) -> str:
    if eligibility_status == "out_of_scope_rookie_or_prospect":
        return "out_of_scope_rookie_or_prospect"
    if eligibility_status == "out_of_scope_unsupported_position":
        return NOT_ENOUGH_INFORMATION
    if feature_coverage_status == "feature_covered_2025_regular_season":
        return str(PRIOR_SEASON)
    value = material_lookup.get(gsis_id)
    return str(value) if value is not None else NOT_ENOUGH_INFORMATION


def _seasons_since(material: str) -> str:
    value = pd.to_numeric(material, errors="coerce")
    if pd.isna(value):
        return NOT_ENOUGH_INFORMATION
    return str(max(0, AS_OF_SEASON - int(value)))


def _limited_recent_sample_status(eligibility_status: str, material: str) -> str:
    if eligibility_status == "out_of_scope_rookie_or_prospect":
        return "out_of_scope_rookie_or_prospect"
    if eligibility_status == "out_of_scope_unsupported_position":
        return NOT_ENOUGH_INFORMATION
    if eligibility_status == "missing_current_feature_coverage":
        return "true_missing_2025_feature_row"
    material_year = pd.to_numeric(material, errors="coerce")
    if pd.isna(material_year):
        return NOT_ENOUGH_INFORMATION
    if int(material_year) < PRIOR_SEASON:
        return "true_last_material_activity_before_2025"
    return "false"


def _missed_prior_context_flag(eligibility_status: str, prior: Any | None) -> str:
    if eligibility_status == "out_of_scope_rookie_or_prospect":
        return "out_of_scope_rookie_or_prospect"
    if eligibility_status == "missing_current_feature_coverage":
        return "true_missing_2025_feature_row"
    if prior is None:
        return NOT_ENOUGH_INFORMATION
    out_or_doubtful = _numeric_attr(prior, "out_or_doubtful_weeks")
    if out_or_doubtful > 0:
        return "review_required_prior_out_or_doubtful_context"
    return "false"


def _availability_caveat(row: dict[str, Any]) -> str:
    prior_available = row["prior_season_injury_context_available"] == "true"
    if prior_available:
        return (
            f"Review-only injury context: {row['prior_season_injury_report_weeks']} "
            f"report weeks in {PRIOR_SEASON}; "
            f"{row['prior_season_out_or_doubtful_weeks']} out/doubtful weeks. "
            "This is not a medical projection and does not change Outcome probabilities."
        )
    return (
        f"No review-only injury context row found for {PRIOR_SEASON}; missing injury "
        "context is not clean health and does not change Outcome probabilities."
    )


def _not_enough_information_reason(row: dict[str, Any]) -> str:
    eligibility = row["eligibility_status"]
    if eligibility == "missing_current_feature_coverage":
        return (
            "No approved 2025 Outcome V2 feature row; keep Outcome V2 fields as "
            f"{NOT_ENOUGH_INFORMATION}, not low probability. {row['availability_caveat']}"
        )
    if eligibility == "out_of_scope_rookie_or_prospect":
        return (
            "Normal Outcome V2 excludes rookies/prospects; injury context does not "
            "create rookie probabilities."
        )
    if eligibility == "out_of_scope_unsupported_position":
        return "Unsupported Outcome V2 position; injury context does not create probabilities."
    if row["missed_prior_season_context_flag"].startswith("review_required"):
        return (
            "Outcome V2 probabilities are unchanged; injury context is a review-only "
            "availability caveat, not a model input."
        )
    return (
        "Outcome V2 feature coverage is available where probabilities appear; missing "
        "injury context is not clean health."
    )


def _most_recent_injury_lookup(season_injury_context: pd.DataFrame) -> dict[str, str]:
    lookup: dict[str, str] = {}
    if season_injury_context.empty:
        return lookup
    for gsis_id, group in season_injury_context.groupby("gsis_id"):
        seasons = pd.to_numeric(group["season"], errors="coerce").dropna()
        if not seasons.empty:
            lookup[str(gsis_id)] = str(int(seasons.max()))
    return lookup


def _context_count(prior: Any | None, field: str) -> str:
    if prior is None:
        return NOT_ENOUGH_INFORMATION
    value = _numeric_attr(prior, field)
    return str(int(value))


def _numeric_attr(row: Any, field: str) -> float:
    value = getattr(row, field, 0)
    converted = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(converted) if pd.notna(converted) else 0.0


def _coverage_summary_rows(
    *,
    injury_rows: pd.DataFrame,
    season_injury_context: pd.DataFrame,
    flags: pd.DataFrame,
    enhanced: pd.DataFrame,
) -> list[dict[str, Any]]:
    return [
        {"metric": "raw_injury_rows", "value": len(injury_rows)},
        {"metric": "injury_season_summary_rows", "value": len(season_injury_context)},
        {"metric": "current_display_rows", "value": len(enhanced)},
        {"metric": "flag_rows", "value": len(flags)},
        {
            "metric": "players_with_any_injury_context",
            "value": int(flags["injury_context_available"].eq("true").sum()),
        },
        {
            "metric": "players_with_2025_injury_context",
            "value": int(flags["prior_season_injury_context_available"].eq("true").sum()),
        },
        {
            "metric": "players_with_prior_out_or_doubtful_context",
            "value": int(
                pd.to_numeric(
                    flags["prior_season_out_or_doubtful_weeks"],
                    errors="coerce",
                )
                .fillna(0)
                .gt(0)
                .sum()
            ),
        },
        {
            "metric": "missing_current_feature_coverage_rows",
            "value": int(flags["eligibility_status"].eq("missing_current_feature_coverage").sum()),
        },
        {
            "metric": "rookie_out_of_scope_rows",
            "value": int(flags["eligibility_status"].eq("out_of_scope_rookie_or_prospect").sum()),
        },
        {
            "metric": "medical_projection_made_values",
            "value": "|".join(sorted(flags["medical_projection_made"].unique())),
        },
        {
            "metric": "injury_used_as_model_input_values",
            "value": "|".join(sorted(flags["injury_used_as_model_input"].unique())),
        },
    ]


def _manifest_rows(
    *,
    injury_raw_path: Path,
    outcome_display_path: Path,
    season_label_path: Path,
    flags_path: Path,
    coverage_path: Path,
    enhanced_path: Path,
    injury_rows: pd.DataFrame,
    flags: pd.DataFrame,
    enhanced: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows = [
        {
            "artifact": "source_review_only_injury_context",
            "path": str(injury_raw_path),
            "rows": len(injury_rows),
            "sha256": _sha256(injury_raw_path),
            "tracked_in_git": "false",
        },
        {
            "artifact": "source_outcome_v2_current_display",
            "path": str(outcome_display_path),
            "rows": len(enhanced),
            "sha256": _sha256(outcome_display_path),
            "tracked_in_git": "true",
        },
        {
            "artifact": "source_extended_season_labels",
            "path": str(season_label_path),
            "rows": "",
            "sha256": _sha256(season_label_path),
            "tracked_in_git": "false",
        },
        {
            "artifact": "injury_context_flags_v0",
            "path": str(flags_path),
            "rows": len(flags),
            "sha256": _sha256(flags_path),
            "tracked_in_git": "false",
        },
        {
            "artifact": "injury_context_flags_v0_coverage_summary",
            "path": str(coverage_path),
            "rows": "",
            "sha256": _sha256(coverage_path),
            "tracked_in_git": "false",
        },
        {
            "artifact": "enhanced_outcome_v2_display_with_injury_context",
            "path": str(enhanced_path),
            "rows": len(enhanced),
            "sha256": _sha256(enhanced_path),
            "tracked_in_git": "true",
        },
    ]
    for row in rows:
        row.update(
            {
                "display_only": "true",
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "source_truth_allowed": "false",
                "app_wiring_allowed": "false",
                "medical_projection_made": "false",
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
    return rows


def _validate_no_probability_changes(original: pd.DataFrame, enhanced: pd.DataFrame) -> None:
    original_columns = list(original.columns)
    changed = []
    for column in original_columns:
        if column not in enhanced.columns:
            changed.append(column)
            continue
        if not original[column].astype(str).equals(enhanced[column].astype(str)):
            changed.append(column)
    if changed:
        raise ValueError(f"Enhanced artifact changed existing Outcome V2 columns: {changed}")


def _validate_no_forbidden_medical_columns(frame: pd.DataFrame) -> None:
    lower_columns = {column.lower() for column in frame.columns}
    forbidden = [column for column in FORBIDDEN_MEDICAL_COLUMNS if column in lower_columns]
    if forbidden:
        raise ValueError(f"Forbidden medical/rank fields present: {forbidden}")


def _flag_output_columns() -> list[str]:
    return [
        "nwr_player_id",
        "sleeper_id",
        "gsis_id",
        "player_name",
        "position",
        "team",
        "eligibility_status",
        "feature_coverage_status",
        *INJURY_FLAG_COLUMNS,
    ]


def _distinct_week_count(frame: pd.DataFrame) -> int:
    if frame.empty or "week" not in frame.columns:
        return 0
    return int(pd.to_numeric(frame["week"], errors="coerce").dropna().nunique())


def _first_text(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns or frame.empty:
        return ""
    values = _text_series(frame, column)
    non_empty = values[values.ne("")]
    return str(non_empty.iloc[0]) if not non_empty.empty else ""


def _text_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([""] * len(frame), index=frame.index)
    return frame[column].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = _fieldnames(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    return fieldnames


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
