from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

NOT_ENOUGH_INFORMATION = "Not enough information"

ANCHOR_LABEL_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended"
    r"\outcome_v2_extended_anchor_horizon_labels.csv"
)
SEASON_LABEL_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended"
    r"\outcome_v2_extended_season_outcome_labels.csv"
)
PLAYER_SEASON_USAGE_PATH = Path(
    r"C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion"
    r"\panels\player_season_core_usage_panel.csv"
)
JOINED_USAGE_PATH = Path(
    r"C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion"
    r"\nfl_usage_expanded_target_backtest_joined_panel_v0.csv"
)
SHARED_OUTPUT_ROOT = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\rb_intermediate_5y_diagnostic"
)

TARGET_THRESHOLDS = (12, 15, 18, 20, 24)
MATERIAL_ACTIVE_MIN_GAMES = 8
MATERIAL_ACTIVE_MIN_POINTS = 100.0
LIMITED_RECENT_SAMPLE_GAMES = 8
MIN_TRAIN_ROWS = 40
MIN_VALIDATION_ROWS = 5
MIN_TRAIN_POSITIVES = 5
MAX_WEIGHTED_CALIBRATION_ABS_ERROR = 0.15
MAX_LARGE_BUCKET_CALIBRATION_ABS_ERROR = 0.30
MIN_ROWS_FOR_LARGE_BUCKET_CALIBRATION = 20

BLOCKED_SOURCE_TOKENS = (
    "adp",
    "market",
    "dynastyprocess",
    "cfbd",
    "gmail",
    "rotowire",
    "fantasypros",
    "projection",
    "analyst",
    "trade_value",
    "true_routes",
    "tprr",
    "yprr",
)

DATASET_FILENAME = "rb_intermediate_5y_diagnostic_dataset.csv"
TARGET_SUMMARY_FILENAME = "rb_intermediate_5y_target_summary.csv"
FOLD_METRICS_FILENAME = "rb_intermediate_5y_fold_metrics.csv"
CALIBRATION_FILENAME = "rb_intermediate_5y_calibration_buckets.csv"
ERROR_SLICES_FILENAME = "rb_intermediate_5y_error_slices.csv"
RECOMMENDATIONS_FILENAME = "rb_intermediate_5y_recommendations.csv"
MANIFEST_FILENAME = "rb_intermediate_5y_manifest.csv"


@dataclass(frozen=True)
class RBIntermediate5YDiagnosticResult:
    output_root: Path
    dataset_path: Path
    target_summary_path: Path
    fold_metrics_path: Path
    calibration_path: Path
    error_slices_path: Path
    recommendations_path: Path
    manifest_path: Path
    dataset_rows: int
    verdict: str


def required_source_paths() -> dict[str, Path]:
    return {
        "anchor_labels": ANCHOR_LABEL_PATH,
        "season_labels": SEASON_LABEL_PATH,
        "player_season_usage": PLAYER_SEASON_USAGE_PATH,
        "joined_usage": JOINED_USAGE_PATH,
    }


def validate_source_paths(source_paths: dict[str, Path] | None = None) -> list[dict[str, Any]]:
    paths = source_paths or required_source_paths()
    rows: list[dict[str, Any]] = []
    for source_name, path in paths.items():
        exists = path.exists() and path.is_file()
        rows.append(
            {
                "source_name": source_name,
                "path": str(path),
                "status": "exists_readable" if exists else "missing",
                "blocked_source_scan": _blocked_source_status(path),
                "size_bytes": path.stat().st_size if exists else 0,
                "sha256": _sha256(path) if exists else "",
            }
        )
    return rows


def load_review_only_sources(
    source_paths: dict[str, Path] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = source_paths or required_source_paths()
    source_rows = validate_source_paths(paths)
    missing = [row["path"] for row in source_rows if row["status"] != "exists_readable"]
    if missing:
        raise FileNotFoundError(f"Missing RB intermediate diagnostic source files: {missing}")
    blocked = [row["path"] for row in source_rows if row["blocked_source_scan"] != "pass"]
    if blocked:
        raise ValueError(f"Blocked source path detected for RB intermediate diagnostic: {blocked}")
    return (
        pd.read_csv(paths["anchor_labels"]),
        pd.read_csv(paths["season_labels"]),
        pd.read_csv(paths["player_season_usage"]),
        pd.read_csv(paths["joined_usage"]),
    )


def build_rb_intermediate_dataset(
    anchor_labels: pd.DataFrame,
    season_labels: pd.DataFrame,
    usage_panel: pd.DataFrame | None = None,
    joined_usage: pd.DataFrame | None = None,
) -> pd.DataFrame:
    anchors = _prepare_anchor_labels(anchor_labels)
    seasons = _prepare_season_labels(season_labels)
    usage = _prepare_usage_features(usage_panel, joined_usage)
    season_index = _season_index(seasons)
    usage_index = _usage_index(usage)
    max_target_season = int(seasons["season"].max())
    history_by_player = {
        str(player_id): group.sort_values("season").reset_index(drop=True)
        for player_id, group in seasons.groupby("player_id")
    }

    rows: list[dict[str, Any]] = []
    for anchor in anchors.itertuples(index=False):
        player_id = str(anchor.player_id)
        anchor_season = int(anchor.anchor_season)
        current = season_index.get((player_id, anchor_season))
        usage_row = usage_index.get((player_id, anchor_season))
        history = history_by_player.get(player_id, pd.DataFrame())
        row = _base_anchor_row(anchor, current, usage_row, history)
        for threshold in TARGET_THRESHOLDS:
            target = _within_5y_target(
                season_index=season_index,
                player_id=player_id,
                anchor_season=anchor_season,
                threshold=threshold,
                max_target_season=max_target_season,
            )
            prefix = _target_prefix(threshold)
            row[f"{prefix}_hit"] = target["hit"]
            row[f"{prefix}_window_complete"] = target["window_complete"]
            row[f"{prefix}_censoring_status"] = target["censoring_status"]
        row["blocked_inputs_used"] = "false"
        row["display_only"] = "true"
        row["diagnostic_only"] = "true"
        row["model_use_allowed"] = "false"
        row["training_allowed"] = "false"
        row["app_wiring_allowed"] = "false"
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["anchor_season", "player_name"]).reset_index(drop=True)


def run_rb_intermediate_5y_diagnostic(
    dataset: pd.DataFrame,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    target_summary = _target_summary_rows(dataset)
    fold_metrics: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    error_slices: list[dict[str, Any]] = []

    for threshold in TARGET_THRESHOLDS:
        field_id = _field_id(threshold)
        target_col = f"{_target_prefix(threshold)}_hit"
        complete_col = f"{_target_prefix(threshold)}_window_complete"
        complete = dataset[
            (dataset[complete_col] == True)  # noqa: E712
            & (dataset[target_col].isin(["hit", "miss"]))
        ].copy()
        complete["target"] = (complete[target_col] == "hit").astype(int)

        baseline_predictions = _rolling_baseline_predictions(complete)
        baseline_metrics, baseline_calibration, baseline_slices = _summarize_predictions(
            field_id=field_id,
            feature_set="empirical_baseline",
            frame=complete,
            predictions=baseline_predictions,
            model_description="rolling train prevalence baseline",
        )
        fold_metrics.append(baseline_metrics)
        calibration_rows.extend(baseline_calibration)
        error_slices.extend(baseline_slices)

        for feature_set in (
            "season_totals",
            "per_game_rates",
            "per_opportunity_rates",
            "role_availability",
            "recency_material_activity",
        ):
            predictions = _rolling_bucket_predictions(complete, threshold, feature_set)
            metrics, calibration, slices = _summarize_predictions(
                field_id=field_id,
                feature_set=feature_set,
                frame=complete,
                predictions=predictions,
                model_description="rolling empirical bucket model",
            )
            fold_metrics.append(metrics)
            calibration_rows.extend(calibration)
            error_slices.extend(slices)

    recommendations = _recommendation_rows(target_summary, fold_metrics, error_slices)
    return target_summary, fold_metrics, calibration_rows, error_slices, recommendations


def write_rb_intermediate_5y_diagnostic_artifacts(
    output_root: str | Path = SHARED_OUTPUT_ROOT,
    source_paths: dict[str, Path] | None = None,
) -> RBIntermediate5YDiagnosticResult:
    paths = source_paths or required_source_paths()
    anchors, seasons, usage, joined = load_review_only_sources(paths)
    dataset = build_rb_intermediate_dataset(anchors, seasons, usage, joined)
    target_summary, fold_metrics, calibration_rows, error_slices, recommendations = (
        run_rb_intermediate_5y_diagnostic(dataset)
    )
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)

    dataset_path = output / DATASET_FILENAME
    target_summary_path = output / TARGET_SUMMARY_FILENAME
    fold_metrics_path = output / FOLD_METRICS_FILENAME
    calibration_path = output / CALIBRATION_FILENAME
    error_slices_path = output / ERROR_SLICES_FILENAME
    recommendations_path = output / RECOMMENDATIONS_FILENAME
    manifest_path = output / MANIFEST_FILENAME

    dataset.to_csv(dataset_path, index=False)
    _write_csv(target_summary_path, target_summary)
    _write_csv(fold_metrics_path, fold_metrics)
    _write_csv(calibration_path, calibration_rows)
    _write_csv(error_slices_path, error_slices)
    _write_csv(recommendations_path, recommendations)
    _write_csv(
        manifest_path,
        _manifest_rows(
            paths=paths,
            outputs={
                "diagnostic_dataset": dataset_path,
                "target_summary": target_summary_path,
                "fold_metrics": fold_metrics_path,
                "calibration_buckets": calibration_path,
                "error_slices": error_slices_path,
                "recommendations": recommendations_path,
            },
            dataset_rows=len(dataset),
        ),
    )
    verdict = (
        "GREEN_DIAGNOSTIC_COMPLETE"
        if recommendations
        else "YELLOW_DIAGNOSTIC_PARTIAL"
    )
    return RBIntermediate5YDiagnosticResult(
        output_root=output,
        dataset_path=dataset_path,
        target_summary_path=target_summary_path,
        fold_metrics_path=fold_metrics_path,
        calibration_path=calibration_path,
        error_slices_path=error_slices_path,
        recommendations_path=recommendations_path,
        manifest_path=manifest_path,
        dataset_rows=len(dataset),
        verdict=verdict,
    )


def _prepare_anchor_labels(anchor_labels: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        anchor_labels,
        {"player_id", "player_name", "position", "anchor_season", "team"},
        "anchor_labels",
    )
    frame = anchor_labels.copy()
    frame["position"] = frame["position"].astype(str).str.upper()
    frame = frame[frame["position"] == "RB"].copy()
    frame["anchor_season"] = pd.to_numeric(frame["anchor_season"], errors="coerce")
    frame = frame.dropna(subset=["player_id", "anchor_season"])
    frame["anchor_season"] = frame["anchor_season"].astype(int)
    return frame


def _prepare_season_labels(season_labels: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        season_labels,
        {
            "player_id",
            "player_name",
            "position",
            "season",
            "team",
            "fantasy_points",
            "position_finish",
            "games_played",
        },
        "season_labels",
    )
    frame = season_labels.copy()
    frame["position"] = frame["position"].astype(str).str.upper()
    frame = frame[frame["position"] == "RB"].copy()
    frame["season"] = pd.to_numeric(frame["season"], errors="coerce")
    frame = frame.dropna(subset=["player_id", "season"])
    frame["season"] = frame["season"].astype(int)
    for column in ("fantasy_points", "position_finish", "games_played"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.sort_values(["player_id", "season"]).reset_index(drop=True)


def _prepare_usage_features(
    usage_panel: pd.DataFrame | None,
    joined_usage: pd.DataFrame | None,
) -> pd.DataFrame:
    usage = joined_usage.copy() if joined_usage is not None and not joined_usage.empty else None
    if usage is None and usage_panel is not None and not usage_panel.empty:
        usage = usage_panel.copy()
    if usage is None:
        return pd.DataFrame()
    required = {"season", "player_id", "position", "team"}
    if not required <= set(usage.columns):
        return pd.DataFrame()
    usage["position"] = usage["position"].astype(str).str.upper()
    usage = usage[usage["position"] == "RB"].copy()
    usage["season"] = pd.to_numeric(usage["season"], errors="coerce")
    usage = usage.dropna(subset=["player_id", "season"])
    usage["season"] = usage["season"].astype(int)
    numeric_columns = [
        "targets",
        "carries",
        "receptions",
        "rushing_yards",
        "receiving_yards",
        "rushing_first_downs",
        "receiving_first_downs",
        "touches",
        "opportunities",
        "offense_snaps",
        "games_with_usage_row",
        "offense_pct",
        "red_zone_touches",
        "inside_5_touches",
    ]
    for column in numeric_columns:
        if column not in usage.columns:
            usage[column] = np.nan
        usage[column] = pd.to_numeric(usage[column], errors="coerce")
    team_opportunities = usage.groupby(["season", "team"])["opportunities"].transform("sum")
    usage["team_opportunity_share"] = _safe_divide_series(
        usage["opportunities"],
        team_opportunities,
    )
    return usage.drop_duplicates(["player_id", "season"], keep="first")


def _base_anchor_row(
    anchor: Any,
    current: pd.Series | None,
    usage_row: pd.Series | None,
    history: pd.DataFrame,
) -> dict[str, Any]:
    anchor_season = int(anchor.anchor_season)
    current_points = _series_number(current, "fantasy_points")
    current_games = _series_number(current, "games_played")
    current_finish = _series_number(current, "position_finish")
    material = _last_materially_active(history, anchor_season)
    prior = _prior_season_row(history, anchor_season)
    first_observed = _first_observed_season(history)
    experience = _experience_year_number(history, anchor_season)
    missed_prior = _missed_prior_season_flag(prior, experience)
    limited_recent = _limited_recent_sample_flag(current, prior, material, anchor_season)

    row: dict[str, Any] = {
        "player_id": str(anchor.player_id),
        "player_name": str(anchor.player_name),
        "position": "RB",
        "anchor_season": anchor_season,
        "team": str(anchor.team),
        "current_season_row_status": "available" if current is not None else NOT_ENOUGH_INFORMATION,
        "current_fantasy_points": current_points,
        "current_position_finish": current_finish,
        "current_games_played": current_games,
        "current_points_per_game": _safe_divide(current_points, current_games),
        "experience_year_number": experience,
        "seasons_since_first_observed": (
            anchor_season - first_observed if first_observed is not None else np.nan
        ),
        "last_materially_active_season": material.get("season", np.nan),
        "last_materially_active_points": material.get("fantasy_points", np.nan),
        "last_materially_active_position_finish": material.get("position_finish", np.nan),
        "last_materially_active_games": material.get("games_played", np.nan),
        "seasons_since_last_materially_active": (
            anchor_season - int(material["season"]) if material else np.nan
        ),
        "material_activity_definition": (
            "games_played>=8 or fantasy_points>=100 or position_finish<=36"
        ),
        "missed_prior_season_flag": missed_prior,
        "missed_prior_season_flag_numeric": _flag_to_number(missed_prior),
        "limited_recent_sample_flag": limited_recent,
        "limited_recent_sample_flag_numeric": _flag_to_number(limited_recent),
        "availability_caveat": _availability_caveat(current, prior, material, anchor_season),
        "medical_inference_used": "false",
    }
    row.update(_usage_feature_row(usage_row, current_points, current_games))
    row.update(_recency_features(history, anchor_season))
    return row


def _usage_feature_row(
    usage_row: pd.Series | None,
    current_points: float,
    current_games: float,
) -> dict[str, Any]:
    if usage_row is None:
        return {
            "usage_feature_status": NOT_ENOUGH_INFORMATION,
            "current_carries": np.nan,
            "current_targets": np.nan,
            "current_receptions": np.nan,
            "current_touches": np.nan,
            "current_opportunities": np.nan,
            "current_rushing_yards": np.nan,
            "current_receiving_yards": np.nan,
            "current_rushing_first_downs": np.nan,
            "current_receiving_first_downs": np.nan,
            "current_touches_per_game": np.nan,
            "current_opportunities_per_game": np.nan,
            "current_yards_per_game": np.nan,
            "current_yards_per_opportunity": np.nan,
            "current_first_downs_per_opportunity": np.nan,
            "current_points_per_opportunity": np.nan,
            "usage_games_with_usage_row": np.nan,
            "usage_offense_pct": np.nan,
            "team_opportunity_share": np.nan,
            "red_zone_touches": np.nan,
            "inside_5_touches": np.nan,
        }
    carries = _series_number(usage_row, "carries")
    targets = _series_number(usage_row, "targets")
    receptions = _series_number(usage_row, "receptions")
    touches = _series_number(usage_row, "touches")
    opportunities = _series_number(usage_row, "opportunities")
    rush_yards = _series_number(usage_row, "rushing_yards")
    rec_yards = _series_number(usage_row, "receiving_yards")
    rush_fd = _series_number(usage_row, "rushing_first_downs")
    rec_fd = _series_number(usage_row, "receiving_first_downs")
    yards = _add_numbers(rush_yards, rec_yards)
    first_downs = _add_numbers(rush_fd, rec_fd)
    return {
        "usage_feature_status": "available",
        "current_carries": carries,
        "current_targets": targets,
        "current_receptions": receptions,
        "current_touches": touches,
        "current_opportunities": opportunities,
        "current_rushing_yards": rush_yards,
        "current_receiving_yards": rec_yards,
        "current_rushing_first_downs": rush_fd,
        "current_receiving_first_downs": rec_fd,
        "current_touches_per_game": _safe_divide(touches, current_games),
        "current_opportunities_per_game": _safe_divide(opportunities, current_games),
        "current_yards_per_game": _safe_divide(yards, current_games),
        "current_yards_per_opportunity": _safe_divide(yards, opportunities),
        "current_first_downs_per_opportunity": _safe_divide(first_downs, opportunities),
        "current_points_per_opportunity": _safe_divide(current_points, opportunities),
        "usage_games_with_usage_row": _series_number(usage_row, "games_with_usage_row"),
        "usage_offense_pct": _series_number(usage_row, "offense_pct"),
        "team_opportunity_share": _series_number(usage_row, "team_opportunity_share"),
        "red_zone_touches": _series_number(usage_row, "red_zone_touches"),
        "inside_5_touches": _series_number(usage_row, "inside_5_touches"),
    }


def _within_5y_target(
    *,
    season_index: dict[tuple[str, int], pd.Series],
    player_id: str,
    anchor_season: int,
    threshold: int,
    max_target_season: int,
) -> dict[str, Any]:
    target_seasons = list(range(anchor_season + 1, anchor_season + 6))
    if max(target_seasons) > max_target_season:
        return {
            "hit": NOT_ENOUGH_INFORMATION,
            "window_complete": False,
            "censoring_status": "right_censored_future_window",
        }
    targets = [season_index.get((player_id, season)) for season in target_seasons]
    if any(target is None for target in targets):
        return {
            "hit": NOT_ENOUGH_INFORMATION,
            "window_complete": False,
            "censoring_status": "missing_target_season",
        }
    finishes = [_series_number(target, "position_finish") for target in targets]
    if any(math.isnan(finish) for finish in finishes):
        return {
            "hit": NOT_ENOUGH_INFORMATION,
            "window_complete": False,
            "censoring_status": "missing_position_finish",
        }
    return {
        "hit": "hit" if min(finishes) <= threshold else "miss",
        "window_complete": True,
        "censoring_status": "complete",
    }


def _target_summary_rows(dataset: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for threshold in TARGET_THRESHOLDS:
        field_id = _field_id(threshold)
        target_col = f"{_target_prefix(threshold)}_hit"
        complete_col = f"{_target_prefix(threshold)}_window_complete"
        complete = dataset[
            (dataset[complete_col] == True)  # noqa: E712
            & dataset[target_col].isin(["hit", "miss"])
        ]
        positives = int((complete[target_col] == "hit").sum())
        rows.append(
            {
                "field_id": field_id,
                "threshold": threshold,
                "complete_rows": int(len(complete)),
                "positive_count": positives,
                "negative_count": int((complete[target_col] == "miss").sum()),
                "prevalence": round(positives / len(complete), 6) if len(complete) else "",
                "censored_or_missing_rows": int(len(dataset) - len(complete)),
                "complete_anchor_seasons": _join_ints(complete["anchor_season"].unique()),
                "display_only": "true",
                "diagnostic_only": "true",
                "model_use_allowed": "false",
            }
        )
    return rows


def _rolling_baseline_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    predictions: list[dict[str, Any]] = []
    for season in _validation_seasons(frame):
        train = frame[frame["anchor_season"] < season].copy()
        validation = frame[frame["anchor_season"] == season].copy()
        if not _fold_is_usable(train, validation):
            continue
        probability = _smoothed_rate(train["target"].astype(int).tolist())
        for row in validation.to_dict("records"):
            predictions.append(_prediction_row(row, probability, season))
    return pd.DataFrame(predictions)


def _rolling_bucket_predictions(
    frame: pd.DataFrame,
    threshold: int,
    feature_set: str,
) -> pd.DataFrame:
    predictions: list[dict[str, Any]] = []
    work = frame.copy()
    work["profile_bucket"] = work.apply(
        lambda row: _profile_bucket(row, threshold, feature_set),
        axis=1,
    )
    for season in _validation_seasons(work):
        train = work[work["anchor_season"] < season].copy()
        validation = work[work["anchor_season"] == season].copy()
        if not _fold_is_usable(train, validation):
            continue
        baseline = _smoothed_rate(train["target"].astype(int).tolist())
        bucket_rates = _bucket_rates(train, baseline)
        for row in validation.to_dict("records"):
            probability = bucket_rates.get(str(row["profile_bucket"]), baseline)
            predictions.append(_prediction_row(row, probability, season))
    return pd.DataFrame(predictions)


def _summarize_predictions(
    *,
    field_id: str,
    feature_set: str,
    frame: pd.DataFrame,
    predictions: pd.DataFrame,
    model_description: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if predictions.empty:
        metrics = _blocked_metric(field_id, feature_set, frame, "BLOCKED_NO_USABLE_FOLDS")
        return metrics, [], []
    predictions = predictions.copy()
    targets = predictions["target"].astype(int)
    probabilities = predictions["prediction"].astype(float)
    model_brier = _brier(probabilities, targets)
    baseline_predictions = _rolling_baseline_predictions(frame)
    baseline_brier = _brier(
        baseline_predictions["prediction"],
        baseline_predictions["target"],
    )
    calibration = _calibration_rows(
        field_id=field_id,
        feature_set=feature_set,
        predictions=probabilities.tolist(),
        targets=targets.tolist(),
    )
    calibration_quality = _calibration_quality(calibration)
    fold_summary = _fold_summary(predictions, baseline_predictions)
    validation_status = _validation_status(
        model_brier=model_brier,
        baseline_brier=baseline_brier,
        calibration_quality=calibration_quality,
        fold_win_rate=fold_summary["fold_win_rate"],
        feature_set=feature_set,
    )
    metrics = {
        "field_id": field_id,
        "feature_set": feature_set,
        "model_description": model_description,
        "complete_rows": int(len(frame)),
        "positive_count": int(frame["target"].sum()) if "target" in frame else "",
        "validation_rows": int(len(predictions)),
        "validation_positives": int(targets.sum()),
        "validation_anchor_seasons": _join_ints(predictions["validation_season"].unique()),
        "fold_count": fold_summary["fold_count"],
        "folds_beating_baseline": fold_summary["folds_beating_baseline"],
        "fold_win_rate": fold_summary["fold_win_rate"],
        "fold_stability_status": fold_summary["fold_stability_status"],
        "model_brier": round(model_brier, 6),
        "baseline_brier": round(baseline_brier, 6),
        "brier_delta_vs_baseline": round(baseline_brier - model_brier, 6),
        "weighted_calibration_abs_error": calibration_quality[
            "weighted_calibration_abs_error"
        ],
        "max_large_bucket_calibration_abs_error": calibration_quality[
            "max_large_bucket_calibration_abs_error"
        ],
        "calibration_status": calibration_quality["calibration_status"],
        "validation_status": validation_status,
        "blocked_inputs_used": "false",
        "display_only": "true",
        "diagnostic_only": "true",
        "model_use_allowed": "false",
        "app_wiring_allowed": "false",
    }
    return metrics, calibration, _error_slice_rows(field_id, feature_set, predictions)


def _blocked_metric(
    field_id: str,
    feature_set: str,
    frame: pd.DataFrame,
    status: str,
) -> dict[str, Any]:
    return {
        "field_id": field_id,
        "feature_set": feature_set,
        "model_description": "",
        "complete_rows": int(len(frame)),
        "positive_count": int(frame["target"].sum()) if "target" in frame else "",
        "validation_rows": 0,
        "validation_positives": 0,
        "validation_anchor_seasons": "",
        "fold_count": 0,
        "folds_beating_baseline": 0,
        "fold_win_rate": "",
        "fold_stability_status": "BLOCKED_NO_USABLE_FOLDS",
        "model_brier": "",
        "baseline_brier": "",
        "brier_delta_vs_baseline": "",
        "weighted_calibration_abs_error": "",
        "max_large_bucket_calibration_abs_error": "",
        "calibration_status": "",
        "validation_status": status,
        "blocked_inputs_used": "false",
        "display_only": "true",
        "diagnostic_only": "true",
        "model_use_allowed": "false",
        "app_wiring_allowed": "false",
    }


def _recommendation_rows(
    target_summary: list[dict[str, Any]],
    fold_metrics: list[dict[str, Any]],
    error_slices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metrics_by_field: dict[str, list[dict[str, Any]]] = {}
    for metric in fold_metrics:
        metrics_by_field.setdefault(str(metric["field_id"]), []).append(metric)
    best_by_field = {
        field_id: _best_non_baseline_metric(metrics)
        for field_id, metrics in metrics_by_field.items()
    }
    t12_best = best_by_field.get("RB_T12_WITHIN_5Y", {})
    t24_best = best_by_field.get("RB_T24_WITHIN_5Y", {})
    for summary in target_summary:
        field_id = str(summary["field_id"])
        threshold = int(summary["threshold"])
        best = best_by_field.get(field_id, {})
        slice_status = _slice_stability_status(field_id, str(best.get("feature_set")), error_slices)
        recommendation = _recommendation_status(best, slice_status, threshold, t12_best, t24_best)
        rows.append(
            {
                "field_id": field_id,
                "threshold": threshold,
                "best_feature_set": best.get("feature_set", ""),
                "best_model_brier": best.get("model_brier", ""),
                "best_baseline_brier": best.get("baseline_brier", ""),
                "best_brier_delta_vs_baseline": best.get("brier_delta_vs_baseline", ""),
                "best_weighted_calibration_abs_error": best.get(
                    "weighted_calibration_abs_error",
                    "",
                ),
                "best_max_large_bucket_calibration_abs_error": best.get(
                    "max_large_bucket_calibration_abs_error",
                    "",
                ),
                "best_fold_win_rate": best.get("fold_win_rate", ""),
                "slice_stability_status": slice_status,
                "recommendation_status": recommendation,
                "recommendation_notes": _recommendation_notes(
                    threshold,
                    recommendation,
                    best,
                    t12_best,
                    t24_best,
                    slice_status,
                ),
                "display_only": "true",
                "diagnostic_only": "true",
                "app_wiring_allowed": "false",
            }
        )
    return rows


def _profile_bucket(row: pd.Series, threshold: int, feature_set: str) -> str:
    if feature_set == "season_totals":
        finish = _series_number(row, "current_position_finish")
        points = _series_number(row, "current_fantasy_points")
        if math.isnan(finish):
            return "no_current_finish"
        if finish <= threshold:
            return "prior_threshold_hit"
        if finish <= threshold * 1.5:
            return "near_intermediate"
        if points >= 100:
            return "productive_depth"
        return "low_or_missing_production"
    if feature_set == "per_game_rates":
        ppg = _series_number(row, "current_points_per_game")
        oppg = _series_number(row, "current_opportunities_per_game")
        if math.isnan(ppg):
            return "missing_ppg"
        if ppg >= 11:
            return "high_ppg"
        if ppg >= 8 and not math.isnan(oppg) and oppg >= 12:
            return "solid_ppg_with_role"
        if ppg >= 6:
            return "depth_ppg"
        return "low_ppg"
    if feature_set == "per_opportunity_rates":
        points_per_opp = _series_number(row, "current_points_per_opportunity")
        yards_per_opp = _series_number(row, "current_yards_per_opportunity")
        if math.isnan(points_per_opp) and math.isnan(yards_per_opp):
            return "missing_efficiency"
        if points_per_opp >= 0.75 or yards_per_opp >= 6:
            return "high_efficiency"
        if points_per_opp >= 0.55 or yards_per_opp >= 4.5:
            return "solid_efficiency"
        return "low_efficiency"
    if feature_set == "role_availability":
        share = _series_number(row, "team_opportunity_share")
        games = _series_number(row, "current_games_played")
        red_zone = _series_number(row, "red_zone_touches")
        if math.isnan(share):
            return "missing_role"
        if share >= 0.45 and games >= 12:
            return "lead_role_available"
        if share >= 0.30 and red_zone >= 20:
            return "scoring_role"
        if share >= 0.20:
            return "rotation_role"
        return "limited_role"
    material_gap = _series_number(row, "seasons_since_last_materially_active")
    trailing_ppg = _series_number(row, "trailing_3y_weighted_points_per_game")
    missed = str(row.get("missed_prior_season_flag", NOT_ENOUGH_INFORMATION))
    limited = str(row.get("limited_recent_sample_flag", NOT_ENOUGH_INFORMATION))
    if missed == "true" or limited == "true" or (not math.isnan(material_gap) and material_gap > 0):
        return "limited_recent_or_material_gap"
    if not math.isnan(trailing_ppg) and trailing_ppg >= 10:
        return "strong_multi_year_ppg"
    if not math.isnan(trailing_ppg) and trailing_ppg >= 7:
        return "solid_multi_year_ppg"
    return "thin_multi_year_baseline"


def _bucket_rates(train: pd.DataFrame, baseline_probability: float) -> dict[str, float]:
    rates: dict[str, float] = {}
    shrink_weight = 5.0
    for bucket, group in train.groupby("profile_bucket"):
        positives = float(group["target"].sum())
        rows = float(len(group))
        rates[str(bucket)] = (positives + baseline_probability * shrink_weight) / (
            rows + shrink_weight
        )
    return rates


def _calibration_rows(
    *,
    field_id: str,
    feature_set: str,
    predictions: list[float],
    targets: list[int],
) -> list[dict[str, Any]]:
    bands = (
        ("0.00-0.10", 0.0, 0.10),
        ("0.10-0.20", 0.10, 0.20),
        ("0.20-0.35", 0.20, 0.35),
        ("0.35-0.50", 0.35, 0.50),
        ("0.50-0.70", 0.50, 0.70),
        ("0.70-1.00", 0.70, 1.01),
    )
    rows: list[dict[str, Any]] = []
    for label, low, high in bands:
        pairs = [
            (prediction, target)
            for prediction, target in zip(predictions, targets, strict=True)
            if low <= prediction < high
        ]
        if not pairs:
            continue
        rows.append(
            {
                "field_id": field_id,
                "feature_set": feature_set,
                "probability_band": label,
                "rows": len(pairs),
                "average_prediction": round(
                    sum(prediction for prediction, _target in pairs) / len(pairs),
                    6,
                ),
                "observed_rate": round(
                    sum(target for _prediction, target in pairs) / len(pairs),
                    6,
                ),
                "positive_count": sum(target for _prediction, target in pairs),
            }
        )
    return rows


def _calibration_quality(calibration_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not calibration_rows:
        return {
            "weighted_calibration_abs_error": "",
            "max_large_bucket_calibration_abs_error": "",
            "calibration_status": "BLOCKED_NO_CALIBRATION_BUCKETS",
        }
    total_rows = sum(int(row["rows"]) for row in calibration_rows)
    weighted_error = sum(
        abs(float(row["average_prediction"]) - float(row["observed_rate"]))
        * int(row["rows"])
        for row in calibration_rows
    ) / total_rows
    large_errors = [
        abs(float(row["average_prediction"]) - float(row["observed_rate"]))
        for row in calibration_rows
        if int(row["rows"]) >= MIN_ROWS_FOR_LARGE_BUCKET_CALIBRATION
    ]
    max_large_error = max(large_errors) if large_errors else 0.0
    status = (
        "PASS_CALIBRATION_REVIEW"
        if weighted_error <= MAX_WEIGHTED_CALIBRATION_ABS_ERROR
        and max_large_error <= MAX_LARGE_BUCKET_CALIBRATION_ABS_ERROR
        else "BLOCKED_CALIBRATION_WEAK"
    )
    return {
        "weighted_calibration_abs_error": round(weighted_error, 6),
        "max_large_bucket_calibration_abs_error": round(max_large_error, 6),
        "calibration_status": status,
    }


def _fold_summary(predictions: pd.DataFrame, baseline_predictions: pd.DataFrame) -> dict[str, Any]:
    if predictions.empty:
        return {
            "fold_count": 0,
            "folds_beating_baseline": 0,
            "fold_win_rate": "",
            "fold_stability_status": "BLOCKED_NO_FOLDS",
        }
    folds = []
    for season, group in predictions.groupby("validation_season"):
        baseline = baseline_predictions[baseline_predictions["validation_season"] == season]
        if group.empty or baseline.empty:
            continue
        model_brier = _brier(group["prediction"], group["target"])
        baseline_brier = _brier(baseline["prediction"], baseline["target"])
        folds.append(model_brier <= baseline_brier)
    fold_count = len(folds)
    wins = sum(1 for value in folds if value)
    win_rate = wins / fold_count if fold_count else 0.0
    return {
        "fold_count": fold_count,
        "folds_beating_baseline": wins,
        "fold_win_rate": round(win_rate, 6),
        "fold_stability_status": (
            "PASS_FOLD_STABILITY_REVIEW"
            if fold_count >= 2 and win_rate >= 0.5
            else "BLOCKED_FOLD_STABILITY_WEAK"
        ),
    }


def _error_slice_rows(
    field_id: str,
    feature_set: str,
    predictions: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for column in ("missed_prior_season_flag", "limited_recent_sample_flag"):
        if column not in predictions.columns:
            continue
        for value, group in predictions.groupby(column, dropna=False):
            if group.empty:
                continue
            rows.append(
                {
                    "field_id": field_id,
                    "feature_set": feature_set,
                    "slice": column,
                    "slice_value": str(value),
                    "rows": int(len(group)),
                    "positive_count": int(group["target"].sum()),
                    "observed_rate": round(float(group["target"].mean()), 6),
                    "average_prediction": round(float(group["prediction"].mean()), 6),
                    "brier": round(_brier(group["prediction"], group["target"]), 6),
                    "absolute_calibration_error": round(
                        abs(float(group["prediction"].mean()) - float(group["target"].mean())),
                        6,
                    ),
                }
            )
    return rows


def _validation_status(
    *,
    model_brier: float,
    baseline_brier: float,
    calibration_quality: dict[str, Any],
    fold_win_rate: Any,
    feature_set: str,
) -> str:
    if feature_set == "empirical_baseline":
        return "BASELINE_REFERENCE"
    if model_brier > baseline_brier:
        return "BLOCKED_VALIDATION_WEAK"
    if calibration_quality["calibration_status"] != "PASS_CALIBRATION_REVIEW":
        return "BLOCKED_CALIBRATION_WEAK"
    if _safe_float(fold_win_rate) < 0.5:
        return "BLOCKED_FOLD_STABILITY_WEAK"
    return "PASS_DIAGNOSTIC_VALIDATION"


def _recommendation_status(
    best: dict[str, Any],
    slice_status: str,
    threshold: int,
    t12_best: dict[str, Any],
    t24_best: dict[str, Any],
) -> str:
    if best.get("validation_status") != "PASS_DIAGNOSTIC_VALIDATION":
        return "keep_blocked"
    if slice_status != "PASS_SLICE_REVIEW":
        return "test_only"
    if threshold in (15, 18, 20):
        if not _intermediate_clearly_useful(best, t12_best, t24_best):
            return "test_only"
        if (
            _safe_float(best.get("weighted_calibration_abs_error")) <= 0.08
            and _safe_float(best.get("max_large_bucket_calibration_abs_error")) <= 0.15
            and _safe_float(best.get("fold_win_rate")) >= 0.6
        ):
            return "safe_for_display_candidate"
    return "test_only"


def _intermediate_clearly_useful(
    best: dict[str, Any],
    t12_best: dict[str, Any],
    t24_best: dict[str, Any],
) -> bool:
    if not t12_best or not t24_best:
        return False
    calibration = _safe_float(best.get("weighted_calibration_abs_error"))
    t12_calibration = _safe_float(t12_best.get("weighted_calibration_abs_error"))
    t24_calibration = _safe_float(t24_best.get("weighted_calibration_abs_error"))
    brier_delta = _safe_float(best.get("brier_delta_vs_baseline"))
    return (
        brier_delta > 0
        and calibration <= t12_calibration + 0.02
        and calibration <= t24_calibration + 0.03
    )


def _slice_stability_status(
    field_id: str,
    feature_set: str,
    error_slices: list[dict[str, Any]],
) -> str:
    true_slices = [
        row
        for row in error_slices
        if row.get("field_id") == field_id
        and row.get("feature_set") == feature_set
        and row.get("slice_value") == "true"
    ]
    if not true_slices:
        return "NO_TRUE_SLICE_ROWS"
    unstable = [
        row
        for row in true_slices
        if int(row.get("rows", 0)) < 10
        or _safe_float(row.get("absolute_calibration_error")) > 0.30
    ]
    return "BLOCKED_SLICE_TOO_SPARSE_OR_UNSTABLE" if unstable else "PASS_SLICE_REVIEW"


def _recommendation_notes(
    threshold: int,
    recommendation: str,
    best: dict[str, Any],
    t12_best: dict[str, Any],
    t24_best: dict[str, Any],
    slice_status: str,
) -> str:
    if recommendation == "keep_blocked":
        return "Calibration or Brier validation did not pass; keep as Not enough information."
    if slice_status != "PASS_SLICE_REVIEW":
        return (
            "Core validation passed, but missed-prior-season or limited-sample slices "
            "remain too sparse/unstable for display promotion."
        )
    if threshold in (15, 18, 20) and not _intermediate_clearly_useful(best, t12_best, t24_best):
        return "Intermediate threshold did not clearly improve over T12/T24 calibration."
    if recommendation == "safe_for_display_candidate":
        return "Review-only candidate: passes strict Brier, calibration, fold, and slice checks."
    return "Useful diagnostic signal only; keep out of app until separately approved."


def _best_non_baseline_metric(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in metrics if row.get("feature_set") != "empirical_baseline"]
    if not candidates:
        return {}
    return sorted(candidates, key=_metric_rank)[0]


def _metric_rank(metric: dict[str, Any]) -> tuple[int, float, float]:
    status_rank = 0 if metric.get("validation_status") == "PASS_DIAGNOSTIC_VALIDATION" else 1
    calibration = _safe_float(metric.get("weighted_calibration_abs_error"))
    brier = _safe_float(metric.get("model_brier"))
    return (status_rank, calibration, brier)


def _recency_features(history: pd.DataFrame, anchor_season: int) -> dict[str, float]:
    return {
        "trailing_2y_weighted_points": _weighted_history_value(
            history,
            anchor_season,
            "fantasy_points",
            years=2,
        ),
        "trailing_2y_weighted_points_per_game": _weighted_points_per_game(
            history,
            anchor_season,
            years=2,
        ),
        "trailing_2y_weighted_games": _weighted_history_value(
            history,
            anchor_season,
            "games_played",
            years=2,
        ),
        "trailing_3y_weighted_points": _weighted_history_value(
            history,
            anchor_season,
            "fantasy_points",
            years=3,
        ),
        "trailing_3y_weighted_points_per_game": _weighted_points_per_game(
            history,
            anchor_season,
            years=3,
        ),
        "trailing_3y_weighted_games": _weighted_history_value(
            history,
            anchor_season,
            "games_played",
            years=3,
        ),
    }


def _last_materially_active(history: pd.DataFrame, anchor_season: int) -> dict[str, Any]:
    if history.empty:
        return {}
    eligible = history[history["season"] <= anchor_season].copy()
    eligible = eligible[eligible.apply(_is_materially_active, axis=1)]
    if eligible.empty:
        return {}
    row = eligible.sort_values("season").iloc[-1]
    return {
        "season": int(row["season"]),
        "fantasy_points": _series_number(row, "fantasy_points"),
        "position_finish": _series_number(row, "position_finish"),
        "games_played": _series_number(row, "games_played"),
    }


def _is_materially_active(row: pd.Series) -> bool:
    games = _series_number(row, "games_played")
    points = _series_number(row, "fantasy_points")
    finish = _series_number(row, "position_finish")
    return (
        (not math.isnan(games) and games >= MATERIAL_ACTIVE_MIN_GAMES)
        or (not math.isnan(points) and points >= MATERIAL_ACTIVE_MIN_POINTS)
        or (not math.isnan(finish) and finish <= 36)
    )


def _missed_prior_season_flag(prior: pd.Series | None, experience: float) -> str:
    if math.isnan(experience) or experience <= 1:
        return NOT_ENOUGH_INFORMATION
    if prior is None:
        return "true"
    games = _series_number(prior, "games_played")
    if math.isnan(games):
        return NOT_ENOUGH_INFORMATION
    return "true" if games <= 0 else "false"


def _limited_recent_sample_flag(
    current: pd.Series | None,
    prior: pd.Series | None,
    material: dict[str, Any],
    anchor_season: int,
) -> str:
    current_games = _series_number(current, "games_played")
    prior_games = _series_number(prior, "games_played")
    if not material:
        return "true"
    if anchor_season - int(material["season"]) > 0:
        return "true"
    if not math.isnan(current_games) and current_games < LIMITED_RECENT_SAMPLE_GAMES:
        return "true"
    recent_games = _add_numbers(current_games, prior_games)
    if not math.isnan(recent_games) and recent_games < 12:
        return "true"
    return "false"


def _availability_caveat(
    current: pd.Series | None,
    prior: pd.Series | None,
    material: dict[str, Any],
    anchor_season: int,
) -> str:
    if current is None:
        return NOT_ENOUGH_INFORMATION
    limited = _limited_recent_sample_flag(current, prior, material, anchor_season)
    if limited == "true":
        return "limited_recent_factual_sample_no_medical_inference"
    return "factual_games_context_only_no_medical_inference"


def _weighted_history_value(
    history: pd.DataFrame,
    anchor_season: int,
    column: str,
    *,
    years: int,
) -> float:
    recent = _recent_window(history, anchor_season, years)
    if recent.empty or column not in recent.columns:
        return np.nan
    values = pd.to_numeric(recent[column], errors="coerce")
    weights = np.arange(1, len(recent) + 1, dtype=float)
    valid = values.notna()
    if not valid.any():
        return np.nan
    return float(np.average(values[valid], weights=weights[valid]))


def _weighted_points_per_game(history: pd.DataFrame, anchor_season: int, *, years: int) -> float:
    recent = _recent_window(history, anchor_season, years)
    if recent.empty:
        return np.nan
    values = pd.to_numeric(recent["fantasy_points"], errors="coerce")
    games = pd.to_numeric(recent["games_played"], errors="coerce")
    ppg = values / games.replace(0, np.nan)
    weights = np.arange(1, len(recent) + 1, dtype=float)
    valid = ppg.notna()
    if not valid.any():
        return np.nan
    return float(np.average(ppg[valid], weights=weights[valid]))


def _prior_season_row(history: pd.DataFrame, anchor_season: int) -> pd.Series | None:
    if history.empty:
        return None
    prior = history[history["season"] == anchor_season - 1]
    if prior.empty:
        return None
    return prior.iloc[0]


def _recent_window(history: pd.DataFrame, anchor_season: int, years: int) -> pd.DataFrame:
    if history.empty:
        return history
    start = anchor_season - years + 1
    return history[(history["season"] >= start) & (history["season"] <= anchor_season)].copy()


def _first_observed_season(history: pd.DataFrame) -> int | None:
    if history.empty:
        return None
    return int(history["season"].min())


def _experience_year_number(history: pd.DataFrame, anchor_season: int) -> float:
    if history.empty:
        return np.nan
    return float((history["season"] <= anchor_season).sum())


def _season_index(seasons: pd.DataFrame) -> dict[tuple[str, int], pd.Series]:
    return {
        (str(row.player_id), int(row.season)): seasons.iloc[index]
        for index, row in enumerate(seasons.itertuples(index=False))
    }


def _usage_index(usage: pd.DataFrame) -> dict[tuple[str, int], pd.Series]:
    if usage.empty:
        return {}
    return {
        (str(row.player_id), int(row.season)): usage.iloc[index]
        for index, row in enumerate(usage.itertuples(index=False))
    }


def _validation_seasons(frame: pd.DataFrame) -> list[int]:
    seasons = sorted(int(season) for season in frame["anchor_season"].dropna().unique())
    return seasons[1:]


def _fold_is_usable(train: pd.DataFrame, validation: pd.DataFrame) -> bool:
    if len(train) < MIN_TRAIN_ROWS or len(validation) < MIN_VALIDATION_ROWS:
        return False
    positives = int(train["target"].sum())
    negatives = int(len(train) - positives)
    return positives >= MIN_TRAIN_POSITIVES and negatives >= MIN_TRAIN_POSITIVES


def _prediction_row(
    row: dict[str, Any],
    probability: float,
    validation_season: int,
) -> dict[str, Any]:
    return {
        "player_id": str(row.get("player_id", "")),
        "player_name": str(row.get("player_name", "")),
        "anchor_season": int(row.get("anchor_season", validation_season)),
        "validation_season": validation_season,
        "target": int(row.get("target", 0)),
        "prediction": max(0.001, min(0.999, float(probability))),
        "missed_prior_season_flag": row.get(
            "missed_prior_season_flag",
            NOT_ENOUGH_INFORMATION,
        ),
        "limited_recent_sample_flag": row.get(
            "limited_recent_sample_flag",
            NOT_ENOUGH_INFORMATION,
        ),
    }


def _target_prefix(threshold: int) -> str:
    return f"rb_t{threshold}_within_5y"


def _field_id(threshold: int) -> str:
    return f"RB_T{threshold}_WITHIN_5Y"


def _safe_divide(numerator: float, denominator: float) -> float:
    if math.isnan(numerator) or math.isnan(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator


def _safe_divide_series(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def _series_number(row: pd.Series | None, column: str) -> float:
    if row is None:
        return np.nan
    try:
        value = row.get(column, np.nan)
    except AttributeError:
        value = getattr(row, column, np.nan)
    converted = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return float(converted) if pd.notna(converted) else np.nan


def _add_numbers(*values: float) -> float:
    valid = [value for value in values if not math.isnan(value)]
    return float(sum(valid)) if valid else np.nan


def _flag_to_number(flag: str) -> float:
    if flag == "true":
        return 1.0
    if flag == "false":
        return 0.0
    return np.nan


def _smoothed_rate(values: list[int]) -> float:
    return (sum(values) + 1.0) / (len(values) + 2.0)


def _brier(probabilities: pd.Series | list[float], targets: pd.Series | list[int]) -> float:
    probs = pd.to_numeric(pd.Series(probabilities), errors="coerce")
    actuals = pd.to_numeric(pd.Series(targets), errors="coerce")
    valid = probs.notna() & actuals.notna()
    if not valid.any():
        return math.inf
    return float(((probs[valid] - actuals[valid]) ** 2).mean())


def _safe_float(value: Any) -> float:
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return math.inf
    return converted if not math.isnan(converted) else math.inf


def _join_ints(values: Any) -> str:
    converted = sorted({int(value) for value in pd.Series(values).dropna().tolist()})
    return "|".join(str(value) for value in converted)


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _blocked_source_status(path: Path) -> str:
    normalized = str(path).lower().replace("\\", "/")
    return "blocked" if any(token in normalized for token in BLOCKED_SOURCE_TOKENS) else "pass"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _manifest_rows(
    *,
    paths: dict[str, Path],
    outputs: dict[str, Path],
    dataset_rows: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in validate_source_paths(paths):
        rows.append(
            {
                "artifact": f"source_{source['source_name']}",
                "path": source["path"],
                "rows": "",
                "sha256": source["sha256"],
                "display_only": "true",
                "diagnostic_only": "true",
                "model_use_allowed": "false",
                "app_wiring_allowed": "false",
                "blocked_source_scan": source["blocked_source_scan"],
                "notes": "review-only historical veteran NFL source",
            }
        )
    for name, path in outputs.items():
        rows.append(
            {
                "artifact": name,
                "path": str(path),
                "rows": dataset_rows if name == "diagnostic_dataset" else "",
                "sha256": _sha256(path) if path.exists() else "",
                "display_only": "true",
                "diagnostic_only": "true",
                "model_use_allowed": "false",
                "app_wiring_allowed": "false",
                "blocked_source_scan": "pass",
                "notes": "offline RB intermediate 5Y diagnostic artifact",
            }
        )
    rows.append(
        {
            "artifact": "run_metadata",
            "path": "",
            "rows": dataset_rows,
            "sha256": "",
            "display_only": "true",
            "diagnostic_only": "true",
            "model_use_allowed": "false",
            "app_wiring_allowed": "false",
            "blocked_source_scan": "pass",
            "notes": f"created_at={datetime.now(UTC).isoformat()}",
        }
    )
    return rows
