"""Audit expanded rookie baseline metrics before any tuning.

This script is local/export-only. It does not tune, create a v2 board, promote
artifacts, or write app-readable outputs.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_historical_allowlist_qa_expanded_baseline_v1 import (
    baseline_rows,
    to_float,
)


DEFAULT_EXPANDED_DIR = Path("local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615")
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/expanded_pool_baseline_audit_tuning_readiness_20260615")
LABEL_FILE = "expanded_historical_labels_v2_20260615.csv"

BUCKETS = (12, 24, 36)
YEARS = [str(year) for year in range(2010, 2024)]
PERIODS = {
    "2010_2014": {str(year) for year in range(2010, 2015)},
    "2015_2019": {str(year) for year in range(2015, 2020)},
    "2020_2023": {str(year) for year in range(2020, 2024)},
    "2010_2023_full": set(YEARS),
}
POSITIONS = ("QB", "RB", "WR", "TE")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def safe_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def avg(values: list[float]) -> str:
    return f"{sum(values) / len(values):.3f}" if values else ""


def rate(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.3f}" if denominator else "0.000"


def complete_rows(labels: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in labels if row.get("backtest_ready") == "yes" and row.get("partial_window_only") == "no"]


def selected_by_year(rows: list[dict[str, str]], years: set[str], bucket: int) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for year in sorted(years):
        year_rows = [row for row in rows if row["draft_year"] == year]
        selected.extend([row for row in year_rows if safe_int(row.get("class_rank", "999999")) <= bucket])
    return selected


def metric_row(scope: str, value: str, rows: list[dict[str, str]], selected: list[dict[str, str]], bucket: int) -> dict[str, str]:
    stars_total = sum(1 for row in rows if row["star_label"] == "1")
    busts_total = sum(1 for row in rows if row["bust_label"] == "1")
    stars_selected = sum(1 for row in selected if row["star_label"] == "1")
    busts_selected = sum(1 for row in selected if row["bust_label"] == "1")
    statuses = Counter(row["historical_label_status"] for row in rows)
    return {
        "metric_scope": scope,
        "scope_value": value,
        "bucket": f"top_{bucket}",
        "row_count": str(len(rows)),
        "selected_rows": str(len(selected)),
        "stars_total": str(stars_total),
        "stars_captured": str(stars_selected),
        "star_capture_rate": rate(stars_selected, stars_total),
        "bust_total": str(busts_total),
        "bust_count_selected": str(busts_selected),
        "bust_rate_selected": rate(busts_selected, len(selected)),
        "avg_selected_three_year_points": avg([to_float(row["three_year_points"]) for row in selected]),
        "label_quality_notes": "; ".join(f"{key}={value}" for key, value in sorted(statuses.items())),
        "notes": "year-class Top-N is draft-realistic; labels remain evaluation-only",
    }


def year_class_metrics(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for year in YEARS:
        scoped = [row for row in rows if row["draft_year"] == year]
        for bucket in BUCKETS:
            selected = [row for row in scoped if safe_int(row.get("class_rank", "999999")) <= bucket]
            output.append(metric_row("year_class", year, scoped, selected, bucket))
    for period, years in PERIODS.items():
        scoped = [row for row in rows if row["draft_year"] in years]
        for bucket in BUCKETS:
            output.append(metric_row("period_year_class", period, scoped, selected_by_year(rows, years, bucket), bucket))
    return output


def calibration_note(position: str, top_36_star_rate: float, top_36_bust_rate: float) -> str:
    if position == "QB":
        if top_36_star_rate < 0.20:
            return "1QB devaluation may be too harsh; diagnose without forcing QB promotion"
        return "1QB devaluation appears meaningful but not empty"
    if position == "TE":
        if top_36_star_rate < 0.25:
            return "TE capture is low; gate may be strict or draft-capital baseline lacks TE-specific signals"
        return "TE gate appears usable with continued caution"
    if top_36_bust_rate > 0.35:
        return "position may be too friendly to false positives"
    if top_36_star_rate < 0.25:
        return "position may need more upside-feature evidence before tuning"
    return "position balance is acceptable for baseline audit"


def position_metrics(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for position in POSITIONS:
        scoped = sorted(
            [row for row in rows if row["position"] == position],
            key=lambda row: (-to_float(row["baseline_score"]), to_float(row.get("overall_pick", ""), 999), row["player_name"]),
        )
        for index, row in enumerate(scoped, start=1):
            row["position_rank"] = str(index)
        stars_total = sum(1 for row in scoped if row["star_label"] == "1")
        top_36 = [row for row in scoped if safe_int(row.get("position_rank", "999999")) <= 36]
        top_36_star_rate = sum(1 for row in top_36 if row["star_label"] == "1") / stars_total if stars_total else 0.0
        top_36_bust_rate = sum(1 for row in top_36 if row["bust_label"] == "1") / len(top_36) if top_36 else 0.0
        note = calibration_note(position, top_36_star_rate, top_36_bust_rate)
        for bucket in BUCKETS:
            selected = [row for row in scoped if safe_int(row.get("position_rank", "999999")) <= bucket]
            output.append(
                {
                    "position": position,
                    "bucket": f"top_{bucket}",
                    "row_count": str(len(scoped)),
                    "selected_rows": str(len(selected)),
                    "stars_total": str(stars_total),
                    "stars_captured": str(sum(1 for row in selected if row["star_label"] == "1")),
                    "star_capture_rate": rate(sum(1 for row in selected if row["star_label"] == "1"), stars_total),
                    "bust_total": str(sum(1 for row in scoped if row["bust_label"] == "1")),
                    "bust_count_selected": str(sum(1 for row in selected if row["bust_label"] == "1")),
                    "bust_rate_selected": rate(sum(1 for row in selected if row["bust_label"] == "1"), len(selected)),
                    "avg_global_rank": avg([to_float(row.get("baseline_rank", "")) for row in scoped]),
                    "avg_class_rank": avg([to_float(row.get("class_rank", "")) for row in scoped]),
                    "calibration_note": note,
                }
            )
    return output


def classify_missed_star(row: dict[str, str]) -> tuple[str, str]:
    round_no = safe_int(row.get("draft_round", ""))
    pick = safe_int(row.get("overall_pick", ""))
    position = row.get("position", "")
    if row.get("historical_label_status") != "GREEN_COMPLETE":
        return "label_issue", "resolve label quality before using this row for tuning"
    if round_no >= 4 or pick > 100:
        return "late_outlier_low_signal", "late-pick stars are diagnosable but should not create player-specific rules"
    if position == "QB":
        return "scoring_format_issue", "1QB devaluation may suppress some historical QB stars"
    if position == "TE":
        return "position_calibration_issue", "TE-specific development/usage features may be underrepresented"
    if round_no <= 3:
        return "true_model_miss", "draft-capital/position baseline lacks college production and role/archetype feature families"
    return "needs_human_review", "generalizable feature-family diagnosis needed before tuning"


def classify_high_bust(row: dict[str, str]) -> tuple[str, str]:
    if row.get("historical_label_status") != "GREEN_COMPLETE":
        return "label_issue", "label quality needs review before tuning against this bust"
    if safe_int(row.get("draft_round", "")) == 1:
        return "draft_capital_trap", "baseline may overtrust early draft capital without enough bust-warning evidence"
    if row.get("position") in {"QB", "TE"}:
        return "position_calibration_issue", "position-specific gates may need later review"
    return "true_model_false_positive", "later tuning should test general warning/gate families only"


def diagnostic_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    stars = [
        row
        for row in rows
        if row["star_label"] == "1" and safe_int(row.get("baseline_rank", "999999")) > 36
    ]
    stars.sort(key=lambda row: (safe_int(row.get("baseline_rank", "999999")), -to_float(row["three_year_points"])))
    busts = [
        row
        for row in rows
        if row["bust_label"] == "1" and safe_int(row.get("baseline_rank", "999999")) <= 36
    ]
    busts.sort(key=lambda row: safe_int(row.get("baseline_rank", "999999")))
    star_output = []
    for row in stars[:30]:
        classification, hypothesis = classify_missed_star(row)
        star_output.append(
            {
                "baseline_rank": row["baseline_rank"],
                "class_rank": row["class_rank"],
                "draft_year": row["draft_year"],
                "player_name": row["player_name"],
                "position": row["position"],
                "draft_round": row["draft_round"],
                "overall_pick": row["overall_pick"],
                "baseline_score": row["baseline_score"],
                "three_year_points": row["three_year_points"],
                "best_first_3_years_pos_finish": row["best_first_3_years_pos_finish"],
                "historical_label_status": row["historical_label_status"],
                "diagnostic_classification": classification,
                "feature_family_hypothesis": hypothesis,
                "anti_cheat_note": "diagnosis only; no player-specific tuning",
            }
        )
    bust_output = []
    for row in busts:
        classification, hypothesis = classify_high_bust(row)
        bust_output.append(
            {
                "baseline_rank": row["baseline_rank"],
                "class_rank": row["class_rank"],
                "draft_year": row["draft_year"],
                "player_name": row["player_name"],
                "position": row["position"],
                "draft_round": row["draft_round"],
                "overall_pick": row["overall_pick"],
                "baseline_score": row["baseline_score"],
                "three_year_points": row["three_year_points"],
                "historical_label_status": row["historical_label_status"],
                "diagnostic_classification": classification,
                "warning_gate_hypothesis": hypothesis,
                "anti_cheat_note": "diagnosis only; no player-specific tuning",
            }
        )
    return star_output, bust_output


def feature_family_hypotheses(stars: list[dict[str, str]], busts: list[dict[str, str]]) -> list[dict[str, str]]:
    star_counts = Counter(row["diagnostic_classification"] for row in stars)
    bust_counts = Counter(row["diagnostic_classification"] for row in busts)
    rows = [
        {
            "hypothesis_area": "metric_semantics",
            "evidence_count": "1",
            "general_hypothesis": "year-class Top-N should be the primary draft-realistic metric; global Top-N is a rough pool diagnostic only",
            "allowed_next_action": "use year-class metrics for tuning gate design",
            "blocked_action": "do not tune to global Top-N alone",
        },
        {
            "hypothesis_area": "upside_features",
            "evidence_count": str(star_counts.get("true_model_miss", 0)),
            "general_hypothesis": "draft-capital/position baseline likely misses college production, target/rush earning, explosive play, and role/archetype upside families",
            "allowed_next_action": "test feature-family weights in a later approved tuning task",
            "blocked_action": "do not add player-specific boosts",
        },
        {
            "hypothesis_area": "late_outlier_handling",
            "evidence_count": str(star_counts.get("late_outlier_low_signal", 0)),
            "general_hypothesis": "late-pick stars require upside signal families but should remain capped without evidence",
            "allowed_next_action": "audit general upside indicators before tuning",
            "blocked_action": "do not tune around named late outliers",
        },
        {
            "hypothesis_area": "position_calibration",
            "evidence_count": str(star_counts.get("position_calibration_issue", 0) + bust_counts.get("position_calibration_issue", 0)),
            "general_hypothesis": "QB/TE/RB/WR balance should be evaluated separately under 1QB non-PPR first-down scoring",
            "allowed_next_action": "use position-level holdout validation in a later tuning task",
            "blocked_action": "do not force position promotions from diagnostics alone",
        },
        {
            "hypothesis_area": "draft_capital_trap",
            "evidence_count": str(bust_counts.get("draft_capital_trap", 0)),
            "general_hypothesis": "early draft capital alone can create false positives; later tuning should test general warning/gate families",
            "allowed_next_action": "evaluate warning visibility and bust gates later",
            "blocked_action": "do not special-case historical bust names",
        },
        {
            "hypothesis_area": "label_quality",
            "evidence_count": str(star_counts.get("label_issue", 0) + bust_counts.get("label_issue", 0)),
            "general_hypothesis": "label-caveat rows should stay visible and may be excluded from sensitive tuning slices",
            "allowed_next_action": "repair labels before using them for tuning validation",
            "blocked_action": "do not use label issues to change scoring features",
        },
    ]
    return rows


def semantics_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    stars_total = sum(1 for row in rows if row["star_label"] == "1")
    return [
        {
            "metric_name": "global_pool_top_n",
            "metric_type": "global",
            "star_capture_denominator": f"all stars in complete-window pool ({stars_total})",
            "bust_rate_denominator": "selected Top-N rows from entire complete-window pool",
            "draft_realism": "low_to_medium",
            "interpretation": "useful rough diagnostic, but not draft-realistic because Tim drafts one class at a time",
        },
        {
            "metric_name": "year_class_top_n",
            "metric_type": "year_class",
            "star_capture_denominator": "stars in that draft year or stars in period when aggregating per-year selections",
            "bust_rate_denominator": "selected Top-N rows within each draft class",
            "draft_realism": "high",
            "interpretation": "primary metric family for rookie draft simulation and tuning gates",
        },
        {
            "metric_name": "position_top_n",
            "metric_type": "position",
            "star_capture_denominator": "stars within the position",
            "bust_rate_denominator": "selected Top-N rows within the position",
            "draft_realism": "medium",
            "interpretation": "useful for diagnosing 1QB, TE strictness, RB/WR balance, and position calibration",
        },
    ]


def decision_rows(labels: list[dict[str, str]], stars: list[dict[str, str]], busts: list[dict[str, str]]) -> list[dict[str, str]]:
    status_counts = Counter(row["historical_label_status"] for row in labels)
    excluded = status_counts.get("EXCLUDED", 0)
    partial = status_counts.get("YELLOW_PARTIAL_WINDOW", 0)
    return [
        {"gate": "label_quality", "verdict": "YELLOW", "rationale": f"labels are usable for audit, but {excluded} excluded rows and {partial} partial rows remain"},
        {"gate": "metric_quality", "verdict": "GREEN", "rationale": "global, year-class, period, and position metrics are separated with denominators documented"},
        {"gate": "anti_cheat_leakage", "verdict": "GREEN", "rationale": "diagnostics use names only for reporting; no tuning or player-specific rules"},
        {"gate": "expanded_baseline_trust", "verdict": "YELLOW", "rationale": "baseline is trustworthy as a no-tuning diagnostic, but too draft-capital/position-limited for final model judgment"},
        {"gate": "tuning_readiness", "verdict": "YELLOW", "rationale": "safe to prepare a separate tightly gated tuning prompt, but do not tune before label caveats and holdout design are accepted"},
        {"gate": "manual_draft_trust", "verdict": "YELLOW", "rationale": "manual use can reference advisory boards with warnings, but expanded baseline alone is not a draft board"},
        {"gate": "diagnostic_coverage", "verdict": "GREEN", "rationale": f"classified {len(stars)} top missed stars and {len(busts)} high-ranked busts"},
    ]


def build_exports(expanded_dir: Path, output_dir: Path) -> dict[str, int]:
    labels = read_csv(expanded_dir / LABEL_FILE)
    rows = baseline_rows(complete_rows(labels))
    year_rows = year_class_metrics(rows)
    pos_rows = position_metrics(rows)
    missed_stars, high_busts = diagnostic_rows(rows)
    hypothesis_rows = feature_family_hypotheses(missed_stars, high_busts)
    semantic_rows = semantics_rows(rows)
    decisions = decision_rows(labels, missed_stars, high_busts)

    write_csv(
        output_dir / "metric_semantics_audit_20260615.csv",
        semantic_rows,
        ["metric_name", "metric_type", "star_capture_denominator", "bust_rate_denominator", "draft_realism", "interpretation"],
    )
    write_csv(
        output_dir / "year_class_baseline_metrics_20260615.csv",
        year_rows,
        [
            "metric_scope",
            "scope_value",
            "bucket",
            "row_count",
            "selected_rows",
            "stars_total",
            "stars_captured",
            "star_capture_rate",
            "bust_total",
            "bust_count_selected",
            "bust_rate_selected",
            "avg_selected_three_year_points",
            "label_quality_notes",
            "notes",
        ],
    )
    write_csv(
        output_dir / "position_baseline_metrics_20260615.csv",
        pos_rows,
        [
            "position",
            "bucket",
            "row_count",
            "selected_rows",
            "stars_total",
            "stars_captured",
            "star_capture_rate",
            "bust_total",
            "bust_count_selected",
            "bust_rate_selected",
            "avg_global_rank",
            "avg_class_rank",
            "calibration_note",
        ],
    )
    write_csv(
        output_dir / "top_missed_stars_diagnostic_20260615.csv",
        missed_stars,
        [
            "baseline_rank",
            "class_rank",
            "draft_year",
            "player_name",
            "position",
            "draft_round",
            "overall_pick",
            "baseline_score",
            "three_year_points",
            "best_first_3_years_pos_finish",
            "historical_label_status",
            "diagnostic_classification",
            "feature_family_hypothesis",
            "anti_cheat_note",
        ],
    )
    write_csv(
        output_dir / "high_ranked_busts_diagnostic_20260615.csv",
        high_busts,
        [
            "baseline_rank",
            "class_rank",
            "draft_year",
            "player_name",
            "position",
            "draft_round",
            "overall_pick",
            "baseline_score",
            "three_year_points",
            "historical_label_status",
            "diagnostic_classification",
            "warning_gate_hypothesis",
            "anti_cheat_note",
        ],
    )
    write_csv(
        output_dir / "feature_family_hypotheses_20260615.csv",
        hypothesis_rows,
        ["hypothesis_area", "evidence_count", "general_hypothesis", "allowed_next_action", "blocked_action"],
    )
    write_csv(
        output_dir / "tuning_readiness_decision_20260615.csv",
        decisions,
        ["gate", "verdict", "rationale"],
    )
    readme = output_dir / "README_ROOKIE_EXPANDED_POOL_BASELINE_AUDIT_TUNING_READINESS_20260615.md"
    readme.write_text(
        "# Rookie Expanded-Pool Baseline Audit / Tuning Readiness\n\n"
        "Local-only audit exports. No tuning, v2 board, probabilities, bands, app wiring, or promoted artifacts.\n",
        encoding="utf-8",
    )
    return {
        "label_rows": len(labels),
        "complete_rows": len(rows),
        "year_metric_rows": len(year_rows),
        "position_metric_rows": len(pos_rows),
        "missed_star_rows": len(missed_stars),
        "high_bust_rows": len(high_busts),
        "hypothesis_rows": len(hypothesis_rows),
        "decision_rows": len(decisions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expanded-dir", type=Path, default=DEFAULT_EXPANDED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build_exports(args.expanded_dir, args.output_dir)
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
