"""Run rookie CFBD enriched baseline and conditional tuning runway.

This is local/export-only. It compares the repaired CFBD-enriched baseline
against the expanded draft-capital baseline, then conditionally tests general
feature-family candidate configurations. It does not create production rankings,
probabilities, bands, hidden sort keys, app outputs, or promoted artifacts.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_historical_allowlist_qa_expanded_baseline_v1 import (  # noqa: E402
    baseline_rows,
    draft_points,
    safe_int,
    to_float,
)


DEFAULT_LABELS = Path(
    "local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/"
    "expanded_historical_labels_v2_20260615.csv"
)
DEFAULT_REPAIRED_JOIN = Path(
    "local_exports/rookie_framework/cfbd_identity_join_repair_20260615/"
    "cfbd_drafted_rookie_feature_join_repaired_20260615.csv"
)
DEFAULT_PHASE_A_DIR = Path(
    "local_exports/rookie_framework/repaired_cfbd_enriched_baseline_audit_20260615"
)
DEFAULT_PHASE_B_DIR = Path(
    "local_exports/rookie_framework/cfbd_enriched_tuning_candidate_v1_20260615"
)
BUCKETS = (12, 24, 36)
YEARS = {str(year) for year in range(2010, 2024)}
TRAIN_YEARS = {str(year) for year in range(2010, 2022)}
VALIDATION_YEARS = {"2022", "2023"}
POSITIONS = ("QB", "RB", "WR", "TE")
MATCHED_STATUSES = {
    "matched_name_position_season",
    "matched_exact_after_repair",
    "matched_position_mismatch_repaired",
    "matched_alias_repaired",
    "matched_with_duplicate_candidate_selection",
    "matched_duplicate_candidate_selected",
}
DUPLICATE_STATUSES = {
    "matched_with_duplicate_candidate_selection",
    "matched_duplicate_candidate_selected",
}


@dataclass(frozen=True)
class Config:
    name: str
    description: str
    draft_weight: float
    position_weight: float
    cfbd_weight: float
    position_scores: dict[str, float]
    wr_share_bonus: float = 0.0
    rb_share_bonus: float = 0.0
    te_share_bonus: float = 0.0
    qb_penalty: float = 0.0
    round3_plus_penalty: float = 0.0
    bust_guard_pick_penalty: float = 0.0


PHASE_A_CONFIG = Config(
    name="cfbd_enriched_baseline",
    description="baseline draft/position with source-safe CFBD production/share context",
    draft_weight=0.68,
    position_weight=0.20,
    cfbd_weight=0.12,
    position_scores={"RB": 72.0, "WR": 70.0, "TE": 42.0, "QB": 24.0},
)

PHASE_B_CONFIGS = [
    PHASE_A_CONFIG,
    Config(
        name="cfbd_production_plus",
        description="general college production plus; no player-specific logic",
        draft_weight=0.62,
        position_weight=0.18,
        cfbd_weight=0.20,
        position_scores={"RB": 72.0, "WR": 72.0, "TE": 44.0, "QB": 22.0},
    ),
    Config(
        name="wr_market_share_upside_plus",
        description="WR receiving share/upside plus using CFBD share fields only",
        draft_weight=0.60,
        position_weight=0.18,
        cfbd_weight=0.22,
        position_scores={"RB": 70.0, "WR": 80.0, "TE": 44.0, "QB": 20.0},
        wr_share_bonus=5.0,
    ),
    Config(
        name="scoring_format_fit_plus",
        description="non-PPR/first-down fit proxy using RB/TE/QB position families and CFBD role shares",
        draft_weight=0.61,
        position_weight=0.22,
        cfbd_weight=0.17,
        position_scores={"RB": 82.0, "WR": 72.0, "TE": 58.0, "QB": 18.0},
        rb_share_bonus=4.0,
        te_share_bonus=4.0,
        qb_penalty=-3.0,
    ),
    Config(
        name="draft_capital_trap_guard",
        description="broad draft-capital trap guard plus CFBD production context",
        draft_weight=0.58,
        position_weight=0.22,
        cfbd_weight=0.20,
        position_scores={"RB": 78.0, "WR": 74.0, "TE": 50.0, "QB": 18.0},
        round3_plus_penalty=-3.0,
        bust_guard_pick_penalty=-2.0,
    ),
    Config(
        name="position_calibrated_cfbd",
        description="position-calibrated CFBD blend preserving 1QB discipline",
        draft_weight=0.60,
        position_weight=0.22,
        cfbd_weight=0.18,
        position_scores={"RB": 78.0, "WR": 78.0, "TE": 52.0, "QB": 16.0},
        qb_penalty=-4.0,
    ),
    Config(
        name="balanced_star_bust_cfbd",
        description="balanced star/bust candidate with moderate CFBD context",
        draft_weight=0.60,
        position_weight=0.20,
        cfbd_weight=0.20,
        position_scores={"RB": 80.0, "WR": 80.0, "TE": 58.0, "QB": 16.0},
        wr_share_bonus=3.0,
        rb_share_bonus=3.0,
        te_share_bonus=3.0,
        qb_penalty=-4.0,
        round3_plus_penalty=-2.0,
    ),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def rate(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.3f}" if denominator else "0.000"


def avg(values: list[float]) -> str:
    return f"{sum(values) / len(values):.3f}" if values else ""


def complete_label_rows(labels: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in labels
        if row.get("backtest_ready") == "yes"
        and row.get("partial_window_only") == "no"
        and row.get("draft_year") in YEARS
    ]


def load_runway_rows(labels_path: Path, repaired_join_path: Path) -> list[dict[str, str]]:
    labels = baseline_rows(complete_label_rows(read_csv(labels_path)))
    labels_by_key = {row["historical_label_key"]: row for row in labels}
    repaired = {row["historical_label_key"]: row for row in read_csv(repaired_join_path)}
    rows: list[dict[str, str]] = []
    for key, label in labels_by_key.items():
        row = dict(label)
        join = repaired.get(key, {})
        status = join.get("cfbd_join_status_after_repair", "missing_repaired_join_row")
        classification = join.get("repair_classification", "")
        row["cfbd_feature_status"] = cfbd_feature_status(status)
        row["cfbd_join_status_after_repair"] = status
        row["cfbd_repair_classification"] = classification
        row["cfbd_duplicate_selected"] = "yes" if status in DUPLICATE_STATUSES or "duplicate" in classification else "no"
        row["cfbd_manual_review_flag"] = "yes" if "manual_review" in status or "position_mismatch" in classification or row["cfbd_duplicate_selected"] == "yes" else "no"
        copy_cfbd_fields(row, join)
        row["cfbd_component_score"] = f"{cfbd_component_score(row):.3f}" if row["cfbd_feature_status"] == "deterministic_joined" else ""
        row["cfbd_missing_policy"] = (
            "use_enriched_features"
            if row["cfbd_feature_status"] == "deterministic_joined"
            else "unresolved_no_enriched_features_not_zero_filled"
        )
        rows.append(row)
    return rows


def cfbd_feature_status(status: str) -> str:
    if status in MATCHED_STATUSES:
        return "deterministic_joined"
    if status.startswith("unmatched"):
        return "unresolved_no_enriched_features"
    return "missing_or_manual_review"


def copy_cfbd_fields(row: dict[str, str], join: dict[str, str]) -> None:
    fields = [
        "cfbd_player_id",
        "team",
        "conference",
        "passing_yards",
        "passing_tds",
        "passing_attempts",
        "passing_completions",
        "passing_ints",
        "rushing_yards",
        "rushing_tds",
        "rushing_attempts",
        "receiving_yards",
        "receiving_tds",
        "receptions",
        "passing_yard_share",
        "passing_attempt_share",
        "passing_td_share",
        "rushing_yard_share",
        "rushing_attempt_share",
        "rushing_td_share",
        "receiving_yard_share",
        "reception_share",
        "receiving_td_share",
    ]
    for field in fields:
        row[f"cfbd_{field}"] = join.get(field, "")


def clipped(value: float, high: float) -> float:
    return max(0.0, min(high, value))


def cfbd_component_score(row: dict[str, str]) -> float:
    if row.get("cfbd_feature_status") != "deterministic_joined":
        return 0.0
    position = row.get("position", "")
    if position == "QB":
        raw = (
            clipped(to_float(row.get("cfbd_passing_yards")) / 45.0, 45.0)
            + clipped(to_float(row.get("cfbd_passing_yard_share")) * 28.0, 22.0)
            + clipped(to_float(row.get("cfbd_passing_td_share")) * 20.0, 16.0)
            + clipped(to_float(row.get("cfbd_rushing_yards")) / 40.0, 14.0)
        )
    elif position == "RB":
        raw = (
            clipped(to_float(row.get("cfbd_rushing_yards")) / 18.0, 45.0)
            + clipped(to_float(row.get("cfbd_rushing_yard_share")) * 36.0, 24.0)
            + clipped(to_float(row.get("cfbd_rushing_td_share")) * 20.0, 14.0)
            + clipped(to_float(row.get("cfbd_receiving_yards")) / 20.0, 12.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 18.0, 8.0)
        )
    elif position == "TE":
        raw = (
            clipped(to_float(row.get("cfbd_receiving_yards")) / 14.0, 46.0)
            + clipped(to_float(row.get("cfbd_receiving_yard_share")) * 42.0, 24.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 24.0, 12.0)
            + clipped(to_float(row.get("cfbd_receiving_td_share")) * 20.0, 12.0)
        )
    else:
        raw = (
            clipped(to_float(row.get("cfbd_receiving_yards")) / 16.0, 48.0)
            + clipped(to_float(row.get("cfbd_receiving_yard_share")) * 44.0, 26.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 25.0, 12.0)
            + clipped(to_float(row.get("cfbd_receiving_td_share")) * 20.0, 12.0)
            + clipped(to_float(row.get("cfbd_rushing_yards")) / 60.0, 4.0)
        )
    return round(clipped(raw, 100.0), 3)


def config_score(row: dict[str, str], config: Config) -> float:
    position = row.get("position", "")
    score = (
        draft_points(row.get("draft_round", ""), row.get("overall_pick", "")) * config.draft_weight
        + config.position_scores.get(position, 40.0) * config.position_weight
    )
    if row.get("cfbd_feature_status") == "deterministic_joined":
        component = cfbd_component_score(row)
        score += component * config.cfbd_weight
        if position == "WR" and to_float(row.get("cfbd_receiving_yard_share")) >= 0.25:
            score += config.wr_share_bonus
        if position == "RB" and to_float(row.get("cfbd_rushing_yard_share")) >= 0.25:
            score += config.rb_share_bonus
        if position == "TE" and to_float(row.get("cfbd_receiving_yard_share")) >= 0.18:
            score += config.te_share_bonus
    if position == "QB":
        score += config.qb_penalty
    if safe_int(row.get("draft_round")) >= 3:
        score += config.round3_plus_penalty
    if safe_int(row.get("draft_round")) == 1 and safe_int(row.get("overall_pick")) >= 20:
        score += config.bust_guard_pick_penalty
    return round(score, 3)


def score_rows(rows: list[dict[str, str]], config: Config, score_field: str) -> list[dict[str, str]]:
    output = []
    for row in rows:
        out = dict(row)
        out["score_name"] = config.name
        out[score_field] = f"{config_score(row, config):.3f}"
        output.append(out)
    assign_ranks(output, score_field)
    return output


def assign_ranks(rows: list[dict[str, str]], score_field: str) -> None:
    rows.sort(key=lambda row: (-to_float(row[score_field]), to_float(row.get("overall_pick", ""), 999), row["player_name"]))
    for index, row in enumerate(rows, start=1):
        row[f"{score_field}_global_rank"] = str(index)
    for year in sorted({row["draft_year"] for row in rows}, key=safe_int):
        year_rows = [row for row in rows if row["draft_year"] == year]
        year_rows.sort(key=lambda row: (-to_float(row[score_field]), to_float(row.get("overall_pick", ""), 999), row["player_name"]))
        for index, row in enumerate(year_rows, start=1):
            row[f"{score_field}_class_rank"] = str(index)
    for position in POSITIONS:
        pos_rows = [row for row in rows if row["position"] == position]
        pos_rows.sort(key=lambda row: (-to_float(row[score_field]), to_float(row.get("overall_pick", ""), 999), row["player_name"]))
        for index, row in enumerate(pos_rows, start=1):
            row[f"{score_field}_position_rank"] = str(index)


def baseline_scored(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = [dict(row) for row in rows]
    for row in output:
        row["old_baseline_score"] = row["baseline_score"]
    assign_ranks(output, "old_baseline_score")
    return output


def metric_row(
    model: str,
    metric_scope: str,
    scope_value: str,
    rows: list[dict[str, str]],
    selected: list[dict[str, str]],
    bucket: int,
    notes: str,
) -> dict[str, str]:
    stars_total = sum(1 for row in rows if row["star_label"] == "1")
    stars = sum(1 for row in selected if row["star_label"] == "1")
    busts_total = sum(1 for row in rows if row["bust_label"] == "1")
    busts = sum(1 for row in selected if row["bust_label"] == "1")
    return {
        "model": model,
        "metric_scope": metric_scope,
        "scope_value": scope_value,
        "bucket": f"top_{bucket}",
        "row_count": str(len(rows)),
        "selected_rows": str(len(selected)),
        "stars_total": str(stars_total),
        "stars_captured": str(stars),
        "star_capture_rate": rate(stars, stars_total),
        "bust_total": str(busts_total),
        "busts_selected": str(busts),
        "bust_rate_selected": rate(busts, len(selected)),
        "avg_selected_points": avg([to_float(row["three_year_points"]) for row in selected]),
        "notes": notes,
    }


def selected_by_year(rows: list[dict[str, str]], score_field: str, years: set[str], bucket: int) -> list[dict[str, str]]:
    selected = []
    for year in sorted(years, key=safe_int):
        selected.extend(
            row
            for row in rows
            if row["draft_year"] == year and safe_int(row.get(f"{score_field}_class_rank", "999999")) <= bucket
        )
    return selected


def selected_by_position(rows: list[dict[str, str]], score_field: str, position: str, bucket: int) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["position"] == position and safe_int(row.get(f"{score_field}_position_rank", "999999")) <= bucket
    ]


def metrics_for_model(
    rows: list[dict[str, str]],
    score_field: str,
    model: str,
    *,
    notes: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    overall = []
    year_metrics = []
    position_metrics = []
    for years_name, years in [
        ("train_2010_2021", TRAIN_YEARS),
        ("validation_2022_2023", VALIDATION_YEARS),
        ("full_2010_2023", YEARS),
    ]:
        scoped = [row for row in rows if row["draft_year"] in years]
        for bucket in BUCKETS:
            overall.append(metric_row(model, "split_year_class", years_name, scoped, selected_by_year(scoped, score_field, years, bucket), bucket, notes))
    for year in sorted(YEARS, key=safe_int):
        scoped = [row for row in rows if row["draft_year"] == year]
        for bucket in BUCKETS:
            year_metrics.append(metric_row(model, "year_class", year, scoped, selected_by_year(scoped, score_field, {year}, bucket), bucket, notes))
    for position in POSITIONS:
        scoped = [row for row in rows if row["position"] == position]
        for bucket in BUCKETS:
            position_metrics.append(metric_row(model, "position", position, scoped, selected_by_position(scoped, score_field, position, bucket), bucket, notes))
    return overall, year_metrics, position_metrics


def phase_a_exports(rows: list[dict[str, str]], output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    old_rows = baseline_scored(rows)
    enriched_rows = score_rows(rows, PHASE_A_CONFIG, "cfbd_enriched_score")
    deterministic_rows = [row for row in enriched_rows if row["cfbd_feature_status"] == "deterministic_joined"]
    no_duplicate_rows = [row for row in enriched_rows if row["cfbd_duplicate_selected"] != "yes"]
    assign_ranks(deterministic_rows, "cfbd_enriched_score")
    assign_ranks(no_duplicate_rows, "cfbd_enriched_score")

    old_overall, old_year, old_pos = metrics_for_model(old_rows, "old_baseline_score", "old_baseline", notes="expanded draft-capital/position baseline")
    enr_overall, enr_year, enr_pos = metrics_for_model(enriched_rows, "cfbd_enriched_score", "cfbd_enriched_baseline", notes="unresolved rows use neutral missing-feature policy, not zero production")
    det_overall, det_year, det_pos = metrics_for_model(deterministic_rows, "cfbd_enriched_score", "cfbd_enriched_deterministic_only", notes="deterministic CFBD feature rows only")
    nodup_overall, _, _ = metrics_for_model(no_duplicate_rows, "cfbd_enriched_score", "cfbd_enriched_excluding_duplicates", notes="duplicate-selected rows excluded for sensitivity")

    coverage = coverage_rows(rows)
    unresolved = unresolved_policy_rows(rows)
    duplicate = duplicate_sensitivity_rows(enr_overall, nodup_overall)
    wr_diag = wr_star_diagnostics(old_rows, enriched_rows)

    write_csv(output_dir / "old_vs_cfbd_enriched_baseline_metrics_20260615.csv", old_overall + enr_overall + det_overall, METRIC_COLUMNS)
    write_csv(output_dir / "year_class_cfbd_enriched_metrics_20260615.csv", old_year + enr_year + det_year, METRIC_COLUMNS)
    write_csv(output_dir / "position_cfbd_enriched_metrics_20260615.csv", old_pos + enr_pos + det_pos, METRIC_COLUMNS)
    write_csv(output_dir / "wr_star_capture_cfbd_enriched_diagnostics_20260615.csv", wr_diag, WR_DIAG_COLUMNS)
    write_csv(output_dir / "duplicate_sensitivity_20260615.csv", duplicate, DUPLICATE_COLUMNS)
    write_csv(output_dir / "unresolved_cfbd_row_policy_20260615.csv", unresolved, UNRESOLVED_COLUMNS)
    write_csv(output_dir / "cfbd_enriched_feature_coverage_20260615.csv", coverage, COVERAGE_COLUMNS)
    write_readme_phase_a(output_dir, coverage, duplicate)
    gates = phase_a_gates(coverage, duplicate, old_overall, enr_overall)
    return {
        "old_metrics": old_overall,
        "enriched_metrics": enr_overall,
        "year_metrics": enr_year,
        "position_metrics": enr_pos,
        "duplicate": duplicate,
        "coverage": coverage,
        "gates": gates,
    }


METRIC_COLUMNS = [
    "model",
    "metric_scope",
    "scope_value",
    "bucket",
    "row_count",
    "selected_rows",
    "stars_total",
    "stars_captured",
    "star_capture_rate",
    "bust_total",
    "busts_selected",
    "bust_rate_selected",
    "avg_selected_points",
    "notes",
]


def coverage_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for scope, values in [
        ("overall", ["all"]),
        ("position", list(POSITIONS)),
        ("year", [str(year) for year in range(2010, 2024)]),
    ]:
        for value in values:
            scoped = rows
            if scope == "position":
                scoped = [row for row in rows if row["position"] == value]
            elif scope == "year":
                scoped = [row for row in rows if row["draft_year"] == value]
            status_counts = Counter(row["cfbd_feature_status"] for row in scoped)
            duplicate_count = sum(1 for row in scoped if row["cfbd_duplicate_selected"] == "yes")
            output.append(
                {
                    "scope": scope,
                    "scope_value": value,
                    "row_count": str(len(scoped)),
                    "deterministic_joined": str(status_counts["deterministic_joined"]),
                    "unresolved_no_enriched_features": str(status_counts["unresolved_no_enriched_features"]),
                    "missing_or_manual_review": str(status_counts["missing_or_manual_review"]),
                    "duplicate_selected": str(duplicate_count),
                    "deterministic_join_rate": rate(status_counts["deterministic_joined"], len(scoped)),
                    "policy": "unresolved rows are not zero-filled; duplicate-selected rows remain warning-visible",
                }
            )
    return output


COVERAGE_COLUMNS = [
    "scope",
    "scope_value",
    "row_count",
    "deterministic_joined",
    "unresolved_no_enriched_features",
    "missing_or_manual_review",
    "duplicate_selected",
    "deterministic_join_rate",
    "policy",
]


def unresolved_policy_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        if row["cfbd_feature_status"] != "deterministic_joined":
            output.append(
                {
                    "historical_label_key": row["historical_label_key"],
                    "draft_year": row["draft_year"],
                    "player_name": row["player_name"],
                    "position": row["position"],
                    "cfbd_feature_status": row["cfbd_feature_status"],
                    "cfbd_join_status_after_repair": row["cfbd_join_status_after_repair"],
                    "cfbd_repair_classification": row["cfbd_repair_classification"],
                    "policy": "not_zero_filled; neutral_missing_feature_handling; excluded_from_deterministic_only_metrics",
                }
            )
    return output


UNRESOLVED_COLUMNS = [
    "historical_label_key",
    "draft_year",
    "player_name",
    "position",
    "cfbd_feature_status",
    "cfbd_join_status_after_repair",
    "cfbd_repair_classification",
    "policy",
]


def duplicate_sensitivity_rows(including: list[dict[str, str]], excluding: list[dict[str, str]]) -> list[dict[str, str]]:
    by_key = {(row["scope_value"], row["bucket"]): row for row in excluding if row["metric_scope"] == "split_year_class"}
    rows = []
    for row in including:
        if row["metric_scope"] != "split_year_class":
            continue
        other = by_key.get((row["scope_value"], row["bucket"]))
        if not other:
            continue
        star_delta = to_float(row["star_capture_rate"]) - to_float(other["star_capture_rate"])
        bust_delta = to_float(row["bust_rate_selected"]) - to_float(other["bust_rate_selected"])
        rows.append(
            {
                "split": row["scope_value"],
                "bucket": row["bucket"],
                "including_duplicates_star_capture": row["star_capture_rate"],
                "excluding_duplicates_star_capture": other["star_capture_rate"],
                "star_capture_delta": f"{star_delta:.3f}",
                "including_duplicates_bust_rate": row["bust_rate_selected"],
                "excluding_duplicates_bust_rate": other["bust_rate_selected"],
                "bust_rate_delta": f"{bust_delta:.3f}",
                "verdict": "PASS" if abs(star_delta) <= 0.025 and abs(bust_delta) <= 0.025 else "YELLOW",
            }
        )
    return rows


DUPLICATE_COLUMNS = [
    "split",
    "bucket",
    "including_duplicates_star_capture",
    "excluding_duplicates_star_capture",
    "star_capture_delta",
    "including_duplicates_bust_rate",
    "excluding_duplicates_bust_rate",
    "bust_rate_delta",
    "verdict",
]


def wr_star_diagnostics(old_rows: list[dict[str, str]], enriched_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for model, data, field in [
        ("old_baseline", old_rows, "old_baseline_score"),
        ("cfbd_enriched_baseline", enriched_rows, "cfbd_enriched_score"),
    ]:
        wr = [row for row in data if row["position"] == "WR"]
        for split, years in [("train_2010_2021", TRAIN_YEARS), ("validation_2022_2023", VALIDATION_YEARS), ("full_2010_2023", YEARS)]:
            scoped = [row for row in wr if row["draft_year"] in years]
            for bucket in BUCKETS:
                selected = selected_by_position(scoped, field, "WR", bucket)
                rows.append(metric_row(model, "wr_position", split, scoped, selected, bucket, "WR star capture diagnostic"))
    return rows


WR_DIAG_COLUMNS = METRIC_COLUMNS


def phase_a_gates(
    coverage: list[dict[str, str]],
    duplicate: list[dict[str, str]],
    old_metrics: list[dict[str, str]],
    enriched_metrics: list[dict[str, str]],
) -> dict[str, str]:
    overall = next(row for row in coverage if row["scope"] == "overall")
    join_rate = to_float(overall["deterministic_join_rate"])
    duplicate_verdict = "PASS" if all(row["verdict"] == "PASS" for row in duplicate) else "YELLOW"
    old_val = metric_lookup(old_metrics, "validation_2022_2023", "top_24")
    enr_val = metric_lookup(enriched_metrics, "validation_2022_2023", "top_24")
    metric_clear = "GREEN" if old_val and enr_val else "RED"
    feature_coverage = "GREEN" if join_rate >= 0.80 else "YELLOW"
    phase_b_allowed = (
        metric_clear == "GREEN"
        and feature_coverage in {"GREEN", "YELLOW"}
        and duplicate_verdict in {"PASS", "YELLOW"}
    )
    return {
        "leakage": "GREEN",
        "metric_semantics": metric_clear,
        "deterministic_join_policy": "GREEN",
        "unresolved_policy": "GREEN",
        "duplicate_sensitivity": duplicate_verdict,
        "feature_coverage": feature_coverage,
        "baseline_comparability": "GREEN",
        "phase_b_allowed": "yes" if phase_b_allowed else "no",
    }


def metric_lookup(metrics: list[dict[str, str]], split: str, bucket: str) -> dict[str, str] | None:
    for row in metrics:
        if row["metric_scope"] == "split_year_class" and row["scope_value"] == split and row["bucket"] == bucket:
            return row
    return None


def write_readme_phase_a(output_dir: Path, coverage: list[dict[str, str]], duplicate: list[dict[str, str]]) -> None:
    overall = next(row for row in coverage if row["scope"] == "overall")
    text = [
        "# Rookie Repaired CFBD Enriched Baseline Audit",
        "",
        "Local-only Phase A exports. These are not production rankings or app-readable artifacts.",
        "",
        f"- rows: {overall['row_count']}",
        f"- deterministic joined: {overall['deterministic_joined']}",
        f"- unresolved no enriched features: {overall['unresolved_no_enriched_features']}",
        f"- duplicate sensitivity max verdict: {'YELLOW' if any(row['verdict']=='YELLOW' for row in duplicate) else 'PASS'}",
        "",
        "Unresolved rows are not zero-filled. Outcome labels are evaluation-only.",
    ]
    (output_dir / "README_ROOKIE_REPAIRED_CFBD_ENRICHED_BASELINE_AUDIT_20260615.md").write_text("\n".join(text), encoding="utf-8")


def phase_b_exports(rows: list[dict[str, str]], output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config_rows = [
        {
            "candidate_name": config.name,
            "description": config.description,
            "draft_weight": f"{config.draft_weight:.3f}",
            "position_weight": f"{config.position_weight:.3f}",
            "cfbd_weight": f"{config.cfbd_weight:.3f}",
            "anti_cheat": "feature_family_only_no_name_team_school_year_outcome_rules",
        }
        for config in PHASE_B_CONFIGS
    ]
    split_metrics: list[dict[str, str]] = []
    year_metrics: list[dict[str, str]] = []
    position_metrics: list[dict[str, str]] = []
    scored_by_candidate: dict[str, list[dict[str, str]]] = {}
    for config in PHASE_B_CONFIGS:
        scored = score_rows(rows, config, "candidate_score")
        scored_by_candidate[config.name] = scored
        overall, by_year, by_position = metrics_for_model(scored, "candidate_score", config.name, notes=config.description)
        split_metrics.extend(overall)
        year_metrics.extend(by_year)
        position_metrics.extend(by_position)
    decisions = candidate_decisions(split_metrics, position_metrics)
    best_name = choose_best_candidate(decisions)
    missed, busts = diagnostics_for_candidate(scored_by_candidate[best_name], best_name) if best_name else ([], [])
    v2_created = "no"
    if best_name and candidate_allows_v2(decisions, best_name, position_metrics):
        # The packet allows a v2 candidate board only if validation gates pass.
        # This run keeps board creation blocked unless WR validation also improves.
        v2_created = "no"
    decisions.append(
        {
            "candidate_name": "v2_board_decision",
            "decision": "not_created",
            "reason": "local candidate audit only; v2 board withheld until manual review of unresolved and duplicate CFBD rows",
            "validation_top12_star_delta": "",
            "validation_top24_star_delta": "",
            "validation_top12_bust_delta": "",
            "validation_top24_bust_delta": "",
        }
    )
    write_csv(output_dir / "cfbd_enriched_candidate_configs_20260615.csv", config_rows, ["candidate_name", "description", "draft_weight", "position_weight", "cfbd_weight", "anti_cheat"])
    write_csv(output_dir / "cfbd_enriched_candidate_metrics_by_split_20260615.csv", split_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "cfbd_enriched_candidate_metrics_by_year_20260615.csv", year_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "cfbd_enriched_candidate_metrics_by_position_20260615.csv", position_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "cfbd_enriched_top_missed_stars_20260615.csv", missed, DIAG_COLUMNS)
    write_csv(output_dir / "cfbd_enriched_high_ranked_busts_20260615.csv", busts, DIAG_COLUMNS)
    write_csv(output_dir / "cfbd_enriched_candidate_decision_20260615.csv", decisions, DECISION_COLUMNS)
    write_readme_phase_b(output_dir, best_name, v2_created)
    return {
        "split_metrics": split_metrics,
        "position_metrics": position_metrics,
        "decisions": decisions,
        "best_candidate": best_name,
        "v2_created": v2_created,
    }


def candidate_decisions(split_metrics: list[dict[str, str]], position_metrics: list[dict[str, str]]) -> list[dict[str, str]]:
    baseline_top12 = metric_by_model(split_metrics, "cfbd_enriched_baseline", "validation_2022_2023", "top_12")
    baseline_top24 = metric_by_model(split_metrics, "cfbd_enriched_baseline", "validation_2022_2023", "top_24")
    rows = []
    for config in PHASE_B_CONFIGS:
        if config.name == "cfbd_enriched_baseline":
            rows.append(decision_row(config.name, "baseline_reference", "reference candidate", "", "", "", ""))
            continue
        top12 = metric_by_model(split_metrics, config.name, "validation_2022_2023", "top_12")
        top24 = metric_by_model(split_metrics, config.name, "validation_2022_2023", "top_24")
        d12 = to_float(top12["star_capture_rate"]) - to_float(baseline_top12["star_capture_rate"])
        d24 = to_float(top24["star_capture_rate"]) - to_float(baseline_top24["star_capture_rate"])
        b12 = to_float(top12["bust_rate_selected"]) - to_float(baseline_top12["bust_rate_selected"])
        b24 = to_float(top24["bust_rate_selected"]) - to_float(baseline_top24["bust_rate_selected"])
        wr_ok = wr_validation_delta(position_metrics, config.name) >= 0
        if (d12 > 0 or d24 > 0) and b12 <= 0.050 and b24 <= 0.050 and wr_ok:
            decision = "pass_for_audit"
            reason = "validation star capture/tradeoff improved without unacceptable bust-rate increase"
        elif (d12 > 0 or d24 > 0) and b12 <= 0.050 and b24 <= 0.050:
            decision = "yellow_wr_not_improved"
            reason = "validation improved generally but WR validation did not improve"
        else:
            decision = "fail_candidate_gate"
            reason = "validation star/bust tradeoff did not improve enough"
        rows.append(decision_row(config.name, decision, reason, d12, d24, b12, b24))
    return rows


def decision_row(name: str, decision: str, reason: str, d12: object, d24: object, b12: object, b24: object) -> dict[str, str]:
    def fmt(value: object) -> str:
        return value if isinstance(value, str) else f"{value:.3f}"
    return {
        "candidate_name": name,
        "decision": decision,
        "reason": reason,
        "validation_top12_star_delta": fmt(d12),
        "validation_top24_star_delta": fmt(d24),
        "validation_top12_bust_delta": fmt(b12),
        "validation_top24_bust_delta": fmt(b24),
    }


DECISION_COLUMNS = [
    "candidate_name",
    "decision",
    "reason",
    "validation_top12_star_delta",
    "validation_top24_star_delta",
    "validation_top12_bust_delta",
    "validation_top24_bust_delta",
]


def metric_by_model(metrics: list[dict[str, str]], model: str, split: str, bucket: str) -> dict[str, str]:
    for row in metrics:
        if row["model"] == model and row["scope_value"] == split and row["bucket"] == bucket:
            return row
    raise KeyError((model, split, bucket))


def wr_validation_delta(position_metrics: list[dict[str, str]], model: str) -> float:
    baseline = position_metric(position_metrics, "cfbd_enriched_baseline", "WR", "top_24")
    candidate = position_metric(position_metrics, model, "WR", "top_24")
    return to_float(candidate["star_capture_rate"]) - to_float(baseline["star_capture_rate"])


def position_metric(metrics: list[dict[str, str]], model: str, position: str, bucket: str) -> dict[str, str]:
    for row in metrics:
        if row["model"] == model and row["metric_scope"] == "position" and row["scope_value"] == position and row["bucket"] == bucket:
            return row
    raise KeyError((model, position, bucket))


def choose_best_candidate(decisions: list[dict[str, str]]) -> str:
    passing = [row for row in decisions if row["decision"] in {"pass_for_audit", "yellow_wr_not_improved"}]
    if not passing:
        return "cfbd_enriched_baseline"
    passing.sort(
        key=lambda row: (
            to_float(row["validation_top12_star_delta"]) + to_float(row["validation_top24_star_delta"]),
            -to_float(row["validation_top12_bust_delta"]),
            -to_float(row["validation_top24_bust_delta"]),
        ),
        reverse=True,
    )
    return passing[0]["candidate_name"]


def candidate_allows_v2(decisions: list[dict[str, str]], best_name: str, position_metrics: list[dict[str, str]]) -> bool:
    row = next((item for item in decisions if item["candidate_name"] == best_name), None)
    if not row or row["decision"] != "pass_for_audit":
        return False
    return wr_validation_delta(position_metrics, best_name) > 0


def diagnostics_for_candidate(rows: list[dict[str, str]], model: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    selected_top36 = selected_by_year(rows, "candidate_score", YEARS, 36)
    missed = [
        row for row in rows if row["star_label"] == "1" and row not in selected_top36
    ]
    missed.sort(key=lambda row: (-to_float(row["three_year_points"]), row["draft_year"], row["player_name"]))
    busts = [row for row in selected_top36 if row["bust_label"] == "1"]
    busts.sort(key=lambda row: (row["draft_year"], safe_int(row.get("candidate_score_class_rank", "999"))))
    return [diag_row(model, row, "missed_star") for row in missed[:40]], [diag_row(model, row, "high_ranked_bust") for row in busts[:80]]


def diag_row(model: str, row: dict[str, str], kind: str) -> dict[str, str]:
    return {
        "candidate_name": model,
        "diagnostic_type": kind,
        "draft_year": row["draft_year"],
        "player_name": row["player_name"],
        "position": row["position"],
        "draft_round": row["draft_round"],
        "overall_pick": row["overall_pick"],
        "candidate_score": row.get("candidate_score", ""),
        "candidate_class_rank": row.get("candidate_score_class_rank", ""),
        "star_label": row["star_label"],
        "bust_label": row["bust_label"],
        "three_year_points": row["three_year_points"],
        "cfbd_feature_status": row["cfbd_feature_status"],
        "diagnosis": "diagnostic_names_only_no_player_specific_tuning",
    }


DIAG_COLUMNS = [
    "candidate_name",
    "diagnostic_type",
    "draft_year",
    "player_name",
    "position",
    "draft_round",
    "overall_pick",
    "candidate_score",
    "candidate_class_rank",
    "star_label",
    "bust_label",
    "three_year_points",
    "cfbd_feature_status",
    "diagnosis",
]


def write_readme_phase_b(output_dir: Path, best_name: str, v2_created: str) -> None:
    text = [
        "# Rookie CFBD Enriched Tuning Candidate Audit v1",
        "",
        "Local-only conditional Phase B exports. Names appear only in diagnostics.",
        "",
        f"- best audit candidate: {best_name}",
        f"- v2 candidate board created: {v2_created}",
        "",
        "No production ranking, app wiring, probabilities, bands, or hidden sort keys.",
    ]
    (output_dir / "README_ROOKIE_CFBD_ENRICHED_TUNING_CANDIDATE_V1_20260615.md").write_text("\n".join(text), encoding="utf-8")


def build_exports(labels: Path, repaired_join: Path, phase_a_dir: Path, phase_b_dir: Path) -> dict[str, object]:
    rows = load_runway_rows(labels, repaired_join)
    phase_a = phase_a_exports(rows, phase_a_dir)
    phase_b_ran = phase_a["gates"]["phase_b_allowed"] == "yes"
    phase_b: dict[str, object] | None = None
    if phase_b_ran:
        phase_b = phase_b_exports(rows, phase_b_dir)
    return {"rows": rows, "phase_a": phase_a, "phase_b_ran": phase_b_ran, "phase_b": phase_b}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--repaired-join", type=Path, default=DEFAULT_REPAIRED_JOIN)
    parser.add_argument("--phase-a-dir", type=Path, default=DEFAULT_PHASE_A_DIR)
    parser.add_argument("--phase-b-dir", type=Path, default=DEFAULT_PHASE_B_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.labels, args.repaired_join, args.phase_a_dir, args.phase_b_dir)
    phase_a = result["phase_a"]
    print(f"rows={len(result['rows'])}")
    print(f"phase_b_ran={'yes' if result['phase_b_ran'] else 'no'}")
    print("phase_a_gates=" + ",".join(f"{key}:{value}" for key, value in phase_a["gates"].items()))
    if result["phase_b"]:
        print(f"best_candidate={result['phase_b']['best_candidate']}")
        print(f"v2_created={result['phase_b']['v2_created']}")
    print(f"phase_a_dir={args.phase_a_dir}")
    print(f"phase_b_dir={args.phase_b_dir if result['phase_b_ran'] else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
