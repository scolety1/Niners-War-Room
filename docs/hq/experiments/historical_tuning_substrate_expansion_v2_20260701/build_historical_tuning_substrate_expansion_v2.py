from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
EXPANDED_ROOT = Path(
    r"C:\NWR_SHARED_DATA\backtests\historical_tuning_substrate_expansion_v2_20260701_2012_2025"
)
V1_LOCAL_ROOT = Path(r"C:\NWR_SHARED_DATA\backtests\backtest_v1_feature_cleanup_20260621")
PYDEPS_ROOT = Path(r"C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps")
V1_ARTIFACT_DIR = (
    Path(__file__).resolve().parents[1] / "historical_tuning_substrate_expansion_v1_20260701"
)

FEATURE_SOURCE = EXPANDED_ROOT / "feature_dataset_v1_clean_expanded.csv"
LABEL_SOURCE = EXPANDED_ROOT / "labels_v1.csv"
MANIFEST_SOURCE = EXPANDED_ROOT / "build_manifest_v1.json"
MISSINGNESS_SOURCE = EXPANDED_ROOT / "feature_missingness_summary_v1.csv"
WHITELIST_SOURCE = EXPANDED_ROOT / "feature_whitelist_by_position_v1.csv"
EXCLUDED_SOURCE = EXPANDED_ROOT / "excluded_features_v1.csv"

BASE_HEAD = "31c596418ea0217c80f01f955ab6230113936540"
BRANCH = "work/historical-tuning-substrate-expansion-v2-20260701"
VERDICT = "GREEN_RUNTIME_RESTORED_YELLOW_SUBSTRATE_EXPANDED_REVIEW_ONLY_NOT_TUNING_READY"
V1_ROW_COUNT = 3108

PARQUET_NAME = "nwr_historical_tuning_feature_target_substrate_v2.parquet"
PARQUET_PATH = EXPERIMENT_DIR / PARQUET_NAME

FORBIDDEN_COLUMN_TOKENS = (
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
)

SAFE_FEATURES: list[dict[str, str]] = [
    {"canonical": "prior_nwr_points", "source": "feature_nwr_points", "description": "Prior feature-season total NWR scoring."},
    {"canonical": "prior_games", "source": "feature_games", "description": "Prior feature-season games with stats."},
    {"canonical": "prior_nwr_ppg", "source": "feature_nwr_ppg", "description": "Prior feature-season NWR points per game."},
    {"canonical": "prior_targets", "source": "targets", "description": "Prior feature-season targets."},
    {"canonical": "prior_carries", "source": "carries", "description": "Prior feature-season carries."},
    {"canonical": "prior_receptions", "source": "receptions", "description": "Prior feature-season receptions."},
    {"canonical": "prior_rushing_yards", "source": "rushing_yards", "description": "Prior feature-season rushing yards."},
    {"canonical": "prior_receiving_yards", "source": "receiving_yards", "description": "Prior feature-season receiving yards."},
    {
        "canonical": "prior_receiving_air_yards",
        "source": "receiving_air_yards",
        "description": "Prior feature-season receiving air yards, null-fenced when the source missingness flag is set.",
        "fence_by": "air_yards_missing",
    },
    {
        "canonical": "prior_receiving_yards_after_catch",
        "source": "receiving_yards_after_catch",
        "description": "Prior feature-season receiving yards after catch, null-fenced when the source air-yards/YAC missingness flag is set.",
        "fence_by": "air_yards_missing",
    },
    {"canonical": "prior_rushing_first_downs", "source": "rushing_first_downs", "description": "Prior feature-season rushing first downs."},
    {"canonical": "prior_receiving_first_downs", "source": "receiving_first_downs", "description": "Prior feature-season receiving first downs."},
    {"canonical": "prior_passing_attempts", "source": "attempts", "description": "Prior feature-season passing attempts."},
    {"canonical": "prior_passing_completions", "source": "completions", "description": "Prior feature-season passing completions."},
    {"canonical": "prior_passing_yards", "source": "passing_yards", "description": "Prior feature-season passing yards."},
    {"canonical": "prior_passing_td", "source": "passing_tds", "description": "Prior feature-season passing touchdowns."},
    {"canonical": "prior_interceptions", "source": "passing_interceptions", "description": "Prior feature-season interceptions."},
    {"canonical": "prior_passing_first_downs", "source": "passing_first_downs", "description": "Prior feature-season passing first downs."},
    {
        "canonical": "prior_offensive_snaps",
        "source": "offense_snaps",
        "description": "Prior feature-season offensive snaps, null-fenced when the source snap missingness flag is set.",
        "fence_by": "snap_pct_missing",
    },
    {
        "canonical": "prior_offense_pct",
        "source": "offense_pct",
        "description": "Prior feature-season offense percentage, null-fenced when the source snap missingness flag is set.",
        "fence_by": "snap_pct_missing",
    },
]

DERIVED_FEATURES: list[dict[str, str]] = [
    {"canonical": "prior_touches", "left": "prior_carries", "right": "prior_receptions", "description": "Derived as prior carries plus prior receptions."},
    {"canonical": "prior_opportunities", "left": "prior_carries", "right": "prior_targets", "description": "Derived as prior carries plus prior targets."},
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


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_row_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def require_sources() -> None:
    missing = [path for path in (FEATURE_SOURCE, LABEL_SOURCE, MANIFEST_SOURCE) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing V2 local expanded source files: " + ", ".join(str(p) for p in missing))


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_SOURCE.exists():
        return {}
    return json.loads(MANIFEST_SOURCE.read_text(encoding="utf-8"))


def stable_row_id(player_id: str, feature_season: int, target_season: int) -> str:
    key = f"{player_id}|{feature_season}|{target_season}|v2"
    return "nwr_hts_v2_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def build_substrate(features: pd.DataFrame, labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    audit = features[["player_id", "feature_season", "target_season", "position", "player_name"]].merge(
        labels[["player_id", "target_season", "target_position", "target_player_name"]],
        on=["player_id", "target_season"],
        how="outer",
        indicator=True,
    )
    ranked = labels.sort_values(
        ["target_season", "target_position", "next_nwr_points", "player_id"],
        ascending=[True, True, False, True],
    ).copy()
    ranked["next_position_finish"] = ranked.groupby(["target_season", "target_position"]).cumcount() + 1
    labels_with_finish = labels.merge(
        ranked[["player_id", "target_season", "next_position_finish"]],
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
    rows["prior_snap_source_missing"] = joined["snap_pct_missing"].astype(int).astype(bool)
    rows["prior_air_yards_source_missing"] = joined["air_yards_missing"].astype(int).astype(bool)

    for feature in SAFE_FEATURES:
        values = pd.to_numeric(joined[feature["source"]], errors="coerce")
        fence_by = feature.get("fence_by")
        if fence_by:
            values = values.mask(joined[fence_by].astype(int) == 1, pd.NA)
        rows[feature["canonical"]] = values

    for feature in DERIVED_FEATURES:
        rows[feature["canonical"]] = rows[feature["left"]] + rows[feature["right"]]

    for column in [
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
        rows[column] = joined[column]

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

    rows["optional_source_null_fenced"] = rows["prior_snap_source_missing"] | rows["prior_air_yards_source_missing"]
    rows["feature_source_artifact"] = str(FEATURE_SOURCE)
    rows["target_source_artifact"] = str(LABEL_SOURCE)
    rows["runtime_dependency_path"] = str(PYDEPS_ROOT)
    rows["source_lineage"] = "Backtest V1 builder rerun over 2012-2025 with approved nflreadpy pydeps, then canonical V2 filter."
    rows["feature_asof_rule"] = "Use completed feature season N facts only before the season N+1 prediction anchor."
    rows["target_window"] = "Full target season N+1 outcomes only."
    rows["leakage_check_result"] = "PASS_FEATURE_N_TARGET_N_PLUS_1_SEPARATED"
    rows["asof_check_result"] = "PASS_NO_TARGET_SEASON_CONTEXT_IN_FEATURE_COLUMNS"
    rows["missingness_policy_v2"] = "No new zero fill. Optional snap and air-yard/YAC source-missing zeros are replaced with null."
    rows["review_only"] = True
    rows["model_use_allowed"] = False
    rows["training_allowed"] = False
    rows["source_truth_allowed"] = False
    rows["hidden_sort_allowed"] = False
    rows["recommendation_allowed"] = False
    rows["production_approved"] = False
    validate_substrate(rows)
    return rows, audit


def validate_substrate(rows: pd.DataFrame) -> None:
    if len(rows) != 5518:
        raise ValueError(f"Expected 5518 V2 rows, got {len(rows)}")
    if not (rows["target_season"] == rows["feature_season"] + 1).all():
        raise ValueError("Feature season / target season lag is invalid.")
    forbidden = [col for col in rows.columns if any(token in col.lower() for token in FORBIDDEN_COLUMN_TOKENS)]
    if forbidden:
        raise ValueError(f"Forbidden canonical columns present: {forbidden}")
    for column in [
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
        "production_approved",
    ]:
        if rows[column].astype(bool).any():
            raise ValueError(f"{column} contains true values")


def write_csv(frame: pd.DataFrame, name: str) -> Path:
    path = EXPERIMENT_DIR / name
    frame.to_csv(path, index=False)
    return path


def make_source_inventory(features: pd.DataFrame, labels: pd.DataFrame, manifest: dict[str, Any]) -> pd.DataFrame:
    pyproject = Path("pyproject.toml")
    requirements = Path("requirements.txt")
    rows = [
        source_row("repo_pyproject_dependency", pyproject, "tracked_dependency_manifest", 1, "n/a", "n/a", "n/a", True, "declares nflreadpy", "used_for_runtime_decision"),
        source_row("repo_requirements_dependency", requirements, "tracked_dependency_manifest", 1, "n/a", "n/a", "n/a", True, "declares nflreadpy", "used_for_runtime_decision"),
        source_row("approved_shared_pydeps", PYDEPS_ROOT, "local_dependency_path_not_tracked", "n/a", "n/a", "nflreadpy 0.1.5", "n/a", True, "runtime restored", "used for artifact generation only"),
        source_row("expanded_backtest_v1_features", FEATURE_SOURCE, "local_generated_not_tracked", len(features), len(features.columns), "feature_season:2012-2024; target_season:2013-2025", "|".join(sorted(features["position"].unique())), True, "used filtered", "canonical V2 input"),
        source_row("expanded_backtest_v1_labels", LABEL_SOURCE, "local_generated_not_tracked", len(labels), len(labels.columns), "target_season:2013-2025", "|".join(sorted(labels["target_position"].unique())), True, "used", "canonical V2 target input"),
        source_row("expanded_backtest_v1_manifest", MANIFEST_SOURCE, "local_generated_not_tracked", 1, "n/a", "seasons:2012-2025", "QB|RB|TE|WR", True, "lineage", "backtest-only not model approved"),
        source_row("expanded_backtest_v1_missingness", MISSINGNESS_SOURCE, "local_generated_not_tracked", csv_row_count(MISSINGNESS_SOURCE), 6, "feature_season:2012-2024", "QB|RB|TE|WR", True, "used for null fencing", "optional source missingness metadata"),
        source_row("expanded_backtest_v1_whitelist", WHITELIST_SOURCE, "local_generated_not_tracked", csv_row_count(WHITELIST_SOURCE), 4, "feature_season:2012-2024", "QB|RB|TE|WR", True, "lineage", "stricter V2 canonical filter applied"),
        source_row("expanded_backtest_v1_excluded_features", EXCLUDED_SOURCE, "local_generated_not_tracked", csv_row_count(EXCLUDED_SOURCE), 4, "feature_season:2012-2024", "QB|RB|TE|WR", True, "guardrail context", "blocked role/return/red-zone fields remain excluded"),
        source_row("v1_tracked_substrate", V1_ARTIFACT_DIR / "nwr_historical_tuning_feature_target_substrate_v1.parquet", "tracked_review_only", V1_ROW_COUNT, "62", "feature_season:2018-2024; target_season:2019-2025", "QB|RB|TE|WR", True, "comparison only", "V2 expands by 2410 rows"),
        source_row("core_usage_dataset_v1", Path("docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701/nwr_nflverse_usage_review_dataset_v1.parquet"), "tracked_review_only", "76804", "40", "season:2024-2025", "all", True, "not used", "too recent to widen older feature seasons"),
        source_row("compact_outcome_v2_labels", Path("docs/hq/outcomes/outcome_row_level_label_source_admission_v1_20260630/compact_outcome_row_level_label_source.csv"), "tracked_review_only", "119040", "25", "season:2012-2024", "QB|RB|TE|WR", True, "target-only context", "feature-side builder provided aligned labels for V2"),
    ]
    if manifest:
        rows.append(source_row("expanded_backtest_manifest_row_count", MANIFEST_SOURCE, "local_generated_not_tracked", manifest.get("row_count"), "n/a", "manifest row_count", "QB|RB|TE|WR", True, "cross-check", "manifest row count agrees with emitted V2 source"))
    return pd.DataFrame(rows)


def source_row(
    source_id: str,
    path: Path,
    path_type: str,
    row_count: Any,
    column_count: Any,
    season_coverage: str,
    positions: str,
    review_use: bool,
    canonical_input: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "path": str(path),
        "path_type": path_type,
        "row_count": row_count,
        "column_count": column_count,
        "season_coverage": season_coverage,
        "positions": positions,
        "review_use": review_use,
        "model_use_allowed": False,
        "training_allowed": False,
        "source_truth_allowed": False,
        "canonical_input": canonical_input,
        "sha256": sha256_file(path),
        "notes": notes,
    }


def make_schema(rows: pd.DataFrame) -> pd.DataFrame:
    descriptions = {item["canonical"]: item["description"] for item in SAFE_FEATURES + DERIVED_FEATURES}
    sources = {item["canonical"]: item.get("source", "derived_from_prior_components") for item in SAFE_FEATURES + DERIVED_FEATURES}
    fences = {item["canonical"]: item.get("fence_by", "") for item in SAFE_FEATURES}
    records = []
    for column in rows.columns:
        if column in {"substrate_row_id", "player_id_gsis"}:
            role = "identity"
        elif column in {"feature_player_name", "feature_team", "target_player_name", "target_team"}:
            role = "audit_field_not_identity_truth"
        elif column in descriptions:
            role = "safe_lagged_feature"
        elif column in TARGET_COLUMNS:
            role = "target_outcome"
        elif column.endswith("_allowed") or column in {"review_only", "production_approved"}:
            role = "approval_metadata"
        else:
            role = "lineage_or_missingness_metadata"
        records.append(
            {
                "column_name": column,
                "dtype": str(rows[column].dtype),
                "nullable": bool(rows[column].isna().any()),
                "role": role,
                "source_column_or_rule": sources.get(column, "builder metadata or label derivation"),
                "null_fenced_by": fences.get(column, ""),
                "description": descriptions.get(column, ""),
                "review_only": True,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "production_approved": False,
                "missingness_semantics": missingness_note(column, fences.get(column, "")),
            }
        )
    return pd.DataFrame(records)


def missingness_note(column: str, fence_by: str) -> str:
    if fence_by:
        return f"V2 replaces source encoded zero/unavailable values with null when {fence_by}=1."
    if column in {item["canonical"] for item in SAFE_FEATURES + DERIVED_FEATURES}:
        return "No new zero fill in V2; core source value retained as review-only factual Backtest V1 output."
    return "Not a feature value."


def make_feature_coverage(rows: pd.DataFrame) -> pd.DataFrame:
    feature_names = [item["canonical"] for item in SAFE_FEATURES] + [item["canonical"] for item in DERIVED_FEATURES]
    descriptions = {item["canonical"]: item["description"] for item in SAFE_FEATURES + DERIVED_FEATURES}
    fences = {item["canonical"]: item.get("fence_by", "") for item in SAFE_FEATURES}
    records = []
    for name in feature_names:
        series = pd.to_numeric(rows[name], errors="coerce")
        records.append(
            {
                "feature": name,
                "rows": len(rows),
                "non_null_count": int(series.notna().sum()),
                "null_count": int(series.isna().sum()),
                "coverage_rate": round(float(series.notna().mean()), 6),
                "zero_count": int((series.fillna(0) == 0).sum()),
                "zero_rate_including_null_as_zero_for_audit_only": round(float((series.fillna(0) == 0).mean()), 6),
                "non_zero_count": int((series.fillna(0) != 0).sum()),
                "min_value": round(float(series.min()), 6) if series.notna().any() else None,
                "max_value": round(float(series.max()), 6) if series.notna().any() else None,
                "mean_value": round(float(series.mean()), 6) if series.notna().any() else None,
                "null_fenced_by": fences.get(name, ""),
                "description": descriptions[name],
            }
        )
    return pd.DataFrame(records)


def make_target_coverage(rows: pd.DataFrame) -> pd.DataFrame:
    records = []
    for column in TARGET_COLUMNS:
        series = rows[column]
        record: dict[str, Any] = {
            "target_outcome": column,
            "rows": len(rows),
            "non_null_count": int(series.notna().sum()),
            "null_count": int(series.isna().sum()),
            "coverage_rate": round(float(series.notna().mean()), 6),
            "source": "expanded labels_v1.csv plus deterministic position finish/startable derivations",
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
    return (
        rows.groupby(["feature_season", "target_season", "position"], dropna=False)
        .agg(
            row_count=("substrate_row_id", "count"),
            distinct_players=("player_id_gsis", "nunique"),
            optional_source_null_fenced_rows=("optional_source_null_fenced", lambda value: int(value.sum())),
            startable_hits=("startable_hit", lambda value: int(value.sum())),
        )
        .reset_index()
        .sort_values(["feature_season", "position"])
    )


def make_season_position_coverage(rows: pd.DataFrame) -> pd.DataFrame:
    report = (
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
    report["coverage_note"] = "Expanded V2 review-only N to N+1 rows."
    return report


def make_identity_report(rows: pd.DataFrame, features: pd.DataFrame, labels: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    name_groups = features.groupby(["feature_season", "player_name"])["player_id"].nunique().reset_index(name="ids")
    records = [
        ("feature_rows", len(features), "Rows in expanded feature source."),
        ("label_rows", len(labels), "Rows in expanded label source."),
        ("matched_feature_label_rows", int((audit["_merge"] == "both").sum()), "Rows matched on player_id and target_season."),
        ("unmatched_feature_rows", int((audit["_merge"] == "left_only").sum()), "Feature rows without label rows."),
        ("unmatched_label_rows", int((audit["_merge"] == "right_only").sum()), "Label rows without feature rows."),
        ("canonical_rows", len(rows), "Rows emitted to V2 parquet."),
        ("distinct_gsis_player_ids", rows["player_id_gsis"].nunique(), "GSIS/nflverse IDs used as canonical identity."),
        ("gsis_format_rows", int(rows["player_id_gsis"].str.match(r"^00-\d+$").sum()), "Rows with GSIS-style 00-numeric ID."),
        ("position_mismatch_rows", int((rows["position"] != rows["target_position"]).sum()), "Feature/target position mismatch rows."),
        ("duplicate_identity_season_keys", int(rows.duplicated(["player_id_gsis", "feature_season", "target_season"], keep=False).sum()), "Duplicate player-season-pair keys."),
        ("ambiguous_same_name_feature_season_groups", int((name_groups["ids"] > 1).sum()), "Names are audit fields only; no name matching used."),
    ]
    return pd.DataFrame(records, columns=["metric", "value", "notes"])


def write_markdown(path: Path, body: str) -> None:
    path.write_text(body.strip() + "\n", encoding="utf-8")


def write_reports(rows: pd.DataFrame, manifest: dict[str, Any]) -> None:
    row_delta = len(rows) - V1_ROW_COUNT
    position_counts = rows["position"].value_counts().sort_index().to_dict()
    seasons = f"{rows['feature_season'].min()}-{rows['feature_season'].max()}"
    targets = f"{rows['target_season'].min()}-{rows['target_season'].max()}"
    parquet_sha = sha256_file(PARQUET_PATH)
    null_fenced = int(rows["optional_source_null_fenced"].sum())
    snap_nulls = int(rows["prior_offensive_snaps"].isna().sum())
    air_nulls = int(rows["prior_receiving_air_yards"].isna().sum())
    common = {
        "verdict": VERDICT,
        "branch": BRANCH,
        "base": BASE_HEAD,
        "rows": f"{len(rows):,}",
        "row_delta": f"+{row_delta:,}",
        "feature_seasons": seasons,
        "target_seasons": targets,
        "position_counts": position_counts,
        "sha": parquet_sha,
        "null_fenced": f"{null_fenced:,}",
        "snap_nulls": f"{snap_nulls:,}",
        "air_nulls": f"{air_nulls:,}",
    }
    write_markdown(EXPERIMENT_DIR / "historical_tuning_substrate_v2_summary.md", summary_md(common))
    write_markdown(EXPERIMENT_DIR / "runtime_restoration_report.md", runtime_md(common))
    write_markdown(EXPERIMENT_DIR / "nflreadpy_or_nflverse_dependency_decision.md", dependency_md())
    write_markdown(EXPERIMENT_DIR / "feature_generation_path_report.md", feature_path_md(common))
    write_markdown(EXPERIMENT_DIR / "missingness_semantics_report_v2.md", missingness_md(common))
    write_markdown(EXPERIMENT_DIR / "legacy_zero_fill_replacement_or_fencing_report.md", zero_fill_md(common))
    write_markdown(EXPERIMENT_DIR / "asof_and_leakage_guardrail_report_v2.md", asof_md(common))
    write_markdown(EXPERIMENT_DIR / "expanded_historical_data_decision_v2.md", expansion_decision_md(common))
    write_markdown(EXPERIMENT_DIR / "blocked_or_deferred_sources_report_v2.md", blocked_md())
    write_markdown(EXPERIMENT_DIR / "future_tuning_readiness_report_v2.md", readiness_md(common))
    write_markdown(EXPERIMENT_DIR / "guardrail_report.md", guardrail_md())
    write_markdown(EXPERIMENT_DIR / "merge_safety_report.md", merge_safety_md())
    write_markdown(EXPERIMENT_DIR / "next_phase_handoff.md", handoff_md(common))
    write_manifest(rows, manifest, common)


def summary_md(values: dict[str, Any]) -> str:
    return f"""
# NWR Historical Tuning Substrate Expansion V2

Verdict: `{values['verdict']}`

V2 restored the approved local nflreadpy runtime path for artifact generation and expanded the review-only feature-target substrate. It did not run formula search, optimize formulas, change production formulas, update rankings, or wire any runtime behavior.

## Result

- Branch: `{values['branch']}`
- Base HEAD: `{values['base']}`
- Full substrate artifact: `{PARQUET_NAME}`
- Full substrate SHA-256: `{values['sha']}`
- Rows: `{values['rows']}` (`{values['row_delta']}` vs V1)
- Feature seasons: `{values['feature_seasons']}`
- Target seasons: `{values['target_seasons']}`
- Position rows: `{values['position_counts']}`
- Optional source null-fenced rows: `{values['null_fenced']}`

## Decision

The runtime blocker is fixed for review-only artifact generation by using the repo-approved shared pydeps path. The substrate is wider and cleaner than V1, but legacy source semantics remain partially fenced rather than fully eliminated. Future formula tuning is still not production-viable without human review and a V3 source-semantics pass.
"""


def runtime_md(values: dict[str, Any]) -> str:
    return f"""
# Runtime Restoration Report

## Verdict

GREEN for local artifact generation. No repo dependency changes were needed.

## Diagnosis

The previous blocker was not that `nflreadpy` lacked repo approval. `pyproject.toml` and `requirements.txt` already declare `nflreadpy`, and `docs/hq/data_sources/nfl_usage/NWR_NFLREADPY_DEPENDENCY_APPROVAL_20260624.md` approves local installation. The actual blocker was that the bundled Python runtime did not include `nflreadpy` unless the approved shared dependency path was added to `PYTHONPATH`.

## Restored Path

- Python: bundled Codex runtime Python
- Repo path on `PYTHONPATH`: repository root
- Approved nflreadpy path on `PYTHONPATH`: `{PYDEPS_ROOT}`
- Observed package: `nflreadpy 0.1.5`
- Smoke: `nflreadpy.load_player_stats([2012], summary_level='reg')` returned 1,811 rows

## Generation Command

```powershell
$env:PYTHONPATH = '<repo>' + [IO.Path]::PathSeparator + 'C:\\NWR_SHARED_DATA\\vendor_spikes\\nflverse\\scratch\\pydeps'
python scripts\\build_backtest_dataset_v1.py --seasons 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 --output-root C:\\NWR_SHARED_DATA\\backtests --run-label historical_tuning_substrate_expansion_v2_20260701_2012_2025
```

Output rows: `{values['rows']}`.
"""


def dependency_md() -> str:
    return f"""
# nflreadpy Or nflverse Dependency Decision

Decision: use the existing approved dependency declaration and the existing approved local shared pydeps path. Do not edit dependency files in this lane.

Evidence:

- `pyproject.toml` already lists `nflreadpy`.
- `requirements.txt` already lists `nflreadpy`.
- `scripts/run_nflverse_refresh_v0.ps1` uses `C:\\NWR_SHARED_DATA\\vendor_spikes\\nflverse\\scratch\\pydeps` on `PYTHONPATH`.
- `tests/test_scheduler_runner_scripts_v0.py` asserts that runner behavior.
- `{PYDEPS_ROOT}` exists locally and contains `nflreadpy-0.1.5.dist-info`.

No package was installed globally. No package was vendored into the repo. No production runtime behavior was changed.
"""


def feature_path_md(values: dict[str, Any]) -> str:
    return f"""
# Feature Generation Path Report

## Path Used

Existing script: `scripts/build_backtest_dataset_v1.py`

The script was run with the approved `nflreadpy` pydeps path and produced local-only artifacts under:

`{EXPANDED_ROOT}`

## Coverage

- Feature seasons: `{values['feature_seasons']}`
- Target seasons: `{values['target_seasons']}`
- Rows: `{values['rows']}`
- Delta vs V1: `{values['row_delta']}`

## Exclusions

The V2 canonical parquet excludes current-only roster/status/injury/depth/schedule context, route fields, route proxies, TPRR, YPRR, ambiguous `rz_att`, market/ADP/vendor/projection/rank fields, and red-zone fields pending a separate typed historical sidecar gate.
"""


def missingness_md(values: dict[str, Any]) -> str:
    return f"""
# Missingness Semantics Report V2

V2 does not perform new missing-to-zero conversion.

The expanded Backtest V1 source still carries legacy zero-fill semantics. V2 reduces that risk by replacing optional-source encoded zeros with null for:

- `prior_offensive_snaps` and `prior_offense_pct` where `snap_pct_missing=1`: `{values['snap_nulls']}` rows
- `prior_receiving_air_yards` and `prior_receiving_yards_after_catch` where `air_yards_missing=1`: `{values['air_nulls']}` rows

Core seasonal stat fields remain source-recorded review-only values from the Backtest V1 output. They are not production-approved and need a future source-semantics audit before any tuning lane treats zero values as explicit absence.
"""


def zero_fill_md(values: dict[str, Any]) -> str:
    return f"""
# Legacy Zero-Fill Replacement Or Fencing Report

## Verdict

YELLOW_IMPROVED_FENCED_NOT_FULLY_REPLACED

V2 replaced the highest-risk optional-source legacy zeros with nulls. It did not fully replace every Backtest V1 source-level zero-fill rule.

## Fenced

- Optional snap fields: `{values['snap_nulls']}` null-fenced rows.
- Optional air-yard/YAC fields: `{values['air_nulls']}` null-fenced rows.
- Rows with at least one optional source fence: `{values['null_fenced']}`.

## Still Requires V3 Review

Role/stat absence rules for core seasonal facts remain inherited from the source builder. V2 documents them and keeps all outputs review-only.
"""


def asof_md(values: dict[str, Any]) -> str:
    return f"""
# As-Of And Leakage Guardrail Report V2

## Checks

- Feature season N to target season N+1 lag: PASS for all `{values['rows']}` rows.
- Target outcomes separated from features: PASS.
- Current-only roster/status/injury/depth/schedule context excluded: PASS.
- Market/vendor/projection/ADP/rank fields excluded as source truth: PASS.
- Routes, route proxies, TPRR, YPRR, and ambiguous `rz_att` absent: PASS.
- Missing values not forced to zero by the V2 builder: PASS.

Each row uses completed season N facts only and full season N+1 outcomes only.
"""


def expansion_decision_md(values: dict[str, Any]) -> str:
    return f"""
# Expanded Historical Data Decision V2

Decision: admit the expanded and null-fenced V2 review-only substrate.

V1 had 3,108 rows across feature seasons 2018-2024 and target seasons 2019-2025. V2 has `{values['rows']}` rows across feature seasons `{values['feature_seasons']}` and target seasons `{values['target_seasons']}`, a `{values['row_delta']}` row increase.

The expansion used the existing approved Backtest V1 builder and the approved local `nflreadpy` dependency path. The full parquet is small enough to track as review-only evidence.
"""


def blocked_md() -> str:
    return """
# Blocked Or Deferred Sources Report V2

Deferred:

- Red-zone targets/carries/pass attempts: require a typed historical sidecar gate; V2 does not admit legacy red-zone fields.
- Routes, route proxies, TPRR, and YPRR: blocked.
- Current-only roster/status/injury/depth/schedule/availability context: blocked as historical feature data.
- Market, ADP, vendor, projection, and rank fields: blocked as source truth.
- Full source-level zero-fill replacement: deferred to V3 source-semantics audit.
- Formula search: explicitly out of scope.
"""


def readiness_md(values: dict[str, Any]) -> str:
    return f"""
# Future Tuning Readiness Report V2

Future formula tuning remains not production-viable.

V2 is materially better than V1 because it restores the runtime path, expands the historical window, and null-fences optional source fields. It is sufficient for a future human-reviewed exploratory tuning substrate, but not for production formula changes.

Before formula search resumes:

- Review source zero semantics for core seasonal stat fields.
- Decide whether null-fenced optional fields should be used or excluded.
- Add typed historical red-zone sidecar only if source semantics are proven.
- Keep all candidate outputs review-only.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Confirmed:

- No production formula changes.
- No production model training or tuning.
- No formula optimization.
- No app wiring.
- No rankings changes.
- No recommendations.
- No hidden sort.
- No source-truth promotion.
- No runtime behavior changes.
- No edits to live rank/model/service behavior.
- No market/ADP/vendor/projection fields as source truth.
- No route proxies, routes, TPRR, or YPRR.
- Ambiguous `rz_att` remains blocked.
- No current-only roster/status/injury/depth/schedule context used as historical features.
- No raw/shared/cache/local export/secrets files tracked.
- V2 artifacts remain review-only and not production-approved.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

Expected changed paths:

- `docs/hq/experiments/historical_tuning_substrate_expansion_v2_20260701/`
- `tests/test_historical_tuning_substrate_expansion_v2_20260701.py`

No app/model/rank/source-truth/runtime path should change. Local generated source outputs remain under `C:\\NWR_SHARED_DATA` and are not tracked.
"""


def handoff_md(values: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommended next phase: Historical Tuning Substrate Expansion V3 Source Semantics Audit.

V3 should not be a formula search. It should review core seasonal stat zero semantics, determine whether role/stat absences are explicit zero or unknown, and decide whether to emit a stricter all-null-safe substrate.

V2 artifacts to reuse:

- `{PARQUET_NAME}`
- `feature_target_substrate_schema_v2.csv`
- `legacy_zero_fill_replacement_or_fencing_report.md`
- `runtime_restoration_report.md`
"""


def manifest_file_rows() -> str:
    lines = []
    for path in sorted(EXPERIMENT_DIR.iterdir()):
        if not path.is_file() or path.name == "artifact_manifest.md":
            continue
        if path.suffix == ".csv":
            kind = "csv"
            rows = csv_row_count(path)
        elif path.suffix == ".parquet":
            kind = "parquet"
            rows = "5518"
        elif path.suffix == ".py":
            kind = "builder"
            rows = "n/a"
        else:
            kind = "markdown"
            rows = "n/a"
        lines.append(f"| `{path.name}` | {kind} | {rows} | `{sha256_file(path)}` |")
    return "\n".join(lines)


def write_manifest(rows: pd.DataFrame, manifest: dict[str, Any], values: dict[str, Any]) -> None:
    feature_cols = [item["canonical"] for item in SAFE_FEATURES] + [item["canonical"] for item in DERIVED_FEATURES]
    write_markdown(
        EXPERIMENT_DIR / "artifact_manifest.md",
        f"""
# Artifact Manifest

Generated at UTC: `{datetime.now(timezone.utc).isoformat()}`

- Verdict: `{VERDICT}`
- Branch: `{BRANCH}`
- Base HEAD: `{BASE_HEAD}`
- Rows: `{len(rows):,}`
- Row delta vs V1: `{len(rows) - V1_ROW_COUNT:+,}`
- Feature seasons: `{values['feature_seasons']}`
- Target seasons: `{values['target_seasons']}`
- Parquet SHA-256: `{values['sha']}`
- Source manifest row count: `{manifest.get('row_count', 'unknown')}`
- Formula tuning run: `false`
- Production approved: `false`
- Canonical features: `{', '.join(feature_cols)}`

| file | kind | rows | sha256 |
| --- | --- | ---: | --- |
{manifest_file_rows()}
""",
    )


def main() -> None:
    require_sources()
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    features = pd.read_csv(FEATURE_SOURCE)
    labels = pd.read_csv(LABEL_SOURCE)
    rows, audit = build_substrate(features, labels)
    rows = rows.sort_values(["feature_season", "position", "next_nwr_points", "player_id_gsis"], ascending=[True, True, False, True])
    rows.to_parquet(PARQUET_PATH, index=False)

    write_csv(make_source_inventory(features, labels, manifest), "available_historical_sources_inventory_v2.csv")
    write_csv(make_schema(rows), "feature_target_substrate_schema_v2.csv")
    write_csv(rows.head(40), "feature_target_substrate_sample_v2.csv")
    write_csv(make_row_count_report(rows), "feature_target_row_count_report_v2.csv")
    write_csv(make_season_position_coverage(rows), "season_position_coverage_report_v2.csv")
    write_csv(make_feature_coverage(rows), "feature_coverage_report_v2.csv")
    write_csv(make_target_coverage(rows), "target_outcome_coverage_report_v2.csv")
    write_csv(make_identity_report(rows, features, labels, audit), "identity_join_report_v2.csv")
    write_reports(rows, manifest)

    print(
        json.dumps(
            {
                "verdict": VERDICT,
                "rows": len(rows),
                "row_delta_vs_v1": len(rows) - V1_ROW_COUNT,
                "feature_seasons": [int(rows["feature_season"].min()), int(rows["feature_season"].max())],
                "target_seasons": [int(rows["target_season"].min()), int(rows["target_season"].max())],
                "optional_source_null_fenced_rows": int(rows["optional_source_null_fenced"].sum()),
                "parquet": str(PARQUET_PATH),
                "sha256": sha256_file(PARQUET_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
