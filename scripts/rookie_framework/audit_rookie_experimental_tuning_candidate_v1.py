"""Experimental rookie tuning candidate audit v1.

This script compares general feature-family candidate configurations against
the expanded 2010-2023 complete-window label pool. It does not create a v2
board, tune from names, write app-readable outputs, or promote artifacts.
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
    draft_points,
    safe_int,
    to_float,
)


DEFAULT_LABELS = Path(
    "local_exports/rookie_framework/historical_allowlist_qa_expanded_baseline_20260615/"
    "expanded_historical_labels_v2_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/experimental_tuning_candidate_v1_20260615")
TRAIN_YEARS = {str(year) for year in range(2010, 2022)}
VALIDATION_YEARS = {"2022", "2023"}
ALL_YEARS = TRAIN_YEARS | VALIDATION_YEARS
BUCKETS = (12, 24, 36)
POSITIONS = ("QB", "RB", "WR", "TE")


@dataclass(frozen=True)
class CandidateConfig:
    name: str
    description: str
    draft_weight: float
    position_weight: float
    position_scores: dict[str, float]
    wr_mid_pick_bonus: float = 0.0
    wr_day2_bonus: float = 0.0
    rb_day2_3_bonus: float = 0.0
    te_day2_3_bonus: float = 0.0
    qb_penalty: float = 0.0
    round3_plus_penalty: float = 0.0
    late_round1_wr_penalty: float = 0.0


CONFIGS = [
    CandidateConfig(
        name="baseline",
        description="committed expanded baseline: draft capital plus position prior",
        draft_weight=0.78,
        position_weight=0.22,
        position_scores={"RB": 72.0, "WR": 70.0, "TE": 42.0, "QB": 24.0},
    ),
    CandidateConfig(
        name="wr_upside_plus",
        description="general WR mid-first/day-two upside plus; no player-specific logic",
        draft_weight=0.74,
        position_weight=0.26,
        position_scores={"RB": 72.0, "WR": 80.0, "TE": 42.0, "QB": 24.0},
        wr_mid_pick_bonus=4.0,
        wr_day2_bonus=2.0,
    ),
    CandidateConfig(
        name="scoring_format_fit_plus",
        description="non-PPR first-down fit proxy: RB/TE day-two/three role paths plus 1QB discipline",
        draft_weight=0.72,
        position_weight=0.28,
        position_scores={"RB": 82.0, "WR": 74.0, "TE": 60.0, "QB": 18.0},
        rb_day2_3_bonus=10.0,
        te_day2_3_bonus=16.0,
        qb_penalty=-4.0,
    ),
    CandidateConfig(
        name="draft_capital_trap_guard",
        description="reduces pure draft-capital trust with broad round and position guardrails",
        draft_weight=0.70,
        position_weight=0.30,
        position_scores={"RB": 78.0, "WR": 74.0, "TE": 50.0, "QB": 18.0},
        round3_plus_penalty=-4.0,
        late_round1_wr_penalty=-3.0,
        qb_penalty=-2.0,
    ),
    CandidateConfig(
        name="balanced_star_bust",
        description="balanced RB/WR/TE role-path boost with mild later-round guard",
        draft_weight=0.70,
        position_weight=0.30,
        position_scores={"RB": 82.0, "WR": 82.0, "TE": 62.0, "QB": 16.0},
        wr_mid_pick_bonus=6.0,
        rb_day2_3_bonus=10.0,
        te_day2_3_bonus=16.0,
        qb_penalty=-6.0,
        round3_plus_penalty=-2.0,
    ),
    CandidateConfig(
        name="position_calibrated",
        description="explicit 1QB/TE/RB/WR calibration proxy; still draft-capital and position only",
        draft_weight=0.73,
        position_weight=0.27,
        position_scores={"RB": 76.0, "WR": 82.0, "TE": 46.0, "QB": 18.0},
        wr_mid_pick_bonus=3.0,
        te_day2_3_bonus=2.0,
        qb_penalty=-3.0,
    ),
]


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


def rate(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.3f}" if denominator else "0.000"


def avg(values: list[float]) -> str:
    return f"{sum(values) / len(values):.3f}" if values else ""


def complete_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        dict(row)
        for row in rows
        if row.get("backtest_ready") == "yes"
        and row.get("partial_window_only") == "no"
        and row.get("draft_year") in ALL_YEARS
    ]


def candidate_score(row: dict[str, str], config: CandidateConfig) -> float:
    position = row.get("position", "")
    draft_round = safe_int(row.get("draft_round", ""))
    pick = safe_int(row.get("overall_pick", ""))
    score = (
        draft_points(row.get("draft_round", ""), row.get("overall_pick", "")) * config.draft_weight
        + config.position_scores.get(position, 40.0) * config.position_weight
    )
    if position == "WR" and 15 <= pick <= 80:
        score += config.wr_mid_pick_bonus
    if position == "WR" and draft_round in {2, 3}:
        score += config.wr_day2_bonus
    if position == "RB" and draft_round in {2, 3}:
        score += config.rb_day2_3_bonus
    if position == "TE" and draft_round in {2, 3}:
        score += config.te_day2_3_bonus
    if position == "QB":
        score += config.qb_penalty
    if draft_round >= 3:
        score += config.round3_plus_penalty
    if position == "WR" and draft_round == 1 and pick >= 6:
        score += config.late_round1_wr_penalty
    return round(score, 3)


def scored_rows(rows: list[dict[str, str]], config: CandidateConfig) -> list[dict[str, str]]:
    output = []
    for row in rows:
        out = dict(row)
        out["candidate_name"] = config.name
        out["candidate_score"] = f"{candidate_score(out, config):.3f}"
        output.append(out)
    for year in sorted({row["draft_year"] for row in output}, key=safe_int):
        year_rows = [row for row in output if row["draft_year"] == year]
        year_rows.sort(key=lambda row: (-to_float(row["candidate_score"]), to_float(row.get("overall_pick", ""), 999), row["player_name"]))
        for rank, row in enumerate(year_rows, start=1):
            row["candidate_class_rank"] = str(rank)
    for position in POSITIONS:
        pos_rows = [row for row in output if row["position"] == position]
        pos_rows.sort(key=lambda row: (-to_float(row["candidate_score"]), to_float(row.get("overall_pick", ""), 999), row["player_name"]))
        for rank, row in enumerate(pos_rows, start=1):
            row["candidate_position_rank"] = str(rank)
    output.sort(key=lambda row: (-to_float(row["candidate_score"]), to_float(row.get("overall_pick", ""), 999), row["player_name"]))
    for rank, row in enumerate(output, start=1):
        row["candidate_global_rank"] = str(rank)
    return output


def selected_by_year(rows: list[dict[str, str]], years: set[str], bucket: int) -> list[dict[str, str]]:
    selected = []
    for year in sorted(years):
        selected.extend(
            row
            for row in rows
            if row["draft_year"] == year and safe_int(row.get("candidate_class_rank", "999999")) <= bucket
        )
    return selected


def selected_by_position(rows: list[dict[str, str]], position: str, bucket: int) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["position"] == position and safe_int(row.get("candidate_position_rank", "999999")) <= bucket
    ]


def metric_row(candidate: str, split: str, scope: str, value: str, rows: list[dict[str, str]], selected: list[dict[str, str]], bucket: int) -> dict[str, str]:
    stars_total = sum(1 for row in rows if row["star_label"] == "1")
    stars = sum(1 for row in selected if row["star_label"] == "1")
    busts_total = sum(1 for row in rows if row["bust_label"] == "1")
    busts = sum(1 for row in selected if row["bust_label"] == "1")
    return {
        "candidate_name": candidate,
        "split": split,
        "metric_scope": scope,
        "scope_value": value,
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
    }


def split_metrics(rows: list[dict[str, str]], config: CandidateConfig) -> list[dict[str, str]]:
    output = []
    splits = {
        "train_2010_2021": TRAIN_YEARS,
        "validation_2022_2023": VALIDATION_YEARS,
        "full_2010_2023": ALL_YEARS,
    }
    for split, years in splits.items():
        scoped = [row for row in rows if row["draft_year"] in years]
        for bucket in BUCKETS:
            output.append(metric_row(config.name, split, "year_class", "all_years_in_split", scoped, selected_by_year(scoped, years, bucket), bucket))
    return output


def year_metrics(rows: list[dict[str, str]], config: CandidateConfig) -> list[dict[str, str]]:
    output = []
    for year in sorted(ALL_YEARS, key=safe_int):
        scoped = [row for row in rows if row["draft_year"] == year]
        split = "train_2010_2021" if year in TRAIN_YEARS else "validation_2022_2023"
        for bucket in BUCKETS:
            selected = [
                row
                for row in scoped
                if safe_int(row.get("candidate_class_rank", "999999")) <= bucket
            ]
            output.append(metric_row(config.name, split, "year", year, scoped, selected, bucket))
    return output


def position_metrics(rows: list[dict[str, str]], config: CandidateConfig) -> list[dict[str, str]]:
    output = []
    for split, years in {"train_2010_2021": TRAIN_YEARS, "validation_2022_2023": VALIDATION_YEARS}.items():
        split_rows = [row for row in rows if row["draft_year"] in years]
        for position in POSITIONS:
            scoped = sorted(
                [row for row in split_rows if row["position"] == position],
                key=lambda row: (-to_float(row["candidate_score"]), to_float(row.get("overall_pick", ""), 999), row["player_name"]),
            )
            for bucket in BUCKETS:
                selected = scoped[:bucket]
                output.append(metric_row(config.name, split, "position", position, scoped, selected, bucket))
    return output


def rank_delta_rows(base_rows: list[dict[str, str]], candidate_rows: list[dict[str, str]], candidate_name: str) -> dict[str, tuple[int, int]]:
    base = {row["historical_label_key"]: safe_int(row["candidate_class_rank"]) for row in base_rows}
    cand = {row["historical_label_key"]: safe_int(row["candidate_class_rank"]) for row in candidate_rows}
    return {key: (base.get(key, 999999), cand.get(key, 999999)) for key in cand}


def diagnostics(base_rows: list[dict[str, str]], candidate_rows: list[dict[str, str]], candidate_name: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    deltas = rank_delta_rows(base_rows, candidate_rows, candidate_name)
    missed_stars = []
    high_busts = []
    for row in candidate_rows:
        base_rank, cand_rank = deltas.get(row["historical_label_key"], (999999, 999999))
        common = {
            "candidate_name": candidate_name,
            "split": "train_2010_2021" if row["draft_year"] in TRAIN_YEARS else "validation_2022_2023",
            "draft_year": row["draft_year"],
            "player_name": row["player_name"],
            "position": row["position"],
            "draft_round": row["draft_round"],
            "overall_pick": row["overall_pick"],
            "base_class_rank": str(base_rank),
            "candidate_class_rank": str(cand_rank),
            "candidate_score": row["candidate_score"],
            "three_year_points": row["three_year_points"],
            "historical_label_status": row["historical_label_status"],
            "anti_cheat_note": "diagnosis only; no player-specific tuning",
        }
        if row["star_label"] == "1" and cand_rank > 36:
            missed_stars.append(
                {
                    **common,
                    "diagnostic_classification": "feature_availability_gap" if row["position"] in {"WR", "RB"} else "position_calibration_issue",
                    "general_hypothesis": "expanded pool lacks structured production/role/archetype feature families beyond draft capital and position",
                }
            )
        if row["bust_label"] == "1" and cand_rank <= 36:
            high_busts.append(
                {
                    **common,
                    "diagnostic_classification": "draft_capital_trap" if safe_int(row["draft_round"]) <= 2 else "acceptable_risk",
                    "general_hypothesis": "candidate selection still needs general warning/gate inputs before board creation",
                }
            )
    missed_stars.sort(key=lambda row: (row["split"], safe_int(row["candidate_class_rank"]), -to_float(row["three_year_points"])))
    high_busts.sort(key=lambda row: (row["split"], safe_int(row["candidate_class_rank"])))
    return missed_stars[:40], high_busts[:40]


def config_rows() -> list[dict[str, str]]:
    rows = []
    for config in CONFIGS:
        rows.append(
            {
                "candidate_name": config.name,
                "description": config.description,
                "draft_weight": f"{config.draft_weight:.3f}",
                "position_weight": f"{config.position_weight:.3f}",
                "position_scores": ";".join(f"{key}:{value:.1f}" for key, value in sorted(config.position_scores.items())),
                "wr_mid_pick_bonus": f"{config.wr_mid_pick_bonus:.3f}",
                "wr_day2_bonus": f"{config.wr_day2_bonus:.3f}",
                "rb_day2_3_bonus": f"{config.rb_day2_3_bonus:.3f}",
                "te_day2_3_bonus": f"{config.te_day2_3_bonus:.3f}",
                "qb_penalty": f"{config.qb_penalty:.3f}",
                "round3_plus_penalty": f"{config.round3_plus_penalty:.3f}",
                "late_round1_wr_penalty": f"{config.late_round1_wr_penalty:.3f}",
                "anti_cheat_note": "general feature-family weights/gates only; no names, IDs, teams, schools, years, ADP, market, probabilities, or bands",
            }
        )
    return rows


def metric_lookup(metrics: list[dict[str, str]], candidate: str, split: str, bucket: str) -> dict[str, str]:
    for row in metrics:
        if row["candidate_name"] == candidate and row["split"] == split and row["metric_scope"] == "year_class" and row["bucket"] == bucket:
            return row
    raise KeyError((candidate, split, bucket))


def decision_rows(metrics: list[dict[str, str]], position_rows: list[dict[str, str]], candidate_names: list[str]) -> list[dict[str, str]]:
    base12 = metric_lookup(metrics, "baseline", "validation_2022_2023", "top_12")
    base24 = metric_lookup(metrics, "baseline", "validation_2022_2023", "top_24")
    base_top12_stars = safe_int(base12["stars_captured"])
    base_top24_stars = safe_int(base24["stars_captured"])
    base_top12_bust = to_float(base12["bust_rate_selected"])
    base_top24_bust = to_float(base24["bust_rate_selected"])
    rows = []
    best_name = "none"
    best_score = -999.0
    for name in candidate_names:
        if name == "baseline":
            continue
        top12 = metric_lookup(metrics, name, "validation_2022_2023", "top_12")
        top24 = metric_lookup(metrics, name, "validation_2022_2023", "top_24")
        star_gain_12 = safe_int(top12["stars_captured"]) - base_top12_stars
        star_gain_24 = safe_int(top24["stars_captured"]) - base_top24_stars
        bust_delta_12 = to_float(top12["bust_rate_selected"]) - base_top12_bust
        bust_delta_24 = to_float(top24["bust_rate_selected"]) - base_top24_bust
        gate = star_gain_12 > 0 and star_gain_24 >= 0 and bust_delta_12 <= 0.05 and bust_delta_24 <= 0.05
        score = star_gain_12 * 10 + star_gain_24 * 4 - max(0.0, bust_delta_12) * 30 - max(0.0, bust_delta_24) * 20
        if gate and score > best_score:
            best_score = score
            best_name = name
        rows.append(
            {
                "candidate_name": name,
                "validation_gate": "PASS" if gate else "FAIL",
                "validation_top12_star_gain": str(star_gain_12),
                "validation_top24_star_gain": str(star_gain_24),
                "validation_top12_bust_delta": f"{bust_delta_12:.3f}",
                "validation_top24_bust_delta": f"{bust_delta_24:.3f}",
                "candidate_decision": "eligible_candidate" if gate else "not_selected",
                "notes": "validation uses 2022-2023 complete-window rows; no names or outcomes used as scoring features",
            }
        )
    wr_rows = [
        row
        for row in position_rows
        if row["split"] == "validation_2022_2023" and row["metric_scope"] == "position" and row["scope_value"] == "WR" and row["bucket"] == "top_12"
    ]
    base_wr = next(row for row in wr_rows if row["candidate_name"] == "baseline")
    best_wr = next((row for row in wr_rows if row["candidate_name"] == best_name), {})
    rows.append(
        {
            "candidate_name": best_name,
            "validation_gate": "PASS" if best_name != "none" else "FAIL",
            "validation_top12_star_gain": "",
            "validation_top24_star_gain": "",
            "validation_top12_bust_delta": "",
            "validation_top24_bust_delta": "",
            "candidate_decision": "best_candidate_selected_for_audit_only" if best_name != "none" else "no_candidate_selected",
            "notes": (
                f"best candidate does not create a v2 board; validation WR top12 capture "
                f"baseline={base_wr.get('stars_captured')}/{base_wr.get('stars_total')} "
                f"best={best_wr.get('stars_captured', '')}/{best_wr.get('stars_total', '')}"
            ),
        }
    )
    return rows


def build_exports(labels_path: Path, output_dir: Path) -> dict[str, int | str]:
    labels = complete_rows(read_csv(labels_path))
    config_output = config_rows()
    split_output: list[dict[str, str]] = []
    year_output: list[dict[str, str]] = []
    position_output: list[dict[str, str]] = []
    missed_output: list[dict[str, str]] = []
    bust_output: list[dict[str, str]] = []
    scored_by_name: dict[str, list[dict[str, str]]] = {}
    for config in CONFIGS:
        scored = scored_rows(labels, config)
        scored_by_name[config.name] = scored
        split_output.extend(split_metrics(scored, config))
        year_output.extend(year_metrics(scored, config))
        position_output.extend(position_metrics(scored, config))
    for config in CONFIGS:
        if config.name == "baseline":
            continue
        missed, busts = diagnostics(scored_by_name["baseline"], scored_by_name[config.name], config.name)
        missed_output.extend(missed)
        bust_output.extend(busts)
    decisions = decision_rows(split_output, position_output, [config.name for config in CONFIGS])

    write_csv(
        output_dir / "candidate_configurations_v1_20260615.csv",
        config_output,
        [
            "candidate_name",
            "description",
            "draft_weight",
            "position_weight",
            "position_scores",
            "wr_mid_pick_bonus",
            "wr_day2_bonus",
            "rb_day2_3_bonus",
            "te_day2_3_bonus",
            "qb_penalty",
            "round3_plus_penalty",
            "late_round1_wr_penalty",
            "anti_cheat_note",
        ],
    )
    metric_columns = [
        "candidate_name",
        "split",
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
    ]
    write_csv(output_dir / "candidate_split_metrics_v1_20260615.csv", split_output, metric_columns)
    write_csv(output_dir / "candidate_year_metrics_v1_20260615.csv", year_output, metric_columns)
    write_csv(output_dir / "candidate_position_metrics_v1_20260615.csv", position_output, metric_columns)
    diagnostic_columns = [
        "candidate_name",
        "split",
        "draft_year",
        "player_name",
        "position",
        "draft_round",
        "overall_pick",
        "base_class_rank",
        "candidate_class_rank",
        "candidate_score",
        "three_year_points",
        "historical_label_status",
        "diagnostic_classification",
        "general_hypothesis",
        "anti_cheat_note",
    ]
    write_csv(output_dir / "candidate_top_missed_stars_v1_20260615.csv", missed_output, diagnostic_columns)
    write_csv(output_dir / "candidate_high_ranked_busts_v1_20260615.csv", bust_output, diagnostic_columns)
    write_csv(
        output_dir / "candidate_decision_v1_20260615.csv",
        decisions,
        [
            "candidate_name",
            "validation_gate",
            "validation_top12_star_gain",
            "validation_top24_star_gain",
            "validation_top12_bust_delta",
            "validation_top24_bust_delta",
            "candidate_decision",
            "notes",
        ],
    )
    (output_dir / "README_ROOKIE_EXPERIMENTAL_TUNING_CANDIDATE_V1_20260615.md").write_text(
        "# Rookie Experimental Tuning Candidate Audit v1\n\n"
        "Local-only candidate tuning audit exports. No v2 board, production promotion, app wiring, probabilities, bands, "
        "hidden sort keys, or ADP/market/private-score inputs.\n",
        encoding="utf-8",
    )
    best = next((row["candidate_name"] for row in decisions if row["candidate_decision"] == "best_candidate_selected_for_audit_only"), "none")
    return {
        "label_rows": len(labels),
        "candidate_count": len(CONFIGS),
        "split_metric_rows": len(split_output),
        "year_metric_rows": len(year_output),
        "position_metric_rows": len(position_output),
        "missed_star_rows": len(missed_output),
        "high_bust_rows": len(bust_output),
        "best_candidate": best,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    counts = build_exports(args.labels, args.output_dir)
    for key in sorted(counts):
        print(f"{key}={counts[key]}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
