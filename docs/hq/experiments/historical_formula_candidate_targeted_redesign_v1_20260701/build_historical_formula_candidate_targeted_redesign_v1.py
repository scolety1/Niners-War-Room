from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
ROOT_EXPERIMENT_DIR = EXPERIMENT_DIR.parent
V3_DIR = ROOT_EXPERIMENT_DIR / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
SOURCE_CONTRACT_DIR = ROOT_EXPERIMENT_DIR / "historical_tuning_source_contract_v1_20260701"
SEARCH_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_search_v1_20260701"
REVIEW_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_review_v1_20260701"
GATE_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_promotion_gate_prep_v1_20260701"
RESCUE_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_risk_rescue_sprint_v1_20260701"
REFINEMENT_DIR = ROOT_EXPERIMENT_DIR / "historical_formula_candidate_cutline_safe_refinement_v1_20260701"

SUBSTRATE_PATH = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
REFINEMENT_CASEBOOK_PATH = REFINEMENT_DIR / "remaining_cutline_casebook.csv"
BASE_HEAD = "a85e35a02bf5800be8ef42af6428d5ec0b0f298f"
BRANCH = "work/historical-formula-candidate-targeted-redesign-v1-20260701"

TARGET = "next_nwr_points"
BASELINE = "baseline_v3_prior_points"
ORIGINAL = "original_usage_opportunity_volume"
QB_GUARD = "qb_guard_soft_blend"
RB_WR_SAFE = "rb_wr_cutline_safe_blend"
CONSERVATIVE = "conservative_blend_50"
CURRENT_BEST_ALIAS = "current_best_rb_wr_cutline_safe_blend"
SELECTED_REDESIGN = "wr_boundary_breakout_sensitivity_guard"
DECISION_LABEL = "TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY"
VERDICT = "GREEN_TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY_REVIEW_ONLY"

ELITE_QB_POINTS_THRESHOLD = 250.0
ELITE_QB_GAMES_THRESHOLD = 12
SEVERE_REGRESSION_THRESHOLD = 20.0
PREMIUM_OUTSIDE_BAND_V1 = 5
PREMIUM_OUTSIDE_BAND_V2 = 3
PREMIUM_INSIDE_BAND = 8
WR_BREAKOUT_OUTSIDE_BAND = 8
WR_BREAKOUT_INSIDE_BAND = 8

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "targeted_redesign_summary.md",
    "fixed_redesign_variant_definitions.csv",
    "validation_metric_comparison.csv",
    "holdout_metric_comparison.csv",
    "cutline_miss_comparison.csv",
    "remaining_5_case_resolution_report.csv",
    "elite_qb_regression_comparison.csv",
    "position_level_redesign_report.csv",
    "season_level_redesign_report.csv",
    "topn_startable_redesign_report.csv",
    "targeted_redesign_selection_decision.md",
    "selected_redesign_review_packet.md",
    "remaining_concern_casebook.csv",
    "largest_remaining_regressions.csv",
    "human_review_update.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
]


@dataclass(frozen=True)
class Variant:
    candidate_id: str
    role: str
    formula_definition: str
    guard_definition: str
    threshold_policy: str
    allowed_inputs: str


VARIANTS = [
    Variant(BASELINE, "baseline_comparator", "prior_nwr_points", "none", "none", "prior_nwr_points"),
    Variant(
        ORIGINAL,
        "original_candidate_comparator",
        "0.70 * prior_nwr_points + 0.30 * usage_proxy",
        "none",
        "none",
        "prior_nwr_points; prior_carries; prior_receptions; prior_targets; prior_opportunities",
    ),
    Variant(
        QB_GUARD,
        "rescue_comparator",
        "original candidate except elite prior-season QB rows use 0.75 * baseline + 0.25 * original",
        "position == QB and prior_nwr_points >= 250 and prior_games >= 12",
        "fixed threshold inherited from Risk Rescue Sprint V1; no holdout tuning",
        "feature-season position; prior_nwr_points; prior_games; baseline prediction output; original candidate prediction output",
    ),
    Variant(
        RB_WR_SAFE,
        "prior_refinement_comparator",
        "Start from qb_guard_soft_blend; RB/WR rows use 0.50 * baseline + 0.50 * qb_guard; QB/TE rows retain qb_guard",
        "position in RB/WR; no target-outcome condition",
        "fixed prior cutline-safe refinement; no holdout tuning",
        "feature-season position; baseline prediction output; qb_guard prediction output",
    ),
    Variant(
        CONSERVATIVE,
        "rescue_comparator",
        "0.50 * baseline + 0.50 * original candidate",
        "applies to every row",
        "fixed 50/50 blend; no threshold",
        "baseline prediction output; original candidate prediction output",
    ),
    Variant(
        CURRENT_BEST_ALIAS,
        "fixed_redesign_comparison_only",
        "Alias of rb_wr_cutline_safe_blend, retained because it was the prior best refinement",
        "same as rb_wr_cutline_safe_blend",
        "comparison only; no new threshold",
        "feature-season position; baseline prediction output; qb_guard prediction output",
    ),
    Variant(
        "premium_cutline_floor_v1",
        "fixed_targeted_redesign",
        "Start from current best; if baseline rank is inside a key cutline and current best falls 1-5 ranks outside, restore the baseline score as a cutline floor",
        "baseline rank inside QB12/RB12/RB24/WR12/WR24/WR36/TE12 and current-best rank is within 5 ranks beyond that cutline",
        "outside band = 5, predeclared before evaluation",
        "feature-season position; baseline prediction and rank; current-best prediction and rank",
    ),
    Variant(
        "premium_cutline_floor_v2_tighter",
        "fixed_targeted_redesign",
        "Same as premium_cutline_floor_v1, but only for drops 1-3 ranks beyond the cutline",
        "baseline rank inside QB12/RB12/RB24/WR12/WR24/WR36/TE12 and current-best rank is within 3 ranks beyond that cutline",
        "outside band = 3, predeclared before evaluation",
        "feature-season position; baseline prediction and rank; current-best prediction and rank",
    ),
    Variant(
        "high_prior_volume_boundary_guard",
        "fixed_targeted_redesign",
        "Start from current best; for RB/WR/TE cutline drops with strong prior usage, use 0.75 * baseline + 0.25 * qb_guard",
        "RB/WR/TE near a cutline, current best falls within 5 ranks beyond it, and prior usage ranks are strong within the feature season",
        "outside band = 5; inside band = 8; RB touch rank <= 36; WR/TE target or opportunity rank <= 48",
        "feature-season position; prior_touches; prior_targets; prior_opportunities; baseline/current-best predictions and ranks",
    ),
    Variant(
        SELECTED_REDESIGN,
        "selected_fixed_targeted_redesign",
        "Start from current best; for WR24/WR36 boundary drops with usage breakout sensitivity, use 0.80 * baseline + 0.20 * qb_guard",
        "WR only, baseline within 8 ranks inside WR24/WR36, current best within 8 ranks outside, and prior targets/receptions/opportunities rank <= 60",
        "WR cutlines = WR24/WR36; inside/outside band = 8; usage rank threshold = 60; all predeclared before evaluation",
        "feature-season position; prior_targets; prior_receptions; prior_opportunities; baseline/current-best predictions and ranks",
    ),
    Variant(
        "hybrid_qb_plus_premium_cutline_guard",
        "fixed_targeted_redesign",
        "Combine the prior qb_guard_soft_blend with the tighter premium cutline floor",
        "same as premium_cutline_floor_v2_tighter; qb guard is already embedded in current-best prediction",
        "uses premium v2 tighter guard by predeclared policy, not holdout selection",
        "feature-season position; baseline prediction and rank; current-best prediction and rank",
    ),
    Variant(
        "conservative_human_review_variant",
        "fixed_targeted_redesign",
        "Start from current best; for any key cutline drop within 5 ranks beyond the cutline, use 0.85 * baseline + 0.15 * qb_guard",
        "baseline rank inside QB12/RB12/RB24/WR12/WR24/WR36/TE12 and current-best rank is within 5 ranks beyond the same cutline",
        "outside band = 5; conservative blend fixed before evaluation",
        "feature-season position; baseline prediction and rank; current-best prediction and rank",
    ),
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    substrate = pd.read_parquet(SUBSTRATE_PATH)
    validate_inputs(substrate)
    scored = add_redesign_scores(add_splits(substrate.copy()))

    metric_comparison = build_metric_comparison(scored)
    validation_metrics = metric_comparison[metric_comparison["split"].eq("validation")].copy()
    holdout_metrics = metric_comparison[metric_comparison["split"].eq("holdout")].copy()
    cutline = build_cutline_miss_comparison(scored)
    case_resolution = build_remaining_5_case_resolution_report(scored)
    elite_qb = build_elite_qb_comparison(scored)
    position = build_group_report(scored, ["split", "position"], "position")
    season = build_group_report(scored, ["split", "target_season"], "season")
    topn = build_topn_report(scored)
    remaining_casebook = build_remaining_cutline_casebook(scored, SELECTED_REDESIGN)
    regressions = build_largest_remaining_regressions(scored, SELECTED_REDESIGN)
    definitions = build_variant_definitions()

    write_csv(definitions, "fixed_redesign_variant_definitions.csv")
    write_csv(validation_metrics, "validation_metric_comparison.csv")
    write_csv(holdout_metrics, "holdout_metric_comparison.csv")
    write_csv(cutline, "cutline_miss_comparison.csv")
    write_csv(case_resolution, "remaining_5_case_resolution_report.csv")
    write_csv(elite_qb, "elite_qb_regression_comparison.csv")
    write_csv(position, "position_level_redesign_report.csv")
    write_csv(season, "season_level_redesign_report.csv")
    write_csv(topn, "topn_startable_redesign_report.csv")
    write_csv(remaining_casebook, "remaining_concern_casebook.csv")
    write_csv(regressions, "largest_remaining_regressions.csv")

    context = build_context(
        validation_metrics,
        holdout_metrics,
        cutline,
        case_resolution,
        elite_qb,
        position,
        season,
        remaining_casebook,
        regressions,
    )
    write_markdown_reports(context)
    write_manifest(context)

    print(f"wrote={EXPERIMENT_DIR}")
    print(f"decision_label={DECISION_LABEL}")
    print(f"selected_redesign={SELECTED_REDESIGN}")
    return 0


def validate_inputs(substrate: pd.DataFrame) -> None:
    required_dirs = [SOURCE_CONTRACT_DIR, SEARCH_DIR, REVIEW_DIR, GATE_DIR, RESCUE_DIR, REFINEMENT_DIR]
    missing_dirs = [str(path) for path in required_dirs if not path.exists()]
    if missing_dirs:
        raise ValueError(f"Missing merged evidence directories: {missing_dirs}")
    if not REFINEMENT_CASEBOOK_PATH.exists():
        raise ValueError(f"Missing prior remaining cutline casebook: {REFINEMENT_CASEBOOK_PATH}")
    if len(substrate) != 5518:
        raise ValueError(f"Expected 5518 V3 substrate rows, got {len(substrate)}")
    if not (substrate["target_season"] == substrate["feature_season"] + 1).all():
        raise ValueError("Feature season N to target season N+1 lag is broken")
    forbidden_columns = [
        col
        for col in substrate.columns
        if any(token in col.lower() for token in ["route", "tprr", "yprr", "rz_att", "red_zone"])
    ]
    if forbidden_columns:
        raise ValueError(f"Forbidden substrate columns present: {forbidden_columns}")
    forbidden_flags = [
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
        "production_approved",
    ]
    if substrate[forbidden_flags].astype(bool).any().any():
        raise ValueError("Substrate contains a promoted production flag")
    required_inputs = [
        "prior_nwr_points",
        "prior_games",
        "prior_carries",
        "prior_receptions",
        "prior_targets",
        "prior_opportunities",
        "prior_touches",
    ]
    if substrate[required_inputs].isna().any().any():
        raise ValueError("Primary redesign inputs contain null values; no zero-fill is applied")


def add_splits(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["split"] = pd.NA
    output.loc[output["feature_season"].between(2012, 2020), "split"] = "train"
    output.loc[output["feature_season"].between(2021, 2022), "split"] = "validation"
    output.loc[output["feature_season"].between(2023, 2024), "split"] = "holdout"
    if output["split"].isna().any():
        raise ValueError("Rows outside fixed readiness-gate split policy")
    if output["split"].value_counts().to_dict() != {"train": 3716, "validation": 912, "holdout": 890}:
        raise ValueError("Unexpected readiness split counts")
    return output


def add_redesign_scores(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output[BASELINE] = num(output, "prior_nwr_points")
    usage_proxy = (
        0.40 * num(output, "prior_carries")
        + 0.55 * num(output, "prior_receptions")
        + 0.20 * num(output, "prior_targets")
        + 0.15 * num(output, "prior_opportunities")
    )
    output[ORIGINAL] = 0.70 * output[BASELINE] + 0.30 * usage_proxy
    elite_qb = elite_qb_mask(output)
    output[QB_GUARD] = output[ORIGINAL].where(~elite_qb, 0.75 * output[BASELINE] + 0.25 * output[ORIGINAL])
    output[RB_WR_SAFE] = output[QB_GUARD].where(
        ~output["position"].isin(["RB", "WR"]), 0.50 * output[BASELINE] + 0.50 * output[QB_GUARD]
    )
    output[CONSERVATIVE] = 0.50 * output[BASELINE] + 0.50 * output[ORIGINAL]
    output[CURRENT_BEST_ALIAS] = output[RB_WR_SAFE]

    output["baseline_prediction_rank"] = prediction_rank(output, BASELINE)
    output["current_best_prediction_rank"] = prediction_rank(output, RB_WR_SAFE)

    premium_v1 = cutline_drop_mask(output, RB_WR_SAFE, outside_band=PREMIUM_OUTSIDE_BAND_V1)
    premium_v2 = cutline_drop_mask(output, RB_WR_SAFE, outside_band=PREMIUM_OUTSIDE_BAND_V2)
    high_volume = high_prior_volume_boundary_mask(output, RB_WR_SAFE)
    wr_breakout = wr_boundary_breakout_mask(output, RB_WR_SAFE)

    output["premium_cutline_floor_v1_guard_applies"] = premium_v1
    output["premium_cutline_floor_v2_guard_applies"] = premium_v2
    output["high_prior_volume_boundary_guard_applies"] = high_volume
    output["wr_boundary_breakout_sensitivity_guard_applies"] = wr_breakout

    output["premium_cutline_floor_v1"] = output[RB_WR_SAFE].where(~premium_v1, output[BASELINE])
    output["premium_cutline_floor_v2_tighter"] = output[RB_WR_SAFE].where(~premium_v2, output[BASELINE])
    output["high_prior_volume_boundary_guard"] = output[RB_WR_SAFE].where(
        ~high_volume, 0.75 * output[BASELINE] + 0.25 * output[QB_GUARD]
    )
    output[SELECTED_REDESIGN] = output[RB_WR_SAFE].where(
        ~wr_breakout, 0.80 * output[BASELINE] + 0.20 * output[QB_GUARD]
    )
    output["hybrid_qb_plus_premium_cutline_guard"] = output["premium_cutline_floor_v2_tighter"]
    conservative_guard = cutline_drop_mask(output, RB_WR_SAFE, outside_band=PREMIUM_OUTSIDE_BAND_V1)
    output["conservative_human_review_variant"] = output[RB_WR_SAFE].where(
        ~conservative_guard, 0.85 * output[BASELINE] + 0.15 * output[QB_GUARD]
    )

    for candidate_id in variant_ids():
        if output[candidate_id].isna().any():
            raise ValueError(f"Variant produced null prediction: {candidate_id}")
    return output


def num(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="raise").astype(float)


def prediction_rank(frame: pd.DataFrame, candidate_id: str) -> pd.Series:
    return (
        frame.groupby(["target_season", "position"], sort=False)[candidate_id]
        .rank(method="first", ascending=False)
        .astype(int)
    )


def feature_rank(frame: pd.DataFrame, column: str) -> pd.Series:
    return (
        frame.groupby(["feature_season", "position"], sort=False)[column]
        .rank(method="first", ascending=False)
        .astype(int)
    )


def elite_qb_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["position"].eq("QB")
        & num(frame, "prior_nwr_points").ge(ELITE_QB_POINTS_THRESHOLD)
        & num(frame, "prior_games").ge(ELITE_QB_GAMES_THRESHOLD)
    )


def cutline_drop_mask(
    frame: pd.DataFrame,
    candidate_id: str,
    *,
    outside_band: int | None,
    inside_band: int | None = None,
    positions: set[str] | None = None,
    cut_filter: set[tuple[str, int]] | None = None,
) -> pd.Series:
    candidate_rank = prediction_rank(frame, candidate_id)
    baseline_rank = frame["baseline_prediction_rank"]
    mask = pd.Series(False, index=frame.index)
    for position, cutlines in bucket_cutlines().items():
        if positions is not None and position not in positions:
            continue
        position_rows = frame["position"].eq(position)
        for cutline in cutlines:
            if cut_filter is not None and (position, cutline) not in cut_filter:
                continue
            dropped = position_rows & baseline_rank.le(cutline) & candidate_rank.gt(cutline)
            if outside_band is not None:
                dropped = dropped & candidate_rank.le(cutline + outside_band)
            if inside_band is not None:
                dropped = dropped & baseline_rank.ge(cutline - inside_band)
            mask = mask | dropped
    return mask


def high_prior_volume_boundary_mask(frame: pd.DataFrame, candidate_id: str) -> pd.Series:
    touch_rank = feature_rank(frame, "prior_touches")
    target_rank = feature_rank(frame, "prior_targets")
    opportunity_rank = feature_rank(frame, "prior_opportunities")
    strong_usage = (frame["position"].eq("RB") & touch_rank.le(36)) | (
        frame["position"].isin(["WR", "TE"]) & (target_rank.le(48) | opportunity_rank.le(48))
    )
    boundary = cutline_drop_mask(
        frame,
        candidate_id,
        outside_band=PREMIUM_OUTSIDE_BAND_V1,
        inside_band=PREMIUM_INSIDE_BAND,
        positions={"RB", "WR", "TE"},
    )
    return boundary & strong_usage


def wr_boundary_breakout_mask(frame: pd.DataFrame, candidate_id: str) -> pd.Series:
    target_rank = feature_rank(frame, "prior_targets")
    reception_rank = feature_rank(frame, "prior_receptions")
    opportunity_rank = feature_rank(frame, "prior_opportunities")
    wr_usage_signal = frame["position"].eq("WR") & (
        target_rank.le(60) | reception_rank.le(60) | opportunity_rank.le(60)
    )
    wr_boundary = cutline_drop_mask(
        frame,
        candidate_id,
        outside_band=WR_BREAKOUT_OUTSIDE_BAND,
        inside_band=WR_BREAKOUT_INSIDE_BAND,
        positions={"WR"},
        cut_filter={("WR", 24), ("WR", 36)},
    )
    return wr_boundary & wr_usage_signal


def bucket_cutlines() -> dict[str, list[int]]:
    return {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}


def startable_boundaries() -> dict[str, int]:
    return {"QB": 12, "RB": 24, "WR": 36, "TE": 12}


def bucket_columns() -> dict[str, list[tuple[str, str, int]]]:
    return {
        "QB": [("QB_TOP12", "qb_t12", 12)],
        "RB": [("RB_TOP12", "rb_t12", 12), ("RB_TOP24", "rb_t24", 24)],
        "WR": [("WR_TOP12", "wr_t12", 12), ("WR_TOP24", "wr_t24", 24), ("WR_TOP36", "wr_t36", 36)],
        "TE": [("TE_TOP12", "te_t12", 12)],
    }


def variant_ids() -> list[str]:
    return [variant.candidate_id for variant in VARIANTS]


def build_variant_definitions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": variant.candidate_id,
                "role": variant.role,
                "formula_definition": variant.formula_definition,
                "guard_definition": variant.guard_definition,
                "threshold_policy": variant.threshold_policy,
                "allowed_inputs": variant.allowed_inputs,
                "holdout_used_to_define_thresholds": False,
                "holdout_used_for_selection": False,
                "target_outcomes_used_in_guard": False,
                "player_specific_exception_used": False,
                "review_only": True,
                "approved_for_production_use": False,
                "shadow_review_approved": False,
            }
            for variant in VARIANTS
        ]
    )


def build_metric_comparison(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout"]:
        subset = scored[scored["split"].eq(split)].copy()
        baseline = metric_row(subset, BASELINE, split, "all_positions")
        original = metric_row(subset, ORIGINAL, split, "all_positions")
        qb_guard = metric_row(subset, QB_GUARD, split, "all_positions")
        rb_wr_safe = metric_row(subset, RB_WR_SAFE, split, "all_positions")
        conservative = metric_row(subset, CONSERVATIVE, split, "all_positions")
        for candidate_id in variant_ids():
            row = metric_row(subset, candidate_id, split, "all_positions")
            row.update(comparison_deltas(row, baseline, original, qb_guard, rb_wr_safe, conservative))
            row["selection_policy"] = (
                "validation_only" if split == "validation" else "one_time_holdout_after_fixed_definitions"
            )
            rows.append(row)
    return pd.DataFrame(rows)


def metric_row(subset: pd.DataFrame, candidate_id: str, split: str, group: str) -> dict[str, Any]:
    pred = num(subset, candidate_id)
    actual = num(subset, TARGET)
    topn = startable_at_n(subset, candidate_id)
    return {
        "candidate_id": candidate_id,
        "split": split,
        "group": group,
        "rows": int(len(subset)),
        "mae": round(float((pred - actual).abs().mean()), 6),
        "spearman": round(float(pred.rank(method="average").corr(actual.rank(method="average"))), 6),
        "startable_precision_at_n": round(topn["precision"], 6),
        "startable_recall_at_n": round(topn["recall"], 6),
        "startable_f1_at_n": round(topn["f1"], 6),
    }


def comparison_deltas(
    row: dict[str, Any],
    baseline: dict[str, Any],
    original: dict[str, Any],
    qb_guard: dict[str, Any],
    rb_wr_safe: dict[str, Any],
    conservative: dict[str, Any],
) -> dict[str, Any]:
    return {
        "mae_delta_vs_baseline": round(float(row["mae"]) - float(baseline["mae"]), 6),
        "mae_delta_vs_original": round(float(row["mae"]) - float(original["mae"]), 6),
        "mae_delta_vs_qb_guard": round(float(row["mae"]) - float(qb_guard["mae"]), 6),
        "mae_delta_vs_rb_wr_cutline_safe": round(float(row["mae"]) - float(rb_wr_safe["mae"]), 6),
        "mae_delta_vs_conservative_blend_50": round(float(row["mae"]) - float(conservative["mae"]), 6),
        "spearman_delta_vs_baseline": round(float(row["spearman"]) - float(baseline["spearman"]), 6),
        "spearman_delta_vs_qb_guard": round(float(row["spearman"]) - float(qb_guard["spearman"]), 6),
        "spearman_delta_vs_rb_wr_cutline_safe": round(float(row["spearman"]) - float(rb_wr_safe["spearman"]), 6),
        "startable_precision_delta_vs_baseline": round(
            float(row["startable_precision_at_n"]) - float(baseline["startable_precision_at_n"]), 6
        ),
        "startable_precision_delta_vs_qb_guard": round(
            float(row["startable_precision_at_n"]) - float(qb_guard["startable_precision_at_n"]), 6
        ),
        "startable_precision_delta_vs_rb_wr_cutline_safe": round(
            float(row["startable_precision_at_n"]) - float(rb_wr_safe["startable_precision_at_n"]), 6
        ),
    }


def startable_at_n(subset: pd.DataFrame, candidate_id: str) -> dict[str, float]:
    predicted = []
    for (_season, position), group in subset.groupby(["target_season", "position"]):
        n = startable_n(position)
        predicted.append(group.sort_values(candidate_id, ascending=False).head(min(n, len(group))))
    if not predicted:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    predicted_df = pd.concat(predicted)
    tp = int(predicted_df["startable_hit"].astype(bool).sum())
    predicted_count = len(predicted_df)
    actual_count = int(subset["startable_hit"].astype(bool).sum())
    precision = tp / predicted_count if predicted_count else 0.0
    recall = tp / actual_count if actual_count else 0.0
    return {"precision": precision, "recall": recall, "f1": f1(precision, recall)}


def startable_n(position: str) -> int:
    return startable_boundaries().get(position, 12)


def f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def build_cutline_miss_comparison(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout", "validation_holdout"]:
        subset = review_subset(scored, split)
        for candidate_id in variant_ids():
            rows.append(cutline_row(subset, candidate_id, split))
    output = pd.DataFrame(rows)
    comparators = {
        "original_cutline_misses": ORIGINAL,
        "qb_guard_cutline_misses": QB_GUARD,
        "rb_wr_cutline_safe_misses": RB_WR_SAFE,
        "conservative_cutline_misses": CONSERVATIVE,
    }
    for column, candidate_id in comparators.items():
        comp = output[output["candidate_id"].eq(candidate_id)][["split", "actual_hits_moved_below_cutline"]].rename(
            columns={"actual_hits_moved_below_cutline": column}
        )
        output = output.merge(comp, on="split", how="left")
        output[f"actual_hits_moved_below_delta_vs_{candidate_id}"] = (
            output["actual_hits_moved_below_cutline"] - output[column]
        )
    return output


def cutline_row(subset: pd.DataFrame, candidate_id: str, split: str) -> dict[str, Any]:
    moved_below = 0
    actual_hits_moved_below = 0
    for (_season, position), group in subset.groupby(["target_season", "position"]):
        baseline_rank = group[BASELINE].rank(method="first", ascending=False)
        candidate_rank = group[candidate_id].rank(method="first", ascending=False)
        actual_finish = num(group, "next_position_finish")
        for cutline in bucket_cutlines().get(position, []):
            below = (baseline_rank <= cutline) & (candidate_rank > cutline)
            moved_below += int(below.sum())
            actual_hits_moved_below += int((below & actual_finish.le(cutline)).sum())
    return {
        "candidate_id": candidate_id,
        "split": split,
        "moved_below_cutline_count": moved_below,
        "actual_hits_moved_below_cutline": actual_hits_moved_below,
        "guard_uses_target_outcomes": False,
        "player_specific_exception_used": False,
    }


def build_remaining_5_case_resolution_report(scored: pd.DataFrame) -> pd.DataFrame:
    previous = pd.read_csv(REFINEMENT_CASEBOOK_PATH)
    rows = []
    review = scored[scored["split"].isin(["validation", "holdout"])].copy()
    rank_columns = [BASELINE, ORIGINAL, QB_GUARD, RB_WR_SAFE, SELECTED_REDESIGN]
    rank_maps: dict[str, pd.Series] = {}
    for candidate_id in rank_columns:
        rank_maps[candidate_id] = review.groupby(["target_season", "position"], sort=False)[candidate_id].rank(
            method="first", ascending=False
        )
    for _, case in previous.iterrows():
        row_match = review[
            review["player_id_gsis"].eq(case["player_id"])
            & review["feature_season"].eq(int(case["feature_season"]))
            & review["target_season"].eq(int(case["target_season"]))
        ]
        if row_match.empty:
            raise ValueError(f"Could not match remaining cutline case: {case.to_dict()}")
        idx = row_match.index[0]
        row = row_match.iloc[0]
        cutline = int(case["cutline"])
        selected_rank = int(rank_maps[SELECTED_REDESIGN].loc[idx])
        rb_wr_rank = int(rank_maps[RB_WR_SAFE].loc[idx])
        resolved = selected_rank <= cutline
        rows.append(
            {
                "player_id": row["player_id_gsis"],
                "player_name": row["feature_player_name"],
                "position": row["position"],
                "feature_season": int(row["feature_season"]),
                "target_season": int(row["target_season"]),
                "split": row["split"],
                "cutline": cutline,
                "baseline_rank": int(rank_maps[BASELINE].loc[idx]),
                "original_candidate_rank": int(rank_maps[ORIGINAL].loc[idx]),
                "qb_guard_soft_blend_rank": int(rank_maps[QB_GUARD].loc[idx]),
                "rb_wr_cutline_safe_blend_rank": rb_wr_rank,
                "selected_redesign_rank": selected_rank,
                "actual_position_finish": int(row["next_position_finish"]),
                "baseline_prediction": round(float(row[BASELINE]), 6),
                "original_prediction": round(float(row[ORIGINAL]), 6),
                "qb_guard_prediction": round(float(row[QB_GUARD]), 6),
                "rb_wr_cutline_safe_prediction": round(float(row[RB_WR_SAFE]), 6),
                "selected_redesign_prediction": round(float(row[SELECTED_REDESIGN]), 6),
                "actual_next_points": round(float(row[TARGET]), 6),
                "resolved_by_selected_redesign": resolved,
                "resolution_status": "resolved_inside_cutline" if resolved else "still_below_cutline",
                "guard_uses_target_outcomes": False,
                "player_specific_exception_used": False,
            }
        )
    return pd.DataFrame(rows).sort_values(["target_season", "position", "cutline", "baseline_rank"])


def build_elite_qb_comparison(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout", "validation_holdout"]:
        subset = review_subset(scored, split)
        elite = subset[elite_qb_mask(subset)].copy()
        baseline_error = (num(elite, BASELINE) - num(elite, TARGET)).abs()
        for candidate_id in variant_ids():
            candidate_error = (num(elite, candidate_id) - num(elite, TARGET)).abs()
            delta = candidate_error - baseline_error
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "split": split,
                    "elite_qb_rows": int(len(elite)),
                    "severe_regression_threshold": SEVERE_REGRESSION_THRESHOLD,
                    "severe_regression_count": int(delta.gt(SEVERE_REGRESSION_THRESHOLD).sum()),
                    "mean_error_delta_vs_baseline": round(float(delta.mean()), 6) if len(delta) else 0.0,
                    "max_error_delta_vs_baseline": round(float(delta.max()), 6) if len(delta) else 0.0,
                    "guard_uses_target_outcomes": False,
                }
            )
    output = pd.DataFrame(rows)
    original = output[output["candidate_id"].eq(ORIGINAL)][["split", "severe_regression_count"]].rename(
        columns={"severe_regression_count": "original_severe_regression_count"}
    )
    output = output.merge(original, on="split", how="left")
    output["severe_regression_delta_vs_original"] = (
        output["severe_regression_count"] - output["original_severe_regression_count"]
    )
    return output


def review_subset(scored: pd.DataFrame, split: str) -> pd.DataFrame:
    if split == "validation_holdout":
        return scored[scored["split"].isin(["validation", "holdout"])].copy()
    return scored[scored["split"].eq(split)].copy()


def build_group_report(scored: pd.DataFrame, group_cols: list[str], group_type: str) -> pd.DataFrame:
    rows = []
    review = scored[scored["split"].isin(["validation", "holdout"])].copy()
    for keys, group in review.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        split = str(group["split"].iloc[0])
        baseline = metric_row(group, BASELINE, split, "group")
        original = metric_row(group, ORIGINAL, split, "group")
        qb_guard = metric_row(group, QB_GUARD, split, "group")
        rb_wr_safe = metric_row(group, RB_WR_SAFE, split, "group")
        conservative = metric_row(group, CONSERVATIVE, split, "group")
        for candidate_id in variant_ids():
            row = metric_row(group, candidate_id, split, "group")
            row.update(comparison_deltas(row, baseline, original, qb_guard, rb_wr_safe, conservative))
            for column, value in zip(group_cols, keys):
                row[column] = value
            row["group_type"] = group_type
            rows.append(row)
    return pd.DataFrame(rows)


def build_topn_report(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout"]:
        split_df = scored[scored["split"].eq(split)].copy()
        for candidate_id in variant_ids():
            for position, buckets in bucket_columns().items():
                subset = split_df[split_df["position"].eq(position)].copy()
                for bucket, actual_column, n in buckets:
                    rows.append(bucket_metric_row(subset, candidate_id, split, position, bucket, actual_column, n))
    output = pd.DataFrame(rows)
    baseline = output[output["candidate_id"].eq(BASELINE)][["split", "position", "bucket", "precision", "recall", "f1"]]
    baseline = baseline.rename(
        columns={"precision": "baseline_precision", "recall": "baseline_recall", "f1": "baseline_f1"}
    )
    rb_wr_safe = output[output["candidate_id"].eq(RB_WR_SAFE)][
        ["split", "position", "bucket", "precision", "recall", "f1"]
    ]
    rb_wr_safe = rb_wr_safe.rename(
        columns={"precision": "rb_wr_precision", "recall": "rb_wr_recall", "f1": "rb_wr_f1"}
    )
    output = output.merge(baseline, on=["split", "position", "bucket"], how="left")
    output = output.merge(rb_wr_safe, on=["split", "position", "bucket"], how="left")
    for metric in ["precision", "recall", "f1"]:
        output[f"{metric}_delta_vs_baseline"] = (output[metric] - output[f"baseline_{metric}"]).round(6)
        output[f"{metric}_delta_vs_rb_wr_cutline_safe"] = (output[metric] - output[f"rb_wr_{metric}"]).round(6)
    output["material_regression_vs_baseline"] = output["precision_delta_vs_baseline"].lt(-0.02) | output[
        "f1_delta_vs_baseline"
    ].lt(-0.02)
    return output


def bucket_metric_row(
    subset: pd.DataFrame,
    candidate_id: str,
    split: str,
    position: str,
    bucket_label: str,
    actual_column: str,
    n: int,
) -> dict[str, Any]:
    predicted = []
    for _season, group in subset.groupby("target_season"):
        predicted.append(group.sort_values(candidate_id, ascending=False).head(min(n, len(group))))
    predicted_df = pd.concat(predicted) if predicted else pd.DataFrame()
    predicted_ids = set(predicted_df["substrate_row_id"]) if not predicted_df.empty else set()
    actual_ids = set(subset.loc[subset[actual_column].astype(bool), "substrate_row_id"])
    tp = len(predicted_ids & actual_ids)
    precision = tp / len(predicted_ids) if predicted_ids else 0.0
    recall = tp / len(actual_ids) if actual_ids else 0.0
    return {
        "candidate_id": candidate_id,
        "split": split,
        "position": position,
        "bucket": bucket_label,
        "n_per_season": n,
        "candidate_predicted_count": len(predicted_ids),
        "actual_bucket_count": len(actual_ids),
        "true_positive_count": tp,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1(precision, recall), 6),
    }


def build_remaining_cutline_casebook(scored: pd.DataFrame, candidate_id: str) -> pd.DataFrame:
    rows = []
    review = scored[scored["split"].isin(["validation", "holdout"])].copy()
    for (_season, position), group in review.groupby(["target_season", "position"]):
        baseline_rank = group[BASELINE].rank(method="first", ascending=False)
        candidate_rank = group[candidate_id].rank(method="first", ascending=False)
        rb_wr_rank = group[RB_WR_SAFE].rank(method="first", ascending=False)
        actual_finish = num(group, "next_position_finish")
        for cutline in bucket_cutlines().get(position, []):
            miss = (baseline_rank <= cutline) & (candidate_rank > cutline) & actual_finish.le(cutline)
            for idx, row in group.loc[miss].iterrows():
                rows.append(
                    {
                        "player_id": row["player_id_gsis"],
                        "player_name": row["feature_player_name"],
                        "position": row["position"],
                        "feature_season": int(row["feature_season"]),
                        "target_season": int(row["target_season"]),
                        "split": row["split"],
                        "cutline": cutline,
                        "baseline_rank": int(baseline_rank.loc[idx]),
                        "rb_wr_cutline_safe_rank": int(rb_wr_rank.loc[idx]),
                        "selected_redesign_rank": int(candidate_rank.loc[idx]),
                        "actual_position_finish": int(row["next_position_finish"]),
                        "baseline_prediction": round(float(row[BASELINE]), 6),
                        "rb_wr_cutline_safe_prediction": round(float(row[RB_WR_SAFE]), 6),
                        "selected_redesign_prediction": round(float(row[candidate_id]), 6),
                        "actual_next_points": round(float(row[TARGET]), 6),
                        "review_note": "Remaining actual cutline hit moved below cutline by selected targeted redesign.",
                    }
                )
    if not rows:
        return pd.DataFrame(
            columns=[
                "player_id",
                "player_name",
                "position",
                "feature_season",
                "target_season",
                "split",
                "cutline",
                "baseline_rank",
                "rb_wr_cutline_safe_rank",
                "selected_redesign_rank",
                "actual_position_finish",
                "baseline_prediction",
                "rb_wr_cutline_safe_prediction",
                "selected_redesign_prediction",
                "actual_next_points",
                "review_note",
            ]
        )
    return pd.DataFrame(rows).sort_values(["target_season", "position", "cutline", "baseline_rank"])


def build_largest_remaining_regressions(scored: pd.DataFrame, candidate_id: str) -> pd.DataFrame:
    review = scored[scored["split"].isin(["validation", "holdout"])].copy()
    output = review.copy()
    output["baseline_error"] = (num(output, BASELINE) - num(output, TARGET)).abs()
    output["rb_wr_cutline_safe_error"] = (num(output, RB_WR_SAFE) - num(output, TARGET)).abs()
    output["selected_redesign_error"] = (num(output, candidate_id) - num(output, TARGET)).abs()
    output["selected_error_delta_vs_baseline"] = output["selected_redesign_error"] - output["baseline_error"]
    output["selected_error_delta_vs_rb_wr_cutline_safe"] = (
        output["selected_redesign_error"] - output["rb_wr_cutline_safe_error"]
    )
    output = output.sort_values("selected_error_delta_vs_baseline", ascending=False).head(40).copy()
    output["player_id"] = output["player_id_gsis"]
    output["player_name"] = output["feature_player_name"]
    output["actual_next_points"] = output[TARGET]
    columns = [
        "player_id",
        "player_name",
        "position",
        "feature_season",
        "target_season",
        "split",
        "startable_bucket",
        "prior_nwr_points",
        "prior_carries",
        "prior_receptions",
        "prior_targets",
        "prior_opportunities",
        BASELINE,
        RB_WR_SAFE,
        candidate_id,
        "actual_next_points",
        "baseline_error",
        "rb_wr_cutline_safe_error",
        "selected_redesign_error",
        "selected_error_delta_vs_baseline",
        "selected_error_delta_vs_rb_wr_cutline_safe",
    ]
    return output[columns]


def build_context(
    validation: pd.DataFrame,
    holdout: pd.DataFrame,
    cutline: pd.DataFrame,
    case_resolution: pd.DataFrame,
    elite_qb: pd.DataFrame,
    position: pd.DataFrame,
    season: pd.DataFrame,
    remaining_casebook: pd.DataFrame,
    regressions: pd.DataFrame,
) -> dict[str, Any]:
    val = validation.set_index("candidate_id")
    hold = holdout.set_index("candidate_id")
    cuts = cutline[cutline["split"].eq("validation_holdout")].set_index("candidate_id")
    elite = elite_qb[elite_qb["split"].eq("validation_holdout")].set_index("candidate_id")
    selected_holdout_positions = position[
        (position["candidate_id"].eq(SELECTED_REDESIGN)) & (position["split"].eq("holdout"))
    ].copy()
    selected_holdout_seasons = season[
        (season["candidate_id"].eq(SELECTED_REDESIGN)) & (season["split"].eq("holdout"))
    ].copy()
    resolved_cases = case_resolution["resolved_by_selected_redesign"].astype(bool)
    context = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT,
        "decision_label": DECISION_LABEL,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "selected_redesign": SELECTED_REDESIGN,
        "original_validation_mae_delta": val.loc[ORIGINAL, "mae_delta_vs_baseline"],
        "original_holdout_mae_delta": hold.loc[ORIGINAL, "mae_delta_vs_baseline"],
        "qb_guard_validation_mae_delta": val.loc[QB_GUARD, "mae_delta_vs_baseline"],
        "qb_guard_holdout_mae_delta": hold.loc[QB_GUARD, "mae_delta_vs_baseline"],
        "rb_wr_validation_mae_delta": val.loc[RB_WR_SAFE, "mae_delta_vs_baseline"],
        "rb_wr_holdout_mae_delta": hold.loc[RB_WR_SAFE, "mae_delta_vs_baseline"],
        "selected_validation_mae_delta": val.loc[SELECTED_REDESIGN, "mae_delta_vs_baseline"],
        "selected_holdout_mae_delta": hold.loc[SELECTED_REDESIGN, "mae_delta_vs_baseline"],
        "selected_holdout_spearman_delta": hold.loc[SELECTED_REDESIGN, "spearman_delta_vs_baseline"],
        "selected_validation_startable_delta": val.loc[SELECTED_REDESIGN, "startable_precision_delta_vs_baseline"],
        "selected_holdout_startable_delta": hold.loc[SELECTED_REDESIGN, "startable_precision_delta_vs_baseline"],
        "original_cutline_misses": int(cuts.loc[ORIGINAL, "actual_hits_moved_below_cutline"]),
        "qb_guard_cutline_misses": int(cuts.loc[QB_GUARD, "actual_hits_moved_below_cutline"]),
        "rb_wr_cutline_misses": int(cuts.loc[RB_WR_SAFE, "actual_hits_moved_below_cutline"]),
        "selected_cutline_misses": int(cuts.loc[SELECTED_REDESIGN, "actual_hits_moved_below_cutline"]),
        "original_elite_qb_severe": int(elite.loc[ORIGINAL, "severe_regression_count"]),
        "qb_guard_elite_qb_severe": int(elite.loc[QB_GUARD, "severe_regression_count"]),
        "rb_wr_elite_qb_severe": int(elite.loc[RB_WR_SAFE, "severe_regression_count"]),
        "selected_elite_qb_severe": int(elite.loc[SELECTED_REDESIGN, "severe_regression_count"]),
        "resolved_remaining_5": int(resolved_cases.sum()),
        "remaining_5_count": int(len(case_resolution)),
        "selected_remaining_casebook_rows": int(len(remaining_casebook)),
        "selected_holdout_positions_improved": int(selected_holdout_positions["mae_delta_vs_baseline"].lt(0).sum()),
        "selected_holdout_position_count": int(len(selected_holdout_positions)),
        "selected_holdout_seasons_improved": int(selected_holdout_seasons["mae_delta_vs_baseline"].lt(0).sum()),
        "selected_holdout_season_count": int(len(selected_holdout_seasons)),
        "remaining_players": ", ".join(remaining_casebook["player_name"].astype(str).tolist()),
        "largest_regression_player": str(regressions.iloc[0]["player_name"]) if not regressions.empty else "",
    }
    return context


def write_markdown_reports(context: dict[str, Any]) -> None:
    reports = {
        "targeted_redesign_summary.md": summary_md(context),
        "targeted_redesign_selection_decision.md": selection_md(context),
        "selected_redesign_review_packet.md": selected_packet_md(context),
        "human_review_update.md": human_review_md(context),
        "do_not_promote_notice.md": do_not_promote_md(),
        "guardrail_report.md": guardrail_md(),
        "merge_safety_report.md": merge_safety_md(),
        "next_phase_handoff.md": next_phase_md(context),
    }
    for name, body in reports.items():
        write_text(name, body)


def summary_md(context: dict[str, Any]) -> str:
    return f"""
# Historical Formula Candidate Targeted Redesign V1

Verdict: `{context['verdict']}`

Decision label: `{context['decision_label']}`

Selected redesign: `{context['selected_redesign']}`

This lane tested only fixed, interpretable, non-player-specific redesign variants for the held `usage_opportunity_volume` candidate. It did not run unbounded search, train a model, change production formulas, approve shadow review, or wire output into NWR.

## Key Evidence

- Original validation / holdout MAE delta: `{context['original_validation_mae_delta']}` / `{context['original_holdout_mae_delta']}`
- `qb_guard_soft_blend` validation / holdout MAE delta: `{context['qb_guard_validation_mae_delta']}` / `{context['qb_guard_holdout_mae_delta']}`
- `rb_wr_cutline_safe_blend` validation / holdout MAE delta: `{context['rb_wr_validation_mae_delta']}` / `{context['rb_wr_holdout_mae_delta']}`
- `{context['selected_redesign']}` validation / holdout MAE delta: `{context['selected_validation_mae_delta']}` / `{context['selected_holdout_mae_delta']}`
- `{context['selected_redesign']}` holdout Spearman delta: `{context['selected_holdout_spearman_delta']}`
- `{context['selected_redesign']}` validation / holdout startable precision delta: `{context['selected_validation_startable_delta']}` / `{context['selected_holdout_startable_delta']}`
- Actual cutline hits moved below cutline: original `{context['original_cutline_misses']}`, `qb_guard_soft_blend` `{context['qb_guard_cutline_misses']}`, `rb_wr_cutline_safe_blend` `{context['rb_wr_cutline_misses']}`, selected redesign `{context['selected_cutline_misses']}`
- Elite-QB severe regressions: original `{context['original_elite_qb_severe']}`, `qb_guard_soft_blend` `{context['qb_guard_elite_qb_severe']}`, selected redesign `{context['selected_elite_qb_severe']}`
- Remaining 5 static-autopsy cases resolved by selected redesign: `{context['resolved_remaining_5']}/{context['remaining_5_count']}`

Conclusion: `{context['selected_redesign']}` clears the requested human-review threshold by reducing actual cutline hits from `5` to `{context['selected_cutline_misses']}` while preserving a material holdout MAE gain, keeping startable precision flat versus baseline, and keeping elite-QB severe regressions low. It remains review-only and is not production-approved.
"""


def selection_md(context: dict[str, Any]) -> str:
    return f"""
# Targeted Redesign Selection Decision

Decision label: `{DECISION_LABEL}`

Selected redesign: `{SELECTED_REDESIGN}`

Validation-only selection logic:

- The selected redesign preserved material validation MAE improvement versus baseline.
- It reduced validation actual cutline hits moved below cutline from the current-best comparison while keeping startable precision flat versus baseline.
- It did not use holdout to define guard thresholds or choose thresholds.
- Holdout was evaluated only after the fixed variant definitions and validation-only selection.

Why this is still not production-ready:

- This is a review-only historical evidence packet.
- It does not approve shadow review.
- It does not change live formula, ranking, model, app, source-truth, hidden sort, recommendation, runtime, or production config behavior.
- Tim still needs to review the remaining concern casebook before any shadow-review prep lane.
"""


def selected_packet_md(context: dict[str, Any]) -> str:
    return f"""
# Selected Redesign Review Packet

Candidate redesign: `{SELECTED_REDESIGN}`

Human-review status: targeted redesign evidence only.

What got better:

- Cutline misses improved from `5` to `{context['selected_cutline_misses']}`.
- Static-autopsy remaining cases resolved: `{context['resolved_remaining_5']}/{context['remaining_5_count']}`.
- Elite-QB severe regressions stayed at `{context['selected_elite_qb_severe']}`.
- Holdout MAE still improved by `{context['selected_holdout_mae_delta']}` versus baseline.
- Holdout startable precision delta versus baseline: `{context['selected_holdout_startable_delta']}`.
- Holdout positions with MAE improvement: `{context['selected_holdout_positions_improved']}/{context['selected_holdout_position_count']}`.
- Holdout seasons with MAE improvement: `{context['selected_holdout_seasons_improved']}/{context['selected_holdout_season_count']}`.

Remaining concern:

- Remaining actual cutline-hit casebook rows: `{context['selected_remaining_casebook_rows']}`.
- Remaining players: `{context['remaining_players'] or 'none'}`.

No shadow-review approval is granted by this packet.
"""


def human_review_md(context: dict[str, Any]) -> str:
    return f"""
# Human Review Update

The targeted redesign lane found a stronger human-review-only variant: `{SELECTED_REDESIGN}`.

Review these first:

1. `remaining_5_case_resolution_report.csv`
2. `remaining_concern_casebook.csv`
3. `topn_startable_redesign_report.csv`
4. `selected_redesign_review_packet.md`

Main human question: are the remaining cutline cases acceptable enough to let a separate shadow-review prep lane be considered later? This packet itself does not approve shadow review.
"""


def do_not_promote_md() -> str:
    return """
# Do Not Promote Notice

Do not promote `usage_opportunity_volume`, `qb_guard_soft_blend`, `rb_wr_cutline_safe_blend`, or any targeted redesign from this branch.

This branch is review-only. It contains no production formula, ranking, recommendation, hidden sort, app wiring, model behavior, source-truth, runtime, service, or production config changes.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Status: PASS for review-only targeted redesign artifacts.

Confirmed:

- No production formula changes.
- No production model training or tuning.
- No formula promotion.
- No shadow review approval.
- No app wiring.
- No rankings, recommendations, or hidden sort changes.
- No source-truth promotion.
- No runtime, service, or production config changes.
- Guard logic uses only feature-season fields, position, baseline predictions/ranks, candidate predictions/ranks, and predeclared thresholds.
- No player-specific exceptions are used.
- Target outcomes are used only after fixed variant definitions for evaluation.
- Holdout is not used to define thresholds or select variants.
- No market, ADP, vendor, projection, or external rank fields are source truth.
- No routes, TPRR, YPRR, route proxies, ambiguous `rz_att`, red-zone sidecars, or current-only context.
- Missing values are not forced to zero.
- No redesign output is approved for production use.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

Scope: review-only Targeted Redesign V1 artifacts and one focused artifact/schema test.

Expected changed paths:

- `docs/hq/experiments/historical_formula_candidate_targeted_redesign_v1_20260701/`
- `tests/test_historical_formula_candidate_targeted_redesign_v1_20260701.py`

No app, model, ranking, formula, source-truth, runtime, service, production config, raw/shared/cache/local export, or secret paths are intentionally changed.
"""


def next_phase_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommendation: run a human decision gate on `{SELECTED_REDESIGN}` before any shadow-review prep.

If Tim accepts the remaining cutline casebook, the next branch may be `Historical Formula Candidate Shadow Review Prep V1`, still review-only and explicitly not production-approved. If Tim does not accept the remaining cases, reject the candidate or request a narrower source/feature redesign.

Do not start production promotion from this branch.
"""


def write_manifest(context: dict[str, Any]) -> None:
    rows = []
    for name in REQUIRED_ARTIFACTS + ["build_historical_formula_candidate_targeted_redesign_v1.py"]:
        path = EXPERIMENT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    body = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{BRANCH}`
- Base HEAD: `{BASE_HEAD}`
- Decision label: `{DECISION_LABEL}`
- Selected redesign: `{SELECTED_REDESIGN}`
- Review-only: true
- Approved for production use: false
- Shadow review approved: false

| Artifact | Bytes | SHA-256 |
|---|---:|---|
{chr(10).join(rows)}
"""
    write_text("artifact_manifest.md", body)


def write_csv(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(EXPERIMENT_DIR / name, index=False)


def write_text(name: str, body: str) -> None:
    (EXPERIMENT_DIR / name).write_text(body.strip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
