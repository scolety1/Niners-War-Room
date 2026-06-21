from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_backtest_dataset_v0 import (
    BASELINE_NUMERIC_COLUMNS,
    BLOCKED_FEATURE_TOKENS,
    CORE_POSITIONS,
    EXPANDED_EXTRA_COLUMNS,
    LABEL_COLUMNS,
    YELLOW_CHALLENGER_ALLOWED_EXACT,
    YELLOW_CHALLENGER_TOKENS,
)

TOP_N_BY_POSITION = {"QB": 12, "RB": 24, "WR": 36, "TE": 12}


class BacktestRunError(RuntimeError):
    pass


@dataclass(frozen=True)
class BacktestRunResult:
    output_dir: Path
    metrics_by_position_path: Path
    metrics_by_year_path: Path
    report_path: Path
    manifest_path: Path
    metrics_by_position: pd.DataFrame
    metrics_by_year: pd.DataFrame


def run_backtest(
    *,
    dataset_dir: Path,
    output_dir: Path | None = None,
    min_train_seasons: int = 2,
) -> BacktestRunResult:
    output = output_dir or dataset_dir
    output.mkdir(parents=True, exist_ok=True)
    baseline = pd.read_csv(dataset_dir / "feature_dataset_baseline.csv")
    expanded = pd.read_csv(dataset_dir / "feature_dataset_expanded.csv")
    labels = pd.read_csv(dataset_dir / "labels.csv")
    _validate_inputs(baseline, expanded, labels)

    rows: list[dict[str, Any]] = []
    year_rows: list[dict[str, Any]] = []
    for feature_set_name, features, feature_columns in (
        ("baseline", baseline, BASELINE_NUMERIC_COLUMNS),
        ("expanded_factual", expanded, BASELINE_NUMERIC_COLUMNS + EXPANDED_EXTRA_COLUMNS),
    ):
        merged = features.merge(labels, on=["player_id", "target_season"], how="inner")
        for position in CORE_POSITIONS:
            position_rows = merged[merged["target_position"] == position].copy()
            if position_rows.empty:
                continue
            prediction_rows = _rolling_predictions(
                position_rows=position_rows,
                feature_columns=[column for column in feature_columns if column in position_rows],
                feature_set=feature_set_name,
                position=position,
                min_train_seasons=min_train_seasons,
            )
            rows.extend(prediction_rows)
            year_rows.extend(_metrics_by_year(prediction_rows, feature_set_name, position))

    predictions = pd.DataFrame(rows)
    if predictions.empty:
        raise BacktestRunError("no rolling-origin predictions were produced")
    metrics_by_position = _metrics_by_position(predictions)
    metrics_by_year = pd.DataFrame(year_rows)
    metrics_by_position_path = output / "metrics_by_position.csv"
    metrics_by_year_path = output / "metrics_by_year.csv"
    report_path = output / "backtest_v0_report.md"
    manifest_path = output / "run_manifest.json"
    predictions_path = output / "predictions.csv"

    predictions.to_csv(predictions_path, index=False, encoding="utf-8")
    metrics_by_position.to_csv(metrics_by_position_path, index=False, encoding="utf-8")
    metrics_by_year.to_csv(metrics_by_year_path, index=False, encoding="utf-8")
    manifest = _run_manifest(
        dataset_dir=dataset_dir,
        output_dir=output,
        baseline=baseline,
        expanded=expanded,
        labels=labels,
        predictions=predictions,
        metrics_by_position=metrics_by_position,
        metrics_by_year=metrics_by_year,
        files={
            "metrics_by_position.csv": metrics_by_position_path,
            "metrics_by_year.csv": metrics_by_year_path,
            "predictions.csv": predictions_path,
        },
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report_path.write_text(_markdown_report(manifest, metrics_by_position), encoding="utf-8")
    return BacktestRunResult(
        output_dir=output,
        metrics_by_position_path=metrics_by_position_path,
        metrics_by_year_path=metrics_by_year_path,
        report_path=report_path,
        manifest_path=manifest_path,
        metrics_by_position=metrics_by_position,
        metrics_by_year=metrics_by_year,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run local-only Backtest V0 evaluation from prepared feature datasets."
    )
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--min-train-seasons", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_backtest(
            dataset_dir=args.dataset_dir,
            output_dir=args.output_dir,
            min_train_seasons=args.min_train_seasons,
        )
    except Exception as exc:
        print(f"Backtest V0 run failed: {type(exc).__name__}: {exc}")
        return 1
    print(f"output_dir={result.output_dir}")
    print(f"metrics_by_position={result.metrics_by_position_path}")
    print(f"metrics_by_year={result.metrics_by_year_path}")
    print(f"report={result.report_path}")
    print(f"manifest={result.manifest_path}")
    return 0


def _validate_inputs(baseline: pd.DataFrame, expanded: pd.DataFrame, labels: pd.DataFrame) -> None:
    for name, frame in {"baseline": baseline, "expanded": expanded, "labels": labels}.items():
        if frame.empty:
            raise BacktestRunError(f"{name} dataset is empty")
    for frame_name, frame in {"baseline": baseline, "expanded": expanded}.items():
        for column in frame.columns:
            lower = str(column).lower()
            if any(token in lower for token in BLOCKED_FEATURE_TOKENS):
                raise BacktestRunError(f"blocked feature in {frame_name}: {column}")
            if lower not in YELLOW_CHALLENGER_ALLOWED_EXACT and any(
                token in lower for token in YELLOW_CHALLENGER_TOKENS
            ):
                raise BacktestRunError(f"YELLOW challenger feature in main {frame_name}: {column}")
    missing_label_columns = sorted(set(LABEL_COLUMNS).difference(labels.columns))
    if missing_label_columns:
        raise BacktestRunError(f"labels missing columns: {missing_label_columns}")


def _rolling_predictions(
    *,
    position_rows: pd.DataFrame,
    feature_columns: list[str],
    feature_set: str,
    position: str,
    min_train_seasons: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seasons = sorted(int(season) for season in position_rows["target_season"].unique())
    for test_season in seasons:
        train_seasons = [season for season in seasons if season < test_season]
        if len(train_seasons) < min_train_seasons:
            continue
        train = position_rows[position_rows["target_season"].isin(train_seasons)].copy()
        test = position_rows[position_rows["target_season"] == test_season].copy()
        if len(train) < 20 or len(test) < 3:
            continue
        pred_points = _ridge_predict(train, test, feature_columns, "next_nwr_points")
        pred_ppg = _ridge_predict(train, test, feature_columns, "next_nwr_ppg")
        for (_, row), points, ppg in zip(test.iterrows(), pred_points, pred_ppg, strict=False):
            rows.append(
                {
                    "feature_set": feature_set,
                    "position": position,
                    "player_id": row["player_id"],
                    "player_name": row.get("target_player_name", ""),
                    "target_season": int(row["target_season"]),
                    "actual_points": float(row["next_nwr_points"]),
                    "predicted_points": float(points),
                    "actual_ppg": float(row["next_nwr_ppg"]),
                    "predicted_ppg": float(ppg),
                    "target_games": float(row.get("target_games", 0)),
                }
            )
    return rows


def _ridge_predict(
    train: pd.DataFrame,
    test: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    alpha: float = 1.0,
) -> np.ndarray:
    columns = [column for column in feature_columns if column in train.columns]
    if not columns:
        return np.full(len(test), float(train[target_column].mean()))
    x_train = train[columns].apply(pd.to_numeric, errors="coerce")
    x_test = test[columns].apply(pd.to_numeric, errors="coerce")
    medians = x_train.median(numeric_only=True).fillna(0)
    x_train = x_train.fillna(medians)
    x_test = x_test.fillna(medians)
    means = x_train.mean()
    stds = x_train.std(ddof=0).replace(0, 1)
    x_train = (x_train - means) / stds
    x_test = (x_test - means) / stds
    train_matrix = np.c_[np.ones(len(x_train)), x_train.to_numpy(dtype=float)]
    test_matrix = np.c_[np.ones(len(x_test)), x_test.to_numpy(dtype=float)]
    y = pd.to_numeric(train[target_column], errors="coerce").fillna(0).to_numpy(dtype=float)
    penalty = np.eye(train_matrix.shape[1]) * alpha
    penalty[0, 0] = 0
    try:
        beta = np.linalg.solve(train_matrix.T @ train_matrix + penalty, train_matrix.T @ y)
    except np.linalg.LinAlgError:
        beta = np.linalg.pinv(train_matrix.T @ train_matrix + penalty) @ train_matrix.T @ y
    return test_matrix @ beta


def _metrics_by_position(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (feature_set, position), group in predictions.groupby(["feature_set", "position"]):
        rows.append(_metric_row(group, feature_set, position, target_season="ALL"))
    output = pd.DataFrame(rows)
    baseline = output[output["feature_set"] == "baseline"][
        ["position", "mae_points", "rmse_points", "spearman_points", "top_n_hit_rate"]
    ]
    baseline = baseline.rename(
        columns={
            "mae_points": "baseline_mae_points",
            "rmse_points": "baseline_rmse_points",
            "spearman_points": "baseline_spearman_points",
            "top_n_hit_rate": "baseline_top_n_hit_rate",
        }
    )
    output = output.merge(baseline, on="position", how="left")
    output["mae_improvement_vs_baseline"] = output["baseline_mae_points"] - output["mae_points"]
    output["rmse_improvement_vs_baseline"] = output["baseline_rmse_points"] - output["rmse_points"]
    output["spearman_improvement_vs_baseline"] = (
        output["spearman_points"] - output["baseline_spearman_points"]
    )
    output["top_n_hit_rate_improvement_vs_baseline"] = (
        output["top_n_hit_rate"] - output["baseline_top_n_hit_rate"]
    )
    return output


def _metrics_by_year(
    prediction_rows: list[dict[str, Any]], feature_set: str, position: str
) -> list[dict[str, Any]]:
    frame = pd.DataFrame(prediction_rows)
    rows = []
    if frame.empty:
        return rows
    for season, group in frame.groupby("target_season"):
        rows.append(_metric_row(group, feature_set, position, target_season=int(season)))
    return rows


def _metric_row(
    group: pd.DataFrame, feature_set: str, position: str, target_season: Any
) -> dict[str, Any]:
    actual = pd.to_numeric(group["actual_points"], errors="coerce").fillna(0)
    pred = pd.to_numeric(group["predicted_points"], errors="coerce").fillna(0)
    actual_ppg = pd.to_numeric(group["actual_ppg"], errors="coerce").fillna(0)
    pred_ppg = pd.to_numeric(group["predicted_ppg"], errors="coerce").fillna(0)
    errors = pred - actual
    ppg_errors = pred_ppg - actual_ppg
    return {
        "feature_set": feature_set,
        "position": position,
        "target_season": target_season,
        "sample_size": len(group),
        "seasons_evaluated": ",".join(
            str(int(season)) for season in sorted(group["target_season"].unique())
        ),
        "mae_points": float(errors.abs().mean()),
        "rmse_points": float(math.sqrt(float((errors**2).mean()))),
        "spearman_points": _spearman(actual, pred),
        "mae_ppg": float(ppg_errors.abs().mean()),
        "rmse_ppg": float(math.sqrt(float((ppg_errors**2).mean()))),
        "spearman_ppg": _spearman(actual_ppg, pred_ppg),
        "top_n_hit_rate": _top_n_hit_rate(group, TOP_N_BY_POSITION.get(position, 12)),
    }


def _spearman(actual: pd.Series, pred: pd.Series) -> float:
    if len(actual) < 2:
        return 0.0
    value = actual.rank().corr(pred.rank())
    return 0.0 if pd.isna(value) else float(value)


def _top_n_hit_rate(group: pd.DataFrame, top_n: int) -> float:
    if group.empty:
        return 0.0
    n = min(top_n, len(group))
    actual_top = set(group.sort_values("actual_points", ascending=False).head(n)["player_id"])
    pred_top = set(group.sort_values("predicted_points", ascending=False).head(n)["player_id"])
    return len(actual_top & pred_top) / n if n else 0.0


def _run_manifest(
    *,
    dataset_dir: Path,
    output_dir: Path,
    baseline: pd.DataFrame,
    expanded: pd.DataFrame,
    labels: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics_by_position: pd.DataFrame,
    metrics_by_year: pd.DataFrame,
    files: dict[str, Path],
) -> dict[str, Any]:
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "purpose": "local_only_backtest_v0_evaluation",
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "positions": list(CORE_POSITIONS),
        "target_seasons": sorted(int(season) for season in labels["target_season"].unique()),
        "feature_sets": ["baseline", "expanded_factual"],
        "methods": ["rolling_origin_numpy_ridge"],
        "sklearn_used": False,
        "yellow_challenger_results": "not_run",
        "input_rows": {
            "baseline": len(baseline),
            "expanded": len(expanded),
            "labels": len(labels),
            "predictions": len(predictions),
        },
        "blocked_feature_tokens_enforced": list(BLOCKED_FEATURE_TOKENS),
        "yellow_challenger_tokens_excluded": list(YELLOW_CHALLENGER_TOKENS),
        "forbidden_use": [
            "private_value",
            "rankings",
            "hidden_sort",
            "recommendations",
            "simulations",
            "final_draft_decisions",
            "deployment",
            "latest_approved",
        ],
        "expanded_improvement_summary": _improvement_summary(metrics_by_position),
        "files": {name: _file_record(path) for name, path in files.items()},
    }


def _improvement_summary(metrics: pd.DataFrame) -> dict[str, Any]:
    expanded = metrics[metrics["feature_set"] == "expanded_factual"].copy()
    return {
        str(row["position"]): {
            "mae_improvement_vs_baseline": float(row["mae_improvement_vs_baseline"]),
            "rmse_improvement_vs_baseline": float(row["rmse_improvement_vs_baseline"]),
            "spearman_improvement_vs_baseline": float(row["spearman_improvement_vs_baseline"]),
            "top_n_hit_rate_improvement_vs_baseline": float(
                row["top_n_hit_rate_improvement_vs_baseline"]
            ),
        }
        for _, row in expanded.iterrows()
    }


def _markdown_report(manifest: dict[str, Any], metrics: pd.DataFrame) -> str:
    lines = [
        "# NWR Backtest V0 Local Report",
        "",
        "## Scope",
        "",
        "Local-only, backtest-only evaluation. This is not private value, rankings, "
        "hidden sort, recommendations, simulations, final draft decisions, deployment, "
        "or `latest_approved` approval.",
        "",
        "## Run Summary",
        "",
        f"- Dataset dir: `{manifest['dataset_dir']}`",
        f"- Target seasons: `{', '.join(str(season) for season in manifest['target_seasons'])}`",
        f"- Positions: `{', '.join(manifest['positions'])}`",
        f"- Method: `{', '.join(manifest['methods'])}`",
        f"- sklearn used: `{manifest['sklearn_used']}`",
        f"- YELLOW challenger results: `{manifest['yellow_challenger_results']}`",
        "",
        "## Metrics By Position",
        "",
        "| Feature set | Position | N | MAE points | RMSE points | Spearman | Top-N hit |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in metrics.sort_values(["position", "feature_set"]).iterrows():
        lines.append(
            f"| `{row['feature_set']}` | `{row['position']}` | {int(row['sample_size'])} | "
            f"{row['mae_points']:.3f} | {row['rmse_points']:.3f} | "
            f"{row['spearman_points']:.3f} | {row['top_n_hit_rate']:.3f} |"
        )
    lines.extend(["", "## Expanded Feature Improvement Versus Baseline", ""])
    for position, values in manifest["expanded_improvement_summary"].items():
        lines.append(
            f"- `{position}`: MAE {values['mae_improvement_vs_baseline']:.3f}, "
            f"RMSE {values['rmse_improvement_vs_baseline']:.3f}, "
            f"Spearman {values['spearman_improvement_vs_baseline']:.3f}, "
            f"Top-N {values['top_n_hit_rate_improvement_vs_baseline']:.3f}."
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- ADP, market, ranking, projection, and trade-calculator fields were not used.",
            "- `fantasy_points` and `fantasy_points_ppr` were not used as input features.",
            "- YELLOW challenger fields were excluded from main feature sets.",
            "- Outputs are local-only and outside Git.",
        ]
    )
    return "\n".join(lines) + "\n"


def _file_record(path: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {
        "path": str(path),
        "row_count": _csv_row_count(path),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


if __name__ == "__main__":
    raise SystemExit(main())
