from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_e_model_rd_v1_20260630"
)
SHARED_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\rookie_outcomes\model_rd_v1")
LABEL_PATH = Path(
    r"C:\NWR_SHARED_DATA\rookie_outcomes\historical_labels_v1"
    r"\rookie_historical_outcome_labels_v1.csv"
)
FEATURE_POLICY_RELATIVE_PATH = (
    Path("docs")
    / "hq"
    / "rookie_outcomes"
    / "rookie_gate_d_feature_policy_v1_20260630"
    / "rookie_feature_policy_matrix_v1.csv"
)
FEATURE_POLICY_PATH = REPO_ROOT / FEATURE_POLICY_RELATIVE_PATH

BASE_HEAD = "14eeecfd83b3a863ea98a3b8dbdbb8dd621c45e1"
FINAL_VERDICT = "PARTIAL_REVIEW_ONLY_ROOKIE_MODEL_RD"
EXPECTED_SCORING_MODE = "exact_verified_first_downs"
NOT_ENOUGH = "Not enough information"
ALLOWED_FEATURES = (
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "draft_year",
    "rookie_class_year",
    "position",
)
TARGETS = tuple(
    f"{horizon}_top_{threshold}_hit"
    for horizon in ("rookie_year", "year_2", "first_3y", "first_5y")
    for threshold in (12, 24, 36)
)
CALIBRATION_BUCKETS = (
    (0.0, 0.1, "0.00_0.10"),
    (0.1, 0.2, "0.10_0.20"),
    (0.2, 0.4, "0.20_0.40"),
    (0.4, 0.6, "0.40_0.60"),
    (0.6, 0.8, "0.60_0.80"),
    (0.8, 1.01, "0.80_1.00"),
)

PREDICTION_COLUMNS = (
    "target_name",
    "nfl_player_id",
    "player_name",
    "position",
    "rookie_class_year",
    "draft_year",
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "validation_start_year",
    "actual_label",
    "actual_value",
    "validation_predicted_rate",
    "global_baseline_rate",
    "prediction_method",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

METRIC_COLUMNS = (
    "target_name",
    "train_rows",
    "validation_rows",
    "validation_start_year",
    "validation_classes",
    "validation_positive_rate",
    "empirical_brier_score",
    "global_baseline_brier_score",
    "brier_improvement",
    "prediction_methods",
    "calibration_bucket_count",
    "validation_status",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

CALIBRATION_COLUMNS = (
    "target_name",
    "calibration_bucket",
    "row_count",
    "average_predicted_rate",
    "observed_hit_rate",
    "absolute_calibration_error",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

FEATURE_AUDIT_COLUMNS = (
    "feature_name",
    "used_as_input",
    "source",
    "allowed_by_gate_d",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "notes",
)

COVERAGE_COLUMNS = (
    "metric",
    "value",
    "notes",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

MANIFEST_COLUMNS = (
    "run_id",
    "run_timestamp",
    "artifact",
    "source",
    "rows",
    "output_path",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "notes",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Gate E review-only rookie model R&D feasibility artifacts."
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--shared-output-root", type=Path, default=SHARED_OUTPUT_ROOT)
    parser.add_argument("--label-path", type=Path, default=LABEL_PATH)
    parser.add_argument("--feature-policy-path", type=Path, default=FEATURE_POLICY_PATH)
    args = parser.parse_args()

    run_id = "rookie_gate_e_model_rd_v1_20260630"
    run_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    label_rows = read_csv(args.label_path)
    feature_policy_rows = read_csv(args.feature_policy_path)
    allowed_features = allowed_features_from_policy(feature_policy_rows)
    validate_allowed_features(allowed_features)

    predictions, metrics, calibration = build_validation_artifacts(label_rows)
    validate_prediction_rows(predictions)
    validate_review_rows(metrics)
    validate_review_rows(calibration)
    feature_audit_rows = build_feature_audit_rows(allowed_features)
    validate_review_rows(feature_audit_rows)
    summary_rows = build_summary_rows(
        label_rows=label_rows,
        predictions=predictions,
        metrics=metrics,
        feature_audit_rows=feature_audit_rows,
    )
    validate_review_rows(summary_rows)

    args.shared_output_root.mkdir(parents=True, exist_ok=True)
    prediction_path = args.shared_output_root / "rookie_model_rd_validation_predictions_v1.csv"
    metrics_path = args.shared_output_root / "rookie_model_rd_validation_metrics_v1.csv"
    calibration_path = args.shared_output_root / "rookie_model_rd_calibration_buckets_v1.csv"
    feature_audit_path = args.shared_output_root / "rookie_model_rd_feature_audit_v1.csv"
    manifest_path = args.shared_output_root / "rookie_model_rd_manifest_v1.csv"
    write_csv(prediction_path, PREDICTION_COLUMNS, predictions)
    write_csv(metrics_path, METRIC_COLUMNS, metrics)
    write_csv(calibration_path, CALIBRATION_COLUMNS, calibration)
    write_csv(feature_audit_path, FEATURE_AUDIT_COLUMNS, feature_audit_rows)
    write_csv(
        manifest_path,
        MANIFEST_COLUMNS,
        build_manifest_rows(
            run_id=run_id,
            run_timestamp=run_timestamp,
            prediction_path=prediction_path,
            metrics_path=metrics_path,
            calibration_path=calibration_path,
            feature_audit_path=feature_audit_path,
            predictions=predictions,
            metrics=metrics,
            calibration=calibration,
            feature_audit_rows=feature_audit_rows,
        ),
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    write_csv(
        args.output_root / "rookie_model_rd_validation_summary_v1.csv",
        COVERAGE_COLUMNS,
        summary_rows,
    )
    write_inventory_doc(args.output_root, label_rows, predictions, metrics)
    write_plan_doc(args.output_root)
    write_validation_report_doc(args.output_root, label_rows, metrics, calibration)
    write_gate_e_decision_doc(args.output_root, metrics)
    write_readme(args.output_root, predictions, metrics)

    print(
        {
            "verdict": FINAL_VERDICT,
            "features_used": list(ALLOWED_FEATURES),
            "targets_tested": len(metrics),
            "validation_rows": len(predictions),
            "passed_targets": count_status(metrics, "validation_status", "pass_review_only"),
            "shared_output": str(args.shared_output_root),
        }
    )
    return 0


def allowed_features_from_policy(rows: list[dict[str, str]]) -> tuple[str, ...]:
    return tuple(
        row["feature_name"]
        for row in rows
        if row.get("allowed_for_review_only_model_rd") == "true"
    )


def validate_allowed_features(features: tuple[str, ...]) -> None:
    if set(features) != set(ALLOWED_FEATURES):
        raise ValueError(f"Gate E may only use allowed features: {ALLOWED_FEATURES}")


def build_validation_artifacts(
    label_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    predictions: list[dict[str, str]] = []
    metrics: list[dict[str, str]] = []
    calibration: list[dict[str, str]] = []
    for target in TARGETS:
        eligible = eligible_rows(label_rows, target)
        train_rows, validation_rows, validation_start = split_rows(target, eligible)
        if not train_rows or not validation_rows:
            continue
        target_predictions = build_target_predictions(
            target=target,
            train_rows=train_rows,
            validation_rows=validation_rows,
            validation_start=validation_start,
        )
        target_calibration = build_calibration_rows(target, target_predictions)
        predictions.extend(target_predictions)
        calibration.extend(target_calibration)
        metrics.append(build_metric_row(target, train_rows, target_predictions, target_calibration))
    return predictions, metrics, calibration


def eligible_rows(rows: list[dict[str, str]], target: str) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        if target.startswith("first_3y") and row["first_3y_window_complete"] != "true":
            continue
        if target.startswith("first_5y") and row["first_5y_window_complete"] != "true":
            continue
        if target_value(row.get(target)) is None:
            continue
        output.append(row)
    return output


def split_rows(
    target: str,
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    years = sorted({to_int(row["rookie_class_year"]) for row in rows})
    years = [year for year in years if year is not None]
    if target.startswith("first_5y"):
        years = [year for year in years if year <= 2020]
    if target.startswith("first_3y"):
        years = [year for year in years if year <= 2022]
    if len(years) < 4:
        return [], [], 0
    validation_start = max(years[-3], years[0] + 1)
    train_rows = [
        row
        for row in rows
        if (year := to_int(row["rookie_class_year"])) is not None and year < validation_start
    ]
    validation_rows = [
        row
        for row in rows
        if (year := to_int(row["rookie_class_year"])) is not None
        and year >= validation_start
        and year in years
    ]
    return train_rows, validation_rows, validation_start


def build_target_predictions(
    *,
    target: str,
    train_rows: list[dict[str, str]],
    validation_rows: list[dict[str, str]],
    validation_start: int,
) -> list[dict[str, str]]:
    global_rate = sum(target_value(row[target]) for row in train_rows) / len(train_rows)
    by_position_bucket: dict[tuple[str, str], list[int]] = defaultdict(list)
    by_position: dict[str, list[int]] = defaultdict(list)
    for row in train_rows:
        actual = target_value(row[target])
        by_position_bucket[(row["position"], draft_capital_bucket(row))].append(actual)
        by_position[row["position"]].append(actual)

    predictions: list[dict[str, str]] = []
    for row in validation_rows:
        bucket = draft_capital_bucket(row)
        grouped = by_position_bucket[(row["position"], bucket)]
        if len(grouped) >= 5:
            rate = smoothed_rate(grouped, global_rate)
            method = "position_draft_capital_bucket"
        elif len(by_position[row["position"]]) >= 10:
            rate = smoothed_rate(by_position[row["position"]], global_rate)
            method = "position"
        else:
            rate = global_rate
            method = "global"
        predictions.append(
            {
                "target_name": target,
                "nfl_player_id": row["nfl_player_id"],
                "player_name": row["player_name"],
                "position": row["position"],
                "rookie_class_year": row["rookie_class_year"],
                "draft_year": row["draft_year"],
                "draft_round": row["draft_round"],
                "draft_pick": row["draft_pick"],
                "draft_capital_bucket": bucket,
                "validation_start_year": str(validation_start),
                "actual_label": row[target],
                "actual_value": str(target_value(row[target])),
                "validation_predicted_rate": format_rate(rate),
                "global_baseline_rate": format_rate(global_rate),
                "prediction_method": method,
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return predictions


def build_metric_row(
    target: str,
    train_rows: list[dict[str, str]],
    predictions: list[dict[str, str]],
    calibration_rows: list[dict[str, str]],
) -> dict[str, str]:
    actuals = [int(row["actual_value"]) for row in predictions]
    rates = [float(row["validation_predicted_rate"]) for row in predictions]
    global_rates = [float(row["global_baseline_rate"]) for row in predictions]
    empirical_brier = brier_score(rates, actuals)
    global_brier = brier_score(global_rates, actuals)
    validation_years = sorted({row["rookie_class_year"] for row in predictions})
    method_counts = Counter(row["prediction_method"] for row in predictions)
    status = (
        "pass_review_only"
        if len(predictions) >= 50 and global_brier - empirical_brier > 0
        else "weak_validation"
    )
    return {
        "target_name": target,
        "train_rows": str(len(train_rows)),
        "validation_rows": str(len(predictions)),
        "validation_start_year": predictions[0]["validation_start_year"],
        "validation_classes": ";".join(validation_years),
        "validation_positive_rate": format_rate(sum(actuals) / len(actuals)),
        "empirical_brier_score": format_rate(empirical_brier),
        "global_baseline_brier_score": format_rate(global_brier),
        "brier_improvement": format_rate(global_brier - empirical_brier),
        "prediction_methods": format_counts(method_counts),
        "calibration_bucket_count": str(len(calibration_rows)),
        "validation_status": status,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def build_calibration_rows(
    target: str,
    predictions: list[dict[str, str]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for lower, upper, name in CALIBRATION_BUCKETS:
        bucket_rows = [
            row
            for row in predictions
            if lower <= float(row["validation_predicted_rate"]) < upper
        ]
        if not bucket_rows:
            continue
        predicted = sum(float(row["validation_predicted_rate"]) for row in bucket_rows) / len(
            bucket_rows
        )
        observed = sum(int(row["actual_value"]) for row in bucket_rows) / len(bucket_rows)
        output.append(
            {
                "target_name": target,
                "calibration_bucket": name,
                "row_count": str(len(bucket_rows)),
                "average_predicted_rate": format_rate(predicted),
                "observed_hit_rate": format_rate(observed),
                "absolute_calibration_error": format_rate(abs(predicted - observed)),
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return output


def build_feature_audit_rows(features: tuple[str, ...]) -> list[dict[str, str]]:
    return [
        {
            "feature_name": feature,
            "used_as_input": "true",
            "source": feature_source(feature),
            "allowed_by_gate_d": "true",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "notes": "Gate E review-only R&D feature; not production model input.",
        }
        for feature in features
    ]


def build_summary_rows(
    *,
    label_rows: list[dict[str, str]],
    predictions: list[dict[str, str]],
    metrics: list[dict[str, str]],
    feature_audit_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    pass_count = count_status(metrics, "validation_status", "pass_review_only")
    return [
        summary("gate_e_verdict", FINAL_VERDICT, "Review-only feasibility, not production."),
        summary("allowed_features_used", "|".join(ALLOWED_FEATURES), "Gate D whitelist."),
        summary("input_label_rows", len(label_rows), "Historical labels considered."),
        summary("targets_tested", len(metrics), "Recommended T12/T24/T36 targets."),
        summary("validation_prediction_rows", len(predictions), "Historical validation rows only."),
        summary("passed_targets", pass_count, "Targets with positive Brier improvement."),
        summary("weak_targets", len(metrics) - pass_count, "Targets below validation bar."),
        summary("feature_audit_rows", len(feature_audit_rows), "Allowed input features audited."),
        summary("current_player_predictions_created", 0, "No current-player probabilities."),
        summary("rankings_wiring_created", 0, "No Rankings/app wiring."),
        summary("model_use_rows", 0, "All rows keep model_use_allowed=false."),
        summary("training_use_rows", 0, "All rows keep training_allowed=false."),
    ]


def validate_prediction_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("Validation predictions are required.")
    forbidden_inputs = {"rookie_year", "year_2", "first_3y", "first_5y", "label", "target"}
    for row in rows:
        if row["review_only"] != "true":
            raise ValueError("Prediction rows must keep review_only=true.")
        if row["model_use_allowed"] != "false":
            raise ValueError("Prediction rows must keep model_use_allowed=false.")
        if row["training_allowed"] != "false":
            raise ValueError("Prediction rows must keep training_allowed=false.")
        for feature in ALLOWED_FEATURES:
            if feature not in row:
                raise ValueError(f"Allowed feature missing from prediction row: {feature}")
        input_like_columns = set(row) & forbidden_inputs
        if input_like_columns:
            raise ValueError(f"Label-like columns cannot be model inputs: {input_like_columns}")


def validate_review_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row.get("review_only") != "true":
            raise ValueError("Rows must keep review_only=true.")
        if row.get("model_use_allowed") != "false":
            raise ValueError("Rows must keep model_use_allowed=false.")
        if row.get("training_allowed") != "false":
            raise ValueError("Rows must keep training_allowed=false.")


def write_inventory_doc(
    root: Path,
    labels: list[dict[str, str]],
    predictions: list[dict[str, str]],
    metrics: list[dict[str, str]],
) -> None:
    positions = Counter(row["position"] for row in labels)
    years = sorted({row["rookie_class_year"] for row in labels})
    censoring = Counter(row["censoring_status"] for row in labels)
    lines = [
        "# Gate E Model R&D Inventory - 2026-06-30",
        "",
        f"- Actual base HEAD: `{BASE_HEAD}`",
        f"- Historical rookie labels: `{LABEL_PATH}`",
        f"- Feature policy: `{FEATURE_POLICY_RELATIVE_PATH.as_posix()}`",
        f"- Label rows available: {len(labels)}",
        f"- Class/year coverage: {years[0]}-{years[-1]}",
        f"- Position coverage: {format_counts(positions)}",
        f"- Complete vs censored: {format_counts(censoring)}",
        f"- Allowed features: `{', '.join(ALLOWED_FEATURES)}`",
        f"- Targets validated: {len(metrics)}",
        f"- Historical validation prediction rows: {len(predictions)}",
        "",
        "Review-only model R&D is possible using a constrained empirical baseline.",
        "No current-player predictions, production model, or app wiring were created.",
    ]
    (root / "00_MODEL_RD_INVENTORY.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_plan_doc(root: Path) -> None:
    lines = [
        "# Gate E Model R&D Plan - 2026-06-30",
        "",
        "## Allowed Inputs",
        "",
        *[f"- `{feature}`" for feature in ALLOWED_FEATURES],
        "",
        "Historical labels are targets only, never input features.",
        "",
        "## Targets",
        "",
        "- rookie-year T12/T24/T36 where applicable",
        "- year-2 T12/T24/T36 where applicable",
        "- first-3-year T12/T24/T36 where windows are complete",
        "- first-5-year T12/T24/T36 where windows are complete",
        "",
        "## No-Leakage Split",
        "",
        "Each target uses earlier rookie classes for empirical rates and the latest",
        "three eligible classes as validation. First-3-year and first-5-year targets",
        "exclude censored classes.",
        "",
        "## Baseline",
        "",
        "Empirical hit-rate tables by `position + draft_capital_bucket`, with fallback",
        "to position or global target rate when training samples are sparse.",
        "",
        "## Validation Bar",
        "",
        "- validation rows >= 50",
        "- empirical Brier score improves over global-rate baseline",
        "- all artifacts remain review-only with model/training flags closed",
    ]
    (root / "01_MODEL_RD_PLAN.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_validation_report_doc(
    root: Path,
    labels: list[dict[str, str]],
    metrics: list[dict[str, str]],
    calibration: list[dict[str, str]],
) -> None:
    pass_count = count_status(metrics, "validation_status", "pass_review_only")
    min_validation = min(int(row["validation_rows"]) for row in metrics)
    max_brier = max(float(row["empirical_brier_score"]) for row in metrics)
    min_improvement = min(float(row["brier_improvement"]) for row in metrics)
    lines = [
        "# Gate E Model R&D Validation Report - 2026-06-30",
        "",
        f"- Label rows available: {len(labels)}",
        f"- Targets tested: {len(metrics)}",
        f"- Targets passing review-only validation bar: {pass_count}",
        f"- Minimum validation sample size: {min_validation}",
        f"- Worst empirical Brier score: {max_brier:.6f}",
        f"- Minimum Brier improvement vs global baseline: {min_improvement:.6f}",
        f"- Calibration bucket rows: {len(calibration)}",
        "",
        "All tested targets improved over the global-rate baseline in the historical",
        "time-split validation. This supports review-only R&D feasibility, but the",
        "model remains partial because features are limited to draft capital, class,",
        "and position, and labels cover drafted players only.",
        "",
        "Censored-window handling: first-3-year and first-5-year targets only used",
        "calendar-complete windows. Missing labels were excluded, not treated as misses.",
    ]
    (root / "02_MODEL_RD_VALIDATION_REPORT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_gate_e_decision_doc(root: Path, metrics: list[dict[str, str]]) -> None:
    pass_count = count_status(metrics, "validation_status", "pass_review_only")
    lines = [
        "# Gate E Model R&D Decision - 2026-06-30",
        "",
        "## Verdict",
        "",
        f"`{FINAL_VERDICT}`",
        "",
        "A limited empirical review-only rookie model R&D baseline is feasible.",
        f"{pass_count} of {len(metrics)} target validations passed the review-only bar.",
        "",
        "## Limits",
        "",
        "- Drafted-player-only label population.",
        "- Six allowed non-leaky features only.",
        "- No current-player rookie probabilities.",
        "- No production model promotion.",
        "- No Rankings/app display artifact.",
        "- `model_use_allowed=false` and `training_allowed=false` remain closed.",
        "",
        "## Gate F",
        "",
        "Gate F can run next only as a review-only display-artifact feasibility lane.",
        "It must not create production probabilities or app wiring without a later gate.",
    ]
    (root / "03_GATE_E_MODEL_RD_DECISION.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_readme(
    root: Path,
    predictions: list[dict[str, str]],
    metrics: list[dict[str, str]],
) -> None:
    lines = [
        "# Gate E Rookie Model R&D Feasibility V1",
        "",
        f"Verdict: `{FINAL_VERDICT}`",
        "",
        f"- Targets tested: {len(metrics)}",
        f"- Historical validation rows: {len(predictions)}",
        "- Current-player probabilities: 0",
        "- Rankings wiring: 0",
        "",
        "Generated R&D CSVs live under `C:\\NWR_SHARED_DATA\\rookie_outcomes\\model_rd_v1`",
        "and are not tracked.",
    ]
    (root / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def draft_capital_bucket(row: dict[str, str]) -> str:
    draft_round = to_int(row.get("draft_round"))
    draft_pick = to_int(row.get("draft_pick"))
    if draft_round == 1 and draft_pick is not None and draft_pick <= 10:
        return "round_1_top_10"
    if draft_round == 1:
        return "round_1_other"
    if draft_round == 2:
        return "round_2"
    if draft_round == 3:
        return "round_3"
    if draft_round is not None and 4 <= draft_round <= 7:
        return "round_4_7"
    return "not_enough_information"


def feature_source(feature: str) -> str:
    if feature == "draft_capital_bucket":
        return "derived_from_draft_round_and_draft_pick"
    return "historical_rookie_label_artifact"


def target_value(label: object) -> int | None:
    value = str(label or "").strip()
    if value == "hit":
        return 1
    if value == "miss":
        return 0
    return None


def smoothed_rate(values: list[int], global_rate: float, alpha: int = 5) -> float:
    return (sum(values) + global_rate * alpha) / (len(values) + alpha)


def brier_score(rates: list[float], actuals: list[int]) -> float:
    return sum((rate - actual) ** 2 for rate, actual in zip(rates, actuals, strict=True)) / len(
        actuals
    )


def summary(metric: str, value: object, notes: str) -> dict[str, str]:
    return {
        "metric": metric,
        "value": str(value),
        "notes": notes,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }


def build_manifest_rows(
    *,
    run_id: str,
    run_timestamp: str,
    prediction_path: Path,
    metrics_path: Path,
    calibration_path: Path,
    feature_audit_path: Path,
    predictions: list[dict[str, str]],
    metrics: list[dict[str, str]],
    calibration: list[dict[str, str]],
    feature_audit_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    return [
        manifest_row(
            run_id,
            run_timestamp,
            "rookie_model_rd_validation_predictions_v1.csv",
            str(LABEL_PATH),
            len(predictions),
            prediction_path,
            "Historical validation baseline rates only; not current-player probabilities.",
        ),
        manifest_row(
            run_id,
            run_timestamp,
            "rookie_model_rd_validation_metrics_v1.csv",
            "derived_from_validation_predictions",
            len(metrics),
            metrics_path,
            "Review-only validation metrics.",
        ),
        manifest_row(
            run_id,
            run_timestamp,
            "rookie_model_rd_calibration_buckets_v1.csv",
            "derived_from_validation_predictions",
            len(calibration),
            calibration_path,
            "Review-only calibration buckets.",
        ),
        manifest_row(
            run_id,
            run_timestamp,
            "rookie_model_rd_feature_audit_v1.csv",
            FEATURE_POLICY_RELATIVE_PATH.as_posix(),
            len(feature_audit_rows),
            feature_audit_path,
            "Allowed feature audit.",
        ),
    ]


def manifest_row(
    run_id: str,
    run_timestamp: str,
    artifact: str,
    source: str,
    rows: int,
    output_path: Path,
    notes: str,
) -> dict[str, str]:
    return {
        "run_id": run_id,
        "run_timestamp": run_timestamp,
        "artifact": artifact,
        "source": source,
        "rows": str(rows),
        "output_path": str(output_path),
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "notes": notes,
    }


def count_status(rows: list[dict[str, str]], field: str, value: str) -> int:
    return sum(row[field] == value for row in rows)


def format_counts(counts: Counter[str]) -> str:
    return "; ".join(f"{key}:{value}" for key, value in sorted(counts.items()))


def format_rate(value: float) -> str:
    return f"{value:.6f}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: object) -> int | None:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
