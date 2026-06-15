"""Sprint 5CO local-only aggregate shadow model evaluation.

This script evaluates 5CN-approved heads with rolling historical holdouts and
writes only aggregate metrics. It never writes row/player-level predictions,
current-player scores, app-readable outputs, production models, rankings, hidden
sort keys, or promoted artifacts.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTCOME_EXPORT_ROOT = REPO_ROOT / "local_exports" / "outcome_probability"
RUN_ID = "sprint_5co_local_only_aggregate_shadow_model_evaluation"
OUT_DIR = OUTCOME_EXPORT_ROOT / RUN_ID

PACKAGE_CONFIGS = [
    ("5CI", "2010_2011", OUTCOME_EXPORT_ROOT / "sprint_5ci_2010_2011_historical_feature_label_rebuild"),
    ("5CF", "2012_2013", OUTCOME_EXPORT_ROOT / "sprint_5cf_2012_2013_historical_feature_label_rebuild"),
    ("5CC", "2014_2015", OUTCOME_EXPORT_ROOT / "sprint_5cc_2014_2015_historical_feature_label_rebuild"),
    ("5BZ", "2016_2017", OUTCOME_EXPORT_ROOT / "sprint_5bz_2016_2017_historical_feature_label_rebuild"),
    ("5BV", "2018_2019", OUTCOME_EXPORT_ROOT / "sprint_5bv_2018_2019_historical_feature_label_rebuild"),
]

ELIGIBLE_HEADS = {
    "QB": ["same_year_qb_t12", "same_year_qb_t18", "same_year_qb_t24"],
    "RB": ["same_year_rb_t12", "same_year_rb_t24", "same_year_rb_t36", "same_year_rb_t48"],
    "WR": ["same_year_wr_t12", "same_year_wr_t24", "same_year_wr_t36", "same_year_wr_t48"],
    "TE": ["same_year_te_t12", "same_year_te_t18", "same_year_te_t24"],
}

WEAK_NOT_EVALUATED = [
    "same_year_qb_t6",
    "same_year_rb_t6",
    "same_year_wr_t6",
    "same_year_te_t3",
    "same_year_te_t6",
]

FOLDS = [
    (tuple(range(2010, 2016)), 2016),
    (tuple(range(2010, 2017)), 2017),
    (tuple(range(2010, 2018)), 2018),
    (tuple(range(2010, 2019)), 2019),
]

APPROVED_FEATURES = [
    "prior_completed_season_games",
    "prior_completed_season_games_active",
    "prior_completed_season_games_played",
    "prior_completed_season_passing_yards",
    "prior_completed_season_receiving_first_downs",
    "prior_completed_season_receiving_yards",
    "prior_completed_season_receptions",
    "prior_completed_season_rushing_first_downs",
    "prior_completed_season_rushing_yards",
    "prior_season_nwr_finish_rank",
    "prior_season_nwr_ppg",
]

FORBIDDEN_FEATURE_TERMS = [
    "fantasy",
    "epa",
    "wopr",
    "racr",
    "pacr",
    "dakota",
    "target_share",
    "air_yards_share",
    "adp",
    "ranking",
    "projection",
    "market",
    "trade",
    "rotowire",
    "private_score",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sprint, seasons, base in PACKAGE_CONFIGS:
        features_path = base / f"historical_{seasons}_feature_snapshots.csv"
        labels_path = base / f"historical_{seasons}_outcome_labels.csv"
        if not features_path.exists() or not labels_path.exists():
            raise FileNotFoundError(f"Missing local package files for {sprint}: {base}")
        features = {row["row_id"]: row for row in read_csv(features_path)}
        labels = {row["row_id"]: row for row in read_csv(labels_path)}
        for row_id, feature_row in features.items():
            label_row = labels.get(row_id)
            if label_row is None:
                continue
            feature_vector = json.loads(feature_row["feature_vector"])
            threshold_labels = json.loads(label_row["threshold_labels_json"])
            rows.append(
                {
                    "sprint": sprint,
                    "row_id": row_id,
                    "target_season": int(feature_row["target_season"]),
                    "position": feature_row["position"],
                    "feature_vector": feature_vector,
                    "threshold_labels": threshold_labels,
                }
            )
    return rows


def feature_values(row: dict[str, object]) -> list[float]:
    feature_vector = row["feature_vector"]
    if not isinstance(feature_vector, dict):
        raise TypeError("feature_vector must be a dict")
    return [float(feature_vector[name]) for name in APPROVED_FEATURES]


def standardize(train_x: list[list[float]], holdout_x: list[list[float]]) -> tuple[list[list[float]], list[list[float]]]:
    cols = len(train_x[0])
    means = [mean(row[col] for row in train_x) for col in range(cols)]
    stds: list[float] = []
    for col in range(cols):
        variance = mean((row[col] - means[col]) ** 2 for row in train_x)
        stds.append(math.sqrt(variance) or 1.0)
    return (
        [[(value - means[col]) / stds[col] for col, value in enumerate(row)] for row in train_x],
        [[(value - means[col]) / stds[col] for col, value in enumerate(row)] for row in holdout_x],
    )


def fit_logistic(train_x: list[list[float]], train_y: list[int]) -> list[float]:
    x, _ = standardize(train_x, train_x)
    weights = [0.0 for _ in range(len(x[0]) + 1)]
    lr = 0.08
    l2 = 0.01
    for _ in range(140):
        gradients = [0.0 for _ in weights]
        for values, target in zip(x, train_y, strict=True):
            z = weights[0] + sum(weight * value for weight, value in zip(weights[1:], values, strict=True))
            pred = sigmoid(z)
            err = pred - target
            gradients[0] += err
            for index, value in enumerate(values, start=1):
                gradients[index] += err * value
        scale = 1 / len(x)
        weights[0] -= lr * gradients[0] * scale
        for index in range(1, len(weights)):
            weights[index] -= lr * ((gradients[index] * scale) + (l2 * weights[index]))
    return weights


def logistic_predict(train_x: list[list[float]], holdout_x: list[list[float]], weights: list[float]) -> list[float]:
    _, x = standardize(train_x, holdout_x)
    preds: list[float] = []
    for values in x:
        z = weights[0] + sum(weight * value for weight, value in zip(weights[1:], values, strict=True))
        preds.append(sigmoid(z))
    return preds


def auc_score(y_true: list[int], scores: list[float]) -> float | None:
    positives = sum(y_true)
    negatives = len(y_true) - positives
    if positives == 0 or negatives == 0:
        return None
    pairs = sorted(zip(scores, y_true, strict=True), key=lambda item: item[0])
    rank_sum = 0.0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and pairs[end][0] == pairs[index][0]:
            end += 1
        avg_rank = (index + 1 + end) / 2
        for _, target in pairs[index:end]:
            if target == 1:
                rank_sum += avg_rank
        index = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def average_precision(y_true: list[int], scores: list[float]) -> float | None:
    positives = sum(y_true)
    if positives == 0:
        return None
    sorted_pairs = sorted(zip(scores, y_true, strict=True), key=lambda item: item[0], reverse=True)
    found = 0
    precision_sum = 0.0
    for rank, (_, target) in enumerate(sorted_pairs, start=1):
        if target == 1:
            found += 1
            precision_sum += found / rank
    return precision_sum / positives


def brier(y_true: list[int], probs: list[float]) -> float:
    return mean((prob - target) ** 2 for prob, target in zip(probs, y_true, strict=True))


def log_loss(y_true: list[int], probs: list[float]) -> float:
    eps = 1e-6
    losses = []
    for prob, target in zip(probs, y_true, strict=True):
        p = min(max(prob, eps), 1 - eps)
        losses.append(-(target * math.log(p) + (1 - target) * math.log(1 - p)))
    return mean(losses)


def calibration_summary(y_true: list[int], probs: list[float], bins: int = 5) -> tuple[int, int, float | None]:
    bucket_totals: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for target, prob in zip(y_true, probs, strict=True):
        bucket = min(bins - 1, int(prob * bins))
        bucket_totals[bucket].append((target, prob))
    populated = 0
    thin = 0
    max_gap = 0.0
    for values in bucket_totals.values():
        if not values:
            continue
        populated += 1
        if len(values) < 10:
            thin += 1
        observed = mean(target for target, _ in values)
        predicted = mean(prob for _, prob in values)
        max_gap = max(max_gap, abs(observed - predicted))
    return populated, thin, max_gap if populated else None


def metric_value(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()

    feature_audit_rows = []
    for feature_name in APPROVED_FEATURES:
        feature_audit_rows.append(
            {
                "output_scope": "internal_only_not_app_readable",
                "feature": feature_name,
                "approved_by_5cn": "yes",
                "forbidden_term_match": "|".join(
                    term for term in FORBIDDEN_FEATURE_TERMS if term in feature_name.lower()
                ),
                "used_in_5co": "yes",
            }
        )
    forbidden_failures = [row for row in feature_audit_rows if row["forbidden_term_match"]]

    aggregate_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    for position, heads in ELIGIBLE_HEADS.items():
        position_rows = [row for row in rows if row["position"] == position]
        for head in heads:
            for fold_index, (train_seasons, holdout_season) in enumerate(FOLDS, start=1):
                train = [row for row in position_rows if row["target_season"] in train_seasons]
                holdout = [row for row in position_rows if row["target_season"] == holdout_season]
                train = [row for row in train if head in row["threshold_labels"]]
                holdout = [row for row in holdout if head in row["threshold_labels"]]
                train_y = [1 if row["threshold_labels"][head] else 0 for row in train]
                holdout_y = [1 if row["threshold_labels"][head] else 0 for row in holdout]
                train_x = [feature_values(row) for row in train]
                holdout_x = [feature_values(row) for row in holdout]
                train_pos = sum(train_y)
                holdout_pos = sum(holdout_y)
                train_neg = len(train_y) - train_pos
                holdout_neg = len(holdout_y) - holdout_pos
                can_score = train_pos > 0 and train_neg > 0 and holdout_pos > 0 and holdout_neg > 0

                base_prob = train_pos / len(train_y) if train_y else 0.0
                base_probs = [base_prob for _ in holdout_y]
                prior_rank_scores = [
                    -float(row["feature_vector"]["prior_season_nwr_finish_rank"]) for row in holdout
                ]
                prior_ppg_scores = [
                    float(row["feature_vector"]["prior_season_nwr_ppg"]) for row in holdout
                ]

                methods = [
                    ("base_rate_train_fold", base_probs, "probability"),
                    ("prior_rank_score", prior_rank_scores, "score"),
                    ("prior_ppg_score", prior_ppg_scores, "score"),
                ]

                if can_score:
                    weights = fit_logistic(train_x, train_y)
                    logistic_probs = logistic_predict(train_x, holdout_x, weights)
                    methods.append(("logistic_low_complexity", logistic_probs, "probability"))
                    for feature_name, weight in zip(["intercept", *APPROVED_FEATURES], weights, strict=True):
                        coefficient_rows.append(
                            {
                                "output_scope": "internal_only_not_app_readable",
                                "head": head,
                                "position": position,
                                "fold": fold_index,
                                "holdout_season": holdout_season,
                                "method": "logistic_low_complexity",
                                "feature": feature_name,
                                "coefficient": f"{weight:.8f}",
                            }
                        )

                for method, scores, score_type in methods:
                    auc = auc_score(holdout_y, scores)
                    ap = average_precision(holdout_y, scores)
                    brier_value = brier(holdout_y, scores) if score_type == "probability" and holdout_y else None
                    logloss_value = log_loss(holdout_y, scores) if score_type == "probability" and holdout_y else None
                    cal_bins, thin_bins, max_gap = (
                        calibration_summary(holdout_y, scores)
                        if score_type == "probability" and holdout_y
                        else (0, 0, None)
                    )
                    aggregate_rows.append(
                        {
                            "output_scope": "internal_only_not_app_readable",
                            "head": head,
                            "position": position,
                            "fold": fold_index,
                            "train_seasons": f"{min(train_seasons)}-{max(train_seasons)}",
                            "holdout_season": holdout_season,
                            "method": method,
                            "score_type": score_type,
                            "train_rows": len(train_y),
                            "train_positives": train_pos,
                            "train_negatives": train_neg,
                            "holdout_rows": len(holdout_y),
                            "holdout_positives": holdout_pos,
                            "holdout_negatives": holdout_neg,
                            "metric_status": "computed" if can_score or method == "base_rate_train_fold" else "limited_support",
                            "auc": metric_value(auc),
                            "pr_auc": metric_value(ap),
                            "brier": metric_value(brier_value),
                            "log_loss": metric_value(logloss_value),
                            "calibration_bins_populated": cal_bins,
                            "calibration_bins_thin": thin_bins,
                            "calibration_max_abs_gap": metric_value(max_gap),
                            "notes": "Aggregate fold metrics only; no row/player probabilities exported.",
                        }
                    )

    head_summary: list[dict[str, object]] = []
    for position, heads in ELIGIBLE_HEADS.items():
        for head in heads:
            rows_for_head = [
                row
                for row in aggregate_rows
                if row["head"] == head and row["method"] == "logistic_low_complexity"
            ]
            if rows_for_head:
                auc_values = [float(row["auc"]) for row in rows_for_head if row["auc"]]
                brier_values = [float(row["brier"]) for row in rows_for_head if row["brier"]]
                logloss_values = [float(row["log_loss"]) for row in rows_for_head if row["log_loss"]]
                status = "metrics_available"
            else:
                auc_values = []
                brier_values = []
                logloss_values = []
                status = "no_logistic_metric"
            head_summary.append(
                {
                    "output_scope": "internal_only_not_app_readable",
                    "head": head,
                    "position": position,
                    "folds_evaluated": len(rows_for_head),
                    "logistic_auc_mean": metric_value(mean(auc_values) if auc_values else None),
                    "logistic_brier_mean": metric_value(mean(brier_values) if brier_values else None),
                    "logistic_log_loss_mean": metric_value(mean(logloss_values) if logloss_values else None),
                    "summary_status": status,
                    "notes": "Aggregate summary only. Not release-ready and not app-readable.",
                }
            )

    output_files = {
        "aggregate_metrics_by_head_fold.csv",
        "head_metric_summary.csv",
        "feature_quarantine_audit.csv",
        "logistic_coefficients_by_head_fold.csv",
        "metadata_sprint_5co.json",
        "README_SPRINT_5CO.md",
    }

    write_csv(
        OUT_DIR / "aggregate_metrics_by_head_fold.csv",
        aggregate_rows,
        [
            "output_scope",
            "head",
            "position",
            "fold",
            "train_seasons",
            "holdout_season",
            "method",
            "score_type",
            "train_rows",
            "train_positives",
            "train_negatives",
            "holdout_rows",
            "holdout_positives",
            "holdout_negatives",
            "metric_status",
            "auc",
            "pr_auc",
            "brier",
            "log_loss",
            "calibration_bins_populated",
            "calibration_bins_thin",
            "calibration_max_abs_gap",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "head_metric_summary.csv",
        head_summary,
        [
            "output_scope",
            "head",
            "position",
            "folds_evaluated",
            "logistic_auc_mean",
            "logistic_brier_mean",
            "logistic_log_loss_mean",
            "summary_status",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "feature_quarantine_audit.csv",
        feature_audit_rows,
        ["output_scope", "feature", "approved_by_5cn", "forbidden_term_match", "used_in_5co"],
    )
    write_csv(
        OUT_DIR / "logistic_coefficients_by_head_fold.csv",
        coefficient_rows,
        ["output_scope", "head", "position", "fold", "holdout_season", "method", "feature", "coefficient"],
    )

    method_counts = Counter(row["method"] for row in aggregate_rows)
    metadata = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "audit_verdict": "GREEN" if not forbidden_failures else "RED",
        "output_scope": "internal_only_not_app_readable",
        "eligible_heads_evaluated": sum(len(heads) for heads in ELIGIBLE_HEADS.values()),
        "weak_heads_not_evaluated": WEAK_NOT_EVALUATED,
        "folds": [{"train_seasons": f"{min(train)}-{max(train)}", "holdout_season": holdout} for train, holdout in FOLDS],
        "methods": dict(method_counts),
        "forbidden_feature_failures": len(forbidden_failures),
        "output_files": sorted(output_files),
        "row_level_predictions_exported": False,
        "current_player_probabilities_created": False,
        "exact_display_percentages_created": False,
        "coarse_display_bands_created": False,
        "app_readable_outputs_created": False,
        "production_model_artifacts_created": False,
        "model_pickles_created": False,
        "app_wiring_created": False,
        "rankings_sorting_created": False,
        "hidden_sort_keys_created": False,
        "promoted_artifacts_created": False,
    }
    (OUT_DIR / "metadata_sprint_5co.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "README_SPRINT_5CO.md").write_text(
        "# Sprint 5CO Local-Only Aggregate Shadow Model Evaluation\n\n"
        "Aggregate shadow metrics only. No row/player probabilities, app-readable outputs, "
        "production model artifacts, exact display percentages, coarse display bands, rankings, "
        "hidden sort keys, or promoted artifacts.\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
