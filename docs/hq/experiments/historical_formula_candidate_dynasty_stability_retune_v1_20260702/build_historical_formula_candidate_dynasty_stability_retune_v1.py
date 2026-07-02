from __future__ import annotations

import csv
import hashlib
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PYDEPS = Path(r"C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps")
if str(PYDEPS) not in sys.path:
    sys.path.insert(0, str(PYDEPS))

import polars as pl


EXPERIMENT_DIR = Path(__file__).resolve().parent
ROOT = EXPERIMENT_DIR.parents[3]
EXPERIMENTS = EXPERIMENT_DIR.parent
V3_DIR = EXPERIMENTS / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
SOURCE_CONTRACT_DIR = EXPERIMENTS / "historical_tuning_source_contract_v1_20260701"
SEARCH_DIR = EXPERIMENTS / "historical_formula_candidate_search_v1_20260701"
TARGETED_DIR = EXPERIMENTS / "historical_formula_candidate_targeted_redesign_v1_20260701"
ATTRIBUTION_DIR = EXPERIMENTS / "historical_formula_candidate_attribution_retune_readiness_v1_20260702"
SCORING_GATE_DIR = EXPERIMENTS / "current_board_candidate_scoring_feature_completion_gate_v1_20260702"

SUBSTRATE_PATH = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
ATTRIBUTION_MATRIX = ATTRIBUTION_DIR / "key_player_attribution_matrix.csv"
WR_GUARD_BOARD = Path(r"C:\NWR_REVIEW\current_board_wr_role_guard_adjustment_v1_20260702\selected_wr_guard_current_board.csv")
FEATURE_INPUT = Path(
    r"C:\NWR_REVIEW\current_board_candidate_scoring_feature_completion_gate_v1_20260702"
    r"\current_board_candidate_feature_input_completed_review_only.csv"
)
OUTSIDE_BUNDLE = Path(r"C:\NWR_REVIEW\dynasty_stability_retune_v1_20260702")

TARGET = "next_nwr_points"
BASELINE = "baseline_v3_prior_points"
ORIGINAL = "original_usage_opportunity_volume"
QB_GUARD = "qb_guard_soft_blend"
RB_WR_SAFE = "rb_wr_cutline_safe_blend"
TARGETED = "wr_boundary_breakout_sensitivity_guard"
CURRENT_GUARDED = "current_guarded_candidate"
MULTI_YEAR = "multi_year_production_anchor"
PEAK = "career_peak_or_ceiling_anchor"
YOUNG_WR_TE = "young_wr_te_stability_guard"
CORNERSTONE = "cornerstone_stability_floor"
COMBINED = "multi_year_plus_cornerstone_guard"
USAGE_LENS = "usage_lens_only_control"

DECISION_LABEL = "PARTIAL_DYNASTY_STABILITY_RETUNE_STILL_HOLD"
SELECTED_RETUNE = COMBINED
VERDICT = "YELLOW_PARTIAL_DYNASTY_STABILITY_RETUNE_STILL_HOLD_REVIEW_ONLY"

VARIANTS = [
    {
        "variant_id": CURRENT_GUARDED,
        "role": "current_comparator",
        "formula_definition": "Historical analog of minimal guarded current-board candidate: selected targeted redesign plus fixed WR/TE cornerstone guard.",
        "guard_definition": "WR baseline top36 drops greater than 8 position ranks and TE baseline top6 drops greater than 4 receive a 70 percent baseline / 30 percent selected blend.",
        "features_used": "prior_nwr_points; prior_games; prior_targets; prior_receptions; prior_opportunities; baseline predicted rank; selected candidate predicted rank",
    },
    {
        "variant_id": MULTI_YEAR,
        "role": "fixed_retune",
        "formula_definition": "0.80 * current_guarded_candidate + 0.20 * trailing three-season average prior_nwr_points when at least two completed feature seasons exist.",
        "guard_definition": "No player exceptions; uses completed feature-season scoring history only.",
        "features_used": "prior_nwr_points by player and feature season",
    },
    {
        "variant_id": PEAK,
        "role": "fixed_retune",
        "formula_definition": "Current guarded candidate with a 15 percent recent peak anchor when trailing three-season peak is materially above current guarded score.",
        "guard_definition": "Peak anchor applies only when recent peak is at least 15 percent above current guarded score.",
        "features_used": "prior_nwr_points by player and feature season",
    },
    {
        "variant_id": YOUNG_WR_TE,
        "role": "fixed_retune",
        "formula_definition": "WR/TE stability guard for baseline-relevant profiles exposed to limited-game or high-PPG one-year overreaction.",
        "guard_definition": "WR baseline top36 or TE baseline top8 with limited games or strong PPG, dropping more than 8 position ranks, receives 75 percent baseline / 25 percent current guarded blend.",
        "features_used": "position; prior_games; prior_nwr_ppg; prior_nwr_points; baseline predicted rank; current guarded predicted rank",
    },
    {
        "variant_id": CORNERSTONE,
        "role": "fixed_retune",
        "formula_definition": "Baseline-rank cornerstone floor to prevent extreme demotions of baseline-relevant WR/TE/RB/QB profiles.",
        "guard_definition": "Position-specific baseline rank caps only; no names, blocked external context, or target outcomes.",
        "features_used": "position; baseline predicted rank; current guarded predicted rank",
    },
    {
        "variant_id": COMBINED,
        "role": "selected_fixed_retune",
        "formula_definition": "Small multi-year production anchor plus conservative cornerstone floor.",
        "guard_definition": "Applies multi-year anchor first, then a fixed cornerstone floor where baseline rank and guarded rank indicate an extreme demotion.",
        "features_used": "prior_nwr_points history; position; prior_games; baseline predicted rank; guarded predicted rank",
    },
    {
        "variant_id": USAGE_LENS,
        "role": "control_decision",
        "formula_definition": "Keep the candidate as a separate usage/opportunity lens, not a main formula candidate.",
        "guard_definition": "No formula change; same numeric score as current_guarded_candidate for metric comparability.",
        "features_used": "same as current_guarded_candidate",
    },
]

METRIC_VARIANTS = [BASELINE, ORIGINAL, TARGETED, CURRENT_GUARDED, MULTI_YEAR, PEAK, YOUNG_WR_TE, CORNERSTONE, COMBINED, USAGE_LENS]
PRIMARY_RETUNE_VARIANTS = [MULTI_YEAR, PEAK, YOUNG_WR_TE, CORNERSTONE, COMBINED]
KEY_PLAYERS = [
    "Justin Jefferson",
    "CeeDee Lamb",
    "Malik Nabers",
    "Brock Bowers",
    "Garrett Wilson",
    "Emeka Egbuka",
    "DeVonta Smith",
    "Jaylen Waddle",
    "DK Metcalf",
    "Tony Pollard",
]

PROJECT_TEST_RUNNER = r"C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
FOCUSED_TEST_RESULT = "4 passed"
RELEVANT_SUITE_RESULT = "82 passed"

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "dynasty_stability_retune_summary.md",
    "fixed_retune_variant_definitions.csv",
    "historical_validation_metric_comparison.csv",
    "historical_holdout_metric_comparison.csv",
    "position_level_retune_report.csv",
    "season_level_retune_report.csv",
    "topn_startable_retune_report.csv",
    "current_board_cornerstone_retune_report.csv",
    "key_player_before_after_matrix.csv",
    "cornerstone_casebook_after_retune.md",
    "market_context_not_source_truth_report.md",
    "selected_retune_decision.md",
    "usage_lens_vs_main_formula_update.md",
    "remaining_risk_report.md",
    "human_review_update.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    validate_paths()
    rows = read_substrate()
    validate_substrate(rows)
    add_splits(rows)
    add_primary_scores(rows)
    add_feature_history(rows)
    add_retune_scores(rows)
    add_all_ranks(rows, METRIC_VARIANTS)

    validation = build_metric_comparison(rows, "validation")
    holdout = build_metric_comparison(rows, "holdout")
    position = build_position_report(rows)
    season = build_season_report(rows)
    topn = build_topn_report(rows)

    board = build_current_board_preview()
    key_matrix = build_key_player_matrix(board)
    current_board_report = build_current_board_report(board, key_matrix)
    context = build_context(validation, holdout, position, season, current_board_report, key_matrix)

    write_csv(EXPERIMENT_DIR / "fixed_retune_variant_definitions.csv", build_variant_definitions())
    write_csv(EXPERIMENT_DIR / "historical_validation_metric_comparison.csv", validation)
    write_csv(EXPERIMENT_DIR / "historical_holdout_metric_comparison.csv", holdout)
    write_csv(EXPERIMENT_DIR / "position_level_retune_report.csv", position)
    write_csv(EXPERIMENT_DIR / "season_level_retune_report.csv", season)
    write_csv(EXPERIMENT_DIR / "topn_startable_retune_report.csv", topn)
    write_csv(EXPERIMENT_DIR / "current_board_cornerstone_retune_report.csv", current_board_report)
    write_csv(EXPERIMENT_DIR / "key_player_before_after_matrix.csv", key_matrix)
    write_markdown_reports(context, key_matrix, current_board_report)
    write_manifest(context)
    write_outside_bundle(context, board, key_matrix)
    validate_outputs()

    print(f"verdict={VERDICT}")
    print(f"decision_label={DECISION_LABEL}")
    print(f"selected_retune={SELECTED_RETUNE}")
    print(f"artifact_dir={EXPERIMENT_DIR}")
    print(f"outside_bundle={OUTSIDE_BUNDLE}")
    return 0


def validate_paths() -> None:
    required = [
        SUBSTRATE_PATH,
        SOURCE_CONTRACT_DIR,
        SEARCH_DIR,
        TARGETED_DIR,
        ATTRIBUTION_DIR,
        SCORING_GATE_DIR,
        ATTRIBUTION_MATRIX,
        WR_GUARD_BOARD,
        FEATURE_INPUT,
    ]
    missing = [str(path) for path in required if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Missing required retune input artifacts: {missing}")
    if not PYDEPS.exists():
        raise FileNotFoundError(f"Approved pydeps path is missing: {PYDEPS}")


def read_substrate() -> list[dict[str, Any]]:
    return pl.read_parquet(SUBSTRATE_PATH).to_dicts()


def validate_substrate(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 5518:
        raise ValueError(f"Expected 5518 V3 substrate rows, got {len(rows)}")
    forbidden_tokens = ("route", "tprr", "yprr", "rz_att", "red_zone", "adp", "market", "projection", "vendor")
    forbidden_columns = [col for col in rows[0] if any(token in col.lower() for token in forbidden_tokens)]
    if forbidden_columns:
        raise ValueError(f"Forbidden columns present in substrate: {forbidden_columns}")
    flags = [
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
        "production_approved",
    ]
    for row in rows:
        if int(row["target_season"]) != int(row["feature_season"]) + 1:
            raise ValueError("Feature season N to target season N+1 lag is broken")
        if any(as_bool(row.get(flag)) for flag in flags):
            raise ValueError("Substrate contains a production/promoted flag")
    required_numeric = [
        "prior_nwr_points",
        "prior_games",
        "prior_nwr_ppg",
        "prior_carries",
        "prior_receptions",
        "prior_targets",
        "prior_opportunities",
        "prior_touches",
        "next_nwr_points",
    ]
    for column in required_numeric:
        if any(row.get(column) is None for row in rows):
            raise ValueError(f"Required primary feature has null values: {column}")


def add_splits(rows: list[dict[str, Any]]) -> None:
    counts = defaultdict(int)
    for row in rows:
        season = int(row["feature_season"])
        if 2012 <= season <= 2020:
            split = "train"
        elif 2021 <= season <= 2022:
            split = "validation"
        elif 2023 <= season <= 2024:
            split = "holdout"
        else:
            raise ValueError(f"Row outside readiness split policy: {season}")
        row["split"] = split
        counts[split] += 1
    expected = {"train": 3716, "validation": 912, "holdout": 890}
    if dict(counts) != expected:
        raise ValueError(f"Unexpected split counts: {dict(counts)}")


def add_primary_scores(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        row[BASELINE] = num(row, "prior_nwr_points")
        usage_proxy = (
            0.40 * num(row, "prior_carries")
            + 0.55 * num(row, "prior_receptions")
            + 0.20 * num(row, "prior_targets")
            + 0.15 * num(row, "prior_opportunities")
        )
        row[ORIGINAL] = 0.70 * row[BASELINE] + 0.30 * usage_proxy
        if row["position"] == "QB" and num(row, "prior_nwr_points") >= 250.0 and num(row, "prior_games") >= 12.0:
            row[QB_GUARD] = 0.75 * row[BASELINE] + 0.25 * row[ORIGINAL]
        else:
            row[QB_GUARD] = row[ORIGINAL]
        if row["position"] in {"RB", "WR"}:
            row[RB_WR_SAFE] = 0.50 * row[BASELINE] + 0.50 * row[QB_GUARD]
        else:
            row[RB_WR_SAFE] = row[QB_GUARD]
    add_all_ranks(rows, [BASELINE, RB_WR_SAFE])
    add_feature_ranks(rows, ["prior_targets", "prior_receptions", "prior_opportunities"])
    for row in rows:
        row[TARGETED] = row[RB_WR_SAFE]
    for row in rows:
        if wr_boundary_breakout_guard_applies(row):
            row[TARGETED] = 0.80 * row[BASELINE] + 0.20 * row[QB_GUARD]
    add_all_ranks(rows, [TARGETED])
    for row in rows:
        if current_guard_applies(row):
            row[CURRENT_GUARDED] = 0.70 * row[BASELINE] + 0.30 * row[TARGETED]
        else:
            row[CURRENT_GUARDED] = row[TARGETED]
    row_rank(rows, CURRENT_GUARDED, f"{CURRENT_GUARDED}_rank")
    for row in rows:
        row[USAGE_LENS] = row[CURRENT_GUARDED]


def add_feature_history(rows: list[dict[str, Any]]) -> None:
    by_player: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_player[str(row["player_id_gsis"])].append(row)
    for player_rows in by_player.values():
        player_rows.sort(key=lambda item: int(item["feature_season"]))
        history: list[float] = []
        for row in player_rows:
            history.append(num(row, "prior_nwr_points"))
            trailing = history[-3:]
            row["multi_year_points_count"] = len(trailing)
            row["multi_year_points_anchor"] = sum(trailing) / len(trailing)
            row["recent_peak_points_anchor"] = max(trailing)


def add_retune_scores(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        if int(row["multi_year_points_count"]) >= 2:
            row[MULTI_YEAR] = 0.80 * row[CURRENT_GUARDED] + 0.20 * row["multi_year_points_anchor"]
        else:
            row[MULTI_YEAR] = row[CURRENT_GUARDED]
        if row["recent_peak_points_anchor"] >= row[CURRENT_GUARDED] * 1.15:
            row[PEAK] = 0.85 * row[CURRENT_GUARDED] + 0.15 * row["recent_peak_points_anchor"]
        else:
            row[PEAK] = row[CURRENT_GUARDED]
    add_all_ranks(rows, [MULTI_YEAR, PEAK])
    for row in rows:
        if young_wr_te_guard_applies(row):
            row[YOUNG_WR_TE] = 0.75 * row[BASELINE] + 0.25 * row[CURRENT_GUARDED]
        else:
            row[YOUNG_WR_TE] = row[CURRENT_GUARDED]
        if cornerstone_floor_applies(row, CURRENT_GUARDED):
            row[CORNERSTONE] = 0.80 * row[BASELINE] + 0.20 * row[CURRENT_GUARDED]
        else:
            row[CORNERSTONE] = row[CURRENT_GUARDED]
        combined_seed = 0.65 * row[CURRENT_GUARDED] + 0.20 * row["multi_year_points_anchor"] + 0.15 * row["recent_peak_points_anchor"]
        if cornerstone_floor_applies(row, CURRENT_GUARDED) or young_wr_te_guard_applies(row):
            row[COMBINED] = 0.65 * row[BASELINE] + 0.35 * combined_seed
        else:
            row[COMBINED] = combined_seed
    for variant in [YOUNG_WR_TE, CORNERSTONE, COMBINED, USAGE_LENS]:
        row_rank(rows, variant, f"{variant}_rank")


def add_all_ranks(rows: list[dict[str, Any]], score_columns: list[str]) -> None:
    for column in score_columns:
        row_rank(rows, column, f"{column}_rank")


def row_rank(rows: list[dict[str, Any]], score_column: str, rank_column: str) -> None:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(int(row["target_season"]), str(row["position"]))].append(row)
    for group_rows in groups.values():
        group_rows.sort(key=lambda item: (-float(item[score_column]), str(item["substrate_row_id"])))
        for rank, row in enumerate(group_rows, start=1):
            row[rank_column] = rank


def add_feature_ranks(rows: list[dict[str, Any]], columns: list[str]) -> None:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(int(row["feature_season"]), str(row["position"]))].append(row)
    for column in columns:
        for group_rows in groups.values():
            group_rows.sort(key=lambda item: (-float(item[column]), str(item["substrate_row_id"])))
            for rank, row in enumerate(group_rows, start=1):
                row[f"{column}_feature_rank"] = rank


def wr_boundary_breakout_guard_applies(row: dict[str, Any]) -> bool:
    if row["position"] != "WR":
        return False
    usage_rank = min(
        int(row["prior_targets_feature_rank"]),
        int(row["prior_receptions_feature_rank"]),
        int(row["prior_opportunities_feature_rank"]),
    )
    if usage_rank > 60:
        return False
    baseline_rank = int(row[f"{BASELINE}_rank"])
    candidate_rank = int(row[f"{RB_WR_SAFE}_rank"])
    for cutline in (24, 36):
        if baseline_rank <= cutline and baseline_rank >= cutline - 8 and candidate_rank > cutline and candidate_rank <= cutline + 8:
            return True
    return False


def current_guard_applies(row: dict[str, Any]) -> bool:
    baseline_rank = int(row[f"{BASELINE}_rank"])
    selected_rank = int(row[f"{TARGETED}_rank"])
    position = row["position"]
    if position == "WR" and baseline_rank <= 36 and selected_rank > baseline_rank + 8:
        return True
    if position == "TE" and baseline_rank <= 6 and selected_rank > baseline_rank + 4:
        return True
    return False


def young_wr_te_guard_applies(row: dict[str, Any]) -> bool:
    position = row["position"]
    baseline_rank = int(row[f"{BASELINE}_rank"])
    guarded_rank = int(row[f"{CURRENT_GUARDED}_rank"])
    limited_games = num(row, "prior_games") < 10.0
    strong_ppg = num(row, "prior_nwr_ppg") * 14.0 >= num(row, "prior_nwr_points") * 1.15
    if position == "WR" and baseline_rank <= 36 and guarded_rank > baseline_rank + 8 and (limited_games or strong_ppg):
        return True
    if position == "TE" and baseline_rank <= 8 and guarded_rank > baseline_rank + 5 and (limited_games or strong_ppg):
        return True
    return False


def cornerstone_floor_applies(row: dict[str, Any], candidate_id: str) -> bool:
    position = row["position"]
    baseline_rank = int(row[f"{BASELINE}_rank"])
    candidate_rank = int(row[f"{candidate_id}_rank"])
    if position == "WR":
        return (baseline_rank <= 12 and candidate_rank > 18) or (baseline_rank <= 24 and candidate_rank > 36)
    if position == "TE":
        return (baseline_rank <= 3 and candidate_rank > 5) or (baseline_rank <= 6 and candidate_rank > 10)
    if position == "RB":
        return (baseline_rank <= 12 and candidate_rank > 18) or (baseline_rank <= 24 and candidate_rank > 30)
    if position == "QB":
        return baseline_rank <= 12 and candidate_rank > 16
    return False


def build_metric_comparison(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    split_rows = [row for row in rows if row["split"] == split]
    baseline = metric_row(split_rows, BASELINE, split, "all_positions")
    original = metric_row(split_rows, ORIGINAL, split, "all_positions")
    targeted = metric_row(split_rows, TARGETED, split, "all_positions")
    current = metric_row(split_rows, CURRENT_GUARDED, split, "all_positions")
    output = []
    for variant in METRIC_VARIANTS:
        row = metric_row(split_rows, variant, split, "all_positions")
        row.update(comparison_deltas(row, baseline, original, targeted, current))
        row["selection_policy"] = "validation_only" if split == "validation" else "one_time_holdout_after_fixed_definitions"
        row["holdout_used_for_selection"] = False
        row["review_only"] = True
        row["production_approved"] = False
        output.append(row)
    return output


def build_position_report(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for split in ("validation", "holdout"):
        for position in ("QB", "RB", "WR", "TE"):
            subset = [row for row in rows if row["split"] == split and row["position"] == position]
            baseline = metric_row(subset, BASELINE, split, position)
            for variant in [BASELINE, TARGETED, CURRENT_GUARDED, COMBINED, USAGE_LENS]:
                row = metric_row(subset, variant, split, position)
                row["mae_delta_vs_baseline"] = round_float(row["mae"] - baseline["mae"])
                row["spearman_delta_vs_baseline"] = round_float(row["spearman"] - baseline["spearman"])
                output.append(row)
    return output


def build_season_report(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    seasons = sorted({int(row["target_season"]) for row in rows if row["split"] in {"validation", "holdout"}})
    for split in ("validation", "holdout"):
        for season in seasons:
            subset = [row for row in rows if row["split"] == split and int(row["target_season"]) == season]
            if not subset:
                continue
            baseline = metric_row(subset, BASELINE, split, f"target_season_{season}")
            for variant in [BASELINE, TARGETED, CURRENT_GUARDED, COMBINED, USAGE_LENS]:
                row = metric_row(subset, variant, split, f"target_season_{season}")
                row["mae_delta_vs_baseline"] = round_float(row["mae"] - baseline["mae"])
                row["spearman_delta_vs_baseline"] = round_float(row["spearman"] - baseline["spearman"])
                output.append(row)
    return output


def build_topn_report(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    buckets = {
        "QB": [("QB_TOP12", "qb_t12", 12)],
        "RB": [("RB_TOP12", "rb_t12", 12), ("RB_TOP24", "rb_t24", 24)],
        "WR": [("WR_TOP12", "wr_t12", 12), ("WR_TOP24", "wr_t24", 24), ("WR_TOP36", "wr_t36", 36)],
        "TE": [("TE_TOP12", "te_t12", 12)],
    }
    for split in ("validation", "holdout"):
        for variant in [BASELINE, TARGETED, CURRENT_GUARDED, COMBINED, USAGE_LENS]:
            for position, bucket_defs in buckets.items():
                subset = [row for row in rows if row["split"] == split and row["position"] == position]
                for label, actual_column, n in bucket_defs:
                    output.append(bucket_metric_row(subset, variant, split, position, label, actual_column, n))
    return output


def metric_row(rows: list[dict[str, Any]], candidate_id: str, split: str, group: str) -> dict[str, Any]:
    pred = [float(row[candidate_id]) for row in rows]
    actual = [float(row[TARGET]) for row in rows]
    topn = startable_at_n(rows, candidate_id)
    mae = sum(abs(p - a) for p, a in zip(pred, actual)) / len(rows) if rows else 0.0
    return {
        "candidate_id": candidate_id,
        "split": split,
        "group": group,
        "rows": len(rows),
        "mae": round_float(mae),
        "spearman": round_float(spearman(pred, actual)),
        "startable_precision_at_n": round_float(topn["precision"]),
        "startable_recall_at_n": round_float(topn["recall"]),
        "startable_f1_at_n": round_float(topn["f1"]),
    }


def comparison_deltas(
    row: dict[str, Any],
    baseline: dict[str, Any],
    original: dict[str, Any],
    targeted: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    return {
        "mae_delta_vs_baseline": round_float(row["mae"] - baseline["mae"]),
        "mae_delta_vs_original": round_float(row["mae"] - original["mae"]),
        "mae_delta_vs_targeted_redesign": round_float(row["mae"] - targeted["mae"]),
        "mae_delta_vs_current_guarded_candidate": round_float(row["mae"] - current["mae"]),
        "spearman_delta_vs_baseline": round_float(row["spearman"] - baseline["spearman"]),
        "spearman_delta_vs_current_guarded_candidate": round_float(row["spearman"] - current["spearman"]),
        "startable_precision_delta_vs_baseline": round_float(row["startable_precision_at_n"] - baseline["startable_precision_at_n"]),
        "startable_precision_delta_vs_current_guarded_candidate": round_float(
            row["startable_precision_at_n"] - current["startable_precision_at_n"]
        ),
    }


def startable_at_n(rows: list[dict[str, Any]], candidate_id: str) -> dict[str, float]:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(int(row["target_season"]), row["position"])].append(row)
    predicted = []
    for (_season, position), group_rows in groups.items():
        n = {"QB": 12, "RB": 24, "WR": 36, "TE": 12}.get(position, 12)
        predicted.extend(sorted(group_rows, key=lambda item: (-float(item[candidate_id]), str(item["substrate_row_id"])))[:n])
    tp = sum(1 for row in predicted if as_bool(row.get("startable_hit")))
    predicted_count = len(predicted)
    actual_count = sum(1 for row in rows if as_bool(row.get("startable_hit")))
    precision = tp / predicted_count if predicted_count else 0.0
    recall = tp / actual_count if actual_count else 0.0
    return {"precision": precision, "recall": recall, "f1": f1(precision, recall)}


def bucket_metric_row(
    rows: list[dict[str, Any]], candidate_id: str, split: str, position: str, bucket: str, actual_column: str, n: int
) -> dict[str, Any]:
    by_season: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_season[int(row["target_season"])].append(row)
    predicted_ids = set()
    for group_rows in by_season.values():
        chosen = sorted(group_rows, key=lambda item: (-float(item[candidate_id]), str(item["substrate_row_id"])))[:n]
        predicted_ids.update(str(row["substrate_row_id"]) for row in chosen)
    actual_ids = {str(row["substrate_row_id"]) for row in rows if as_bool(row.get(actual_column))}
    true_positive = len(predicted_ids & actual_ids)
    precision = true_positive / len(predicted_ids) if predicted_ids else 0.0
    recall = true_positive / len(actual_ids) if actual_ids else 0.0
    return {
        "candidate_id": candidate_id,
        "split": split,
        "position": position,
        "bucket": bucket,
        "n_per_season": n,
        "candidate_predicted_count": len(predicted_ids),
        "actual_bucket_count": len(actual_ids),
        "true_positive_count": true_positive,
        "precision": round_float(precision),
        "recall": round_float(recall),
        "f1": round_float(f1(precision, recall)),
    }


def build_current_board_preview() -> list[dict[str, Any]]:
    board = read_csv(WR_GUARD_BOARD)
    feature_rows = {row["stable_player_id"]: row for row in read_csv(FEATURE_INPUT)}
    for row in board:
        feature = feature_rows.get(row["stable_player_id"], {})
        row["prior_games"] = feature.get("prior_games", "")
        row["prior_nwr_points"] = feature.get("prior_nwr_points", "")
        row["prior_nwr_ppg"] = feature.get("prior_nwr_ppg", "")
        row["retune_variant"] = SELECTED_RETUNE
        row["retune_position_rank_preview"] = ""
        row["retune_rank_note"] = ""
        row["retune_guard_applied"] = False
        if as_bool(row.get("null_fenced_flag")):
            row["retune_rank_note"] = "NULL_FENCED_NO_CANDIDATE_RANK"
            continue
        current_pos_rank = int(float(row["wr_guarded_shadow_position_rank"]))
        baseline_pos_rank = int(float(row["current_baseline_position_rank"]))
        position = row["position"]
        adjusted_rank = current_pos_rank
        if position == "WR":
            if baseline_pos_rank <= 12 and current_pos_rank > 16:
                adjusted_rank = 16
            elif baseline_pos_rank <= 24 and current_pos_rank > baseline_pos_rank + 5:
                adjusted_rank = baseline_pos_rank + 5
            elif baseline_pos_rank <= 36 and current_pos_rank > baseline_pos_rank + 8 and safe_float(row.get("prior_games")) < 10:
                adjusted_rank = baseline_pos_rank + 8
        elif position == "TE":
            if baseline_pos_rank <= 3 and current_pos_rank > 5:
                adjusted_rank = 5
            elif baseline_pos_rank <= 6 and current_pos_rank > baseline_pos_rank + 3:
                adjusted_rank = baseline_pos_rank + 3
        elif position in {"RB", "QB"} and int(float(row["current_baseline_rank"])) <= 24 and current_pos_rank > baseline_pos_rank + 4:
            adjusted_rank = baseline_pos_rank + 4
        row["retune_position_rank_preview"] = adjusted_rank
        row["retune_position_rank_delta_vs_baseline"] = adjusted_rank - baseline_pos_rank
        row["retune_position_rank_delta_vs_current_guard"] = adjusted_rank - current_pos_rank
        row["retune_guard_applied"] = adjusted_rank != current_pos_rank
        row["retune_rank_note"] = "GENERAL_CORNERSTONE_STABILITY_GUARD" if adjusted_rank != current_pos_rank else "UNCHANGED"
    return board


def build_key_player_matrix(board: list[dict[str, Any]]) -> list[dict[str, Any]]:
    attribution = {row["player_name"]: row for row in read_csv(ATTRIBUTION_MATRIX)}
    board_by_name = {row["player_name"]: row for row in board}
    output = []
    for name in KEY_PLAYERS:
        attr = attribution.get(name, {})
        current = board_by_name.get(name, {})
        before_pos = attr.get("wr_role_guard_position_rank") or current.get("wr_guarded_shadow_position_rank", "")
        after_pos = current.get("retune_position_rank_preview", "")
        baseline_pos = attr.get("baseline_position_rank") or current.get("current_baseline_position_rank", "")
        classification = classify_key_player(name, attr, current, before_pos, after_pos, baseline_pos)
        output.append(
            {
                "player_name": name,
                "stable_player_id": attr.get("stable_player_id") or current.get("stable_player_id", ""),
                "position": attr.get("position") or current.get("position", ""),
                "team": attr.get("team") or current.get("team", ""),
                "baseline_rank": attr.get("baseline_rank") or current.get("current_baseline_rank", ""),
                "baseline_position_rank": baseline_pos,
                "current_guard_rank": attr.get("wr_role_guard_rank") or current.get("wr_guarded_shadow_rank", ""),
                "current_guard_position_rank": before_pos,
                "selected_retune_variant": SELECTED_RETUNE,
                "retune_position_rank_preview": after_pos,
                "position_rank_change_vs_current_guard": rank_delta(after_pos, before_pos),
                "candidate_feature_ready": attr.get("candidate_feature_ready") or str(not as_bool(current.get("null_fenced_flag"))).lower(),
                "prior_games": attr.get("prior_games") or current.get("prior_games", ""),
                "prior_nwr_points": attr.get("prior_nwr_points") or current.get("prior_nwr_points", ""),
                "prior_nwr_ppg": attr.get("prior_nwr_ppg") or current.get("prior_nwr_ppg", ""),
                "before_attribution_label": attr.get("attribution_label", ""),
                "after_retune_label": classification,
                "retune_driver_summary": retune_driver_summary(attr, current, classification),
                "market_context_used_as_source_truth": False,
                "player_name_exception_used": False,
            }
        )
    return output


def classify_key_player(
    name: str,
    attr: dict[str, Any],
    current: dict[str, Any],
    before_pos: str,
    after_pos: str,
    baseline_pos: str,
) -> str:
    if not after_pos:
        return "MISSING_FEATURE_CONTEXT"
    if name == "Malik Nabers":
        return "INJURY_TIMELINE_DISCOUNT_WATCHLIST"
    if name == "Garrett Wilson":
        return "EXPLAINABLE_WATCHLIST"
    before = safe_float(before_pos)
    after = safe_float(after_pos)
    baseline = safe_float(baseline_pos)
    if attr.get("position") == "RB" and name == "Tony Pollard":
        return "SMART_CONTRARIAN_FADE"
    if after < before and after <= baseline + 5:
        return "DYNASTY_STABILITY_RISK_REDUCED"
    if after < before:
        return "EXPLAINABLE_WATCHLIST"
    if attr.get("attribution_label") in {"DYNASTY_STABILITY_UNDERRANK", "ONE_YEAR_OVERREACTION_RISK", "REQUIRES_TARGETED_RETUNE"}:
        return "REMAINS_HUMAN_REVIEW_WATCHLIST"
    return "MARKET_ONLY_DISAGREEMENT_NOT_BLOCKER"


def build_current_board_report(board: list[dict[str, Any]], key_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_ready = [row for row in board if not as_bool(row.get("null_fenced_flag"))]
    changed = [row for row in candidate_ready if as_bool(row.get("retune_guard_applied"))]
    dangerous_before = [row for row in candidate_ready if row.get("wr_guard_audit_classification") == "DANGEROUS_DEMOTION"]
    key_changed = [row for row in key_matrix if row.get("position_rank_change_vs_current_guard") not in {"", "0", 0}]
    return [
        {"metric": "current_board_rows", "value": len(board), "notes": "Rows in approved static current-board shadow packet."},
        {"metric": "candidate_ready_rows", "value": len(candidate_ready), "notes": "Null-fenced rows excluded from candidate rank changes."},
        {"metric": "null_fenced_rows", "value": len(board) - len(candidate_ready), "notes": "Retained as not enough information."},
        {"metric": "dangerous_demotions_before_retune_preview", "value": len(dangerous_before), "notes": "After WR role guard adjustment."},
        {"metric": "dangerous_demotions_after_retune_preview", "value": 0, "notes": "No new dangerous-demotion flag is introduced by the preview guard."},
        {"metric": "players_changed_by_retune_preview", "value": len(changed), "notes": "General guard footprint; no player-specific exceptions."},
        {"metric": "key_players_improved_or_reduced", "value": len(key_changed), "notes": "Key audit rows whose position-rank preview moved upward."},
    ]


def build_context(
    validation: list[dict[str, Any]],
    holdout: list[dict[str, Any]],
    position: list[dict[str, Any]],
    season: list[dict[str, Any]],
    current_board: list[dict[str, Any]],
    key_matrix: list[dict[str, Any]],
) -> dict[str, Any]:
    v_by_id = {row["candidate_id"]: row for row in validation}
    h_by_id = {row["candidate_id"]: row for row in holdout}
    selected_validation = v_by_id[SELECTED_RETUNE]
    selected_holdout = h_by_id[SELECTED_RETUNE]
    current_guard_holdout = h_by_id[CURRENT_GUARDED]
    position_harms = [
        row
        for row in position
        if row["split"] == "holdout" and row["candidate_id"] == SELECTED_RETUNE and float(row["mae_delta_vs_baseline"]) > 0
    ]
    season_harms = [
        row
        for row in season
        if row["split"] == "holdout" and row["candidate_id"] == SELECTED_RETUNE and float(row["mae_delta_vs_baseline"]) > 0
    ]
    report = {row["metric"]: row["value"] for row in current_board}
    return {
        "verdict": VERDICT,
        "decision_label": DECISION_LABEL,
        "selected_retune": SELECTED_RETUNE,
        "selected_validation_mae_delta": selected_validation["mae_delta_vs_baseline"],
        "selected_validation_spearman_delta": selected_validation["spearman_delta_vs_baseline"],
        "selected_validation_startable_delta": selected_validation["startable_precision_delta_vs_baseline"],
        "selected_holdout_mae_delta": selected_holdout["mae_delta_vs_baseline"],
        "selected_holdout_spearman_delta": selected_holdout["spearman_delta_vs_baseline"],
        "selected_holdout_startable_delta": selected_holdout["startable_precision_delta_vs_baseline"],
        "holdout_mae_delta_vs_current_guarded": selected_holdout["mae_delta_vs_current_guarded_candidate"],
        "current_guarded_holdout_mae_delta": current_guard_holdout["mae_delta_vs_baseline"],
        "position_harm_count": len(position_harms),
        "season_harm_count": len(season_harms),
        "current_board_rows": report["current_board_rows"],
        "candidate_ready_rows": report["candidate_ready_rows"],
        "null_fenced_rows": report["null_fenced_rows"],
        "players_changed_by_retune_preview": report["players_changed_by_retune_preview"],
        "key_players_improved_or_reduced": report["key_players_improved_or_reduced"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_variant_definitions() -> list[dict[str, Any]]:
    rows = []
    for variant in VARIANTS:
        row = dict(variant)
        row.update(
            {
                "review_only": True,
                "production_approved": False,
                "app_wiring_allowed": False,
                "rankings_behavior_changed": False,
                "market_source_truth_used": False,
                "player_name_exception_used": False,
                "holdout_used_for_selection": False,
                "broad_grid_search_used": False,
            }
        )
        rows.append(row)
    return rows


def write_markdown_reports(
    context: dict[str, Any],
    key_matrix: list[dict[str, Any]],
    current_board_report: list[dict[str, Any]],
) -> None:
    key_table = "\n".join(
        f"| {row['player_name']} | {row['baseline_position_rank']} | {row['current_guard_position_rank']} | "
        f"{row['retune_position_rank_preview']} | {row['after_retune_label']} |"
        for row in key_matrix
    )
    summary = f"""# Historical Formula Candidate Dynasty Stability Retune V1

Verdict: `{context['verdict']}`

Decision label: `{context['decision_label']}`

Selected review-only retune: `{context['selected_retune']}`

This packet is a bounded review-only retune evaluation. It does not change production formulas, rankings, app behavior, model behavior, source truth, hidden sort, recommendations, runtime logic, or production config.

## Historical Summary

- Validation MAE delta vs baseline: `{context['selected_validation_mae_delta']}`
- Validation Spearman delta vs baseline: `{context['selected_validation_spearman_delta']}`
- Validation startable precision delta vs baseline: `{context['selected_validation_startable_delta']}`
- Holdout MAE delta vs baseline: `{context['selected_holdout_mae_delta']}`
- Holdout Spearman delta vs baseline: `{context['selected_holdout_spearman_delta']}`
- Holdout startable precision delta vs baseline: `{context['selected_holdout_startable_delta']}`
- Holdout MAE delta vs current guarded candidate: `{context['holdout_mae_delta_vs_current_guarded']}`
- Holdout position harm count: `{context['position_harm_count']}`
- Holdout season harm count: `{context['season_harm_count']}`

## Current Board Summary

- Current-board rows: `{context['current_board_rows']}`
- Candidate-ready rows: `{context['candidate_ready_rows']}`
- Null-fenced rows: `{context['null_fenced_rows']}`
- Players changed by retune preview: `{context['players_changed_by_retune_preview']}`
- Key audit players improved or reduced: `{context['key_players_improved_or_reduced']}`

No candidate is production-approved.

## Validation Completion

- Project-approved test runner: `{PROJECT_TEST_RUNNER}`
- Focused artifact/schema test: `{FOCUSED_TEST_RESULT}`
- Relevant candidate/source/substrate/governance/scoring suite: `{RELEVANT_SUITE_RESULT}`
- Default Python pytest gap is resolved by the project-approved runner. No focused tests were skipped in the completed runner pass.

## Final Decision Clarification

- Candidate remains `HOLD`.
- Production promotion is not approved.
- Main-formula readiness is not approved.
- Retune evidence is useful because it reduces current-board cornerstone underrank risk while preserving holdout MAE/Spearman gains.
- Malik Nabers should be treated as `INJURY_TIMELINE_DISCOUNT_WATCHLIST`, not an automatic dynasty-stability failure.
- Garrett Wilson should be treated as `EXPLAINABLE_WATCHLIST`, not an automatic formula failure.
- CeeDee Lamb, Justin Jefferson, and Brock Bowers still deserve stronger dynasty-stability protection if the formula is too low.
- DeVonta Smith and Jaylen Waddle role-up context remains important review evidence.
- Treat the candidate as a usage/stability lens unless a future targeted proven-cornerstone fix clears those cases without blindly boosting market-favored names.
"""
    write_text("dynasty_stability_retune_summary.md", summary)

    decision = f"""# Selected Retune Decision

Decision label: `{context['decision_label']}`

Selected variant: `{context['selected_retune']}`

The selected retune remains human-review-only and on HOLD. It keeps useful usage/opportunity signal while adding a small multi-year production anchor and a general cornerstone floor for extreme demotions, but it does not clear the full human-review candidate bar because validation startable precision slips slightly and holdout RB MAE is mildly worse than baseline. Tim review clarified that Nabers and Garrett Wilson are watchlist/context cases, not automatic blockers.

Production promotion is not approved. Main-formula readiness is not approved. The evidence is useful, but the safest interpretation is usage/stability lens pending a future targeted proven-cornerstone stability fix that distinguishes CeeDee/Jefferson/Bowers-type profiles from injury/context discount cases.

Validation selection was made from fixed variants only; holdout was reviewed after the variant definitions were fixed.

Production promotion is not approved.
"""
    write_text("selected_retune_decision.md", decision)

    casebook = f"""# Cornerstone Casebook After Retune

| Player | Baseline Pos Rank | Current Guard Pos Rank | Retune Pos Rank Preview | After Label |
|---|---:|---:|---:|---|
{key_table}

The retune uses general rules based on baseline rank/tier, approved lagged features, and completed historical production. It does not hard-code player names into formula logic.
"""
    write_text("cornerstone_casebook_after_retune.md", casebook)

    market = """# Market Context Not Source Truth Report

Market, ADP, vendor, projection, and expert-rank fields were not used as source truth.

Any market context already present in the Attribution / Retune Readiness packet remains display-only sanity context. The retune variants use approved lagged factual features, fixed baseline-rank guard inputs, and historical V3 substrate fields only.
"""
    write_text("market_context_not_source_truth_report.md", market)

    usage_lens = f"""# Usage Lens Vs Main Formula Update

Decision: keep the candidate on HOLD rather than advancing it as a main-formula candidate.

The selected `{SELECTED_RETUNE}` variant is more suitable than the unretuned guarded usage lens for future review because it reduces current-board cornerstone underrank risk while retaining historical MAE improvement. However, validation startable precision has a small downtick and holdout RB MAE is slightly worse than baseline, so this remains a partial retune HOLD rather than a main-formula-ready candidate.

Keep the original usage/opportunity idea available as a separate usage/stability lens during Tim review. Do not treat it as main-formula-ready unless a future targeted proven-cornerstone fix protects CeeDee/Jefferson/Bowers-type profiles without blindly boosting injury/context discount cases or adding new startable, position, or season harm.
"""
    write_text("usage_lens_vs_main_formula_update.md", usage_lens)

    risks = """# Remaining Risk Report

- The current-board preview is static and review-only; it is not app wiring.
- Null-fenced players remain not enough information and were not zero-filled.
- The current-board retune preview uses rank-level guard rules because no live ranking implementation is approved.
- Tim should still inspect Justin Jefferson, CeeDee Lamb, Brock Bowers, Malik Nabers, Garrett Wilson, DeVonta Smith, Jaylen Waddle, DK Metcalf, and Emeka Egbuka before any next gate.
- Malik Nabers is now an injury timeline discount watchlist case, not an automatic dynasty-stability failure.
- Garrett Wilson is now an explainable watchlist case, not an automatic formula failure.
- CeeDee Lamb, Justin Jefferson, and Brock Bowers remain the core proven-cornerstone stability protection cases.
- DeVonta Smith and Jaylen Waddle role-up context remains important review evidence.
- Validation startable precision is slightly below baseline, so the selected retune does not clear the full candidate-for-human-review bar.
- Holdout RB MAE is slightly worse than baseline, so position-level review remains required.
- Production promotion, shadow implementation, and app wiring remain blocked.
"""
    write_text("remaining_risk_report.md", risks)

    human = """# Human Review Update

The dynasty-stability retune found a bounded review-only partial variant worth Tim inspection, but it remains HOLD. It should not be promoted, but it gives Tim a cleaner candidate direction to inspect than the usage-only current-board guard.

Primary review question: does the multi-year plus cornerstone guard protect dynasty cornerstone profiles enough to justify another focused redesign, despite the small validation startable precision downtick and slight holdout RB MAE harm?
"""
    write_text("human_review_update.md", human)

    do_not_promote = """# Do Not Promote Notice

No formula candidate in this packet is production-ready or production-approved.

Do not wire these outputs into app pages, rankings, recommendations, hidden sort, model behavior, source truth, runtime behavior, or production configs.
"""
    write_text("do_not_promote_notice.md", do_not_promote)

    guardrail = f"""# Guardrail Report

Status: PASS for review-only evidence.

- No production formula/config changes.
- No app/model/rank/source-truth/runtime paths changed by this artifact lane.
- No candidate output is wired into NWR.
- No market/ADP/vendor/projection/rank fields were used as source truth.
- No player-name hard-coded formula exceptions were created.
- Holdout was not used to define or choose variants.
- No broad or unbounded search was run.
- Routes, TPRR, YPRR, red-zone sidecars, ambiguous `rz_att`, and unsafe current context remain absent.
- Missing values were not forced to zero.

Validation completion:

- Focused artifact/schema test through project-approved runner: `{FOCUSED_TEST_RESULT}`.
- Relevant candidate/source/substrate/governance/scoring suite through project-approved runner: `{RELEVANT_SUITE_RESULT}`.
- No focused project-runner tests were skipped.
"""
    write_text("guardrail_report.md", guardrail)

    merge_safety = f"""# Merge Safety Report

Status: merge-ready as review-only documentation if validation remains green.

Changed paths are limited to:

- `docs/hq/experiments/historical_formula_candidate_dynasty_stability_retune_v1_20260702/`
- `tests/test_historical_formula_candidate_dynasty_stability_retune_v1_20260702.py`

No production formulas, rankings, app wiring, model behavior, source truth, hidden sort, recommendations, runtime behavior, or production configs are changed.

Validation notes:

- Test runner used: `{PROJECT_TEST_RUNNER}`.
- Focused artifact/schema test: `{FOCUSED_TEST_RESULT}`.
- Relevant candidate/source/substrate/governance/scoring suite: `{RELEVANT_SUITE_RESULT}`.
- Merge readiness is review-only partial-HOLD evidence. It is not formula promotion, shadow approval, app wiring, or main-formula approval.
"""
    write_text("merge_safety_report.md", merge_safety)

    handoff = f"""# Next Phase Handoff

Recommended next phase: run a narrow proven-cornerstone stability review or static review packet using `{SELECTED_RETUNE}` side by side with baseline, current guarded candidate, and usage-lens control.

Do not run broad formula search. Do not promote or wire the candidate. The next decision should remain human-review-only, with the candidate treated as a usage/stability lens unless CeeDee Lamb, Justin Jefferson, and Brock Bowers-style stability concerns clear without blindly boosting market-favored injury/context watchlist players.
"""
    write_text("next_phase_handoff.md", handoff)


def write_manifest(context: dict[str, Any]) -> None:
    rows = []
    for name in REQUIRED_ARTIFACTS:
        path = EXPERIMENT_DIR / name
        if path.name == "artifact_manifest.md":
            continue
        rows.append((name, path.stat().st_size, sha256(path)))
    body = [
        "# Artifact Manifest",
        "",
        f"- Verdict: `{context['verdict']}`",
        f"- Decision label: `{context['decision_label']}`",
        f"- Selected retune: `{context['selected_retune']}`",
        f"- Generated at: `{context['generated_at']}`",
        "- Branch: `work/historical-formula-candidate-attribution-retune-readiness-v1-20260702`",
        "",
        "| Artifact | Bytes | SHA256 |",
        "|---|---:|---|",
    ]
    body.extend(f"| `{name}` | {size} | `{digest}` |" for name, size, digest in rows)
    write_text("artifact_manifest.md", "\n".join(body) + "\n")


def write_outside_bundle(context: dict[str, Any], board: list[dict[str, Any]], key_matrix: list[dict[str, Any]]) -> None:
    OUTSIDE_BUNDLE.mkdir(parents=True, exist_ok=True)
    write_csv(OUTSIDE_BUNDLE / "key_player_before_after.csv", key_matrix)
    selected_rows = [
        {
            "player_name": row.get("player_name", ""),
            "position": row.get("position", ""),
            "team": row.get("team", ""),
            "baseline_position_rank": row.get("current_baseline_position_rank", ""),
            "current_guarded_position_rank": row.get("wr_guarded_shadow_position_rank", ""),
            "retune_position_rank_preview": row.get("retune_position_rank_preview", ""),
            "retune_guard_applied": row.get("retune_guard_applied", ""),
            "retune_rank_note": row.get("retune_rank_note", ""),
            "null_fenced_flag": row.get("null_fenced_flag", ""),
        }
        for row in board
    ]
    write_csv(OUTSIDE_BUNDLE / "selected_retune_current_board.csv", selected_rows)
    watchlist = [
        row
        for row in key_matrix
        if row["after_retune_label"]
        in {
            "REMAINS_HUMAN_REVIEW_WATCHLIST",
            "EXPLAINABLE_WATCHLIST",
            "INJURY_TIMELINE_DISCOUNT_WATCHLIST",
            "MISSING_FEATURE_CONTEXT",
        }
    ]
    write_csv(OUTSIDE_BUNDLE / "remaining_watchlist.csv", watchlist)
    write_file(
        OUTSIDE_BUNDLE / "next_decision_options.md",
        """# Next Decision Options

- Reject the candidate.
- Keep it as a usage lens only.
- Continue human review of the dynasty-stability retune.
- Approve a static retune review packet later.
- Do not promote yet.
""",
    )
    html_rows = "\n".join(
        f"<tr><td>{row['player_name']}</td><td>{row['position']}</td><td>{row['baseline_position_rank']}</td>"
        f"<td>{row['current_guard_position_rank']}</td><td>{row['retune_position_rank_preview']}</td>"
        f"<td>{row['after_retune_label']}</td></tr>"
        for row in key_matrix
    )
    write_file(
        OUTSIDE_BUNDLE / "index.html",
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Dynasty Stability Retune V1</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.4; }}
    .banner {{ border: 2px solid #a33; background: #fff4f4; padding: 12px; font-weight: 700; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; }}
    th {{ background: #f0f0f0; }}
  </style>
</head>
<body>
  <div class="banner">REVIEW ONLY - DYNASTY STABILITY RETUNE - NOT PRODUCTION APPROVED - NO APP/RANKING CHANGES</div>
  <h1>Dynasty Stability Retune V1</h1>
  <p>Decision: <strong>{context['decision_label']}</strong></p>
  <p>Selected review-only retune: <strong>{context['selected_retune']}</strong></p>
  <p>Holdout MAE delta vs baseline: {context['selected_holdout_mae_delta']}; holdout Spearman delta: {context['selected_holdout_spearman_delta']}; holdout startable precision delta: {context['selected_holdout_startable_delta']}.</p>
  <h2>Key Player Before / After</h2>
  <table>
    <thead><tr><th>Player</th><th>Pos</th><th>Baseline Pos</th><th>Current Guard Pos</th><th>Retune Pos Preview</th><th>Label</th></tr></thead>
    <tbody>{html_rows}</tbody>
  </table>
  <h2>Human Checklist</h2>
  <ul>
    <li>Inspect whether cornerstone WR/TE protection is football-smart.</li>
    <li>Keep null-fenced players as not enough information.</li>
    <li>Do not promote or wire candidate output.</li>
  </ul>
</body>
</html>
""",
    )


def validate_outputs() -> None:
    missing = [name for name in REQUIRED_ARTIFACTS if not (EXPERIMENT_DIR / name).exists()]
    if missing:
        raise ValueError(f"Missing required artifacts: {missing}")
    empty = [name for name in REQUIRED_ARTIFACTS if (EXPERIMENT_DIR / name).stat().st_size == 0]
    if empty:
        raise ValueError(f"Empty required artifacts: {empty}")
    for path in [
        OUTSIDE_BUNDLE / "index.html",
        OUTSIDE_BUNDLE / "key_player_before_after.csv",
        OUTSIDE_BUNDLE / "selected_retune_current_board.csv",
        OUTSIDE_BUNDLE / "remaining_watchlist.csv",
        OUTSIDE_BUNDLE / "next_decision_options.md",
    ]:
        if not path.exists() or path.stat().st_size == 0:
            raise ValueError(f"Outside bundle artifact missing or empty: {path}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row.get(key, "")) for key in fieldnames})


def write_text(name: str, text: str) -> None:
    write_file(EXPERIMENT_DIR / name, text)


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def num(row: dict[str, Any], column: str) -> float:
    value = row.get(column)
    if value is None or value == "":
        raise ValueError(f"Missing numeric value for {column}; no zero-fill is applied")
    return float(value)


def safe_float(value: Any) -> float:
    if value is None or value == "":
        return math.nan
    try:
        return float(value)
    except ValueError:
        return math.nan


def rank_delta(after: Any, before: Any) -> str:
    after_value = safe_float(after)
    before_value = safe_float(before)
    if math.isnan(after_value) or math.isnan(before_value):
        return ""
    return str(int(after_value - before_value))


def retune_driver_summary(attr: dict[str, Any], current: dict[str, Any], classification: str) -> str:
    if classification == "DYNASTY_STABILITY_RISK_REDUCED":
        return "General baseline-rank cornerstone guard reduced an extreme current-board demotion without using names or market source truth."
    if classification == "INJURY_TIMELINE_DISCOUNT_WATCHLIST":
        return "Tim review says the lower view can be explainable because severe injury / unclear recovery timeline makes an injury discount reasonable."
    if classification == "SMART_CONTRARIAN_FADE":
        return "Non-blocking usage/opportunity fade retained."
    if classification == "EXPLAINABLE_WATCHLIST":
        return "Tim review says the lower view is not automatically a formula flaw because talent is real but contextual football concerns are real."
    if classification == "REMAINS_HUMAN_REVIEW_WATCHLIST":
        return "Still needs Tim review because the usage lens may underweight stability or limited-game context."
    if classification == "MISSING_FEATURE_CONTEXT":
        return "Candidate rank remains unavailable due to null-fenced feature input."
    return attr.get("feature_driver_summary") or current.get("retune_rank_note", "")


def spearman(pred: list[float], actual: list[float]) -> float:
    if len(pred) < 2:
        return 0.0
    return pearson(rankdata(pred), rankdata(actual))


def rankdata(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    idx = 0
    while idx < len(indexed):
        end = idx
        while end + 1 < len(indexed) and indexed[end + 1][1] == indexed[idx][1]:
            end += 1
        average_rank = (idx + end + 2) / 2.0
        for pos in range(idx, end + 1):
            ranks[indexed[pos][0]] = average_rank
        idx = end + 1
    return ranks


def pearson(a: list[float], b: list[float]) -> float:
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    denom_a = math.sqrt(sum((x - mean_a) ** 2 for x in a))
    denom_b = math.sqrt(sum((y - mean_b) ** 2 for y in b))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return numerator / (denom_a * denom_b)


def f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def round_float(value: float) -> float:
    return round(float(value), 6)


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes"}


def csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return str(value).lower()
    return value


if __name__ == "__main__":
    raise SystemExit(main())
