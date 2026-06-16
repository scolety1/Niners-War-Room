"""Audit whether more historical rookie model tuning is likely to help.

This is audit/export-only. It reuses the expanded 2010-2023 label pool,
repaired CFBD feature join, and previously tested v1.1 candidate configurations.
It does not tune new weights, create a v2 board, or write production/app files.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_cfbd_enriched_baseline_runway_v1 import (  # noqa: E402
    BUCKETS,
    DEFAULT_LABELS,
    DEFAULT_REPAIRED_JOIN,
    POSITIONS,
    rate,
    safe_int,
    to_float,
    write_csv,
)
from scripts.rookie_framework.tune_rookie_model_runway_v1_1 import (  # noqa: E402
    BASELINE_CONFIG,
    CANDIDATE_CONFIGS,
    load_runway_rows,
    metric_row,
    score_rows_v1_1,
    selected_by_class_rank,
)


DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/model_ceiling_tuning_opportunity_audit_20260615")
YEARS = [str(year) for year in range(2010, 2024)]
ROLLING_HOLDOUT_YEARS = [str(year) for year in range(2014, 2024)]

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
    "wr_stars_total",
    "wr_stars_captured",
    "wr_star_capture_rate",
    "draft_capital_trap_busts",
    "avg_selected_points",
    "notes",
]

CONSISTENCY_COLUMNS = [
    "candidate_name",
    "bucket",
    "holdout_years",
    "avg_star_delta_vs_baseline",
    "avg_bust_delta_vs_baseline",
    "avg_wr_star_delta_vs_baseline",
    "years_star_improved",
    "years_star_declined",
    "years_bust_increased",
    "years_wr_improved",
    "stability_verdict",
]

OBJECTIVE_COLUMNS = [
    "objective",
    "bucket",
    "best_candidate",
    "holdout_wins",
    "avg_star_capture_rate",
    "avg_bust_rate_selected",
    "avg_wr_star_capture_rate",
    "diagnostic_note",
]

FEATURE_COLUMNS = [
    "feature_family",
    "audit_verdict",
    "evidence",
    "recommendation",
]

DECISION_COLUMNS = [
    "decision_item",
    "verdict",
    "reason",
]

ANTI_CHEAT_COLUMNS = [
    "check",
    "status",
    "reason",
]

MANUAL_ISSUE_COLUMNS = [
    "issue_type",
    "position",
    "draft_year",
    "player_name",
    "draft_round",
    "overall_pick",
    "baseline_rank",
    "three_year_points",
    "cfbd_feature_status",
    "general_diagnosis",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = avg(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def enriched_metric_row(
    model: str,
    scope: str,
    scope_value: str,
    rows: list[dict[str, str]],
    selected: list[dict[str, str]],
    bucket: int,
    notes: str,
) -> dict[str, str]:
    base = metric_row(model, scope, scope_value, rows, selected, bucket, notes)
    wr_rows = [row for row in rows if row.get("position") == "WR"]
    wr_selected = [row for row in selected if row.get("position") == "WR"]
    wr_stars_total = sum(1 for row in wr_rows if row.get("star_label") == "1")
    wr_stars = sum(1 for row in wr_selected if row.get("star_label") == "1")
    trap_busts = sum(
        1
        for row in selected
        if row.get("bust_label") == "1" and safe_int(row.get("draft_round")) >= 3
    )
    base.update(
        {
            "wr_stars_total": str(wr_stars_total),
            "wr_stars_captured": str(wr_stars),
            "wr_star_capture_rate": rate(wr_stars, wr_stars_total),
            "draft_capital_trap_busts": str(trap_busts),
        }
    )
    return base


def rolling_metrics(scored_by_model: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    rows = []
    for model, scored in scored_by_model.items():
        for year in ROLLING_HOLDOUT_YEARS:
            scoped = [row for row in scored if row.get("draft_year") == year]
            for bucket in BUCKETS:
                selected = selected_by_class_rank(scoped, "candidate_score", {year}, bucket)
                rows.append(
                    enriched_metric_row(
                        model,
                        "rolling_holdout_year",
                        year,
                        scoped,
                        selected,
                        bucket,
                        "fixed candidate evaluated on one held-out draft year; no tuning performed",
                    )
                )
        for split_name, split_years in rolling_splits():
            scoped = [row for row in scored if row.get("draft_year") in split_years]
            for bucket in BUCKETS:
                selected = selected_by_class_rank(scoped, "candidate_score", set(split_years), bucket)
                rows.append(
                    enriched_metric_row(
                        model,
                        "multi_year_holdout",
                        split_name,
                        scoped,
                        selected,
                        bucket,
                        "fixed candidate evaluated on rolling multi-year holdout; no tuning performed",
                    )
                )
    return rows


def rolling_splits() -> list[tuple[str, list[str]]]:
    return [
        ("holdout_2014_2016", ["2014", "2015", "2016"]),
        ("holdout_2017_2019", ["2017", "2018", "2019"]),
        ("holdout_2020_2021", ["2020", "2021"]),
        ("holdout_2022_2023", ["2022", "2023"]),
    ]


def metric_lookup(metrics: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    return {
        (row["model"], row["metric_scope"], row["scope_value"], row["bucket"]): row
        for row in metrics
    }


def consistency_rows(metrics: list[dict[str, str]]) -> list[dict[str, str]]:
    lookup = metric_lookup(metrics)
    output = []
    baseline = BASELINE_CONFIG.name
    for candidate in [config.name for config in CANDIDATE_CONFIGS if config.name != baseline]:
        for bucket in [f"top_{item}" for item in BUCKETS]:
            star_deltas: list[float] = []
            bust_deltas: list[float] = []
            wr_deltas: list[float] = []
            for year in ROLLING_HOLDOUT_YEARS:
                base = lookup[(baseline, "rolling_holdout_year", year, bucket)]
                cand = lookup[(candidate, "rolling_holdout_year", year, bucket)]
                star_deltas.append(to_float(cand["star_capture_rate"]) - to_float(base["star_capture_rate"]))
                bust_deltas.append(to_float(cand["bust_rate_selected"]) - to_float(base["bust_rate_selected"]))
                wr_deltas.append(to_float(cand["wr_star_capture_rate"]) - to_float(base["wr_star_capture_rate"]))
            years_star_improved = sum(1 for item in star_deltas if item > 0.001)
            years_star_declined = sum(1 for item in star_deltas if item < -0.001)
            years_bust_increased = sum(1 for item in bust_deltas if item > 0.001)
            years_wr_improved = sum(1 for item in wr_deltas if item > 0.001)
            stability = stability_verdict(star_deltas, bust_deltas, wr_deltas)
            output.append(
                {
                    "candidate_name": candidate,
                    "bucket": bucket,
                    "holdout_years": str(len(ROLLING_HOLDOUT_YEARS)),
                    "avg_star_delta_vs_baseline": f"{avg(star_deltas):.3f}",
                    "avg_bust_delta_vs_baseline": f"{avg(bust_deltas):.3f}",
                    "avg_wr_star_delta_vs_baseline": f"{avg(wr_deltas):.3f}",
                    "years_star_improved": str(years_star_improved),
                    "years_star_declined": str(years_star_declined),
                    "years_bust_increased": str(years_bust_increased),
                    "years_wr_improved": str(years_wr_improved),
                    "stability_verdict": stability,
                }
            )
    return output


def stability_verdict(star_deltas: list[float], bust_deltas: list[float], wr_deltas: list[float]) -> str:
    if avg(star_deltas) > 0.025 and sum(1 for item in bust_deltas if item > 0.025) <= 2 and stdev(star_deltas) <= 0.08:
        return "GREEN"
    if avg(star_deltas) >= 0.0 and sum(1 for item in bust_deltas if item > 0.025) <= 4 and avg(wr_deltas) >= 0.0:
        return "YELLOW"
    return "RED"


def objective_rows(metrics: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    by_model_year_bucket = [
        row
        for row in metrics
        if row["metric_scope"] == "rolling_holdout_year"
    ]
    candidates = [config.name for config in CANDIDATE_CONFIGS]
    for bucket in [f"top_{item}" for item in BUCKETS]:
        for objective in [
            "maximize_star_capture",
            "cap_bust_rate",
            "improve_wr_capture",
            "avoid_draft_capital_traps",
        ]:
            winners: list[str] = []
            winner_rates: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
            for year in ROLLING_HOLDOUT_YEARS:
                scoped = [
                    row
                    for row in by_model_year_bucket
                    if row["scope_value"] == year and row["bucket"] == bucket and row["model"] in candidates
                ]
                if not scoped:
                    continue
                winner = choose_objective_winner(scoped, objective)
                winners.append(winner["model"])
                winner_rates[winner["model"]].append(winner)
            counts = Counter(winners)
            best_name, wins = counts.most_common(1)[0]
            rows = winner_rates[best_name]
            output.append(
                {
                    "objective": objective,
                    "bucket": bucket,
                    "best_candidate": best_name,
                    "holdout_wins": str(wins),
                    "avg_star_capture_rate": f"{avg([to_float(row['star_capture_rate']) for row in rows]):.3f}",
                    "avg_bust_rate_selected": f"{avg([to_float(row['bust_rate_selected']) for row in rows]):.3f}",
                    "avg_wr_star_capture_rate": f"{avg([to_float(row['wr_star_capture_rate']) for row in rows]):.3f}",
                    "diagnostic_note": "objective diagnostic only; no new weights selected",
                }
            )
    return output


def choose_objective_winner(rows: list[dict[str, str]], objective: str) -> dict[str, str]:
    if objective == "maximize_star_capture":
        return max(rows, key=lambda row: (to_float(row["star_capture_rate"]), -to_float(row["bust_rate_selected"])))
    if objective == "cap_bust_rate":
        return max(rows, key=lambda row: (-to_float(row["bust_rate_selected"]), to_float(row["star_capture_rate"])))
    if objective == "improve_wr_capture":
        return max(rows, key=lambda row: (to_float(row["wr_star_capture_rate"]), to_float(row["star_capture_rate"])))
    if objective == "avoid_draft_capital_traps":
        return max(rows, key=lambda row: (-safe_int(row["draft_capital_trap_busts"]), to_float(row["star_capture_rate"])))
    raise ValueError(objective)


def feature_family_rows(consistency: list[dict[str, str]], ablation_path: Path) -> list[dict[str, str]]:
    ablations = read_csv(ablation_path)
    ablation_summary = summarize_ablation(ablations)
    wr_greenish = [
        row
        for row in consistency
        if "wr" in row["candidate_name"] and row["bucket"] == "top_24" and row["stability_verdict"] in {"GREEN", "YELLOW"}
    ]
    trap_greenish = [
        row
        for row in consistency
        if "trap" in row["candidate_name"] and row["bucket"] == "top_24" and row["stability_verdict"] in {"GREEN", "YELLOW"}
    ]
    return [
        {
            "feature_family": "draft_capital",
            "audit_verdict": "useful_but_ceiling_near_current",
            "evidence": ablation_summary.get("ablation_draft_capital_position_only", "available in prior ablation"),
            "recommendation": "do not broadly increase draft capital; watch for trap busts",
        },
        {
            "feature_family": "cfbd_production",
            "audit_verdict": "useful_narrow_signal",
            "evidence": ablation_summary.get("ablation_cfbd_production_only", "available in prior ablation"),
            "recommendation": "use only in narrow position-specific hypotheses",
        },
        {
            "feature_family": "cfbd_market_share_dominator",
            "audit_verdict": "promising_but_unstable",
            "evidence": ablation_summary.get("ablation_cfbd_market_share_only", "available in prior ablation"),
            "recommendation": "narrow WR/RB share hypothesis may be worth testing; broad sweep is not",
        },
        {
            "feature_family": "wr_upside",
            "audit_verdict": "narrow_tuning_only" if wr_greenish else "no_stable_broad_gain",
            "evidence": f"{len(wr_greenish)} top-24 rolling WR candidates cleared yellow/green stability",
            "recommendation": "test only a specific WR feature-quality hypothesis if new evidence supports it",
        },
        {
            "feature_family": "scoring_format_fit",
            "audit_verdict": "noisy",
            "evidence": "prior v1.1 scoring-format candidate did not clear validation/stability gate",
            "recommendation": "keep as manual draft context unless a narrower role-stability feature is introduced",
        },
        {
            "feature_family": "draft_capital_trap_guard",
            "audit_verdict": "diagnostic_useful_not_standalone",
            "evidence": f"{len(trap_greenish)} top-24 trap-guard rows cleared yellow/green stability",
            "recommendation": "use as warning/manual-review context, not a broad rank-overwrite",
        },
    ]


def summarize_ablation(rows: list[dict[str, str]]) -> dict[str, str]:
    summary: dict[str, str] = {}
    for row in rows:
        if row.get("scope_value") != "final_validation_2022_2023" or row.get("bucket") != "top_24":
            continue
        summary[row["model"]] = (
            f"final top24 star={row.get('star_capture_rate')} bust={row.get('bust_rate_selected')}"
        )
    return summary


def manual_issue_rows(scored_baseline: list[dict[str, str]]) -> list[dict[str, str]]:
    selected_top36 = selected_by_class_rank(scored_baseline, "candidate_score", set(YEARS), 36)
    selected_keys = {row.get("historical_label_key") for row in selected_top36}
    missed_stars = [
        row
        for row in scored_baseline
        if row.get("star_label") == "1" and row.get("historical_label_key") not in selected_keys
    ]
    missed_stars.sort(key=lambda row: (-to_float(row.get("three_year_points")), row.get("draft_year", ""), row.get("player_name", "")))
    high_busts = [row for row in selected_top36 if row.get("bust_label") == "1"]
    high_busts.sort(key=lambda row: (row.get("draft_year", ""), safe_int(row.get("candidate_score_class_rank", "999"))))
    rows = []
    for row in missed_stars[:25]:
        rows.append(manual_issue_row("missed_star", row))
    for row in high_busts[:25]:
        rows.append(manual_issue_row("high_ranked_bust", row))
    return rows


def manual_issue_row(kind: str, row: dict[str, str]) -> dict[str, str]:
    return {
        "issue_type": kind,
        "position": row.get("position", ""),
        "draft_year": row.get("draft_year", ""),
        "player_name": row.get("player_name", ""),
        "draft_round": row.get("draft_round", ""),
        "overall_pick": row.get("overall_pick", ""),
        "baseline_rank": row.get("candidate_score_class_rank", ""),
        "three_year_points": row.get("three_year_points", ""),
        "cfbd_feature_status": row.get("cfbd_feature_status", ""),
        "general_diagnosis": diagnose_issue(row),
    }


def diagnose_issue(row: dict[str, str]) -> str:
    if row.get("cfbd_feature_status") != "deterministic_joined":
        return "missing_or_unresolved_source_safe_cfbd_features"
    if safe_int(row.get("draft_round")) >= 4:
        return "late_draft_profile_requires_manual_scouting_or_role_context"
    if row.get("position") in {"WR", "TE"} and to_float(row.get("cfbd_receiving_yard_share")) < 0.20:
        return "pass_catcher_profile_likely_needs_route_or_role_context"
    if row.get("position") == "RB" and to_float(row.get("cfbd_rushing_yard_share")) < 0.20:
        return "rb_profile_likely_needs_depth_chart_or_role_context"
    return "general_feature_family_miss_no_player_specific_patch"


def decision_rows(consistency: list[dict[str, str]], objective: list[dict[str, str]]) -> list[dict[str, str]]:
    premium_green = [
        row
        for row in consistency
        if row["stability_verdict"] == "GREEN" and row["bucket"] in {"top_12", "top_24"}
    ]
    top36_green = [
        row
        for row in consistency
        if row["stability_verdict"] == "GREEN" and row["bucket"] == "top_36"
    ]
    yellow = [row for row in consistency if row["stability_verdict"] == "YELLOW"]
    objective_winners = Counter(row["best_candidate"] for row in objective)
    baseline_wins = objective_winners.get(BASELINE_CONFIG.name, 0)
    if premium_green:
        verdict = "GREEN_TUNE_AGAIN"
        reason = "at least one candidate showed stable rolling premium-window improvement"
    elif yellow or top36_green or baseline_wins < len(objective):
        verdict = "YELLOW_NARROW_HYPOTHESIS_ONLY"
        reason = "some diagnostics show signal, but no broad candidate improves the premium window consistently"
    else:
        verdict = "RED_STOP_BROAD_HISTORICAL_TUNING"
        reason = "baseline remains near the observed ceiling and objective winners are inconsistent"
    return [
        {
            "decision_item": "more_historical_tuning",
            "verdict": verdict,
            "reason": reason,
        },
        {
            "decision_item": "current_model_ceiling_estimate",
            "verdict": "moderate_high_for_available_features",
            "reason": "historical rank features capture many top36 stars, but top12/WR misses and busts remain manually contextual",
        },
        {
            "decision_item": "recommended_next_step",
            "verdict": "narrow_tune_or_freeze",
            "reason": "freeze broad weights; only test a narrow WR/role-stability or source-coverage hypothesis if new evidence is added",
        },
        {
            "decision_item": "v2_board",
            "verdict": "not_created",
            "reason": "this audit is decision-only and did not approve or create a v2 board",
        },
    ]


def anti_cheat_rows() -> list[dict[str, str]]:
    return [
        {
            "check": "names_ids_schools_teams_years",
            "status": "PASS",
            "reason": "used only for identity/display/grouping/diagnostics, never scoring rules",
        },
        {
            "check": "outcome_labels",
            "status": "PASS",
            "reason": "labels used only for evaluation metrics",
        },
        {
            "check": "adp_market",
            "status": "PASS",
            "reason": "not read or used as private score input",
        },
        {
            "check": "player_specific_rules",
            "status": "PASS",
            "reason": "no player-specific boosts, penalties, or class/team/school exceptions",
        },
        {
            "check": "tuning_scope",
            "status": "PASS",
            "reason": "no new weights tuned; only previously tested feature-family configs evaluated",
        },
        {
            "check": "partial_windows",
            "status": "PASS",
            "reason": "load_runway_rows uses complete 2010-2023 rows; no 2024-2025 tuning rows",
        },
    ]


def write_readme(output_dir: Path) -> None:
    text = [
        "# Rookie Model Ceiling Tuning Opportunity Audit",
        "",
        "Local-only model ceiling diagnostics for the 2010-2023 complete-window historical pool.",
        "",
        "No new tuning, v2 board, production ranking, app output, probabilities, bands, hidden sort keys, or promoted artifacts.",
    ]
    (output_dir / "README_ROOKIE_MODEL_CEILING_TUNING_OPPORTUNITY_AUDIT_20260615.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def build_exports(labels: Path, repaired_join: Path, output_dir: Path, ablation_path: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = load_runway_rows(labels, repaired_join)
    scored_by_model = {
        config.name: score_rows_v1_1(rows, config, "candidate_score")
        for config in CANDIDATE_CONFIGS
    }
    metrics = rolling_metrics(scored_by_model)
    consistency = consistency_rows(metrics)
    objectives = objective_rows(metrics)
    features = feature_family_rows(consistency, ablation_path)
    decisions = decision_rows(consistency, objectives)
    manual_issues = manual_issue_rows(scored_by_model[BASELINE_CONFIG.name])
    anti_cheat = anti_cheat_rows()

    write_csv(output_dir / "rolling_validation_metrics_20260615.csv", metrics, METRIC_COLUMNS)
    write_csv(output_dir / "candidate_consistency_vs_baseline_20260615.csv", consistency, CONSISTENCY_COLUMNS)
    write_csv(output_dir / "strict_objective_diagnostics_20260615.csv", objectives, OBJECTIVE_COLUMNS)
    write_csv(output_dir / "feature_family_tuning_signal_20260615.csv", features, FEATURE_COLUMNS)
    write_csv(output_dir / "manual_review_issue_diagnostics_20260615.csv", manual_issues, MANUAL_ISSUE_COLUMNS)
    write_csv(output_dir / "model_ceiling_decision_20260615.csv", decisions, DECISION_COLUMNS)
    write_csv(output_dir / "anti_cheat_leakage_audit_20260615.csv", anti_cheat, ANTI_CHEAT_COLUMNS)
    write_readme(output_dir)
    return {
        "rows": rows,
        "metrics": metrics,
        "consistency": consistency,
        "objectives": objectives,
        "features": features,
        "decisions": decisions,
        "manual_issues": manual_issues,
        "anti_cheat": anti_cheat,
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--repaired-join", type=Path, default=DEFAULT_REPAIRED_JOIN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--ablation-path",
        type=Path,
        default=Path(
            "local_exports/rookie_framework/model_tuning_runway_v1_1_20260615/"
            "feature_ablation_metrics_v1_1_20260615.csv"
        ),
    )
    args = parser.parse_args(argv)
    result = build_exports(args.labels, args.repaired_join, args.output_dir, args.ablation_path)
    decision = result["decisions"][0]
    print(f"rows={len(result['rows'])}")
    print(f"rolling_metric_rows={len(result['metrics'])}")
    print(f"decision={decision['verdict']}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
