from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = Path(r"C:\NWR_SHARED_DATA\backtests\backtest_v1_feature_cleanup_20260621")
FEATURE_SOURCE = SOURCE_ROOT / "feature_dataset_v1_clean_expanded.csv"
LABEL_SOURCE = SOURCE_ROOT / "labels_v1.csv"
MANIFEST_SOURCE = SOURCE_ROOT / "build_manifest_v1.json"
MISSINGNESS_SOURCE = SOURCE_ROOT / "feature_missingness_summary_v1.csv"
WHITELIST_SOURCE = SOURCE_ROOT / "feature_whitelist_by_position_v1.csv"
EXCLUDED_SOURCE = SOURCE_ROOT / "excluded_features_v1.csv"
OLDER_PROBE_DIR = Path(
    r"C:\NWR_SHARED_DATA\backtests\historical_tuning_substrate_expansion_v1_20260701_probe_2012_2025"
)
OUTCOME_2000_PROBE = Path(r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_2000_probe")
OVERNIGHT_TUNE_DIR = Path(r"C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v1_expanded_20260622")

BASE_HEAD = "2e11d704179c46bfd72862c660d888de51922271"
BRANCH = "work/historical-tuning-substrate-expansion-v1-20260701"
VERDICT = "YELLOW_SUBSTRATE_VALIDATED_REVIEW_ONLY_NEEDS_SOURCE_EXPANSION_BEFORE_FORMULA_SEARCH"

PARQUET_NAME = "nwr_historical_tuning_feature_target_substrate_v1.parquet"
PARQUET_PATH = EXPERIMENT_DIR / PARQUET_NAME


SAFE_FEATURES: list[dict[str, str]] = [
    {
        "canonical": "prior_nwr_points",
        "source": "feature_nwr_points",
        "description": "Prior feature-season total NWR scoring from local Backtest V1.",
    },
    {
        "canonical": "prior_games",
        "source": "feature_games",
        "description": "Prior feature-season games with stats from local Backtest V1.",
    },
    {
        "canonical": "prior_nwr_ppg",
        "source": "feature_nwr_ppg",
        "description": "Prior feature-season NWR points per game from local Backtest V1.",
    },
    {"canonical": "prior_targets", "source": "targets", "description": "Prior feature-season targets."},
    {"canonical": "prior_carries", "source": "carries", "description": "Prior feature-season carries."},
    {"canonical": "prior_receptions", "source": "receptions", "description": "Prior feature-season receptions."},
    {
        "canonical": "prior_rushing_yards",
        "source": "rushing_yards",
        "description": "Prior feature-season rushing yards.",
    },
    {
        "canonical": "prior_receiving_yards",
        "source": "receiving_yards",
        "description": "Prior feature-season receiving yards.",
    },
    {
        "canonical": "prior_receiving_air_yards",
        "source": "receiving_air_yards",
        "description": "Prior feature-season receiving air yards where available in Backtest V1.",
    },
    {
        "canonical": "prior_receiving_yards_after_catch",
        "source": "receiving_yards_after_catch",
        "description": "Prior feature-season receiving yards after catch where available in Backtest V1.",
    },
    {
        "canonical": "prior_rushing_first_downs",
        "source": "rushing_first_downs",
        "description": "Prior feature-season rushing first downs.",
    },
    {
        "canonical": "prior_receiving_first_downs",
        "source": "receiving_first_downs",
        "description": "Prior feature-season receiving first downs.",
    },
    {
        "canonical": "prior_passing_attempts",
        "source": "attempts",
        "description": "Prior feature-season passing attempts.",
    },
    {
        "canonical": "prior_passing_completions",
        "source": "completions",
        "description": "Prior feature-season passing completions.",
    },
    {
        "canonical": "prior_passing_yards",
        "source": "passing_yards",
        "description": "Prior feature-season passing yards.",
    },
    {
        "canonical": "prior_passing_td",
        "source": "passing_tds",
        "description": "Prior feature-season passing touchdowns.",
    },
    {
        "canonical": "prior_interceptions",
        "source": "passing_interceptions",
        "description": "Prior feature-season passing interceptions.",
    },
    {
        "canonical": "prior_passing_first_downs",
        "source": "passing_first_downs",
        "description": "Prior feature-season passing first downs.",
    },
    {
        "canonical": "prior_offensive_snaps",
        "source": "offense_snaps",
        "description": "Prior feature-season offensive snaps where available in Backtest V1.",
    },
    {
        "canonical": "prior_offense_pct",
        "source": "offense_pct",
        "description": "Prior feature-season offensive snap share where available in Backtest V1.",
    },
]

DERIVED_FEATURES: list[dict[str, str]] = [
    {
        "canonical": "prior_touches",
        "left": "prior_carries",
        "right": "prior_receptions",
        "description": "Derived as prior carries plus prior receptions from source V1 values.",
    },
    {
        "canonical": "prior_opportunities",
        "left": "prior_carries",
        "right": "prior_targets",
        "description": "Derived as prior carries plus prior targets from source V1 values.",
    },
]

TARGET_COLUMNS = [
    "target_games",
    "next_nwr_points",
    "next_nwr_ppg",
    "next_position_finish",
    "qb_t12",
    "rb_t12",
    "rb_t24",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
    "startable_hit",
    "startable_bucket",
]

FORBIDDEN_CANONICAL_COLUMN_TOKENS = [
    "route",
    "tprr",
    "yprr",
    "rz_att",
    "adp",
    "market",
    "projection",
    "vendor",
    "depth",
    "injury",
    "schedule",
    "active_weeks",
    "is_active_any_week",
]


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_row_count(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        row_count = sum(1 for _ in handle)
    return max(row_count - 1, 0)


def read_manifest() -> dict[str, Any]:
    if not MANIFEST_SOURCE.exists():
        return {}
    return json.loads(MANIFEST_SOURCE.read_text(encoding="utf-8"))


def require_sources() -> None:
    missing = [path for path in [FEATURE_SOURCE, LABEL_SOURCE, MANIFEST_SOURCE] if not path.exists()]
    if missing:
        formatted = "\n".join(str(path) for path in missing)
        raise FileNotFoundError(f"Required local substrate sources are missing:\n{formatted}")


def stable_row_id(player_id: str, feature_season: int, target_season: int) -> str:
    key = f"{player_id}|{feature_season}|{target_season}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"nwr_hts_v1_{digest}"


def build_substrate(features: pd.DataFrame, labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_keys = features[["player_id", "feature_season", "target_season", "position", "player_name"]].copy()
    label_keys = labels[["player_id", "target_season", "target_position", "target_player_name"]].copy()
    join_audit = feature_keys.merge(
        label_keys,
        on=["player_id", "target_season"],
        how="outer",
        indicator=True,
        suffixes=("_feature", "_target"),
    )

    labels_ranked = labels.sort_values(
        ["target_season", "target_position", "next_nwr_points", "player_id"],
        ascending=[True, True, False, True],
    ).copy()
    labels_ranked["next_position_finish"] = (
        labels_ranked.groupby(["target_season", "target_position"]).cumcount() + 1
    )
    labels_with_finish = labels.merge(
        labels_ranked[["player_id", "target_season", "next_position_finish"]],
        on=["player_id", "target_season"],
        how="left",
    )

    joined = features.merge(labels_with_finish, on=["player_id", "target_season"], how="inner")
    rows = pd.DataFrame()
    rows["substrate_row_id"] = [
        stable_row_id(player_id, int(feature_season), int(target_season))
        for player_id, feature_season, target_season in zip(
            joined["player_id"], joined["feature_season"], joined["target_season"]
        )
    ]
    rows["player_id_gsis"] = joined["player_id"].astype(str)
    rows["feature_season"] = joined["feature_season"].astype(int)
    rows["target_season"] = joined["target_season"].astype(int)
    rows["feature_target_year_lag"] = rows["target_season"] - rows["feature_season"]
    rows["position"] = joined["position"].astype(str)
    rows["target_position"] = joined["target_position"].astype(str)
    rows["feature_player_name"] = joined["player_name"].astype(str)
    rows["feature_team"] = joined["recent_team"].astype(str)
    rows["target_player_name"] = joined["target_player_name"].astype(str)
    rows["target_team"] = joined["target_team"].astype(str)

    for feature in SAFE_FEATURES:
        rows[feature["canonical"]] = joined[feature["source"]]

    for feature in DERIVED_FEATURES:
        rows[feature["canonical"]] = rows[feature["left"]] + rows[feature["right"]]

    for col in [
        "target_games",
        "next_nwr_points",
        "next_nwr_ppg",
        "next_position_finish",
        "qb_t12",
        "rb_t12",
        "rb_t24",
        "wr_t12",
        "wr_t24",
        "wr_t36",
        "te_t12",
    ]:
        rows[col] = joined[col]

    rows["startable_hit"] = (
        ((rows["target_position"] == "QB") & (rows["qb_t12"] == 1))
        | ((rows["target_position"] == "RB") & (rows["rb_t24"] == 1))
        | ((rows["target_position"] == "WR") & (rows["wr_t36"] == 1))
        | ((rows["target_position"] == "TE") & (rows["te_t12"] == 1))
    )
    rows["startable_bucket"] = "OUTSIDE_STARTABLE"
    rows.loc[(rows["target_position"] == "QB") & (rows["qb_t12"] == 1), "startable_bucket"] = "QB_TOP12"
    rows.loc[(rows["target_position"] == "RB") & (rows["rb_t24"] == 1), "startable_bucket"] = "RB_TOP24"
    rows.loc[(rows["target_position"] == "WR") & (rows["wr_t36"] == 1), "startable_bucket"] = "WR_TOP36"
    rows.loc[(rows["target_position"] == "TE") & (rows["te_t12"] == 1), "startable_bucket"] = "TE_TOP12"

    rows["feature_source_artifact"] = str(FEATURE_SOURCE)
    rows["target_source_artifact"] = str(LABEL_SOURCE)
    rows["source_lineage"] = "local Backtest V1 feature cleanup filtered into canonical review-only substrate"
    rows["feature_asof_rule"] = "Use only completed feature season N facts before the season N+1 prediction anchor."
    rows["target_window"] = "Full target season N+1 outcomes only."
    rows["leakage_check_result"] = "PASS_FEATURE_N_TARGET_N_PLUS_1_SEPARATED"
    rows["asof_check_result"] = "PASS_NO_TARGET_SEASON_CONTEXT_IN_FEATURE_COLUMNS"
    rows["source_missingness_policy"] = (
        "No new zero fill in this builder. Source Backtest V1 may encode stat absence or unavailable optional "
        "sources as zero with separate missingness metadata; see missingness_semantics_report.md."
    )
    rows["missingness_metadata_source"] = str(MISSINGNESS_SOURCE)
    rows["review_only"] = True
    rows["model_use_allowed"] = False
    rows["training_allowed"] = False
    rows["source_truth_allowed"] = False
    rows["hidden_sort_allowed"] = False
    rows["recommendation_allowed"] = False
    rows["production_approved"] = False

    validate_substrate(rows)
    return rows, join_audit


def validate_substrate(rows: pd.DataFrame) -> None:
    if not (rows["feature_target_year_lag"] == 1).all():
        raise ValueError("Substrate includes rows where target season is not feature season plus one.")
    forbidden_hits = []
    for col in rows.columns:
        lower = col.lower()
        for token in FORBIDDEN_CANONICAL_COLUMN_TOKENS:
            if token in lower:
                forbidden_hits.append(col)
                break
    if forbidden_hits:
        raise ValueError(f"Forbidden canonical columns present: {sorted(set(forbidden_hits))}")
    if rows["production_approved"].any():
        raise ValueError("Substrate contains production-approved rows.")
    if rows["model_use_allowed"].any() or rows["training_allowed"].any():
        raise ValueError("Substrate contains model/training allowed rows.")


def write_csv(df: pd.DataFrame, filename: str) -> Path:
    path = EXPERIMENT_DIR / filename
    df.to_csv(path, index=False)
    return path


def make_feature_coverage(rows: pd.DataFrame) -> pd.DataFrame:
    feature_cols = [feature["canonical"] for feature in SAFE_FEATURES] + [
        feature["canonical"] for feature in DERIVED_FEATURES
    ]
    records = []
    descriptions = {feature["canonical"]: feature["description"] for feature in SAFE_FEATURES + DERIVED_FEATURES}
    source_columns = {feature["canonical"]: feature.get("source", "derived") for feature in SAFE_FEATURES + DERIVED_FEATURES}
    for col in feature_cols:
        series = pd.to_numeric(rows[col], errors="coerce")
        records.append(
            {
                "feature": col,
                "source_column": source_columns[col],
                "rows": len(rows),
                "non_null_count": int(series.notna().sum()),
                "null_count": int(series.isna().sum()),
                "coverage_rate": round(float(series.notna().mean()), 6),
                "zero_count": int((series.fillna(0) == 0).sum()),
                "zero_rate": round(float((series.fillna(0) == 0).mean()), 6),
                "non_zero_count": int((series.fillna(0) != 0).sum()),
                "min_value": round(float(series.min()), 6) if series.notna().any() else None,
                "max_value": round(float(series.max()), 6) if series.notna().any() else None,
                "mean_value": round(float(series.mean()), 6) if series.notna().any() else None,
                "missingness_note": "No new zero fill in builder; source V1 missingness semantics apply.",
                "description": descriptions[col],
            }
        )
    return pd.DataFrame(records)


def make_target_coverage(rows: pd.DataFrame) -> pd.DataFrame:
    records = []
    for col in TARGET_COLUMNS:
        series = rows[col]
        record: dict[str, Any] = {
            "target_outcome": col,
            "rows": len(rows),
            "non_null_count": int(series.notna().sum()),
            "null_count": int(series.isna().sum()),
            "coverage_rate": round(float(series.notna().mean()), 6),
            "source": "labels_v1.csv plus deterministic position finish/startable derivations",
        }
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce")
            record["positive_or_true_count"] = int((numeric.fillna(0) > 0).sum())
            record["min_value"] = round(float(numeric.min()), 6) if numeric.notna().any() else None
            record["max_value"] = round(float(numeric.max()), 6) if numeric.notna().any() else None
            record["mean_value"] = round(float(numeric.mean()), 6) if numeric.notna().any() else None
        else:
            record["positive_or_true_count"] = int((series.astype(str) != "").sum())
            record["min_value"] = ""
            record["max_value"] = ""
            record["mean_value"] = ""
        records.append(record)
    return pd.DataFrame(records)


def make_row_count_report(rows: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        rows.groupby(["feature_season", "target_season", "position"], dropna=False)
        .agg(
            row_count=("substrate_row_id", "count"),
            distinct_players=("player_id_gsis", "nunique"),
            target_points_non_null=("next_nwr_points", lambda value: int(value.notna().sum())),
            target_ppg_non_null=("next_nwr_ppg", lambda value: int(value.notna().sum())),
            startable_hits=("startable_hit", lambda value: int(value.sum())),
        )
        .reset_index()
        .sort_values(["feature_season", "position"])
    )
    return grouped


def make_season_position_coverage(rows: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        rows.groupby(["target_season", "position"], dropna=False)
        .agg(
            row_count=("substrate_row_id", "count"),
            distinct_players=("player_id_gsis", "nunique"),
            target_games_non_null=("target_games", lambda value: int(value.notna().sum())),
            next_nwr_points_non_null=("next_nwr_points", lambda value: int(value.notna().sum())),
            next_position_finish_non_null=("next_position_finish", lambda value: int(value.notna().sum())),
            startable_hits=("startable_hit", lambda value: int(value.sum())),
        )
        .reset_index()
        .sort_values(["target_season", "position"])
    )
    grouped["coverage_note"] = "Validated target-season outcomes for canonical feature-target rows."
    return grouped


def make_identity_report(
    rows: pd.DataFrame, features: pd.DataFrame, labels: pd.DataFrame, join_audit: pd.DataFrame
) -> pd.DataFrame:
    matched = int((join_audit["_merge"] == "both").sum())
    feature_only = int((join_audit["_merge"] == "left_only").sum())
    label_only = int((join_audit["_merge"] == "right_only").sum())
    gsis_format_count = int(rows["player_id_gsis"].astype(str).str.match(r"^00-\d+$").sum())
    position_mismatch = int((rows["position"] != rows["target_position"]).sum())
    duplicate_keys = int(
        rows.duplicated(["player_id_gsis", "feature_season", "target_season"], keep=False).sum()
    )
    name_reuse = (
        features.groupby(["feature_season", "player_name"])["player_id"]
        .nunique()
        .reset_index(name="distinct_ids")
    )
    ambiguous_name_rows = int((name_reuse["distinct_ids"] > 1).sum())
    records = [
        ("feature_rows", len(features), "Rows in local feature_dataset_v1_clean_expanded.csv."),
        ("label_rows", len(labels), "Rows in local labels_v1.csv."),
        ("matched_feature_label_rows", matched, "Inner canonical rows matched on player_id and target_season."),
        ("unmatched_feature_rows", feature_only, "Feature rows without matching label rows."),
        ("unmatched_label_rows", label_only, "Label rows without matching feature rows."),
        ("canonical_rows", len(rows), "Rows emitted to the canonical review-only substrate."),
        ("distinct_gsis_player_ids", rows["player_id_gsis"].nunique(), "Stable player_id_gsis values used as identity."),
        ("gsis_format_rows", gsis_format_count, "Rows whose player_id_gsis matches the 00-numeric GSIS format."),
        ("position_mismatch_rows", position_mismatch, "Feature position differs from target position."),
        ("duplicate_identity_season_keys", duplicate_keys, "Duplicate player_id_gsis + season-pair keys."),
        ("ambiguous_same_name_feature_season_groups", ambiguous_name_rows, "Names are audit fields only; no name matching used."),
    ]
    return pd.DataFrame(records, columns=["metric", "value", "notes"])


def source_row(
    source_id: str,
    path: Path | str,
    path_type: str,
    row_count: int | str | None,
    column_count: int | str | None,
    season_coverage: str,
    positions: str,
    review_use: bool,
    canonical_input: str,
    status: str,
    notes: str,
) -> dict[str, Any]:
    actual_path = Path(path) if isinstance(path, str) and ":" in path else path
    sha = sha256_file(actual_path) if isinstance(actual_path, Path) else ""
    return {
        "source_id": source_id,
        "path": str(path),
        "path_type": path_type,
        "row_count": row_count,
        "column_count": column_count,
        "season_coverage": season_coverage,
        "positions": positions,
        "review_use": review_use,
        "canonical_input": canonical_input,
        "status": status,
        "sha256": sha,
        "notes": notes,
    }


def make_source_inventory(features: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    compact_labels = Path(
        r"docs\hq\outcomes\outcome_row_level_label_source_admission_v1_20260630\compact_outcome_row_level_label_source.csv"
    )
    core_usage = Path(
        r"docs\hq\data_sources\nflverse_core_usage_review_dataset_v1_20260701\nwr_nflverse_usage_review_dataset_v1.parquet"
    )
    redzone_sidecar = Path(
        r"docs\hq\data_sources\nflverse_core_usage_review_dataset_v1_20260701\nwr_player_week_redzone_sidecar_v1.parquet"
    )
    outcome_season = OUTCOME_2000_PROBE / "outcome_v2_extended_season_outcome_labels.csv"
    outcome_anchor = OUTCOME_2000_PROBE / "outcome_v2_extended_anchor_horizon_labels.csv"
    rows = [
        source_row(
            "local_backtest_v1_clean_expanded_features",
            FEATURE_SOURCE,
            "local_generated_not_tracked",
            len(features),
            len(features.columns),
            "feature_season:2018-2024; target_season:2019-2025",
            "|".join(sorted(features["position"].dropna().unique())),
            True,
            "used_filtered",
            "canonical_input_after_column_filter",
            "Used only after excluding current-only, depth, red-zone, formula, vendor, and blocked fields.",
        ),
        source_row(
            "local_backtest_v1_labels",
            LABEL_SOURCE,
            "local_generated_not_tracked",
            len(labels),
            len(labels.columns),
            "target_season:2019-2025",
            "|".join(sorted(labels["target_position"].dropna().unique())),
            True,
            "used",
            "canonical_target_input",
            "Used for next-season NWR scoring, PPG, Top-N buckets, and deterministic position finish derivation.",
        ),
        source_row(
            "local_backtest_v1_manifest",
            MANIFEST_SOURCE,
            "local_generated_not_tracked",
            1 if MANIFEST_SOURCE.exists() else 0,
            "n/a",
            "2018-2025 source seasons",
            "QB|RB|TE|WR",
            True,
            "lineage_only",
            "review_only_lineage",
            "Documents backtest-only status, blocked feature families, and legacy imputation rules.",
        ),
        source_row(
            "local_backtest_v1_missingness_summary",
            MISSINGNESS_SOURCE,
            "local_generated_not_tracked",
            csv_row_count(MISSINGNESS_SOURCE),
            "6",
            "2018-2024 feature seasons",
            "QB|RB|TE|WR",
            True,
            "metadata_report",
            "review_only_missingness_metadata",
            "Tracked as report lineage only; missingness indicators are not canonical modeling features in this lane.",
        ),
        source_row(
            "local_backtest_v1_feature_whitelist",
            WHITELIST_SOURCE,
            "local_generated_not_tracked",
            csv_row_count(WHITELIST_SOURCE),
            "4",
            "2018-2024 feature seasons",
            "QB|RB|TE|WR",
            True,
            "lineage_only",
            "review_only_feature_admission_context",
            "Used to understand legacy feature admission; this lane applies a stricter canonical filter.",
        ),
        source_row(
            "local_backtest_v1_excluded_features",
            EXCLUDED_SOURCE,
            "local_generated_not_tracked",
            csv_row_count(EXCLUDED_SOURCE),
            "4",
            "2018-2024 feature seasons",
            "QB|RB|TE|WR",
            True,
            "guardrail_context",
            "review_only_exclusion_context",
            "Confirms prior exclusions for inappropriate role fields, return fields, and red-zone side fields.",
        ),
        source_row(
            "nflverse_core_usage_review_dataset_v1",
            core_usage,
            "tracked_review_only",
            "76804",
            "40",
            "season:2024-2025",
            "all nflverse positions",
            True,
            "not_used",
            "coverage_too_recent_for_n_to_n_plus_1_substrate",
            "Player-week usage data is valuable for future expansion but only covers 2024-2025 in admitted form.",
        ),
        source_row(
            "nflverse_redzone_sidecar_v1",
            redzone_sidecar,
            "tracked_review_only",
            "6424",
            "18",
            "season:2024-2025",
            "n/a",
            True,
            "deferred",
            "no_overlap_for_safe_historical_target_substrate",
            "Typed red-zone sidecar is review-only and too recent for the canonical N to N+1 substrate here.",
        ),
        source_row(
            "compact_outcome_row_level_label_source",
            compact_labels,
            "tracked_review_only",
            "119040",
            "25",
            "season:2012-2024; anchor_season:2012-2024",
            "QB|RB|TE|WR",
            True,
            "target_only_deferred",
            "feature_side_missing_for_older_expansion",
            "Outcome V2 compact labels broaden target history but do not by themselves create safe feature rows.",
        ),
        source_row(
            "outcome_v2_historical_2000_probe_season_labels",
            outcome_season,
            "local_generated_not_tracked",
            csv_row_count(outcome_season),
            "unknown",
            "reported 2000-2024",
            "QB|RB|TE|WR",
            True,
            "target_only_deferred",
            "review_only_partial_target_expansion",
            "Useful future target substrate, but older safe feature-side regeneration remains blocked in this lane.",
        ),
        source_row(
            "outcome_v2_historical_2000_probe_anchor_labels",
            outcome_anchor,
            "local_generated_not_tracked",
            csv_row_count(outcome_anchor),
            "unknown",
            "reported 2000-2024",
            "QB|RB|TE|WR",
            True,
            "target_only_deferred",
            "review_only_partial_target_expansion",
            "Same target-only limitation as the season label probe.",
        ),
        source_row(
            "historical_tuning_substrate_expansion_probe_2012_2025",
            OLDER_PROBE_DIR,
            "local_generated_not_tracked",
            0,
            0,
            "attempted seasons:2012-2025",
            "QB|RB|TE|WR",
            True,
            "not_used",
            "blocked_missing_approved_nflverse_runtime",
            "Existing safe builder failed because nflreadpy was unavailable in the approved local-only runtime.",
        ),
        source_row(
            "overnight_model_tune_v1_expanded_20260622",
            OVERNIGHT_TUNE_DIR,
            "local_generated_not_tracked",
            "n/a",
            "n/a",
            "unknown",
            "QB|RB|TE|WR",
            True,
            "not_used",
            "formula_tuning_and_vendor_contamination_risk",
            "Not admitted for this data-substrate lane because it is a formula-tuning artifact area.",
        ),
    ]
    return pd.DataFrame(rows)


def make_schema(rows: pd.DataFrame) -> pd.DataFrame:
    safe_sources = {feature["canonical"]: feature["source"] for feature in SAFE_FEATURES}
    safe_sources.update({feature["canonical"]: "derived_from_prior_components" for feature in DERIVED_FEATURES})
    descriptions = {feature["canonical"]: feature["description"] for feature in SAFE_FEATURES}
    descriptions.update({feature["canonical"]: feature["description"] for feature in DERIVED_FEATURES})
    records = []
    for col in rows.columns:
        if col in {"substrate_row_id", "player_id_gsis"}:
            role = "identity"
            source = "builder"
        elif col in {"feature_season", "target_season", "feature_target_year_lag", "position", "target_position"}:
            role = "coverage_metadata"
            source = "feature and label keys"
        elif col in {"feature_player_name", "feature_team", "target_player_name", "target_team"}:
            role = "audit_field_not_identity_truth"
            source = "feature or label audit field"
        elif col in safe_sources:
            role = "safe_lagged_feature"
            source = safe_sources[col]
        elif col in TARGET_COLUMNS:
            role = "target_outcome"
            source = "labels_v1.csv or deterministic target derivation"
        elif col.endswith("_allowed") or col in {"review_only", "production_approved"}:
            role = "approval_metadata"
            source = "builder constant"
        else:
            role = "lineage_or_guardrail_metadata"
            source = "builder constant"
        records.append(
            {
                "column_name": col,
                "dtype": str(rows[col].dtype),
                "nullable": bool(rows[col].isna().any()),
                "role": role,
                "source_column_or_rule": source,
                "description": descriptions.get(col, ""),
                "review_only": True,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "production_approved": False,
                "missingness_semantics": (
                    "No new zero fill in builder; source missingness semantics documented separately."
                    if role == "safe_lagged_feature"
                    else "Not a feature value or derived target outcome."
                ),
            }
        )
    return pd.DataFrame(records)


def write_markdown(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def coverage_sentence(rows: pd.DataFrame) -> str:
    return (
        f"{len(rows):,} rows; feature seasons {rows['feature_season'].min()}-"
        f"{rows['feature_season'].max()}; target seasons {rows['target_season'].min()}-"
        f"{rows['target_season'].max()}; positions {', '.join(sorted(rows['position'].unique()))}."
    )


def write_reports(
    rows: pd.DataFrame,
    feature_coverage: pd.DataFrame,
    target_coverage: pd.DataFrame,
    identity_report: pd.DataFrame,
    source_inventory: pd.DataFrame,
) -> None:
    position_counts = rows["position"].value_counts().sort_index().to_dict()
    startable_counts = rows["startable_bucket"].value_counts().sort_index().to_dict()
    parquet_sha = sha256_file(PARQUET_PATH)
    feature_cols = [feature["canonical"] for feature in SAFE_FEATURES] + [
        feature["canonical"] for feature in DERIVED_FEATURES
    ]

    write_markdown(
        EXPERIMENT_DIR / "historical_tuning_substrate_summary.md",
        f"""
# NWR Historical Tuning Substrate Expansion V1

Verdict: `{VERDICT}`

This lane generated and validated a canonical, review-only season N to season N+1 feature-target substrate. It did not run formula tuning, did not update production formulas, and did not promote any source as production truth.

## Result

- Branch: `{BRANCH}`
- Base HEAD: `{BASE_HEAD}`
- Full substrate artifact: `{PARQUET_NAME}`
- Full substrate SHA-256: `{parquet_sha}`
- Coverage: {coverage_sentence(rows)}
- Position rows: {position_counts}
- Startable target buckets: {startable_counts}

## Interpretation

The available 2018-2024 feature seasons and 2019-2025 target seasons are preserved and validated. Older expansion was attempted through the existing safe Backtest V1 builder, but the approved local nflverse runtime was unavailable, so no older feature rows were admitted.

This is a stronger substrate review packet, not evidence that formula tuning is ready. Future formula work remains YELLOW until older safe feature coverage is expanded and the missingness semantics are reviewed by a human.
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "missingness_semantics_report.md",
        f"""
# Missingness Semantics Report

## Verdict

YELLOW: the canonical builder did not convert missing values to zero, but the local Backtest V1 source carries legacy zero-fill semantics for stat absence, unavailable optional sources, and denominator-safe rates.

## Builder Behavior

- No `fillna(0)` or equivalent missing-to-zero conversion is applied by this substrate builder.
- Canonical safe lagged features are selected from the local Backtest V1 source after excluding current-only/depth/status/red-zone fields.
- Derived `prior_touches` and `prior_opportunities` are arithmetic combinations of source V1 component columns.
- Missingness metadata is reported in `feature_coverage_report_v1.csv` and source lineage is retained through `{MISSINGNESS_SOURCE}`.

## Source Caveat

The Backtest V1 manifest states:

- role/stat absence can be zero-filled when no usage or unavailable optional source exists
- metadata absence can be zero-filled with explicit missing indicators
- rate denominators can be zero when the denominator is zero or missing

Those source semantics are preserved as review-only context. They are not approved for production modeling or tuning.
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "asof_and_leakage_guardrail_report.md",
        f"""
# As-Of And Leakage Guardrail Report

## Checks

- Feature season N to target season N+1 lag: PASS for all {len(rows):,} rows.
- Target outcomes separated from features: PASS.
- Current-only roster/status/injury/depth/schedule context excluded from canonical columns: PASS.
- Market/vendor/projection/ADP fields excluded: PASS.
- Routes, route proxies, TPRR, YPRR, and ambiguous `rz_att` absent: PASS.
- Red-zone side fields excluded from canonical substrate pending stronger historical admission: PASS.
- Missing values not forced to zero by this builder: PASS, with source-level YELLOW caveat documented in `missingness_semantics_report.md`.

## As-Of Rule

Each row uses completed season N facts as the feature side and completed season N+1 outcomes as the target side. No target-season availability, depth, schedule, ADP, rankings, projections, vendor context, hidden sort, or recommendation output is admitted as a feature.
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "expanded_historical_data_decision.md",
        f"""
# Expanded Historical Data Decision

## Decision

Preserve and validate the existing 2018-2024 feature seasons with 2019-2025 target seasons. Do not admit older feature rows in V1.

## Why Older Expansion Did Not Land

The existing safe Backtest V1 builder was attempted for 2012-2025 season inputs. It failed before producing rows because `nflreadpy` was unavailable in the approved local-only nflverse runtime. Since this lane cannot silently switch to an unapproved runtime or source path, older feature-side expansion is deferred.

## Target-Only Expansion

Outcome V2 historical target labels exist as review-only target-side evidence, including the local 2000 probe and tracked compact labels. They are not sufficient alone because this substrate requires aligned safe season N features and season N+1 targets.
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "blocked_or_deferred_sources_report.md",
        f"""
# Blocked Or Deferred Sources Report

## Deferred

- Older Backtest V1 regeneration: blocked because the approved local nflverse runtime did not expose `nflreadpy`.
- Outcome V2 2000 probe labels: target-only; feature-side expansion still required.
- Compact Outcome V2 labels through 2024: target-only for this lane.
- Core Usage Dataset V1: 2024-2025 player-week coverage is too recent to widen the season N to N+1 substrate by itself.
- Red-zone sidecar V1: typed and review-only, but only 2024-2025; not enough historical overlap for this substrate.
- Overnight formula-tuning directories: not used because this is not a tuning lane and those areas risk formula/vendor contamination.

## Blocked Feature Families

Routes, route proxies, TPRR, YPRR, ambiguous `rz_att`, market/vendor/projection/ADP fields, target-season rankings, current-only roster/status/injury/depth/schedule context, recommendations, and hidden sort outputs remain blocked.
""",
    )

    viable = "NO for production tuning; YES for substrate review and future expansion planning"
    write_markdown(
        EXPERIMENT_DIR / "future_tuning_readiness_report.md",
        f"""
# Future Tuning Readiness Report

## Readiness

Future formula tuning viability: {viable}.

The canonical substrate is useful for audit, coverage measurement, and pipeline validation. It is not enough to restart formula search as a production-relevant lane because the bottleneck remains historical feature coverage and legacy missingness semantics.

## Recommended Next Phase

Run a historical substrate expansion phase that installs or exposes the approved nflverse runtime, regenerates safe season-level feature rows back to at least 2012 where source coverage allows, and joins them to Outcome V2 labels without introducing current-only or vendor fields.
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "guardrail_report.md",
        f"""
# Guardrail Report

## Verdict

GREEN for review-only artifact generation. YELLOW for future tuning readiness.

## Confirmed

- No production formula changes.
- No production model training or tuning.
- No app wiring.
- No rankings changes.
- No recommendations.
- No hidden sort.
- No source-truth promotion.
- No runtime behavior changes.
- No live rank/model/service behavior edits.
- No market, ADP, vendor, or projection fields used as source truth.
- No routes, route proxies, TPRR, YPRR, or ambiguous `rz_att`.
- No current-only roster/status/injury/depth/schedule context as historical features.
- No raw/shared/cache/local export/secrets files tracked.
- Full substrate is review-only and not production-approved.
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "merge_safety_report.md",
        f"""
# Merge Safety Report

## Expected Changed Paths

All intended changes are limited to:

- `docs/hq/experiments/historical_tuning_substrate_expansion_v1_20260701/`
- `tests/test_historical_tuning_substrate_expansion_v1_20260701.py`

## Protected Paths

No production app/model/rank/source-truth/runtime path is intentionally changed by this lane.

## Artifact Policy

The full parquet is small and review-only, so it is tracked in the experiment artifact directory. Local source CSVs under `C:\\NWR_SHARED_DATA` remain untracked.
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "next_phase_handoff.md",
        f"""
# Next Phase Handoff

## Handoff Recommendation

Do not run another formula search next. Run Historical Tuning Substrate Expansion V2.

## V2 Goals

- Restore or install the approved local-only nflverse runtime required by the existing safe builder.
- Regenerate older safe season-level feature rows where source coverage permits.
- Join older features to Outcome V2 target labels without name-matching ambiguous players.
- Keep GSIS/nflverse IDs canonical and Sleeper IDs crosswalk-only.
- Preserve missingness semantics instead of forcing missing values to zero.
- Re-run leakage, forbidden-field, and source-governance checks before any tuning discussion.

## V1 Output To Reuse

- Canonical schema: `feature_target_substrate_schema_v1.csv`
- Full review-only substrate: `{PARQUET_NAME}`
- Coverage reports: row counts, season/position, feature, target, and identity join reports
""",
    )

    write_markdown(
        EXPERIMENT_DIR / "artifact_manifest.md",
        f"""
# Artifact Manifest

## Run Metadata

- Generated at UTC: `{datetime.now(timezone.utc).isoformat()}`
- Verdict: `{VERDICT}`
- Branch: `{BRANCH}`
- Base HEAD: `{BASE_HEAD}`
- Purpose: review-only historical tuning data substrate expansion
- Formula tuning run: `false`
- Production approved: `false`

## Substrate

- File: `{PARQUET_NAME}`
- Rows: `{len(rows):,}`
- Columns: `{len(rows.columns)}`
- SHA-256: `{parquet_sha}`
- Feature seasons: `{rows['feature_season'].min()}-{rows['feature_season'].max()}`
- Target seasons: `{rows['target_season'].min()}-{rows['target_season'].max()}`
- Canonical feature columns: `{', '.join(feature_cols)}`

## Files

| file | kind | rows | sha256 |
| --- | --- | ---: | --- |
{manifest_file_rows()}
""",
    )


def manifest_file_rows() -> str:
    files = sorted(path for path in EXPERIMENT_DIR.iterdir() if path.is_file() and path.name != "artifact_manifest.md")
    rows = []
    for path in files:
        if path.suffix == ".csv":
            count: int | str | None = csv_row_count(path)
            kind = "csv"
        elif path.suffix == ".parquet":
            count = "see summary"
            kind = "parquet"
        elif path.suffix == ".py":
            count = "n/a"
            kind = "builder"
        else:
            count = "n/a"
            kind = "markdown"
        rows.append(f"| `{path.name}` | {kind} | {count} | `{sha256_file(path)}` |")
    return "\n".join(rows)


def main() -> None:
    require_sources()
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    features = pd.read_csv(FEATURE_SOURCE)
    labels = pd.read_csv(LABEL_SOURCE)
    _manifest = read_manifest()

    rows, join_audit = build_substrate(features, labels)
    rows = rows.sort_values(["feature_season", "position", "next_nwr_points", "player_id_gsis"], ascending=[True, True, False, True])
    rows.to_parquet(PARQUET_PATH, index=False)

    source_inventory = make_source_inventory(features, labels)
    schema = make_schema(rows)
    feature_coverage = make_feature_coverage(rows)
    target_coverage = make_target_coverage(rows)
    identity_report = make_identity_report(rows, features, labels, join_audit)
    row_count_report = make_row_count_report(rows)
    season_position_coverage = make_season_position_coverage(rows)

    write_csv(source_inventory, "available_historical_sources_inventory.csv")
    write_csv(schema, "feature_target_substrate_schema_v1.csv")
    write_csv(rows.head(40), "feature_target_substrate_sample_v1.csv")
    write_csv(row_count_report, "feature_target_row_count_report_v1.csv")
    write_csv(season_position_coverage, "season_position_coverage_report_v1.csv")
    write_csv(feature_coverage, "feature_coverage_report_v1.csv")
    write_csv(target_coverage, "target_outcome_coverage_report_v1.csv")
    write_csv(identity_report, "identity_join_report_v1.csv")

    write_reports(rows, feature_coverage, target_coverage, identity_report, source_inventory)
    print(
        json.dumps(
            {
                "verdict": VERDICT,
                "rows": len(rows),
                "columns": len(rows.columns),
                "feature_seasons": [int(rows["feature_season"].min()), int(rows["feature_season"].max())],
                "target_seasons": [int(rows["target_season"].min()), int(rows["target_season"].max())],
                "parquet": str(PARQUET_PATH),
                "sha256": sha256_file(PARQUET_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
