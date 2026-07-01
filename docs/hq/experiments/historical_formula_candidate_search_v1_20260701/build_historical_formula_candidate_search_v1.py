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
READINESS_DIR = EXPERIMENT_DIR.parent / "historical_formula_tuning_readiness_gate_v1_20260701"

SUBSTRATE_PATH = V3_DIR / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
ALLOWED_CONTRACT = SOURCE_CONTRACT_DIR / "allowed_review_only_feature_contract_v1.csv"
NULL_FENCED_CONTRACT = SOURCE_CONTRACT_DIR / "null_fenced_feature_contract_v1.csv"
BLOCKED_CONTRACT = SOURCE_CONTRACT_DIR / "blocked_feature_contract_v1.csv"

BASE_HEAD = "9ca171833d0b6fcc800b3d3e7d47b1c34e824d42"
BRANCH = "work/historical-formula-candidate-search-v1-20260701"
READINESS_DECISION = "GO_LIMITED_FORMULA_SEARCH_REVIEW_ONLY"

FORBIDDEN_COLUMN_TOKENS = (
    "route",
    "tprr",
    "yprr",
    "rz_att",
    "adp",
    "market",
    "projection",
    "vendor",
    "depth",
    "injury",
    "schedule",
    "active_weeks",
    "is_active_any_week",
)
NULL_FENCED_FEATURES = [
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
]
TARGET = "next_nwr_points"
BASELINE_ID = "baseline_v3_prior_points"


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    family_id: str
    family_name: str
    primary_or_sensitivity: str
    formula: str
    features: list[str]
    positions: str = "QB|RB|WR|TE"


CANDIDATES = [
    Candidate(
        BASELINE_ID,
        "baseline_v3_prior_points",
        "Frozen V3 baseline",
        "primary_baseline",
        "prior_nwr_points",
        ["prior_nwr_points"],
    ),
    Candidate(
        "conservative_ppg_games_blend",
        "conservative_ppg_games_blend",
        "Conservative PPG/games blend",
        "primary",
        "0.65 * prior_nwr_points + 0.35 * prior_nwr_ppg * 14",
        ["prior_nwr_points", "prior_nwr_ppg", "prior_games"],
    ),
    Candidate(
        "usage_opportunity_volume",
        "usage_volume_opportunity",
        "Usage/opportunity volume variant",
        "primary",
        "0.70 * prior_nwr_points + 0.30 * (0.40*carries + 0.55*receptions + 0.20*targets + 0.15*opportunities)",
        ["prior_nwr_points", "prior_carries", "prior_receptions", "prior_targets", "prior_opportunities"],
    ),
    Candidate(
        "yards_first_down_production",
        "production_yards_first_downs",
        "Yards/first-down production variant",
        "primary",
        "0.65 * prior_nwr_points + 0.35 * yards_and_first_down_points_proxy",
        [
            "prior_nwr_points",
            "prior_rushing_yards",
            "prior_receiving_yards",
            "prior_passing_yards",
            "prior_rushing_first_downs",
            "prior_receiving_first_downs",
            "prior_passing_first_downs",
        ],
    ),
    Candidate(
        "qb_td_dampened_review",
        "td_dampened_scoring_review",
        "QB TD-dampened review variant",
        "primary",
        "QB rows use dampened passing-TD blend; non-QB rows retain frozen baseline for aggregate comparability",
        [
            "prior_nwr_points",
            "prior_nwr_ppg",
            "prior_passing_yards",
            "prior_passing_attempts",
            "prior_passing_completions",
            "prior_passing_first_downs",
            "prior_passing_td",
            "prior_interceptions",
        ],
    ),
    Candidate(
        "position_specific_interpretable_blend",
        "position_specific_interpretable_blend",
        "Position-specific interpretable blend",
        "primary",
        "Fixed position-specific blend of prior scoring, usage, yards, and first-down context",
        [
            "prior_nwr_points",
            "prior_nwr_ppg",
            "prior_games",
            "prior_targets",
            "prior_carries",
            "prior_receptions",
            "prior_touches",
            "prior_opportunities",
            "prior_rushing_yards",
            "prior_receiving_yards",
            "prior_rushing_first_downs",
            "prior_receiving_first_downs",
            "prior_passing_attempts",
            "prior_passing_completions",
            "prior_passing_yards",
            "prior_passing_td",
            "prior_interceptions",
            "prior_passing_first_downs",
        ],
    ),
    Candidate(
        "optional_air_yac_sensitivity",
        "optional_air_yac_sensitivity",
        "Optional air/YAC sensitivity variant",
        "sensitivity",
        "Eligible non-null rows only: 0.85 * position_specific_interpretable_blend + 0.15 * air_yac_proxy",
        ["prior_receiving_air_yards", "prior_receiving_yards_after_catch"],
        positions="RB|WR|TE",
    ),
    Candidate(
        "optional_snap_context_sensitivity",
        "optional_snap_context_sensitivity",
        "Optional snap-context sensitivity variant",
        "sensitivity",
        "Eligible non-null rows only: 0.85 * position_specific_interpretable_blend + 0.15 * snap_context_proxy",
        ["prior_offensive_snaps", "prior_offense_pct"],
    ),
    Candidate(
        "small_fixed_review_ensemble",
        "simple_ranked_ensemble_review",
        "Small fixed review ensemble",
        "secondary_review",
        "Mean of frozen baseline, PPG blend, usage volume, yards/first-down, and position-specific blend",
        [
            "baseline_v3_prior_points",
            "conservative_ppg_games_blend",
            "usage_opportunity_volume",
            "yards_first_down_production",
            "position_specific_interpretable_blend",
        ],
    ),
]


def main() -> int:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    substrate = pd.read_parquet(SUBSTRATE_PATH)
    allowed_contract = pd.read_csv(ALLOWED_CONTRACT)
    null_fenced_contract = pd.read_csv(NULL_FENCED_CONTRACT)
    blocked_contract = pd.read_csv(BLOCKED_CONTRACT)
    validate_inputs(substrate, allowed_contract, null_fenced_contract, blocked_contract)

    scored = add_splits(substrate.copy())
    scored = add_candidate_scores(scored)
    validate_candidate_scores(scored)

    definitions = candidate_definitions()
    family_matrix = candidate_family_matrix(definitions)
    split_report = split_report_frame(scored)
    baseline_metrics = metric_report(scored, [BASELINE_ID], ["train", "validation", "holdout"])
    train_validation_candidates = [
        candidate.candidate_id
        for candidate in CANDIDATES
        if candidate.candidate_id != BASELINE_ID
    ]
    candidate_metrics = metric_report(
        scored,
        train_validation_candidates,
        ["train", "validation"],
        include_sensitivity=True,
    )
    validation_leaderboard = make_validation_leaderboard(scored, baseline_metrics, candidate_metrics)
    selected = select_candidate(validation_leaderboard, scored)
    holdout = holdout_report(scored, selected)
    position_report = position_metric_report(scored, selected)
    season_report = season_metric_report(scored, selected)
    topn_report = topn_bucket_report(scored, selected)
    sensitivity_report = null_fenced_sensitivity_report(scored)
    overfit_report = overfit_frame(scored, selected)

    write_csv(definitions, "candidate_formula_definitions.csv")
    write_csv(family_matrix, "candidate_formula_family_matrix.csv")
    write_csv(split_report, "train_validation_holdout_split_report.csv")
    write_csv(baseline_metrics, "baseline_metric_report.csv")
    write_csv(candidate_metrics, "candidate_metric_report.csv")
    write_csv(validation_leaderboard, "validation_leaderboard.csv")
    write_csv(holdout, "holdout_evaluation_report.csv")
    write_csv(position_report, "position_level_metric_report.csv")
    write_csv(season_report, "season_level_metric_report.csv")
    write_csv(topn_report, "topn_bucket_metric_report.csv")
    write_csv(sensitivity_report, "null_fenced_sensitivity_report.csv")
    write_csv(overfit_report, "overfit_gap_matrix.csv")

    decision = final_decision(selected, validation_leaderboard, holdout, position_report, season_report)
    context = build_context(scored, selected, decision, baseline_metrics, validation_leaderboard, holdout)
    write_markdown_reports(context, selected, decision)
    write_manifest(context)

    print(f"wrote={EXPERIMENT_DIR}")
    print(f"candidate_verdict={context['candidate_verdict']}")
    print(f"selected_candidate={selected['candidate_id']}")
    print(f"final_verdict={context['verdict']}")
    return 0


def validate_inputs(
    substrate: pd.DataFrame,
    allowed_contract: pd.DataFrame,
    null_fenced_contract: pd.DataFrame,
    blocked_contract: pd.DataFrame,
) -> None:
    if len(substrate) != 5518:
        raise ValueError(f"Expected 5518 V3 rows, got {len(substrate)}")
    if not (substrate["target_season"] == substrate["feature_season"] + 1).all():
        raise ValueError("Feature season N to target season N+1 lag is broken")
    split_counts = add_splits(substrate.copy())["split"].value_counts().to_dict()
    if split_counts != {"train": 3716, "validation": 912, "holdout": 890}:
        raise ValueError(f"Unexpected split counts: {split_counts}")
    allowed = set(allowed_contract["feature"])
    null_fenced = set(null_fenced_contract["feature"])
    if len(allowed) != 18 or len(null_fenced) != 4:
        raise ValueError("Unexpected source-contract feature counts")
    if set(NULL_FENCED_FEATURES) != null_fenced:
        raise ValueError("Null-fenced feature contract does not match candidate-search policy")
    primary_features = {
        feature
        for candidate in CANDIDATES
        if candidate.primary_or_sensitivity in {"primary", "primary_baseline", "secondary_review"}
        for feature in candidate.features
        if feature.startswith("prior_")
    }
    forbidden_primary = primary_features & null_fenced
    if forbidden_primary:
        raise ValueError(f"Null-fenced fields used in primary pass: {sorted(forbidden_primary)}")
    forbidden_columns = [
        col for col in substrate.columns if any(token in col.lower() for token in FORBIDDEN_COLUMN_TOKENS)
    ]
    if forbidden_columns:
        raise ValueError(f"Forbidden substrate columns present: {forbidden_columns}")
    blocked_features = set(blocked_contract["feature"])
    required_blocked = {
        "red_zone_targets",
        "red_zone_carries",
        "red_zone_pass_attempts",
        "ambiguous_rz_att",
        "routes_tprr_yprr_family",
        "market_fields",
        "adp_fields",
        "vendor_fields",
        "projection_fields",
        "rank_fields",
    }
    if not required_blocked.issubset(blocked_features):
        raise ValueError("Blocked source-contract families are incomplete")


def add_splits(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["split"] = pd.NA
    output.loc[output["feature_season"].between(2012, 2020), "split"] = "train"
    output.loc[output["feature_season"].between(2021, 2022), "split"] = "validation"
    output.loc[output["feature_season"].between(2023, 2024), "split"] = "holdout"
    if output["split"].isna().any():
        raise ValueError("Rows outside fixed readiness-gate split policy")
    return output


def add_candidate_scores(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output[BASELINE_ID] = num(output, "prior_nwr_points")
    output["conservative_ppg_games_blend"] = (
        0.65 * num(output, "prior_nwr_points") + 0.35 * num(output, "prior_nwr_ppg") * 14.0
    )
    usage_proxy = (
        0.40 * num(output, "prior_carries")
        + 0.55 * num(output, "prior_receptions")
        + 0.20 * num(output, "prior_targets")
        + 0.15 * num(output, "prior_opportunities")
    )
    output["usage_opportunity_volume"] = 0.70 * num(output, "prior_nwr_points") + 0.30 * usage_proxy

    production_proxy = (
        0.10 * num(output, "prior_rushing_yards")
        + 0.10 * num(output, "prior_receiving_yards")
        + 0.04 * num(output, "prior_passing_yards")
        + 0.80
        * (
            num(output, "prior_rushing_first_downs")
            + num(output, "prior_receiving_first_downs")
            + num(output, "prior_passing_first_downs")
        )
    )
    output["yards_first_down_production"] = (
        0.65 * num(output, "prior_nwr_points") + 0.35 * production_proxy
    )

    qb_proxy = (
        0.04 * num(output, "prior_passing_yards")
        + 0.03 * num(output, "prior_passing_attempts")
        + 0.05 * num(output, "prior_passing_completions")
        + 0.60 * num(output, "prior_passing_first_downs")
        - 0.80 * num(output, "prior_passing_td")
        - 1.00 * num(output, "prior_interceptions")
    )
    output["qb_td_dampened_review"] = output[BASELINE_ID]
    qb_mask = output["position"].eq("QB")
    output.loc[qb_mask, "qb_td_dampened_review"] = (
        0.70 * num(output.loc[qb_mask], "prior_nwr_points")
        + 0.15 * num(output.loc[qb_mask], "prior_nwr_ppg") * 14.0
        + 0.15 * qb_proxy[qb_mask]
    )

    output["position_specific_interpretable_blend"] = output[BASELINE_ID]
    qb_score = (
        0.48 * num(output, "prior_nwr_points")
        + 0.22 * num(output, "prior_nwr_ppg") * 14.0
        + 0.30
        * (
            0.04 * num(output, "prior_passing_yards")
            + 0.04 * num(output, "prior_passing_attempts")
            + 0.07 * num(output, "prior_passing_completions")
            + 0.60 * num(output, "prior_passing_first_downs")
        )
    )
    rb_score = 0.45 * num(output, "prior_nwr_points") + 0.35 * usage_proxy + 0.20 * production_proxy
    wrte_score = (
        0.45 * num(output, "prior_nwr_points")
        + 0.30
        * (
            0.35 * num(output, "prior_targets")
            + 0.85 * num(output, "prior_receptions")
            + 0.10 * num(output, "prior_opportunities")
        )
        + 0.25
        * (
            0.10 * num(output, "prior_receiving_yards")
            + 0.80 * num(output, "prior_receiving_first_downs")
        )
    )
    output.loc[output["position"].eq("QB"), "position_specific_interpretable_blend"] = qb_score[
        output["position"].eq("QB")
    ]
    output.loc[output["position"].eq("RB"), "position_specific_interpretable_blend"] = rb_score[
        output["position"].eq("RB")
    ]
    output.loc[output["position"].isin(["WR", "TE"]), "position_specific_interpretable_blend"] = wrte_score[
        output["position"].isin(["WR", "TE"])
    ]

    output["small_fixed_review_ensemble"] = output[
        [
            BASELINE_ID,
            "conservative_ppg_games_blend",
            "usage_opportunity_volume",
            "yards_first_down_production",
            "position_specific_interpretable_blend",
        ]
    ].mean(axis=1)

    air_yac_proxy = (
        0.05 * num_nullable(output, "prior_receiving_air_yards")
        + 0.10 * num_nullable(output, "prior_receiving_yards_after_catch")
    )
    output["optional_air_yac_sensitivity"] = pd.NA
    eligible_air = (
        output["position"].isin(["RB", "WR", "TE"])
        & output["prior_receiving_air_yards"].notna()
        & output["prior_receiving_yards_after_catch"].notna()
    )
    output.loc[eligible_air, "optional_air_yac_sensitivity"] = (
        0.85 * output.loc[eligible_air, "position_specific_interpretable_blend"]
        + 0.15 * air_yac_proxy[eligible_air]
    )

    snap_proxy = (
        0.12 * num_nullable(output, "prior_offensive_snaps")
        + 120.0 * num_nullable(output, "prior_offense_pct")
    )
    output["optional_snap_context_sensitivity"] = pd.NA
    eligible_snap = output["prior_offensive_snaps"].notna() & output["prior_offense_pct"].notna()
    output.loc[eligible_snap, "optional_snap_context_sensitivity"] = (
        0.85 * output.loc[eligible_snap, "position_specific_interpretable_blend"]
        + 0.15 * snap_proxy[eligible_snap]
    )
    return output


def validate_candidate_scores(frame: pd.DataFrame) -> None:
    primary = [
        candidate.candidate_id
        for candidate in CANDIDATES
        if candidate.primary_or_sensitivity in {"primary", "primary_baseline", "secondary_review"}
    ]
    for column in primary:
        if frame[column].isna().any():
            raise ValueError(f"Primary candidate has null predictions: {column}")
    for column in ["optional_air_yac_sensitivity", "optional_snap_context_sensitivity"]:
        if frame[column].notna().sum() == len(frame):
            raise ValueError(f"Sensitivity candidate unexpectedly has full coverage: {column}")


def num(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="raise").astype(float)


def num_nullable(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce").astype(float)


def metric_report(
    scored: pd.DataFrame,
    candidate_ids: list[str],
    splits: list[str],
    *,
    include_sensitivity: bool = False,
) -> pd.DataFrame:
    rows = []
    candidate_meta = {candidate.candidate_id: candidate for candidate in CANDIDATES}
    for candidate_id in candidate_ids:
        candidate = candidate_meta[candidate_id]
        if candidate.primary_or_sensitivity == "sensitivity" and not include_sensitivity:
            continue
        for split in splits:
            subset = scored[scored["split"].eq(split)].copy()
            if candidate.primary_or_sensitivity == "sensitivity":
                subset = subset[subset[candidate_id].notna()].copy()
            rows.append(metric_row(subset, candidate_id, split, "all_positions", candidate))
    return pd.DataFrame(rows)


def metric_row(
    subset: pd.DataFrame,
    candidate_id: str,
    split: str,
    group: str,
    candidate: Candidate | None = None,
) -> dict[str, Any]:
    if subset.empty:
        return {
            "candidate_id": candidate_id,
            "split": split,
            "group": group,
            "rows": 0,
            "mae": None,
            "spearman": None,
            "startable_precision_at_n": None,
            "startable_recall_at_n": None,
            "primary_or_sensitivity": candidate.primary_or_sensitivity if candidate else "",
        }
    pred = pd.to_numeric(subset[candidate_id], errors="coerce")
    actual = pd.to_numeric(subset[TARGET], errors="coerce")
    valid = pred.notna() & actual.notna()
    filtered = subset.loc[valid].copy()
    pred = pred[valid]
    actual = actual[valid]
    topn = startable_at_n(filtered, candidate_id)
    return {
        "candidate_id": candidate_id,
        "split": split,
        "group": group,
        "rows": int(len(filtered)),
        "mae": round(float((pred - actual).abs().mean()), 6),
        "spearman": round(float(pred.rank(method="average").corr(actual.rank(method="average"))), 6),
        "startable_precision_at_n": round(topn["precision"], 6),
        "startable_recall_at_n": round(topn["recall"], 6),
        "startable_f1_at_n": round(topn["f1"], 6),
        "primary_or_sensitivity": candidate.primary_or_sensitivity if candidate else "",
    }


def startable_at_n(subset: pd.DataFrame, candidate_id: str) -> dict[str, float]:
    predicted = []
    for (_season, position), group in subset.groupby(["target_season", "position"]):
        n = startable_n(position)
        group = group.sort_values(candidate_id, ascending=False).head(min(n, len(group)))
        predicted.append(group)
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


def make_validation_leaderboard(
    scored: pd.DataFrame,
    baseline_metrics: pd.DataFrame,
    candidate_metrics: pd.DataFrame,
) -> pd.DataFrame:
    baseline = baseline_metrics[baseline_metrics["split"].eq("validation")].iloc[0]
    validation = candidate_metrics[candidate_metrics["split"].eq("validation")].copy()
    validation["baseline_mae"] = float(baseline["mae"])
    validation["baseline_spearman"] = float(baseline["spearman"])
    validation["baseline_startable_precision_at_n"] = float(baseline["startable_precision_at_n"])
    validation["mae_delta_vs_baseline"] = validation["mae"] - validation["baseline_mae"]
    validation["spearman_delta_vs_baseline"] = validation["spearman"] - validation["baseline_spearman"]
    validation["startable_precision_delta_vs_baseline"] = (
        validation["startable_precision_at_n"] - validation["baseline_startable_precision_at_n"]
    )
    validation["position_harm_flag"] = validation["candidate_id"].map(
        lambda cid: position_harm_flag(scored, cid, "validation")
    )
    validation["season_isolation_flag"] = validation["candidate_id"].map(
        lambda cid: season_isolation_flag(scored, cid, "validation")
    )
    validation["selection_eligible"] = (
        validation["primary_or_sensitivity"].isin(["primary", "secondary_review"])
        & validation["mae_delta_vs_baseline"].lt(0)
        & validation["spearman_delta_vs_baseline"].ge(-0.03)
        & validation["startable_precision_delta_vs_baseline"].ge(-0.03)
        & ~validation["position_harm_flag"]
        & ~validation["season_isolation_flag"]
    )
    validation["leaderboard_sort_score"] = (
        -validation["mae_delta_vs_baseline"]
        + 8.0 * validation["spearman_delta_vs_baseline"].clip(lower=-0.02)
        + 4.0 * validation["startable_precision_delta_vs_baseline"].clip(lower=-0.02)
    )
    validation = validation.sort_values(
        ["selection_eligible", "leaderboard_sort_score", "mae_delta_vs_baseline"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    validation["validation_rank"] = validation.index + 1
    return validation


def position_harm_flag(scored: pd.DataFrame, candidate_id: str, split: str) -> bool:
    rows = []
    subset = scored[scored["split"].eq(split)]
    for position, group in subset.groupby("position"):
        candidate_mae = mae(group, candidate_id)
        baseline_mae = mae(group, BASELINE_ID)
        rows.append(candidate_mae - baseline_mae > max(5.0, baseline_mae * 0.08))
    return any(rows)


def season_isolation_flag(scored: pd.DataFrame, candidate_id: str, split: str) -> bool:
    subset = scored[scored["split"].eq(split)]
    deltas = []
    for _season, group in subset.groupby("target_season"):
        deltas.append(mae(group, candidate_id) - mae(group, BASELINE_ID))
    improvements = [delta for delta in deltas if delta < 0]
    return len(improvements) < max(1, len(deltas) // 2)


def mae(frame: pd.DataFrame, candidate_id: str) -> float:
    pred = pd.to_numeric(frame[candidate_id], errors="coerce")
    actual = pd.to_numeric(frame[TARGET], errors="coerce")
    valid = pred.notna() & actual.notna()
    return float((pred[valid] - actual[valid]).abs().mean())


def select_candidate(validation_leaderboard: pd.DataFrame, scored: pd.DataFrame) -> dict[str, Any]:
    eligible = validation_leaderboard[validation_leaderboard["selection_eligible"]]
    if not eligible.empty:
        selected = eligible.iloc[0].to_dict()
        selected["selection_reason"] = "Best validation-only eligible candidate after MAE, rank, startable, position, and season checks."
        return selected
    non_sensitivity = validation_leaderboard[
        validation_leaderboard["primary_or_sensitivity"].isin(["primary", "secondary_review"])
    ]
    selected = non_sensitivity.iloc[0].to_dict()
    selected["selection_reason"] = "Best validation candidate selected for one-time holdout review, but it did not clear all human-review gates."
    return selected


def holdout_report(scored: pd.DataFrame, selected: dict[str, Any]) -> pd.DataFrame:
    candidate_ids = [BASELINE_ID]
    selected_id = selected["candidate_id"]
    if selected_id not in candidate_ids:
        candidate_ids.append(selected_id)
    rows = []
    meta = {candidate.candidate_id: candidate for candidate in CANDIDATES}
    for candidate_id in candidate_ids:
        rows.append(metric_row(scored[scored["split"].eq("holdout")], candidate_id, "holdout", "all_positions", meta[candidate_id]))
    output = pd.DataFrame(rows)
    baseline = output[output["candidate_id"].eq(BASELINE_ID)].iloc[0]
    output["holdout_mae_delta_vs_baseline"] = output["mae"] - float(baseline["mae"])
    output["holdout_spearman_delta_vs_baseline"] = output["spearman"] - float(baseline["spearman"])
    output["holdout_startable_precision_delta_vs_baseline"] = (
        output["startable_precision_at_n"] - float(baseline["startable_precision_at_n"])
    )
    output["holdout_evaluated_after_validation_selection"] = True
    return output


def position_metric_report(scored: pd.DataFrame, selected: dict[str, Any]) -> pd.DataFrame:
    candidate_ids = [BASELINE_ID, selected["candidate_id"]]
    rows = []
    meta = {candidate.candidate_id: candidate for candidate in CANDIDATES}
    for split in ["train", "validation", "holdout"]:
        for candidate_id in dict.fromkeys(candidate_ids):
            for position, group in scored[scored["split"].eq(split)].groupby("position"):
                rows.append(metric_row(group, candidate_id, split, position, meta[candidate_id]))
    return pd.DataFrame(rows)


def season_metric_report(scored: pd.DataFrame, selected: dict[str, Any]) -> pd.DataFrame:
    candidate_ids = [BASELINE_ID, selected["candidate_id"]]
    rows = []
    meta = {candidate.candidate_id: candidate for candidate in CANDIDATES}
    for split in ["train", "validation", "holdout"]:
        for candidate_id in dict.fromkeys(candidate_ids):
            for season, group in scored[scored["split"].eq(split)].groupby("target_season"):
                rows.append(metric_row(group, candidate_id, split, f"target_season_{int(season)}", meta[candidate_id]))
    return pd.DataFrame(rows)


def topn_bucket_report(scored: pd.DataFrame, selected: dict[str, Any]) -> pd.DataFrame:
    candidate_ids = list(dict.fromkeys([BASELINE_ID, selected["candidate_id"]]))
    rows = []
    for split in ["train", "validation", "holdout"]:
        split_df = scored[scored["split"].eq(split)]
        for candidate_id in candidate_ids:
            for position, buckets in bucket_columns().items():
                for label, column, n in buckets:
                    subset = split_df[split_df["position"].eq(position)]
                    rows.append(bucket_metric_row(subset, candidate_id, split, position, label, column, n))
    return pd.DataFrame(rows)


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
    actual = subset[actual_column].astype(bool)
    actual_ids = set(subset.loc[actual, "substrate_row_id"])
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


def null_fenced_sensitivity_report(scored: pd.DataFrame) -> pd.DataFrame:
    sensitivity_ids = ["optional_air_yac_sensitivity", "optional_snap_context_sensitivity"]
    baseline_for_rows = "position_specific_interpretable_blend"
    rows = []
    for candidate_id in sensitivity_ids:
        for split in ["train", "validation"]:
            subset = scored[scored["split"].eq(split)].copy()
            eligible = subset[subset[candidate_id].notna()].copy()
            sensitivity = metric_row(eligible, candidate_id, split, "eligible_rows", candidate_by_id(candidate_id))
            comparator = metric_row(eligible, baseline_for_rows, split, "eligible_rows", candidate_by_id("position_specific_interpretable_blend"))
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "split": split,
                    "eligible_rows": int(len(eligible)),
                    "excluded_null_fenced_rows": int(len(subset) - len(eligible)),
                    "sensitivity_mae": sensitivity["mae"],
                    "eligible_comparator_mae": comparator["mae"],
                    "mae_delta_vs_eligible_comparator": round(
                        float(sensitivity["mae"]) - float(comparator["mae"]), 6
                    )
                    if sensitivity["mae"] is not None and comparator["mae"] is not None
                    else None,
                    "null_handling": "Rows with null-fenced inputs are excluded from this sensitivity metric; missing values are not filled with zero.",
                    "primary_pass_used": False,
                    "production_approved": False,
                }
            )
    return pd.DataFrame(rows)


def overfit_frame(scored: pd.DataFrame, selected: dict[str, Any]) -> pd.DataFrame:
    candidate_ids = list(dict.fromkeys([BASELINE_ID, selected["candidate_id"]]))
    rows = []
    for candidate_id in candidate_ids:
        metrics = metric_report(scored, [candidate_id], ["train", "validation", "holdout"], include_sensitivity=True)
        by_split = metrics.set_index("split")
        rows.append(
            {
                "candidate_id": candidate_id,
                "train_mae": by_split.loc["train", "mae"],
                "validation_mae": by_split.loc["validation", "mae"],
                "holdout_mae": by_split.loc["holdout", "mae"],
                "validation_minus_train_mae": round(float(by_split.loc["validation", "mae"] - by_split.loc["train", "mae"]), 6),
                "holdout_minus_validation_mae": round(float(by_split.loc["holdout", "mae"] - by_split.loc["validation", "mae"]), 6),
                "train_spearman": by_split.loc["train", "spearman"],
                "validation_spearman": by_split.loc["validation", "spearman"],
                "holdout_spearman": by_split.loc["holdout", "spearman"],
                "overfit_flag": bool(
                    by_split.loc["holdout", "mae"] - by_split.loc["validation", "mae"] > 10
                    or by_split.loc["holdout", "spearman"] < by_split.loc["validation", "spearman"] - 0.08
                ),
            }
        )
    return pd.DataFrame(rows)


def final_decision(
    selected: dict[str, Any],
    validation_leaderboard: pd.DataFrame,
    holdout: pd.DataFrame,
    position_report: pd.DataFrame,
    season_report: pd.DataFrame,
) -> dict[str, Any]:
    selected_id = selected["candidate_id"]
    selected_validation = validation_leaderboard[validation_leaderboard["candidate_id"].eq(selected_id)].iloc[0]
    holdout_selected = holdout[holdout["candidate_id"].eq(selected_id)]
    if holdout_selected.empty:
        return {
            "candidate_verdict": "NO_CANDIDATE_BEATS_BASELINE",
            "worth_human_review": False,
            "reason": "No non-baseline candidate selected for holdout.",
        }
    holdout_row = holdout_selected.iloc[0]
    position_holdout = position_report[
        (position_report["split"].eq("holdout")) & (position_report["candidate_id"].eq(selected_id))
    ]
    baseline_position = position_report[
        (position_report["split"].eq("holdout")) & (position_report["candidate_id"].eq(BASELINE_ID))
    ].set_index("group")
    material_position_harm = False
    for row in position_holdout.to_dict("records"):
        baseline_mae = float(baseline_position.loc[row["group"], "mae"])
        if float(row["mae"]) - baseline_mae > max(6.0, baseline_mae * 0.10):
            material_position_harm = True
    holdout_material_degrade = (
        float(holdout_row["holdout_mae_delta_vs_baseline"]) > 4.0
        or float(holdout_row["holdout_spearman_delta_vs_baseline"]) < -0.04
        or float(holdout_row["holdout_startable_precision_delta_vs_baseline"]) < -0.04
    )
    validation_improved = (
        float(selected_validation["mae_delta_vs_baseline"]) < 0
        or float(selected_validation["spearman_delta_vs_baseline"]) > 0
        or float(selected_validation["startable_precision_delta_vs_baseline"]) > 0
    )
    if (
        validation_improved
        and not holdout_material_degrade
        and not material_position_harm
        and not bool(selected_validation["season_isolation_flag"])
    ):
        strong = (
            float(selected_validation["mae_delta_vs_baseline"]) < -1.0
            and float(holdout_row["holdout_mae_delta_vs_baseline"]) <= 0.5
            and float(holdout_row["holdout_spearman_delta_vs_baseline"]) >= -0.02
        )
        return {
            "candidate_verdict": "STRONG_REVIEW_ONLY_CANDIDATE_NOT_PRODUCTION_APPROVED"
            if strong
            else "MIXED_CANDIDATE_FOR_HUMAN_REVIEW_ONLY",
            "worth_human_review": True,
            "reason": "Selected candidate passed validation-only selection and did not materially degrade on holdout.",
        }
    if validation_improved:
        return {
            "candidate_verdict": "MIXED_CANDIDATE_FOR_HUMAN_REVIEW_ONLY",
            "worth_human_review": False,
            "reason": "Validation improved at least one metric, but holdout/position/stability checks were mixed.",
        }
    return {
        "candidate_verdict": "NO_CANDIDATE_BEATS_BASELINE",
        "worth_human_review": False,
        "reason": "No candidate clearly beat baseline across validation metrics.",
    }


def candidate_by_id(candidate_id: str) -> Candidate:
    for candidate in CANDIDATES:
        if candidate.candidate_id == candidate_id:
            return candidate
    return Candidate(candidate_id, candidate_id, candidate_id, "primary", candidate_id, [])


def candidate_definitions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "candidate_id": candidate.candidate_id,
                "family_id": candidate.family_id,
                "family_name": candidate.family_name,
                "primary_or_sensitivity": candidate.primary_or_sensitivity,
                "positions": candidate.positions,
                "formula_definition": candidate.formula,
                "features_used": "; ".join(candidate.features),
                "holdout_used_for_selection": False,
                "production_approved": False,
                "model_use_allowed": False,
                "training_allowed": False,
                "source_truth_allowed": False,
                "hidden_sort_allowed": False,
                "recommendation_allowed": False,
            }
            for candidate in CANDIDATES
        ]
    )


def candidate_family_matrix(definitions: pd.DataFrame) -> pd.DataFrame:
    output = definitions[
        [
            "family_id",
            "family_name",
            "candidate_id",
            "primary_or_sensitivity",
            "positions",
            "features_used",
            "production_approved",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
            "hidden_sort_allowed",
            "recommendation_allowed",
        ]
    ].copy()
    output["review_only_constraints"] = output["primary_or_sensitivity"].map(
        lambda value: "primary pass excludes null-fenced features"
        if value in {"primary", "primary_baseline", "secondary_review"}
        else "sensitivity only; null-fenced rows excluded rather than filled"
    )
    return output


def split_report_frame(scored: pd.DataFrame) -> pd.DataFrame:
    report = (
        scored.groupby(["split", "feature_season", "target_season", "position"])
        .agg(
            rows=("substrate_row_id", "count"),
            distinct_players=("player_id_gsis", "nunique"),
            startable_hits=("startable_hit", lambda value: int(value.sum())),
        )
        .reset_index()
        .sort_values(["split", "feature_season", "position"])
    )
    report["split_policy"] = "readiness_gate_fixed_feature_season_policy"
    report["holdout_used_for_selection"] = False
    return report


def write_csv(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(EXPERIMENT_DIR / name, index=False)


def build_context(
    scored: pd.DataFrame,
    selected: dict[str, Any],
    decision: dict[str, Any],
    baseline_metrics: pd.DataFrame,
    validation_leaderboard: pd.DataFrame,
    holdout: pd.DataFrame,
) -> dict[str, Any]:
    baseline_validation = baseline_metrics[baseline_metrics["split"].eq("validation")].iloc[0]
    baseline_holdout = baseline_metrics[baseline_metrics["split"].eq("holdout")].iloc[0]
    selected_holdout = holdout[holdout["candidate_id"].eq(selected["candidate_id"])]
    selected_holdout_row = selected_holdout.iloc[0].to_dict() if not selected_holdout.empty else {}
    best_validation = validation_leaderboard.iloc[0].to_dict()
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "GREEN_REVIEW_ONLY_CANDIDATE_SEARCH_COMPLETED",
        "candidate_verdict": decision["candidate_verdict"],
        "worth_human_review": bool(decision["worth_human_review"]),
        "decision_reason": decision["reason"],
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "rows": len(scored),
        "feature_seasons": f"{int(scored['feature_season'].min())}-{int(scored['feature_season'].max())}",
        "target_seasons": f"{int(scored['target_season'].min())}-{int(scored['target_season'].max())}",
        "position_counts": scored["position"].value_counts().sort_index().to_dict(),
        "train_rows": int(scored["split"].eq("train").sum()),
        "validation_rows": int(scored["split"].eq("validation").sum()),
        "holdout_rows": int(scored["split"].eq("holdout").sum()),
        "baseline_validation_mae": baseline_validation["mae"],
        "baseline_validation_spearman": baseline_validation["spearman"],
        "baseline_holdout_mae": baseline_holdout["mae"],
        "baseline_holdout_spearman": baseline_holdout["spearman"],
        "best_validation_candidate": best_validation["candidate_id"],
        "best_validation_mae_delta": best_validation["mae_delta_vs_baseline"],
        "selected_candidate": selected["candidate_id"],
        "selected_holdout_mae_delta": selected_holdout_row.get("holdout_mae_delta_vs_baseline", ""),
        "selected_holdout_spearman_delta": selected_holdout_row.get("holdout_spearman_delta_vs_baseline", ""),
        "selected_holdout_startable_delta": selected_holdout_row.get("holdout_startable_precision_delta_vs_baseline", ""),
    }


def write_markdown_reports(context: dict[str, Any], selected: dict[str, Any], decision: dict[str, Any]) -> None:
    write_text("historical_formula_candidate_search_summary.md", summary_md(context))
    write_text("candidate_search_scope.md", scope_md())
    write_text("baseline_formula_definition.md", baseline_md())
    write_text("candidate_selection_decision.md", selection_md(context, selected, decision))
    write_text("selected_candidate_review_packet.md", selected_packet_md(context, selected, decision))
    write_text("overfit_and_leakage_report.md", overfit_md(context))
    write_text("blocked_feature_compliance_report.md", blocked_md())
    write_text("production_non_promotion_report.md", non_promotion_md())
    write_text("guardrail_report.md", guardrail_md())
    write_text("merge_safety_report.md", merge_safety_md())
    write_text("next_phase_handoff.md", handoff_md(context))


def write_text(name: str, body: str) -> None:
    (EXPERIMENT_DIR / name).write_text(body.strip() + "\n", encoding="utf-8")


def summary_md(context: dict[str, Any]) -> str:
    return f"""
# Historical Formula Candidate Search V1

Verdict: `{context['verdict']}`

Candidate verdict: `{context['candidate_verdict']}`

This is a bounded review-only formula candidate search following the merged readiness gate decision `{READINESS_DECISION}`. It does not change production formulas, rankings, app behavior, model behavior, source truth, hidden sort, recommendations, runtime logic, or production config.

## Coverage

- Rows: `{context['rows']:,}`
- Feature seasons: `{context['feature_seasons']}`
- Target seasons: `{context['target_seasons']}`
- Split rows: train `{context['train_rows']:,}`, validation `{context['validation_rows']:,}`, holdout `{context['holdout_rows']:,}`
- Position rows: `{context['position_counts']}`

## Results

- Baseline validation MAE: `{context['baseline_validation_mae']}`
- Baseline holdout MAE: `{context['baseline_holdout_mae']}`
- Best validation candidate: `{context['best_validation_candidate']}` with MAE delta `{context['best_validation_mae_delta']}`
- Selected candidate for one-time holdout review: `{context['selected_candidate']}`
- Selected holdout MAE delta: `{context['selected_holdout_mae_delta']}`
- Selected holdout Spearman delta: `{context['selected_holdout_spearman_delta']}`
- Worth human review only: `{context['worth_human_review']}`

No candidate is production-approved.
"""


def scope_md() -> str:
    return """
# Candidate Search Scope

Scope follows Historical Formula Tuning Readiness Gate V1:

- Use canonical V3 substrate only.
- Use Source Contract V1 only.
- Use fixed train/validation/holdout split.
- Select from validation only.
- Evaluate holdout once after validation selection.
- Keep candidate families fixed, small, and interpretable.
- Keep null-fenced fields out of the primary pass.
- Use null-fenced fields only in explicitly labeled sensitivity variants.
- Do not use red-zone sidecars, routes, TPRR, YPRR, route proxies, ambiguous `rz_att`, market/ADP/vendor/projection/rank fields, or current-only context.
"""


def baseline_md() -> str:
    return """
# Baseline Formula Definition

Frozen V3 baseline: `prior_nwr_points`.

The baseline is a review-only rerun over the V3 substrate. It is not a production formula, not a ranking update, not a recommendation, and not a source-truth promotion.
"""


def selection_md(context: dict[str, Any], selected: dict[str, Any], decision: dict[str, Any]) -> str:
    return f"""
# Candidate Selection Decision

Selected candidate: `{context['selected_candidate']}`

Selection source: validation metrics only. Holdout was not used for selection.

Selection reason: {selected['selection_reason']}

Candidate verdict after one-time holdout review: `{decision['candidate_verdict']}`

Reason: {decision['reason']}

Worth human review only: `{decision['worth_human_review']}`.

No candidate is production-ready or production-approved.
"""


def selected_packet_md(context: dict[str, Any], selected: dict[str, Any], decision: dict[str, Any]) -> str:
    return f"""
# Selected Candidate Review Packet

- Candidate: `{context['selected_candidate']}`
- Validation MAE delta vs baseline: `{selected['mae_delta_vs_baseline']}`
- Validation Spearman delta vs baseline: `{selected['spearman_delta_vs_baseline']}`
- Validation startable precision delta vs baseline: `{selected['startable_precision_delta_vs_baseline']}`
- Holdout MAE delta vs baseline: `{context['selected_holdout_mae_delta']}`
- Holdout Spearman delta vs baseline: `{context['selected_holdout_spearman_delta']}`
- Holdout startable precision delta vs baseline: `{context['selected_holdout_startable_delta']}`
- Candidate verdict: `{decision['candidate_verdict']}`

This packet is candidate-only evidence. It must not be wired into NWR.
"""


def overfit_md(context: dict[str, Any]) -> str:
    return """
# Overfit And Leakage Report

Leakage checks: PASS.

- Feature season N and target season N+1 lag is preserved.
- Target outcomes are not used as features.
- Holdout was evaluated after validation selection.
- Null-fenced fields were excluded from primary candidates.
- Sensitivity variants exclude rows with null-fenced inputs rather than filling missing values with zero.
- Blocked feature families are absent from formulas.

Overfit gap details are tracked in `overfit_gap_matrix.csv`, `position_level_metric_report.csv`, and `season_level_metric_report.csv`.
"""


def blocked_md() -> str:
    return """
# Blocked Feature Compliance Report

PASS.

Blocked families remain blocked and absent from primary candidate formulas:

- routes
- TPRR
- YPRR
- route proxies
- ambiguous `rz_att`
- red-zone sidecars
- market/ADP/vendor/projection/rank fields as source truth
- current-only roster/status/injury/depth/schedule context
"""


def non_promotion_md() -> str:
    return """
# Production Non-Promotion Report

No candidate is production-approved.

This branch does not change production formulas, rankings, app wiring, model behavior, source truth, hidden sort, recommendations, runtime logic, or production config. Candidate outputs remain review-only evidence.
"""


def guardrail_md() -> str:
    return """
# Guardrail Report

Status: PASS for review-only candidate evidence.

Confirmed:

- No production formula changes.
- No production model training or tuning.
- No app wiring.
- No rankings changes.
- No recommendations or hidden sort.
- No source-truth promotion.
- No runtime behavior changes.
- No production config updates.
- No route, TPRR, YPRR, route proxy, ambiguous `rz_att`, red-zone sidecar, market, ADP, vendor, projection, rank, or current-only context feature use.
- No missing values forced to zero.
"""


def merge_safety_md() -> str:
    return """
# Merge Safety Report

This branch is merge-ready only as review-only candidate evidence if validation remains green.

Expected changed paths:

- `docs/hq/experiments/historical_formula_candidate_search_v1_20260701/`
- `tests/test_historical_formula_candidate_search_v1_20260701.py`

No production app/model/rank/source-truth/runtime paths are expected to change.
"""


def handoff_md(context: dict[str, Any]) -> str:
    return f"""
# Next Phase Handoff

Recommended next phase: `Historical Formula Candidate Review V1`.

Do not promote a candidate to production from this branch. If reviewers accept a candidate for further study, run a separate human-review lane that stress-tests the candidate against additional seasons, scoring assumptions, and position-specific failure modes.

Candidate verdict: `{context['candidate_verdict']}`.
Worth human review only: `{context['worth_human_review']}`.
"""


def write_manifest(context: dict[str, Any]) -> None:
    names = [
        "artifact_manifest.md",
        "historical_formula_candidate_search_summary.md",
        "candidate_search_scope.md",
        "baseline_formula_definition.md",
        "candidate_formula_definitions.csv",
        "candidate_formula_family_matrix.csv",
        "train_validation_holdout_split_report.csv",
        "baseline_metric_report.csv",
        "candidate_metric_report.csv",
        "validation_leaderboard.csv",
        "holdout_evaluation_report.csv",
        "position_level_metric_report.csv",
        "season_level_metric_report.csv",
        "topn_bucket_metric_report.csv",
        "candidate_selection_decision.md",
        "selected_candidate_review_packet.md",
        "null_fenced_sensitivity_report.csv",
        "null_fenced_sensitivity_report.md",
        "overfit_and_leakage_report.md",
        "overfit_gap_matrix.csv",
        "blocked_feature_compliance_report.md",
        "production_non_promotion_report.md",
        "guardrail_report.md",
        "merge_safety_report.md",
        "next_phase_handoff.md",
        "build_historical_formula_candidate_search_v1.py",
    ]
    artifact_manifest = EXPERIMENT_DIR / "artifact_manifest.md"
    if not artifact_manifest.exists():
        artifact_manifest.write_text("pending\n", encoding="utf-8")
    write_text(
        "null_fenced_sensitivity_report.md",
        """
# Null-Fenced Sensitivity Report

The primary candidate pass excludes null-fenced fields. Sensitivity variants use optional air/YAC and snap-context fields only on rows where the required inputs are non-null. Missing values are not filled with zero.

See `null_fenced_sensitivity_report.csv` for row counts and metrics.
""",
    )
    rows = []
    for name in names:
        path = EXPERIMENT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | {path.stat().st_size} | `{sha256_file(path)}` |")
    manifest = f"""
# Artifact Manifest

Verdict: `{context['verdict']}`

Candidate verdict: `{context['candidate_verdict']}`

- Created at: `{context['created_at']}`
- Branch: `{context['branch']}`
- Base HEAD: `{context['base_head']}`
- Review-only: true
- Production-approved: false
- Holdout used for selection: false

| Artifact | Bytes | SHA-256 |
|---|---:|---|
{chr(10).join(rows)}
"""
    write_text("artifact_manifest.md", manifest)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
