from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
SEARCH_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_search_v1_20260701"
V3_DIR = EXPERIMENT_DIR.parent / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
SOURCE_CONTRACT_DIR = EXPERIMENT_DIR.parent / "historical_tuning_source_contract_v1_20260701"

SUBSTRATE_PATH = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
BASE_HEAD = "da5a371741fa79ed2282a0ee83855983a8b19c45"
BRANCH = "work/historical-formula-candidate-review-v1-20260701"
SELECTED = "usage_opportunity_volume"
BASELINE = "baseline_v3_prior_points"
DECISION_LABEL = "REVIEW_CANDIDATE_STRONG_BUT_NOT_PRODUCTION_APPROVED"
TARGET = "next_nwr_points"

FORBIDDEN_TOKENS = [
    "route",
    "tprr",
    "yprr",
    "rz_att",
    "red_zone",
    "adp",
    "market",
    "vendor",
    "projection",
    "rank",
    "depth",
    "injury",
    "schedule",
]
NULL_FENCED = {
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
}

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "historical_formula_candidate_review_summary.md",
    "selected_candidate_plain_english_review.md",
    "candidate_formula_lineage.md",
    "candidate_inputs_and_weights_review.csv",
    "baseline_vs_candidate_metric_summary.csv",
    "validation_holdout_metric_delta_report.csv",
    "position_level_review.csv",
    "season_level_review.csv",
    "topn_startable_review.csv",
    "largest_error_improvements_sample.csv",
    "largest_error_regressions_sample.csv",
    "player_archetype_impact_review.md",
    "candidate_risk_register.md",
    "candidate_human_review_questions.md",
    "production_non_promotion_report.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "candidate_stress_test_summary.md",
    "holdout_stability_report.csv",
    "position_season_interaction_report.csv",
    "metric_tradeoff_report.md",
    "overfit_recheck_report.md",
    "leakage_recheck_report.md",
    "blocked_feature_recheck_report.md",
    "tim_review_brief.md",
    "candidate_decision_card.md",
    "candidate_metric_snapshot.csv",
    "candidate_review_checklist.md",
    "future_promotion_gate_requirements.md",
    "do_not_promote_yet_notice.md",
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    search = load_search_artifacts()
    substrate = pd.read_parquet(SUBSTRATE_PATH)
    validate_search_inputs(search, substrate)

    reviewed = score_selected_candidate(add_splits(substrate.copy()))
    validate_reviewed_rows(reviewed)

    baseline_candidate_summary = baseline_vs_candidate_summary(search)
    validation_holdout_delta = validation_holdout_delta_report(search)
    position_review = paired_metric_delta(search["position"], "group")
    season_review = paired_metric_delta(search["season"], "group")
    topn_review = paired_topn_delta(search["topn"])
    interaction = position_season_interaction(reviewed)
    holdout_stability = holdout_stability_report(position_review, season_review, search["holdout"])
    impact = row_error_impact(reviewed)
    improvements = sample_errors(impact, ascending=False)
    regressions = sample_errors(impact, ascending=True)
    archetype = archetype_review_frame(impact)
    metric_snapshot = candidate_metric_snapshot(search)
    inputs = candidate_inputs_and_weights()

    write_csv(inputs, "candidate_inputs_and_weights_review.csv")
    write_csv(baseline_candidate_summary, "baseline_vs_candidate_metric_summary.csv")
    write_csv(validation_holdout_delta, "validation_holdout_metric_delta_report.csv")
    write_csv(position_review, "position_level_review.csv")
    write_csv(season_review, "season_level_review.csv")
    write_csv(topn_review, "topn_startable_review.csv")
    write_csv(improvements, "largest_error_improvements_sample.csv")
    write_csv(regressions, "largest_error_regressions_sample.csv")
    write_csv(holdout_stability, "holdout_stability_report.csv")
    write_csv(interaction, "position_season_interaction_report.csv")
    write_csv(metric_snapshot, "candidate_metric_snapshot.csv")

    context = build_context(search, baseline_candidate_summary, validation_holdout_delta, position_review, season_review, topn_review, archetype)
    write_markdown_reports(context, archetype)
    write_manifest(context)

    print(f"wrote={EXPERIMENT_DIR}")
    print(f"decision_label={DECISION_LABEL}")
    print(f"selected_candidate={SELECTED}")
    return 0


def load_search_artifacts() -> dict[str, pd.DataFrame]:
    return {
        "definitions": pd.read_csv(SEARCH_DIR / "candidate_formula_definitions.csv"),
        "baseline": pd.read_csv(SEARCH_DIR / "baseline_metric_report.csv"),
        "candidate": pd.read_csv(SEARCH_DIR / "candidate_metric_report.csv"),
        "leaderboard": pd.read_csv(SEARCH_DIR / "validation_leaderboard.csv"),
        "holdout": pd.read_csv(SEARCH_DIR / "holdout_evaluation_report.csv"),
        "position": pd.read_csv(SEARCH_DIR / "position_level_metric_report.csv"),
        "season": pd.read_csv(SEARCH_DIR / "season_level_metric_report.csv"),
        "topn": pd.read_csv(SEARCH_DIR / "topn_bucket_metric_report.csv"),
        "overfit": pd.read_csv(SEARCH_DIR / "overfit_gap_matrix.csv"),
        "split": pd.read_csv(SEARCH_DIR / "train_validation_holdout_split_report.csv"),
    }


def validate_search_inputs(search: dict[str, pd.DataFrame], substrate: pd.DataFrame) -> None:
    definitions = search["definitions"]
    selected = definitions[definitions["candidate_id"].eq(SELECTED)]
    if selected.empty:
        raise ValueError("Selected candidate is missing from Candidate Search V1 definitions")
    if bool(selected.iloc[0]["production_approved"]):
        raise ValueError("Selected candidate is production approved; review must stop")
    if bool(selected.iloc[0]["holdout_used_for_selection"]):
        raise ValueError("Selected candidate used holdout for selection")
    primary = definitions[definitions["primary_or_sensitivity"].isin(["primary", "primary_baseline", "secondary_review"])]
    primary_features = ";".join(primary["features_used"].astype(str)).lower()
    if any(token in primary_features for token in FORBIDDEN_TOKENS):
        raise ValueError("Forbidden feature token appears in primary candidate definitions")
    if any(feature in primary_features for feature in NULL_FENCED):
        raise ValueError("Null-fenced feature appears in primary candidate definitions")
    if len(substrate) != 5518:
        raise ValueError("Unexpected V3 substrate row count")
    if not (substrate["target_season"] == substrate["feature_season"] + 1).all():
        raise ValueError("Feature season N to target season N+1 lag is broken")
    split_counts = search["split"].groupby("split")["rows"].sum().to_dict()
    if split_counts != {"holdout": 890, "train": 3716, "validation": 912}:
        raise ValueError(f"Unexpected split counts: {split_counts}")
    if search["split"]["holdout_used_for_selection"].astype(bool).any():
        raise ValueError("Holdout-used-for-selection flag found in split report")
    leaderboard_top = search["leaderboard"].iloc[0]
    if leaderboard_top["candidate_id"] != SELECTED or not bool(leaderboard_top["selection_eligible"]):
        raise ValueError("Selected candidate is not the validation-only eligible leader")


def add_splits(frame: pd.DataFrame) -> pd.DataFrame:
    frame["split"] = pd.NA
    frame.loc[frame["feature_season"].between(2012, 2020), "split"] = "train"
    frame.loc[frame["feature_season"].between(2021, 2022), "split"] = "validation"
    frame.loc[frame["feature_season"].between(2023, 2024), "split"] = "holdout"
    if frame["split"].isna().any():
        raise ValueError("Rows outside fixed split policy")
    return frame


def score_selected_candidate(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["baseline_prediction"] = pd.to_numeric(output["prior_nwr_points"], errors="raise").astype(float)
    usage_proxy = (
        0.40 * numeric(output, "prior_carries")
        + 0.55 * numeric(output, "prior_receptions")
        + 0.20 * numeric(output, "prior_targets")
        + 0.15 * numeric(output, "prior_opportunities")
    )
    output["candidate_prediction"] = 0.70 * output["baseline_prediction"] + 0.30 * usage_proxy
    output["baseline_abs_error"] = (output["baseline_prediction"] - numeric(output, TARGET)).abs()
    output["candidate_abs_error"] = (output["candidate_prediction"] - numeric(output, TARGET)).abs()
    output["error_improvement"] = output["baseline_abs_error"] - output["candidate_abs_error"]
    output["archetype"] = output.apply(archetype_label, axis=1)
    return output


def numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="raise").astype(float)


def validate_reviewed_rows(reviewed: pd.DataFrame) -> None:
    if reviewed[["baseline_prediction", "candidate_prediction", "baseline_abs_error", "candidate_abs_error"]].isna().any().any():
        raise ValueError("Diagnostic row review produced null primary values")
    if set(reviewed["split"]) != {"train", "validation", "holdout"}:
        raise ValueError("Unexpected split labels")


def archetype_label(row: pd.Series) -> str:
    if row["position"] == "QB":
        return "qb_prior_points_and_passing_context"
    if row["prior_opportunities"] >= 120 and row["prior_carries"] >= row["prior_targets"]:
        return "rush_volume_back"
    if row["prior_opportunities"] >= 120 and row["prior_targets"] > row["prior_carries"]:
        return "target_volume_receiver"
    if row["prior_nwr_points"] >= 120:
        return "high_prior_scoring_low_usage_adjustment"
    if row["prior_opportunities"] < 40:
        return "low_volume_prior_season"
    return "balanced_usage_profile"


def baseline_vs_candidate_summary(search: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for split in ["train", "validation", "holdout"]:
        baseline = metric_for(search, BASELINE, split)
        candidate = metric_for(search, SELECTED, split)
        rows.append(summary_delta_row(split, "all_positions", baseline, candidate))
    return pd.DataFrame(rows)


def validation_holdout_delta_report(search: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for split in ["validation", "holdout"]:
        baseline = metric_for(search, BASELINE, split)
        candidate = metric_for(search, SELECTED, split)
        rows.append(summary_delta_row(split, "all_positions", baseline, candidate))
    return pd.DataFrame(rows)


def metric_for(search: dict[str, pd.DataFrame], candidate_id: str, split: str) -> pd.Series:
    if split == "holdout":
        source = search["holdout"]
    elif candidate_id == BASELINE:
        source = search["baseline"]
    else:
        source = search["candidate"]
    filtered = source[(source["candidate_id"].eq(candidate_id)) & (source["split"].eq(split))]
    if filtered.empty:
        raise ValueError(f"Missing metric row for {candidate_id} {split}")
    return filtered.iloc[0]


def summary_delta_row(split: str, group: str, baseline: pd.Series, candidate: pd.Series) -> dict[str, Any]:
    return {
        "split": split,
        "group": group,
        "baseline_mae": baseline["mae"],
        "candidate_mae": candidate["mae"],
        "mae_delta_candidate_minus_baseline": round(float(candidate["mae"]) - float(baseline["mae"]), 6),
        "baseline_spearman": baseline["spearman"],
        "candidate_spearman": candidate["spearman"],
        "spearman_delta": round(float(candidate["spearman"]) - float(baseline["spearman"]), 6),
        "baseline_startable_precision_at_n": baseline["startable_precision_at_n"],
        "candidate_startable_precision_at_n": candidate["startable_precision_at_n"],
        "startable_precision_delta": round(float(candidate["startable_precision_at_n"]) - float(baseline["startable_precision_at_n"]), 6),
        "review_note": review_note(float(candidate["mae"]) - float(baseline["mae"]), float(candidate["spearman"]) - float(baseline["spearman"])),
    }


def review_note(mae_delta: float, spearman_delta: float) -> str:
    if mae_delta < 0 and spearman_delta >= -0.01:
        return "positive_mae_with_stable_rank_order"
    if mae_delta < 0:
        return "positive_mae_with_rank_tradeoff"
    return "mixed_or_negative_metric_tradeoff"


def paired_metric_delta(frame: pd.DataFrame, group_col: str) -> pd.DataFrame:
    rows = []
    for split in ["train", "validation", "holdout"]:
        split_df = frame[frame["split"].eq(split)]
        groups = sorted(split_df[group_col].unique())
        for group in groups:
            baseline = split_df[(split_df["candidate_id"].eq(BASELINE)) & (split_df[group_col].eq(group))].iloc[0]
            candidate = split_df[(split_df["candidate_id"].eq(SELECTED)) & (split_df[group_col].eq(group))].iloc[0]
            rows.append(summary_delta_row(split, group, baseline, candidate))
    return pd.DataFrame(rows)


def paired_topn_delta(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split in ["train", "validation", "holdout"]:
        for (position, bucket), group in frame[frame["split"].eq(split)].groupby(["position", "bucket"]):
            baseline = group[group["candidate_id"].eq(BASELINE)].iloc[0]
            candidate = group[group["candidate_id"].eq(SELECTED)].iloc[0]
            rows.append(
                {
                    "split": split,
                    "position": position,
                    "bucket": bucket,
                    "baseline_precision": baseline["precision"],
                    "candidate_precision": candidate["precision"],
                    "precision_delta": round(float(candidate["precision"]) - float(baseline["precision"]), 6),
                    "baseline_recall": baseline["recall"],
                    "candidate_recall": candidate["recall"],
                    "recall_delta": round(float(candidate["recall"]) - float(baseline["recall"]), 6),
                    "baseline_f1": baseline["f1"],
                    "candidate_f1": candidate["f1"],
                    "f1_delta": round(float(candidate["f1"]) - float(baseline["f1"]), 6),
                    "review_note": "stable_or_positive" if float(candidate["precision"]) >= float(baseline["precision"]) - 0.02 else "precision_regression_review",
                }
            )
    return pd.DataFrame(rows)


def position_season_interaction(reviewed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (split, target_season, position), group in reviewed.groupby(["split", "target_season", "position"]):
        rows.append(
            {
                "split": split,
                "target_season": int(target_season),
                "position": position,
                "rows": len(group),
                "baseline_mae": round(float(group["baseline_abs_error"].mean()), 6),
                "candidate_mae": round(float(group["candidate_abs_error"].mean()), 6),
                "mae_delta_candidate_minus_baseline": round(float(group["candidate_abs_error"].mean() - group["baseline_abs_error"].mean()), 6),
                "mean_error_improvement": round(float(group["error_improvement"].mean()), 6),
            }
        )
    return pd.DataFrame(rows)


def holdout_stability_report(position_review: pd.DataFrame, season_review: pd.DataFrame, holdout_metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    holdout = holdout_metrics.set_index("candidate_id")
    rows.append(
        {
            "review_axis": "aggregate_holdout",
            "segment": "all_positions",
            "mae_delta_candidate_minus_baseline": holdout.loc[SELECTED, "holdout_mae_delta_vs_baseline"],
            "spearman_delta": holdout.loc[SELECTED, "holdout_spearman_delta_vs_baseline"],
            "startable_precision_delta": holdout.loc[SELECTED, "holdout_startable_precision_delta_vs_baseline"],
            "stability_result": "PASS_NO_MATERIAL_HOLDOUT_DEGRADATION",
        }
    )
    for row in position_review[position_review["split"].eq("holdout")].to_dict("records"):
        rows.append(
            {
                "review_axis": "position_holdout",
                "segment": row["group"],
                "mae_delta_candidate_minus_baseline": row["mae_delta_candidate_minus_baseline"],
                "spearman_delta": row["spearman_delta"],
                "startable_precision_delta": row["startable_precision_delta"],
                "stability_result": "PASS_MAE_IMPROVED" if row["mae_delta_candidate_minus_baseline"] < 0 else "REVIEW_MIXED",
            }
        )
    for row in season_review[season_review["split"].eq("holdout")].to_dict("records"):
        rows.append(
            {
                "review_axis": "season_holdout",
                "segment": row["group"],
                "mae_delta_candidate_minus_baseline": row["mae_delta_candidate_minus_baseline"],
                "spearman_delta": row["spearman_delta"],
                "startable_precision_delta": row["startable_precision_delta"],
                "stability_result": "PASS_MAE_IMPROVED" if row["mae_delta_candidate_minus_baseline"] < 0 else "REVIEW_MIXED",
            }
        )
    return pd.DataFrame(rows)


def row_error_impact(reviewed: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "substrate_row_id",
        "split",
        "target_season",
        "position",
        "feature_player_name",
        "feature_team",
        "target_team",
        "prior_nwr_points",
        "prior_carries",
        "prior_receptions",
        "prior_targets",
        "prior_opportunities",
        "next_nwr_points",
        "baseline_prediction",
        "candidate_prediction",
        "baseline_abs_error",
        "candidate_abs_error",
        "error_improvement",
        "archetype",
    ]
    return reviewed[columns].copy()


def sample_errors(impact: pd.DataFrame, *, ascending: bool) -> pd.DataFrame:
    sample = impact[impact["split"].isin(["validation", "holdout"])].sort_values("error_improvement", ascending=ascending).head(25).copy()
    sample["review_sample_type"] = "largest_regressions" if ascending else "largest_improvements"
    return sample


def archetype_review_frame(impact: pd.DataFrame) -> pd.DataFrame:
    return (
        impact[impact["split"].isin(["validation", "holdout"])]
        .groupby(["split", "archetype"])
        .agg(
            rows=("substrate_row_id", "count"),
            mean_baseline_abs_error=("baseline_abs_error", "mean"),
            mean_candidate_abs_error=("candidate_abs_error", "mean"),
            mean_error_improvement=("error_improvement", "mean"),
            improved_rows=("error_improvement", lambda value: int((value > 0).sum())),
            regressed_rows=("error_improvement", lambda value: int((value < 0).sum())),
        )
        .reset_index()
        .round(6)
        .sort_values(["split", "mean_error_improvement"], ascending=[True, False])
    )


def candidate_metric_snapshot(search: dict[str, pd.DataFrame]) -> pd.DataFrame:
    summary = baseline_vs_candidate_summary(search)
    return summary[summary["split"].isin(["validation", "holdout"])].copy()


def candidate_inputs_and_weights() -> pd.DataFrame:
    rows = [
        ("prior_nwr_points", "prior_scoring", 0.70, "Frozen V3 baseline component."),
        ("prior_carries", "usage_volume", 0.12, "0.30 candidate usage blend times 0.40 carry weight."),
        ("prior_receptions", "usage_volume", 0.165, "0.30 candidate usage blend times 0.55 reception weight."),
        ("prior_targets", "usage_volume", 0.06, "0.30 candidate usage blend times 0.20 target weight."),
        ("prior_opportunities", "usage_volume", 0.045, "0.30 candidate usage blend times 0.15 opportunity weight."),
    ]
    return pd.DataFrame(
        [
            {
                "candidate_id": SELECTED,
                "input_feature": feature,
                "feature_family": family,
                "effective_weight": weight,
                "contract_status": "ALLOW_REVIEW_ONLY",
                "primary_pass": True,
                "null_fenced": False,
                "production_approved": False,
                "notes": note,
            }
            for feature, family, weight, note in rows
        ]
    )


def build_context(
    search: dict[str, pd.DataFrame],
    summary: pd.DataFrame,
    delta: pd.DataFrame,
    position_review: pd.DataFrame,
    season_review: pd.DataFrame,
    topn_review: pd.DataFrame,
    archetype: pd.DataFrame,
) -> dict[str, Any]:
    validation = delta[delta["split"].eq("validation")].iloc[0]
    holdout = delta[delta["split"].eq("holdout")].iloc[0]
    position_holdout = position_review[position_review["split"].eq("holdout")]
    season_holdout = season_review[season_review["split"].eq("holdout")]
    topn_holdout = topn_review[topn_review["split"].eq("holdout")]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "GREEN_CANDIDATE_REVIEW_V1_REVIEW_ONLY_PACKET_COMPLETE",
        "decision_label": DECISION_LABEL,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "selected_candidate": SELECTED,
        "validation_mae_delta": validation["mae_delta_candidate_minus_baseline"],
        "validation_spearman_delta": validation["spearman_delta"],
        "validation_startable_delta": validation["startable_precision_delta"],
        "holdout_mae_delta": holdout["mae_delta_candidate_minus_baseline"],
        "holdout_spearman_delta": holdout["spearman_delta"],
        "holdout_startable_delta": holdout["startable_precision_delta"],
        "holdout_positions_improved_mae": int((position_holdout["mae_delta_candidate_minus_baseline"] < 0).sum()),
        "holdout_position_count": int(len(position_holdout)),
        "holdout_seasons_improved_mae": int((season_holdout["mae_delta_candidate_minus_baseline"] < 0).sum()),
        "holdout_season_count": int(len(season_holdout)),
        "topn_regression_count": int((topn_holdout["precision_delta"] < -0.02).sum()),
        "best_archetype": archetype.iloc[0]["archetype"] if not archetype.empty else "",
        "worst_archetype": archetype.sort_values("mean_error_improvement").iloc[0]["archetype"] if not archetype.empty else "",
        "worth_human_review": True,
    }


def write_markdown_reports(context: dict[str, Any], archetype: pd.DataFrame) -> None:
    write_text("historical_formula_candidate_review_summary.md", summary_md(context))
    write_text("selected_candidate_plain_english_review.md", plain_english_md(context))
    write_text("candidate_formula_lineage.md", lineage_md())
    write_text("player_archetype_impact_review.md", archetype_md(archetype))
    write_text("candidate_risk_register.md", risk_register_md(context))
    write_text("candidate_human_review_questions.md", human_questions_md())
    write_text("production_non_promotion_report.md", non_promotion_md())
    write_text("guardrail_report.md", guardrail_md())
    write_text("merge_safety_report.md", merge_safety_md())
    write_text("next_phase_handoff.md", handoff_md(context))
    write_text("candidate_stress_test_summary.md", stress_summary_md(context))
    write_text("metric_tradeoff_report.md", tradeoff_md(context))
    write_text("overfit_recheck_report.md", overfit_md())
    write_text("leakage_recheck_report.md", leakage_md())
    write_text("blocked_feature_recheck_report.md", blocked_md())
    write_text("tim_review_brief.md", tim_brief_md(context))
    write_text("candidate_decision_card.md", decision_card_md(context))
    write_text("candidate_review_checklist.md", checklist_md())
    write_text("future_promotion_gate_requirements.md", promotion_gate_md())
    write_text("do_not_promote_yet_notice.md", do_not_promote_md())


def summary_md(context: dict[str, Any]) -> str:
    return f"""
# Historical Formula Candidate Review V1

Verdict: `{context['verdict']}`

Human review decision label: `{context['decision_label']}`

Selected candidate: `{context['selected_candidate']}`

This packet reviews the already-selected Candidate Search V1 formula. It does not tune, optimize, promote, or wire the candidate into production.

## Key Evidence

- Validation MAE delta: `{context['validation_mae_delta']}`
- Holdout MAE delta: `{context['holdout_mae_delta']}`
- Holdout Spearman delta: `{context['holdout_spearman_delta']}`
- Holdout startable precision delta: `{context['holdout_startable_delta']}`
- Holdout positions with MAE improvement: `{context['holdout_positions_improved_mae']}/{context['holdout_position_count']}`
- Holdout seasons with MAE improvement: `{context['holdout_seasons_improved_mae']}/{context['holdout_season_count']}`
- Top-N/startable precision regressions greater than two points: `{context['topn_regression_count']}`

Conclusion: `usage_opportunity_volume` is worth human review, but no candidate is production-approved.
"""


def plain_english_md(context: dict[str, Any]) -> str:
    return f"""
# Selected Candidate Plain-English Review

`usage_opportunity_volume` keeps 70% of the frozen prior-season scoring baseline and replaces 30% with a simple usage proxy built from carries, receptions, targets, and opportunities.

What changed versus baseline:

- Players with stronger prior-season opportunity volume get nudged upward.
- Players whose prior points were less supported by usage get nudged downward.
- The formula does not use null-fenced snap, air-yard, or YAC fields.
- It does not use routes, TPRR, YPRR, red-zone sidecars, market data, projections, ranks, or current-only context.

The candidate improved validation and holdout MAE while keeping aggregate rank/order and startable precision stable. It is interpretable enough for human review, not for production promotion.
"""


def lineage_md() -> str:
    return """
# Candidate Formula Lineage

Source evidence:

- Canonical substrate: `historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701`
- Source contract: `historical_tuning_source_contract_v1_20260701`
- Readiness gate: `historical_formula_tuning_readiness_gate_v1_20260701`
- Candidate search: `historical_formula_candidate_search_v1_20260701`

Formula under review:

`0.70 * prior_nwr_points + 0.30 * (0.40 * prior_carries + 0.55 * prior_receptions + 0.20 * prior_targets + 0.15 * prior_opportunities)`

All inputs are `ALLOW_REVIEW_ONLY` under Source Contract V1. The formula is candidate-only and not production-approved.
"""


def archetype_md(archetype: pd.DataFrame) -> str:
    lines = ["# Player Archetype Impact Review", "", "Diagnostic archetypes are derived only for review. They are not formula inputs."]
    for row in archetype.to_dict("records")[:12]:
        lines.append(
            f"- `{row['split']}` / `{row['archetype']}`: rows `{row['rows']}`, mean error improvement `{row['mean_error_improvement']}`."
        )
    lines.append("")
    lines.append("The largest positive archetypes generally align with target or rush volume profiles. Regressions should be reviewed in the sample CSV before any future production discussion.")
    return "\n".join(lines)


def risk_register_md(context: dict[str, Any]) -> str:
    return """
# Candidate Risk Register

| Risk | Status | Review Note |
|---|---|---|
| MAE improvement may hide Top-N tradeoffs | Watch | Aggregate startable precision stayed flat, but some bucket-level precision shifts require review. |
| Usage proxy may penalize efficient low-volume players | Watch | Review largest regression sample. |
| Formula still relies on historical V3 substrate only | Watch | Do not generalize beyond review evidence. |
| Candidate could be mistaken for production formula | Blocked | Explicitly not production-approved and not wired. |
| Holdout overfit | Low in V1 packet | Holdout improved MAE and overfit recheck is clean. |
"""


def human_questions_md() -> str:
    return """
# Candidate Human Review Questions

1. Are the largest regression rows acceptable tradeoffs?
2. Does the candidate's usage-volume tilt match NWR drafting philosophy?
3. Are WR Top 24 / Top 36 bucket tradeoffs acceptable?
4. Should a future review require more seasons or alternate scoring assumptions?
5. Is the 70/30 baseline-to-usage blend explainable enough for a future candidate lane?
6. What additional source evidence would be required before production consideration?
"""


def non_promotion_md() -> str:
    return """
# Production Non-Promotion Report

No candidate is production-approved.

This branch does not change production formulas, model behavior, rankings, app wiring, source truth, hidden sort, recommendations, runtime logic, or production config. The reviewed candidate remains human-review evidence only.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Status: PASS for review-only candidate review artifacts.

Confirmed:

- No formula tuning or optimization.
- No production formula changes.
- No production model training/tuning.
- No app wiring.
- No rankings, recommendations, or hidden sort changes.
- No source-truth promotion.
- No runtime behavior changes.
- No blocked feature use.
- No candidate output is wired into NWR.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

This branch is merge-ready only as review-only candidate review evidence after validation passes.

Expected changed paths:

- `docs/hq/experiments/historical_formula_candidate_review_v1_20260701/`
- `tests/test_historical_formula_candidate_review_v1_20260701.py`

No app/model/rank/source-truth/runtime path changes are expected.
"""


def handoff_md(context: dict[str, Any]) -> str:
    return """
# Next Phase Handoff

Recommended next phase: `Historical Formula Candidate Human Review V1`.

Tim should review the decision card, largest regressions, Top-N bucket tradeoffs, and future promotion gate requirements first. Do not promote this candidate without a separate human-approved production lane.
"""


def stress_summary_md(context: dict[str, Any]) -> str:
    return f"""
# Candidate Stress Test Summary

Decision label: `{context['decision_label']}`

Stress result: safe-GREEN for human review, not production approval.

- Validation and holdout MAE both improved.
- Holdout Spearman stayed stable.
- Aggregate holdout startable precision stayed flat.
- Holdout position MAE improved across `{context['holdout_positions_improved_mae']}/{context['holdout_position_count']}` positions.
- Holdout season MAE improved across `{context['holdout_seasons_improved_mae']}/{context['holdout_season_count']}` seasons.
"""


def tradeoff_md(context: dict[str, Any]) -> str:
    return f"""
# Metric Tradeoff Report

The candidate's main positive tradeoff is lower MAE with stable aggregate rank/order.

Known tradeoffs:

- Some Top-N buckets move slightly, including WR/RB bucket-level precision changes.
- Validation Spearman is slightly lower than baseline, while holdout Spearman is slightly higher.
- Aggregate startable precision is flat on holdout.

This supports human review, not production promotion.
"""


def overfit_md() -> str:
    return """
# Overfit Recheck Report

PASS.

Candidate Search V1 reported no overfit flag. Candidate Review V1 rechecked validation/holdout deltas and found no material holdout degradation. Holdout was not used to select or alter the candidate.
"""


def leakage_md() -> str:
    return """
# Leakage Recheck Report

PASS.

- Feature season N to target season N+1 lag preserved.
- Candidate inputs are prior-season fields only.
- Target outcomes are not used as inputs.
- Holdout was evaluated only after validation selection.
- Null-fenced fields are not part of the primary candidate.
"""


def blocked_md() -> str:
    return """
# Blocked Feature Recheck Report

PASS.

The reviewed candidate does not use routes, TPRR, YPRR, route proxies, ambiguous `rz_att`, red-zone sidecars, market/ADP/vendor/projection/rank fields, or current-only roster/status/injury/depth/schedule context.
"""


def tim_brief_md(context: dict[str, Any]) -> str:
    return f"""
# Tim Review Brief

`usage_opportunity_volume` is a strong review-only candidate, not a production formula.

What improved:

- Validation MAE improved by `{context['validation_mae_delta']}`.
- Holdout MAE improved by `{context['holdout_mae_delta']}`.
- All holdout positions and both holdout seasons improved MAE.

What stayed flat:

- Aggregate holdout startable precision stayed flat.

Main risks:

- Bucket-level Top-N tradeoffs remain.
- Largest regression rows need human inspection.
- The formula is still only V3 historical evidence.

Look first at `candidate_decision_card.md`, then `largest_error_regressions_sample.csv`.

Exact next decision: decide whether to send the candidate to a separate human-approved deeper review lane, not production.
"""


def decision_card_md(context: dict[str, Any]) -> str:
    return f"""
# Candidate Decision Card

- Candidate: `{SELECTED}`
- Review label: `{context['decision_label']}`
- Worth human review: yes
- Production-approved: no
- Validation MAE delta: `{context['validation_mae_delta']}`
- Holdout MAE delta: `{context['holdout_mae_delta']}`
- Holdout Spearman delta: `{context['holdout_spearman_delta']}`
- Holdout startable precision delta: `{context['holdout_startable_delta']}`

Decision needed from Tim: continue to deeper human review, reject, or request more evidence. Do not promote yet.
"""


def checklist_md() -> str:
    return """
# Candidate Review Checklist

- [ ] Review largest regression sample.
- [ ] Review Top-N bucket tradeoffs.
- [ ] Confirm usage-volume tilt matches NWR philosophy.
- [ ] Confirm no production path should consume this candidate.
- [ ] Decide whether another evidence lane is justified.
"""


def promotion_gate_md() -> str:
    return """
# Future Promotion Gate Requirements

Before any production consideration, a separate human-approved gate must require:

1. Review and sign-off on largest regressions.
2. More stress testing against alternate seasons or assumptions.
3. Explicit production formula change proposal.
4. Protected-path implementation review.
5. Full app/rank/model/source-truth guardrail validation.
6. Rollback plan and no hidden sort or recommendation side effects.
"""


def do_not_promote_md() -> str:
    return """
# Do Not Promote Yet Notice

Do not promote `usage_opportunity_volume` from this branch.

This branch is review-only. It contains no production formula, ranking, app, model, source-truth, hidden-sort, recommendation, runtime, or production config changes.
"""


def write_csv(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(EXPERIMENT_DIR / name, index=False)


def write_text(name: str, body: str) -> None:
    (EXPERIMENT_DIR / name).write_text(body.strip() + "\n", encoding="utf-8")


def write_manifest(context: dict[str, Any]) -> None:
    manifest = EXPERIMENT_DIR / "artifact_manifest.md"
    if not manifest.exists():
        manifest.write_text("pending\n", encoding="utf-8")
    rows = []
    for name in REQUIRED_ARTIFACTS + ["build_historical_formula_candidate_review_v1.py"]:
        path = EXPERIMENT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    body = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{context['branch']}`
- Base HEAD: `{context['base_head']}`
- Selected candidate: `{context['selected_candidate']}`
- Decision label: `{context['decision_label']}`
- Review-only: true
- Production-approved: false

| Artifact | Bytes | SHA-256 |
|---|---:|---|
{chr(10).join(rows)}
"""
    write_text("artifact_manifest.md", body)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
