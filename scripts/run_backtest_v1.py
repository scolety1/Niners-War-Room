from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_backtest_dataset_v0 import BASELINE_NUMERIC_COLUMNS, CORE_POSITIONS
from scripts.build_backtest_dataset_v1 import (
    V1_BASELINE_FEATURES_BY_POSITION,
    V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
    BacktestBuildError,
    _validate_v1_feature_columns,
)
from scripts.run_backtest_v0 import (
    BacktestRunError,
    _metric_row,
    _ridge_predict,
)


@dataclass(frozen=True)
class BacktestV1RunResult:
    output_dir: Path
    metrics_by_position_path: Path
    metrics_by_year_path: Path
    report_path: Path
    manifest_path: Path
    metrics_by_position: pd.DataFrame
    metrics_by_year: pd.DataFrame


def run_backtest_v1(
    *,
    dataset_dir: Path,
    output_dir: Path | None = None,
    min_train_seasons: int = 2,
) -> BacktestV1RunResult:
    output = output_dir or dataset_dir
    output.mkdir(parents=True, exist_ok=True)
    baseline = pd.read_csv(dataset_dir / "feature_dataset_v1_baseline.csv")
    clean_expanded = pd.read_csv(dataset_dir / "feature_dataset_v1_clean_expanded.csv")
    labels = pd.read_csv(dataset_dir / "labels_v1.csv")
    _validate_inputs_v1(baseline, clean_expanded, labels)

    rows: list[dict[str, Any]] = []
    year_rows: list[dict[str, Any]] = []
    feature_specs = [
        ("v0_baseline_reference", baseline, None),
        ("v1_baseline", baseline, V1_BASELINE_FEATURES_BY_POSITION),
        ("v1_clean_expanded", clean_expanded, V1_CLEAN_EXPANDED_FEATURES_BY_POSITION),
    ]
    for feature_set_name, features, feature_map in feature_specs:
        merged = features.merge(labels, on=["player_id", "target_season"], how="inner")
        for position in CORE_POSITIONS:
            position_rows = merged[merged["target_position"] == position].copy()
            if position_rows.empty:
                continue
            if feature_map is None:
                feature_columns = [
                    column for column in BASELINE_NUMERIC_COLUMNS if column in position_rows
                ]
            else:
                feature_columns = [
                    column for column in feature_map[position] if column in position_rows
                ]
            prediction_rows = _rolling_predictions_v1(
                position_rows=position_rows,
                feature_columns=feature_columns,
                feature_set=feature_set_name,
                position=position,
                min_train_seasons=min_train_seasons,
            )
            rows.extend(prediction_rows)
            year_rows.extend(_metrics_by_year_v1(prediction_rows, feature_set_name, position))

    predictions = pd.DataFrame(rows)
    if predictions.empty:
        raise BacktestRunError("no rolling-origin predictions were produced")
    metrics_by_position = _metrics_by_position_v1(predictions)
    metrics_by_year = pd.DataFrame(year_rows)

    metrics_by_position_path = output / "metrics_by_position_v1.csv"
    metrics_by_year_path = output / "metrics_by_year_v1.csv"
    predictions_path = output / "predictions_v1.csv"
    report_path = output / "backtest_v1_feature_cleanup_report.md"
    manifest_path = output / "run_manifest.json"

    predictions.to_csv(predictions_path, index=False, encoding="utf-8")
    metrics_by_position.to_csv(metrics_by_position_path, index=False, encoding="utf-8")
    metrics_by_year.to_csv(metrics_by_year_path, index=False, encoding="utf-8")
    manifest = _run_manifest_v1(
        dataset_dir=dataset_dir,
        output_dir=output,
        baseline=baseline,
        clean_expanded=clean_expanded,
        labels=labels,
        predictions=predictions,
        metrics_by_position=metrics_by_position,
        metrics_by_year=metrics_by_year,
        files={
            "metrics_by_position_v1.csv": metrics_by_position_path,
            "metrics_by_year_v1.csv": metrics_by_year_path,
            "predictions_v1.csv": predictions_path,
        },
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report_path.write_text(_markdown_report_v1(manifest, metrics_by_position), encoding="utf-8")
    return BacktestV1RunResult(
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
        description="Run local-only Backtest V1 feature-cleanup evaluation."
    )
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--min-train-seasons", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run_backtest_v1(
            dataset_dir=args.dataset_dir,
            output_dir=args.output_dir,
            min_train_seasons=args.min_train_seasons,
        )
    except Exception as exc:
        print(f"Backtest V1 run failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"output_dir={result.output_dir}")
    print(f"metrics_by_position={result.metrics_by_position_path}")
    print(f"metrics_by_year={result.metrics_by_year_path}")
    print(f"report={result.report_path}")
    print(f"manifest={result.manifest_path}")
    return 0


def _validate_inputs_v1(
    baseline: pd.DataFrame,
    clean_expanded: pd.DataFrame,
    labels: pd.DataFrame,
) -> None:
    for name, frame in {
        "baseline": baseline,
        "clean_expanded": clean_expanded,
        "labels": labels,
    }.items():
        if frame.empty:
            raise BacktestRunError(f"{name} dataset is empty")
    try:
        _validate_v1_feature_columns(baseline.columns)
        _validate_v1_feature_columns(clean_expanded.columns)
    except BacktestBuildError as exc:
        raise BacktestRunError(str(exc)) from exc
    required_label_columns = {
        "player_id",
        "target_season",
        "target_player_name",
        "target_position",
        "target_team",
        "target_games",
        "next_nwr_points",
        "next_nwr_ppg",
    }
    missing = sorted(required_label_columns.difference(labels.columns))
    if missing:
        raise BacktestRunError(f"labels missing columns: {missing}")


def _rolling_predictions_v1(
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
                    "feature_count": len(feature_columns),
                }
            )
    return rows


def _metrics_by_position_v1(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (feature_set, position), group in predictions.groupby(["feature_set", "position"]):
        rows.append(_metric_row(group, feature_set, position, target_season="ALL"))
    output = pd.DataFrame(rows)
    for reference_name in ("v0_baseline_reference", "v1_baseline"):
        reference = output[output["feature_set"] == reference_name][
            ["position", "mae_points", "rmse_points", "spearman_points", "top_n_hit_rate"]
        ].rename(
            columns={
                "mae_points": f"{reference_name}_mae_points",
                "rmse_points": f"{reference_name}_rmse_points",
                "spearman_points": f"{reference_name}_spearman_points",
                "top_n_hit_rate": f"{reference_name}_top_n_hit_rate",
            }
        )
        output = output.merge(reference, on="position", how="left")
        output[f"mae_improvement_vs_{reference_name}"] = (
            output[f"{reference_name}_mae_points"] - output["mae_points"]
        )
        output[f"rmse_improvement_vs_{reference_name}"] = (
            output[f"{reference_name}_rmse_points"] - output["rmse_points"]
        )
        output[f"spearman_improvement_vs_{reference_name}"] = (
            output["spearman_points"] - output[f"{reference_name}_spearman_points"]
        )
        output[f"top_n_hit_rate_improvement_vs_{reference_name}"] = (
            output["top_n_hit_rate"] - output[f"{reference_name}_top_n_hit_rate"]
        )
    output["v1_success_vs_baseline"] = output.apply(_success_label, axis=1)
    return output


def _metrics_by_year_v1(
    prediction_rows: list[dict[str, Any]], feature_set: str, position: str
) -> list[dict[str, Any]]:
    frame = pd.DataFrame(prediction_rows)
    rows = []
    if frame.empty:
        return rows
    for season, group in frame.groupby("target_season"):
        rows.append(_metric_row(group, feature_set, position, target_season=int(season)))
    return rows


def _success_label(row: pd.Series) -> str:
    if row["feature_set"] != "v1_clean_expanded":
        return "reference"
    improvements = [
        row.get("mae_improvement_vs_v1_baseline", 0) > 0,
        row.get("rmse_improvement_vs_v1_baseline", 0) > 0,
        row.get("spearman_improvement_vs_v1_baseline", 0) > 0,
        row.get("top_n_hit_rate_improvement_vs_v1_baseline", 0) > 0,
    ]
    severe_worse = (
        row.get("mae_improvement_vs_v1_baseline", 0) < -2
        or row.get("rmse_improvement_vs_v1_baseline", 0) < -2
        or row.get("spearman_improvement_vs_v1_baseline", 0) < -0.03
        or row.get("top_n_hit_rate_improvement_vs_v1_baseline", 0) < -0.05
    )
    if sum(improvements) >= 2 and not severe_worse:
        return "improved"
    return "baseline_preferred"


def _run_manifest_v1(
    *,
    dataset_dir: Path,
    output_dir: Path,
    baseline: pd.DataFrame,
    clean_expanded: pd.DataFrame,
    labels: pd.DataFrame,
    predictions: pd.DataFrame,
    metrics_by_position: pd.DataFrame,
    metrics_by_year: pd.DataFrame,
    files: dict[str, Path],
) -> dict[str, Any]:
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "purpose": "local_only_backtest_v1_feature_cleanup_evaluation",
        "dataset_dir": str(dataset_dir),
        "output_dir": str(output_dir),
        "positions": list(CORE_POSITIONS),
        "target_seasons": sorted(int(season) for season in labels["target_season"].unique()),
        "feature_sets": [
            "v0_baseline_reference",
            "v1_baseline",
            "v1_clean_expanded",
        ],
        "methods": ["rolling_origin_numpy_ridge"],
        "sklearn_used": False,
        "yellow_challenger_results": "not_run",
        "input_rows": {
            "baseline": len(baseline),
            "clean_expanded": len(clean_expanded),
            "labels": len(labels),
            "predictions": len(predictions),
        },
        "success_summary_vs_v1_baseline": _success_summary(metrics_by_position),
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
        "files": {name: _file_record(path) for name, path in files.items()},
        "metrics_rows": len(metrics_by_position),
        "metrics_by_year_rows": len(metrics_by_year),
    }


def _success_summary(metrics: pd.DataFrame) -> dict[str, Any]:
    clean = metrics[metrics["feature_set"] == "v1_clean_expanded"].copy()
    return {
        str(row["position"]): {
            "mae_improvement_vs_v1_baseline": float(row["mae_improvement_vs_v1_baseline"]),
            "rmse_improvement_vs_v1_baseline": float(row["rmse_improvement_vs_v1_baseline"]),
            "spearman_improvement_vs_v1_baseline": float(
                row["spearman_improvement_vs_v1_baseline"]
            ),
            "top_n_hit_rate_improvement_vs_v1_baseline": float(
                row["top_n_hit_rate_improvement_vs_v1_baseline"]
            ),
            "verdict": row["v1_success_vs_baseline"],
        }
        for _, row in clean.iterrows()
    }


def _markdown_report_v1(manifest: dict[str, Any], metrics: pd.DataFrame) -> str:
    lines = [
        "# NWR Backtest V1 Feature Cleanup Local Report",
        "",
        "## Scope",
        "",
        "Local-only, backtest-only feature cleanup evaluation. This is not private "
        "value, rankings, hidden sort, recommendations, simulations, final draft "
        "decisions, deployment, Mock Draft logic, or `latest_approved` approval.",
        "",
        "## Run Summary",
        "",
        f"- Dataset dir: `{manifest['dataset_dir']}`",
        f"- Target seasons: `{', '.join(str(season) for season in manifest['target_seasons'])}`",
        f"- Positions: `{', '.join(manifest['positions'])}`",
        f"- Method: `{', '.join(manifest['methods'])}`",
        "- YELLOW challenger results: `not_run`",
        "",
        "## Metrics By Position",
        "",
        "| Feature set | Position | N | MAE points | RMSE points | Spearman | "
        "Top-N hit | V1 verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for _, row in metrics.sort_values(["position", "feature_set"]).iterrows():
        lines.append(
            f"| `{row['feature_set']}` | `{row['position']}` | {int(row['sample_size'])} | "
            f"{row['mae_points']:.3f} | {row['rmse_points']:.3f} | "
            f"{row['spearman_points']:.3f} | {row['top_n_hit_rate']:.3f} | "
            f"`{row['v1_success_vs_baseline']}` |"
        )
    lines.extend(["", "## Clean Expanded Improvement Versus V1 Baseline", ""])
    for position, values in manifest["success_summary_vs_v1_baseline"].items():
        lines.append(
            f"- `{position}`: MAE {values['mae_improvement_vs_v1_baseline']:.3f}, "
            f"RMSE {values['rmse_improvement_vs_v1_baseline']:.3f}, "
            f"Spearman {values['spearman_improvement_vs_v1_baseline']:.3f}, "
            f"Top-N {values['top_n_hit_rate_improvement_vs_v1_baseline']:.3f}; "
            f"verdict `{values['verdict']}`."
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- ADP, market, ranking, projection, and trade-calculator fields were not used.",
            "- `fantasy_points` and `fantasy_points_ppr` were not used as input features.",
            "- YELLOW challenger fields were excluded from primary V1 feature sets.",
            "- Preprocessing statistics were fit inside train folds only.",
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
