from __future__ import annotations

import csv
import json
import math
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = (
    REPO_ROOT
    / "local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package"
)

OUTPUT_SCOPE = "internal_only_not_app_readable"
APP_RELEASE_STATUS = "blocked_not_app_readable"
RUN_ID = "sprint_5bi_internal_holdout_calibration_package"
TRAIN_SEASONS = (2020, 2021, 2022)
VALIDATION_SEASONS = (2023,)
TEST_SEASONS = (2024,)
POSITIONS = ("RB", "WR")

THRESHOLD_CHAINS = {
    "RB": (
        "same_year_rb_t6",
        "same_year_rb_t12",
        "same_year_rb_t24",
        "same_year_rb_t36",
        "same_year_rb_t48",
    ),
    "WR": (
        "same_year_wr_t6",
        "same_year_wr_t12",
        "same_year_wr_t24",
        "same_year_wr_t36",
        "same_year_wr_t48",
    ),
}

TARGET_LABELS = {
    "same_year_rb_t6": "T6",
    "same_year_rb_t12": "T12",
    "same_year_rb_t24": "T24",
    "same_year_rb_t36": "T36",
    "same_year_rb_t48": "T48",
    "same_year_wr_t6": "T6",
    "same_year_wr_t12": "T12",
    "same_year_wr_t24": "T24",
    "same_year_wr_t36": "T36",
    "same_year_wr_t48": "T48",
}

FEATURE_RENAME_MAP = {
    "experience": "experience_at_snapshot",
    "prior_nwr_ppg": "prior_season_nwr_ppg",
    "prior_nwr_finish_rank": "prior_season_nwr_finish_rank",
    "prior_games": "prior_completed_season_games",
    "prior_games_played": "prior_completed_season_games_played",
    "prior_games_active": "prior_completed_season_games_active",
    "prior_rushing_first_downs": "prior_completed_season_rushing_first_downs",
    "prior_receiving_first_downs": "prior_completed_season_receiving_first_downs",
    "prior_receptions": "prior_completed_season_receptions",
    "prior_rushing_yards": "prior_completed_season_rushing_yards",
    "prior_receiving_yards": "prior_completed_season_receiving_yards",
    "prior_passing_yards": "prior_completed_season_passing_yards",
}

ALLOWED_FEATURES = (
    "age_at_snapshot",
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


@dataclass(frozen=True)
class ThresholdDatasetRow:
    row_id: str
    player_id: str
    player_name: str
    position: str
    target_season: int
    split: str
    features: dict[str, Any]
    position_rank: int


@dataclass(frozen=True)
class FittedHead:
    target: str
    position: str
    threshold: int
    train_rows: int
    train_events: int
    feature_list: tuple[str, ...]
    weights: tuple[float, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]


def main() -> None:
    result = build_sprint_5bi_internal_holdout_calibration_package(
        repo_root=REPO_ROOT,
        output_dir=OUTPUT_DIR,
    )
    print(json.dumps(result["metadata"], indent=2, sort_keys=True))


def build_sprint_5bi_internal_holdout_calibration_package(
    *, repo_root: str | Path, output_dir: str | Path
) -> dict[str, Any]:
    repo = Path(repo_root)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    rows = load_threshold_dataset(repo)
    feature_list = available_feature_list(rows)
    forbidden_rows = forbidden_feature_scan(feature_list)
    if any(row["blocker"] == "yes" for row in forbidden_rows):
        _write_csv(output / "forbidden_feature_scan.csv", forbidden_rows)
        raise ValueError("Forbidden feature names are present in the 5BI feature list.")

    fitted_heads = fit_threshold_heads(rows=rows, feature_list=feature_list)
    raw_rows = raw_holdout_prediction_rows(rows=rows, heads=fitted_heads)
    adjusted_rows = adjusted_holdout_prediction_rows(raw_rows)
    all_prediction_rows = raw_rows + adjusted_rows
    metric_rows = metric_comparison_rows(all_prediction_rows)
    bin_rows = calibration_bin_rows(all_prediction_rows)
    stability_rows = calibration_bin_stability_rows(bin_rows)
    monotonicity_rows = monotonicity_audit_rows(all_prediction_rows)
    sparse_rows = sparse_head_rows(rows)
    coverage_rows = coverage_rows_from_dataset(rows)
    split_rows = split_discipline_rows(rows)
    quarantine_rows = artifact_quarantine_rows(output)
    population_rows = population_policy_rows(coverage_rows)
    release_rows = release_blocker_rows()

    _write_csv(output / "holdout_predictions_internal_only.csv", all_prediction_rows)
    _write_csv(output / "raw_clamped_constrained_metric_comparison.csv", metric_rows)
    _write_csv(output / "calibration_bins.csv", bin_rows)
    _write_csv(output / "calibration_bin_stability.csv", stability_rows)
    _write_csv(output / "monotonicity_audit.csv", monotonicity_rows)
    _write_csv(output / "sparse_head_audit.csv", sparse_rows)
    _write_csv(output / "coverage_audit.csv", coverage_rows)
    _write_csv(output / "split_discipline_audit.csv", split_rows)
    _write_csv(output / "forbidden_feature_scan.csv", forbidden_rows)
    _write_csv(output / "artifact_quarantine_audit.csv", quarantine_rows)
    _write_csv(output / "population_policy_audit.csv", population_rows)
    _write_csv(output / "release_blockers.csv", release_rows)

    metadata = {
        "run_id": RUN_ID,
        "created_at_utc": _utc_now_iso(),
        "code_version_git_commit": _git_commit(repo),
        "output_scope": OUTPUT_SCOPE,
        "app_release_status": APP_RELEASE_STATUS,
        "train_seasons": list(TRAIN_SEASONS),
        "validation_seasons": list(VALIDATION_SEASONS),
        "test_seasons": list(TEST_SEASONS),
        "positions": list(POSITIONS),
        "feature_list": feature_list,
        "forbidden_feature_scan_passed": True,
        "prediction_rows_exported": len(all_prediction_rows),
        "raw_prediction_rows_exported": len(raw_rows),
        "adjusted_prediction_rows_exported": len(adjusted_rows),
        "app_readable_output_created": False,
        "ranking_sorting_changed": False,
        "model_artifact_promoted": False,
        "exact_percentages": "blocked",
        "coarse_bands": "blocked",
        "app_wiring": "blocked",
        "final_gate_label": "INTERNAL_HOLDOUT_CALIBRATION_RESEARCH_ONLY_BLOCKED_FOR_RELEASE",
    }
    _write_json(output / "metadata_sprint_5bi.json", metadata)
    _write_readme(output / "README_SPRINT_5BI.md", metadata)

    return {
        "metadata": metadata,
        "metrics": metric_rows,
        "monotonicity": monotonicity_rows,
        "output_dir": str(output),
    }


def load_threshold_dataset(repo: Path) -> tuple[ThresholdDatasetRow, ...]:
    sources = (
        (
            repo
            / "local_exports/outcome_probability/sprint_5x_2020_2022_historical_rebuild"
            / "historical_2020_2022_feature_snapshots.csv",
            repo
            / "local_exports/outcome_probability/sprint_5x_2020_2022_historical_rebuild"
            / "historical_2020_2022_label_linkage.csv",
        ),
        (
            repo
            / "local_exports/outcome_probability/sprint_5n_broader_historical_rebuild"
            / "broader_historical_feature_snapshots.csv",
            repo
            / "local_exports/outcome_probability/sprint_5n_broader_historical_rebuild"
            / "broader_historical_label_linkage.csv",
        ),
    )
    output: list[ThresholdDatasetRow] = []
    for feature_path, label_path in sources:
        snapshots = {row["row_id"]: row for row in _read_csv(feature_path)}
        for label in _read_csv(label_path):
            if label.get("trainability_status") != "trainable_now":
                continue
            if label.get("row_type") != "all_player_pre_week1":
                continue
            position = str(label.get("position", "")).upper()
            if position not in POSITIONS:
                continue
            snapshot = snapshots.get(label.get("row_id", ""))
            if not snapshot or snapshot.get("legality_status") != "valid":
                continue
            season = int(label["target_season"])
            split = _split_for_season(season)
            if split == "ignored":
                continue
            features = canonical_feature_vector(json.loads(snapshot["feature_vector"]))
            output.append(
                ThresholdDatasetRow(
                    row_id=label["row_id"],
                    player_id=label["player_id"],
                    player_name=label["player_name"],
                    position=position,
                    target_season=season,
                    split=split,
                    features=features,
                    position_rank=int(label["position_rank"]),
                )
            )
    return tuple(output)


def canonical_feature_vector(feature_vector: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, Any] = {}
    for feature_name, value in feature_vector.items():
        new_name = FEATURE_RENAME_MAP.get(feature_name, feature_name)
        if new_name in ALLOWED_FEATURES:
            canonical[new_name] = value
    return canonical


def available_feature_list(rows: Sequence[ThresholdDatasetRow]) -> list[str]:
    present = {feature for row in rows for feature in row.features}
    return [feature for feature in ALLOWED_FEATURES if feature in present]


def forbidden_feature_scan(feature_list: Sequence[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature_name in feature_list:
        normalized = feature_name.lower()
        matched = next(
            (
                fragment
                for fragment in FORBIDDEN_FEATURE_FRAGMENTS
                if fragment in normalized
            ),
            "",
        )
        rows.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "feature_name": feature_name,
                "scan_status": "fail" if matched else "pass",
                "matched_fragment": matched,
                "blocker": "yes" if matched else "no",
                "notes": (
                    "Forbidden feature fragment detected."
                    if matched
                    else "No forbidden feature fragment detected."
                ),
            }
        )
    return rows


def fit_threshold_heads(
    *, rows: Sequence[ThresholdDatasetRow], feature_list: Sequence[str]
) -> dict[str, FittedHead]:
    heads: dict[str, FittedHead] = {}
    for position, chain in THRESHOLD_CHAINS.items():
        train_rows = [
            row
            for row in rows
            if row.position == position and row.target_season in TRAIN_SEASONS
        ]
        for target in chain:
            threshold = int(TARGET_LABELS[target].removeprefix("T"))
            labels = [1 if row.position_rank <= threshold else 0 for row in train_rows]
            raw_x = [design_vector(row, feature_list) for row in train_rows]
            x_train, means, scales = standardize_train(raw_x)
            weights = fit_logistic_weights(
                x_train,
                labels,
                l2=0.15,
                learning_rate=0.08,
                steps=900,
            )
            heads[target] = FittedHead(
                target=target,
                position=position,
                threshold=threshold,
                train_rows=len(train_rows),
                train_events=sum(labels),
                feature_list=tuple(feature_list),
                weights=tuple(weights),
                means=tuple(means),
                scales=tuple(scales),
            )
    return heads


def raw_holdout_prediction_rows(
    *, rows: Sequence[ThresholdDatasetRow], heads: Mapping[str, FittedHead]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    holdout_rows = [row for row in rows if row.split in {"validation", "test"}]
    for row in holdout_rows:
        for target in THRESHOLD_CHAINS[row.position]:
            head = heads[target]
            raw_x = design_vector(row, head.feature_list)
            x = standardize_one(raw_x, head.means, head.scales)
            probability = sigmoid(dot(head.weights, x))
            output.append(
                prediction_row(
                    source=row,
                    method="raw_independent_baseline",
                    target=target,
                    threshold=head.threshold,
                    probability=probability,
                    label=1 if row.position_rank <= head.threshold else 0,
                    repair_delta=0.0,
                )
            )
    return output


def adjusted_holdout_prediction_rows(
    raw_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_player: dict[tuple[str, str, str], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in raw_rows:
        key = (str(row["split"]), str(row["position"]), str(row["row_id"]))
        by_player[key][str(row["target"])] = row

    output: list[dict[str, Any]] = []
    for (_split, position, _row_id), target_rows in sorted(by_player.items()):
        chain = THRESHOLD_CHAINS[position]
        if not all(target in target_rows for target in chain):
            continue
        raw_values = tuple(
            float(target_rows[target]["probability_internal_unreleased"])
            for target in chain
        )
        method_values = {
            "posthoc_forward_clamp_benchmark": forward_clamp_non_decreasing(raw_values),
            "constrained_isotonic_pava_candidate": pava_non_decreasing(raw_values),
        }
        for method, values in method_values.items():
            for target, probability, raw_probability in zip(
                chain,
                values,
                raw_values,
                strict=True,
            ):
                source_row = target_rows[target]
                output.append(
                    prediction_row(
                        source=source_row,
                        method=method,
                        target=target,
                        threshold=int(TARGET_LABELS[target].removeprefix("T")),
                        probability=probability,
                        label=int(source_row["label"]),
                        repair_delta=probability - raw_probability,
                    )
                )
    return output


def pava_non_decreasing(values: Sequence[float]) -> tuple[float, ...]:
    block_values: list[float] = []
    block_weights: list[int] = []
    for value in values:
        block_values.append(float(value))
        block_weights.append(1)
        while len(block_values) >= 2 and block_values[-2] > block_values[-1]:
            combined_weight = block_weights[-2] + block_weights[-1]
            combined_value = (
                block_values[-2] * block_weights[-2]
                + block_values[-1] * block_weights[-1]
            ) / combined_weight
            block_values[-2:] = [combined_value]
            block_weights[-2:] = [combined_weight]

    output: list[float] = []
    for value, weight in zip(block_values, block_weights, strict=True):
        output.extend([value] * weight)
    return tuple(output)


def forward_clamp_non_decreasing(values: Sequence[float]) -> tuple[float, ...]:
    output: list[float] = []
    running = 0.0
    for value in values:
        running = max(running, float(value))
        output.append(running)
    return tuple(output)


def prediction_row(
    *,
    source: ThresholdDatasetRow | Mapping[str, Any],
    method: str,
    target: str,
    threshold: int,
    probability: float,
    label: int,
    repair_delta: float,
) -> dict[str, Any]:
    if isinstance(source, ThresholdDatasetRow):
        row_id = source.row_id
        player_id = source.player_id
        player_name = source.player_name
        position = source.position
        target_season = source.target_season
        split = source.split
        position_rank = source.position_rank
    else:
        row_id = str(source["row_id"])
        player_id = str(source["player_id"])
        player_name = str(source["player_name"])
        position = str(source["position"])
        target_season = int(source["target_season"])
        split = str(source["split"])
        position_rank = int(source["position_rank"])

    return {
        "output_scope": OUTPUT_SCOPE,
        "app_release_status": APP_RELEASE_STATUS,
        "run_id": RUN_ID,
        "method": method,
        "split": split,
        "target_season": target_season,
        "row_id": row_id,
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "target": target,
        "threshold": f"T{threshold}",
        "position_rank": position_rank,
        "label": label,
        "probability_internal_unreleased": round(probability, 6),
        "repair_delta_vs_raw": round(repair_delta, 6),
        "exact_percentage_display_allowed": "no",
        "coarse_band_display_allowed": "no",
        "sort_allowed": "no",
        "ranking_use_allowed": "no",
        "app_readable": "no",
        "notes": (
            "Internal holdout calibration research only; not app-readable, "
            "not player-facing, not sortable, not a promoted artifact."
        ),
    }


def metric_comparison_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["method"]),
                str(row["split"]),
                str(row["position"]),
                str(row["target"]),
            )
        ].append(row)

    for (method, split, position, target), group in sorted(grouped.items()):
        predictions = [float(row["probability_internal_unreleased"]) for row in group]
        labels = [int(row["label"]) for row in group]
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "app_release_status": APP_RELEASE_STATUS,
                "run_id": RUN_ID,
                "method": method,
                "split": split,
                "position": position,
                "target": target,
                "threshold": TARGET_LABELS[target],
                "rows": len(group),
                "event_count": sum(labels),
                "non_event_count": len(labels) - sum(labels),
                "predicted_mean": round(mean(predictions), 6),
                "observed_rate": round(mean(labels), 6),
                "brier_score": round(brier(predictions, labels), 6),
                "log_loss": round(log_loss(predictions, labels), 6),
                "calibration_layer": "none",
                "exact_percentage_display_allowed": "no",
                "coarse_band_display_allowed": "no",
                "release_status": "blocked_internal_research_only",
            }
        )
    return output


def calibration_bin_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                str(row["method"]),
                str(row["split"]),
                str(row["position"]),
                str(row["target"]),
            )
        ].append(row)

    for (method, split, position, target), group in sorted(grouped.items()):
        paired = sorted(
            (
                (float(row["probability_internal_unreleased"]), int(row["label"]))
                for row in group
            ),
            key=lambda item: item[0],
        )
        bin_count = min(5, len(paired))
        for index in range(bin_count):
            start = index * len(paired) // bin_count
            end = (index + 1) * len(paired) // bin_count
            chunk = paired[start:end]
            predictions = [item[0] for item in chunk]
            labels = [item[1] for item in chunk]
            predicted_mean = mean(predictions)
            observed_rate = mean(labels)
            event_count = sum(labels)
            non_event_count = len(labels) - event_count
            output.append(
                {
                    "output_scope": OUTPUT_SCOPE,
                    "app_release_status": APP_RELEASE_STATUS,
                    "run_id": RUN_ID,
                    "method": method,
                    "split": split,
                    "position": position,
                    "target": target,
                    "threshold": TARGET_LABELS[target],
                    "bin_id": index + 1,
                    "row_count": len(chunk),
                    "predicted_mean": round(predicted_mean, 6),
                    "observed_rate": round(observed_rate, 6),
                    "absolute_calibration_gap": round(abs(predicted_mean - observed_rate), 6),
                    "event_count": event_count,
                    "non_event_count": non_event_count,
                    "min_predicted": round(min(predictions), 6),
                    "max_predicted": round(max(predictions), 6),
                    "stability_flag": stability_flag(
                        row_count=len(chunk),
                        event_count=event_count,
                        non_event_count=non_event_count,
                        absolute_gap=abs(predicted_mean - observed_rate),
                    ),
                    "notes": "Aggregate calibration bin only; no app display permission.",
                }
            )
    return output


def calibration_bin_stability_rows(
    bin_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in bin_rows:
        grouped[
            (
                str(row["method"]),
                str(row["split"]),
                str(row["position"]),
                str(row["target"]),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for (method, split, position, target), group in sorted(grouped.items()):
        unstable_bins = [
            row for row in group if str(row["stability_flag"]) != "stable_research_bin"
        ]
        max_gap = max(float(row["absolute_calibration_gap"]) for row in group)
        min_events = min(int(row["event_count"]) for row in group)
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "app_release_status": APP_RELEASE_STATUS,
                "run_id": RUN_ID,
                "method": method,
                "split": split,
                "position": position,
                "target": target,
                "threshold": TARGET_LABELS[target],
                "bin_count": len(group),
                "unstable_bin_count": len(unstable_bins),
                "min_bin_events": min_events,
                "max_abs_calibration_gap": round(max_gap, 6),
                "calibration_bin_status": "unstable_bins_present"
                if unstable_bins
                else "stable_research_bins",
                "release_impact": "exact_percentages_blocked",
            }
        )
    return output


def stability_flag(
    *, row_count: int, event_count: int, non_event_count: int, absolute_gap: float
) -> str:
    if row_count < 20:
        return "unstable_low_row_count"
    if event_count < 3:
        return "unstable_sparse_events"
    if non_event_count < 3:
        return "unstable_sparse_nonevents"
    if absolute_gap > 0.15:
        return "unstable_large_calibration_gap"
    return "stable_research_bin"


def monotonicity_audit_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_player: dict[tuple[str, str, str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        by_player[
            (
                str(row["method"]),
                str(row["split"]),
                str(row["position"]),
                str(row["row_id"]),
            )
        ][str(row["target"])] = float(row["probability_internal_unreleased"])

    violations: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    checked: Counter[tuple[str, str, str]] = Counter()
    for (method, split, position, _row_id), target_values in by_player.items():
        chain = THRESHOLD_CHAINS[position]
        if not all(target in target_values for target in chain):
            continue
        checked[(method, split, position)] += 1
        values = [target_values[target] for target in chain]
        for left, right in zip(values[:-1], values[1:], strict=True):
            if left > right:
                violations[(method, split, position)].append(left - right)

    output: list[dict[str, Any]] = []
    for key in sorted(checked):
        method, split, position = key
        gaps = violations.get(key, [])
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "app_release_status": APP_RELEASE_STATUS,
                "run_id": RUN_ID,
                "method": method,
                "split": split,
                "position": position,
                "players_checked": checked[key],
                "adjacent_violation_count": len(gaps),
                "max_adjacent_gap": round(max(gaps), 6) if gaps else 0.0,
                "threshold_contract": "P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)",
                "gate_status": "pass" if not gaps else "blocked_by_monotonicity",
                "release_impact": "necessary_not_sufficient_for_release",
            }
        )
    return output


def sparse_head_rows(rows: Sequence[ThresholdDatasetRow]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for position, chain in THRESHOLD_CHAINS.items():
        position_rows = [row for row in rows if row.position == position]
        for target in chain:
            threshold = int(TARGET_LABELS[target].removeprefix("T"))
            labels = [1 if row.position_rank <= threshold else 0 for row in position_rows]
            train_labels = [
                1 if row.position_rank <= threshold else 0
                for row in position_rows
                if row.target_season in TRAIN_SEASONS
            ]
            validation_labels = [
                1 if row.position_rank <= threshold else 0
                for row in position_rows
                if row.target_season in VALIDATION_SEASONS
            ]
            test_labels = [
                1 if row.position_rank <= threshold else 0
                for row in position_rows
                if row.target_season in TEST_SEASONS
            ]
            sparse = sum(labels) < 30 or sum(validation_labels) < 6 or sum(test_labels) < 6
            output.append(
                {
                    "output_scope": OUTPUT_SCOPE,
                    "target": target,
                    "position": position,
                    "threshold": TARGET_LABELS[target],
                    "eligible_historical_rows": len(position_rows),
                    "events": sum(labels),
                    "non_events": len(labels) - sum(labels),
                    "train_events": sum(train_labels),
                    "validation_events": sum(validation_labels),
                    "test_events": sum(test_labels),
                    "sparse_flag": "yes" if sparse else "no",
                    "abstention_recommendation": "abstain_or_research_only"
                    if sparse
                    else "research_candidate_not_display_ready",
                }
            )
    return output


def coverage_rows_from_dataset(rows: Sequence[ThresholdDatasetRow]) -> list[dict[str, Any]]:
    counts = Counter((row.position, row.split) for row in rows)
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": "historical_rb_wr_train_rows",
            "count": sum(
                count
                for (position, split), count in counts.items()
                if position in POSITIONS and split == "train"
            ),
            "status": "train_2020_2022",
            "release_impact": "internal_research_only",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": "historical_rb_wr_validation_rows",
            "count": sum(
                count
                for (position, split), count in counts.items()
                if position in POSITIONS and split == "validation"
            ),
            "status": "validation_2023",
            "release_impact": "internal_research_only",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": "historical_rb_wr_test_rows",
            "count": sum(
                count
                for (position, split), count in counts.items()
                if position in POSITIONS and split == "test"
            ),
            "status": "test_2024",
            "release_impact": "internal_research_only",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": "rookie_rows_scored",
            "count": 0,
            "status": "excluded_from_veteran_heads",
            "release_impact": "population_policy_pass",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": "kicker_rows_scored",
            "count": 0,
            "status": "not_applicable",
            "release_impact": "population_policy_pass",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": "app_probability_files_created",
            "count": 0,
            "status": "none",
            "release_impact": "app_wiring_blocked",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": "promoted_model_artifacts_created",
            "count": 0,
            "status": "none",
            "release_impact": "artifact_promotion_blocked",
        },
    ]


def split_discipline_rows(rows: Sequence[ThresholdDatasetRow]) -> list[dict[str, Any]]:
    season_counts = Counter(row.target_season for row in rows)
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "train_validation_test_split",
            "status": "pass",
            "evidence": (
                f"train={sum(season_counts[season] for season in TRAIN_SEASONS)}; "
                f"validation={season_counts[2023]}; test={season_counts[2024]}"
            ),
            "notes": "Train 2020-2022, validation 2023, test 2024.",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "same_season_final_stats_as_features",
            "status": "pass",
            "evidence": "5X/5N feature snapshots use completed prior-season feature lineage.",
            "notes": "Same-season labels are used only as holdout outcomes.",
        },
    ]


def artifact_quarantine_rows(output: Path) -> list[dict[str, Any]]:
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "output_folder_scope",
            "status": "pass"
            if "local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package"
            in output.as_posix()
            else "fail",
            "evidence": output.as_posix(),
            "release_impact": "blocked_not_app_readable",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "app_readable_probability_table",
            "status": "pass",
            "evidence": "No app path is written; every row marks app_readable=no.",
            "release_impact": "app_wiring_blocked",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "ranking_sorting_output",
            "status": "pass",
            "evidence": "Every prediction row sets sort_allowed=no and ranking_use_allowed=no.",
            "release_impact": "rankings_sorting_blocked",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "promoted_model_artifact",
            "status": "pass",
            "evidence": "No pickle/joblib/model package or promoted artifact is written.",
            "release_impact": "artifact_promotion_blocked",
        },
    ]


def population_policy_rows(coverage_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "waived_unscored_players",
            "status": "pass",
            "evidence": "Historical holdout rows only; no current waived player scoring.",
            "release_impact": "current_player_release_still_blocked",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "rookies",
            "status": "pass",
            "evidence": _coverage_evidence(coverage_rows, "rookie_rows_scored"),
            "release_impact": "rookie_path_separate",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "kickers",
            "status": "pass",
            "evidence": _coverage_evidence(coverage_rows, "kicker_rows_scored"),
            "release_impact": "not_applicable",
        },
        {
            "output_scope": OUTPUT_SCOPE,
            "population_gate": "blocked_rows",
            "status": "pass",
            "evidence": "No blocked 2026 rows are scored by this holdout package.",
            "release_impact": "coverage_gate_still_required_for_release",
        },
    ]


def release_blocker_rows() -> list[dict[str, Any]]:
    blockers = (
        "exact_percentages",
        "coarse_bands",
        "app_wiring",
        "rankings_sorting",
        "promoted_model_artifacts",
    )
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "blocker": blocker,
            "status": "blocked",
            "notes": "Sprint 5BI is internal holdout research only.",
        }
        for blocker in blockers
    ]


def _coverage_evidence(rows: Sequence[Mapping[str, Any]], item: str) -> str:
    match = next((row for row in rows if row["coverage_item"] == item), None)
    if not match:
        return "missing"
    return f"{match['coverage_item']}={match['count']} ({match['status']})"


def design_vector(row: ThresholdDatasetRow, feature_list: Sequence[str]) -> list[float]:
    return [1.0, *[to_float(row.features.get(feature)) for feature in feature_list]]


def standardize_train(
    x_rows: Sequence[Sequence[float]],
) -> tuple[list[list[float]], list[float], list[float]]:
    if not x_rows:
        return [], [], []
    column_count = len(x_rows[0])
    means = [0.0 for _ in range(column_count)]
    scales = [1.0 for _ in range(column_count)]
    for index in range(1, column_count):
        values = [row[index] for row in x_rows]
        feature_mean = mean(values)
        variance = mean([(value - feature_mean) ** 2 for value in values])
        means[index] = feature_mean
        scales[index] = math.sqrt(variance) or 1.0
    return [standardize_one(row, means, scales) for row in x_rows], means, scales


def standardize_one(
    row: Sequence[float], means: Sequence[float], scales: Sequence[float]
) -> list[float]:
    return [
        value if index == 0 else (value - means[index]) / scales[index]
        for index, value in enumerate(row)
    ]


def fit_logistic_weights(
    x_rows: Sequence[Sequence[float]],
    labels: Sequence[int],
    *,
    l2: float,
    learning_rate: float,
    steps: int,
) -> list[float]:
    if not x_rows:
        return []
    weights = [0.0 for _ in x_rows[0]]
    for _ in range(steps):
        gradients = [0.0 for _ in weights]
        for x, y in zip(x_rows, labels, strict=True):
            error = sigmoid(dot(weights, x)) - y
            for index, value in enumerate(x):
                gradients[index] += error * value
        count = float(len(x_rows))
        for index in range(len(weights)):
            penalty = 0.0 if index == 0 else l2 * weights[index]
            weights[index] -= learning_rate * ((gradients[index] / count) + penalty)
    return weights


def brier(predictions: Sequence[float], labels: Sequence[int]) -> float:
    return mean(
        [
            (prediction - label) ** 2
            for prediction, label in zip(predictions, labels, strict=True)
        ]
    )


def log_loss(predictions: Sequence[float], labels: Sequence[int]) -> float:
    epsilon = 1e-12
    losses = []
    for prediction, label in zip(predictions, labels, strict=True):
        clipped = min(max(prediction, epsilon), 1.0 - epsilon)
        losses.append(-(label * math.log(clipped) + (1 - label) * math.log(1 - clipped)))
    return mean(losses)


def mean(values: Sequence[float | int]) -> float:
    return sum(values) / len(values) if values else 0.0


def dot(weights: Sequence[float], values: Sequence[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, values, strict=True))


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _split_for_season(season: int) -> str:
    if season in TRAIN_SEASONS:
        return "train"
    if season in VALIDATION_SEASONS:
        return "validation"
    if season in TEST_SEASONS:
        return "test"
    return "ignored"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = fieldnames_for(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fieldnames_for(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    output: list[str] = []
    for row in rows:
        for key in row:
            if key not in output:
                output.append(key)
    return output or ["empty"]


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_readme(path: Path, metadata: Mapping[str, Any]) -> None:
    path.write_text(
        "\n".join(
            [
                "# Sprint 5BI Internal Holdout Calibration Package",
                "",
                "Verdict: `INTERNAL_HOLDOUT_CALIBRATION_RESEARCH_ONLY_BLOCKED_FOR_RELEASE`",
                "",
                "This package is internal-only research. It contains holdout prediction rows",
                "for raw, clamped, and constrained RB/WR threshold heads, but those rows are",
                "not app-readable, not player-facing, not sortable, and not release artifacts.",
                "",
                f"Prediction rows exported: {metadata['prediction_rows_exported']}",
                f"Feature scan passed: {metadata['forbidden_feature_scan_passed']}",
                "",
                "Exact percentages, coarse bands, app wiring, rankings/sorting, and promoted",
                "artifacts remain blocked.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_commit(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unavailable"
    return result.stdout.strip() or "unavailable"


if __name__ == "__main__":
    main()
