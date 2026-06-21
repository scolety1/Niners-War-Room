from __future__ import annotations

import argparse
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
from scripts.build_overnight_tune_dataset_v0 import blocked_field_reason
from scripts.run_backtest_v0 import TOP_N_BY_POSITION, _spearman

DEFAULT_OUTPUT_ROOT = Path(
    r"C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v1_expanded_20260622"
)
PHASE_ORDER = ["phase1_base_grid", "phase2_deepening", "phase3_stability_stress"]


class OvernightTuneV1RunError(RuntimeError):
    pass


@dataclass(frozen=True)
class OvernightTuneV1RunResult:
    output_root: Path
    run_manifest_path: Path
    completed_fits_path: Path
    position_results_path: Path
    planned_fits: int
    completed_fits: int
    runtime_seconds: float


def run_overnight_tune_v1(
    *,
    dataset_root: Path = DEFAULT_OUTPUT_ROOT,
    output_root: Path | None = None,
    positions: list[str] | None = None,
    time_budget_minutes: float = 480.0,
    resume: bool = False,
    full_run: bool = False,
    confirm_full_run: bool = False,
    require_expanded_grid: bool = False,
    require_vendor_challengers: bool = False,
    max_fits: int | None = None,
) -> OvernightTuneV1RunResult:
    if full_run and not confirm_full_run:
        raise OvernightTuneV1RunError("full V1 run requires --confirm-full-run")
    output_root = output_root or dataset_root
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = _read_json(dataset_root / "tune_input_manifest_v1.json")
    grid = pd.read_csv(dataset_root / "V1_EXPANDED_PRE_RUN_GRID_MANIFEST.csv")
    if positions:
        grid = grid[grid["position"].isin(positions)].copy()
    if require_expanded_grid and len(grid) < 500:
        raise OvernightTuneV1RunError(f"expanded grid required but only {len(grid)} fits planned")
    if require_vendor_challengers and not bool(manifest.get("vendor_ready")):
        raise OvernightTuneV1RunError(
            "vendor challengers required but manifest vendor_ready is false"
        )
    if (
        require_vendor_challengers
        and not grid["feature_family"].eq("VENDOR_YELLOW_CHALLENGER").any()
    ):
        raise OvernightTuneV1RunError("vendor challengers required but no vendor fit rows exist")

    labels = pd.read_csv(dataset_root / "labels_v1.csv")
    datasets = {
        "safe_baseline_features_v1.csv": pd.read_csv(
            dataset_root / "safe_baseline_features_v1.csv"
        ),
        "safe_expanded_features_v1.csv": pd.read_csv(
            dataset_root / "safe_expanded_features_v1.csv"
        ),
        "safe_no_snap_features_v1.csv": pd.read_csv(dataset_root / "safe_no_snap_features_v1.csv"),
        "safe_snap_fixed_features_v1.csv": pd.read_csv(
            dataset_root / "safe_snap_fixed_features_v1.csv"
        ),
        "vendor_joined_features_v1.csv": pd.read_csv(
            dataset_root / "vendor_joined_features_v1.csv"
        ),
    }
    _validate_inputs(grid, datasets, labels)

    checkpoint_path = output_root / "checkpoints" / "v1_expanded_checkpoint.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    completed_ids = _load_completed(checkpoint_path) if resume else set()
    started = time.monotonic()
    prediction_rows: list[dict[str, Any]] = []
    fit_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    phase_rows: list[dict[str, Any]] = []

    planned = grid if max_fits is None else grid.head(max_fits).copy()
    for phase in PHASE_ORDER:
        phase_grid = planned[planned["phase"].eq(phase)].copy()
        phase_start = time.monotonic()
        phase_completed = 0
        for _, fit in phase_grid.iterrows():
            fit_id = str(fit["fit_id"])
            if fit_id in completed_ids:
                continue
            if _time_exceeded(started, time_budget_minutes):
                skipped_rows.append(_skip_row(fit, "time budget reached"))
                break
            try:
                preds, fit_record = _run_fit(fit, datasets, labels)
            except Exception as exc:
                skipped_rows.append(_skip_row(fit, f"{type(exc).__name__}: {exc}"))
                continue
            prediction_rows.extend(preds)
            fit_rows.append(fit_record)
            completed_ids.add(fit_id)
            phase_completed += 1
            if phase_completed % 25 == 0:
                _write_checkpoint(
                    checkpoint_path,
                    completed=completed_ids,
                    dataset_root=dataset_root,
                    output_root=output_root,
                    phase=phase,
                )
        phase_rows.append(
            {
                "phase": phase,
                "planned_fits": int(len(phase_grid)),
                "completed_new_fits": phase_completed,
                "runtime_seconds": round(time.monotonic() - phase_start, 3),
            }
        )
        _write_checkpoint(
            checkpoint_path,
            completed=completed_ids,
            dataset_root=dataset_root,
            output_root=output_root,
            phase=phase,
        )
        if _time_exceeded(started, time_budget_minutes):
            break

    runtime_seconds = round(time.monotonic() - started, 3)
    predictions = pd.DataFrame(prediction_rows)
    if predictions.empty:
        raise OvernightTuneV1RunError("no V1 predictions were produced")
    completed_fits = pd.DataFrame(fit_rows)
    skipped = pd.DataFrame(skipped_rows)
    phase_summary = pd.DataFrame(phase_rows)
    yearly = _metrics_by_year(predictions)
    position = _metrics_by_position(predictions, yearly)
    ranked = _rank_variants(position)
    hyper = _hyperparameter_results(position)
    vendor_results = position[position["feature_family"].eq("VENDOR_YELLOW_CHALLENGER")].copy()
    blocked_scan = _scan_grid(grid, "blocked")
    leakage_scan = _scan_grid(grid, "leakage")

    paths = _write_outputs(
        output_root=output_root,
        predictions=predictions,
        completed_fits=completed_fits,
        skipped=skipped,
        phase_summary=phase_summary,
        yearly=yearly,
        position=position,
        ranked=ranked,
        hyper=hyper,
        vendor_results=vendor_results,
        blocked_scan=blocked_scan,
        leakage_scan=leakage_scan,
        manifest=manifest,
        planned_count=len(planned),
        runtime_seconds=runtime_seconds,
        checkpoint_path=checkpoint_path,
    )
    return OvernightTuneV1RunResult(
        output_root=output_root,
        run_manifest_path=paths["manifest"],
        completed_fits_path=paths["completed"],
        position_results_path=paths["position"],
        planned_fits=len(planned),
        completed_fits=len(completed_fits),
        runtime_seconds=runtime_seconds,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Overnight Tune V1 expanded search.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full-run", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-full-run", action="store_true")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--positions", nargs="+", default=list(CORE_POSITIONS))
    parser.add_argument("--time-budget-minutes", type=float, default=480.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--require-expanded-grid", action="store_true")
    parser.add_argument("--require-vendor-challengers", action="store_true")
    parser.add_argument("--max-fits", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_overnight_tune_v1(
            dataset_root=args.dataset_root,
            output_root=args.output_root,
            positions=args.positions,
            time_budget_minutes=args.time_budget_minutes,
            resume=args.resume,
            full_run=args.full_run,
            confirm_full_run=args.confirm_full_run,
            require_expanded_grid=args.require_expanded_grid,
            require_vendor_challengers=args.require_vendor_challengers,
            max_fits=args.max_fits,
        )
    except Exception as exc:
        print(f"Overnight Tune V1 run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"output_root={result.output_root}")
    print(f"run_manifest={result.run_manifest_path}")
    print(f"completed_fits={result.completed_fits_path}")
    print(f"position_results={result.position_results_path}")
    print(f"planned_fits={result.planned_fits}")
    print(f"completed_fits_count={result.completed_fits}")
    print(f"runtime_seconds={result.runtime_seconds}")
    return 0


def _run_fit(
    fit: pd.Series, datasets: dict[str, pd.DataFrame], labels: pd.DataFrame
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = str(fit["source_dataset"])
    frame = datasets[source]
    feature_columns = json.loads(str(fit["feature_columns_json"]))
    _scan_columns(feature_columns)
    merged = frame.merge(labels, on=["player_id", "target_season"], how="inner")
    position = str(fit["position"])
    position_rows = merged[merged["target_position"].eq(position)].copy()
    if position_rows.empty:
        raise OvernightTuneV1RunError(f"no rows for position {position}")
    params = json.loads(str(fit["hyperparameters_json"]))
    rows: list[dict[str, Any]] = []
    seasons = sorted(int(season) for season in position_rows["target_season"].unique())
    for test_season in [2021, 2022, 2023, 2024, 2025]:
        if test_season not in seasons:
            continue
        train_seasons = [season for season in seasons if season < test_season]
        if len(train_seasons) < 2:
            continue
        train = position_rows[position_rows["target_season"].isin(train_seasons)].copy()
        test = position_rows[position_rows["target_season"].eq(test_season)].copy()
        if len(train) < 20 or len(test) < 3:
            continue
        pred_points = _predict(train, test, feature_columns, "next_nwr_points", fit, params)
        pred_ppg = _predict(train, test, feature_columns, "next_nwr_ppg", fit, params)
        for (_, row), points, ppg in zip(test.iterrows(), pred_points, pred_ppg, strict=False):
            rows.append(
                {
                    "fit_id": fit["fit_id"],
                    "phase": fit["phase"],
                    "variant_id": fit["variant_id"],
                    "feature_family": fit["feature_family"],
                    "model_family": fit["model_family"],
                    "model_name": fit["model_name"],
                    "hyperparameters_json": fit["hyperparameters_json"],
                    "position": position,
                    "player_id": row["player_id"],
                    "target_season": int(row["target_season"]),
                    "actual_points": float(row["next_nwr_points"]),
                    "predicted_points": float(points),
                    "actual_ppg": float(row["next_nwr_ppg"]),
                    "predicted_ppg": float(ppg),
                    "feature_count": len([c for c in feature_columns if c in train.columns]),
                }
            )
    if not rows:
        raise OvernightTuneV1RunError("fit produced no predictions")
    return rows, {
        "fit_id": fit["fit_id"],
        "phase": fit["phase"],
        "variant_id": fit["variant_id"],
        "feature_family": fit["feature_family"],
        "position": position,
        "model_family": fit["model_family"],
        "model_name": fit["model_name"],
        "hyperparameters_json": fit["hyperparameters_json"],
        "feature_count": len(feature_columns),
        "prediction_rows": len(rows),
        "status": "completed",
    }


def _predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    fit: pd.Series,
    params: dict[str, Any],
) -> np.ndarray:
    model_name = str(fit["model_name"])
    columns = [column for column in feature_columns if column in train.columns]
    if not columns:
        return np.full(
            len(test), float(pd.to_numeric(train[target_column], errors="coerce").mean())
        )
    x_train, x_test, y = _matrices(train, test, columns, target_column)
    if model_name == "numpy_ridge":
        return _numpy_ridge(x_train, x_test, y, float(params.get("alpha", 1.0)))
    if model_name == "sklearn_ridge":
        from sklearn.linear_model import Ridge  # type: ignore

        model = Ridge(alpha=float(params.get("alpha", 1.0)))
    elif model_name == "sklearn_elastic_net":
        from sklearn.linear_model import ElasticNet  # type: ignore

        model = ElasticNet(
            alpha=float(params.get("alpha", 0.05)),
            l1_ratio=float(params.get("l1_ratio", 0.2)),
            max_iter=int(params.get("max_iter", 12000)),
            random_state=42,
        )
    elif model_name == "sklearn_random_forest":
        from sklearn.ensemble import RandomForestRegressor  # type: ignore

        model = RandomForestRegressor(n_jobs=1, **params)
    elif model_name == "sklearn_extra_trees":
        from sklearn.ensemble import ExtraTreesRegressor  # type: ignore

        model = ExtraTreesRegressor(n_jobs=1, **params)
    elif model_name == "sklearn_gradient_boosting":
        from sklearn.ensemble import GradientBoostingRegressor  # type: ignore

        model = GradientBoostingRegressor(**params)
    else:
        raise OvernightTuneV1RunError(f"unsupported model {model_name}")
    model.fit(x_train, y)
    return np.asarray(model.predict(x_test), dtype=float)


def _matrices(
    train: pd.DataFrame, test: pd.DataFrame, columns: list[str], target_column: str
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    x_train = train[columns].apply(pd.to_numeric, errors="coerce")
    x_test = test[columns].apply(pd.to_numeric, errors="coerce")
    medians = x_train.median(numeric_only=True).fillna(0)
    x_train = x_train.fillna(medians)
    x_test = x_test.fillna(medians)
    y = pd.to_numeric(train[target_column], errors="coerce").fillna(0).to_numpy(dtype=float)
    return x_train, x_test, y


def _numpy_ridge(
    x_train: pd.DataFrame, x_test: pd.DataFrame, y: np.ndarray, alpha: float
) -> np.ndarray:
    means = x_train.mean()
    stds = x_train.std(ddof=0).replace(0, 1)
    train_matrix = np.c_[np.ones(len(x_train)), ((x_train - means) / stds).to_numpy(dtype=float)]
    test_matrix = np.c_[np.ones(len(x_test)), ((x_test - means) / stds).to_numpy(dtype=float)]
    penalty = np.eye(train_matrix.shape[1]) * alpha
    penalty[0, 0] = 0
    try:
        beta = np.linalg.solve(train_matrix.T @ train_matrix + penalty, train_matrix.T @ y)
    except np.linalg.LinAlgError:
        beta = np.linalg.pinv(train_matrix.T @ train_matrix + penalty) @ train_matrix.T @ y
    return test_matrix @ beta


def _metrics_by_year(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = [
        "fit_id",
        "phase",
        "variant_id",
        "feature_family",
        "model_family",
        "model_name",
        "hyperparameters_json",
        "position",
        "target_season",
    ]
    for keys, group in predictions.groupby(group_cols):
        rows.append(_metric_row(group, dict(zip(group_cols, keys, strict=False))))
    return pd.DataFrame(rows)


def _metrics_by_position(predictions: pd.DataFrame, yearly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = [
        "fit_id",
        "phase",
        "variant_id",
        "feature_family",
        "model_family",
        "model_name",
        "hyperparameters_json",
        "position",
    ]
    for keys, group in predictions.groupby(group_cols):
        payload = dict(zip(group_cols, keys, strict=False))
        payload["target_season"] = "ALL"
        rows.append(_metric_row(group, payload))
    output = pd.DataFrame(rows)
    base = output[
        (output["variant_id"].eq("safe_baseline"))
        & (output["model_name"].eq("numpy_ridge"))
        & (output["phase"].eq("phase1_base_grid"))
    ].sort_values(["position", "top_n_hit_rate"], ascending=[True, False])
    base = (
        base.groupby("position")
        .head(1)[["position", "top_n_hit_rate", "spearman_points", "mae_points", "rmse_points"]]
        .rename(
            columns={
                "top_n_hit_rate": "baseline_top_n_hit_rate",
                "spearman_points": "baseline_spearman_points",
                "mae_points": "baseline_mae_points",
                "rmse_points": "baseline_rmse_points",
            }
        )
    )
    output = output.merge(base, on="position", how="left")
    output["top_n_hit_rate_improvement_vs_baseline"] = (
        output["top_n_hit_rate"] - output["baseline_top_n_hit_rate"]
    )
    output["spearman_improvement_vs_baseline"] = (
        output["spearman_points"] - output["baseline_spearman_points"]
    )
    output["mae_improvement_vs_baseline"] = output["baseline_mae_points"] - output["mae_points"]
    output["rmse_improvement_vs_baseline"] = output["baseline_rmse_points"] - output["rmse_points"]
    stability = _stability(yearly)
    output = output.merge(stability, on=["fit_id", "position"], how="left")
    output["candidate_label"] = output.apply(_candidate_label, axis=1)
    return output


def _metric_row(group: pd.DataFrame, payload: dict[str, Any]) -> dict[str, Any]:
    actual = pd.to_numeric(group["actual_points"], errors="coerce").fillna(0)
    pred = pd.to_numeric(group["predicted_points"], errors="coerce").fillna(0)
    errors = pred - actual
    output = dict(payload)
    output.update(
        {
            "sample_size": int(len(group)),
            "feature_count": int(pd.to_numeric(group["feature_count"], errors="coerce").max()),
            "top_n_hit_rate": _top_n_hit_rate(
                group, TOP_N_BY_POSITION.get(str(payload["position"]), 12)
            ),
            "spearman_points": _spearman(actual, pred),
            "mae_points": float(errors.abs().mean()),
            "rmse_points": float(math.sqrt(float((errors**2).mean()))),
        }
    )
    return output


def _top_n_hit_rate(group: pd.DataFrame, top_n: int) -> float:
    if group.empty:
        return 0.0
    n = min(top_n, len(group))
    actual_top = set(group.sort_values("actual_points", ascending=False).head(n)["player_id"])
    pred_top = set(group.sort_values("predicted_points", ascending=False).head(n)["player_id"])
    return len(actual_top & pred_top) / n if n else 0.0


def _stability(yearly: pd.DataFrame) -> pd.DataFrame:
    base = yearly[
        (yearly["variant_id"].eq("safe_baseline"))
        & (yearly["model_name"].eq("numpy_ridge"))
        & (yearly["phase"].eq("phase1_base_grid"))
    ].sort_values(["position", "target_season", "top_n_hit_rate"], ascending=[True, True, False])
    base = (
        base.groupby(["position", "target_season"])
        .head(1)[["position", "target_season", "top_n_hit_rate"]]
        .rename(columns={"top_n_hit_rate": "baseline_year_top_n_hit_rate"})
    )
    merged = yearly.merge(base, on=["position", "target_season"], how="left")
    merged["year_top_n_improvement"] = (
        merged["top_n_hit_rate"] - merged["baseline_year_top_n_hit_rate"]
    )
    rows = []
    for (fit_id, position), group in merged.groupby(["fit_id", "position"]):
        gains = pd.to_numeric(group["year_top_n_improvement"], errors="coerce").fillna(0)
        rows.append(
            {
                "fit_id": fit_id,
                "position": position,
                "years_beating_baseline_top_n": int(gains.gt(0).sum()),
                "top_n_improvement_variance": float(gains.var(ddof=0)) if len(gains) else 0.0,
                "worst_year_top_n_drawdown": float(gains.min()) if len(gains) else 0.0,
                "median_yearly_top_n_improvement": float(gains.median()) if len(gains) else 0.0,
                "one_lucky_season_flag": bool(gains.gt(0).sum() == 1 and gains.max() > 0),
                "major_collapse_flag": bool(gains.min() < -0.10),
            }
        )
    return pd.DataFrame(rows)


def _rank_variants(position: pd.DataFrame) -> pd.DataFrame:
    ranked = position.sort_values(
        [
            "position",
            "top_n_hit_rate",
            "median_yearly_top_n_improvement",
            "years_beating_baseline_top_n",
            "spearman_points",
            "mae_points",
            "feature_count",
        ],
        ascending=[True, False, False, False, False, True, True],
    ).copy()
    ranked["position_rank"] = ranked.groupby("position").cumcount() + 1
    return ranked


def _hyperparameter_results(position: pd.DataFrame) -> pd.DataFrame:
    return (
        position.groupby(["model_family", "model_name", "hyperparameters_json"], as_index=False)
        .agg(
            mean_top_n_hit_rate=("top_n_hit_rate", "mean"),
            median_top_n_hit_rate=("top_n_hit_rate", "median"),
            mean_spearman=("spearman_points", "mean"),
            mean_mae=("mae_points", "mean"),
            fit_count=("fit_id", "count"),
        )
        .sort_values(["mean_top_n_hit_rate", "mean_spearman"], ascending=[False, False])
    )


def _candidate_label(row: pd.Series) -> str:
    if row["feature_family"] == "VENDOR_YELLOW_CHALLENGER":
        if (
            float(row.get("top_n_hit_rate_improvement_vs_baseline", 0) or 0) > 0
            and int(row.get("years_beating_baseline_top_n", 0) or 0) >= 2
            and not bool(row.get("major_collapse_flag", False))
        ):
            return "VENDOR_RESEARCH_CANDIDATE"
        return "VENDOR_YELLOW_HOLD"
    if row["variant_id"] == "safe_baseline":
        return "BASELINE_REFERENCE"
    if (
        (
            float(row.get("top_n_hit_rate_improvement_vs_baseline", 0) or 0) > 0
            or (
                abs(float(row.get("top_n_hit_rate_improvement_vs_baseline", 0) or 0)) < 1e-12
                and float(row.get("median_yearly_top_n_improvement", 0) or 0) > 0
            )
        )
        and int(row.get("years_beating_baseline_top_n", 0) or 0) >= 2
        and not bool(row.get("major_collapse_flag", False))
        and not bool(row.get("one_lucky_season_flag", False))
    ):
        return "SAFE_RESEARCH_CANDIDATE"
    return "BASELINE_OR_CONTROL_PREFERRED"


def _write_outputs(
    *,
    output_root: Path,
    predictions: pd.DataFrame,
    completed_fits: pd.DataFrame,
    skipped: pd.DataFrame,
    phase_summary: pd.DataFrame,
    yearly: pd.DataFrame,
    position: pd.DataFrame,
    ranked: pd.DataFrame,
    hyper: pd.DataFrame,
    vendor_results: pd.DataFrame,
    blocked_scan: pd.DataFrame,
    leakage_scan: pd.DataFrame,
    manifest: dict[str, Any],
    planned_count: int,
    runtime_seconds: float,
    checkpoint_path: Path,
) -> dict[str, Path]:
    predictions.to_csv(output_root / "V1_EXPANDED_PREDICTIONS_LOCAL_ONLY.csv", index=False)
    completed_path = output_root / "V1_EXPANDED_COMPLETED_FITS.csv"
    position_path = output_root / "V1_EXPANDED_POSITION_RESULTS.csv"
    yearly_path = output_root / "V1_EXPANDED_YEARLY_RESULTS.csv"
    completed_fits.to_csv(completed_path, index=False)
    position.to_csv(position_path, index=False)
    yearly.to_csv(yearly_path, index=False)
    ranked.to_csv(output_root / "V1_EXPANDED_VARIANT_RANKINGS.csv", index=False)
    hyper.to_csv(output_root / "V1_EXPANDED_HYPERPARAMETER_RESULTS.csv", index=False)
    vendor_results.to_csv(output_root / "V1_EXPANDED_VENDOR_CHALLENGER_RESULTS.csv", index=False)
    blocked_scan.to_csv(output_root / "V1_EXPANDED_BLOCKED_FIELD_SCAN.csv", index=False)
    leakage_scan.to_csv(output_root / "V1_EXPANDED_LEAKAGE_SCAN.csv", index=False)
    skipped.to_csv(output_root / "V1_EXPANDED_SKIPPED_FITS.csv", index=False)
    phase_summary.to_csv(output_root / "V1_EXPANDED_PHASE_SUMMARY.csv", index=False)
    run_manifest = pd.DataFrame(
        [
            {"key": "created_at", "value": datetime.now(UTC).isoformat()},
            {"key": "approval_status", "value": "research_run_only_not_model_approved"},
            {"key": "planned_fit_count", "value": planned_count},
            {"key": "completed_fit_count", "value": len(completed_fits)},
            {"key": "skipped_fit_count", "value": len(skipped)},
            {"key": "position_result_rows", "value": len(position)},
            {"key": "yearly_result_rows", "value": len(yearly)},
            {"key": "prediction_rows", "value": len(predictions)},
            {"key": "runtime_seconds", "value": runtime_seconds},
            {
                "key": "phase2_ran",
                "value": bool(phase_summary["phase"].eq("phase2_deepening").any()),
            },
            {
                "key": "phase3_ran",
                "value": bool(phase_summary["phase"].eq("phase3_stability_stress").any()),
            },
            {
                "key": "blocked_field_scan",
                "value": "PASS" if blocked_scan["scan_result"].eq("PASS").all() else "FAIL",
            },
            {
                "key": "leakage_scan",
                "value": "PASS" if leakage_scan["scan_result"].eq("PASS").all() else "FAIL",
            },
            {"key": "vendor_ready", "value": bool(manifest.get("vendor_ready"))},
            {"key": "checkpoint_path", "value": str(checkpoint_path)},
        ]
    )
    manifest_path = output_root / "V1_EXPANDED_RUN_MANIFEST.csv"
    run_manifest.to_csv(manifest_path, index=False)
    _write_winners(output_root, ranked)
    _write_final_report(output_root, ranked, position, vendor_results, skipped, run_manifest)
    return {"manifest": manifest_path, "completed": completed_path, "position": position_path}


def _write_winners(output_root: Path, ranked: pd.DataFrame) -> None:
    best = ranked[ranked["position_rank"].eq(1)].copy()
    lines = [
        "# V1 Expanded Winners By Position",
        "",
        "Local-only research summary. No model approval or draft-use approval.",
        "",
        "| Position | Variant | Family | Model | Top-N | Spearman | MAE | RMSE | Label |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in best.iterrows():
        lines.append(
            f"| `{row['position']}` | `{row['variant_id']}` | `{row['feature_family']}` | "
            f"`{row['model_name']}` | {row['top_n_hit_rate']:.3f} | "
            f"{row['spearman_points']:.3f} | {row['mae_points']:.3f} | "
            f"{row['rmse_points']:.3f} | `{row['candidate_label']}` |"
        )
    (output_root / "V1_EXPANDED_WINNERS_BY_POSITION.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _write_final_report(
    output_root: Path,
    ranked: pd.DataFrame,
    position: pd.DataFrame,
    vendor_results: pd.DataFrame,
    skipped: pd.DataFrame,
    run_manifest: pd.DataFrame,
) -> None:
    best = ranked[ranked["position_rank"].eq(1)].copy()
    safe_candidates = position[position["candidate_label"].eq("SAFE_RESEARCH_CANDIDATE")]
    vendor_candidates = vendor_results[
        vendor_results["candidate_label"].eq("VENDOR_RESEARCH_CANDIDATE")
    ]
    lines = [
        "# V1 Expanded Overnight Tune Final Report",
        "",
        "Local-only evidence generation only. No private value, rankings, Mock Draft "
        "behavior, simulations, final draft advice, deployment, `latest_candidate`, "
        "or `latest_approved`.",
        "",
        "## Run Manifest",
        "",
    ]
    for _, row in run_manifest.iterrows():
        lines.append(f"- {row['key']}: `{row['value']}`")
    lines.extend(
        [
            "",
            "## Best By Position",
            "",
            "| Position | Variant | Family | Model | Top-N | Stability years | "
            "Worst drawdown | Label |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for _, row in best.iterrows():
        lines.append(
            f"| `{row['position']}` | `{row['variant_id']}` | `{row['feature_family']}` | "
            f"`{row['model_name']}` | {row['top_n_hit_rate']:.3f} | "
            f"{int(row['years_beating_baseline_top_n'])} | "
            f"{row['worst_year_top_n_drawdown']:.3f} | `{row['candidate_label']}` |"
        )
    lines.extend(
        [
            "",
            "## Candidate Summary",
            "",
            f"- SAFE_RESEARCH_CANDIDATE rows: `{len(safe_candidates)}`",
            f"- VENDOR_RESEARCH_CANDIDATE rows: `{len(vendor_candidates)}`",
            f"- Skipped fits: `{len(skipped)}`",
            "",
            "Baseline can remain preferred where it is best or safest. No model is promoted.",
        ]
    )
    (output_root / "V1_EXPANDED_FINAL_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _validate_inputs(
    grid: pd.DataFrame, datasets: dict[str, pd.DataFrame], labels: pd.DataFrame
) -> None:
    if grid.empty:
        raise OvernightTuneV1RunError("grid is empty")
    if labels.empty:
        raise OvernightTuneV1RunError("labels are empty")
    for name, frame in datasets.items():
        if frame.empty:
            raise OvernightTuneV1RunError(f"{name} is empty")
    for _, row in grid.iterrows():
        _scan_columns(json.loads(str(row["feature_columns_json"])))


def _scan_grid(grid: pd.DataFrame, scan_type: str) -> pd.DataFrame:
    rows = []
    leakage = {
        "next_nwr_points",
        "next_nwr_ppg",
        "target_games",
        "fantasy_points",
        "fantasy_points_ppr",
    }
    for _, row in grid.iterrows():
        cols = json.loads(str(row["feature_columns_json"]))
        if scan_type == "blocked":
            bad = [c for c in cols if blocked_field_reason(c)]
            key = "blocked"
        else:
            bad = [c for c in cols if _norm_col(c) in leakage]
            key = "leakage"
        rows.append(
            {
                "fit_id": row["fit_id"],
                "variant_id": row["variant_id"],
                "feature_family": row["feature_family"],
                "position": row["position"],
                f"{key}_field_count": len(bad),
                f"{key}_fields": ";".join(bad),
                "scan_result": "PASS" if not bad else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def _scan_columns(columns: list[str]) -> None:
    leakage = {
        "next_nwr_points",
        "next_nwr_ppg",
        "target_games",
        "fantasy_points",
        "fantasy_points_ppr",
    }
    for column in columns:
        if blocked_field_reason(column):
            raise OvernightTuneV1RunError(f"blocked field in model input: {column}")
        if _norm_col(column) in leakage:
            raise OvernightTuneV1RunError(f"leakage field in model input: {column}")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise OvernightTuneV1RunError(f"missing manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _skip_row(fit: pd.Series, reason: str) -> dict[str, Any]:
    return {
        "fit_id": fit.get("fit_id", ""),
        "phase": fit.get("phase", ""),
        "variant_id": fit.get("variant_id", ""),
        "feature_family": fit.get("feature_family", ""),
        "position": fit.get("position", ""),
        "model_name": fit.get("model_name", ""),
        "reason": reason,
    }


def _load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")).get("completed", []))


def _write_checkpoint(
    path: Path, *, completed: set[str], dataset_root: Path, output_root: Path, phase: str
) -> None:
    payload = {
        "updated_at": datetime.now(UTC).isoformat(),
        "dataset_root": str(dataset_root),
        "output_root": str(output_root),
        "phase": phase,
        "completed": sorted(completed),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _time_exceeded(started: float, minutes: float) -> bool:
    return (time.monotonic() - started) >= minutes * 60


def _norm_col(value: Any) -> str:
    text = str(value).strip().lower()
    for char in (" ", "-", "/", "%", "."):
        text = text.replace(char, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
