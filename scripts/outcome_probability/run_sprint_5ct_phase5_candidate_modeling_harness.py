"""Phase 5 local-only candidate modeling harness.

The harness is intentionally narrow:
- historical 2010-2019 feature/label packages only
- 5CS-approved candidate heads only
- deterministic rolling historical folds
- local-only aggregate outputs only
- no current-player inference
- no app-readable outputs
- no serialized model artifacts
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORT_ROOT = REPO_ROOT / "local_exports" / "outcome_probability"

APPROVED_HEADS = {
    "qb_t12": ("QB", "same_year_qb_t12"),
    "qb_t18": ("QB", "same_year_qb_t18"),
    "qb_t24": ("QB", "same_year_qb_t24"),
    "rb_t12": ("RB", "same_year_rb_t12"),
    "rb_t24": ("RB", "same_year_rb_t24"),
    "wr_t12": ("WR", "same_year_wr_t12"),
    "wr_t24": ("WR", "same_year_wr_t24"),
    "wr_t36": ("WR", "same_year_wr_t36"),
    "te_t12": ("TE", "same_year_te_t12"),
    "te_t18": ("TE", "same_year_te_t18"),
    "te_t24": ("TE", "same_year_te_t24"),
}

DEFERRED_HEADS = {"rb_t36", "rb_t48", "wr_t48"}
BLOCKED_HEADS = {"qb_t6", "rb_t6", "wr_t6", "te_t3", "te_t6"}

PACKAGE_CONFIGS = [
    ("5CI", "2010_2011", EXPORT_ROOT / "sprint_5ci_2010_2011_historical_feature_label_rebuild"),
    ("5CF", "2012_2013", EXPORT_ROOT / "sprint_5cf_2012_2013_historical_feature_label_rebuild"),
    ("5CC", "2014_2015", EXPORT_ROOT / "sprint_5cc_2014_2015_historical_feature_label_rebuild"),
    ("5BZ", "2016_2017", EXPORT_ROOT / "sprint_5bz_2016_2017_historical_feature_label_rebuild"),
    ("5BV", "2018_2019", EXPORT_ROOT / "sprint_5bv_2018_2019_historical_feature_label_rebuild"),
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
    "same_year",
    "target_year",
]

FOLDS = [
    (tuple(range(2010, 2016)), 2016),
    (tuple(range(2010, 2017)), 2017),
    (tuple(range(2010, 2018)), 2018),
    (tuple(range(2010, 2019)), 2019),
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


def fail(message: str) -> None:
    raise SystemExit(f"FAIL_CLOSED: {message}")


def validate_output_dir(path: Path) -> Path:
    resolved = path.resolve()
    allowed_root = EXPORT_ROOT.resolve()
    if not str(resolved).startswith(str(allowed_root)):
        fail(f"output directory outside local outcome exports: {resolved}")
    if any(part.lower() in {"app", "streamlit", "data"} for part in resolved.parts):
        fail(f"forbidden output path component: {resolved}")
    return resolved


def requested_heads(raw_heads: str) -> list[str]:
    if raw_heads == "approved":
        return list(APPROVED_HEADS)
    heads = [head.strip() for head in raw_heads.split(",") if head.strip()]
    for head in heads:
        if head in DEFERRED_HEADS or head in BLOCKED_HEADS:
            fail(f"deferred or blocked head requested: {head}")
        if head not in APPROVED_HEADS:
            fail(f"unknown or unapproved head requested: {head}")
    return heads


def load_historical_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for sprint, seasons, base in PACKAGE_CONFIGS:
        feature_path = base / f"historical_{seasons}_feature_snapshots.csv"
        label_path = base / f"historical_{seasons}_outcome_labels.csv"
        if not feature_path.exists() or not label_path.exists():
            fail(f"missing historical package files for {sprint}: {base}")
        features = {row["row_id"]: row for row in read_csv(feature_path)}
        labels = {row["row_id"]: row for row in read_csv(label_path)}
        for row_id, feature_row in features.items():
            label_row = labels.get(row_id)
            if label_row is None:
                continue
            if feature_row.get("app_readable") != "no" or label_row.get("app_readable") != "no":
                fail(f"app-readable row encountered in historical package: {row_id}")
            feature_vector = json.loads(feature_row["feature_vector"])
            threshold_labels = json.loads(label_row["threshold_labels_json"])
            for key in feature_vector:
                if key not in APPROVED_FEATURES and key != "position":
                    fail(f"unapproved feature in feature vector: {key}")
                if any(term in key.lower() for term in FORBIDDEN_FEATURE_TERMS):
                    fail(f"forbidden feature term in feature vector: {key}")
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
    if any(int(row["target_season"]) > 2019 for row in rows):
        fail("current-player/current-season row detected")
    return rows


def feature_values(row: dict[str, object]) -> list[float]:
    vector = row["feature_vector"]
    if not isinstance(vector, dict):
        fail("feature vector is not a dict")
    return [float(vector[name]) for name in APPROVED_FEATURES]


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


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
    for _ in range(160):
        gradients = [0.0 for _ in weights]
        for values, target in zip(x, train_y, strict=True):
            pred = sigmoid(weights[0] + sum(weight * value for weight, value in zip(weights[1:], values, strict=True)))
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
        preds.append(sigmoid(weights[0] + sum(weight * value for weight, value in zip(weights[1:], values, strict=True))))
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
            if target:
                rank_sum += avg_rank
        index = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def average_precision(y_true: list[int], scores: list[float]) -> float | None:
    positives = sum(y_true)
    if positives == 0:
        return None
    sorted_pairs = sorted(zip(scores, y_true, strict=True), key=lambda item: item[0], reverse=True)
    found = 0
    total = 0.0
    for rank, (_, target) in enumerate(sorted_pairs, start=1):
        if target:
            found += 1
            total += found / rank
    return total / positives


def brier(y_true: list[int], probs: list[float]) -> float:
    return mean((prob - target) ** 2 for prob, target in zip(probs, y_true, strict=True))


def log_loss(y_true: list[int], probs: list[float]) -> float:
    eps = 1e-6
    values = []
    for prob, target in zip(probs, y_true, strict=True):
        p = min(max(prob, eps), 1 - eps)
        values.append(-(target * math.log(p) + (1 - target) * math.log(1 - p)))
    return mean(values)


def calibration_summary(y_true: list[int], probs: list[float]) -> tuple[int, int, float | None]:
    buckets: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for target, prob in zip(y_true, probs, strict=True):
        buckets[min(4, int(prob * 5))].append((target, prob))
    populated = 0
    thin = 0
    max_gap = 0.0
    for bucket_values in buckets.values():
        populated += 1
        if len(bucket_values) < 10:
            thin += 1
        observed = mean(target for target, _ in bucket_values)
        predicted = mean(prob for _, prob in bucket_values)
        max_gap = max(max_gap, abs(observed - predicted))
    return populated, thin, max_gap if populated else None


def metric(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


def evaluate(rows: list[dict[str, object]], heads: list[str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    aggregate_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    for short_head in heads:
        position, canonical_head = APPROVED_HEADS[short_head]
        position_rows = [row for row in rows if row["position"] == position]
        for fold_index, (train_seasons, holdout_season) in enumerate(FOLDS, start=1):
            train = [row for row in position_rows if row["target_season"] in train_seasons]
            holdout = [row for row in position_rows if row["target_season"] == holdout_season]
            train_y = [1 if row["threshold_labels"][canonical_head] else 0 for row in train]
            holdout_y = [1 if row["threshold_labels"][canonical_head] else 0 for row in holdout]
            train_x = [feature_values(row) for row in train]
            holdout_x = [feature_values(row) for row in holdout]
            train_pos = sum(train_y)
            holdout_pos = sum(holdout_y)
            can_fit = train_pos > 0 and train_pos < len(train_y) and holdout_pos > 0 and holdout_pos < len(holdout_y)
            base_prob = train_pos / len(train_y)
            methods = [
                ("base_rate_train_fold", [base_prob for _ in holdout_y], "probability"),
                ("prior_rank_score", [-float(row["feature_vector"]["prior_season_nwr_finish_rank"]) for row in holdout], "score"),
                ("prior_ppg_score", [float(row["feature_vector"]["prior_season_nwr_ppg"]) for row in holdout], "score"),
            ]
            if can_fit:
                weights = fit_logistic(train_x, train_y)
                methods.append(("candidate_logistic_low_complexity", logistic_predict(train_x, holdout_x, weights), "probability"))
                for feature, value in zip(["intercept", *APPROVED_FEATURES], weights, strict=True):
                    coefficient_rows.append(
                        {
                            "output_scope": "internal_only_not_app_readable",
                            "head": short_head,
                            "canonical_head": canonical_head,
                            "position": position,
                            "fold": fold_index,
                            "holdout_season": holdout_season,
                            "feature": feature,
                            "coefficient": f"{value:.8f}",
                        }
                    )
            for method, scores, score_type in methods:
                auc = auc_score(holdout_y, scores)
                ap = average_precision(holdout_y, scores)
                brier_value = brier(holdout_y, scores) if score_type == "probability" else None
                logloss_value = log_loss(holdout_y, scores) if score_type == "probability" else None
                cal_bins, cal_thin, cal_gap = calibration_summary(holdout_y, scores) if score_type == "probability" else (0, 0, None)
                aggregate_rows.append(
                    {
                        "output_scope": "internal_only_not_app_readable",
                        "head": short_head,
                        "canonical_head": canonical_head,
                        "position": position,
                        "fold": fold_index,
                        "train_seasons": f"{min(train_seasons)}-{max(train_seasons)}",
                        "holdout_season": holdout_season,
                        "method": method,
                        "score_type": score_type,
                        "train_rows": len(train_y),
                        "train_positives": train_pos,
                        "train_negatives": len(train_y) - train_pos,
                        "holdout_rows": len(holdout_y),
                        "holdout_positives": holdout_pos,
                        "holdout_negatives": len(holdout_y) - holdout_pos,
                        "auc": metric(auc),
                        "pr_auc": metric(ap),
                        "brier": metric(brier_value),
                        "log_loss": metric(logloss_value),
                        "calibration_bins_populated": cal_bins,
                        "calibration_bins_thin": cal_thin,
                        "calibration_max_abs_gap": metric(cal_gap),
                    }
                )
    return aggregate_rows, coefficient_rows


def summarize(aggregate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_head: dict[str, list[dict[str, object]]] = defaultdict(list)
    base_by_head: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in aggregate_rows:
        if row["method"] == "candidate_logistic_low_complexity":
            by_head[str(row["head"])].append(row)
        if row["method"] == "base_rate_train_fold":
            base_by_head[str(row["head"])].append(row)
    summary_rows: list[dict[str, object]] = []
    for head in APPROVED_HEADS:
        rows = by_head[head]
        base_rows = base_by_head[head]
        aucs = [float(row["auc"]) for row in rows if row["auc"]]
        briers = [float(row["brier"]) for row in rows if row["brier"]]
        log_losses = [float(row["log_loss"]) for row in rows if row["log_loss"]]
        base_briers = [float(row["brier"]) for row in base_rows if row["brier"]]
        base_log_losses = [float(row["log_loss"]) for row in base_rows if row["log_loss"]]
        thin_bins = sum(int(row["calibration_bins_thin"]) for row in rows)
        auc_mean = mean(aucs) if aucs else None
        brier_mean = mean(briers) if briers else None
        base_brier_mean = mean(base_briers) if base_briers else None
        log_loss_mean = mean(log_losses) if log_losses else None
        base_log_loss_mean = mean(base_log_losses) if base_log_losses else None
        if auc_mean is None:
            verdict = "insufficient_support"
        elif auc_mean >= 0.85 and thin_bins <= 8 and brier_mean < base_brier_mean:
            verdict = "candidate_accept"
        elif auc_mean >= 0.80 and brier_mean < base_brier_mean:
            verdict = "candidate_caution"
        else:
            verdict = "candidate_reject"
        position, canonical = APPROVED_HEADS[head]
        summary_rows.append(
            {
                "output_scope": "internal_only_not_app_readable",
                "head": head,
                "canonical_head": canonical,
                "position": position,
                "folds": len(rows),
                "auc_mean": metric(auc_mean),
                "brier_mean": metric(brier_mean),
                "base_brier_mean": metric(base_brier_mean),
                "log_loss_mean": metric(log_loss_mean),
                "base_log_loss_mean": metric(base_log_loss_mean),
                "thin_calibration_bins": thin_bins,
                "candidate_verdict": verdict,
            }
        )
    return summary_rows


def write_outputs(output_dir: Path, heads: list[str], aggregate_rows: list[dict[str, object]], coefficient_rows: list[dict[str, object]]) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_rows = summarize(aggregate_rows)
    feature_audit_rows = [
        {
            "output_scope": "internal_only_not_app_readable",
            "feature": feature,
            "approved": "yes",
            "forbidden_term_match": "|".join(term for term in FORBIDDEN_FEATURE_TERMS if term in feature.lower()),
            "used": "yes",
        }
        for feature in APPROVED_FEATURES
    ]
    write_csv(
        output_dir / "aggregate_metrics_by_head_fold_method.csv",
        aggregate_rows,
        [
            "output_scope",
            "head",
            "canonical_head",
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
            "auc",
            "pr_auc",
            "brier",
            "log_loss",
            "calibration_bins_populated",
            "calibration_bins_thin",
            "calibration_max_abs_gap",
        ],
    )
    write_csv(
        output_dir / "head_candidate_verdicts.csv",
        summary_rows,
        [
            "output_scope",
            "head",
            "canonical_head",
            "position",
            "folds",
            "auc_mean",
            "brier_mean",
            "base_brier_mean",
            "log_loss_mean",
            "base_log_loss_mean",
            "thin_calibration_bins",
            "candidate_verdict",
        ],
    )
    write_csv(
        output_dir / "feature_quarantine_audit.csv",
        feature_audit_rows,
        ["output_scope", "feature", "approved", "forbidden_term_match", "used"],
    )
    write_csv(
        output_dir / "candidate_logistic_coefficients.csv",
        coefficient_rows,
        ["output_scope", "head", "canonical_head", "position", "fold", "holdout_season", "feature", "coefficient"],
    )
    verdict_counts = Counter(row["candidate_verdict"] for row in summary_rows)
    metadata = {
        "run_id": output_dir.name,
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "output_scope": "internal_only_not_app_readable",
        "heads_requested": heads,
        "deferred_heads_excluded": sorted(DEFERRED_HEADS),
        "blocked_heads_excluded": sorted(BLOCKED_HEADS),
        "candidate_verdict_counts": dict(verdict_counts),
        "row_level_predictions_exported": False,
        "current_player_inference_performed": False,
        "app_readable_outputs_created": False,
        "serialized_model_artifacts_created": False,
        "production_model_artifacts_created": False,
        "exact_display_percentages_created": False,
        "coarse_display_bands_created": False,
        "app_wiring_created": False,
        "rankings_sorting_created": False,
        "hidden_sort_keys_created": False,
        "promoted_artifacts_created": False,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Phase 5 local-only candidate modeling evidence\n\n"
        "Historical fold aggregate metrics only. No current-player inference, row-level predictions, "
        "app-readable outputs, serialized models, production artifacts, rankings, hidden sort keys, "
        "exact display percentages, or coarse bands.\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["preflight", "evaluate"], required=True)
    parser.add_argument("--heads", default="approved")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    heads = requested_heads(args.heads)
    output_dir = validate_output_dir(Path(args.output_dir))
    rows = load_historical_rows()

    if args.mode == "preflight":
        sample_heads = heads[:1]
        aggregate_rows, coefficient_rows = evaluate(rows, sample_heads)
        metadata = {
            "run_id": output_dir.name,
            "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "preflight",
            "output_scope": "internal_only_not_app_readable",
            "rows_loaded": len(rows),
            "sample_heads_checked": sample_heads,
            "approved_head_count": len(APPROVED_HEADS),
            "deferred_heads_excluded": sorted(DEFERRED_HEADS),
            "blocked_heads_excluded": sorted(BLOCKED_HEADS),
            "aggregate_rows_generated_for_dry_run": len(aggregate_rows),
            "coefficient_rows_generated_for_dry_run": len(coefficient_rows),
            "current_player_inference_performed": False,
            "app_readable_outputs_created": False,
            "serialized_model_artifacts_created": False,
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "metadata_preflight.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return

    aggregate_rows, coefficient_rows = evaluate(rows, heads)
    metadata = write_outputs(output_dir, heads, aggregate_rows, coefficient_rows)
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
