"""Run guarded local-only rookie ranking tuning experiments v1.

Tuning is allowed only after the label integration backtest produces usable
complete-window baseline rows. Results are experimental/manual-use-only and do
not replace production rankings, private scores, app outputs, probabilities,
bands, hidden sort keys, or promoted artifacts.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


DEFAULT_BACKTEST_DIR = Path("local_exports/rookie_framework/backtest_label_integration_tuning_v1_20260615")
DEFAULT_OUTPUT_DIR = DEFAULT_BACKTEST_DIR
LEGACY_OUTPUT_DIR = Path("local_exports/rookie_framework/tuning_loop_v1_20260615")

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

CANDIDATE_WEIGHTS = {
    "baseline_v1": BASELINE_WEIGHTS,
    "star_capture_plus": {
        **BASELINE_WEIGHTS,
        "star_upside_index": 0.34,
        "long_term_value_index": 0.19,
        "bust_risk_index": -0.28,
        "warning_penalty_index": -0.10,
    },
    "bust_avoidance_plus": {
        **BASELINE_WEIGHTS,
        "star_upside_index": 0.29,
        "bust_risk_index": -0.34,
        "warning_penalty_index": -0.13,
        "evidence_confidence_index": 0.13,
    },
    "non_ppr_role_plus": {
        **BASELINE_WEIGHTS,
        "early_role_index": 0.22,
        "scoring_fit_index": 0.17,
        "star_upside_index": 0.29,
        "bust_risk_index": -0.29,
    },
    "qb_devalue_plus": {
        **BASELINE_WEIGHTS,
        "positional_adjustment_index": 0.11,
        "scoring_fit_index": 0.16,
        "star_upside_index": 0.28,
        "bust_risk_index": -0.30,
    },
}

COMPONENT_COLUMNS = [
    "star_upside_index",
    "bust_risk_index",
    "early_role_index",
    "long_term_value_index",
    "scoring_fit_index",
    "evidence_confidence_index",
    "positional_adjustment_index",
    "warning_penalty_index",
]

RESULT_COLUMNS = [
    "candidate_id",
    "candidate_label",
    "train_years",
    "validation_year",
    "train_rows",
    "validation_rows",
    "train_top12_star_capture",
    "train_top24_bust_rate",
    "validation_top12_star_capture",
    "validation_top24_bust_rate",
    "validation_top36_bust_rate",
    "validation_low_ranked_star_misses",
    "improved_validation_vs_baseline",
    "overfit_warning",
    "production_allowed",
    "notes",
]

LEGACY_CANDIDATE_COLUMNS = ["candidate_id", "candidate_type", "weight_summary", "status", "notes"]
LEGACY_RESULT_COLUMNS = ["candidate_id", "validation_method", "star_capture_change", "bust_avoidance_change", "status", "notes"]
LEGACY_RECOMMENDATION_COLUMNS = ["recommendation", "reason", "production_allowed", "safe_next_step"]


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


def to_float(value: str, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


def backtest_join_is_usable(backtest_dir: Path) -> tuple[bool, str]:
    audit = read_csv(backtest_dir / "rookie_backtest_join_audit_20260615.csv")
    if not audit:
        return False, "join audit missing"
    complete_years = [row for row in audit if row.get("draft_year") in {"2021", "2022", "2023"}]
    if not complete_years:
        return False, "complete-window join audit rows missing"
    bad = [row for row in complete_years if row.get("join_status") != "GREEN"]
    if bad:
        return False, "complete-window join status is not GREEN"
    return True, "complete-window 2021-2023 join is GREEN"


def score_row(row: dict[str, str], weights: dict[str, float]) -> float:
    return round(sum(to_float(row.get(column, "")) * weights[column] for column in COMPONENT_COLUMNS), 3)


def ranked(rows: list[dict[str, str]], weights: dict[str, float]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        copy = dict(row)
        copy["candidate_score"] = f"{score_row(row, weights):.3f}"
        output.append(copy)
    output.sort(key=lambda item: (-to_float(item["candidate_score"]), to_float(item.get("draft_pick", ""), 999), item["prospect_name"]))
    for index, row in enumerate(output, start=1):
        row["candidate_rank"] = str(index)
    return output


def metrics(rows: list[dict[str, str]], weights: dict[str, float], years: set[str]) -> dict[str, float]:
    scoped = [row for row in rows if row.get("draft_year") in years]
    ranked_rows = ranked(scoped, weights)
    stars_total = sum(1 for row in ranked_rows if row.get("label_star_flag") == "1")
    top12 = ranked_rows[:12]
    top24 = ranked_rows[:24]
    top36 = ranked_rows[:36]
    top12_stars = sum(1 for row in top12 if row.get("label_star_flag") == "1")
    top24_busts = sum(1 for row in top24 if row.get("label_bust_flag") == "1")
    top36_busts = sum(1 for row in top36 if row.get("label_bust_flag") == "1")
    low_ranked_stars = sum(1 for row in ranked_rows[36:] if row.get("label_star_flag") == "1")
    return {
        "rows": float(len(ranked_rows)),
        "top12_star_capture": (top12_stars / stars_total) if stars_total else 0.0,
        "top24_bust_rate": (top24_busts / len(top24)) if top24 else 0.0,
        "top36_bust_rate": (top36_busts / len(top36)) if top36 else 0.0,
        "low_ranked_star_misses": float(low_ranked_stars),
    }


def run_experiments(scored_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    baseline_validation = metrics(scored_rows, BASELINE_WEIGHTS, {"2023"})
    results = []
    for candidate_id, weights in CANDIDATE_WEIGHTS.items():
        train = metrics(scored_rows, weights, {"2021", "2022"})
        validation = metrics(scored_rows, weights, {"2023"})
        improved = (
            validation["top12_star_capture"] >= baseline_validation["top12_star_capture"]
            and validation["top24_bust_rate"] <= baseline_validation["top24_bust_rate"]
            and validation["low_ranked_star_misses"] <= baseline_validation["low_ranked_star_misses"]
        )
        overfit = "yes" if train["top12_star_capture"] > baseline_validation["top12_star_capture"] + 0.25 and not improved else "no"
        results.append(
            {
                "candidate_id": candidate_id,
                "candidate_label": "ROOKIE_DRAFT_RANKING_V2_CANDIDATE_MANUAL_USE_ONLY" if candidate_id != "baseline_v1" else "baseline_v1",
                "train_years": "2021|2022",
                "validation_year": "2023",
                "train_rows": str(int(train["rows"])),
                "validation_rows": str(int(validation["rows"])),
                "train_top12_star_capture": f"{train['top12_star_capture']:.3f}",
                "train_top24_bust_rate": f"{train['top24_bust_rate']:.3f}",
                "validation_top12_star_capture": f"{validation['top12_star_capture']:.3f}",
                "validation_top24_bust_rate": f"{validation['top24_bust_rate']:.3f}",
                "validation_top36_bust_rate": f"{validation['top36_bust_rate']:.3f}",
                "validation_low_ranked_star_misses": str(int(validation["low_ranked_star_misses"])),
                "improved_validation_vs_baseline": "yes" if improved and candidate_id != "baseline_v1" else "baseline" if candidate_id == "baseline_v1" else "no",
                "overfit_warning": overfit,
                "production_allowed": "no",
                "notes": "experimental local-only candidate; no official board replacement",
            }
        )
    return results


def weight_summary(weights: dict[str, float]) -> str:
    return "; ".join(f"{key}={value}" for key, value in weights.items())


def write_readme(output_dir: Path, tuning_ran: bool, reason: str) -> None:
    text = f"""# Rookie Tuning Loop v1

Status: {'local-only experimental tuning ran' if tuning_ran else 'blocked scaffold only'}.

Reason: {reason}

Candidate outputs are manual-use-only experiments. No tuned weights are promoted,
and no production ranking, app output, probability, band, hidden sort key, or
private score is created.
"""
    (output_dir / "README_ROOKIE_TUNING_LOOP_V1_20260615.md").write_text(text, encoding="utf-8")


def write_legacy_outputs(output_dir: Path, results: list[dict[str, str]], tuning_ran: bool, reason: str) -> None:
    candidate_rows = [
        {
            "candidate_id": candidate_id,
            "candidate_type": "baseline" if candidate_id == "baseline_v1" else "guarded_candidate",
            "weight_summary": weight_summary(weights),
            "status": "evaluated_local_only" if tuning_ran else "defined_not_run",
            "notes": "manual-use-only; production_allowed=no",
        }
        for candidate_id, weights in CANDIDATE_WEIGHTS.items()
    ]
    legacy_results = [
        {
            "candidate_id": row.get("candidate_id", "baseline_v1"),
            "validation_method": "train_2021_2022_validate_2023" if tuning_ran else "not_run",
            "star_capture_change": row.get("validation_top12_star_capture", "not_computed") if tuning_ran else "not_computed",
            "bust_avoidance_change": row.get("validation_top24_bust_rate", "not_computed") if tuning_ran else "not_computed",
            "status": "evaluated_no_promotion" if tuning_ran else "blocked_missing_label_backtest",
            "notes": row.get("notes", reason),
        }
        for row in (results if results else [{"candidate_id": "baseline_v1", "notes": reason}])
    ]
    recommendation = [
        {
            "recommendation": "review_candidate_results_only" if tuning_ran else "do_not_tune_yet",
            "reason": reason,
            "production_allowed": "no",
            "safe_next_step": "manual review of validation results before any separate candidate-board proposal",
        }
    ]
    write_csv(output_dir / "rookie_tuning_candidates_v1_20260615.csv", candidate_rows, LEGACY_CANDIDATE_COLUMNS)
    write_csv(output_dir / "rookie_tuning_results_v1_20260615.csv", legacy_results, LEGACY_RESULT_COLUMNS)
    write_csv(output_dir / "rookie_tuning_recommendation_v1_20260615.csv", recommendation, LEGACY_RECOMMENDATION_COLUMNS)
    write_readme(output_dir, tuning_ran, reason)


def build_exports(backtest_dir: Path, output_dir: Path, legacy_output_dir: Path = LEGACY_OUTPUT_DIR) -> dict[str, int]:
    usable, reason = backtest_join_is_usable(backtest_dir)
    scored_rows = read_csv(backtest_dir / "rookie_baseline_scored_rows_20260615.csv")
    results: list[dict[str, str]] = []
    tuning_ran = False
    if usable and scored_rows:
        results = run_experiments(scored_rows)
        tuning_ran = True
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_tuning_experiment_results_20260615.csv", results, RESULT_COLUMNS)
    write_legacy_outputs(legacy_output_dir, results, tuning_ran, reason)
    write_readme(output_dir, tuning_ran, reason)
    return {
        "candidate_rows": len(CANDIDATE_WEIGHTS),
        "result_rows": len(results),
        "recommendation_rows": 1,
        "tuning_ran": 1 if tuning_ran else 0,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run guarded rookie ranking tuning experiments v1.")
    parser.add_argument("--backtest-dir", type=Path, default=DEFAULT_BACKTEST_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--legacy-output-dir", type=Path, default=LEGACY_OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        counts = build_exports(args.backtest_dir, args.output_dir, args.legacy_output_dir)
    except RookieTuningError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
