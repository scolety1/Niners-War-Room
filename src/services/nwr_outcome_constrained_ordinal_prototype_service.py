from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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

OUTPUT_SCOPE = "internal_only_not_app_readable"
APP_RELEASE_STATUS = "blocked_not_app_readable"
EXPORT_FOLDER = (
    "local_exports/outcome_probability/"
    "sprint_5bf_constrained_ordinal_internal_prototype"
)


def pava_non_decreasing(values: Sequence[float]) -> tuple[float, ...]:
    """Return the L2 isotonic projection for a nondecreasing sequence."""
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


def adjacent_violation_rows(
    *,
    position: str,
    player_id: str,
    player_name: str,
    chain: Sequence[str],
    values: Sequence[float],
    method: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left_target, right_target, left_value, right_value in zip(
        chain[:-1],
        chain[1:],
        values[:-1],
        values[1:],
        strict=True,
    ):
        if left_value > right_value:
            rows.append(
                {
                    "output_scope": OUTPUT_SCOPE,
                    "app_release_status": APP_RELEASE_STATUS,
                    "method": method,
                    "position": position,
                    "current_player_id": player_id,
                    "player_name": player_name,
                    "violating_pair": f"{left_target}>{right_target}",
                    "violating_pair_label": (
                        f"{TARGET_LABELS[left_target]}>{TARGET_LABELS[right_target]}"
                    ),
                    "narrow_probability_internal_unreleased": round(left_value, 6),
                    "broader_probability_internal_unreleased": round(right_value, 6),
                    "violation_gap": round(left_value - right_value, 6),
                    "exact_percentage_display_allowed": "no",
                    "coarse_band_display_allowed": "no",
                    "sort_allowed": "no",
                    "ranking_use_allowed": "no",
                }
            )
    return rows


def adjustment_rows(
    *,
    position: str,
    player_id: str,
    player_name: str,
    chain: Sequence[str],
    raw_values: Sequence[float],
    adjusted_values: Sequence[float],
    method: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target, raw_value, adjusted_value in zip(
        chain,
        raw_values,
        adjusted_values,
        strict=True,
    ):
        delta = adjusted_value - raw_value
        if abs(delta) <= 1e-12:
            continue
        rows.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "app_release_status": APP_RELEASE_STATUS,
                "method": method,
                "position": position,
                "current_player_id": player_id,
                "player_name": player_name,
                "target": target,
                "threshold": TARGET_LABELS[target],
                "raw_probability_internal_unreleased": round(raw_value, 6),
                "adjusted_probability_internal_unreleased": round(adjusted_value, 6),
                "repair_delta": round(delta, 6),
                "abs_repair_delta": round(abs(delta), 6),
                "exact_percentage_display_allowed": "no",
                "coarse_band_display_allowed": "no",
                "sort_allowed": "no",
                "ranking_use_allowed": "no",
                "notes": (
                    "Internal constrained/ordinal prototype comparison only; "
                    "not calibrated, not release-ready, not app-readable."
                ),
            }
        )
    return rows


def compare_internal_threshold_methods(
    prediction_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    by_player = _prediction_rows_by_player(prediction_rows)
    raw_violations: list[dict[str, Any]] = []
    clamped_violations: list[dict[str, Any]] = []
    constrained_violations: list[dict[str, Any]] = []
    clamped_adjustments: list[dict[str, Any]] = []
    constrained_adjustments: list[dict[str, Any]] = []
    position_counts: Counter[str] = Counter()

    for (position, player_id, player_name), target_values in sorted(by_player.items()):
        chain = THRESHOLD_CHAINS[position]
        if not all(target in target_values for target in chain):
            continue
        position_counts[position] += 1
        raw_values = tuple(target_values[target] for target in chain)
        clamped_values = forward_clamp_non_decreasing(raw_values)
        constrained_values = pava_non_decreasing(raw_values)

        raw_violations.extend(
            adjacent_violation_rows(
                position=position,
                player_id=player_id,
                player_name=player_name,
                chain=chain,
                values=raw_values,
                method="raw_independent_baseline",
            )
        )
        clamped_violations.extend(
            adjacent_violation_rows(
                position=position,
                player_id=player_id,
                player_name=player_name,
                chain=chain,
                values=clamped_values,
                method="posthoc_forward_clamp_benchmark",
            )
        )
        constrained_violations.extend(
            adjacent_violation_rows(
                position=position,
                player_id=player_id,
                player_name=player_name,
                chain=chain,
                values=constrained_values,
                method="constrained_isotonic_pava_projection",
            )
        )
        clamped_adjustments.extend(
            adjustment_rows(
                position=position,
                player_id=player_id,
                player_name=player_name,
                chain=chain,
                raw_values=raw_values,
                adjusted_values=clamped_values,
                method="posthoc_forward_clamp_benchmark",
            )
        )
        constrained_adjustments.extend(
            adjustment_rows(
                position=position,
                player_id=player_id,
                player_name=player_name,
                chain=chain,
                raw_values=raw_values,
                adjusted_values=constrained_values,
                method="constrained_isotonic_pava_projection",
            )
        )

    return {
        "position_counts": dict(position_counts),
        "raw_violations": raw_violations,
        "clamped_violations": clamped_violations,
        "constrained_violations": constrained_violations,
        "clamped_adjustments": clamped_adjustments,
        "constrained_adjustments": constrained_adjustments,
        "summary_rows": _summary_rows(
            position_counts=position_counts,
            raw_violations=raw_violations,
            clamped_violations=clamped_violations,
            constrained_violations=constrained_violations,
            clamped_adjustments=clamped_adjustments,
            constrained_adjustments=constrained_adjustments,
        ),
    }


def artifact_quarantine_rows(output_dir: str | Path) -> list[dict[str, str]]:
    output_path = Path(output_dir).as_posix()
    under_local_exports = EXPORT_FOLDER in output_path
    return [
        {
            "gate": "output_folder_scope",
            "status": "pass" if under_local_exports else "fail",
            "evidence": output_path,
            "release_impact": "blocked_not_app_readable",
        },
        {
            "gate": "app_readable_output_path",
            "status": "pass",
            "evidence": "No app/ or src app data path is written by this exporter.",
            "release_impact": "app_wiring_blocked",
        },
        {
            "gate": "ranking_sorting_output",
            "status": "pass",
            "evidence": "All row-level outputs set sort_allowed=no and ranking_use_allowed=no.",
            "release_impact": "rankings_sorting_blocked",
        },
        {
            "gate": "promoted_model_artifact",
            "status": "pass",
            "evidence": "No model object, pickle, package, or promoted artifact is written.",
            "release_impact": "artifact_promotion_blocked",
        },
    ]


def export_sprint_5bf_internal_prototype(
    *,
    repo_root: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    repo = Path(repo_root)
    output = Path(output_dir) if output_dir is not None else repo / EXPORT_FOLDER
    output.mkdir(parents=True, exist_ok=True)

    input_dir = (
        repo
        / "local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation"
    )
    prediction_rows = _read_csv(
        input_dir / "partial_2026_veteran_prediction_audit_internal_only.csv"
    )
    support_rows = _read_csv(input_dir / "threshold_head_support.csv")
    metrics_rows = _read_csv(input_dir / "threshold_head_validation_metrics.csv")
    coverage_rows = _read_csv(input_dir / "coverage_warning_audit.csv")
    forbidden_rows = _read_csv(input_dir / "forbidden_feature_scan.csv")
    release_rows = _read_csv(input_dir / "threshold_release_decision_table.csv")

    comparison = compare_internal_threshold_methods(prediction_rows)
    support_audit = _support_audit_rows(support_rows)
    metric_rows = _calibration_metric_rows(metrics_rows)
    coverage_audit = _coverage_audit_rows(coverage_rows)
    feature_scan = _feature_scan_rows(forbidden_rows)
    split_rows = _split_discipline_rows(metrics_rows)
    gate_rows = _gate_rows(
        comparison=comparison,
        forbidden_rows=feature_scan,
        coverage_rows=coverage_audit,
        output_dir=output,
    )
    release_rows_out = _release_recommendation_rows(release_rows)

    _write_csv(output / "feature_schema_audit.csv", feature_scan)
    _write_csv(output / "forbidden_feature_scan.csv", feature_scan)
    _write_csv(output / "split_discipline_audit.csv", split_rows)
    _write_csv(output / "threshold_semantics_audit.csv", _threshold_semantics_rows())
    _write_csv(output / "raw_independent_baseline_violations.csv", comparison["raw_violations"])
    _write_csv(
        output / "posthoc_clamped_benchmark_violations.csv",
        comparison["clamped_violations"],
    )
    _write_csv(
        output / "constrained_isotonic_prototype_violations.csv",
        comparison["constrained_violations"],
    )
    _write_csv(
        output / "posthoc_clamped_benchmark_adjustments_internal_only.csv",
        comparison["clamped_adjustments"],
    )
    _write_csv(
        output / "constrained_isotonic_adjustments_internal_only.csv",
        comparison["constrained_adjustments"],
    )
    _write_csv(output / "prototype_comparison_summary.csv", comparison["summary_rows"])
    _write_csv(output / "calibration_metrics_research_only.csv", metric_rows)
    _write_csv(output / "coverage_audit.csv", coverage_audit)
    _write_csv(output / "sparse_head_audit.csv", support_audit)
    _write_csv(output / "artifact_quarantine_audit.csv", artifact_quarantine_rows(output))
    _write_csv(output / "release_gate_blockers.csv", gate_rows)
    _write_csv(output / "threshold_release_recommendation_audit.csv", release_rows_out)

    metadata = {
        "run_id": "sprint_5bf_constrained_ordinal_internal_prototype",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "output_scope": OUTPUT_SCOPE,
        "app_release_status": APP_RELEASE_STATUS,
        "positions_reviewed": sorted(THRESHOLD_CHAINS),
        "position_counts": comparison["position_counts"],
        "raw_violation_count": len(comparison["raw_violations"]),
        "clamped_violation_count": len(comparison["clamped_violations"]),
        "constrained_violation_count": len(comparison["constrained_violations"]),
        "clamped_max_abs_delta": _max_abs_delta(comparison["clamped_adjustments"]),
        "constrained_max_abs_delta": _max_abs_delta(comparison["constrained_adjustments"]),
        "calibration_status": "research_only_prior_metrics_not_valid_for_adjusted_outputs",
        "exact_percentages": "blocked",
        "app_wiring": "blocked",
        "coarse_bands": "blocked_until_separate_gate",
        "model_artifact_promoted": False,
        "app_readable_output_created": False,
        "ranking_sorting_changed": False,
        "final_gate_label": "CONSTRAINED_ORDINAL_PROTOTYPE_INTERNAL_ONLY_CONTINUE",
    }
    _write_json(output / "metadata_sprint_5bf.json", metadata)
    _write_readme(output / "README_SPRINT_5BF.md", metadata)

    return {
        "verdict": "CONSTRAINED_ORDINAL_PROTOTYPE_INTERNAL_ONLY_CONTINUE",
        "metadata": metadata,
        "output_dir": str(output),
        "summary_rows": comparison["summary_rows"],
        "gate_rows": gate_rows,
    }


def _prediction_rows_by_player(
    rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str, str], dict[str, float]]:
    by_player: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        position = str(row.get("position", "")).upper()
        if position not in THRESHOLD_CHAINS:
            continue
        if row.get("source_feature_status") != "ready_feature_snapshot":
            continue
        key = (
            position,
            str(row.get("current_player_id", "")),
            str(row.get("player_name", "")),
        )
        by_player[key][str(row.get("target", ""))] = float(
            row.get("internal_probability_unreleased", 0.0)
        )
    return by_player


def _summary_rows(
    *,
    position_counts: Counter[str],
    raw_violations: Sequence[Mapping[str, Any]],
    clamped_violations: Sequence[Mapping[str, Any]],
    constrained_violations: Sequence[Mapping[str, Any]],
    clamped_adjustments: Sequence[Mapping[str, Any]],
    constrained_adjustments: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for position in sorted(THRESHOLD_CHAINS):
        raw_position = [row for row in raw_violations if row["position"] == position]
        clamped_position = [
            row for row in clamped_violations if row["position"] == position
        ]
        constrained_position = [
            row for row in constrained_violations if row["position"] == position
        ]
        clamped_position_adjustments = [
            row for row in clamped_adjustments if row["position"] == position
        ]
        constrained_position_adjustments = [
            row for row in constrained_adjustments if row["position"] == position
        ]
        rows.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "app_release_status": APP_RELEASE_STATUS,
                "position": position,
                "players_reviewed": position_counts[position],
                "raw_violation_count": len(raw_position),
                "raw_affected_players": _affected_player_count(raw_position),
                "raw_max_violation_gap": _max_gap(raw_position),
                "clamped_violation_count": len(clamped_position),
                "clamped_affected_players": _affected_player_count(
                    clamped_position_adjustments
                ),
                "clamped_adjusted_cells": len(clamped_position_adjustments),
                "clamped_max_abs_delta": _max_abs_delta(clamped_position_adjustments),
                "clamped_average_abs_delta": _avg_abs_delta(clamped_position_adjustments),
                "constrained_violation_count": len(constrained_position),
                "constrained_affected_players": _affected_player_count(
                    constrained_position_adjustments
                ),
                "constrained_adjusted_cells": len(constrained_position_adjustments),
                "constrained_max_abs_delta": _max_abs_delta(
                    constrained_position_adjustments
                ),
                "constrained_average_abs_delta": _avg_abs_delta(
                    constrained_position_adjustments
                ),
                "calibration_status": (
                    "research_only_adjusted_outputs_require_fresh_validation"
                ),
                "exact_percentage_display_allowed": "no",
                "coarse_band_display_allowed": "no",
                "sort_allowed": "no",
                "ranking_use_allowed": "no",
                "release_recommendation": "internal_only_followup_adversarial_audit",
            }
        )
    return rows


def _support_audit_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if row.get("position") not in THRESHOLD_CHAINS:
            continue
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "target": row.get("target", ""),
                "position": row.get("position", ""),
                "threshold": row.get("threshold", ""),
                "eligible_historical_rows": row.get("eligible_historical_rows", ""),
                "events": row.get("events", ""),
                "non_events": row.get("non_events", ""),
                "train_events": row.get("train_events", ""),
                "validation_events": row.get("validation_events", ""),
                "test_events": row.get("test_events", ""),
                "sparse_flag": row.get("sparse_flag", ""),
                "abstention_recommendation": (
                    "abstain_or_research_only"
                    if row.get("sparse_flag") == "yes"
                    else "research_candidate_not_display_ready"
                ),
            }
        )
    return output


def _calibration_metric_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if row.get("position") not in THRESHOLD_CHAINS:
            continue
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "target": row.get("target", ""),
                "position": row.get("position", ""),
                "threshold": row.get("threshold", ""),
                "raw_validation_brier": row.get("validation_brier", ""),
                "raw_test_brier": row.get("test_brier", ""),
                "raw_validation_log_loss": row.get("validation_log_loss", ""),
                "raw_test_log_loss": row.get("test_log_loss", ""),
                "raw_calibration_bin_status": row.get("calibration_bin_status", ""),
                "clamped_calibration_status": "requires_fresh_validation",
                "constrained_calibration_status": "requires_fresh_validation",
                "calibration_drift_vs_raw": "not_measured_without_holdout_predictions",
                "release_impact": "exact_percentages_blocked",
            }
        )
    return output


def _coverage_audit_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "coverage_item": row.get("coverage_item", ""),
            "count": row.get("count", ""),
            "source_status": row.get("status", ""),
            "prototype_policy": _coverage_policy(str(row.get("coverage_item", ""))),
            "release_impact": "coverage_gate_still_required",
        }
        for row in rows
    ]


def _feature_scan_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "feature_name": row.get("feature_name", ""),
            "scan_status": row.get("scan_status", ""),
            "matched_fragment": row.get("matched_fragment", ""),
            "blocker": row.get("blocker", ""),
            "prototype_gate_status": "pass"
            if row.get("scan_status") == "pass" and row.get("blocker") == "no"
            else "fail",
            "notes": row.get("notes", ""),
        }
        for row in rows
    ]


def _split_discipline_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    split_values = {
        (
            row.get("train_rows", ""),
            row.get("validation_rows", ""),
            row.get("test_rows", ""),
        )
        for row in rows
    }
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "gate": "historical_train_validation_test_metrics_present",
            "status": "pass" if split_values else "fail",
            "evidence": f"metric split row signatures={len(split_values)}",
            "notes": (
                "5BF consumes 5AY split metrics; no current 2026 rows fit "
                "calibration or model parameters."
            ),
        }
    ]


def _threshold_semantics_rows() -> list[dict[str, str]]:
    return [
        {
            "output_scope": OUTPUT_SCOPE,
            "position": position,
            "threshold_chain": " <= ".join(TARGET_LABELS[target] for target in chain),
            "event_definition": "top_N_or_better",
            "monotonicity_direction": "nondecreasing_as_threshold_widens",
            "gate_status": "required",
        }
        for position, chain in sorted(THRESHOLD_CHAINS.items())
    ]


def _gate_rows(
    *,
    comparison: Mapping[str, Any],
    forbidden_rows: Sequence[Mapping[str, Any]],
    coverage_rows: Sequence[Mapping[str, Any]],
    output_dir: Path,
) -> list[dict[str, str]]:
    forbidden_failures = [row for row in forbidden_rows if row["prototype_gate_status"] != "pass"]
    coverage_by_item = {row["coverage_item"]: row for row in coverage_rows}
    blocked_count = coverage_by_item.get("blocked_2026_veteran_feature_rows", {}).get(
        "count",
        "0",
    )
    rookie_count = coverage_by_item.get("rookie_rows", {}).get("count", "0")
    kicker_count = coverage_by_item.get("kicker_rows", {}).get("count", "0")
    return [
        {
            "gate": "legal_feature_schema_only",
            "status": "pass" if not forbidden_failures else "fail",
            "evidence": f"forbidden feature failures={len(forbidden_failures)}",
            "release_impact": "leakage_gate_required",
        },
        {
            "gate": "threshold_monotonicity_constrained_candidate",
            "status": "pass"
            if len(comparison["constrained_violations"]) == 0
            else "fail",
            "evidence": f"violations={len(comparison['constrained_violations'])}",
            "release_impact": "necessary_not_sufficient",
        },
        {
            "gate": "no_app_readable_output_path",
            "status": "pass"
            if output_dir.as_posix().endswith(
                "sprint_5bf_constrained_ordinal_internal_prototype"
            )
            else "fail",
            "evidence": output_dir.as_posix(),
            "release_impact": "app_wiring_blocked",
        },
        {
            "gate": "no_rankings_sorting_output",
            "status": "pass",
            "evidence": "sort_allowed=no and ranking_use_allowed=no in row-level exports",
            "release_impact": "rankings_sorting_blocked",
        },
        {
            "gate": "no_promoted_artifacts",
            "status": "pass",
            "evidence": "only CSV/JSON/README research exports are written",
            "release_impact": "artifact_promotion_blocked",
        },
        {
            "gate": "blocked_waived_rookie_kicker_policy",
            "status": "pass",
            "evidence": (
                f"blocked rows not scored={blocked_count}; rookies excluded="
                f"{rookie_count}; kickers not applicable={kicker_count}"
            ),
            "release_impact": "coverage_gate_still_required",
        },
        {
            "gate": "calibration_metrics_research_only",
            "status": "pass",
            "evidence": "raw 5AY metrics exported; adjusted outputs require fresh validation",
            "release_impact": "exact_percentages_blocked",
        },
    ]


def _release_recommendation_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if row.get("position") not in THRESHOLD_CHAINS:
            continue
        output.append(
            {
                "output_scope": OUTPUT_SCOPE,
                "target": row.get("target", ""),
                "position": row.get("position", ""),
                "threshold": row.get("threshold", ""),
                "prior_release_recommendation": row.get("release_recommendation", ""),
                "prototype_release_recommendation": (
                    "internal_only_followup_adversarial_audit"
                ),
                "exact_percentage_display_allowed": "no",
                "coarse_band_display_allowed": "no",
                "sort_allowed": "no",
                "ranking_use_allowed": "no",
            }
        )
    return output


def _coverage_policy(item: str) -> str:
    if item in {
        "blocked_2026_veteran_feature_rows",
        "top_priority_waived_players_missing_features",
    }:
        return "do_not_score_without_valid_features"
    if item == "rookie_rows":
        return "exclude_from_veteran_heads"
    if item == "kicker_rows":
        return "not_applicable"
    if item == "ready_2026_veteran_feature_rows":
        return "eligible_for_internal_research_only"
    return "audit_only_no_release_permission"


def _affected_player_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return len({(row["position"], row["current_player_id"]) for row in rows})


def _max_gap(rows: Sequence[Mapping[str, Any]]) -> float:
    if not rows:
        return 0.0
    return round(max(float(row["violation_gap"]) for row in rows), 6)


def _max_abs_delta(rows: Sequence[Mapping[str, Any]]) -> float:
    if not rows:
        return 0.0
    return round(max(float(row["abs_repair_delta"]) for row in rows), 6)


def _avg_abs_delta(rows: Sequence[Mapping[str, Any]]) -> float:
    if not rows:
        return 0.0
    return round(
        sum(float(row["abs_repair_delta"]) for row in rows) / len(rows),
        6,
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = _fieldnames(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_readme(path: Path, metadata: Mapping[str, Any]) -> None:
    path.write_text(
        "\n".join(
            [
                "# Sprint 5BF Internal Constrained/Ordinal Prototype",
                "",
                "Verdict: `CONSTRAINED_ORDINAL_PROTOTYPE_INTERNAL_ONLY_CONTINUE`",
                "",
                "These artifacts are internal-only research outputs.",
                "They are not app-readable, not player-facing, not release artifacts,",
                "and not promoted model artifacts.",
                "",
                f"Raw violations: {metadata['raw_violation_count']}",
                f"Clamped violations: {metadata['clamped_violation_count']}",
                f"Constrained violations: {metadata['constrained_violation_count']}",
                f"Output scope: `{metadata['output_scope']}`",
                "",
                "Exact percentages remain blocked. App wiring remains blocked.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _fieldnames(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    return keys or ["empty"]


def all_rows_are_quarantined(rows: Iterable[Mapping[str, Any]]) -> bool:
    for row in rows:
        if row.get("output_scope") != OUTPUT_SCOPE:
            return False
        if row.get("app_release_status") != APP_RELEASE_STATUS:
            return False
        if row.get("sort_allowed", "no") != "no":
            return False
        if row.get("ranking_use_allowed", "no") != "no":
            return False
    return True
