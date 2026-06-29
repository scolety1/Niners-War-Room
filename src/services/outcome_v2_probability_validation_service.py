from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

NOT_ENOUGH_INFORMATION = "Not enough information"
SHARED_LABEL_ROOT = Path(r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels")
SHARED_VALIDATION_ROOT = Path(r"C:\NWR_SHARED_DATA\outcome_v2_horizon\validation")
ANCHOR_LABEL_PATH = SHARED_LABEL_ROOT / "outcome_v2_anchor_horizon_labels.csv"
SEASON_LABEL_PATH = SHARED_LABEL_ROOT / "outcome_v2_season_outcome_labels.csv"

POSITION_THRESHOLDS: dict[str, tuple[int, ...]] = {
    "QB": (6, 12),
    "RB": (6, 12, 24, 36),
    "WR": (6, 12, 24, 36),
    "TE": (6, 12),
}
HORIZON_HOLDOUTS: dict[str, tuple[int, ...]] = {
    "this_year": (2022, 2023),
    "next_year": (2021, 2022),
    "within_5y": (2018, 2019),
}
MIN_COMPLETE_LABELS = 100
MIN_POSITIVES = 20
MIN_COMPLETE_ANCHOR_SEASONS = 5
MAX_WEIGHTED_CALIBRATION_ABS_ERROR = 0.15
MAX_LARGE_BUCKET_CALIBRATION_ABS_ERROR = 0.30
MIN_ROWS_FOR_LARGE_BUCKET_CALIBRATION = 20

RESULTS_FILENAME = "outcome_v2_probability_validation_results.csv"
CALIBRATION_FILENAME = "outcome_v2_probability_calibration_buckets.csv"
MODEL_BUCKETS_FILENAME = "outcome_v2_probability_model_bucket_rates.csv"
MANIFEST_FILENAME = "outcome_v2_probability_validation_manifest.csv"


@dataclass(frozen=True)
class OutcomeV2ValidationResult:
    output_root: Path
    validation_results_path: Path
    calibration_path: Path
    model_buckets_path: Path
    manifest_path: Path
    passed_fields: int
    blocked_fields: int


def build_validation_feature_frame(
    anchor_labels_path: str | Path = ANCHOR_LABEL_PATH,
    season_labels_path: str | Path = SEASON_LABEL_PATH,
) -> pd.DataFrame:
    anchors = pd.read_csv(anchor_labels_path)
    season_labels = pd.read_csv(season_labels_path)
    features = season_labels.rename(
        columns={
            "season": "anchor_season",
            "position_finish": "anchor_position_finish",
            "fantasy_points": "anchor_fantasy_points",
            "games_played": "anchor_games_played",
        },
    )[
        [
            "player_id",
            "anchor_season",
            "anchor_position_finish",
            "anchor_fantasy_points",
            "anchor_games_played",
        ]
    ]
    frame = anchors.merge(features, on=["player_id", "anchor_season"], how="left")
    frame["anchor_season"] = pd.to_numeric(frame["anchor_season"], errors="coerce")
    return frame


def field_feasibility_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for position, thresholds in POSITION_THRESHOLDS.items():
        position_frame = frame[frame["position"] == position]
        for horizon in ("this_year", "next_year", "within_5y"):
            complete_col = f"{horizon}_window_complete"
            for threshold in thresholds:
                field_col = f"{horizon}_top_{threshold}_hit"
                complete = _complete_labels(position_frame, complete_col, field_col)
                seasons = sorted(
                    int(value)
                    for value in complete["anchor_season"].dropna().unique()
                )
                positives = int((complete[field_col] == "hit").sum())
                status, reason = _feasibility_status(horizon, len(complete), positives, seasons)
                rows.append(
                    {
                        "field_id": _field_id(position, threshold, horizon),
                        "position": position,
                        "threshold": threshold,
                        "horizon": horizon,
                        "complete_label_rows": len(complete),
                        "positive_label_count": positives,
                        "negative_label_count": int((complete[field_col] == "miss").sum()),
                        "censored_or_missing_rows": int(
                            (position_frame[complete_col] != True).sum()  # noqa: E712
                        ),
                        "anchor_seasons": "|".join(str(season) for season in seasons),
                        "complete_anchor_season_count": len(seasons),
                        "feasibility_status": status,
                        "reason": reason,
                    }
                )
    return rows


def validate_probabilities(
    anchor_labels_path: str | Path = ANCHOR_LABEL_PATH,
    season_labels_path: str | Path = SEASON_LABEL_PATH,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    frame = build_validation_feature_frame(anchor_labels_path, season_labels_path)
    feasibility = field_feasibility_rows(frame)
    results: list[dict[str, Any]] = []
    calibration_rows: list[dict[str, Any]] = []
    model_bucket_rows: list[dict[str, Any]] = []

    for row in feasibility:
        if row["feasibility_status"] != "VALIDATION_FEASIBLE":
            results.append(_blocked_result(row, "BLOCKED_FEASIBILITY_GATE"))
            continue
        field_result, field_calibration, bucket_rows = _validate_field(frame, row)
        results.append(field_result)
        calibration_rows.extend(field_calibration)
        model_bucket_rows.extend(bucket_rows)

    return results, calibration_rows, model_bucket_rows


def write_validation_artifacts(
    output_root: str | Path = SHARED_VALIDATION_ROOT,
    anchor_labels_path: str | Path = ANCHOR_LABEL_PATH,
    season_labels_path: str | Path = SEASON_LABEL_PATH,
) -> OutcomeV2ValidationResult:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    results, calibration_rows, model_bucket_rows = validate_probabilities(
        anchor_labels_path,
        season_labels_path,
    )

    validation_results_path = output / RESULTS_FILENAME
    calibration_path = output / CALIBRATION_FILENAME
    model_buckets_path = output / MODEL_BUCKETS_FILENAME
    manifest_path = output / MANIFEST_FILENAME

    _write_csv(validation_results_path, _validation_header(), results)
    _write_csv(calibration_path, _calibration_header(), calibration_rows)
    _write_csv(model_buckets_path, _bucket_header(), model_bucket_rows)
    passed_fields = sum(
        1 for row in results if row["validation_status"] == "PASS_APP_DISPLAY_VALIDATION"
    )
    blocked_fields = len(results) - passed_fields
    _write_csv(
        manifest_path,
        (
            "artifact",
            "path",
            "rows",
            "display_only",
            "model_use_allowed",
            "training_allowed",
            "blocked_inputs_used",
            "notes",
        ),
        [
            {
                "artifact": "validation_results",
                "path": str(validation_results_path),
                "rows": len(results),
                "display_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "blocked_inputs_used": "false",
                "notes": "held-out empirical validation, no market/adp/cfbd inputs",
            },
            {
                "artifact": "calibration_buckets",
                "path": str(calibration_path),
                "rows": len(calibration_rows),
                "display_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "blocked_inputs_used": "false",
                "notes": "calibration by probability band",
            },
            {
                "artifact": "model_bucket_rates",
                "path": str(model_buckets_path),
                "rows": len(model_bucket_rows),
                "display_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
                "blocked_inputs_used": "false",
                "notes": "shrunk train rates by prior finish bucket",
            },
        ],
    )
    return OutcomeV2ValidationResult(
        output_root=output,
        validation_results_path=validation_results_path,
        calibration_path=calibration_path,
        model_buckets_path=model_buckets_path,
        manifest_path=manifest_path,
        passed_fields=passed_fields,
        blocked_fields=blocked_fields,
    )


def _validate_field(
    frame: pd.DataFrame,
    feasibility_row: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    position = str(feasibility_row["position"])
    threshold = int(feasibility_row["threshold"])
    horizon = str(feasibility_row["horizon"])
    field_col = f"{horizon}_top_{threshold}_hit"
    complete_col = f"{horizon}_window_complete"
    holdout_seasons = HORIZON_HOLDOUTS[horizon]
    position_frame = frame[frame["position"] == position]
    complete = _complete_labels(position_frame, complete_col, field_col).copy()
    complete["target"] = (complete[field_col] == "hit").astype(int)
    complete["profile_bucket"] = complete.apply(
        lambda row: _profile_bucket(row, threshold),
        axis=1,
    )
    train = complete[~complete["anchor_season"].isin(holdout_seasons)].copy()
    validation = complete[complete["anchor_season"].isin(holdout_seasons)].copy()
    if train.empty or validation.empty:
        result = _blocked_result(feasibility_row, "BLOCKED_VALIDATION_SPLIT")
        return result, [], []

    baseline_probability = _smoothed_rate(train["target"].tolist())
    bucket_rates = _bucket_rates(train, baseline_probability)
    probabilities = [
        bucket_rates.get(str(row.profile_bucket), baseline_probability)
        for row in validation.itertuples(index=False)
    ]
    targets = validation["target"].astype(int).tolist()
    model_brier = _brier(probabilities, targets)
    baseline_brier = _brier([baseline_probability] * len(targets), targets)
    brier_delta = baseline_brier - model_brier
    calibration = _calibration_rows(
        field_id=str(feasibility_row["field_id"]),
        probabilities=probabilities,
        targets=targets,
    )
    calibration_quality = _calibration_quality(calibration)
    validation_status, notes = _validation_status(
        model_brier=model_brier,
        baseline_brier=baseline_brier,
        calibration_quality=calibration_quality,
    )
    result = {
        **feasibility_row,
        "train_rows": len(train),
        "train_positives": int(train["target"].sum()),
        "validation_rows": len(validation),
        "validation_positives": int(validation["target"].sum()),
        "train_anchor_seasons": "|".join(
            str(int(season)) for season in sorted(train["anchor_season"].unique())
        ),
        "validation_anchor_seasons": "|".join(
            str(int(season)) for season in sorted(validation["anchor_season"].unique())
        ),
        "baseline_probability": round(baseline_probability, 6),
        "model_brier": round(model_brier, 6),
        "baseline_brier": round(baseline_brier, 6),
        "brier_delta_vs_baseline": round(brier_delta, 6),
        "weighted_calibration_abs_error": calibration_quality[
            "weighted_calibration_abs_error"
        ],
        "max_large_bucket_calibration_abs_error": calibration_quality[
            "max_large_bucket_calibration_abs_error"
        ],
        "calibration_status": calibration_quality["calibration_status"],
        "validation_status": validation_status,
        "display_eligible": str(validation_status == "PASS_APP_DISPLAY_VALIDATION").lower(),
        "blocked_inputs_used": "false",
        "model_description": "shrunk empirical prior-finish bucket model",
        "notes": notes,
    }
    bucket_rows = [
        {
            "field_id": feasibility_row["field_id"],
            "position": position,
            "threshold": threshold,
            "horizon": horizon,
            "profile_bucket": bucket,
            "train_rows": int((train["profile_bucket"] == bucket).sum()),
            "train_positives": int(train[train["profile_bucket"] == bucket]["target"].sum()),
            "probability": round(probability, 6),
            "baseline_probability": round(baseline_probability, 6),
        }
        for bucket, probability in sorted(bucket_rates.items())
    ]
    return result, calibration, bucket_rows


def _blocked_result(row: dict[str, Any], validation_status: str) -> dict[str, Any]:
    return {
        **row,
        "train_rows": 0,
        "train_positives": 0,
        "validation_rows": 0,
        "validation_positives": 0,
        "train_anchor_seasons": "",
        "validation_anchor_seasons": "",
        "baseline_probability": "",
        "model_brier": "",
        "baseline_brier": "",
        "brier_delta_vs_baseline": "",
        "weighted_calibration_abs_error": "",
        "max_large_bucket_calibration_abs_error": "",
        "calibration_status": "",
        "validation_status": validation_status,
        "display_eligible": "false",
        "blocked_inputs_used": "false",
        "model_description": "",
        "notes": str(row.get("reason", "")),
    }


def _feasibility_status(
    horizon: str,
    complete_rows: int,
    positives: int,
    seasons: list[int],
) -> tuple[str, str]:
    if complete_rows < MIN_COMPLETE_LABELS:
        return "BLOCKED_INSUFFICIENT_COMPLETE_LABELS", "fewer than 100 complete labels"
    if positives < MIN_POSITIVES:
        return "BLOCKED_INSUFFICIENT_POSITIVES", "fewer than 20 positive labels"
    if len(seasons) < MIN_COMPLETE_ANCHOR_SEASONS:
        return "BLOCKED_INSUFFICIENT_SEASONS", "fewer than five anchor seasons"
    return "VALIDATION_FEASIBLE", "sufficient complete labels for validation"


def _complete_labels(frame: pd.DataFrame, complete_col: str, field_col: str) -> pd.DataFrame:
    return frame[(frame[complete_col] == True) & (frame[field_col].isin(["hit", "miss"]))].copy()  # noqa: E712


def _profile_bucket(row: pd.Series, threshold: int) -> str:
    finish = pd.to_numeric(row.get("anchor_position_finish"), errors="coerce")
    points = pd.to_numeric(row.get("anchor_fantasy_points"), errors="coerce")
    games = pd.to_numeric(row.get("anchor_games_played"), errors="coerce")
    if pd.isna(finish):
        if pd.isna(points) or float(points) <= 0:
            return "missing_or_no_prior_production"
        return "missing_finish_has_points"
    finish_value = float(finish)
    if finish_value <= threshold:
        return "prior_threshold_hit"
    if finish_value <= threshold * 2:
        return "near_threshold"
    if finish_value <= threshold * 3:
        return "depth_relevant"
    if not pd.isna(games) and float(games) >= 8 and not pd.isna(points) and float(points) > 0:
        return "active_low_finish"
    return "limited_or_inactive"


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


def _smoothed_rate(values: list[int]) -> float:
    return (sum(values) + 1.0) / (len(values) + 2.0)


def _brier(probabilities: list[float], targets: list[int]) -> float:
    squared_errors = [
        (probability - target) ** 2
        for probability, target in zip(probabilities, targets, strict=True)
    ]
    return sum(squared_errors) / len(targets)


def _validation_status(
    *,
    model_brier: float,
    baseline_brier: float,
    calibration_quality: dict[str, Any],
) -> tuple[str, str]:
    if model_brier > baseline_brier:
        return (
            "BLOCKED_VALIDATION_WEAK",
            "held-out binned empirical model underperforms prevalence",
        )
    if calibration_quality["calibration_status"] != "PASS_CALIBRATION_REVIEW":
        return (
            "BLOCKED_CALIBRATION_WEAK",
            "held-out binned empirical model beats prevalence but has weak calibration",
        )
    return (
        "PASS_APP_DISPLAY_VALIDATION",
        "held-out binned empirical model beats or matches prevalence with acceptable calibration",
    )


def _calibration_rows(
    *,
    field_id: str,
    probabilities: list[float],
    targets: list[int],
) -> list[dict[str, Any]]:
    bands = [
        ("0.00-0.05", 0.0, 0.05),
        ("0.05-0.10", 0.05, 0.10),
        ("0.10-0.20", 0.10, 0.20),
        ("0.20-0.35", 0.20, 0.35),
        ("0.35-1.00", 0.35, 1.01),
    ]
    rows: list[dict[str, Any]] = []
    for label, low, high in bands:
        pairs = [
            (probability, target)
            for probability, target in zip(probabilities, targets, strict=True)
            if low <= probability < high
        ]
        if not pairs:
            continue
        rows.append(
            {
                "field_id": field_id,
                "probability_band": label,
                "rows": len(pairs),
                "average_prediction": round(
                    sum(probability for probability, _ in pairs) / len(pairs),
                    6,
                ),
                "observed_rate": round(sum(target for _, target in pairs) / len(pairs), 6),
                "positive_count": sum(target for _, target in pairs),
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
    large_bucket_errors = [
        abs(float(row["average_prediction"]) - float(row["observed_rate"]))
        for row in calibration_rows
        if int(row["rows"]) >= MIN_ROWS_FOR_LARGE_BUCKET_CALIBRATION
    ]
    max_large_bucket_error = max(large_bucket_errors) if large_bucket_errors else 0.0
    calibration_status = (
        "PASS_CALIBRATION_REVIEW"
        if weighted_error <= MAX_WEIGHTED_CALIBRATION_ABS_ERROR
        and max_large_bucket_error <= MAX_LARGE_BUCKET_CALIBRATION_ABS_ERROR
        else "BLOCKED_CALIBRATION_WEAK"
    )
    return {
        "weighted_calibration_abs_error": round(weighted_error, 6),
        "max_large_bucket_calibration_abs_error": round(max_large_bucket_error, 6),
        "calibration_status": calibration_status,
    }


def _field_id(position: str, threshold: int, horizon: str) -> str:
    return f"{position}_T{threshold}_{horizon.upper()}"


def _validation_header() -> tuple[str, ...]:
    return (
        "field_id",
        "position",
        "threshold",
        "horizon",
        "complete_label_rows",
        "positive_label_count",
        "negative_label_count",
        "censored_or_missing_rows",
        "anchor_seasons",
        "complete_anchor_season_count",
        "feasibility_status",
        "reason",
        "train_rows",
        "train_positives",
        "validation_rows",
        "validation_positives",
        "train_anchor_seasons",
        "validation_anchor_seasons",
        "baseline_probability",
        "model_brier",
        "baseline_brier",
        "brier_delta_vs_baseline",
        "weighted_calibration_abs_error",
        "max_large_bucket_calibration_abs_error",
        "calibration_status",
        "validation_status",
        "display_eligible",
        "blocked_inputs_used",
        "model_description",
        "notes",
    )


def _calibration_header() -> tuple[str, ...]:
    return (
        "field_id",
        "probability_band",
        "rows",
        "average_prediction",
        "observed_rate",
        "positive_count",
    )


def _bucket_header() -> tuple[str, ...]:
    return (
        "field_id",
        "position",
        "threshold",
        "horizon",
        "profile_bucket",
        "train_rows",
        "train_positives",
        "probability",
        "baseline_probability",
    )


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
