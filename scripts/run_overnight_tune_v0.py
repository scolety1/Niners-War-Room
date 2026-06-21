from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_backtest_dataset_v0 import CORE_POSITIONS
from scripts.build_overnight_tune_dataset_v0 import (
    DEFAULT_OUTPUT_ROOT,
    blocked_field_reason,
)
from scripts.run_backtest_v0 import TOP_N_BY_POSITION, _ridge_predict, _spearman

DEFAULT_EVALUATION_SEASONS = [2021, 2022, 2023, 2024, 2025]
DEFAULT_MODELS = ["numpy_ridge", "sklearn_ridge", "sklearn_elastic_net", "sklearn_random_forest"]


class OvernightTuneRunError(RuntimeError):
    pass


@dataclass(frozen=True)
class OvernightTuneRunResult:
    output_root: Path
    predictions_path: Path
    metrics_by_position_path: Path
    metrics_by_year_path: Path
    winner_report_path: Path
    report_path: Path
    manifest_path: Path
    checkpoint_path: Path
    metrics_by_position: pd.DataFrame
    dry_run: bool
    sklearn_available: bool


def run_overnight_tune_v0(
    *,
    dataset_root: Path = DEFAULT_OUTPUT_ROOT,
    output_root: Path | None = None,
    dry_run: bool = True,
    confirm_full_run: bool = False,
    evaluation_seasons: list[int] | None = None,
    positions: list[str] | None = None,
    models: list[str] | None = None,
    min_train_seasons: int = 2,
    min_train_rows: int = 20,
    time_budget_minutes: float = 10.0,
    max_variants: int | None = None,
    max_positions: int | None = None,
    max_seasons: int | None = None,
    resume: bool = False,
) -> OvernightTuneRunResult:
    if not dry_run and not confirm_full_run:
        raise OvernightTuneRunError("full tune requires --confirm-full-run")
    output_root = output_root or dataset_root
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = (
        output_root
        / "checkpoints"
        / ("dry_run_checkpoint.json" if dry_run else "overnight_tune_checkpoint.json")
    )
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest(dataset_root / "tune_input_manifest_v0.json")
    input_dataset_dir = Path(manifest["input_dataset_dir"])
    variant_plan = pd.read_csv(dataset_root / "dataset_variant_plan_v0.csv")
    baseline = pd.read_csv(input_dataset_dir / "feature_dataset_v1_baseline.csv")
    clean_expanded = pd.read_csv(input_dataset_dir / "feature_dataset_v1_clean_expanded.csv")
    labels = pd.read_csv(input_dataset_dir / "labels_v1.csv")
    _validate_inputs(baseline, clean_expanded, labels, variant_plan)

    evaluation_seasons = evaluation_seasons or DEFAULT_EVALUATION_SEASONS
    positions = positions or list(CORE_POSITIONS)
    if max_positions is not None:
        positions = positions[:max_positions]
    model_status = sklearn_status()
    selected_models = _selected_models(models, model_status["available"])
    if dry_run:
        selected_models = [model for model in selected_models if model == "numpy_ridge"][:1]
        max_variants = max_variants or 3
        max_seasons = max_seasons or 2
    if max_seasons is not None:
        evaluation_seasons = evaluation_seasons[:max_seasons]

    completed = _load_completed(checkpoint_path) if resume else set()
    rows: list[dict[str, Any]] = []
    year_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    started = time.monotonic()
    variants = _runnable_variants(variant_plan, positions)
    if max_variants is not None:
        variants = variants.head(max_variants)

    for _, variant in variants.iterrows():
        variant_id = str(variant["variant_id"])
        position = str(variant["position"])
        source_dataset = str(variant["source_dataset"])
        feature_columns = json.loads(str(variant["feature_columns_json"]))
        feature_family = str(variant["feature_family"])
        if not _truthy(variant.get("include_in_dry_run", False)) and dry_run:
            skipped_rows.append(_skip_row(variant, "not included in dry run"))
            continue
        if _truthy(variant.get("requires_vendor_join", False)):
            skipped_rows.append(
                _skip_row(variant, "vendor challengers are planned but not joined in V0 dry run")
            )
            continue
        _scan_blocked(feature_columns, context=f"{variant_id}:{position}")
        features = baseline if source_dataset.endswith("baseline.csv") else clean_expanded
        merged = features.merge(labels, on=["player_id", "target_season"], how="inner")
        position_rows = merged[merged["target_position"].eq(position)].copy()
        if position_rows.empty:
            skipped_rows.append(_skip_row(variant, "no rows for position"))
            continue
        for model_name in selected_models:
            key = f"{variant_id}|{position}|{model_name}"
            if key in completed:
                continue
            if _time_exceeded(started, time_budget_minutes):
                skipped_rows.append(_skip_row(variant, "time budget reached"))
                break
            prediction_rows = _rolling_predictions(
                position_rows=position_rows,
                feature_columns=feature_columns,
                variant_id=variant_id,
                feature_family=feature_family,
                position=position,
                model_name=model_name,
                evaluation_seasons=evaluation_seasons,
                min_train_seasons=min_train_seasons,
                min_train_rows=min_train_rows,
            )
            rows.extend(prediction_rows)
            year_rows.extend(
                _metrics_by_year(
                    prediction_rows=prediction_rows,
                    variant_id=variant_id,
                    feature_family=feature_family,
                    position=position,
                    model_name=model_name,
                )
            )
            completed.add(key)
            _write_checkpoint(
                checkpoint_path,
                completed=completed,
                dry_run=dry_run,
                dataset_root=dataset_root,
                output_root=output_root,
            )

    predictions = pd.DataFrame(rows)
    if predictions.empty:
        raise OvernightTuneRunError("no rolling-origin predictions were produced")
    metrics_by_year = pd.DataFrame(year_rows)
    metrics_by_position = _metrics_by_position(predictions, metrics_by_year)
    winner_report = _winner_report(metrics_by_position)

    predictions_path = output_root / (
        "dry_run_predictions.csv" if dry_run else "overnight_tune_predictions.csv"
    )
    metrics_by_position_path = output_root / (
        "dry_run_metrics_by_position.csv" if dry_run else "overnight_tune_metrics_by_position.csv"
    )
    metrics_by_year_path = output_root / (
        "dry_run_metrics_by_year.csv" if dry_run else "overnight_tune_metrics_by_year.csv"
    )
    winner_report_path = output_root / (
        "dry_run_winner_report.csv" if dry_run else "overnight_tune_winner_report.csv"
    )
    skipped_path = output_root / (
        "dry_run_skipped_variants.csv" if dry_run else "overnight_tune_skipped_variants.csv"
    )
    report_path = output_root / (
        "OVERNIGHT_TUNE_V0_DRY_RUN_REPORT.md" if dry_run else "OVERNIGHT_TUNE_V0_REPORT.md"
    )
    manifest_path = output_root / (
        "dry_run_manifest.json" if dry_run else "overnight_tune_manifest.json"
    )

    predictions.to_csv(predictions_path, index=False, encoding="utf-8")
    metrics_by_position.to_csv(metrics_by_position_path, index=False, encoding="utf-8")
    metrics_by_year.to_csv(metrics_by_year_path, index=False, encoding="utf-8")
    winner_report.to_csv(winner_report_path, index=False, encoding="utf-8")
    pd.DataFrame(skipped_rows).to_csv(skipped_path, index=False, encoding="utf-8")
    run_manifest = _run_manifest(
        dataset_root=dataset_root,
        output_root=output_root,
        dry_run=dry_run,
        manifest=manifest,
        model_status=model_status,
        selected_models=selected_models,
        predictions=predictions,
        metrics_by_position=metrics_by_position,
        metrics_by_year=metrics_by_year,
        files={
            predictions_path.name: predictions_path,
            metrics_by_position_path.name: metrics_by_position_path,
            metrics_by_year_path.name: metrics_by_year_path,
            winner_report_path.name: winner_report_path,
            skipped_path.name: skipped_path,
            checkpoint_path.name: checkpoint_path,
        },
    )
    manifest_path.write_text(
        json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report_path.write_text(
        _markdown_report(run_manifest, metrics_by_position, winner_report), encoding="utf-8"
    )
    return OvernightTuneRunResult(
        output_root=output_root,
        predictions_path=predictions_path,
        metrics_by_position_path=metrics_by_position_path,
        metrics_by_year_path=metrics_by_year_path,
        winner_report_path=winner_report_path,
        report_path=report_path,
        manifest_path=manifest_path,
        checkpoint_path=checkpoint_path,
        metrics_by_position=metrics_by_position,
        dry_run=dry_run,
        sklearn_available=bool(model_status["available"]),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local-only Overnight Model Tune V0 dry run or confirmed full tune."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True)
    mode.add_argument("--full-run", action="store_true")
    parser.add_argument("--confirm-full-run", action="store_true")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument(
        "--evaluation-seasons", nargs="+", type=int, default=DEFAULT_EVALUATION_SEASONS
    )
    parser.add_argument("--positions", nargs="+", default=list(CORE_POSITIONS))
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--min-train-seasons", type=int, default=2)
    parser.add_argument("--min-train-rows", type=int, default=20)
    parser.add_argument("--time-budget-minutes", type=float, default=10.0)
    parser.add_argument("--max-variants", type=int, default=None)
    parser.add_argument("--max-positions", type=int, default=None)
    parser.add_argument("--max-seasons", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_overnight_tune_v0(
            dataset_root=args.dataset_root,
            output_root=args.output_root,
            dry_run=not args.full_run,
            confirm_full_run=args.confirm_full_run,
            evaluation_seasons=args.evaluation_seasons,
            positions=args.positions,
            models=args.models,
            min_train_seasons=args.min_train_seasons,
            min_train_rows=args.min_train_rows,
            time_budget_minutes=args.time_budget_minutes,
            max_variants=args.max_variants,
            max_positions=args.max_positions,
            max_seasons=args.max_seasons,
            resume=args.resume,
        )
    except Exception as exc:
        print(f"Overnight Tune V0 run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"output_root={result.output_root}")
    print(f"predictions={result.predictions_path}")
    print(f"metrics_by_position={result.metrics_by_position_path}")
    print(f"metrics_by_year={result.metrics_by_year_path}")
    print(f"winner_report={result.winner_report_path}")
    print(f"report={result.report_path}")
    print(f"manifest={result.manifest_path}")
    print(f"checkpoint={result.checkpoint_path}")
    print(f"dry_run={result.dry_run}")
    print(f"sklearn_available={result.sklearn_available}")
    return 0


def sklearn_status() -> dict[str, Any]:
    try:
        import sklearn  # type: ignore

        return {"available": True, "version": getattr(sklearn, "__version__", "unknown")}
    except Exception as exc:
        return {"available": False, "version": None, "reason": f"{type(exc).__name__}: {exc}"}


def _selected_models(requested: list[str] | None, sklearn_available: bool) -> list[str]:
    requested = requested or DEFAULT_MODELS
    selected = []
    for model in requested:
        if model == "numpy_ridge":
            selected.append(model)
        elif sklearn_available:
            selected.append(model)
    return selected or ["numpy_ridge"]


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise OvernightTuneRunError(f"missing tune input manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_inputs(
    baseline: pd.DataFrame,
    clean_expanded: pd.DataFrame,
    labels: pd.DataFrame,
    variant_plan: pd.DataFrame,
) -> None:
    for name, frame in {
        "baseline": baseline,
        "clean_expanded": clean_expanded,
        "labels": labels,
    }.items():
        if frame.empty:
            raise OvernightTuneRunError(f"{name} is empty")
    for column in variant_plan.columns:
        if blocked_field_reason(column):
            raise OvernightTuneRunError(f"blocked field appears in variant plan column: {column}")
    required_plan = {
        "variant_id",
        "feature_family",
        "position",
        "source_dataset",
        "feature_columns_json",
        "include_in_dry_run",
    }
    missing_plan = sorted(required_plan.difference(variant_plan.columns))
    if missing_plan:
        raise OvernightTuneRunError(f"variant plan missing columns: {missing_plan}")


def _runnable_variants(variant_plan: pd.DataFrame, positions: list[str]) -> pd.DataFrame:
    return variant_plan[variant_plan["position"].isin(positions)].copy()


def _rolling_predictions(
    *,
    position_rows: pd.DataFrame,
    feature_columns: list[str],
    variant_id: str,
    feature_family: str,
    position: str,
    model_name: str,
    evaluation_seasons: list[int],
    min_train_seasons: int,
    min_train_rows: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    available_seasons = sorted(int(season) for season in position_rows["target_season"].unique())
    for test_season in evaluation_seasons:
        if test_season not in available_seasons:
            continue
        train_seasons = [season for season in available_seasons if season < test_season]
        if len(train_seasons) < min_train_seasons:
            continue
        train = position_rows[position_rows["target_season"].isin(train_seasons)].copy()
        test = position_rows[position_rows["target_season"].eq(test_season)].copy()
        if len(train) < min_train_rows or len(test) < 3:
            continue
        pred_points = _predict(train, test, feature_columns, "next_nwr_points", model_name)
        pred_ppg = _predict(train, test, feature_columns, "next_nwr_ppg", model_name)
        for (_, row), points, ppg in zip(test.iterrows(), pred_points, pred_ppg, strict=False):
            rows.append(
                {
                    "variant_id": variant_id,
                    "feature_family": feature_family,
                    "model_name": model_name,
                    "position": position,
                    "player_id": row["player_id"],
                    "player_name": row.get("target_player_name", ""),
                    "target_season": int(row["target_season"]),
                    "actual_points": float(row["next_nwr_points"]),
                    "predicted_points": float(points),
                    "actual_ppg": float(row["next_nwr_ppg"]),
                    "predicted_ppg": float(ppg),
                    "target_games": float(row.get("target_games", 0)),
                    "feature_count": len(
                        [column for column in feature_columns if column in train.columns]
                    ),
                }
            )
    return rows


def _predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    model_name: str,
) -> np.ndarray:
    if model_name == "numpy_ridge":
        return _ridge_predict(train, test, feature_columns, target_column)
    columns = [column for column in feature_columns if column in train.columns]
    if not columns:
        return np.full(
            len(test), float(pd.to_numeric(train[target_column], errors="coerce").mean())
        )
    x_train, x_test, y_train = _sklearn_matrices(train, test, columns, target_column)
    if model_name == "sklearn_ridge":
        from sklearn.linear_model import Ridge  # type: ignore

        model = Ridge(alpha=1.0)
    elif model_name == "sklearn_elastic_net":
        from sklearn.linear_model import ElasticNet  # type: ignore

        model = ElasticNet(alpha=0.05, l1_ratio=0.2, max_iter=5000, random_state=42)
    elif model_name == "sklearn_random_forest":
        from sklearn.ensemble import RandomForestRegressor  # type: ignore

        model = RandomForestRegressor(
            n_estimators=80, min_samples_leaf=4, random_state=42, n_jobs=1
        )
    else:
        raise OvernightTuneRunError(f"unsupported model: {model_name}")
    model.fit(x_train, y_train)
    return np.asarray(model.predict(x_test), dtype=float)


def _sklearn_matrices(
    train: pd.DataFrame, test: pd.DataFrame, columns: list[str], target_column: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    x_train = train[columns].apply(pd.to_numeric, errors="coerce")
    x_test = test[columns].apply(pd.to_numeric, errors="coerce")
    medians = x_train.median(numeric_only=True).fillna(0)
    x_train = x_train.fillna(medians)
    x_test = x_test.fillna(medians)
    y_train = pd.to_numeric(train[target_column], errors="coerce").fillna(0)
    return x_train, x_test, y_train


def _metrics_by_year(
    *,
    prediction_rows: list[dict[str, Any]],
    variant_id: str,
    feature_family: str,
    position: str,
    model_name: str,
) -> list[dict[str, Any]]:
    frame = pd.DataFrame(prediction_rows)
    if frame.empty:
        return []
    return [
        _metric_row(group, variant_id, feature_family, position, model_name, int(season))
        for season, group in frame.groupby("target_season")
    ]


def _metrics_by_position(predictions: pd.DataFrame, metrics_by_year: pd.DataFrame) -> pd.DataFrame:
    rows = [
        _metric_row(group, variant_id, feature_family, position, model_name, "ALL")
        for (variant_id, feature_family, position, model_name), group in predictions.groupby(
            ["variant_id", "feature_family", "position", "model_name"]
        )
    ]
    output = pd.DataFrame(rows)
    reference = output[
        (output["variant_id"].eq("safe_baseline")) & (output["model_name"].eq("numpy_ridge"))
    ][["position", "top_n_hit_rate", "spearman_points", "mae_points", "rmse_points"]].rename(
        columns={
            "top_n_hit_rate": "baseline_top_n_hit_rate",
            "spearman_points": "baseline_spearman_points",
            "mae_points": "baseline_mae_points",
            "rmse_points": "baseline_rmse_points",
        }
    )
    output = output.merge(reference, on="position", how="left")
    output["top_n_hit_rate_improvement_vs_baseline"] = (
        output["top_n_hit_rate"] - output["baseline_top_n_hit_rate"]
    )
    output["spearman_improvement_vs_baseline"] = (
        output["spearman_points"] - output["baseline_spearman_points"]
    )
    output["mae_improvement_vs_baseline"] = output["baseline_mae_points"] - output["mae_points"]
    output["rmse_improvement_vs_baseline"] = output["baseline_rmse_points"] - output["rmse_points"]
    stability = _stability_metrics(metrics_by_year)
    output = output.merge(stability, on=["variant_id", "position", "model_name"], how="left")
    output["candidate_report_label"] = output.apply(_candidate_label, axis=1)
    return output


def _metric_row(
    group: pd.DataFrame,
    variant_id: str,
    feature_family: str,
    position: str,
    model_name: str,
    target_season: Any,
) -> dict[str, Any]:
    actual = pd.to_numeric(group["actual_points"], errors="coerce").fillna(0)
    pred = pd.to_numeric(group["predicted_points"], errors="coerce").fillna(0)
    actual_ppg = pd.to_numeric(group["actual_ppg"], errors="coerce").fillna(0)
    pred_ppg = pd.to_numeric(group["predicted_ppg"], errors="coerce").fillna(0)
    errors = pred - actual
    ppg_errors = pred_ppg - actual_ppg
    return {
        "variant_id": variant_id,
        "feature_family": feature_family,
        "model_name": model_name,
        "position": position,
        "target_season": target_season,
        "sample_size": int(len(group)),
        "seasons_evaluated": ",".join(
            str(int(season)) for season in sorted(group["target_season"].unique())
        ),
        "feature_count": int(pd.to_numeric(group.get("feature_count", 0), errors="coerce").max()),
        "mae_points": float(errors.abs().mean()),
        "rmse_points": float(math.sqrt(float((errors**2).mean()))),
        "spearman_points": _spearman(actual, pred),
        "mae_ppg": float(ppg_errors.abs().mean()),
        "rmse_ppg": float(math.sqrt(float((ppg_errors**2).mean()))),
        "spearman_ppg": _spearman(actual_ppg, pred_ppg),
        "top_n_hit_rate": _top_n_hit_rate(group, TOP_N_BY_POSITION.get(position, 12)),
    }


def _top_n_hit_rate(group: pd.DataFrame, top_n: int) -> float:
    if group.empty:
        return 0.0
    n = min(top_n, len(group))
    actual_top = set(group.sort_values("actual_points", ascending=False).head(n)["player_id"])
    pred_top = set(group.sort_values("predicted_points", ascending=False).head(n)["player_id"])
    return len(actual_top & pred_top) / n if n else 0.0


def _stability_metrics(metrics_by_year: pd.DataFrame) -> pd.DataFrame:
    if metrics_by_year.empty:
        return pd.DataFrame(
            columns=[
                "variant_id",
                "position",
                "model_name",
                "years_beating_baseline_top_n",
                "top_n_improvement_variance",
                "worst_year_top_n_drawdown",
                "median_yearly_top_n_improvement",
                "one_lucky_season_flag",
            ]
        )
    base = metrics_by_year[
        (metrics_by_year["variant_id"].eq("safe_baseline"))
        & (metrics_by_year["model_name"].eq("numpy_ridge"))
    ][["position", "target_season", "top_n_hit_rate"]].rename(
        columns={"top_n_hit_rate": "baseline_year_top_n_hit_rate"}
    )
    merged = metrics_by_year.merge(base, on=["position", "target_season"], how="left")
    merged["year_top_n_improvement"] = (
        merged["top_n_hit_rate"] - merged["baseline_year_top_n_hit_rate"]
    )
    rows = []
    for (variant_id, position, model_name), group in merged.groupby(
        ["variant_id", "position", "model_name"]
    ):
        gains = pd.to_numeric(group["year_top_n_improvement"], errors="coerce").fillna(0)
        positive = gains[gains.gt(0)]
        rows.append(
            {
                "variant_id": variant_id,
                "position": position,
                "model_name": model_name,
                "years_beating_baseline_top_n": int(gains.gt(0).sum()),
                "top_n_improvement_variance": float(gains.var(ddof=0)) if len(gains) else 0.0,
                "worst_year_top_n_drawdown": float(gains.min()) if len(gains) else 0.0,
                "median_yearly_top_n_improvement": float(gains.median()) if len(gains) else 0.0,
                "one_lucky_season_flag": bool(
                    len(positive) == 1
                    and float(positive.max()) > max(float(gains.abs().sum()) * 0.5, 0.0)
                ),
            }
        )
    return pd.DataFrame(rows)


def _candidate_label(row: pd.Series) -> str:
    if row["feature_family"] == "VENDOR_YELLOW_CHALLENGER":
        safe_prefix = "VENDOR_RESEARCH"
    elif row["feature_family"] in {
        "SAFE_BASELINE",
        "SAFE_EXPANDED",
        "SAFE_NO_SNAP",
        "SAFE_SNAP_FIXED",
    }:
        safe_prefix = "SAFE"
    else:
        return "NOT_CANDIDATE"
    if row["variant_id"] == "safe_baseline":
        return "BASELINE_REFERENCE"
    top_n_gain = float(row.get("top_n_hit_rate_improvement_vs_baseline", 0) or 0)
    stability_gain = float(row.get("median_yearly_top_n_improvement", 0) or 0)
    collapse = float(row.get("worst_year_top_n_drawdown", 0) or 0) < -0.10
    lucky = bool(row.get("one_lucky_season_flag", False))
    if (top_n_gain > 0 or (top_n_gain == 0 and stability_gain > 0)) and not collapse and not lucky:
        return f"{safe_prefix}_CANDIDATE_REPORT_ONLY"
    return "BASELINE_OR_CONTROL_PREFERRED"


def _winner_report(metrics_by_position: pd.DataFrame) -> pd.DataFrame:
    sort_columns = [
        "position",
        "top_n_hit_rate",
        "median_yearly_top_n_improvement",
        "years_beating_baseline_top_n",
        "spearman_points",
        "mae_points",
        "feature_count",
    ]
    ascending = [True, False, False, False, False, True, True]
    ranked = metrics_by_position.sort_values(sort_columns, ascending=ascending).copy()
    ranked["position_rank"] = ranked.groupby("position").cumcount() + 1
    return ranked[ranked["position_rank"].le(3)].copy()


def _run_manifest(
    *,
    dataset_root: Path,
    output_root: Path,
    dry_run: bool,
    manifest: dict[str, Any],
    model_status: dict[str, Any],
    selected_models: list[str],
    predictions: pd.DataFrame,
    metrics_by_position: pd.DataFrame,
    metrics_by_year: pd.DataFrame,
    files: dict[str, Path],
) -> dict[str, Any]:
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "purpose": "local_only_overnight_model_tune_v0_dry_run"
        if dry_run
        else "local_only_overnight_model_tune_v0",
        "approval_status": "dry_run_only_not_model_approved"
        if dry_run
        else "research_run_only_not_model_approved",
        "dataset_root": str(dataset_root),
        "output_root": str(output_root),
        "input_dataset_dir": manifest.get("input_dataset_dir"),
        "dry_run": dry_run,
        "sklearn_status": model_status,
        "selected_models": selected_models,
        "prediction_rows": int(len(predictions)),
        "metrics_by_position_rows": int(len(metrics_by_position)),
        "metrics_by_year_rows": int(len(metrics_by_year)),
        "feature_families": manifest.get("feature_families", []),
        "metric_priority": [
            "top_n_hit_rate",
            "stability_across_years",
            "spearman_ranking_quality",
            "mae_rmse",
            "simplicity_and_leakage_safety",
        ],
        "forbidden_use": manifest.get("forbidden_use", []),
        "files": {name: _file_record(path) for name, path in files.items()},
    }


def _markdown_report(
    manifest: dict[str, Any], metrics: pd.DataFrame, winner_report: pd.DataFrame
) -> str:
    lines = [
        "# Overnight Model Tune V0 Dry-Run Report",
        "",
        (
            "Local-only dry run only. This does not approve private value, "
            "rankings, hidden sort, Mock Draft behavior, simulations, final draft "
            "advice, deployment, `latest_candidate`, or `latest_approved`."
        ),
        "",
        "## Run Summary",
        "",
        f"- Dataset root: `{manifest['dataset_root']}`",
        f"- Output root: `{manifest['output_root']}`",
        f"- Dry run: `{manifest['dry_run']}`",
        f"- sklearn available: `{manifest['sklearn_status']['available']}`",
        f"- Selected models: `{', '.join(manifest['selected_models'])}`",
        f"- Prediction rows: `{manifest['prediction_rows']}`",
        "",
        "## Metric Priority",
        "",
        "1. Top-N hit rate",
        "2. Stability across years",
        "3. Spearman / ranking quality",
        "4. MAE / RMSE",
        "5. Simplicity / leakage safety",
        "",
        "## Per-Position Top Rows",
        "",
        (
            "| Position | Variant | Family | Model | Top-N | Median yearly Top-N gain | "
            "Worst drawdown | Label |"
        ),
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for _, row in winner_report.sort_values(["position", "position_rank"]).iterrows():
        lines.append(
            f"| `{row['position']}` | `{row['variant_id']}` | `{row['feature_family']}` | "
            f"`{row['model_name']}` | {row['top_n_hit_rate']:.3f} | "
            f"{row.get('median_yearly_top_n_improvement', 0):.3f} | "
            f"{row.get('worst_year_top_n_drawdown', 0):.3f} | "
            f"`{row['candidate_report_label']}` |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Blocked fields are scanned before fitting.",
            "- Vendor challenger variants are isolated and not joined in this dry run.",
            "- No tuned model is promoted automatically.",
            "- Outputs are local-only and outside Git.",
        ]
    )
    return "\n".join(lines) + "\n"


def _scan_blocked(columns: list[str], *, context: str) -> None:
    for column in columns:
        reason = blocked_field_reason(column)
        if reason:
            raise OvernightTuneRunError(f"blocked feature in {context}: {column} ({reason})")


def _skip_row(variant: pd.Series, reason: str) -> dict[str, Any]:
    return {
        "variant_id": variant.get("variant_id", ""),
        "feature_family": variant.get("feature_family", ""),
        "position": variant.get("position", ""),
        "reason": reason,
    }


def _time_exceeded(started: float, time_budget_minutes: float) -> bool:
    return (time.monotonic() - started) > (time_budget_minutes * 60)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return set(payload.get("completed", []))


def _write_checkpoint(
    path: Path,
    *,
    completed: set[str],
    dry_run: bool,
    dataset_root: Path,
    output_root: Path,
) -> None:
    payload = {
        "updated_at": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "dataset_root": str(dataset_root),
        "output_root": str(output_root),
        "completed": sorted(completed),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_record(path: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {
        "path": str(path),
        "row_count": _csv_row_count(path) if path.suffix.lower() == ".csv" else None,
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


if __name__ == "__main__":
    raise SystemExit(main())
