"""Guarded rookie ranking tuning scaffold v1.

Tuning is allowed only when historical backtest labels/results exist. This
script writes explicit not-run exports when the data is insufficient.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


DEFAULT_BACKTEST_DIR = Path("local_exports/rookie_framework/historical_backtest_v1_20260615")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/tuning_loop_v1_20260615")

BASELINE_WEIGHTS = {
    "star_upside_index": 0.30,
    "early_role_index": 0.18,
    "long_term_value_index": 0.18,
    "scoring_fit_index": 0.14,
    "evidence_confidence_index": 0.12,
    "positional_adjustment_index": 0.08,
    "bust_risk_index": -0.28,
    "warning_penalty_index": -0.10,
}

TUNING_COLUMNS = ["candidate_id", "candidate_type", "weight_summary", "status", "notes"]
RESULT_COLUMNS = ["candidate_id", "validation_method", "star_capture_change", "bust_avoidance_change", "status", "notes"]
RECOMMENDATION_COLUMNS = ["recommendation", "reason", "production_allowed", "safe_next_step"]


class RookieTuningError(RuntimeError):
    """Raised when tuning scaffold fails."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def backtest_has_labels(backtest_dir: Path) -> tuple[bool, str]:
    inventory = read_csv(backtest_dir / "rookie_historical_backtest_inventory_20260615.csv")
    if not inventory:
        return False, "backtest inventory missing"
    row = inventory[0]
    if row.get("backtest_runnable") != "yes":
        return False, row.get("reason", "backtest not runnable")
    labels = row.get("label_columns", "")
    if not labels:
        return False, "backtest inventory has no label columns"
    return True, "label-backed backtest inventory exists"


def build_exports(backtest_dir: Path, output_dir: Path) -> dict[str, int]:
    runnable, reason = backtest_has_labels(backtest_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_summary = "; ".join(f"{key}={value}" for key, value in BASELINE_WEIGHTS.items())
    candidates = [
        {
            "candidate_id": "baseline_v1",
            "candidate_type": "baseline_retained",
            "weight_summary": baseline_summary,
            "status": "retained",
            "notes": "Baseline is retained for rollback and comparison.",
        }
    ]
    results = []
    if runnable:
        candidates.extend(
            [
                {
                    "candidate_id": "star_plus_small",
                    "candidate_type": "guarded_candidate",
                    "weight_summary": "increase star_upside_index by 0.03; decrease warning penalty by 0.01",
                    "status": "candidate_defined_not_promoted",
                    "notes": "Requires leave-one-year-out validation before use.",
                },
                {
                    "candidate_id": "bust_avoidance_plus_small",
                    "candidate_type": "guarded_candidate",
                    "weight_summary": "increase bust_risk_index penalty by 0.03; retain baseline scoring fit",
                    "status": "candidate_defined_not_promoted",
                    "notes": "Requires validation that star capture does not collapse.",
                },
            ]
        )
        results.append(
            {
                "candidate_id": "baseline_v1",
                "validation_method": "not_run_in_v1_scaffold",
                "star_capture_change": "not_computed",
                "bust_avoidance_change": "not_computed",
                "status": "requires_explicit_backtest_metric_runner",
                "notes": "Labels detected, but v1 tuning still does not promote weights.",
            }
        )
    else:
        results.append(
            {
                "candidate_id": "baseline_v1",
                "validation_method": "not_run",
                "star_capture_change": "not_computed",
                "bust_avoidance_change": "not_computed",
                "status": "blocked_missing_label_backtest",
                "notes": reason,
            }
        )
    recommendation = [
        {
            "recommendation": "do_not_tune_yet" if not runnable else "define_candidates_only",
            "reason": reason,
            "production_allowed": "no",
            "safe_next_step": "add point-in-time historical outcome labels and run leave-one-year-out validation",
        }
    ]
    write_csv(output_dir / "rookie_tuning_candidates_v1_20260615.csv", candidates, TUNING_COLUMNS)
    write_csv(output_dir / "rookie_tuning_results_v1_20260615.csv", results, RESULT_COLUMNS)
    write_csv(output_dir / "rookie_tuning_recommendation_v1_20260615.csv", recommendation, RECOMMENDATION_COLUMNS)
    write_readme(output_dir, runnable, reason)
    return {"candidate_rows": len(candidates), "result_rows": len(results), "recommendation_rows": len(recommendation), "tuning_ran": 1 if runnable else 0}


def write_readme(output_dir: Path, runnable: bool, reason: str) -> None:
    text = f"""# Rookie Tuning Loop v1

Status: {'candidate scaffold only' if runnable else 'blocked scaffold only'}.

Reason: {reason}

The baseline remains retained. No tuned weights are promoted, and no production
ranking, app output, probability, band, hidden sort key, or private score is
created.
"""
    (output_dir / "README_ROOKIE_TUNING_LOOP_V1_20260615.md").write_text(text, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build guarded rookie ranking tuning scaffold v1.")
    parser.add_argument("--backtest-dir", type=Path, default=DEFAULT_BACKTEST_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.backtest_dir, args.output_dir)
    except RookieTuningError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
