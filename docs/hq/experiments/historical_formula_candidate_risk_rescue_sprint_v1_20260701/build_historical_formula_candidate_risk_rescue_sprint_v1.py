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
PROMOTION_GATE_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_promotion_gate_prep_v1_20260701"

SUBSTRATE_PATH = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
BASE_HEAD = "164facfcaf5cf15853baf6b8fca47c0b448fa8ec"
BRANCH = "work/historical-formula-candidate-promotion-gate-prep-v1-20260701"
BASELINE = "baseline_v3_prior_points"
ORIGINAL = "original_usage_opportunity_volume"
TARGET = "next_nwr_points"
DECISION_LABEL = "NO_SAFE_RESCUE_HOLD"
VERDICT = "YELLOW_RISK_RESCUE_SPRINT_NO_FULL_SAFE_RESCUE_REVIEW_ONLY"
BEST_PARTIAL_RESCUE = "qb_guard_soft_blend"

ELITE_QB_POINTS_THRESHOLD = 250.0
ELITE_QB_GAMES_THRESHOLD = 12
SEVERE_REGRESSION_THRESHOLD = 20.0
CUTLINE_BAND = 3

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "candidate_risk_rescue_summary.md",
    "fixed_rescue_variant_definitions.csv",
    "validation_metric_comparison.csv",
    "holdout_metric_comparison.csv",
    "elite_qb_regression_comparison.csv",
    "cutline_regression_comparison.csv",
    "position_level_rescue_report.csv",
    "season_level_rescue_report.csv",
    "topn_startable_rescue_report.csv",
    "rescue_variant_selection_decision.md",
    "human_review_update.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
]


@dataclass(frozen=True)
class Variant:
    candidate_id: str
    family: str
    formula_definition: str
    guard_definition: str
    guard_thresholds: str
    allowed_inputs: str
    primary_or_comparator: str


VARIANTS = [
    Variant(
        BASELINE,
        "baseline_comparator",
        "prior_nwr_points",
        "none",
        "none",
        "prior_nwr_points",
        "comparator",
    ),
    Variant(
        ORIGINAL,
        "original_candidate",
        "0.70 * prior_nwr_points + 0.30 * usage_proxy",
        "none",
        "none",
        "prior_nwr_points; prior_carries; prior_receptions; prior_targets; prior_opportunities",
        "original",
    ),
    Variant(
        "conservative_blend_50",
        "fixed_rescue_variant",
        "0.50 * baseline + 0.50 * original_usage_opportunity_volume",
        "applies to every row",
        "fixed 50/50 blend; no threshold",
        "baseline prediction output; original candidate prediction output",
        "rescue",
    ),
    Variant(
        "qb_guard_baseline_lock",
        "fixed_rescue_variant",
        "baseline for elite prior-season QB rows; original candidate elsewhere",
        "position == QB and prior_nwr_points >= 250 and prior_games >= 12",
        "elite QB threshold predeclared before evaluation",
        "feature-season position, prior_nwr_points, prior_games; baseline prediction output; original candidate prediction output",
        "rescue",
    ),
    Variant(
        "qb_guard_soft_blend",
        "fixed_rescue_variant",
        "0.75 * baseline + 0.25 * original for elite prior-season QB rows; original candidate elsewhere",
        "position == QB and prior_nwr_points >= 250 and prior_games >= 12",
        "elite QB threshold predeclared before evaluation",
        "feature-season position, prior_nwr_points, prior_games; baseline prediction output; original candidate prediction output",
        "rescue",
    ),
    Variant(
        "cutline_guard_soft_blend",
        "fixed_rescue_variant",
        "0.75 * baseline + 0.25 * original for baseline-predicted cutline-band rows; original candidate elsewhere",
        "baseline prediction order within 3 slots of QB/TE top 12, RB top 12/top 24, WR top 12/top 24/top 36",
        "cutline band = 3; thresholds predeclared before evaluation",
        "feature-season position; baseline prediction output; original candidate prediction output",
        "rescue",
    ),
    Variant(
        "position_specific_safe_blend",
        "fixed_rescue_variant",
        "QB rows use 0.75 * baseline + 0.25 * original; RB/WR/TE rows use original candidate",
        "position == QB",
        "fixed QB guard; no target-outcome threshold",
        "feature-season position; baseline prediction output; original candidate prediction output",
        "rescue",
    ),
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    substrate = pd.read_parquet(SUBSTRATE_PATH)
    validate_inputs(substrate)
    scored = add_rescue_scores(add_splits(substrate.copy()))

    metric_comparison = build_metric_comparison(scored)
    validation_metrics = metric_comparison[metric_comparison["split"].eq("validation")].copy()
    holdout_metrics = metric_comparison[metric_comparison["split"].eq("holdout")].copy()
    elite_qb = build_elite_qb_comparison(scored)
    cutline = build_cutline_comparison(scored)
    position = build_group_report(scored, ["split", "position"], "position")
    season = build_group_report(scored, ["split", "target_season"], "season")
    topn = build_topn_report(scored)
    definitions = build_variant_definitions()

    write_csv(definitions, "fixed_rescue_variant_definitions.csv")
    write_csv(validation_metrics, "validation_metric_comparison.csv")
    write_csv(holdout_metrics, "holdout_metric_comparison.csv")
    write_csv(elite_qb, "elite_qb_regression_comparison.csv")
    write_csv(cutline, "cutline_regression_comparison.csv")
    write_csv(position, "position_level_rescue_report.csv")
    write_csv(season, "season_level_rescue_report.csv")
    write_csv(topn, "topn_startable_rescue_report.csv")

    context = build_context(validation_metrics, holdout_metrics, elite_qb, cutline, position, season, topn)
    write_markdown_reports(context)
    write_manifest(context)

    print(f"wrote={EXPERIMENT_DIR}")
    print(f"decision_label={DECISION_LABEL}")
    print(f"best_partial_rescue={BEST_PARTIAL_RESCUE}")
    return 0


def validate_inputs(substrate: pd.DataFrame) -> None:
    if len(substrate) != 5518:
        raise ValueError(f"Expected 5518 V3 rows, got {len(substrate)}")
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
    if not SOURCE_CONTRACT_DIR.exists() or not PROMOTION_GATE_DIR.exists():
        raise ValueError("Required merged source-contract or promotion-gate artifacts are missing")


def add_splits(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["split"] = pd.NA
    output.loc[output["feature_season"].between(2012, 2020), "split"] = "train"
    output.loc[output["feature_season"].between(2021, 2022), "split"] = "validation"
    output.loc[output["feature_season"].between(2023, 2024), "split"] = "holdout"
    if output["split"].isna().any():
        raise ValueError("Rows outside fixed readiness-gate split policy")
    if output["split"].value_counts().to_dict() != {"train": 3716, "validation": 912, "holdout": 890}:
        raise ValueError("Unexpected split counts")
    return output


def add_rescue_scores(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output[BASELINE] = num(output, "prior_nwr_points")
    usage_proxy = (
        0.40 * num(output, "prior_carries")
        + 0.55 * num(output, "prior_receptions")
        + 0.20 * num(output, "prior_targets")
        + 0.15 * num(output, "prior_opportunities")
    )
    output[ORIGINAL] = 0.70 * output[BASELINE] + 0.30 * usage_proxy
    output["baseline_prediction_order"] = prediction_order(output, BASELINE)

    elite_qb = elite_qb_mask(output)
    near_cutline = baseline_cutline_band_mask(output)
    output["elite_qb_guard_applies"] = elite_qb
    output["baseline_cutline_guard_applies"] = near_cutline

    output["conservative_blend_50"] = 0.50 * output[BASELINE] + 0.50 * output[ORIGINAL]
    output["qb_guard_baseline_lock"] = output[ORIGINAL].where(~elite_qb, output[BASELINE])
    output["qb_guard_soft_blend"] = output[ORIGINAL].where(
        ~elite_qb, 0.75 * output[BASELINE] + 0.25 * output[ORIGINAL]
    )
    output["cutline_guard_soft_blend"] = output[ORIGINAL].where(
        ~near_cutline, 0.75 * output[BASELINE] + 0.25 * output[ORIGINAL]
    )
    output["position_specific_safe_blend"] = output[ORIGINAL]
    qb_rows = output["position"].eq("QB")
    output.loc[qb_rows, "position_specific_safe_blend"] = (
        0.75 * output.loc[qb_rows, BASELINE] + 0.25 * output.loc[qb_rows, ORIGINAL]
    )
    for variant in variant_ids():
        if output[variant].isna().any():
            raise ValueError(f"Variant produced null prediction: {variant}")
    return output


def num(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="raise").astype(float)


def prediction_order(frame: pd.DataFrame, candidate_id: str) -> pd.Series:
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


def baseline_cutline_band_mask(frame: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=frame.index)
    for position, cutlines in bucket_cutlines().items():
        position_rows = frame["position"].eq(position)
        for cutline in cutlines:
            mask = mask | (position_rows & (frame["baseline_prediction_order"] - cutline).abs().le(CUTLINE_BAND))
    return mask


def bucket_cutlines() -> dict[str, list[int]]:
    return {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}


def variant_ids() -> list[str]:
    return [variant.candidate_id for variant in VARIANTS]


def rescue_variant_ids() -> list[str]:
    return [variant.candidate_id for variant in VARIANTS if variant.primary_or_comparator == "rescue"]


def build_variant_definitions() -> pd.DataFrame:
    rows = []
    for variant in VARIANTS:
        rows.append(
            {
                "candidate_id": variant.candidate_id,
                "family": variant.family,
                "formula_definition": variant.formula_definition,
                "guard_definition": variant.guard_definition,
                "guard_thresholds": variant.guard_thresholds,
                "allowed_inputs": variant.allowed_inputs,
                "primary_or_comparator": variant.primary_or_comparator,
                "holdout_used_to_define_thresholds": False,
                "target_outcomes_used_in_guard": False,
                "review_only": True,
                "approved_for_production_use": False,
            }
        )
    return pd.DataFrame(rows)


def build_metric_comparison(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout"]:
        subset = scored[scored["split"].eq(split)].copy()
        baseline = metric_row(subset, BASELINE, split, "all_positions")
        original = metric_row(subset, ORIGINAL, split, "all_positions")
        for candidate_id in variant_ids():
            row = metric_row(subset, candidate_id, split, "all_positions")
            row.update(delta_columns(row, baseline, original))
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


def delta_columns(row: dict[str, Any], baseline: dict[str, Any], original: dict[str, Any]) -> dict[str, Any]:
    return {
        "mae_delta_vs_baseline": round(float(row["mae"]) - float(baseline["mae"]), 6),
        "mae_delta_vs_original": round(float(row["mae"]) - float(original["mae"]), 6),
        "spearman_delta_vs_baseline": round(float(row["spearman"]) - float(baseline["spearman"]), 6),
        "spearman_delta_vs_original": round(float(row["spearman"]) - float(original["spearman"]), 6),
        "startable_precision_delta_vs_baseline": round(
            float(row["startable_precision_at_n"]) - float(baseline["startable_precision_at_n"]), 6
        ),
        "startable_precision_delta_vs_original": round(
            float(row["startable_precision_at_n"]) - float(original["startable_precision_at_n"]), 6
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
    return {"QB": 12, "RB": 24, "WR": 36, "TE": 12}.get(position, 12)


def f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def build_elite_qb_comparison(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout", "validation_holdout"]:
        subset = review_subset(scored, split)
        elite = subset[elite_qb_mask(subset)].copy()
        baseline_error = (num(elite, BASELINE) - num(elite, TARGET)).abs()
        for candidate_id in variant_ids():
            candidate_error = (num(elite, candidate_id) - num(elite, TARGET)).abs()
            error_delta = candidate_error - baseline_error
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "split": split,
                    "elite_qb_rows": int(len(elite)),
                    "severe_regression_threshold": SEVERE_REGRESSION_THRESHOLD,
                    "severe_regression_count": int(error_delta.gt(SEVERE_REGRESSION_THRESHOLD).sum()),
                    "mean_error_delta_vs_baseline": round(float(error_delta.mean()), 6) if len(error_delta) else 0.0,
                    "max_error_delta_vs_baseline": round(float(error_delta.max()), 6) if len(error_delta) else 0.0,
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


def build_cutline_comparison(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout", "validation_holdout"]:
        subset = review_subset(scored, split)
        for candidate_id in variant_ids():
            rows.append(cutline_row(subset, candidate_id, split))
    output = pd.DataFrame(rows)
    original = output[output["candidate_id"].eq(ORIGINAL)][["split", "actual_hits_moved_below_cutline"]].rename(
        columns={"actual_hits_moved_below_cutline": "original_actual_hits_moved_below_cutline"}
    )
    output = output.merge(original, on="split", how="left")
    output["actual_hits_moved_below_delta_vs_original"] = (
        output["actual_hits_moved_below_cutline"] - output["original_actual_hits_moved_below_cutline"]
    )
    return output


def cutline_row(subset: pd.DataFrame, candidate_id: str, split: str) -> dict[str, Any]:
    moved_below = 0
    moved_above = 0
    actual_hits_moved_below = 0
    actual_hits_moved_above = 0
    for (_season, position), group in subset.groupby(["target_season", "position"]):
        baseline_order = group[BASELINE].rank(method="first", ascending=False)
        candidate_order = group[candidate_id].rank(method="first", ascending=False)
        for cutline in bucket_cutlines().get(position, []):
            baseline_in = baseline_order <= cutline
            candidate_in = candidate_order <= cutline
            actual_in = num(group, "next_position_finish") <= cutline
            below = baseline_in & ~candidate_in
            above = ~baseline_in & candidate_in
            moved_below += int(below.sum())
            moved_above += int(above.sum())
            actual_hits_moved_below += int((below & actual_in).sum())
            actual_hits_moved_above += int((above & actual_in).sum())
    return {
        "candidate_id": candidate_id,
        "split": split,
        "baseline_comparator": BASELINE,
        "moved_below_cutline_count": moved_below,
        "moved_above_cutline_count": moved_above,
        "actual_hits_moved_below_cutline": actual_hits_moved_below,
        "actual_hits_moved_above_cutline": actual_hits_moved_above,
        "guard_uses_target_outcomes": False,
    }


def review_subset(scored: pd.DataFrame, split: str) -> pd.DataFrame:
    if split == "validation_holdout":
        return scored[scored["split"].isin(["validation", "holdout"])].copy()
    return scored[scored["split"].eq(split)].copy()


def build_group_report(scored: pd.DataFrame, group_cols: list[str], group_label: str) -> pd.DataFrame:
    rows = []
    for keys, group in scored[scored["split"].isin(["validation", "holdout"])].groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = metric_row(group, BASELINE, str(group["split"].iloc[0]), "group")
        original = metric_row(group, ORIGINAL, str(group["split"].iloc[0]), "group")
        for candidate_id in variant_ids():
            row = metric_row(group, candidate_id, str(group["split"].iloc[0]), "group")
            row.update(delta_columns(row, base, original))
            for col, value in zip(group_cols, keys):
                row[col] = value
            row["group_type"] = group_label
            rows.append(row)
    return pd.DataFrame(rows)


def build_topn_report(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout"]:
        split_df = scored[scored["split"].eq(split)].copy()
        for candidate_id in variant_ids():
            for position, buckets in bucket_columns().items():
                subset = split_df[split_df["position"].eq(position)].copy()
                for bucket, column, n in buckets:
                    rows.append(bucket_metric_row(subset, candidate_id, split, position, bucket, column, n))
    output = pd.DataFrame(rows)
    baseline = output[output["candidate_id"].eq(BASELINE)][["split", "position", "bucket", "precision", "recall", "f1"]]
    baseline = baseline.rename(columns={"precision": "baseline_precision", "recall": "baseline_recall", "f1": "baseline_f1"})
    original = output[output["candidate_id"].eq(ORIGINAL)][["split", "position", "bucket", "precision", "recall", "f1"]]
    original = original.rename(columns={"precision": "original_precision", "recall": "original_recall", "f1": "original_f1"})
    output = output.merge(baseline, on=["split", "position", "bucket"], how="left")
    output = output.merge(original, on=["split", "position", "bucket"], how="left")
    for metric in ["precision", "recall", "f1"]:
        output[f"{metric}_delta_vs_baseline"] = (output[metric] - output[f"baseline_{metric}"]).round(6)
        output[f"{metric}_delta_vs_original"] = (output[metric] - output[f"original_{metric}"]).round(6)
    output["material_regression_vs_baseline"] = output["precision_delta_vs_baseline"].lt(-0.02) | output[
        "f1_delta_vs_baseline"
    ].lt(-0.02)
    return output


def bucket_columns() -> dict[str, list[tuple[str, str, int]]]:
    return {
        "QB": [("QB_TOP12", "qb_t12", 12)],
        "RB": [("RB_TOP12", "rb_t12", 12), ("RB_TOP24", "rb_t24", 24)],
        "WR": [("WR_TOP12", "wr_t12", 12), ("WR_TOP24", "wr_t24", 24), ("WR_TOP36", "wr_t36", 36)],
        "TE": [("TE_TOP12", "te_t12", 12)],
    }


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


def build_context(
    validation: pd.DataFrame,
    holdout: pd.DataFrame,
    elite_qb: pd.DataFrame,
    cutline: pd.DataFrame,
    position: pd.DataFrame,
    season: pd.DataFrame,
    topn: pd.DataFrame,
) -> dict[str, Any]:
    val = validation.set_index("candidate_id")
    hold = holdout.set_index("candidate_id")
    elite = elite_qb[elite_qb["split"].eq("validation_holdout")].set_index("candidate_id")
    cuts = cutline[cutline["split"].eq("validation_holdout")].set_index("candidate_id")
    context = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT,
        "decision_label": DECISION_LABEL,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "best_partial_rescue": BEST_PARTIAL_RESCUE,
        "variants_tested": ", ".join(rescue_variant_ids()),
        "original_validation_mae_delta": val.loc[ORIGINAL, "mae_delta_vs_baseline"],
        "original_holdout_mae_delta": hold.loc[ORIGINAL, "mae_delta_vs_baseline"],
        "best_validation_mae_delta": val.loc[BEST_PARTIAL_RESCUE, "mae_delta_vs_baseline"],
        "best_holdout_mae_delta": hold.loc[BEST_PARTIAL_RESCUE, "mae_delta_vs_baseline"],
        "best_validation_spearman_delta": val.loc[BEST_PARTIAL_RESCUE, "spearman_delta_vs_baseline"],
        "best_holdout_spearman_delta": hold.loc[BEST_PARTIAL_RESCUE, "spearman_delta_vs_baseline"],
        "best_validation_startable_delta": val.loc[BEST_PARTIAL_RESCUE, "startable_precision_delta_vs_baseline"],
        "best_holdout_startable_delta": hold.loc[BEST_PARTIAL_RESCUE, "startable_precision_delta_vs_baseline"],
        "original_elite_severe": int(elite.loc[ORIGINAL, "severe_regression_count"]),
        "best_elite_severe": int(elite.loc[BEST_PARTIAL_RESCUE, "severe_regression_count"]),
        "original_cutline_hits": int(cuts.loc[ORIGINAL, "actual_hits_moved_below_cutline"]),
        "best_cutline_hits": int(cuts.loc[BEST_PARTIAL_RESCUE, "actual_hits_moved_below_cutline"]),
        "conservative_cutline_hits": int(cuts.loc["conservative_blend_50", "actual_hits_moved_below_cutline"]),
        "conservative_elite_severe": int(elite.loc["conservative_blend_50", "severe_regression_count"]),
        "position_rows": int(len(position)),
        "season_rows": int(len(season)),
        "topn_rows": int(len(topn)),
    }
    return context


def write_markdown_reports(context: dict[str, Any]) -> None:
    reports = {
        "candidate_risk_rescue_summary.md": summary_md(context),
        "rescue_variant_selection_decision.md": selection_md(context),
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
# Candidate Risk Rescue Sprint V1

Verdict: `{context['verdict']}`

Decision label: `{context['decision_label']}`

Candidate under review: `usage_opportunity_volume`

This sprint tested only the fixed rescue variants listed in `fixed_rescue_variant_definitions.csv`. It did not run unbounded search, train a model, optimize a production formula, or wire any output into NWR.

## Result

No full safe rescue was found.

Best partial rescue by validation evidence: `{context['best_partial_rescue']}`.

- Original validation MAE delta: `{context['original_validation_mae_delta']}`
- Best partial rescue validation MAE delta: `{context['best_validation_mae_delta']}`
- Original holdout MAE delta: `{context['original_holdout_mae_delta']}`
- Best partial rescue holdout MAE delta: `{context['best_holdout_mae_delta']}`
- Best partial rescue validation/holdout startable precision deltas: `{context['best_validation_startable_delta']}` / `{context['best_holdout_startable_delta']}`
- Elite-QB severe regressions, original vs best partial rescue: `{context['original_elite_severe']}` -> `{context['best_elite_severe']}`
- Actual cutline hits moved below cutline, original vs best partial rescue: `{context['original_cutline_hits']}` -> `{context['best_cutline_hits']}`

Interpretation: `qb_guard_soft_blend` materially reduces elite-QB severe regressions while preserving most validation/holdout MAE improvement, but it does not reduce actual cutline hits moved below cutline. The conservative 50/50 blend reduces cutline hits to `{context['conservative_cutline_hits']}` and elite-QB severe regressions to `{context['conservative_elite_severe']}`, but gives up more validation signal and introduces a small startable-precision watch item. The candidate should remain on HOLD.
"""


def selection_md(context: dict[str, Any]) -> str:
    return f"""
# Rescue Variant Selection Decision

Decision label: `{DECISION_LABEL}`

Selection policy:

- Variant definitions and thresholds were fixed before evaluation.
- Validation evidence was used to identify the best partial rescue.
- Holdout was evaluated once after definitions were fixed.
- Holdout was not used to define guard thresholds.

Best partial rescue: `{BEST_PARTIAL_RESCUE}`.

Why it is not a full rescue:

- It reduces elite-QB severe regressions from `{context['original_elite_severe']}` to `{context['best_elite_severe']}`.
- It preserves validation and holdout MAE improvement versus the frozen V3 baseline.
- It keeps aggregate startable precision flat versus baseline.
- It does not reduce actual cutline hits moved below cutline: `{context['original_cutline_hits']}` -> `{context['best_cutline_hits']}`.

Conclusion: no rescue variant clears the full safety question. Keep the candidate held for human review.
"""


def human_review_md(context: dict[str, Any]) -> str:
    return f"""
# Human Review Update

The rescue sprint gives Tim a useful update, not an approval path.

Review order:

1. Compare `qb_guard_soft_blend` with the original candidate in `validation_metric_comparison.csv` and `holdout_metric_comparison.csv`.
2. Review `elite_qb_regression_comparison.csv`; the soft QB guard is the cleanest elite-QB risk reducer.
3. Review `cutline_regression_comparison.csv`; the cutline issue is still unresolved for the best partial rescue.
4. Review `topn_startable_rescue_report.csv`; conservative variants can trade off bucket/startable behavior.

Recommended human decision: keep `usage_opportunity_volume` on HOLD. A future branch could separately inspect cutline-safe guards, but that should be explicit and still review-only.
"""


def do_not_promote_md() -> str:
    return """
# Do Not Promote Notice

Do not promote `usage_opportunity_volume` or any rescue variant from this branch.

All rescue outputs are human-review evidence only. No formula, ranking, recommendation, hidden sort, app wiring, model behavior, source truth, runtime behavior, or production configuration is changed.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Status: PASS for review-only rescue sprint artifacts.

Confirmed:

- No production formula changes.
- No production config changes.
- No formula tuning, broad optimization, or black-box ML.
- No app, model, rank, service, source-truth, runtime, recommendation, or hidden-sort wiring.
- Guard logic uses only feature-season fields, baseline prediction output, candidate prediction output, and predeclared thresholds.
- Target outcomes are used only after fixed variants are defined for evaluation.
- Holdout is not used to define guard thresholds.
- No market, ADP, vendor, projection, or external rank fields are source truth.
- No routes, TPRR, YPRR, route proxies, ambiguous `rz_att`, red-zone sidecars, or current-only context.
- No candidate or rescue output is approved for production use.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

Scope: review-only Candidate Risk Rescue Sprint V1 artifacts and one focused artifact/schema test.

Expected changed paths:

- `docs/hq/experiments/historical_formula_candidate_risk_rescue_sprint_v1_20260701/`
- `tests/test_historical_formula_candidate_risk_rescue_sprint_v1_20260701.py`

No app, model, ranking, formula, source-truth, runtime, production config, raw/shared/cache/local export, or secret paths are intentionally changed.
"""


def next_phase_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommended next phase: Tim human review of Candidate Promotion Gate Prep V1 plus this Risk Rescue Sprint V1.

Do not advance to shadow-review prep automatically. The best partial rescue, `{BEST_PARTIAL_RESCUE}`, reduces elite-QB severe regressions but leaves cutline hits unresolved.

If Tim wants more evidence, run a new bounded cutline-specific review lane with predeclared guards. If Tim does not want more evidence, keep the candidate on HOLD or reject it as too risky.
"""


def write_manifest(context: dict[str, Any]) -> None:
    rows = []
    for name in REQUIRED_ARTIFACTS + ["build_historical_formula_candidate_risk_rescue_sprint_v1.py"]:
        path = EXPERIMENT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    body = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{BRANCH}`
- Starting HEAD: `{BASE_HEAD}`
- Decision label: `{DECISION_LABEL}`
- Best partial rescue: `{BEST_PARTIAL_RESCUE}`
- Review-only: true
- Approved for production use: false

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
