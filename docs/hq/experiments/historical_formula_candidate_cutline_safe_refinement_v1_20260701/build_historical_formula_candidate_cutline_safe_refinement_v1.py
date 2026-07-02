from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
V3_DIR = EXPERIMENT_DIR.parent / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
SOURCE_CONTRACT_DIR = EXPERIMENT_DIR.parent / "historical_tuning_source_contract_v1_20260701"
SEARCH_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_search_v1_20260701"
REVIEW_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_review_v1_20260701"
GATE_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_promotion_gate_prep_v1_20260701"
RESCUE_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_risk_rescue_sprint_v1_20260701"

SUBSTRATE_PATH = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
BASE_HEAD = "d3d9616bd0c7d5ce169efd5903f14e216ba2430d"
BRANCH = "work/historical-formula-candidate-cutline-safe-refinement-v1-20260701"
TARGET = "next_nwr_points"
BASELINE = "baseline_v3_prior_points"
ORIGINAL = "original_usage_opportunity_volume"
QB_GUARD = "qb_guard_soft_blend"
CONSERVATIVE = "conservative_blend_50"
SELECTED_PARTIAL = "rb_wr_cutline_safe_blend"
DECISION_LABEL = "PARTIAL_REFINEMENT_STILL_HOLD"
VERDICT = "YELLOW_CUTLINE_SAFE_REFINEMENT_PARTIAL_HOLD_REVIEW_ONLY"

ELITE_QB_POINTS_THRESHOLD = 250.0
ELITE_QB_GAMES_THRESHOLD = 12
CUTLINE_OUTSIDE_BAND = 3
STARTABLE_BAND = 3
SEVERE_REGRESSION_THRESHOLD = 20.0

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "cutline_safe_refinement_summary.md",
    "fixed_refinement_variant_definitions.csv",
    "validation_metric_comparison.csv",
    "holdout_metric_comparison.csv",
    "cutline_miss_comparison.csv",
    "elite_qb_regression_comparison.csv",
    "position_level_refinement_report.csv",
    "season_level_refinement_report.csv",
    "topn_startable_refinement_report.csv",
    "refinement_selection_decision.md",
    "selected_refinement_review_packet.md",
    "remaining_cutline_casebook.csv",
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
    Variant(
        BASELINE,
        "baseline_comparator",
        "prior_nwr_points",
        "none",
        "none",
        "prior_nwr_points",
    ),
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
        "elite-QB thresholds inherited from Risk Rescue Sprint V1; no holdout tuning",
        "feature-season position; prior_nwr_points; prior_games; baseline prediction output; original candidate prediction output",
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
        "qb_guard_plus_cutline_blend_50",
        "fixed_refinement",
        "Start from qb_guard_soft_blend; for cutline-band drops use 0.50 * baseline + 0.50 * qb_guard",
        "baseline predicted rank inside QB12/RB12/RB24/WR12/WR24/WR36/TE12 and qb_guard rank falls 1-3 slots outside that same cutline",
        "cutline outside band = 3, predeclared before evaluation",
        "feature-season position; baseline prediction and rank; qb_guard prediction and rank",
    ),
    Variant(
        "qb_guard_plus_cutline_blend_65",
        "fixed_refinement",
        "Start from qb_guard_soft_blend; for cutline-band drops use 0.35 * baseline + 0.65 * qb_guard",
        "baseline predicted rank inside QB12/RB12/RB24/WR12/WR24/WR36/TE12 and qb_guard rank falls 1-3 slots outside that same cutline",
        "cutline outside band = 3, predeclared before evaluation",
        "feature-season position; baseline prediction and rank; qb_guard prediction and rank",
    ),
    Variant(
        "qb_guard_plus_cutline_floor",
        "fixed_refinement",
        "Start from qb_guard_soft_blend; for any cutline drop apply row-level max(qb_guard, baseline)",
        "baseline predicted rank inside QB12/RB12/RB24/WR12/WR24/WR36/TE12 and qb_guard rank falls outside that same cutline",
        "baseline floor is predeclared; no holdout tuning",
        "feature-season position; baseline prediction and rank; qb_guard prediction and rank",
    ),
    Variant(
        SELECTED_PARTIAL,
        "fixed_refinement_selected_partial",
        "Start from qb_guard_soft_blend; RB/WR rows use 0.50 * baseline + 0.50 * qb_guard; QB/TE rows retain qb_guard",
        "position in RB/WR; no target-outcome condition",
        "fixed RB/WR-only protection because unresolved cutline misses were concentrated there",
        "feature-season position; baseline prediction output; qb_guard prediction output",
    ),
    Variant(
        "startable_band_blend",
        "fixed_refinement",
        "Start from qb_guard_soft_blend; if baseline rank is inside and within 3 slots of the startable boundary while qb_guard falls outside, use 0.50 * baseline + 0.50 * qb_guard",
        "baseline rank inside QB12/RB24/WR36/TE12, within 3 slots of boundary, and qb_guard rank falls outside",
        "startable band = 3, predeclared before evaluation",
        "feature-season position; baseline prediction and rank; qb_guard prediction and rank",
    ),
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    substrate = pd.read_parquet(SUBSTRATE_PATH)
    validate_inputs(substrate)
    scored = add_refinement_scores(add_splits(substrate.copy()))

    metric_comparison = build_metric_comparison(scored)
    validation_metrics = metric_comparison[metric_comparison["split"].eq("validation")].copy()
    holdout_metrics = metric_comparison[metric_comparison["split"].eq("holdout")].copy()
    cutline = build_cutline_miss_comparison(scored)
    elite_qb = build_elite_qb_comparison(scored)
    position = build_group_report(scored, ["split", "position"], "position")
    season = build_group_report(scored, ["split", "target_season"], "season")
    topn = build_topn_report(scored)
    remaining_casebook = build_remaining_cutline_casebook(scored, SELECTED_PARTIAL)
    regressions = build_largest_remaining_regressions(scored, SELECTED_PARTIAL)
    definitions = build_variant_definitions()

    write_csv(definitions, "fixed_refinement_variant_definitions.csv")
    write_csv(validation_metrics, "validation_metric_comparison.csv")
    write_csv(holdout_metrics, "holdout_metric_comparison.csv")
    write_csv(cutline, "cutline_miss_comparison.csv")
    write_csv(elite_qb, "elite_qb_regression_comparison.csv")
    write_csv(position, "position_level_refinement_report.csv")
    write_csv(season, "season_level_refinement_report.csv")
    write_csv(topn, "topn_startable_refinement_report.csv")
    write_csv(remaining_casebook, "remaining_cutline_casebook.csv")
    write_csv(regressions, "largest_remaining_regressions.csv")

    context = build_context(
        validation_metrics,
        holdout_metrics,
        cutline,
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
    print(f"selected_partial_refinement={SELECTED_PARTIAL}")
    return 0


def validate_inputs(substrate: pd.DataFrame) -> None:
    required_dirs = [SOURCE_CONTRACT_DIR, SEARCH_DIR, REVIEW_DIR, GATE_DIR, RESCUE_DIR]
    missing_dirs = [str(path) for path in required_dirs if not path.exists()]
    if missing_dirs:
        raise ValueError(f"Missing merged evidence directories: {missing_dirs}")
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
    ]
    if substrate[required_inputs].isna().any().any():
        raise ValueError("Primary refinement inputs contain null values; no zero-fill is applied")


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


def add_refinement_scores(frame: pd.DataFrame) -> pd.DataFrame:
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
    output[QB_GUARD] = output[ORIGINAL].where(
        ~elite_qb, 0.75 * output[BASELINE] + 0.25 * output[ORIGINAL]
    )
    output[CONSERVATIVE] = 0.50 * output[BASELINE] + 0.50 * output[ORIGINAL]
    output["baseline_prediction_rank"] = prediction_rank(output, BASELINE)
    output["qb_guard_prediction_rank"] = prediction_rank(output, QB_GUARD)

    cutline_band = cutline_drop_mask(output, outside_band=CUTLINE_OUTSIDE_BAND)
    any_cutline_drop = cutline_drop_mask(output, outside_band=None)
    startable_band = startable_band_drop_mask(output)
    rb_wr_rows = output["position"].isin(["RB", "WR"])

    output["cutline_band_guard_applies"] = cutline_band
    output["any_cutline_floor_guard_applies"] = any_cutline_drop
    output["startable_band_guard_applies"] = startable_band
    output["rb_wr_safe_blend_applies"] = rb_wr_rows

    output["qb_guard_plus_cutline_blend_50"] = output[QB_GUARD].where(
        ~cutline_band, 0.50 * output[BASELINE] + 0.50 * output[QB_GUARD]
    )
    output["qb_guard_plus_cutline_blend_65"] = output[QB_GUARD].where(
        ~cutline_band, 0.35 * output[BASELINE] + 0.65 * output[QB_GUARD]
    )
    output["qb_guard_plus_cutline_floor"] = output[QB_GUARD].where(
        ~any_cutline_drop, pd.concat([output[BASELINE], output[QB_GUARD]], axis=1).max(axis=1)
    )
    output[SELECTED_PARTIAL] = output[QB_GUARD].where(
        ~rb_wr_rows, 0.50 * output[BASELINE] + 0.50 * output[QB_GUARD]
    )
    output["startable_band_blend"] = output[QB_GUARD].where(
        ~startable_band, 0.50 * output[BASELINE] + 0.50 * output[QB_GUARD]
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


def elite_qb_mask(frame: pd.DataFrame) -> pd.Series:
    return (
        frame["position"].eq("QB")
        & num(frame, "prior_nwr_points").ge(ELITE_QB_POINTS_THRESHOLD)
        & num(frame, "prior_games").ge(ELITE_QB_GAMES_THRESHOLD)
    )


def cutline_drop_mask(frame: pd.DataFrame, *, outside_band: int | None) -> pd.Series:
    mask = pd.Series(False, index=frame.index)
    for position, cutlines in bucket_cutlines().items():
        position_rows = frame["position"].eq(position)
        for cutline in cutlines:
            dropped = (
                position_rows
                & frame["baseline_prediction_rank"].le(cutline)
                & frame["qb_guard_prediction_rank"].gt(cutline)
            )
            if outside_band is not None:
                dropped = dropped & frame["qb_guard_prediction_rank"].le(cutline + outside_band)
            mask = mask | dropped
    return mask


def startable_band_drop_mask(frame: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=frame.index)
    for position, boundary in startable_boundaries().items():
        position_rows = frame["position"].eq(position)
        dropped = (
            position_rows
            & frame["baseline_prediction_rank"].le(boundary)
            & frame["baseline_prediction_rank"].ge(boundary - STARTABLE_BAND)
            & frame["qb_guard_prediction_rank"].gt(boundary)
        )
        mask = mask | dropped
    return mask


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
    rows = []
    for variant in VARIANTS:
        rows.append(
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
                "review_only": True,
                "approved_for_production_use": False,
                "shadow_review_approved": False,
            }
        )
    return pd.DataFrame(rows)


def build_metric_comparison(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout"]:
        subset = scored[scored["split"].eq(split)].copy()
        baseline = metric_row(subset, BASELINE, split, "all_positions")
        original = metric_row(subset, ORIGINAL, split, "all_positions")
        qb_guard = metric_row(subset, QB_GUARD, split, "all_positions")
        conservative = metric_row(subset, CONSERVATIVE, split, "all_positions")
        for candidate_id in variant_ids():
            row = metric_row(subset, candidate_id, split, "all_positions")
            row.update(comparison_deltas(row, baseline, original, qb_guard, conservative))
            row["selection_policy"] = "validation_only" if split == "validation" else "one_time_holdout_after_fixed_definitions"
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
    conservative: dict[str, Any],
) -> dict[str, Any]:
    return {
        "mae_delta_vs_baseline": round(float(row["mae"]) - float(baseline["mae"]), 6),
        "mae_delta_vs_original": round(float(row["mae"]) - float(original["mae"]), 6),
        "mae_delta_vs_qb_guard": round(float(row["mae"]) - float(qb_guard["mae"]), 6),
        "mae_delta_vs_conservative_blend_50": round(float(row["mae"]) - float(conservative["mae"]), 6),
        "spearman_delta_vs_baseline": round(float(row["spearman"]) - float(baseline["spearman"]), 6),
        "spearman_delta_vs_qb_guard": round(float(row["spearman"]) - float(qb_guard["spearman"]), 6),
        "startable_precision_delta_vs_baseline": round(
            float(row["startable_precision_at_n"]) - float(baseline["startable_precision_at_n"]), 6
        ),
        "startable_precision_delta_vs_qb_guard": round(
            float(row["startable_precision_at_n"]) - float(qb_guard["startable_precision_at_n"]), 6
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
            baseline_in = baseline_rank <= cutline
            candidate_in = candidate_rank <= cutline
            actual_in = actual_finish <= cutline
            below = baseline_in & ~candidate_in
            moved_below += int(below.sum())
            actual_hits_moved_below += int((below & actual_in).sum())
    return {
        "candidate_id": candidate_id,
        "split": split,
        "moved_below_cutline_count": moved_below,
        "actual_hits_moved_below_cutline": actual_hits_moved_below,
        "guard_uses_target_outcomes": False,
    }


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
        conservative = metric_row(group, CONSERVATIVE, split, "group")
        for candidate_id in variant_ids():
            row = metric_row(group, candidate_id, split, "group")
            row.update(comparison_deltas(row, baseline, original, qb_guard, conservative))
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
    baseline = baseline.rename(columns={"precision": "baseline_precision", "recall": "baseline_recall", "f1": "baseline_f1"})
    qb_guard = output[output["candidate_id"].eq(QB_GUARD)][["split", "position", "bucket", "precision", "recall", "f1"]]
    qb_guard = qb_guard.rename(columns={"precision": "qb_guard_precision", "recall": "qb_guard_recall", "f1": "qb_guard_f1"})
    output = output.merge(baseline, on=["split", "position", "bucket"], how="left")
    output = output.merge(qb_guard, on=["split", "position", "bucket"], how="left")
    for metric in ["precision", "recall", "f1"]:
        output[f"{metric}_delta_vs_baseline"] = (output[metric] - output[f"baseline_{metric}"]).round(6)
        output[f"{metric}_delta_vs_qb_guard"] = (output[metric] - output[f"qb_guard_{metric}"]).round(6)
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
        qb_guard_rank = group[QB_GUARD].rank(method="first", ascending=False)
        actual_finish = num(group, "next_position_finish")
        for cutline in bucket_cutlines().get(position, []):
            baseline_in = baseline_rank <= cutline
            candidate_in = candidate_rank <= cutline
            actual_in = actual_finish <= cutline
            miss = baseline_in & ~candidate_in & actual_in
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
                        "qb_guard_rank": int(qb_guard_rank.loc[idx]),
                        "selected_refinement_rank": int(candidate_rank.loc[idx]),
                        "actual_position_finish": int(row["next_position_finish"]),
                        "baseline_prediction": round(float(row[BASELINE]), 6),
                        "qb_guard_prediction": round(float(row[QB_GUARD]), 6),
                        "selected_refinement_prediction": round(float(row[candidate_id]), 6),
                        "actual_next_points": round(float(row[TARGET]), 6),
                        "review_note": "Remaining actual cutline hit moved below cutline by selected partial refinement.",
                    }
                )
    return pd.DataFrame(rows).sort_values(["target_season", "position", "cutline", "baseline_rank"])


def build_largest_remaining_regressions(scored: pd.DataFrame, candidate_id: str) -> pd.DataFrame:
    review = scored[scored["split"].isin(["validation", "holdout"])].copy()
    output = review.copy()
    output["baseline_error"] = (num(output, BASELINE) - num(output, TARGET)).abs()
    output["qb_guard_error"] = (num(output, QB_GUARD) - num(output, TARGET)).abs()
    output["selected_refinement_error"] = (num(output, candidate_id) - num(output, TARGET)).abs()
    output["selected_error_delta_vs_baseline"] = output["selected_refinement_error"] - output["baseline_error"]
    output["selected_error_delta_vs_qb_guard"] = output["selected_refinement_error"] - output["qb_guard_error"]
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
        QB_GUARD,
        candidate_id,
        "actual_next_points",
        "baseline_error",
        "qb_guard_error",
        "selected_refinement_error",
        "selected_error_delta_vs_baseline",
        "selected_error_delta_vs_qb_guard",
    ]
    return output[columns]


def build_context(
    validation: pd.DataFrame,
    holdout: pd.DataFrame,
    cutline: pd.DataFrame,
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
        (position["candidate_id"].eq(SELECTED_PARTIAL)) & (position["split"].eq("holdout"))
    ].copy()
    selected_holdout_seasons = season[
        (season["candidate_id"].eq(SELECTED_PARTIAL)) & (season["split"].eq("holdout"))
    ].copy()
    context = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT,
        "decision_label": DECISION_LABEL,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "selected_partial": SELECTED_PARTIAL,
        "original_validation_mae_delta": val.loc[ORIGINAL, "mae_delta_vs_baseline"],
        "original_holdout_mae_delta": hold.loc[ORIGINAL, "mae_delta_vs_baseline"],
        "qb_guard_validation_mae_delta": val.loc[QB_GUARD, "mae_delta_vs_baseline"],
        "qb_guard_holdout_mae_delta": hold.loc[QB_GUARD, "mae_delta_vs_baseline"],
        "selected_validation_mae_delta": val.loc[SELECTED_PARTIAL, "mae_delta_vs_baseline"],
        "selected_holdout_mae_delta": hold.loc[SELECTED_PARTIAL, "mae_delta_vs_baseline"],
        "selected_holdout_spearman_delta": hold.loc[SELECTED_PARTIAL, "spearman_delta_vs_baseline"],
        "selected_validation_startable_delta": val.loc[SELECTED_PARTIAL, "startable_precision_delta_vs_baseline"],
        "selected_holdout_startable_delta": hold.loc[SELECTED_PARTIAL, "startable_precision_delta_vs_baseline"],
        "original_cutline_misses": int(cuts.loc[ORIGINAL, "actual_hits_moved_below_cutline"]),
        "qb_guard_cutline_misses": int(cuts.loc[QB_GUARD, "actual_hits_moved_below_cutline"]),
        "conservative_cutline_misses": int(cuts.loc[CONSERVATIVE, "actual_hits_moved_below_cutline"]),
        "selected_cutline_misses": int(cuts.loc[SELECTED_PARTIAL, "actual_hits_moved_below_cutline"]),
        "original_elite_qb_severe": int(elite.loc[ORIGINAL, "severe_regression_count"]),
        "qb_guard_elite_qb_severe": int(elite.loc[QB_GUARD, "severe_regression_count"]),
        "selected_elite_qb_severe": int(elite.loc[SELECTED_PARTIAL, "severe_regression_count"]),
        "selected_holdout_positions_improved": int(selected_holdout_positions["mae_delta_vs_baseline"].lt(0).sum()),
        "selected_holdout_position_count": int(len(selected_holdout_positions)),
        "selected_holdout_seasons_improved": int(selected_holdout_seasons["mae_delta_vs_baseline"].lt(0).sum()),
        "selected_holdout_season_count": int(len(selected_holdout_seasons)),
        "remaining_cutline_rows": int(len(remaining_casebook)),
        "largest_regression_player": str(regressions.iloc[0]["player_name"]) if not regressions.empty else "",
    }
    return context


def write_markdown_reports(context: dict[str, Any]) -> None:
    reports = {
        "cutline_safe_refinement_summary.md": summary_md(context),
        "refinement_selection_decision.md": selection_md(context),
        "selected_refinement_review_packet.md": selected_packet_md(context),
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
# Historical Formula Candidate Cutline-Safe Refinement V1

Verdict: `{context['verdict']}`

Decision label: `{context['decision_label']}`

Selected partial refinement: `{context['selected_partial']}`

This lane tested only fixed, interpretable cutline-safe variants of the existing `usage_opportunity_volume` candidate. It did not run unbounded search, train a model, change production formulas, approve shadow review, or wire output into NWR.

## Key Evidence

- Original validation MAE delta: `{context['original_validation_mae_delta']}`
- Original holdout MAE delta: `{context['original_holdout_mae_delta']}`
- `qb_guard_soft_blend` validation MAE delta: `{context['qb_guard_validation_mae_delta']}`
- `qb_guard_soft_blend` holdout MAE delta: `{context['qb_guard_holdout_mae_delta']}`
- `{context['selected_partial']}` validation MAE delta: `{context['selected_validation_mae_delta']}`
- `{context['selected_partial']}` holdout MAE delta: `{context['selected_holdout_mae_delta']}`
- `{context['selected_partial']}` holdout Spearman delta: `{context['selected_holdout_spearman_delta']}`
- `{context['selected_partial']}` validation/holdout startable precision delta: `{context['selected_validation_startable_delta']}` / `{context['selected_holdout_startable_delta']}`
- Actual cutline hits moved below cutline: original `{context['original_cutline_misses']}`, `qb_guard_soft_blend` `{context['qb_guard_cutline_misses']}`, selected partial `{context['selected_cutline_misses']}`
- Elite-QB severe regressions: original `{context['original_elite_qb_severe']}`, `qb_guard_soft_blend` `{context['qb_guard_elite_qb_severe']}`, selected partial `{context['selected_elite_qb_severe']}`

Conclusion: the selected partial refinement improves cutline safety toward the preferred target and keeps elite-QB regressions low, but it introduces a small startable-precision regression and weaker holdout MAE than `qb_guard_soft_blend`. The candidate remains HOLD.
"""


def selection_md(context: dict[str, Any]) -> str:
    return f"""
# Refinement Selection Decision

Decision label: `{DECISION_LABEL}`

Validation-only selection logic:

- The selected partial refinement had validation MAE improvement versus baseline.
- It was the fixed refinement that reduced validation cutline misses while preserving the elite-QB guard.
- Holdout was evaluated only after fixed definitions and the validation-only partial selection.

Selected partial refinement: `{SELECTED_PARTIAL}`.

Why this is not marked `REFINED_CANDIDATE_FOR_HUMAN_REVIEW_ONLY`:

- Holdout MAE still improves versus baseline, but less than `qb_guard_soft_blend`.
- Actual cutline misses improve from `{context['qb_guard_cutline_misses']}` to `{context['selected_cutline_misses']}`.
- Elite-QB severe regressions stay near the desired level at `{context['selected_elite_qb_severe']}`.
- Startable precision regresses slightly on validation and holdout, so the full success criteria are not met.

Result: `PARTIAL_REFINEMENT_STILL_HOLD`.
"""


def selected_packet_md(context: dict[str, Any]) -> str:
    return f"""
# Selected Refinement Review Packet

Candidate: `{SELECTED_PARTIAL}`

Human-review status: partial evidence only, still HOLD.

What got better:

- Cutline misses improved from `8` to `{context['selected_cutline_misses']}`.
- Elite-QB severe regressions stayed at `{context['selected_elite_qb_severe']}`.
- Holdout MAE still improved by `{context['selected_holdout_mae_delta']}` versus baseline.
- Holdout positions with MAE improvement: `{context['selected_holdout_positions_improved']}/{context['selected_holdout_position_count']}`.
- Holdout seasons with MAE improvement: `{context['selected_holdout_seasons_improved']}/{context['selected_holdout_season_count']}`.

What still blocks advancement:

- Startable precision regressed slightly.
- Holdout MAE gain is weaker than the prior `qb_guard_soft_blend` rescue.
- Remaining cutline casebook rows still require Tim review.

No shadow-review approval is granted by this packet.
"""


def human_review_md(context: dict[str, Any]) -> str:
    return f"""
# Human Review Update

The refinement lane found a partial, interpretable risk reducer: `{SELECTED_PARTIAL}`.

Review these first:

1. `remaining_cutline_casebook.csv`
2. `largest_remaining_regressions.csv`
3. `topn_startable_refinement_report.csv`
4. `selected_refinement_review_packet.md`

Main human question: is the cutline improvement from `8` to `{context['selected_cutline_misses']}` enough to justify accepting the smaller startable-precision regression, or should the candidate remain held/rejected?
"""


def do_not_promote_md() -> str:
    return """
# Do Not Promote Notice

Do not promote `usage_opportunity_volume`, `qb_guard_soft_blend`, or any cutline-safe refinement from this branch.

This branch is review-only. It contains no production formula, ranking, recommendation, hidden sort, app wiring, model behavior, source-truth, runtime, service, or production config changes.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Status: PASS for review-only cutline-safe refinement artifacts.

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
- Target outcomes are used only after fixed variant definitions for evaluation.
- Holdout is not used to define thresholds or select variants.
- No market, ADP, vendor, projection, or external rank fields are source truth.
- No routes, TPRR, YPRR, route proxies, ambiguous `rz_att`, red-zone sidecars, or current-only context.
- Missing values are not forced to zero.
- No candidate/refinement output is approved for production use.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

Scope: review-only Cutline-Safe Refinement V1 artifacts and one focused artifact/schema test.

Expected changed paths:

- `docs/hq/experiments/historical_formula_candidate_cutline_safe_refinement_v1_20260701/`
- `tests/test_historical_formula_candidate_cutline_safe_refinement_v1_20260701.py`

No app, model, ranking, formula, source-truth, runtime, service, production config, raw/shared/cache/local export, or secret paths are intentionally changed.
"""


def next_phase_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommendation: keep candidate refinement on HOLD for Tim review.

If Tim accepts the cutline/startable tradeoff, a future branch may prepare a shadow-review proposal, still review-only and explicitly not production-approved. If Tim does not accept the tradeoff, reject the candidate or request a narrower cutline casebook review.

Do not start production promotion from this branch.
"""


def write_manifest(context: dict[str, Any]) -> None:
    rows = []
    for name in REQUIRED_ARTIFACTS + ["build_historical_formula_candidate_cutline_safe_refinement_v1.py"]:
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
- Selected partial refinement: `{SELECTED_PARTIAL}`
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
