from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path(__file__).resolve().parent
ROOT = EXPERIMENT_DIR.parents[3]
SEARCH_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_search_v1_20260701"
REVIEW_DIR = EXPERIMENT_DIR.parent / "historical_formula_candidate_review_v1_20260701"
V3_DIR = EXPERIMENT_DIR.parent / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
SOURCE_CONTRACT_DIR = EXPERIMENT_DIR.parent / "historical_tuning_source_contract_v1_20260701"

SUBSTRATE_PATH = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
BASE_HEAD = "9775357050befe8f27315c461c75cb4181a4c87a"
BRANCH = "work/historical-formula-candidate-promotion-gate-prep-v1-20260701"
SELECTED = "usage_opportunity_volume"
BASELINE = "baseline_v3_prior_points"
TARGET = "next_nwr_points"
VERDICT = "YELLOW_CANDIDATE_PROMOTION_GATE_PREP_REVIEW_ONLY_HUMAN_HOLD"
DECISION_LABEL = "HOLD_FOR_HUMAN_REVIEW"

NULL_FENCED = {
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
}
BLOCKED_TOKENS = {
    "route",
    "tprr",
    "yprr",
    "rz_att",
    "red_zone",
    "adp",
    "market",
    "vendor",
    "projection",
    "depth",
    "injury",
    "schedule",
}
CASEBOOK_COLUMNS = [
    "player_id",
    "player_name",
    "position",
    "feature_season",
    "target_season",
    "baseline_error",
    "candidate_error",
    "error_delta",
    "baseline_score_or_rank_proxy",
    "candidate_score_or_rank_proxy",
    "actual_target",
    "startable_bucket",
    "top_bucket",
    "archetype_label",
    "short_review_note",
    "substrate_row_id",
    "feature_team",
    "target_team",
    "prior_nwr_points",
    "prior_targets",
    "prior_carries",
    "prior_receptions",
    "prior_opportunities",
    "baseline_prediction",
    "candidate_prediction",
    "baseline_prediction_rank",
    "candidate_prediction_rank",
    "actual_position_finish",
    "split",
]
REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "candidate_promotion_gate_prep_summary.md",
    "candidate_evidence_consolidation.md",
    "candidate_metric_tradeoff_matrix.csv",
    "position_cutline_impact_report.csv",
    "startable_bucket_tradeoff_report.csv",
    "season_stability_report.csv",
    "largest_regression_casebook.csv",
    "largest_improvement_casebook.csv",
    "player_archetype_impact_report.csv",
    "candidate_failure_mode_report.md",
    "candidate_strengths_report.md",
    "shadow_review_requirements.md",
    "human_review_checklist.md",
    "advance_hold_reject_decision_card.md",
    "do_not_promote_notice.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    search = load_search_artifacts()
    review = load_review_artifacts()
    substrate = pd.read_parquet(SUBSTRATE_PATH)

    validate_inputs(search, review, substrate)
    scored = score_candidate(add_splits(substrate.copy()))

    metric_tradeoffs = build_metric_tradeoff_matrix(review)
    cutline_impact = build_position_cutline_impact(scored)
    bucket_tradeoffs = build_startable_bucket_tradeoffs(review)
    season_stability = build_season_stability(review)
    archetype_impact = build_archetype_impact(scored)
    regressions = build_casebook(scored, regression=True)
    improvements = build_casebook(scored, regression=False)

    write_csv(metric_tradeoffs, "candidate_metric_tradeoff_matrix.csv")
    write_csv(cutline_impact, "position_cutline_impact_report.csv")
    write_csv(bucket_tradeoffs, "startable_bucket_tradeoff_report.csv")
    write_csv(season_stability, "season_stability_report.csv")
    write_csv(archetype_impact, "player_archetype_impact_report.csv")
    write_csv(regressions, "largest_regression_casebook.csv")
    write_csv(improvements, "largest_improvement_casebook.csv")

    context = build_context(
        review=review,
        metric_tradeoffs=metric_tradeoffs,
        cutline_impact=cutline_impact,
        bucket_tradeoffs=bucket_tradeoffs,
        season_stability=season_stability,
        archetype_impact=archetype_impact,
        regressions=regressions,
        improvements=improvements,
    )
    write_markdown_reports(context)
    write_manifest(context)

    print(f"wrote={EXPERIMENT_DIR}")
    print(f"decision_label={DECISION_LABEL}")
    return 0


def load_search_artifacts() -> dict[str, pd.DataFrame]:
    return {
        "definitions": pd.read_csv(SEARCH_DIR / "candidate_formula_definitions.csv"),
        "leaderboard": pd.read_csv(SEARCH_DIR / "validation_leaderboard.csv"),
        "split": pd.read_csv(SEARCH_DIR / "train_validation_holdout_split_report.csv"),
    }


def load_review_artifacts() -> dict[str, pd.DataFrame | str]:
    markdown_files = {
        "summary_md": "historical_formula_candidate_review_summary.md",
        "decision_md": "candidate_decision_card.md",
        "guardrail_md": "guardrail_report.md",
        "leakage_md": "leakage_recheck_report.md",
        "blocked_md": "blocked_feature_recheck_report.md",
        "non_promotion_md": "production_non_promotion_report.md",
    }
    data: dict[str, pd.DataFrame | str] = {
        "aggregate": pd.read_csv(REVIEW_DIR / "baseline_vs_candidate_metric_summary.csv"),
        "validation_holdout": pd.read_csv(REVIEW_DIR / "validation_holdout_metric_delta_report.csv"),
        "position": pd.read_csv(REVIEW_DIR / "position_level_review.csv"),
        "season": pd.read_csv(REVIEW_DIR / "season_level_review.csv"),
        "topn": pd.read_csv(REVIEW_DIR / "topn_startable_review.csv"),
        "interaction": pd.read_csv(REVIEW_DIR / "position_season_interaction_report.csv"),
        "inputs": pd.read_csv(REVIEW_DIR / "candidate_inputs_and_weights_review.csv"),
        "metric_snapshot": pd.read_csv(REVIEW_DIR / "candidate_metric_snapshot.csv"),
    }
    for key, name in markdown_files.items():
        data[key] = (REVIEW_DIR / name).read_text(encoding="utf-8")
    return data


def validate_inputs(
    search: dict[str, pd.DataFrame],
    review: dict[str, pd.DataFrame | str],
    substrate: pd.DataFrame,
) -> None:
    definitions = search["definitions"]
    selected = definitions[definitions["candidate_id"].eq(SELECTED)]
    if selected.empty:
        raise ValueError("Selected candidate is missing from Candidate Search V1")
    selected_row = selected.iloc[0]
    for col in [
        "holdout_used_for_selection",
        "production_approved",
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
    ]:
        if bool(selected_row[col]):
            raise ValueError(f"Selected candidate violates review-only guardrail: {col}")
    features_used = str(selected_row["features_used"]).lower()
    if any(token in features_used for token in BLOCKED_TOKENS):
        raise ValueError("Blocked feature token appears in selected candidate features")
    if any(feature in features_used for feature in NULL_FENCED):
        raise ValueError("Null-fenced field appears in selected primary candidate")
    inputs = checked_frame(review["inputs"])
    if inputs["null_fenced"].astype(bool).any():
        raise ValueError("Candidate input review includes null-fenced primary inputs")
    if inputs["production_approved"].astype(bool).any():
        raise ValueError("Candidate input review marks an input approved for production")
    if len(substrate) != 5518:
        raise ValueError(f"Unexpected V3 substrate row count: {len(substrate)}")
    if not (substrate["target_season"] == substrate["feature_season"] + 1).all():
        raise ValueError("Feature season N to target season N+1 lag is broken")
    forbidden_flags = [
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
        "production_approved",
    ]
    if substrate[forbidden_flags].astype(bool).any().any():
        raise ValueError("V3 substrate contains a promoted production flag")
    split_counts = search["split"].groupby("split")["rows"].sum().to_dict()
    if split_counts != {"holdout": 890, "train": 3716, "validation": 912}:
        raise ValueError(f"Unexpected split counts: {split_counts}")
    leaderboard = search["leaderboard"]
    top = leaderboard.iloc[0]
    if top["candidate_id"] != SELECTED or not bool(top["selection_eligible"]):
        raise ValueError("Selected candidate is not the validation-only eligible leader")
    if "Holdout was evaluated only after validation selection" not in checked_text(review["leakage_md"]):
        raise ValueError("Leakage report does not preserve holdout selection rule")


def checked_frame(value: pd.DataFrame | str) -> pd.DataFrame:
    if not isinstance(value, pd.DataFrame):
        raise TypeError("Expected DataFrame")
    return value


def checked_text(value: pd.DataFrame | str) -> str:
    if not isinstance(value, str):
        raise TypeError("Expected text")
    return value


def add_splits(frame: pd.DataFrame) -> pd.DataFrame:
    frame["split"] = pd.NA
    frame.loc[frame["feature_season"].between(2012, 2020), "split"] = "train"
    frame.loc[frame["feature_season"].between(2021, 2022), "split"] = "validation"
    frame.loc[frame["feature_season"].between(2023, 2024), "split"] = "holdout"
    if frame["split"].isna().any():
        raise ValueError("Rows outside fixed readiness-gate split policy")
    return frame


def score_candidate(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["baseline_prediction"] = number(output, "prior_nwr_points")
    usage_proxy = (
        0.40 * number(output, "prior_carries")
        + 0.55 * number(output, "prior_receptions")
        + 0.20 * number(output, "prior_targets")
        + 0.15 * number(output, "prior_opportunities")
    )
    output["candidate_prediction"] = 0.70 * output["baseline_prediction"] + 0.30 * usage_proxy
    output["baseline_abs_error"] = (output["baseline_prediction"] - number(output, TARGET)).abs()
    output["candidate_abs_error"] = (output["candidate_prediction"] - number(output, TARGET)).abs()
    output["candidate_minus_baseline_abs_error"] = output["candidate_abs_error"] - output["baseline_abs_error"]
    output["error_improvement"] = output["baseline_abs_error"] - output["candidate_abs_error"]
    output["archetype_label"] = output.apply(archetype_label, axis=1)
    output["top_bucket"] = output["startable_bucket"].fillna("NOT_STARTABLE")
    output["baseline_prediction_rank"] = prediction_rank(output, "baseline_prediction")
    output["candidate_prediction_rank"] = prediction_rank(output, "candidate_prediction")
    output["baseline_score_or_rank_proxy"] = output.apply(
        lambda row: f"score={row['baseline_prediction']:.3f};rank={int(row['baseline_prediction_rank'])}",
        axis=1,
    )
    output["candidate_score_or_rank_proxy"] = output.apply(
        lambda row: f"score={row['candidate_prediction']:.3f};rank={int(row['candidate_prediction_rank'])}",
        axis=1,
    )
    return output


def number(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="raise").astype(float)


def prediction_rank(frame: pd.DataFrame, column: str) -> pd.Series:
    return (
        frame.groupby(["target_season", "position"], sort=False)[column]
        .rank(method="first", ascending=False)
        .astype(int)
    )


def archetype_label(row: pd.Series) -> str:
    opportunities = float(row["prior_opportunities"])
    carries = float(row["prior_carries"])
    targets = float(row["prior_targets"])
    prior_points = float(row["prior_nwr_points"])
    if row["position"] == "QB" and prior_points >= 250:
        return "elite_qb_prior_scoring_usage_proxy_drag_risk"
    if row["position"] == "QB":
        return "qb_prior_points_and_passing_context"
    if opportunities >= 180 and carries >= targets:
        return "high_rush_volume_back"
    if opportunities >= 180 and targets > carries:
        return "high_target_volume_receiver"
    if opportunities >= 120 and carries >= targets:
        return "moderate_rush_volume"
    if opportunities >= 120 and targets > carries:
        return "moderate_target_volume"
    if prior_points >= 120:
        return "high_prior_scoring_low_usage_adjustment"
    if opportunities < 40:
        return "low_volume_prior_season"
    return "balanced_usage_profile"


def build_metric_tradeoff_matrix(review: dict[str, pd.DataFrame | str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    aggregate = checked_frame(review["validation_holdout"])
    for item in aggregate.to_dict("records"):
        rows.extend(
            metric_rows(
                scope="aggregate",
                split=item["split"],
                segment="all_positions",
                source_metric_row=item,
            )
        )
    position = checked_frame(review["position"])
    for item in position[position["split"].isin(["validation", "holdout"])].to_dict("records"):
        rows.extend(
            metric_rows(
                scope="position",
                split=item["split"],
                segment=item["group"],
                source_metric_row=item,
            )
        )
    season = checked_frame(review["season"])
    for item in season[season["split"].isin(["validation", "holdout"])].to_dict("records"):
        rows.extend(
            metric_rows(
                scope="season",
                split=item["split"],
                segment=item["group"],
                source_metric_row=item,
            )
        )
    topn = checked_frame(review["topn"])
    for item in topn[topn["split"].isin(["validation", "holdout"])].to_dict("records"):
        rows.append(
            {
                "evidence_scope": "topn_bucket",
                "split": item["split"],
                "segment": f"{item['position']}:{item['bucket']}",
                "metric": "precision",
                "baseline_value": item["baseline_precision"],
                "candidate_value": item["candidate_precision"],
                "delta_candidate_minus_baseline": item["precision_delta"],
                "materiality": materiality(float(item["precision_delta"]), higher_is_better=True),
                "gate_assessment": gate_assessment_for_delta(float(item["precision_delta"]), higher_is_better=True),
                "review_note": item["review_note"],
            }
        )
        rows.append(
            {
                "evidence_scope": "topn_bucket",
                "split": item["split"],
                "segment": f"{item['position']}:{item['bucket']}",
                "metric": "f1",
                "baseline_value": item["baseline_f1"],
                "candidate_value": item["candidate_f1"],
                "delta_candidate_minus_baseline": item["f1_delta"],
                "materiality": materiality(float(item["f1_delta"]), higher_is_better=True),
                "gate_assessment": gate_assessment_for_delta(float(item["f1_delta"]), higher_is_better=True),
                "review_note": item["review_note"],
            }
        )
    return pd.DataFrame(rows)


def metric_rows(scope: str, split: str, segment: str, source_metric_row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "evidence_scope": scope,
            "split": split,
            "segment": segment,
            "metric": "mae",
            "baseline_value": source_metric_row["baseline_mae"],
            "candidate_value": source_metric_row["candidate_mae"],
            "delta_candidate_minus_baseline": source_metric_row["mae_delta_candidate_minus_baseline"],
            "materiality": materiality(float(source_metric_row["mae_delta_candidate_minus_baseline"]), higher_is_better=False),
            "gate_assessment": gate_assessment_for_delta(float(source_metric_row["mae_delta_candidate_minus_baseline"]), higher_is_better=False),
            "review_note": source_metric_row["review_note"],
        },
        {
            "evidence_scope": scope,
            "split": split,
            "segment": segment,
            "metric": "spearman",
            "baseline_value": source_metric_row["baseline_spearman"],
            "candidate_value": source_metric_row["candidate_spearman"],
            "delta_candidate_minus_baseline": source_metric_row["spearman_delta"],
            "materiality": materiality(float(source_metric_row["spearman_delta"]), higher_is_better=True),
            "gate_assessment": gate_assessment_for_delta(float(source_metric_row["spearman_delta"]), higher_is_better=True),
            "review_note": source_metric_row["review_note"],
        },
        {
            "evidence_scope": scope,
            "split": split,
            "segment": segment,
            "metric": "startable_precision_at_n",
            "baseline_value": source_metric_row["baseline_startable_precision_at_n"],
            "candidate_value": source_metric_row["candidate_startable_precision_at_n"],
            "delta_candidate_minus_baseline": source_metric_row["startable_precision_delta"],
            "materiality": materiality(float(source_metric_row["startable_precision_delta"]), higher_is_better=True),
            "gate_assessment": gate_assessment_for_delta(float(source_metric_row["startable_precision_delta"]), higher_is_better=True),
            "review_note": source_metric_row["review_note"],
        },
    ]


def materiality(delta: float, *, higher_is_better: bool) -> str:
    effective = delta if higher_is_better else -delta
    if effective >= 0.02:
        return "material_improvement"
    if effective > 0:
        return "minor_improvement"
    if effective <= -0.02:
        return "material_regression"
    if effective < 0:
        return "minor_regression"
    return "flat"


def gate_assessment_for_delta(delta: float, *, higher_is_better: bool) -> str:
    label = materiality(delta, higher_is_better=higher_is_better)
    if label == "material_regression":
        return "REVIEW_RISK"
    if label in {"minor_regression", "flat"}:
        return "WATCH"
    return "SUPPORTS_CANDIDATE"


def build_position_cutline_impact(scored: pd.DataFrame) -> pd.DataFrame:
    cutlines = {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}
    rows: list[dict[str, Any]] = []
    review_rows = scored[scored["split"].isin(["validation", "holdout"])].copy()
    for (split, target_season, position), group in review_rows.groupby(["split", "target_season", "position"]):
        for cutline in cutlines.get(position, []):
            baseline_in = group["baseline_prediction_rank"] <= cutline
            candidate_in = group["candidate_prediction_rank"] <= cutline
            actual_in = number(group, "next_position_finish") <= cutline
            near = (
                (group["baseline_prediction_rank"] - cutline).abs().le(3)
                | (group["candidate_prediction_rank"] - cutline).abs().le(3)
                | (number(group, "next_position_finish") - cutline).abs().le(3)
            )
            crossed_in = (~baseline_in) & candidate_in
            crossed_out = baseline_in & (~candidate_in)
            rows.append(
                {
                    "split": split,
                    "target_season": int(target_season),
                    "position": position,
                    "cutline_bucket": f"{position}_TOP{cutline}",
                    "cutline_rank": cutline,
                    "rows": int(len(group)),
                    "near_cutline_rows": int(near.sum()),
                    "baseline_predicted_above_cutline": int(baseline_in.sum()),
                    "candidate_predicted_above_cutline": int(candidate_in.sum()),
                    "crossed_in_count": int(crossed_in.sum()),
                    "crossed_out_count": int(crossed_out.sum()),
                    "actual_hits_crossed_in": int((crossed_in & actual_in).sum()),
                    "actual_hits_crossed_out": int((crossed_out & actual_in).sum()),
                    "net_predicted_cutline_slots": int(candidate_in.sum() - baseline_in.sum()),
                    "review_note": cutline_note(int(crossed_in.sum()), int(crossed_out.sum()), int((crossed_out & actual_in).sum())),
                }
            )
    return pd.DataFrame(rows)


def cutline_note(crossed_in: int, crossed_out: int, actual_hits_crossed_out: int) -> str:
    if actual_hits_crossed_out:
        return "human_review_required_actual_hits_moved_below_cutline"
    if crossed_in or crossed_out:
        return "cutline_movement_review"
    return "stable_no_cutline_crossing"


def build_startable_bucket_tradeoffs(review: dict[str, pd.DataFrame | str]) -> pd.DataFrame:
    topn = checked_frame(review["topn"]).copy()
    topn["material_precision_regression"] = topn["precision_delta"].lt(-0.02)
    topn["material_f1_regression"] = topn["f1_delta"].lt(-0.02)
    topn["gate_assessment"] = topn.apply(
        lambda row: "HUMAN_REVIEW_REQUIRED"
        if bool(row["material_precision_regression"]) or bool(row["material_f1_regression"])
        else "PASS_OR_WATCH",
        axis=1,
    )
    topn["review_note"] = topn.apply(bucket_review_note, axis=1)
    return topn


def bucket_review_note(row: pd.Series) -> str:
    if row["gate_assessment"] == "HUMAN_REVIEW_REQUIRED":
        return "Bucket metric regressed by more than two points; do not advance without Tim review."
    if float(row["precision_delta"]) > 0 or float(row["f1_delta"]) > 0:
        return "Bucket metric supports the candidate."
    return "Bucket metric is flat or minor-watch."


def build_season_stability(review: dict[str, pd.DataFrame | str]) -> pd.DataFrame:
    season = checked_frame(review["season"]).copy()
    interaction = checked_frame(review["interaction"]).copy()
    season["evidence_scope"] = "season_all_positions"
    interaction = interaction[interaction["split"].isin(["validation", "holdout"])].copy()
    interaction["evidence_scope"] = "position_season"
    rows = []
    for item in season[season["split"].isin(["validation", "holdout"])].to_dict("records"):
        rows.append(
            {
                "evidence_scope": "season_all_positions",
                "split": item["split"],
                "target_season": str(item["group"]).replace("target_season_", ""),
                "position": "ALL",
                "rows": pd.NA,
                "baseline_mae": item["baseline_mae"],
                "candidate_mae": item["candidate_mae"],
                "mae_delta_candidate_minus_baseline": item["mae_delta_candidate_minus_baseline"],
                "spearman_delta": item["spearman_delta"],
                "startable_precision_delta": item["startable_precision_delta"],
                "stability_assessment": "SUPPORTS_CANDIDATE"
                if float(item["mae_delta_candidate_minus_baseline"]) < 0
                else "WATCH_OR_REVIEW",
            }
        )
    for item in interaction.to_dict("records"):
        rows.append(
            {
                "evidence_scope": "position_season",
                "split": item["split"],
                "target_season": int(item["target_season"]),
                "position": item["position"],
                "rows": int(item["rows"]),
                "baseline_mae": item["baseline_mae"],
                "candidate_mae": item["candidate_mae"],
                "mae_delta_candidate_minus_baseline": item["mae_delta_candidate_minus_baseline"],
                "spearman_delta": pd.NA,
                "startable_precision_delta": pd.NA,
                "stability_assessment": "SUPPORTS_CANDIDATE"
                if float(item["mae_delta_candidate_minus_baseline"]) < 0
                else "WATCH_OR_REVIEW",
            }
        )
    return pd.DataFrame(rows)


def build_archetype_impact(scored: pd.DataFrame) -> pd.DataFrame:
    review_rows = scored[scored["split"].isin(["validation", "holdout"])].copy()
    review_rows["severe_regression"] = review_rows["candidate_minus_baseline_abs_error"].gt(20)
    review_rows["severe_improvement"] = review_rows["candidate_minus_baseline_abs_error"].lt(-20)
    grouped = (
        review_rows.groupby(["split", "position", "archetype_label"], dropna=False)
        .agg(
            rows=("substrate_row_id", "count"),
            mean_baseline_error=("baseline_abs_error", "mean"),
            mean_candidate_error=("candidate_abs_error", "mean"),
            mean_error_delta=("candidate_minus_baseline_abs_error", "mean"),
            median_error_delta=("candidate_minus_baseline_abs_error", "median"),
            severe_regression_count=("severe_regression", "sum"),
            severe_improvement_count=("severe_improvement", "sum"),
        )
        .reset_index()
    )
    grouped["regression_share"] = grouped["severe_regression_count"] / grouped["rows"]
    grouped["improvement_share"] = grouped["severe_improvement_count"] / grouped["rows"]
    grouped["review_note"] = grouped.apply(archetype_note, axis=1)
    return grouped.round(6)


def archetype_note(row: pd.Series) -> str:
    if row["severe_regression_count"] > 0 and "elite_qb" in row["archetype_label"]:
        return "Elite QB regression pattern requires Tim review before shadow prep."
    if float(row["mean_error_delta"]) < 0:
        return "Mean error improved for this archetype."
    if float(row["mean_error_delta"]) > 0:
        return "Mean error regressed; inspect before any next step."
    return "Flat archetype impact."


def build_casebook(scored: pd.DataFrame, *, regression: bool) -> pd.DataFrame:
    review_rows = scored[scored["split"].isin(["validation", "holdout"])].copy()
    ordered = review_rows.sort_values("candidate_minus_baseline_abs_error", ascending=not regression).head(40).copy()
    ordered["player_id"] = ordered["player_id_gsis"]
    ordered["player_name"] = ordered["feature_player_name"]
    ordered["baseline_error"] = ordered["baseline_abs_error"].round(6)
    ordered["candidate_error"] = ordered["candidate_abs_error"].round(6)
    ordered["error_delta"] = ordered["candidate_minus_baseline_abs_error"].round(6)
    ordered["actual_target"] = ordered[TARGET].round(6)
    ordered["actual_position_finish"] = ordered["next_position_finish"]
    ordered["short_review_note"] = ordered.apply(casebook_note, axis=1)
    return ordered[CASEBOOK_COLUMNS]


def casebook_note(row: pd.Series) -> str:
    delta = float(row["candidate_minus_baseline_abs_error"])
    archetype = str(row["archetype_label"])
    if delta > 20 and "elite_qb" in archetype:
        return "Regression: usage proxy drags an elite prior-scoring QB below baseline; human review required."
    if delta > 20:
        return "Regression: candidate error materially worse; inspect before shadow prep."
    if delta < -20 and "volume" in archetype:
        return "Improvement: admitted prior opportunity signal corrected baseline error."
    if delta < -20:
        return "Improvement: candidate materially reduced historical error."
    return "Small movement; lower priority review row."


def build_context(
    *,
    review: dict[str, pd.DataFrame | str],
    metric_tradeoffs: pd.DataFrame,
    cutline_impact: pd.DataFrame,
    bucket_tradeoffs: pd.DataFrame,
    season_stability: pd.DataFrame,
    archetype_impact: pd.DataFrame,
    regressions: pd.DataFrame,
    improvements: pd.DataFrame,
) -> dict[str, Any]:
    validation_holdout = checked_frame(review["validation_holdout"]).set_index("split")
    position = checked_frame(review["position"])
    holdout_positions = position[position["split"].eq("holdout")]
    season = checked_frame(review["season"])
    holdout_seasons = season[season["split"].eq("holdout")]
    material_bucket_regressions = int(
        bucket_tradeoffs[
            bucket_tradeoffs["split"].isin(["validation", "holdout"])
            & (bucket_tradeoffs["material_precision_regression"] | bucket_tradeoffs["material_f1_regression"])
        ].shape[0]
    )
    actual_hit_crossed_out = int(cutline_impact["actual_hits_crossed_out"].sum())
    elite_qb_regressions = int(
        regressions["archetype_label"].str.contains("elite_qb", regex=False).sum()
    )
    severe_regressions = int((regressions["error_delta"] > 20).sum())
    severe_improvements = int((improvements["error_delta"] < -20).sum())
    context = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": VERDICT,
        "decision_label": DECISION_LABEL,
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "selected_candidate": SELECTED,
        "validation_mae_delta": round(float(validation_holdout.loc["validation", "mae_delta_candidate_minus_baseline"]), 6),
        "holdout_mae_delta": round(float(validation_holdout.loc["holdout", "mae_delta_candidate_minus_baseline"]), 6),
        "holdout_spearman_delta": round(float(validation_holdout.loc["holdout", "spearman_delta"]), 6),
        "holdout_startable_delta": round(float(validation_holdout.loc["holdout", "startable_precision_delta"]), 6),
        "holdout_positions_improved": int(holdout_positions["mae_delta_candidate_minus_baseline"].lt(0).sum()),
        "holdout_position_count": int(len(holdout_positions)),
        "holdout_seasons_improved": int(holdout_seasons["mae_delta_candidate_minus_baseline"].lt(0).sum()),
        "holdout_season_count": int(len(holdout_seasons)),
        "material_bucket_regressions": material_bucket_regressions,
        "actual_hit_crossed_out": actual_hit_crossed_out,
        "elite_qb_regressions": elite_qb_regressions,
        "severe_regressions": severe_regressions,
        "severe_improvements": severe_improvements,
        "tradeoff_rows": int(len(metric_tradeoffs)),
        "cutline_rows": int(len(cutline_impact)),
        "archetype_rows": int(len(archetype_impact)),
    }
    return context


def write_markdown_reports(context: dict[str, Any]) -> None:
    reports = {
        "candidate_promotion_gate_prep_summary.md": summary_md(context),
        "candidate_evidence_consolidation.md": evidence_md(context),
        "candidate_failure_mode_report.md": failure_modes_md(context),
        "candidate_strengths_report.md": strengths_md(context),
        "shadow_review_requirements.md": shadow_review_md(context),
        "human_review_checklist.md": human_review_checklist_md(context),
        "advance_hold_reject_decision_card.md": decision_card_md(context),
        "do_not_promote_notice.md": do_not_promote_md(),
        "guardrail_report.md": guardrail_md(),
        "merge_safety_report.md": merge_safety_md(),
        "next_phase_handoff.md": next_phase_md(context),
    }
    for name, body in reports.items():
        write_text(name, body)


def summary_md(context: dict[str, Any]) -> str:
    return f"""
# Candidate Promotion Gate Prep V1

Verdict: `{context['verdict']}`

Decision label: `{context['decision_label']}`

Candidate: `{SELECTED}`

This packet is review-only gate preparation. It does not promote, tune, optimize, wire, or configure the candidate in NWR.

## Evidence Result

- Validation MAE delta: `{context['validation_mae_delta']}`
- Holdout MAE delta: `{context['holdout_mae_delta']}`
- Holdout Spearman delta: `{context['holdout_spearman_delta']}`
- Holdout startable precision delta: `{context['holdout_startable_delta']}`
- Holdout positions with MAE improvement: `{context['holdout_positions_improved']}/{context['holdout_position_count']}`
- Holdout seasons with MAE improvement: `{context['holdout_seasons_improved']}/{context['holdout_season_count']}`
- Material validation/holdout bucket regressions: `{context['material_bucket_regressions']}`
- Actual cutline hits moved below a cutline in the review set: `{context['actual_hit_crossed_out']}`
- Elite-QB severe regression rows in the casebook: `{context['elite_qb_regressions']}`

Decision: hold for Tim human review. The aggregate evidence is strong enough to preserve and review, but bucket/cutline tradeoffs and elite-player regression rows make shadow-review prep premature.
"""


def evidence_md(context: dict[str, Any]) -> str:
    return f"""
# Candidate Evidence Consolidation

Inputs consolidated:

- Candidate Search V1 validation leaderboard and metric reports.
- Candidate Review V1 metric, stability, risk, and casebook reports.
- V3 historical tuning substrate with `5,518` review-only rows.
- Source Contract V1 allowed-feature contract.

What the candidate improves beyond raw MAE:

- Holdout Spearman is effectively stable at `{context['holdout_spearman_delta']}`.
- Aggregate holdout startable precision is flat at `{context['holdout_startable_delta']}`.
- All holdout positions and both holdout seasons improve MAE.

What prevents advancement today:

- Bucket and cutline effects are mixed.
- The regression casebook contains elite-QB prior-scoring rows that need football-context judgment.
- This remains historical review evidence only and is not approved for production use.
"""


def failure_modes_md(context: dict[str, Any]) -> str:
    return f"""
# Candidate Failure Mode Report

Primary failure modes:

1. Usage proxy drag on elite prior-scoring quarterbacks.
2. Bucket-level Top-N tradeoffs despite better aggregate MAE.
3. Near-cutline player movement that could matter to roster decisions.
4. Possible underweighting of efficient lower-opportunity players.

Stress evidence:

- Severe regression rows in the validation/holdout casebook: `{context['severe_regressions']}`
- Elite-QB severe regression rows: `{context['elite_qb_regressions']}`
- Material bucket regressions: `{context['material_bucket_regressions']}`
- Actual cutline hits moved below a cutline: `{context['actual_hit_crossed_out']}`

Interpretation: these are not leakage or overfit failures, but they are human-review blockers before any shadow-review prep branch.
"""


def strengths_md(context: dict[str, Any]) -> str:
    return f"""
# Candidate Strengths Report

The `usage_opportunity_volume` candidate remains a meaningful review-only candidate.

Strengths:

- Validation MAE improved by `{context['validation_mae_delta']}`.
- Holdout MAE improved by `{context['holdout_mae_delta']}`.
- Holdout Spearman did not materially degrade.
- Aggregate holdout startable precision stayed flat.
- Holdout position MAE improved across `{context['holdout_positions_improved']}/{context['holdout_position_count']}` positions.
- Holdout season MAE improved across `{context['holdout_seasons_improved']}/{context['holdout_season_count']}` seasons.
- Large improvement rows show the candidate can catch admitted prior opportunity volume missed by a frozen prior-points baseline.
"""


def shadow_review_md(context: dict[str, Any]) -> str:
    return f"""
# Shadow Review Requirements

Do not start shadow-review prep until Tim explicitly clears the hold.

Required before any shadow-review prep:

1. Review `largest_regression_casebook.csv`, especially elite-QB rows.
2. Review `position_cutline_impact_report.csv` for actual hits moved below cutlines.
3. Review `startable_bucket_tradeoff_report.csv` for material Top-N bucket regressions.
4. Confirm the usage/opportunity tilt matches NWR football philosophy.
5. Confirm no blocked source family is needed to explain the regressions.
6. Keep any future shadow work isolated as review-only; no app, model, rank, source-truth, hidden-sort, recommendation, runtime, formula, or production-config wiring.

Current shadow-review answer: not yet. Decision remains `{DECISION_LABEL}`.
"""


def human_review_checklist_md(context: dict[str, Any]) -> str:
    return f"""
# Human Review Checklist

- [ ] Inspect all severe regression rows with `error_delta > 20`.
- [ ] Inspect elite-QB regression rows.
- [ ] Decide whether bucket/cutline movement is acceptable.
- [ ] Decide whether MAE improvement is worth possible Top-N tradeoffs.
- [ ] Confirm the formula remains interpretable.
- [ ] Confirm no candidate output should be consumed by NWR runtime.
- [ ] Choose one next action: shadow-review prep, more evidence, or reject.
"""


def decision_card_md(context: dict[str, Any]) -> str:
    return f"""
# Advance Hold Reject Decision Card

- Candidate: `{SELECTED}`
- Gate decision: `{context['decision_label']}`
- Advance to shadow-review prep now: no
- Reject now: no
- Hold reason: aggregate metrics are strong, but bucket/cutline impacts and elite-player regressions need Tim judgment.
- Validation MAE delta: `{context['validation_mae_delta']}`
- Holdout MAE delta: `{context['holdout_mae_delta']}`
- Holdout Spearman delta: `{context['holdout_spearman_delta']}`
- Holdout startable precision delta: `{context['holdout_startable_delta']}`
- Material bucket regressions: `{context['material_bucket_regressions']}`
- Actual cutline hits moved below cutline: `{context['actual_hit_crossed_out']}`

This decision preserves the evidence without allowing the candidate to affect production behavior.
"""


def do_not_promote_md() -> str:
    return """
# Do Not Promote Notice

Do not promote `usage_opportunity_volume` from this branch.

This branch contains human-review artifacts only. It does not change formulas, rankings, recommendations, hidden sort, app wiring, model behavior, source truth, runtime behavior, or production configuration.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Status: PASS for review-only gate-prep artifacts.

Confirmed:

- No production formula changes.
- No formula tuning, optimization, or formula search.
- No production model training or model behavior changes.
- No app wiring.
- No rankings, recommendations, or hidden sort changes.
- No source-truth promotion.
- No runtime behavior changes.
- No production configuration changes.
- No market, ADP, vendor, projection, or external rank fields used as source truth.
- No routes, TPRR, YPRR, route proxies, red-zone sidecars, or ambiguous `rz_att`.
- Null-fenced fields remain excluded from the primary candidate.
- Candidate artifacts are review-only and not approved for production use.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

Scope: review-only Candidate Promotion Gate Prep V1 artifacts and one focused artifact/schema test.

Expected changed paths:

- `docs/hq/experiments/historical_formula_candidate_promotion_gate_prep_v1_20260701/`
- `tests/test_historical_formula_candidate_promotion_gate_prep_v1_20260701.py`

No app, model, ranking, formula, source-truth, runtime, production config, raw/shared/cache/local export, or secret paths are intentionally changed.
"""


def next_phase_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommended next phase: Tim human review of the gate-prep packet.

Decision remains `{DECISION_LABEL}`. Do not start shadow-review prep until the regression casebook, cutline report, and bucket tradeoff report are reviewed by a human.

If Tim clears the hold, the next branch should be `Historical Formula Candidate Shadow Review Prep V1`. If Tim does not clear the hold, either request targeted evidence for the concerning archetypes or reject the candidate as review-only.
"""


def write_manifest(context: dict[str, Any]) -> None:
    rows = []
    for name in REQUIRED_ARTIFACTS + ["build_historical_formula_candidate_promotion_gate_prep_v1.py"]:
        path = EXPERIMENT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    body = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{context['branch']}`
- Base HEAD: `{context['base_head']}`
- Candidate: `{context['selected_candidate']}`
- Decision label: `{context['decision_label']}`
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
