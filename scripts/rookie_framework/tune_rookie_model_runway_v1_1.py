"""Run rookie model tuning runway v1.1.

This is a local/export-only historical tuning harness. It tests general
feature-family configurations with a fixed 2010-2019 train, 2020-2021
development validation, and 2022-2023 final validation split. Names and IDs
appear only in diagnostics; labels are used only for evaluation.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_cfbd_enriched_baseline_runway_v1 import (  # noqa: E402
    BUCKETS,
    DEFAULT_LABELS,
    DEFAULT_REPAIRED_JOIN,
    POSITIONS,
    assign_ranks,
    clipped,
    load_runway_rows,
    rate,
    read_csv,
    safe_int,
    to_float,
    write_csv,
)
from scripts.rookie_framework.build_rookie_historical_allowlist_qa_expanded_baseline_v1 import (  # noqa: E402
    draft_points,
)


DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/model_tuning_runway_v1_1_20260615")
DEFAULT_CURRENT_BOARD = Path(
    "local_exports/rookie_framework/draft_ranking_model_v1_20260615/"
    "rookie_draft_ranking_v1_20260615.csv"
)
YEARS = {str(year) for year in range(2010, 2024)}
TRAIN_YEARS = {str(year) for year in range(2010, 2020)}
DEV_YEARS = {"2020", "2021"}
FINAL_YEARS = {"2022", "2023"}
SPLITS = [
    ("train_2010_2019", TRAIN_YEARS),
    ("dev_validation_2020_2021", DEV_YEARS),
    ("final_validation_2022_2023", FINAL_YEARS),
    ("full_2010_2023", YEARS),
]


@dataclass(frozen=True)
class TuningConfig:
    name: str
    description: str
    draft_weight: float
    position_weight: float
    production_weight: float
    market_share_weight: float
    scoring_fit_weight: float
    position_scores: dict[str, float]
    round3_plus_penalty: float = 0.0
    late_round_penalty: float = 0.0
    late_round_dart_bonus: float = 0.0
    qb_1qb_penalty: float = 0.0
    wr_share_bonus: float = 0.0
    rb_share_bonus: float = 0.0
    te_share_bonus: float = 0.0


BASELINE_CONFIG = TuningConfig(
    name="cfbd_enriched_baseline_v1_1",
    description="reference draft/position/CFBD blend from repaired historical pool",
    draft_weight=0.68,
    position_weight=0.20,
    production_weight=0.07,
    market_share_weight=0.05,
    scoring_fit_weight=0.00,
    position_scores={"RB": 72.0, "WR": 70.0, "TE": 42.0, "QB": 24.0},
)

CANDIDATE_CONFIGS = [
    BASELINE_CONFIG,
    TuningConfig(
        name="scoring_format_fit_plus_v2",
        description="non-PPR and first-down role-fit emphasis with 1QB discipline",
        draft_weight=0.58,
        position_weight=0.20,
        production_weight=0.08,
        market_share_weight=0.05,
        scoring_fit_weight=0.09,
        position_scores={"RB": 82.0, "WR": 74.0, "TE": 58.0, "QB": 18.0},
        qb_1qb_penalty=-4.0,
        rb_share_bonus=3.0,
        te_share_bonus=2.0,
    ),
    TuningConfig(
        name="wr_star_capture_plus",
        description="WR upside plus using source-safe receiving production/share families",
        draft_weight=0.56,
        position_weight=0.20,
        production_weight=0.08,
        market_share_weight=0.09,
        scoring_fit_weight=0.07,
        position_scores={"RB": 72.0, "WR": 84.0, "TE": 50.0, "QB": 16.0},
        qb_1qb_penalty=-5.0,
        wr_share_bonus=5.0,
    ),
    TuningConfig(
        name="cfbd_market_share_plus",
        description="college share/dominator context plus without player-specific logic",
        draft_weight=0.56,
        position_weight=0.18,
        production_weight=0.07,
        market_share_weight=0.13,
        scoring_fit_weight=0.06,
        position_scores={"RB": 76.0, "WR": 80.0, "TE": 54.0, "QB": 16.0},
        qb_1qb_penalty=-5.0,
        wr_share_bonus=3.0,
        rb_share_bonus=3.0,
        te_share_bonus=2.0,
    ),
    TuningConfig(
        name="draft_capital_trap_guard",
        description="reduced late/fragile draft-capital dependence with general bust guard",
        draft_weight=0.61,
        position_weight=0.22,
        production_weight=0.07,
        market_share_weight=0.05,
        scoring_fit_weight=0.05,
        position_scores={"RB": 80.0, "WR": 76.0, "TE": 54.0, "QB": 16.0},
        round3_plus_penalty=-4.0,
        late_round_penalty=-3.0,
        qb_1qb_penalty=-4.0,
    ),
    TuningConfig(
        name="balanced_star_bust_frontier",
        description="balanced star capture and bust avoidance across draft, role, and CFBD families",
        draft_weight=0.57,
        position_weight=0.20,
        production_weight=0.08,
        market_share_weight=0.08,
        scoring_fit_weight=0.07,
        position_scores={"RB": 80.0, "WR": 80.0, "TE": 58.0, "QB": 16.0},
        round3_plus_penalty=-2.0,
        qb_1qb_penalty=-5.0,
        wr_share_bonus=2.0,
        rb_share_bonus=2.0,
        te_share_bonus=2.0,
    ),
    TuningConfig(
        name="position_calibrated_v2",
        description="position-calibrated candidate preserving 1QB and non-PPR balance",
        draft_weight=0.58,
        position_weight=0.24,
        production_weight=0.07,
        market_share_weight=0.05,
        scoring_fit_weight=0.06,
        position_scores={"RB": 84.0, "WR": 78.0, "TE": 62.0, "QB": 14.0},
        qb_1qb_penalty=-6.0,
        rb_share_bonus=2.0,
        te_share_bonus=2.0,
    ),
    TuningConfig(
        name="ensemble_rank_blend_v1",
        description="general ensemble-style blend of scoring-fit, WR-upside, and balanced families",
        draft_weight=0.57,
        position_weight=0.21,
        production_weight=0.08,
        market_share_weight=0.08,
        scoring_fit_weight=0.06,
        position_scores={"RB": 81.0, "WR": 80.0, "TE": 58.0, "QB": 15.0},
        qb_1qb_penalty=-5.0,
        wr_share_bonus=2.5,
        rb_share_bonus=2.0,
        te_share_bonus=2.0,
    ),
]

ABLATION_CONFIGS = [
    TuningConfig(
        name="ablation_draft_capital_position_only",
        description="draft capital plus position only",
        draft_weight=0.76,
        position_weight=0.24,
        production_weight=0.00,
        market_share_weight=0.00,
        scoring_fit_weight=0.00,
        position_scores={"RB": 78.0, "WR": 76.0, "TE": 52.0, "QB": 18.0},
    ),
    TuningConfig(
        name="ablation_cfbd_production_only",
        description="CFBD production only",
        draft_weight=0.00,
        position_weight=0.00,
        production_weight=1.00,
        market_share_weight=0.00,
        scoring_fit_weight=0.00,
        position_scores={"RB": 0.0, "WR": 0.0, "TE": 0.0, "QB": 0.0},
    ),
    TuningConfig(
        name="ablation_cfbd_market_share_only",
        description="CFBD market-share/dominator only",
        draft_weight=0.00,
        position_weight=0.00,
        production_weight=0.00,
        market_share_weight=1.00,
        scoring_fit_weight=0.00,
        position_scores={"RB": 0.0, "WR": 0.0, "TE": 0.0, "QB": 0.0},
    ),
    TuningConfig(
        name="ablation_scoring_format_fit_only",
        description="scoring-format role fit only",
        draft_weight=0.00,
        position_weight=0.00,
        production_weight=0.00,
        market_share_weight=0.00,
        scoring_fit_weight=1.00,
        position_scores={"RB": 0.0, "WR": 0.0, "TE": 0.0, "QB": 0.0},
    ),
    TuningConfig(
        name="ablation_cfbd_production_market_share",
        description="CFBD production plus market share",
        draft_weight=0.00,
        position_weight=0.00,
        production_weight=0.50,
        market_share_weight=0.50,
        scoring_fit_weight=0.00,
        position_scores={"RB": 0.0, "WR": 0.0, "TE": 0.0, "QB": 0.0},
    ),
    TuningConfig(
        name="ablation_draft_cfbd_production_market_share",
        description="draft capital plus CFBD production and market share",
        draft_weight=0.58,
        position_weight=0.00,
        production_weight=0.21,
        market_share_weight=0.21,
        scoring_fit_weight=0.00,
        position_scores={"RB": 0.0, "WR": 0.0, "TE": 0.0, "QB": 0.0},
    ),
]

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

CONFIG_COLUMNS = [
    "candidate_name",
    "description",
    "draft_weight",
    "position_weight",
    "production_weight",
    "market_share_weight",
    "scoring_fit_weight",
    "anti_cheat",
]

DECISION_COLUMNS = [
    "candidate_name",
    "decision",
    "reason",
    "dev_top24_star_delta",
    "dev_top24_bust_delta",
    "final_top12_star_delta",
    "final_top24_star_delta",
    "final_top36_star_delta",
    "final_top12_bust_delta",
    "final_top24_bust_delta",
    "final_top36_bust_delta",
    "wr_final_top24_star_delta",
    "stability_verdict",
    "v2_candidate_board",
]

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


def production_component(row: dict[str, str]) -> float:
    if row.get("cfbd_feature_status") != "deterministic_joined":
        return 0.0
    position = row.get("position", "")
    if position == "QB":
        raw = (
            clipped(to_float(row.get("cfbd_passing_yards")) / 55.0, 48.0)
            + clipped(to_float(row.get("cfbd_passing_tds")) * 1.2, 24.0)
            + clipped(to_float(row.get("cfbd_rushing_yards")) / 45.0, 18.0)
        )
    elif position == "RB":
        raw = (
            clipped(to_float(row.get("cfbd_rushing_yards")) / 18.0, 52.0)
            + clipped(to_float(row.get("cfbd_rushing_tds")) * 1.4, 22.0)
            + clipped(to_float(row.get("cfbd_receiving_yards")) / 24.0, 14.0)
            + clipped(to_float(row.get("cfbd_receptions")) / 5.0, 8.0)
        )
    else:
        raw = (
            clipped(to_float(row.get("cfbd_receiving_yards")) / 16.0, 56.0)
            + clipped(to_float(row.get("cfbd_receiving_tds")) * 1.6, 22.0)
            + clipped(to_float(row.get("cfbd_receptions")) / 4.5, 16.0)
            + clipped(to_float(row.get("cfbd_rushing_yards")) / 55.0, 6.0)
        )
    return round(clipped(raw, 100.0), 3)


def market_share_component(row: dict[str, str]) -> float:
    if row.get("cfbd_feature_status") != "deterministic_joined":
        return 0.0
    position = row.get("position", "")
    if position == "QB":
        raw = (
            clipped(to_float(row.get("cfbd_passing_yard_share")) * 58.0, 42.0)
            + clipped(to_float(row.get("cfbd_passing_td_share")) * 42.0, 34.0)
            + clipped(to_float(row.get("cfbd_rushing_yard_share")) * 24.0, 12.0)
        )
    elif position == "RB":
        raw = (
            clipped(to_float(row.get("cfbd_rushing_yard_share")) * 58.0, 38.0)
            + clipped(to_float(row.get("cfbd_rushing_td_share")) * 42.0, 30.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 50.0, 18.0)
            + clipped(to_float(row.get("cfbd_receiving_yard_share")) * 28.0, 12.0)
        )
    else:
        raw = (
            clipped(to_float(row.get("cfbd_receiving_yard_share")) * 62.0, 42.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 54.0, 28.0)
            + clipped(to_float(row.get("cfbd_receiving_td_share")) * 42.0, 24.0)
            + clipped(to_float(row.get("cfbd_rushing_yard_share")) * 18.0, 6.0)
        )
    return round(clipped(raw, 100.0), 3)


def scoring_fit_component(row: dict[str, str]) -> float:
    if row.get("cfbd_feature_status") != "deterministic_joined":
        return 0.0
    position = row.get("position", "")
    if position == "QB":
        raw = (
            clipped(to_float(row.get("cfbd_passing_yards")) / 90.0, 30.0)
            + clipped(to_float(row.get("cfbd_rushing_yards")) / 42.0, 20.0)
            + clipped(to_float(row.get("cfbd_passing_td_share")) * 24.0, 18.0)
        )
    elif position == "RB":
        raw = (
            clipped(to_float(row.get("cfbd_rushing_yards")) / 20.0, 48.0)
            + clipped(to_float(row.get("cfbd_rushing_yard_share")) * 48.0, 30.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 36.0, 14.0)
            + clipped(to_float(row.get("cfbd_receiving_yards")) / 28.0, 8.0)
        )
    elif position == "TE":
        raw = (
            clipped(to_float(row.get("cfbd_receiving_yards")) / 18.0, 46.0)
            + clipped(to_float(row.get("cfbd_receiving_yard_share")) * 50.0, 30.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 36.0, 16.0)
        )
    else:
        raw = (
            clipped(to_float(row.get("cfbd_receiving_yards")) / 18.0, 48.0)
            + clipped(to_float(row.get("cfbd_receiving_yard_share")) * 48.0, 30.0)
            + clipped(to_float(row.get("cfbd_reception_share")) * 30.0, 14.0)
            + clipped(to_float(row.get("cfbd_rushing_yards")) / 45.0, 8.0)
        )
    return round(clipped(raw, 100.0), 3)


def score_value(row: dict[str, str], config: TuningConfig) -> float:
    position = row.get("position", "")
    score = (
        draft_points(row.get("draft_round", ""), row.get("overall_pick", "")) * config.draft_weight
        + config.position_scores.get(position, 40.0) * config.position_weight
        + production_component(row) * config.production_weight
        + market_share_component(row) * config.market_share_weight
        + scoring_fit_component(row) * config.scoring_fit_weight
    )
    if row.get("cfbd_feature_status") == "deterministic_joined":
        if position == "WR" and to_float(row.get("cfbd_receiving_yard_share")) >= 0.25:
            score += config.wr_share_bonus
        if position == "RB" and to_float(row.get("cfbd_rushing_yard_share")) >= 0.25:
            score += config.rb_share_bonus
        if position == "TE" and to_float(row.get("cfbd_receiving_yard_share")) >= 0.18:
            score += config.te_share_bonus
    if position == "QB":
        score += config.qb_1qb_penalty
    if safe_int(row.get("draft_round")) >= 3:
        score += config.round3_plus_penalty
    if safe_int(row.get("draft_round")) >= 5:
        score += config.late_round_penalty
        if row.get("cfbd_feature_status") == "deterministic_joined" and market_share_component(row) >= 50.0:
            score += config.late_round_dart_bonus
    return round(score, 3)


def score_rows_v1_1(rows: list[dict[str, str]], config: TuningConfig, field: str) -> list[dict[str, str]]:
    output = []
    for row in rows:
        out = dict(row)
        out["candidate_name"] = config.name
        out["production_component"] = f"{production_component(row):.3f}" if row.get("cfbd_feature_status") == "deterministic_joined" else ""
        out["market_share_component"] = f"{market_share_component(row):.3f}" if row.get("cfbd_feature_status") == "deterministic_joined" else ""
        out["scoring_fit_component"] = f"{scoring_fit_component(row):.3f}" if row.get("cfbd_feature_status") == "deterministic_joined" else ""
        out[field] = f"{score_value(row, config):.3f}"
        output.append(out)
    assign_ranks(output, field)
    return output


def selected_by_class_rank(rows: list[dict[str, str]], score_field: str, years: set[str], bucket: int) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("draft_year") in years and safe_int(row.get(f"{score_field}_class_rank", "999999")) <= bucket
    ]


def metric_row(
    model: str,
    metric_scope: str,
    scope_value: str,
    rows: list[dict[str, str]],
    selected: list[dict[str, str]],
    bucket: int,
    notes: str,
) -> dict[str, str]:
    stars_total = sum(1 for row in rows if row.get("star_label") == "1")
    stars = sum(1 for row in selected if row.get("star_label") == "1")
    busts_total = sum(1 for row in rows if row.get("bust_label") == "1")
    busts = sum(1 for row in selected if row.get("bust_label") == "1")
    avg_points = sum(to_float(row.get("three_year_points")) for row in selected) / len(selected) if selected else 0.0
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
        "avg_selected_points": f"{avg_points:.3f}" if selected else "",
        "notes": notes,
    }


def metrics_for_scored(
    rows: list[dict[str, str]],
    score_field: str,
    config: TuningConfig,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    split_rows = []
    year_rows = []
    position_rows = []
    wr_rows = []
    for split_name, years in SPLITS:
        scoped = [row for row in rows if row.get("draft_year") in years]
        for bucket in BUCKETS:
            split_rows.append(
                metric_row(
                    config.name,
                    "split_year_class",
                    split_name,
                    scoped,
                    selected_by_class_rank(scoped, score_field, years, bucket),
                    bucket,
                    config.description,
                )
            )
    for year in sorted(YEARS, key=safe_int):
        scoped = [row for row in rows if row.get("draft_year") == year]
        for bucket in BUCKETS:
            year_rows.append(
                metric_row(
                    config.name,
                    "year_class",
                    year,
                    scoped,
                    selected_by_class_rank(scoped, score_field, {year}, bucket),
                    bucket,
                    config.description,
                )
            )
    for position in POSITIONS:
        scoped = [row for row in rows if row.get("position") == position]
        for bucket in BUCKETS:
            selected = [
                row
                for row in scoped
                if safe_int(row.get(f"{score_field}_position_rank", "999999")) <= bucket
            ]
            position_rows.append(metric_row(config.name, "position", position, scoped, selected, bucket, config.description))
    for split_name, years in SPLITS:
        scoped = [row for row in rows if row.get("position") == "WR" and row.get("draft_year") in years]
        sorted_wr = sorted(scoped, key=lambda row: (-to_float(row.get(score_field)), safe_int(row.get("overall_pick")), row.get("player_name", "")))
        for bucket in BUCKETS:
            wr_rows.append(metric_row(config.name, "wr_signal", split_name, scoped, sorted_wr[:bucket], bucket, config.description))
    return split_rows, year_rows, position_rows, wr_rows


def metric_by_model(metrics: list[dict[str, str]], model: str, split: str, bucket: str) -> dict[str, str]:
    for row in metrics:
        if row["model"] == model and row["scope_value"] == split and row["bucket"] == bucket:
            return row
    raise KeyError((model, split, bucket))


def build_config_rows(configs: list[TuningConfig]) -> list[dict[str, str]]:
    return [
        {
            "candidate_name": config.name,
            "description": config.description,
            "draft_weight": f"{config.draft_weight:.3f}",
            "position_weight": f"{config.position_weight:.3f}",
            "production_weight": f"{config.production_weight:.3f}",
            "market_share_weight": f"{config.market_share_weight:.3f}",
            "scoring_fit_weight": f"{config.scoring_fit_weight:.3f}",
            "anti_cheat": "feature_family_only_no_name_id_school_team_year_outcome_rules",
        }
        for config in configs
    ]


def candidate_decisions(
    split_metrics: list[dict[str, str]],
    wr_metrics: list[dict[str, str]],
) -> list[dict[str, str]]:
    baseline = BASELINE_CONFIG.name
    rows = []
    for config in CANDIDATE_CONFIGS:
        if config.name == baseline:
            rows.append(
                {
                    "candidate_name": config.name,
                    "decision": "baseline_reference",
                    "reason": "reference candidate",
                    "dev_top24_star_delta": "",
                    "dev_top24_bust_delta": "",
                    "final_top12_star_delta": "",
                    "final_top24_star_delta": "",
                    "final_top36_star_delta": "",
                    "final_top12_bust_delta": "",
                    "final_top24_bust_delta": "",
                    "final_top36_bust_delta": "",
                    "wr_final_top24_star_delta": "",
                    "stability_verdict": "reference",
                    "v2_candidate_board": "no",
                }
            )
            continue
        deltas = candidate_deltas(split_metrics, wr_metrics, baseline, config.name)
        final_star_improved = deltas["final_top12_star_delta"] > 0 or deltas["final_top24_star_delta"] > 0 or deltas["final_top36_star_delta"] > 0
        final_star_preserved = deltas["final_top24_star_delta"] >= 0 and deltas["final_top36_star_delta"] >= -0.025
        bust_ok = deltas["final_top12_bust_delta"] <= 0.050 and deltas["final_top24_bust_delta"] <= 0.050
        dev_ok = deltas["dev_top24_star_delta"] >= -0.025 and deltas["dev_top24_bust_delta"] <= 0.050
        wr_ok = deltas["wr_final_top24_star_delta"] >= 0
        if final_star_improved and final_star_preserved and bust_ok and dev_ok and wr_ok:
            decision = "pass_for_manual_candidate"
            reason = "final validation improved or preserved star capture with acceptable bust and WR stability"
            stability = "GREEN"
        elif final_star_improved and bust_ok and dev_ok:
            decision = "yellow_wr_stability"
            reason = "general validation improved but WR-specific stability did not clear"
            stability = "YELLOW"
        else:
            decision = "fail_candidate_gate"
            reason = "validation/stability did not improve enough"
            stability = "RED" if not bust_ok else "YELLOW"
        rows.append(
            {
                "candidate_name": config.name,
                "decision": decision,
                "reason": reason,
                "dev_top24_star_delta": f"{deltas['dev_top24_star_delta']:.3f}",
                "dev_top24_bust_delta": f"{deltas['dev_top24_bust_delta']:.3f}",
                "final_top12_star_delta": f"{deltas['final_top12_star_delta']:.3f}",
                "final_top24_star_delta": f"{deltas['final_top24_star_delta']:.3f}",
                "final_top36_star_delta": f"{deltas['final_top36_star_delta']:.3f}",
                "final_top12_bust_delta": f"{deltas['final_top12_bust_delta']:.3f}",
                "final_top24_bust_delta": f"{deltas['final_top24_bust_delta']:.3f}",
                "final_top36_bust_delta": f"{deltas['final_top36_bust_delta']:.3f}",
                "wr_final_top24_star_delta": f"{deltas['wr_final_top24_star_delta']:.3f}",
                "stability_verdict": stability,
                "v2_candidate_board": "eligible_by_metrics_pending_current_board_mapping" if decision == "pass_for_manual_candidate" else "no",
            }
        )
    return rows


def candidate_deltas(
    split_metrics: list[dict[str, str]],
    wr_metrics: list[dict[str, str]],
    baseline: str,
    candidate: str,
) -> dict[str, float]:
    keys = {}
    for split, bucket in [
        ("dev_validation_2020_2021", "top_24"),
        ("final_validation_2022_2023", "top_12"),
        ("final_validation_2022_2023", "top_24"),
        ("final_validation_2022_2023", "top_36"),
    ]:
        base = metric_by_model(split_metrics, baseline, split, bucket)
        cand = metric_by_model(split_metrics, candidate, split, bucket)
        key = "dev" if split.startswith("dev") else "final"
        bucket_key = bucket.replace("top_", "top")
        keys[f"{key}_{bucket_key}_star_delta"] = to_float(cand["star_capture_rate"]) - to_float(base["star_capture_rate"])
        keys[f"{key}_{bucket_key}_bust_delta"] = to_float(cand["bust_rate_selected"]) - to_float(base["bust_rate_selected"])
    base_wr = metric_by_model(wr_metrics, baseline, "final_validation_2022_2023", "top_24")
    cand_wr = metric_by_model(wr_metrics, candidate, "final_validation_2022_2023", "top_24")
    keys["wr_final_top24_star_delta"] = to_float(cand_wr["star_capture_rate"]) - to_float(base_wr["star_capture_rate"])
    return keys


def choose_best(decisions: list[dict[str, str]]) -> str:
    passing = [row for row in decisions if row["decision"] == "pass_for_manual_candidate"]
    if not passing:
        return BASELINE_CONFIG.name
    passing.sort(
        key=lambda row: (
            to_float(row["final_top24_star_delta"]) + to_float(row["final_top36_star_delta"]),
            -to_float(row["final_top24_bust_delta"]),
            to_float(row["wr_final_top24_star_delta"]),
        ),
        reverse=True,
    )
    return passing[0]["candidate_name"]


def append_v2_decision(decisions: list[dict[str, str]], best_name: str, current_board: Path) -> str:
    best = next((row for row in decisions if row["candidate_name"] == best_name), None)
    if not best or best.get("decision") != "pass_for_manual_candidate":
        reason = "no candidate cleared validation/stability strongly enough"
    elif not current_board.exists():
        reason = "current 2026 board export not found for safe manual-use application"
    else:
        board_columns = set(read_csv(current_board)[0].keys()) if read_csv(current_board) else set()
        needed = {"player_name", "position", "school", "warning_flags", "final_rookie_rank_score"}
        if not needed.issubset(board_columns):
            reason = "current 2026 board lacks stable expected warning/display columns"
        else:
            reason = "withheld pending manual review because historical validation is a candidate audit, not approval to publish v2"
    decisions.append(
        {
            "candidate_name": "v2_board_decision",
            "decision": "not_created",
            "reason": reason,
            "dev_top24_star_delta": "",
            "dev_top24_bust_delta": "",
            "final_top12_star_delta": "",
            "final_top24_star_delta": "",
            "final_top36_star_delta": "",
            "final_top12_bust_delta": "",
            "final_top24_bust_delta": "",
            "final_top36_bust_delta": "",
            "wr_final_top24_star_delta": "",
            "stability_verdict": "blocked",
            "v2_candidate_board": "no",
        }
    )
    return "no"


def diagnostics_for_candidate(rows: list[dict[str, str]], model: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    selected_top36 = selected_by_class_rank(rows, "candidate_score", YEARS, 36)
    missed = [row for row in rows if row.get("star_label") == "1" and row not in selected_top36]
    missed.sort(key=lambda row: (-to_float(row.get("three_year_points")), row.get("draft_year", ""), row.get("player_name", "")))
    busts = [row for row in selected_top36 if row.get("bust_label") == "1"]
    busts.sort(key=lambda row: (row.get("draft_year", ""), safe_int(row.get("candidate_score_class_rank", "999999"))))
    return [diag_row(model, row, "missed_star") for row in missed[:50]], [diag_row(model, row, "high_ranked_bust") for row in busts[:100]]


def diag_row(model: str, row: dict[str, str], kind: str) -> dict[str, str]:
    return {
        "candidate_name": model,
        "diagnostic_type": kind,
        "draft_year": row.get("draft_year", ""),
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "draft_round": row.get("draft_round", ""),
        "overall_pick": row.get("overall_pick", ""),
        "candidate_score": row.get("candidate_score", ""),
        "candidate_class_rank": row.get("candidate_score_class_rank", ""),
        "star_label": row.get("star_label", ""),
        "bust_label": row.get("bust_label", ""),
        "three_year_points": row.get("three_year_points", ""),
        "cfbd_feature_status": row.get("cfbd_feature_status", ""),
        "diagnosis": "diagnostic_names_only_no_player_specific_tuning",
    }


def best_minus_configs(best: TuningConfig) -> list[TuningConfig]:
    return [
        TuningConfig(
            name=f"{best.name}_minus_draft",
            description="best candidate with draft capital removed",
            draft_weight=0.0,
            position_weight=best.position_weight,
            production_weight=best.production_weight,
            market_share_weight=best.market_share_weight,
            scoring_fit_weight=best.scoring_fit_weight,
            position_scores=best.position_scores,
        ),
        TuningConfig(
            name=f"{best.name}_minus_production",
            description="best candidate with CFBD production removed",
            draft_weight=best.draft_weight,
            position_weight=best.position_weight,
            production_weight=0.0,
            market_share_weight=best.market_share_weight,
            scoring_fit_weight=best.scoring_fit_weight,
            position_scores=best.position_scores,
        ),
        TuningConfig(
            name=f"{best.name}_minus_market_share",
            description="best candidate with CFBD market share removed",
            draft_weight=best.draft_weight,
            position_weight=best.position_weight,
            production_weight=best.production_weight,
            market_share_weight=0.0,
            scoring_fit_weight=best.scoring_fit_weight,
            position_scores=best.position_scores,
        ),
        TuningConfig(
            name=f"{best.name}_minus_scoring_fit",
            description="best candidate with scoring-format fit removed",
            draft_weight=best.draft_weight,
            position_weight=best.position_weight,
            production_weight=best.production_weight,
            market_share_weight=best.market_share_weight,
            scoring_fit_weight=0.0,
            position_scores=best.position_scores,
        ),
    ]


def frontier_rows(split_metrics: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for model in sorted({row["model"] for row in split_metrics}):
        for bucket in [f"top_{item}" for item in BUCKETS]:
            final = metric_by_model(split_metrics, model, "final_validation_2022_2023", bucket)
            rows.append(
                {
                    "candidate_name": model,
                    "bucket": bucket,
                    "final_star_capture_rate": final["star_capture_rate"],
                    "final_bust_rate_selected": final["bust_rate_selected"],
                    "frontier_note": "higher star capture with lower bust rate is preferred",
                }
            )
    return rows


FRONTIER_COLUMNS = [
    "candidate_name",
    "bucket",
    "final_star_capture_rate",
    "final_bust_rate_selected",
    "frontier_note",
]


def write_readme(output_dir: Path, best_name: str, v2_created: str) -> None:
    text = [
        "# Rookie Model Tuning Runway v1.1",
        "",
        "Local-only exports for the v1.1 historical tuning runway.",
        "",
        "- Train split: 2010-2019",
        "- Development validation split: 2020-2021",
        "- Final validation split: 2022-2023",
        f"- Best candidate: {best_name}",
        f"- v2 candidate board created: {v2_created}",
        "",
        "No production ranking, app wiring, probabilities, bands, hidden sort keys, or promoted artifacts.",
        "Outcome labels are evaluation-only. Names are diagnostic-only.",
    ]
    (output_dir / "README_ROOKIE_MODEL_TUNING_RUNWAY_V1_1_20260615.md").write_text("\n".join(text), encoding="utf-8")


def build_exports(
    labels: Path,
    repaired_join: Path,
    output_dir: Path,
    current_board: Path = DEFAULT_CURRENT_BOARD,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = load_runway_rows(labels, repaired_join)
    scored_by_candidate: dict[str, list[dict[str, str]]] = {}
    split_metrics: list[dict[str, str]] = []
    year_metrics: list[dict[str, str]] = []
    position_metrics: list[dict[str, str]] = []
    wr_metrics: list[dict[str, str]] = []

    for config in CANDIDATE_CONFIGS:
        scored = score_rows_v1_1(rows, config, "candidate_score")
        scored_by_candidate[config.name] = scored
        split, year, position, wr = metrics_for_scored(scored, "candidate_score", config)
        split_metrics.extend(split)
        year_metrics.extend(year)
        position_metrics.extend(position)
        wr_metrics.extend(wr)

    decisions = candidate_decisions(split_metrics, wr_metrics)
    best_name = choose_best(decisions)
    best_config = next(config for config in CANDIDATE_CONFIGS if config.name == best_name)
    v2_created = append_v2_decision(decisions, best_name, current_board)
    missed, busts = diagnostics_for_candidate(scored_by_candidate[best_name], best_name)

    ablation_metrics: list[dict[str, str]] = []
    for config in [*ABLATION_CONFIGS, *best_minus_configs(best_config)]:
        scored = score_rows_v1_1(rows, config, "candidate_score")
        split, _, _, _ = metrics_for_scored(scored, "candidate_score", config)
        ablation_metrics.extend(split)

    write_csv(output_dir / "candidate_configurations_v1_1_20260615.csv", build_config_rows(CANDIDATE_CONFIGS), CONFIG_COLUMNS)
    write_csv(output_dir / "candidate_validation_metrics_v1_1_20260615.csv", split_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "candidate_year_class_metrics_v1_1_20260615.csv", year_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "candidate_position_metrics_v1_1_20260615.csv", position_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "candidate_wr_signal_metrics_v1_1_20260615.csv", wr_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "feature_ablation_metrics_v1_1_20260615.csv", ablation_metrics, METRIC_COLUMNS)
    write_csv(output_dir / "candidate_star_bust_frontier_v1_1_20260615.csv", frontier_rows(split_metrics), FRONTIER_COLUMNS)
    write_csv(output_dir / "candidate_decision_v1_1_20260615.csv", decisions, DECISION_COLUMNS)
    write_csv(output_dir / "top_missed_stars_after_tuning_v1_1_20260615.csv", missed, DIAG_COLUMNS)
    write_csv(output_dir / "high_ranked_busts_after_tuning_v1_1_20260615.csv", busts, DIAG_COLUMNS)
    write_readme(output_dir, best_name, v2_created)
    return {
        "rows": rows,
        "split_metrics": split_metrics,
        "year_metrics": year_metrics,
        "position_metrics": position_metrics,
        "wr_metrics": wr_metrics,
        "ablation_metrics": ablation_metrics,
        "decisions": decisions,
        "best_candidate": best_name,
        "v2_created": v2_created,
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--repaired-join", type=Path, default=DEFAULT_REPAIRED_JOIN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--current-board", type=Path, default=DEFAULT_CURRENT_BOARD)
    args = parser.parse_args(argv)
    result = build_exports(args.labels, args.repaired_join, args.output_dir, args.current_board)
    print(f"rows={len(result['rows'])}")
    print(f"best_candidate={result['best_candidate']}")
    print(f"v2_created={result['v2_created']}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
