from __future__ import annotations

import csv
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.nwr_outcome_feature_snapshot_service import canonical_feature_name

ALLOWED_OUTCOMES = (
    "same_year_difference_maker",
    "same_year_starter",
    "same_year_useful",
    "same_year_replacement_or_bust",
)

BLOCKED_OUTCOMES = (
    "next_year_starter",
    "multi_year_outcomes",
    "hazard_windows",
)

BASE_ALLOWED_FEATURES = (
    "age_at_snapshot",
    "position",
    "experience_at_snapshot",
    "prior_season_nwr_ppg",
    "prior_season_nwr_finish_rank",
    "prior_completed_season_games",
    "prior_completed_season_games_played",
    "prior_completed_season_games_active",
    "prior_completed_season_rushing_first_downs",
    "prior_completed_season_receiving_first_downs",
    "prior_completed_season_receptions",
    "prior_completed_season_rushing_yards",
    "prior_completed_season_receiving_yards",
    "prior_completed_season_passing_yards",
)

FORBIDDEN_FEATURE_FRAGMENTS = (
    "prior_nwr_ppg",
    "prior_nwr_finish_rank",
    "prior_games_played",
    "prior_games_active",
    "prior_rushing_first_downs",
    "prior_receiving_first_downs",
    "prior_receptions",
    "prior_rushing_yards",
    "prior_receiving_yards",
    "prior_passing_yards",
    "same_season",
    "target_label",
    "public_fantasy",
    "fantasy_points",
    "adp",
    "projection",
    "ranking",
    "rankings",
    "market",
    "trade",
    "prior_fantasy_draft_history",
    "private_score",
    "label_supplement",
)

PACKAGE_METADATA = {
    "run_id": "sprint_5t_internal_logistic_2023_train_2024_test",
    "feature_schema_version": "sprint_5r_renamed_lineage_schema_v1",
    "label_schema_version": "nwr_same_year_outcome_labels_v1",
    "benchmark_policy_id": "nwr_v0_internal_benchmark_policy_20260611",
    "component_policy_id": "truth_set_v0_component_supplemented_internal_v1",
    "source_manifest_version": "sprint_5n_broader_historical_rebuild",
    "training_seasons": [2023],
    "test_seasons": [2024],
    "row_family": "all_player_pre_week1",
    "outcomes": list(ALLOWED_OUTCOMES),
    "renamed_feature_schema_required": True,
    "feature_lineage_required": True,
    "player_output_block": True,
    "app_output_block": True,
    "promotion_allowed": False,
    "calibration_allowed": False,
    "production_artifact": False,
}


@dataclass(frozen=True)
class InternalDatasetRow:
    target_season: int
    features: dict[str, Any]
    labels: dict[str, int]


@dataclass(frozen=True)
class LogisticResult:
    outcome: str
    coefficients: dict[str, float]
    metrics: dict[str, Any]
    bin_rows: tuple[dict[str, Any], ...]


def export_sprint_5t_internal_logistic_package(
    *, repo_root: str | Path, output_dir: str | Path
) -> dict[str, Any]:
    repo = Path(repo_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows = load_internal_dataset(
        feature_snapshot_path=repo
        / "local_exports/outcome_probability/sprint_5n_broader_historical_rebuild"
        / "broader_historical_feature_snapshots.csv",
        label_linkage_path=repo
        / "local_exports/outcome_probability/sprint_5n_broader_historical_rebuild"
        / "broader_historical_label_linkage.csv",
    )
    feature_list = available_feature_list(rows)
    scan_rows = forbidden_feature_scan(feature_list)
    if any(row["blocker"] == "yes" for row in scan_rows):
        _write_csv(
            output / "forbidden_feature_scan.csv",
            scan_rows,
            ("feature_name", "scan_status", "matched_fragment", "blocker", "notes"),
        )
        raise ValueError("Forbidden feature names are present in canonical feature list.")

    metadata = {
        **PACKAGE_METADATA,
        "feature_list": feature_list,
        "forbidden_feature_scan_passed": True,
        "training_row_count": sum(1 for row in rows if row.target_season == 2023),
        "test_row_count": sum(1 for row in rows if row.target_season == 2024),
    }
    _validate_metadata_contract(metadata)

    results = [
        fit_regularized_logistic(
            rows=rows,
            outcome=outcome,
            feature_list=feature_list,
            train_season=2023,
            test_season=2024,
        )
        for outcome in ALLOWED_OUTCOMES
    ]

    _write_json(output / "internal_logistic_package_metadata.json", metadata)
    _write_csv(
        output / "internal_logistic_outcome_metrics.csv",
        [result.metrics for result in results],
        (
            "run_id",
            "outcome",
            "model_family",
            "train_season",
            "test_season",
            "train_rows",
            "test_rows",
            "train_event_count",
            "test_event_count",
            "aggregate_predicted_mean",
            "observed_rate",
            "brier_score",
            "log_loss",
            "calibration_layer",
            "model_artifact_saved",
            "player_level_predictions_exported",
            "notes",
        ),
    )
    _write_csv(
        output / "internal_logistic_bin_summary.csv",
        [row for result in results for row in result.bin_rows],
        (
            "run_id",
            "outcome",
            "model_family",
            "test_season",
            "bin_id",
            "row_count",
            "predicted_mean",
            "observed_rate",
            "event_count",
            "non_event_count",
            "min_predicted",
            "max_predicted",
            "notes",
        ),
    )
    _write_csv(
        output / "internal_logistic_coefficient_sanity.csv",
        coefficient_rows(results),
        (
            "run_id",
            "outcome",
            "model_family",
            "feature_name",
            "coefficient",
            "abs_coefficient_rank",
            "coefficient_direction",
            "notes",
        ),
    )
    _write_csv(
        output / "internal_logistic_feature_sanity.csv",
        feature_sanity_rows(rows, feature_list),
        (
            "feature_name",
            "feature_type",
            "non_missing_count",
            "missing_count",
            "mean_or_levels",
            "allowed_status",
            "notes",
        ),
    )
    _write_csv(
        output / "blocked_output_audit.csv",
        blocked_output_audit_rows(),
        ("output_path", "blocked_status", "reason", "verification"),
    )
    _write_csv(
        output / "forbidden_feature_scan.csv",
        scan_rows,
        ("feature_name", "scan_status", "matched_fragment", "blocker", "notes"),
    )
    _write_csv(
        output / "production_readiness_blockers.csv",
        production_readiness_blockers(),
        ("blocker", "status", "notes"),
    )
    _write_readme(output, metadata, results)
    return {
        "metadata": metadata,
        "results": results,
        "verdict": "INTERNAL_LOGISTIC_PACKAGE_PASS_WITH_WARNINGS",
    }


def load_internal_dataset(
    *, feature_snapshot_path: str | Path, label_linkage_path: str | Path
) -> tuple[InternalDatasetRow, ...]:
    snapshots = _read_csv(Path(feature_snapshot_path))
    labels_by_row_id = {
        row["row_id"]: row
        for row in _read_csv(Path(label_linkage_path))
        if row.get("trainability_status") == "trainable_now"
    }
    rows: list[InternalDatasetRow] = []
    for snapshot in snapshots:
        label = labels_by_row_id.get(snapshot.get("row_id", ""))
        if not label:
            continue
        target_season = _int(label.get("target_season"))
        if target_season not in (2023, 2024):
            continue
        row_type = label.get("row_type") or snapshot.get("row_type")
        if row_type != "all_player_pre_week1":
            continue
        features = canonical_feature_vector(json.loads(snapshot["feature_vector"]))
        labels = {outcome: _bool_int(label.get(outcome)) for outcome in ALLOWED_OUTCOMES}
        rows.append(
            InternalDatasetRow(
                target_season=target_season,
                features=features,
                labels=labels,
            )
        )
    return tuple(rows)


def canonical_feature_vector(feature_vector: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, Any] = {}
    for feature_name, value in feature_vector.items():
        new_name = canonical_feature_name(feature_name)
        if new_name in BASE_ALLOWED_FEATURES:
            canonical[new_name] = value
    return canonical


def available_feature_list(rows: Sequence[InternalDatasetRow]) -> list[str]:
    features = sorted({feature for row in rows for feature in row.features})
    return [feature for feature in features if feature in BASE_ALLOWED_FEATURES]


def validate_feature_contract(feature_list: Sequence[str]) -> None:
    blockers = forbidden_feature_scan(feature_list)
    if any(row["blocker"] == "yes" for row in blockers):
        raise ValueError("Feature list contains forbidden or ambiguous feature names.")


def forbidden_feature_scan(feature_list: Sequence[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for feature_name in feature_list:
        normalized = feature_name.lower()
        matched = next(
            (fragment for fragment in FORBIDDEN_FEATURE_FRAGMENTS if fragment in normalized),
            "",
        )
        rows.append(
            {
                "feature_name": feature_name,
                "scan_status": "fail" if matched else "pass",
                "matched_fragment": matched,
                "blocker": "yes" if matched else "no",
                "notes": (
                    "Forbidden or ambiguous feature fragment detected."
                    if matched
                    else "No forbidden feature fragment detected."
                ),
            }
        )
    return rows


def fit_regularized_logistic(
    *,
    rows: Sequence[InternalDatasetRow],
    outcome: str,
    feature_list: Sequence[str],
    train_season: int,
    test_season: int,
) -> LogisticResult:
    if outcome in BLOCKED_OUTCOMES or outcome not in ALLOWED_OUTCOMES:
        raise ValueError(f"Outcome is not allowed for Sprint 5T: {outcome}")
    train_rows = [row for row in rows if row.target_season == train_season]
    test_rows = [row for row in rows if row.target_season == test_season]
    feature_names = design_feature_names(rows, feature_list)
    raw_x_train = [design_vector(row, feature_names, feature_list) for row in train_rows]
    y_train = [row.labels[outcome] for row in train_rows]
    raw_x_test = [design_vector(row, feature_names, feature_list) for row in test_rows]
    y_test = [row.labels[outcome] for row in test_rows]
    x_train, x_test = _standardize_train_test(raw_x_train, raw_x_test)
    weights = _fit_logistic_weights(x_train, y_train, l2=0.15, learning_rate=0.08, steps=900)
    train_predictions = [_sigmoid(_dot(weights, x)) for x in x_train]
    test_predictions = [_sigmoid(_dot(weights, x)) for x in x_test]
    metrics = {
        "run_id": PACKAGE_METADATA["run_id"],
        "outcome": outcome,
        "model_family": "regularized_logistic_mechanics",
        "train_season": train_season,
        "test_season": test_season,
        "train_rows": len(train_rows),
        "test_rows": len(test_rows),
        "train_event_count": sum(y_train),
        "test_event_count": sum(y_test),
        "aggregate_predicted_mean": _round(_mean(test_predictions)),
        "observed_rate": _round(_mean(y_test)),
        "brier_score": _round(_brier(test_predictions, y_test)),
        "log_loss": _round(_log_loss(test_predictions, y_test)),
        "calibration_layer": "none",
        "model_artifact_saved": "no",
        "player_level_predictions_exported": "no",
        "notes": "Internal mechanics only; no calibration, promotion, or player output.",
    }
    coefficients = dict(zip(feature_names, weights, strict=True))
    coefficients["train_log_loss"] = _log_loss(train_predictions, y_train)
    return LogisticResult(
        outcome=outcome,
        coefficients=coefficients,
        metrics=metrics,
        bin_rows=tuple(
            bin_summary_rows(
                outcome=outcome,
                predictions=test_predictions,
                labels=y_test,
                test_season=test_season,
            )
        ),
    )


def design_feature_names(
    rows: Sequence[InternalDatasetRow], feature_list: Sequence[str]
) -> tuple[str, ...]:
    positions = sorted(
        {
            str(row.features.get("position", "UNK")).upper()
            for row in rows
            if row.features.get("position")
        }
    )
    numeric = [feature for feature in feature_list if feature != "position"]
    return tuple(["intercept", *numeric, *[f"position_{position}" for position in positions]])


def design_vector(
    row: InternalDatasetRow, feature_names: Sequence[str], feature_list: Sequence[str]
) -> list[float]:
    values: list[float] = []
    position = str(row.features.get("position", "UNK")).upper()
    for feature_name in feature_names:
        if feature_name == "intercept":
            values.append(1.0)
        elif feature_name.startswith("position_"):
            values.append(1.0 if feature_name == f"position_{position}" else 0.0)
        elif feature_name in feature_list:
            values.append(_float(row.features.get(feature_name)))
        else:
            values.append(0.0)
    return values


def coefficient_rows(results: Sequence[LogisticResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        ordered = sorted(
            (
                (name, value)
                for name, value in result.coefficients.items()
                if name != "train_log_loss"
            ),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        for rank, (feature_name, coefficient) in enumerate(ordered):
            rows.append(
                {
                    "run_id": PACKAGE_METADATA["run_id"],
                    "outcome": result.outcome,
                    "model_family": "regularized_logistic_mechanics",
                    "feature_name": feature_name,
                    "coefficient": _round(coefficient),
                    "abs_coefficient_rank": rank,
                    "coefficient_direction": "positive" if coefficient >= 0 else "negative",
                    "notes": "Coefficient sanity only; no model promotion.",
                }
            )
    return rows


def feature_sanity_rows(
    rows: Sequence[InternalDatasetRow], feature_list: Sequence[str]
) -> list[dict[str, Any]]:
    sanity_rows: list[dict[str, Any]] = []
    for feature_name in feature_list:
        values = [row.features.get(feature_name) for row in rows]
        non_missing = [value for value in values if value not in (None, "")]
        if feature_name == "position":
            levels = sorted({str(value).upper() for value in non_missing})
            mean_or_levels = "|".join(levels)
            feature_type = "categorical"
        else:
            numeric = [_float(value) for value in non_missing]
            mean_or_levels = _round(_mean(numeric)) if numeric else ""
            feature_type = "numeric"
        sanity_rows.append(
            {
                "feature_name": feature_name,
                "feature_type": feature_type,
                "non_missing_count": len(non_missing),
                "missing_count": len(values) - len(non_missing),
                "mean_or_levels": mean_or_levels,
                "allowed_status": "allowed_internal_mechanics",
                "notes": "Renamed Sprint 5R feature schema.",
            }
        )
    return sanity_rows


def bin_summary_rows(
    *, outcome: str, predictions: Sequence[float], labels: Sequence[int], test_season: int
) -> list[dict[str, Any]]:
    paired = sorted(zip(predictions, labels, strict=True), key=lambda item: item[0])
    if not paired:
        return []
    bin_count = min(10, len(paired))
    rows: list[dict[str, Any]] = []
    for index in range(bin_count):
        start = index * len(paired) // bin_count
        end = (index + 1) * len(paired) // bin_count
        chunk = paired[start:end]
        preds = [item[0] for item in chunk]
        ys = [item[1] for item in chunk]
        events = sum(ys)
        rows.append(
            {
                "run_id": PACKAGE_METADATA["run_id"],
                "outcome": outcome,
                "model_family": "regularized_logistic_mechanics",
                "test_season": test_season,
                "bin_id": index + 1,
                "row_count": len(chunk),
                "predicted_mean": _round(_mean(preds)),
                "observed_rate": _round(_mean(ys)),
                "event_count": events,
                "non_event_count": len(chunk) - events,
                "min_predicted": _round(min(preds)),
                "max_predicted": _round(max(preds)),
                "notes": "Aggregate bin only; no player identifiers.",
            }
        )
    return rows


def blocked_output_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "output_path": "player_level_predictions",
            "blocked_status": "blocked",
            "reason": "Per-player probabilities forbidden.",
            "verification": "No such export is created.",
        },
        {
            "output_path": "app_probability_table",
            "blocked_status": "blocked",
            "reason": "App-readable probability tables forbidden.",
            "verification": "No app path or app table is touched.",
        },
        {
            "output_path": "production_model_artifact",
            "blocked_status": "blocked",
            "reason": "Promotion/release forbidden.",
            "verification": "No model pickle/joblib/json artifact is written.",
        },
        {
            "output_path": "rankings_or_sortable_scores",
            "blocked_status": "blocked",
            "reason": "Rankings forbidden.",
            "verification": "Aggregate diagnostics only.",
        },
    ]


def production_readiness_blockers() -> list[dict[str, str]]:
    return [
        {
            "blocker": "more_seasons_beyond_2023_2024",
            "status": "not_met",
            "notes": "Only one train/test diagnostic split exists.",
        },
        {
            "blocker": "true_calibration_holdout",
            "status": "not_met",
            "notes": "No calibration layer is allowed in Sprint 5T.",
        },
        {
            "blocker": "mature_next_year_or_multi_year_labels",
            "status": "not_met",
            "notes": "next_year_starter remains blocked/censored.",
        },
        {
            "blocker": "confidence_and_app_display_gates",
            "status": "not_met",
            "notes": "No app-facing display gate exists.",
        },
        {
            "blocker": "final_leakage_audit_and_hq_approval",
            "status": "not_met",
            "notes": "Required before app-facing calibrated probabilities.",
        },
    ]


def _validate_metadata_contract(metadata: Mapping[str, Any]) -> None:
    required = (
        "run_id",
        "feature_schema_version",
        "label_schema_version",
        "benchmark_policy_id",
        "component_policy_id",
        "source_manifest_version",
        "training_seasons",
        "test_seasons",
        "row_family",
        "outcomes",
        "feature_list",
        "renamed_feature_schema_required",
        "feature_lineage_required",
        "forbidden_feature_scan_passed",
        "player_output_block",
        "app_output_block",
        "promotion_allowed",
        "calibration_allowed",
        "production_artifact",
    )
    missing = [field for field in required if field not in metadata]
    if missing:
        raise ValueError(f"Missing metadata fields: {', '.join(missing)}")
    if metadata["promotion_allowed"] is not False:
        raise ValueError("promotion_allowed must be false.")
    if metadata["player_output_block"] is not True:
        raise ValueError("player_output_block must be true.")
    if metadata["app_output_block"] is not True:
        raise ValueError("app_output_block must be true.")
    if metadata["calibration_allowed"] is not False:
        raise ValueError("calibration_allowed must be false.")
    if metadata["production_artifact"] is not False:
        raise ValueError("production_artifact must be false.")
    validate_feature_contract(metadata["feature_list"])


def _fit_logistic_weights(
    x_rows: Sequence[Sequence[float]],
    labels: Sequence[int],
    *,
    l2: float,
    learning_rate: float,
    steps: int,
) -> list[float]:
    weights = [0.0 for _ in x_rows[0]]
    for _ in range(steps):
        gradients = [0.0 for _ in weights]
        for x, y in zip(x_rows, labels, strict=True):
            error = _sigmoid(_dot(weights, x)) - y
            for index, value in enumerate(x):
                gradients[index] += error * value
        count = float(len(x_rows))
        for index in range(len(weights)):
            penalty = 0.0 if index == 0 else l2 * weights[index]
            weights[index] -= learning_rate * ((gradients[index] / count) + penalty)
    return weights


def _standardize_train_test(
    x_train: Sequence[Sequence[float]],
    x_test: Sequence[Sequence[float]],
) -> tuple[list[list[float]], list[list[float]]]:
    if not x_train:
        return [], []
    column_count = len(x_train[0])
    means = [0.0 for _ in range(column_count)]
    scales = [1.0 for _ in range(column_count)]
    for index in range(1, column_count):
        values = [row[index] for row in x_train]
        mean = _mean(values)
        variance = _mean([(value - mean) ** 2 for value in values])
        means[index] = mean
        scales[index] = math.sqrt(variance) or 1.0

    def transform(rows: Sequence[Sequence[float]]) -> list[list[float]]:
        transformed: list[list[float]] = []
        for row in rows:
            transformed.append(
                [
                    value if index == 0 else (value - means[index]) / scales[index]
                    for index, value in enumerate(row)
                ]
            )
        return transformed

    return transform(x_train), transform(x_test)


def _write_readme(
    output: Path, metadata: Mapping[str, Any], results: Sequence[LogisticResult]
) -> None:
    lines = [
        "# Sprint 5T Internal Logistic Package",
        "",
        "Verdict: `INTERNAL_LOGISTIC_PACKAGE_PASS_WITH_WARNINGS`",
        "",
        "This local-only packet contains aggregate internal logistic mechanics diagnostics. "
        "It does not contain player-level predictions, app probabilities, rankings, "
        "calibration artifacts, or production model artifacts.",
        "",
        "## Metadata",
        "",
        f"- run_id: `{metadata['run_id']}`",
        f"- feature_schema_version: `{metadata['feature_schema_version']}`",
        f"- train/test: `{metadata['training_seasons']}` -> `{metadata['test_seasons']}`",
        f"- promotion_allowed: `{str(metadata['promotion_allowed']).lower()}`",
        f"- calibration_allowed: `{str(metadata['calibration_allowed']).lower()}`",
        "",
        "## Outcomes",
    ]
    for result in results:
        lines.append(
            f"- `{result.outcome}`: predicted mean {result.metrics['aggregate_predicted_mean']} "
            f"vs observed {result.metrics['observed_rate']}"
        )
    lines.extend(
        [
            "",
            "`next_year_starter` remains blocked.",
            "",
            "Production/app modeling remains blocked.",
        ]
    )
    (output / "README_SPRINT_5T.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], headers: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _bool_int(value: Any) -> int:
    return 1 if str(value).strip().lower() in {"true", "1", "yes"} else 0


def _int(value: Any) -> int:
    return int(str(value))


def _float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _dot(weights: Sequence[float], values: Sequence[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, values, strict=True))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _mean(values: Sequence[float | int]) -> float:
    return sum(values) / len(values) if values else 0.0


def _brier(predictions: Sequence[float], labels: Sequence[int]) -> float:
    return _mean([(pred - label) ** 2 for pred, label in zip(predictions, labels, strict=True)])


def _log_loss(predictions: Sequence[float], labels: Sequence[int]) -> float:
    epsilon = 1e-12
    losses = []
    for pred, label in zip(predictions, labels, strict=True):
        clipped = min(max(pred, epsilon), 1.0 - epsilon)
        losses.append(-(label * math.log(clipped) + (1 - label) * math.log(1 - clipped)))
    return _mean(losses)


def _round(value: float) -> float:
    return round(float(value), 6)
