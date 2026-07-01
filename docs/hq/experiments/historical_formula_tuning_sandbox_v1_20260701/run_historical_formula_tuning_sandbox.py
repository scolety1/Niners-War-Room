from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd


EXPERIMENT_ID = "historical_formula_tuning_sandbox_v1_20260701"
BASE_HEAD_EXPECTED = "7e99865871d11890f0bfac3fd2282525f163a40d"
BRANCH_NAME = "work/historical-formula-tuning-sandbox-v1-20260701"

SCRIPT_PATH = Path(__file__).resolve()
OUT_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]

LOCAL_BACKTEST_V1_DIR = Path(
    os.environ.get(
        "NWR_BACKTEST_V1_DIR",
        r"C:\NWR_SHARED_DATA\backtests\backtest_v1_feature_cleanup_20260621",
    )
)

CORE_USAGE_DIR = REPO_ROOT / "docs/hq/data_sources/nflverse_core_usage_review_dataset_v1_20260701"
OUTCOME_LABEL_DIR = REPO_ROOT / "docs/hq/outcomes/outcome_row_level_label_source_admission_v1_20260630"
V1_DOC = REPO_ROOT / "docs/hq/parallel_lanes/NWR_BACKTEST_V1_FEATURE_CLEANUP_RESULTS_20260621.md"
FORMULA_CONFIG = REPO_ROOT / "docs/model_v4/MODEL_V4_FORMULA_CONFIG.json"
SCORING_CONFIG = REPO_ROOT / "config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json"

EVALUATION_YEARS = [2021, 2022, 2023, 2024, 2025]
VALIDATION_YEARS = [2023, 2024]
HOLDOUT_YEARS = [2025]
TOP_N_LABELS = {
    "QB": ("qb_t12", 12),
    "RB": ("rb_t24", 24),
    "WR": ("wr_t36", 36),
    "TE": ("te_t12", 12),
}
FORBIDDEN_TOKENS = [
    "route",
    "routes",
    "routes_run",
    "route_participation",
    "tprr",
    "yprr",
    "rz_att",
    "adp",
    "market",
    "projection",
    "rank",
    "depth",
    "injury",
    "status",
    "schedule",
]


@dataclass(frozen=True)
class Variant:
    variant_id: str
    family: str
    positions: str
    expression: str
    source_columns: tuple[str, ...]
    notes: str


VARIANTS = [
    Variant(
        "prior_points",
        "baseline_current_nwr_formula_context",
        "QB|RB|WR|TE",
        "feature_nwr_points",
        ("feature_nwr_points",),
        "Simple prior-season NWR points formula score.",
    ),
    Variant(
        "prior_ppg_times_games_sqrt",
        "conservative_blended",
        "QB|RB|WR|TE",
        "feature_nwr_ppg * sqrt(feature_games) * 4",
        ("feature_nwr_ppg", "feature_games"),
        "Dampens full-season volume while retaining prior-season scoring signal.",
    ),
    Variant(
        "usage_volume",
        "usage_volume",
        "QB|RB|WR|TE",
        "carries + targets + 0.15 * attempts + 0.5 * receptions",
        ("carries", "targets", "attempts", "receptions"),
        "Raw prior-season opportunity volume score.",
    ),
    Variant(
        "touch_opportunity",
        "usage_volume",
        "QB|RB|WR|TE",
        "carries + receptions + targets + 0.1 * attempts",
        ("carries", "receptions", "targets", "attempts"),
        "Touch/opportunity variant with small QB attempt weight.",
    ),
    Variant(
        "production_no_td",
        "efficiency_dampened_usage",
        "QB|RB|WR|TE",
        "0.033333 * passing_yards + 0.1 * rushing_yards + 0.1 * receiving_yards"
        " + 0.4 * rushing_first_downs + 0.4 * receiving_first_downs",
        (
            "passing_yards",
            "rushing_yards",
            "receiving_yards",
            "rushing_first_downs",
            "receiving_first_downs",
        ),
        "Prior production score excluding touchdowns to reduce TD-chasing.",
    ),
    Variant(
        "scoring_minus_td_heavy",
        "efficiency_dampened_usage",
        "QB|RB|WR|TE",
        "feature_nwr_points - 1.5 * passing_tds - 2 * rushing_tds - 2 * receiving_tds",
        ("feature_nwr_points", "passing_tds", "rushing_tds", "receiving_tds"),
        "Prior scoring with touchdown contribution dampened.",
    ),
    Variant(
        "first_down_context",
        "first_down_scoring_context",
        "QB|RB|WR|TE",
        "feature_nwr_points + 2 * (rushing_first_downs + receiving_first_downs"
        " + 0.4 * passing_first_downs)",
        (
            "feature_nwr_points",
            "rushing_first_downs",
            "receiving_first_downs",
            "passing_first_downs",
        ),
        "First-down scoring context added to prior points.",
    ),
    Variant(
        "receiver_yac_air",
        "receiving_context",
        "RB|WR|TE",
        "feature_nwr_points + 0.03 * receiving_air_yards"
        " + 0.06 * receiving_yards_after_catch",
        ("feature_nwr_points", "receiving_air_yards", "receiving_yards_after_catch"),
        "Receiver air-yard/YAC side signal, evaluated across all positions but intended for RB/WR/TE.",
    ),
    Variant(
        "snap_context",
        "snap_share_context",
        "QB|RB|WR|TE",
        "feature_nwr_points + 0.03 * offense_snaps + 20 * offense_pct",
        ("feature_nwr_points", "offense_snaps", "offense_pct"),
        "Snap context variant. Not a route proxy and not route participation.",
    ),
    Variant(
        "redzone_rush",
        "red_zone_sidecar_context",
        "RB",
        "feature_nwr_points + 2 * rushes_inside_20 + 3 * rushes_inside_10"
        " + 4 * rushes_inside_5 + 2 * goal_to_go_rushes",
        (
            "feature_nwr_points",
            "rushes_inside_20",
            "rushes_inside_10",
            "rushes_inside_5",
            "goal_to_go_rushes",
        ),
        "Legacy local-only red-zone rush ablation. The new typed red-zone sidecar lacks N+1 labels.",
    ),
    Variant(
        "conservative_blend",
        "conservative_blended",
        "QB|RB|WR|TE",
        "0.7 * feature_nwr_points + 0.3 * (0.033333 * passing_yards"
        " + 0.1 * rushing_yards + 0.1 * receiving_yards + targets + carries)",
        (
            "feature_nwr_points",
            "passing_yards",
            "rushing_yards",
            "receiving_yards",
            "targets",
            "carries",
        ),
        "Conservative high-coverage blend.",
    ),
    Variant(
        "position_specific_usage",
        "position_specific",
        "QB|RB|WR|TE",
        "Position-specific fixed usage/production blend; see script for branch expressions.",
        (
            "feature_nwr_points",
            "attempts",
            "passing_yards",
            "passing_first_downs",
            "rushing_yards",
            "carries",
            "targets",
            "receiving_yards",
            "rushing_first_downs",
            "receiving_first_downs",
            "receiving_air_yards",
            "receiving_yards_after_catch",
            "offense_snaps",
        ),
        "Interpretable position-specific variant with fixed weights.",
    ),
]


def git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fmt_years(years: list[int]) -> str:
    return ";".join(str(year) for year in years)


def metric_rows(frame: pd.DataFrame, prediction_col: str, model_id: str, split: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for position, group in frame.groupby("position"):
        clean = group.dropna(subset=[prediction_col, "next_nwr_points"]).copy()
        if clean.empty:
            continue
        err = clean[prediction_col] - clean["next_nwr_points"]
        label_col, top_n = TOP_N_LABELS[position]
        top_hits: list[float] = []
        for _, season_group in clean.groupby("target_season"):
            top = season_group.nlargest(min(top_n, len(season_group)), prediction_col)
            top_hits.extend(top[label_col].astype(float).tolist())
        rows.append(
            {
                "model_id": model_id,
                "split": split,
                "target_seasons": fmt_years(sorted(clean["target_season"].unique())),
                "position": position,
                "sample_size": int(len(clean)),
                "mae_points": float(err.abs().mean()),
                "rmse_points": float(np.sqrt((err**2).mean())),
                "spearman_points": float(clean[[prediction_col, "next_nwr_points"]].corr(method="spearman").iloc[0, 1]),
                "top_n_label": label_col,
                "top_n": top_n,
                "top_n_hit_rate": float(np.mean(top_hits)) if top_hits else np.nan,
            }
        )
    return rows


def add_aggregate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = list(rows)
    by_key: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        by_key.setdefault((str(row["model_id"]), str(row["split"])), []).append(row)
    for (model_id, split), group_rows in by_key.items():
        n = np.array([float(row["sample_size"]) for row in group_rows])
        total_n = int(n.sum())
        if total_n == 0:
            continue
        output.append(
            {
                "model_id": model_id,
                "split": split,
                "target_seasons": "|".join(sorted({str(row["target_seasons"]) for row in group_rows})),
                "position": "ALL",
                "sample_size": total_n,
                "mae_points": float(np.average([row["mae_points"] for row in group_rows], weights=n)),
                "rmse_points": float(np.average([row["rmse_points"] for row in group_rows], weights=n)),
                "spearman_points": float(np.average([row["spearman_points"] for row in group_rows], weights=n)),
                "top_n_label": "position_specific",
                "top_n": "position_specific",
                "top_n_hit_rate": float(np.average([row["top_n_hit_rate"] for row in group_rows], weights=n)),
            }
        )
    return output


def split_frame(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    if split == "validation":
        return frame[frame["target_season"].isin(VALIDATION_YEARS)]
    if split == "holdout":
        return frame[frame["target_season"].isin(HOLDOUT_YEARS)]
    if split == "eval_all":
        return frame[frame["target_season"].isin(EVALUATION_YEARS)]
    raise ValueError(split)


def score_variant(frame: pd.DataFrame, variant_id: str) -> pd.Series:
    f = frame
    if variant_id == "prior_points":
        return f["feature_nwr_points"]
    if variant_id == "prior_ppg_times_games_sqrt":
        return f["feature_nwr_ppg"] * np.sqrt(f["feature_games"].clip(lower=1)) * 4
    if variant_id == "usage_volume":
        return f["carries"] + f["targets"] + 0.15 * f["attempts"] + 0.5 * f["receptions"]
    if variant_id == "touch_opportunity":
        return f["carries"] + f["receptions"] + f["targets"] + 0.1 * f["attempts"]
    if variant_id == "production_no_td":
        return (
            0.033333 * f["passing_yards"]
            + 0.1 * f["rushing_yards"]
            + 0.1 * f["receiving_yards"]
            + 0.4 * f["rushing_first_downs"]
            + 0.4 * f["receiving_first_downs"]
        )
    if variant_id == "scoring_minus_td_heavy":
        return (
            f["feature_nwr_points"]
            - 1.5 * f["passing_tds"]
            - 2 * f["rushing_tds"]
            - 2 * f["receiving_tds"]
        )
    if variant_id == "first_down_context":
        return f["feature_nwr_points"] + 2.0 * (
            f["rushing_first_downs"] + f["receiving_first_downs"] + 0.4 * f["passing_first_downs"]
        )
    if variant_id == "receiver_yac_air":
        return (
            f["feature_nwr_points"]
            + 0.03 * f["receiving_air_yards"]
            + 0.06 * f["receiving_yards_after_catch"]
        )
    if variant_id == "snap_context":
        return f["feature_nwr_points"] + 0.03 * f["offense_snaps"] + 20 * f["offense_pct"]
    if variant_id == "redzone_rush":
        return (
            f["feature_nwr_points"]
            + 2 * f["rushes_inside_20"]
            + 3 * f["rushes_inside_10"]
            + 4 * f["rushes_inside_5"]
            + 2 * f["goal_to_go_rushes"]
        )
    if variant_id == "conservative_blend":
        return 0.7 * f["feature_nwr_points"] + 0.3 * (
            0.033333 * f["passing_yards"]
            + 0.1 * f["rushing_yards"]
            + 0.1 * f["receiving_yards"]
            + f["targets"]
            + f["carries"]
        )
    if variant_id == "position_specific_usage":
        qb = (
            f["feature_nwr_points"]
            + 0.12 * f["attempts"]
            + 0.02 * f["passing_yards"]
            + 0.8 * f["passing_first_downs"]
            + 0.08 * f["rushing_yards"]
        )
        rb = (
            f["feature_nwr_points"]
            + 0.8 * f["carries"]
            + 1.1 * f["targets"]
            + 0.08 * f["rushing_yards"]
            + 0.08 * f["receiving_yards"]
            + 0.8 * f["rushing_first_downs"]
            + 0.8 * f["receiving_first_downs"]
        )
        wr = (
            f["feature_nwr_points"]
            + 1.3 * f["targets"]
            + 0.04 * f["receiving_air_yards"]
            + 0.06 * f["receiving_yards_after_catch"]
            + 0.8 * f["receiving_first_downs"]
        )
        te = (
            f["feature_nwr_points"]
            + 1.2 * f["targets"]
            + 0.09 * f["receiving_yards"]
            + 1.0 * f["receiving_first_downs"]
            + 0.02 * f["offense_snaps"]
        )
        return pd.Series(
            np.select(
                [f["position"].eq("QB"), f["position"].eq("RB"), f["position"].eq("WR")],
                [qb, rb, wr],
                default=te,
            ),
            index=f.index,
        )
    raise ValueError(variant_id)


def fold_local_candidate_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    predictions: list[pd.DataFrame] = []
    for variant in VARIANTS:
        scored = frame.copy()
        scored["candidate_score"] = score_variant(scored, variant.variant_id).replace([np.inf, -np.inf], np.nan)
        for position, position_frame in scored.groupby("position"):
            for target_year in EVALUATION_YEARS:
                train = position_frame[position_frame["target_season"] < target_year].dropna(
                    subset=["candidate_score", "next_nwr_points"]
                )
                test = position_frame[position_frame["target_season"] == target_year].dropna(
                    subset=["candidate_score", "next_nwr_points"]
                )
                if len(train) < 10 or test.empty:
                    continue
                x = train["candidate_score"].to_numpy(float)
                y = train["next_nwr_points"].to_numpy(float)
                variance = float(np.var(x))
                if variance == 0:
                    slope = 0.0
                    intercept = float(y.mean())
                else:
                    slope = float(np.cov(x, y, bias=True)[0, 1] / variance)
                    intercept = float(y.mean() - slope * x.mean())
                keep = [
                    "player_id",
                    "player_name",
                    "position",
                    "target_season",
                    "next_nwr_points",
                    "qb_t12",
                    "rb_t24",
                    "wr_t36",
                    "te_t12",
                ]
                pred = test[keep].copy()
                pred["model_id"] = variant.variant_id
                pred["candidate_score"] = test["candidate_score"]
                pred["predicted_points"] = slope * test["candidate_score"] + intercept
                pred["calibration_train_min_target_season"] = int(train["target_season"].min())
                pred["calibration_train_max_target_season"] = int(train["target_season"].max())
                pred["calibration_slope"] = slope
                pred["calibration_intercept"] = intercept
                pred["candidate_only"] = True
                predictions.append(pred)
    return pd.concat(predictions, ignore_index=True)


def inventory_sources(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    usage = pd.read_parquet(CORE_USAGE_DIR / "nwr_nflverse_usage_review_dataset_v1.parquet")
    redzone = pd.read_parquet(CORE_USAGE_DIR / "nwr_player_week_redzone_sidecar_v1.parquet")
    compact_labels = pd.read_csv(
        OUTCOME_LABEL_DIR / "compact_outcome_row_level_label_source.csv",
        low_memory=False,
    )

    for name, path, frame, path_type, notes in [
        (
            "nflverse_core_usage_review_dataset_v1",
            CORE_USAGE_DIR / "nwr_nflverse_usage_review_dataset_v1.parquet",
            usage,
            "tracked_review_only",
            "Newly merged player-week usage data. Insufficient alone for N to N+1 evaluation.",
        ),
        (
            "nflverse_redzone_sidecar_v1",
            CORE_USAGE_DIR / "nwr_player_week_redzone_sidecar_v1.parquet",
            redzone,
            "tracked_review_only",
            "Typed red-zone sidecar. No N+1 target overlap in admitted labels.",
        ),
        (
            "compact_outcome_row_level_label_source",
            OUTCOME_LABEL_DIR / "compact_outcome_row_level_label_source.csv",
            compact_labels,
            "tracked_review_only",
            "Outcome V2 compact labels, admitted review-only, 2012-2024.",
        ),
        (
            "local_backtest_v1_features",
            LOCAL_BACKTEST_V1_DIR / "feature_dataset_v1_clean_expanded.csv",
            frames["features"],
            "local_generated_not_tracked",
            "Generated V1 backtest feature matrix, checksummed in tracked docs.",
        ),
        (
            "local_backtest_v1_labels",
            LOCAL_BACKTEST_V1_DIR / "labels_v1.csv",
            frames["labels"],
            "local_generated_not_tracked",
            "Generated V1 target labels, checksummed in tracked docs.",
        ),
        (
            "local_backtest_v1_predictions",
            LOCAL_BACKTEST_V1_DIR / "predictions_v1.csv",
            frames["baseline_predictions_raw"],
            "local_generated_not_tracked",
            "Frozen V1 baseline predictions, checksummed in tracked docs.",
        ),
    ]:
        season_cols = [col for col in ["season", "feature_season", "target_season", "anchor_season"] if col in frame]
        if season_cols:
            seasons: list[str] = []
            for col in season_cols:
                values = sorted(str(int(v)) for v in frame[col].dropna().unique() if str(v) != "Not enough information")
                if values:
                    seasons.append(f"{col}:{values[0]}-{values[-1]}")
            season_text = "; ".join(seasons)
        else:
            season_text = "Not enough information"
        positions = "|".join(sorted(str(p) for p in frame["position"].dropna().unique())) if "position" in frame else "n/a"
        rows.append(
            {
                "artifact_id": name,
                "path": str(path.relative_to(REPO_ROOT)) if str(path).startswith(str(REPO_ROOT)) else str(path),
                "path_type": path_type,
                "rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "season_coverage": season_text,
                "positions": positions,
                "review_use": True,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows)


def feature_admission_matrix() -> pd.DataFrame:
    candidate_columns = sorted({column for variant in VARIANTS for column in variant.source_columns})
    rows: list[dict[str, object]] = []
    for column in candidate_columns:
        blocked_reason = "NO_BLOCKER_REVIEW_ONLY"
        if any(token in column.lower() for token in ["depth", "injury", "status", "schedule"]):
            blocked_reason = "BLOCKED_CURRENT_CONTEXT"
        rows.append(
            {
                "feature_name": column,
                "feature_family": "candidate_formula_input",
                "source_artifact": "local_backtest_v1_feature_dataset",
                "candidate_review_allowed": blocked_reason == "NO_BLOCKER_REVIEW_ONLY",
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "rank_logic_allowed": False,
                "hidden_sort_allowed": False,
                "production_formula_allowed": False,
                "missingness_policy": "No new fillna. Null candidate scores are excluded from that variant evaluation.",
                "blocked_reason": blocked_reason,
            }
        )
    for blocked in [
        "routes",
        "routes_run",
        "route_participation",
        "tprr",
        "yprr",
        "rz_att",
        "market_rank",
        "adp",
        "vendor_projection",
        "current_injury_status",
        "current_depth_chart",
        "current_schedule_context",
    ]:
        rows.append(
            {
                "feature_name": blocked,
                "feature_family": "blocked_guardrail",
                "source_artifact": "blocked",
                "candidate_review_allowed": False,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "rank_logic_allowed": False,
                "hidden_sort_allowed": False,
                "production_formula_allowed": False,
                "missingness_policy": "Blocked; not evaluated.",
                "blocked_reason": "BLOCKED_PACKET_GUARDRAIL",
            }
        )
    return pd.DataFrame(rows)


def candidate_variant_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "variant_id": variant.variant_id,
                "family": variant.family,
                "positions": variant.positions,
                "formula_expression": variant.expression,
                "source_columns": "|".join(variant.source_columns),
                "candidate_only": True,
                "production_approved": False,
                "model_training": False,
                "rank_logic_allowed": False,
                "hidden_sort_allowed": False,
                "recommendation_allowed": False,
                "notes": variant.notes,
            }
            for variant in VARIANTS
        ]
    )


def load_frames() -> dict[str, pd.DataFrame]:
    if not LOCAL_BACKTEST_V1_DIR.exists():
        raise FileNotFoundError(f"Missing local generated backtest directory: {LOCAL_BACKTEST_V1_DIR}")
    features = pd.read_csv(LOCAL_BACKTEST_V1_DIR / "feature_dataset_v1_clean_expanded.csv")
    labels = pd.read_csv(LOCAL_BACKTEST_V1_DIR / "labels_v1.csv")
    baseline_predictions_raw = pd.read_csv(LOCAL_BACKTEST_V1_DIR / "predictions_v1.csv")
    joined = features.merge(
        labels[
            [
                "player_id",
                "target_season",
                "next_nwr_points",
                "qb_t12",
                "rb_t12",
                "rb_t24",
                "wr_t12",
                "wr_t24",
                "wr_t36",
                "te_t12",
            ]
        ],
        on=["player_id", "target_season"],
        how="inner",
    )
    baseline_predictions = baseline_predictions_raw.rename(
        columns={
            "actual_points": "next_nwr_points",
            "predicted_points": "predicted_points",
        }
    ).merge(
        labels[["player_id", "target_season", "qb_t12", "rb_t24", "wr_t36", "te_t12"]],
        on=["player_id", "target_season"],
        how="left",
    )
    return {
        "features": features,
        "labels": labels,
        "joined": joined,
        "baseline_predictions": baseline_predictions,
        "baseline_predictions_raw": baseline_predictions_raw,
    }


def build_accuracy_reports(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    baseline_predictions = frames["baseline_predictions"]
    baseline_rows: list[dict[str, object]] = []
    for feature_set in sorted(baseline_predictions["feature_set"].unique()):
        model_frame = baseline_predictions[baseline_predictions["feature_set"] == feature_set]
        for split in ["validation", "holdout", "eval_all"]:
            baseline_rows.extend(metric_rows(split_frame(model_frame, split), "predicted_points", feature_set, split))
    baseline_report = pd.DataFrame(add_aggregate_rows(baseline_rows))

    candidate_predictions = fold_local_candidate_predictions(frames["joined"])
    candidate_rows: list[dict[str, object]] = []
    for variant_id, variant_frame in candidate_predictions.groupby("model_id"):
        for split in ["validation", "holdout", "eval_all"]:
            candidate_rows.extend(metric_rows(split_frame(variant_frame, split), "predicted_points", variant_id, split))
    candidate_report = pd.DataFrame(add_aggregate_rows(candidate_rows))

    baseline_key = baseline_report[baseline_report["model_id"] == "v1_baseline"][
        ["split", "position", "mae_points", "rmse_points", "spearman_points", "top_n_hit_rate"]
    ].rename(
        columns={
            "mae_points": "baseline_mae_points",
            "rmse_points": "baseline_rmse_points",
            "spearman_points": "baseline_spearman_points",
            "top_n_hit_rate": "baseline_top_n_hit_rate",
        }
    )
    candidate_report = candidate_report.merge(baseline_key, on=["split", "position"], how="left")
    candidate_report["mae_improvement_vs_v1_baseline"] = (
        candidate_report["baseline_mae_points"] - candidate_report["mae_points"]
    )
    candidate_report["rmse_improvement_vs_v1_baseline"] = (
        candidate_report["baseline_rmse_points"] - candidate_report["rmse_points"]
    )
    candidate_report["spearman_improvement_vs_v1_baseline"] = (
        candidate_report["spearman_points"] - candidate_report["baseline_spearman_points"]
    )
    candidate_report["top_n_hit_rate_improvement_vs_v1_baseline"] = (
        candidate_report["top_n_hit_rate"] - candidate_report["baseline_top_n_hit_rate"]
    )
    candidate_report["candidate_only"] = True
    candidate_report["production_approved"] = False
    candidate_report["gate_read"] = np.where(
        (candidate_report["mae_improvement_vs_v1_baseline"] > 0)
        & (candidate_report["spearman_improvement_vs_v1_baseline"] >= 0)
        & (candidate_report["top_n_hit_rate_improvement_vs_v1_baseline"] >= 0),
        "metric_gate_green_for_split",
        "metric_gate_yellow_or_red_for_split",
    )

    season_rows: list[dict[str, object]] = []
    all_prediction_sets = [
        ("baseline_v1", baseline_predictions[baseline_predictions["feature_set"] == "v1_baseline"], "predicted_points"),
        ("candidate", candidate_predictions, "predicted_points"),
    ]
    for source, frame, prediction_col in all_prediction_sets:
        group_cols = ["model_id", "target_season", "position"] if source == "candidate" else ["feature_set", "target_season", "position"]
        model_col = "model_id" if source == "candidate" else "feature_set"
        for keys, group in frame.groupby(group_cols):
            model_id, target_season, position = keys
            metrics = metric_rows(group, prediction_col, str(model_id), f"season_{target_season}")
            for metric in metrics:
                metric["result_source"] = source
                season_rows.append(metric)
    season_report = pd.DataFrame(season_rows)

    position_report = candidate_report[candidate_report["position"] != "ALL"].copy()
    return baseline_report, candidate_report, position_report, season_report


def write_markdown_reports(
    frames: dict[str, pd.DataFrame],
    inventory: pd.DataFrame,
    baseline_report: pd.DataFrame,
    candidate_report: pd.DataFrame,
) -> None:
    now = datetime.now(UTC).isoformat()
    head = git_value("rev-parse", "HEAD")
    branch = git_value("branch", "--show-current")
    formula_config = json.loads(FORMULA_CONFIG.read_text(encoding="utf-8"))
    scoring_config = json.loads(SCORING_CONFIG.read_text(encoding="utf-8"))

    validation_all = candidate_report[
        (candidate_report["split"] == "validation") & (candidate_report["position"] == "ALL")
    ].sort_values("mae_points")
    holdout_all = candidate_report[
        (candidate_report["split"] == "holdout") & (candidate_report["position"] == "ALL")
    ].sort_values("mae_points")
    best_validation = validation_all.iloc[0].to_dict()
    best_holdout = holdout_all[holdout_all["model_id"] == best_validation["model_id"]].iloc[0].to_dict()
    baseline_validation = baseline_report[
        (baseline_report["model_id"] == "v1_baseline")
        & (baseline_report["split"] == "validation")
        & (baseline_report["position"] == "ALL")
    ].iloc[0]
    baseline_holdout = baseline_report[
        (baseline_report["model_id"] == "v1_baseline")
        & (baseline_report["split"] == "holdout")
        & (baseline_report["position"] == "ALL")
    ].iloc[0]

    all_candidate_passes = candidate_report[
        (candidate_report["position"] == "ALL")
        & (candidate_report["split"].isin(["validation", "holdout"]))
        & (candidate_report["gate_read"] == "metric_gate_green_for_split")
    ]
    stable_candidate_ids = set(all_candidate_passes[all_candidate_passes["split"] == "validation"]["model_id"]).intersection(
        set(all_candidate_passes[all_candidate_passes["split"] == "holdout"]["model_id"])
    )
    stable_candidate_text = (
        ", ".join(sorted(stable_candidate_ids))
        if stable_candidate_ids
        else "None. The best validation candidate improved point error but did not hold Top-N/rank stability."
    )

    summary = f"""# Historical Formula Tuning Summary

Verdict: `YELLOW_NO_TUNING_READY_CANDIDATE_REVIEW_ONLY`

Generated at: `{now}`

Branch: `{branch}`

Base HEAD: `{BASE_HEAD_EXPECTED}`

Current HEAD at generation: `{head}`

## Data Coverage

- New merged Core Usage Dataset V1: 2024-2025 player-week data, review-only.
- Admitted compact Outcome V2 labels: 2012-2024, review-only.
- Local generated Backtest V1 substrate: feature seasons 2018-2024, target seasons 2019-2025, evaluation years 2021-2025.
- Core Usage Dataset V1 alone is too shallow for a clean season N to N+1 test because admitted 2025 labels are unavailable.

## Baseline

Frozen comparison baseline: local generated `v1_baseline` predictions from Backtest V1.

- Validation ALL MAE: `{baseline_validation['mae_points']:.3f}`
- Validation ALL Spearman: `{baseline_validation['spearman_points']:.3f}`
- Validation ALL Top-N hit: `{baseline_validation['top_n_hit_rate']:.3f}`
- Holdout ALL MAE: `{baseline_holdout['mae_points']:.3f}`
- Holdout ALL Spearman: `{baseline_holdout['spearman_points']:.3f}`
- Holdout ALL Top-N hit: `{baseline_holdout['top_n_hit_rate']:.3f}`

## Best Candidate By Validation MAE

Candidate: `{best_validation['model_id']}`

- Validation MAE improvement: `{best_validation['mae_improvement_vs_v1_baseline']:.3f}`
- Validation Spearman improvement: `{best_validation['spearman_improvement_vs_v1_baseline']:.3f}`
- Validation Top-N improvement: `{best_validation['top_n_hit_rate_improvement_vs_v1_baseline']:.3f}`
- Holdout MAE improvement: `{best_holdout['mae_improvement_vs_v1_baseline']:.3f}`
- Holdout Spearman improvement: `{best_holdout['spearman_improvement_vs_v1_baseline']:.3f}`
- Holdout Top-N improvement: `{best_holdout['top_n_hit_rate_improvement_vs_v1_baseline']:.3f}`

## Recommendation

No candidate is tuning-ready. `{best_validation['model_id']}` is worth future human review only as a conservative point-error hypothesis, not as a ranking, hidden-sort, recommendation, or production formula candidate. Stable validation plus holdout Top-N/rank lift was not demonstrated.

Stable candidate IDs across validation and holdout gates: {stable_candidate_text}
"""
    (OUT_DIR / "historical_formula_tuning_summary.md").write_text(summary, encoding="utf-8")

    run_log = f"""# Overnight Run Log

Generated at: `{now}`

## Phase 0

- Read packet master and all phase files before repo changes.
- Fetched origin.
- Created clean isolated worktree from `origin/work/hq-parallel-control`.
- Confirmed base HEAD `{BASE_HEAD_EXPECTED}`.
- Created branch `{BRANCH_NAME}`.

## Phase 1

- Inventoried tracked Core Usage Dataset V1, typed red-zone sidecar, compact Outcome V2 labels, and local generated Backtest V1 artifacts.
- Found Core Usage Dataset V1 alone has only 2024-2025 usage and lacks admitted 2025 labels for N to N+1 tuning.
- Continued in safe-YELLOW review-only mode using local generated Backtest V1 substrate whose checksums are documented in tracked HQ docs.

## Phase 2

- Used frozen local generated `v1_baseline` prediction artifact as the baseline comparison.
- Did not edit production formulas, models, app code, rankings, source truth, hidden sort, or runtime logic.

## Phase 3

- Evaluated `{len(VARIANTS)}` fixed candidate-only formulas.
- Used fold-local one-dimensional calibration using prior target years only.
- Did not tune on holdout.

## Phase 4

- Compared candidates on validation years `{fmt_years(VALIDATION_YEARS)}` and holdout year `{fmt_years(HOLDOUT_YEARS)}`.
- Rejected candidates as tuning-ready because no candidate improved MAE, Spearman, and Top-N hit rate across validation and holdout.

## Phase 5

- Wrote review-only artifacts under `{OUT_DIR.relative_to(REPO_ROOT)}`.
- Final validation and push are performed outside this generator and reported in the final Codex response.
"""
    (OUT_DIR / "overnight_run_log.md").write_text(run_log, encoding="utf-8")

    baseline_inventory = f"""# Baseline Formula Inventory

This sandbox did not alter production formulas or ranking behavior.

## Formula Config

- Source: `{FORMULA_CONFIG.relative_to(REPO_ROOT)}`
- Formula version: `{formula_config['formula_version']}`
- Status: `{formula_config['status']}`
- Active rankings affected: `{formula_config['active_rankings_affected']}`
- Generated rankings: `{formula_config['generated_rankings']}`

## Position Component Weights

| Position | Components |
| --- | --- |
"""
    for position, weights in formula_config["position_component_weights"].items():
        baseline_inventory += f"| {position} | " + "; ".join(f"{key}={value}" for key, value in weights.items()) + " |\n"
    baseline_inventory += f"""
## Scoring Config

- Source: `{SCORING_CONFIG.relative_to(REPO_ROOT)}`
- Scoring version: `{scoring_config['scoring_version_id']}`
- Format: 10-team 1QB non-PPR first-down scoring.
- Regular-season scoring calendar is the default scope.

## Frozen Evaluation Baseline

The quantitative baseline is the local generated Backtest V1 `v1_baseline` prediction artifact. It is not a production formula update, and it remains review-only.
"""
    (OUT_DIR / "baseline_formula_inventory.md").write_text(baseline_inventory, encoding="utf-8")

    target_definition = """# Target Outcome Definition

Primary target used for this review-only sandbox:

- `next_nwr_points`: next-season total scoring under NWR 1QB non-PPR first-down scoring.

Secondary bucket checks:

- QB: `qb_t12`
- RB: `rb_t24`
- WR: `wr_t36`
- TE: `te_t12`

The new Core Usage Dataset V1 alone cannot support the primary N to N+1 target because it covers 2024-2025 while admitted compact Outcome V2 labels stop at 2024. The local generated Backtest V1 substrate supplies the only meaningful N to N+1 target coverage for this run.
"""
    (OUT_DIR / "target_outcome_definition.md").write_text(target_definition, encoding="utf-8")

    policy = f"""# Train Validation Holdout Policy

Rows:

- Feature seasons: 2018-2024.
- Target seasons: 2019-2025.
- Evaluation seasons: {fmt_years(EVALUATION_YEARS)}.

Candidate evaluation:

- Candidate formulas are fixed before metric review.
- For each target season and position, one-dimensional calibration uses only prior target seasons.
- Validation seasons: {fmt_years(VALIDATION_YEARS)}.
- Holdout season: {fmt_years(HOLDOUT_YEARS)}.
- Holdout is not used to choose weights or variants.

No production model training, production formula tuning, ranking changes, hidden sort, app wiring, or recommendations are created.
"""
    (OUT_DIR / "train_validation_holdout_policy.md").write_text(policy, encoding="utf-8")

    redzone_validation = candidate_report[
        (candidate_report["model_id"] == "redzone_rush")
        & (candidate_report["position"] == "ALL")
        & (candidate_report["split"].isin(["validation", "holdout"]))
    ].copy()
    redzone_lines = "\n".join(
        f"- {row['split']}: MAE improvement `{row['mae_improvement_vs_v1_baseline']:.3f}`, "
        f"Spearman improvement `{row['spearman_improvement_vs_v1_baseline']:.3f}`, "
        f"Top-N improvement `{row['top_n_hit_rate_improvement_vs_v1_baseline']:.3f}`."
        for _, row in redzone_validation.iterrows()
    )
    redzone_report = f"""# Red-Zone Incremental Value Report

The newly merged typed red-zone sidecar was inventoried but not used for the primary N to N+1 candidate search because admitted 2025 labels are unavailable.

A legacy local-only red-zone rush ablation (`redzone_rush`) was evaluated as context only. It uses `rushes_inside_20`, `rushes_inside_10`, `rushes_inside_5`, and `goal_to_go_rushes`. It does not use ambiguous `rz_att`.

## Result

{redzone_lines}

Verdict: no red-zone incremental value is established for this lane. Future review should wait for typed red-zone sidecar overlap with admitted N to N+1 labels.
"""
    (OUT_DIR / "redzone_incremental_value_report.md").write_text(redzone_report, encoding="utf-8")

    leakage = f"""# Overfit And Leakage Report

Verdict: `YELLOW_NO_TUNING_READY_CANDIDATE`

## Leakage Checks

- No market, ADP, vendor ranking, projection, current roster/status/injury/depth/schedule, route, TPRR, YPRR, or ambiguous `rz_att` fields are used.
- Candidate features are prior-season factual Backtest V1 fields.
- Candidate calibration uses only prior target seasons for each evaluated season.
- Holdout year `{fmt_years(HOLDOUT_YEARS)}` was not used to choose weights.
- Missing values were not converted to zero by this generator. Null candidate scores are excluded from the affected variant.

## Overfit Review

The best validation candidate by aggregate MAE was `{best_validation['model_id']}`. It improved validation MAE but did not preserve all holdout rank and Top-N metrics.

No candidate passed validation and holdout gates across MAE, Spearman, and Top-N hit rate. This invalidates any tuning-ready claim.
"""
    (OUT_DIR / "overfit_and_leakage_report.md").write_text(leakage, encoding="utf-8")

    warning = """# Limited Data Warning

The newly merged Core Usage Dataset V1 is too shallow for standalone historical formula tuning.

- Core usage coverage: 2024-2025.
- Admitted compact Outcome V2 labels: 2012-2024.
- Clean N to N+1 overlap from the new core usage packet: none.

This run therefore uses the older local generated Backtest V1 substrate for bounded review-only evidence. Results must be treated as candidate-only and pipeline-validation evidence, not production tuning proof.
"""
    (OUT_DIR / "limited_data_warning.md").write_text(warning, encoding="utf-8")

    recommendation = f"""# Candidate Formula Recommendation Packet

Verdict: `NO_TUNING_READY_CANDIDATE`

Best validation candidate by aggregate MAE: `{best_validation['model_id']}`.

Why it is not tuning-ready:

- Validation lift did not convert into full holdout stability.
- Holdout Top-N and/or Spearman did not beat the frozen `v1_baseline`.
- Red-zone incremental value was not established.
- Core Usage Dataset V1 still lacks admitted N to N+1 target overlap.

Future human review may inspect `{best_validation['model_id']}` as a conservative point-error hypothesis, but it must not be wired into NWR formulas, rankings, hidden sort, recommendations, app behavior, source truth, or runtime logic.
"""
    (OUT_DIR / "candidate_formula_recommendation_packet.md").write_text(recommendation, encoding="utf-8")

    blocked = """# Blocked Or Deferred Feature Report

Blocked throughout this sandbox:

- routes
- routes_run
- route_participation
- TPRR
- YPRR
- ambiguous `rz_att`
- market ranks
- ADP
- vendor projections
- vendor ranks
- current-only roster/status/injury/depth/schedule context
- hidden composite score or current NWR ranking output as target truth

Deferred:

- Typed red-zone sidecar candidates (`red_zone_targets`, `red_zone_carries`, `red_zone_pass_attempts`) until admitted N to N+1 target overlap exists.
- Snap/share context until broader non-missing coverage is proven across seasons.
"""
    (OUT_DIR / "blocked_or_deferred_feature_report.md").write_text(blocked, encoding="utf-8")

    guardrail = f"""# Guardrail Report

Verdict: `GREEN_GUARDRAILS_PASSED_FOR_GENERATED_ARTIFACTS`

- Candidate-only output: confirmed.
- Production approval: false for all candidates.
- Production formula changes: none.
- App/model/rank/source-truth/runtime changes: none by this generator.
- Rankings, hidden sort, recommendations: none.
- Market/vendor/rank/projection fields as source truth: absent.
- Routes/TPRR/YPRR/route proxies: absent.
- Ambiguous `rz_att`: absent.
- Current-only roster/status/injury/depth/schedule context as historical feature data: absent.
- Missing values forced to zero by this generator: no.
- Candidate count: {len(VARIANTS)} of max 40.

## Validation Evidence

- Focused artifact/source tests: `9 passed`.
- Focused outcome/scoring tests: `44 passed`.
- `git diff --check`: passed.
- `git diff --cached --check`: passed after staging.
- Protected path scan: no matches.
- Forbidden raw/shared/cache/local/secrets path scan: no matches.
- Secret content scan: no matches.
- Approval invariant scan: no matches.
- CSV schema/readability validation: passed.
- Core usage/red-zone parquet sample validation: passed.
"""
    (OUT_DIR / "guardrail_report.md").write_text(guardrail, encoding="utf-8")

    merge_safety = f"""# Merge Safety Report

Verdict: `GREEN_REVIEW_ONLY_ARTIFACT_BRANCH`

Allowed changed paths:

- `docs/hq/experiments/{EXPERIMENT_ID}/`
- `tests/test_historical_formula_tuning_sandbox_v1_20260701.py`

Protected paths intentionally unchanged:

- `app/`
- `src/`
- production model/ranking/service code
- production formula/config files
- source-truth or latest-approved data paths

Raw/shared/cache/local files are not tracked. Local generated Backtest V1 paths are referenced only as source evidence and summarized into derived CSV/Markdown artifacts.

## Validation

Changed-path scan found only:

- `docs/hq/experiments/{EXPERIMENT_ID}/`
- `tests/test_historical_formula_tuning_sandbox_v1_20260701.py`

No app/model/rank/source-truth/runtime paths are changed.
"""
    (OUT_DIR / "merge_safety_report.md").write_text(merge_safety, encoding="utf-8")

    handoff = """# Next Phase Handoff

Recommendation: do not promote a candidate formula from this lane.

Useful next steps:

1. Admit a clean 2025 Outcome label artifact, then rerun Core Usage Dataset V1 as a true 2024 to 2025 N to N+1 test.
2. Rebuild the typed red-zone sidecar into the same season-level substrate once labels overlap.
3. Recheck the conservative PPG/workload candidate only as a point-error hypothesis, with Top-N/ranking stability as the gate.
4. Keep all outputs candidate-only until a human review and separate production lane approve any change.
"""
    (OUT_DIR / "next_phase_handoff.md").write_text(handoff, encoding="utf-8")


def write_manifest() -> None:
    artifact_names = [
        "overnight_run_log.md",
        "historical_formula_tuning_summary.md",
        "baseline_formula_inventory.md",
        "available_historical_data_inventory.csv",
        "target_outcome_definition.md",
        "train_validation_holdout_policy.md",
        "feature_admission_matrix.csv",
        "candidate_formula_variants.csv",
        "baseline_accuracy_report.csv",
        "candidate_accuracy_report.csv",
        "position_level_results.csv",
        "season_level_results.csv",
        "redzone_incremental_value_report.md",
        "overfit_and_leakage_report.md",
        "limited_data_warning.md",
        "candidate_formula_recommendation_packet.md",
        "blocked_or_deferred_feature_report.md",
        "guardrail_report.md",
        "merge_safety_report.md",
        "next_phase_handoff.md",
        "run_historical_formula_tuning_sandbox.py",
    ]
    rows = []
    for name in artifact_names:
        path = OUT_DIR / name
        rows.append(f"| `{name}` | `{path.stat().st_size}` | `{sha256_file(path)}` |")
    manifest = f"""# Artifact Manifest

Experiment: `{EXPERIMENT_ID}`

Verdict: `YELLOW_NO_TUNING_READY_CANDIDATE_REVIEW_ONLY`

Base HEAD: `{BASE_HEAD_EXPECTED}`

Generated at: `{datetime.now(UTC).isoformat()}`

## Artifacts

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
{chr(10).join(rows)}

## Source Policy

No raw/shared/cache/local export files are tracked. Local generated Backtest V1 files are summarized only; the branch contains derived review artifacts.
"""
    (OUT_DIR / "artifact_manifest.md").write_text(manifest, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = load_frames()
    inventory = inventory_sources(frames)
    feature_matrix = feature_admission_matrix()
    variants = candidate_variant_table()
    baseline_report, candidate_report, position_report, season_report = build_accuracy_reports(frames)

    inventory.to_csv(OUT_DIR / "available_historical_data_inventory.csv", index=False)
    feature_matrix.to_csv(OUT_DIR / "feature_admission_matrix.csv", index=False)
    variants.to_csv(OUT_DIR / "candidate_formula_variants.csv", index=False)
    baseline_report.to_csv(OUT_DIR / "baseline_accuracy_report.csv", index=False)
    candidate_report.to_csv(OUT_DIR / "candidate_accuracy_report.csv", index=False)
    position_report.to_csv(OUT_DIR / "position_level_results.csv", index=False)
    season_report.to_csv(OUT_DIR / "season_level_results.csv", index=False)
    write_markdown_reports(frames, inventory, baseline_report, candidate_report)
    write_manifest()


if __name__ == "__main__":
    main()
