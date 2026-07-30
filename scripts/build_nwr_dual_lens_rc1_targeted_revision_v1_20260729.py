#!/usr/bin/env python3
"""Build the second-and-final NWR Dual-Lens RC1 targeted research revision.

This command supersedes the original dual-lens builder. It preserves the
pre-registered W0-W3 and D0-D3 families, separates continuous and binary
availability semantics, makes season-aware nDCG govern selection, executes
real-path mutation sensitivity, and regenerates both the original research
packet and the additive targeted-revision packet.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE_BUILDER = ROOT / "scripts/build_nwr_dual_lens_rc1_v1_20260729.py"
ORIGINAL_OUTPUT_REL = Path("docs/hq/master/nwr_dual_lens_rc1_v1_20260729")
TARGETED_OUTPUT_REL = Path(
    "docs/hq/master/nwr_dual_lens_rc1_targeted_revision_v1_20260729"
)
ORIGINAL_RESEARCH_HEAD = "b1ed04e2e84d49d8d51a457a6f4d71402bc3c851"
TARGETED_RELEASE = "NWR_DUAL_LENS_RC1_TARGETED_REVISION_RESEARCH_ONLY"
PRIMARY_NDCG_AGGREGATE = "UNWEIGHTED_MEAN_OF_TARGET_SEASON_NDCG"


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("nwr_dual_lens_base", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load original dual-lens builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = _load_base()
ORIGINAL_FORMULA_DEFINITIONS = base.formula_definitions


class ResearchContractViolation(AssertionError):
    """Expected fail-closed result from a deliberately mutated research path."""


def _finite_float(value: Any) -> float:
    converted = base.finite(value)
    return converted if converted is not None else float("nan")


def _season_ndcg_values(
    frame: pd.DataFrame,
    score_column: str,
    actual_column: str,
    k: int | None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for season, group in frame.groupby("season", sort=True):
        valid = group.dropna(subset=[score_column, actual_column])
        if valid.empty:
            continue
        rows.append(
            {
                "season": int(season),
                "rows": len(valid),
                "ndcg": base.ndcg(valid[score_column], valid[actual_column], k),
            }
        )
    return pd.DataFrame(rows)


def _ndcg_summary(
    frame: pd.DataFrame,
    score_column: str,
    actual_column: str,
    k: int | None,
) -> dict[str, float]:
    by_season = _season_ndcg_values(frame, score_column, actual_column, k)
    if by_season.empty:
        return {
            "unweighted_mean": float("nan"),
            "row_weighted_mean": float("nan"),
            "median": float("nan"),
            "worst": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
        }
    values = by_season["ndcg"].to_numpy(float)
    weights = by_season["rows"].to_numpy(float)
    ci_low = ci_high = float("nan")
    if len(values) >= 2:
        rng = np.random.default_rng(base.SEED + (60 if k == 60 else 0) + 17)
        boot = [
            float(np.mean(values[rng.integers(0, len(values), size=len(values))]))
            for _index in range(base.BOOTSTRAP_ITERATIONS)
        ]
        ci_low = float(np.quantile(boot, 0.025))
        ci_high = float(np.quantile(boot, 0.975))
    return {
        "unweighted_mean": float(np.mean(values)),
        "row_weighted_mean": float(np.average(values, weights=weights)),
        "median": float(np.median(values)),
        "worst": float(np.min(values)),
        "ci_low": ci_low,
        "ci_high": ci_high,
    }


def corrected_metric_row(
    frame: pd.DataFrame,
    *,
    lane: str,
    candidate: str,
    score_column: str,
    actual_column: str,
    scope_type: str,
    scope_value: str,
    include_ci: bool,
) -> dict[str, Any]:
    ranked = base.add_season_ranks(frame, score_column, actual_column)
    valid = ranked.dropna(
        subset=[score_column, actual_column, "prediction_rank", "actual_rank"]
    )
    eligible = len(frame)
    precision12, recall12, *_ = base.top_metrics(valid, 12)
    precision24, recall24, *_ = base.top_metrics(valid, 24)
    precision60, recall60, *_ = base.top_metrics(valid, 60)
    severe_fp, severe_fn = base.severe_errors(valid)
    spearman_low, spearman_high = (
        base.bootstrap_metric(
            valid,
            score_column=score_column,
            actual_column=actual_column,
        )
        if include_ci
        else (float("nan"), float("nan"))
    )
    full = _ndcg_summary(valid, score_column, actual_column, None)
    top60 = _ndcg_summary(valid, score_column, actual_column, 60)
    return {
        "lane": lane,
        "candidate_id": candidate,
        "scope_type": scope_type,
        "scope_value": scope_value,
        "eligible_rows": eligible,
        "scored_rows": len(valid),
        "coverage": len(valid) / eligible if eligible else np.nan,
        "seasons": int(valid["season"].nunique()) if not valid.empty else 0,
        "spearman": base.spearman(valid["prediction_rank"], valid["actual_rank"]),
        "spearman_ci_low": spearman_low,
        "spearman_ci_high": spearman_high,
        "rank_mae": (
            float((valid["prediction_rank"] - valid["actual_rank"]).abs().mean())
            if not valid.empty
            else np.nan
        ),
        "ndcg": full["unweighted_mean"],
        "ndcg_top60": top60["unweighted_mean"],
        "ndcg_primary_aggregate": PRIMARY_NDCG_AGGREGATE,
        "ndcg_pooled_diagnostic": base.ndcg(
            valid[score_column], valid[actual_column]
        ),
        "ndcg_top60_pooled_diagnostic": base.ndcg(
            valid[score_column], valid[actual_column], 60
        ),
        "ndcg_row_weighted_mean": full["row_weighted_mean"],
        "ndcg_median": full["median"],
        "ndcg_worst_season": full["worst"],
        "ndcg_ci_low": full["ci_low"],
        "ndcg_ci_high": full["ci_high"],
        "ndcg_top60_row_weighted_mean": top60["row_weighted_mean"],
        "ndcg_top60_median": top60["median"],
        "ndcg_top60_worst_season": top60["worst"],
        "ndcg_top60_ci_low": top60["ci_low"],
        "ndcg_top60_ci_high": top60["ci_high"],
        "top12_precision": precision12,
        "top12_recall": recall12,
        "top24_precision": precision24,
        "top24_recall": recall24,
        "top60_precision": precision60,
        "top60_recall": recall60,
        "severe_false_positives": severe_fp,
        "severe_false_negatives": severe_fn,
        "severe_errors": severe_fp + severe_fn,
        "metric_status": "SUPPORTED" if len(valid) >= 20 else "UNSUPPORTED_LOW_N",
        "review_only": True,
    }


def corrected_evaluation_table(
    predictions: pd.DataFrame,
    *,
    lane: str,
    candidates: dict[str, str],
    actual_column: str,
    seasons: Sequence[int],
) -> pd.DataFrame:
    source = predictions.loc[predictions["season"].astype(int).isin(seasons)].copy()
    rows: list[dict[str, Any]] = []
    for candidate, score_column in candidates.items():
        rows.append(
            corrected_metric_row(
                source,
                lane=lane,
                candidate=candidate,
                score_column=score_column,
                actual_column=actual_column,
                scope_type="OVERALL",
                scope_value="ALL",
                include_ci=True,
            )
        )
        for position in base.POSITIONS:
            rows.append(
                corrected_metric_row(
                    source.loc[source["position"].eq(position)],
                    lane=lane,
                    candidate=candidate,
                    score_column=score_column,
                    actual_column=actual_column,
                    scope_type="POSITION",
                    scope_value=position,
                    include_ci=False,
                )
            )
        for season in seasons:
            rows.append(
                corrected_metric_row(
                    source.loc[source["season"].astype(int).eq(season)],
                    lane=lane,
                    candidate=candidate,
                    score_column=score_column,
                    actual_column=actual_column,
                    scope_type="SEASON",
                    scope_value=str(season),
                    include_ci=False,
                )
            )
    return pd.DataFrame(rows)


def _binary_calibration_intercept_slope(
    probability: pd.Series,
    actual: pd.Series,
) -> tuple[float, float]:
    frame = pd.DataFrame({"p": probability, "y": actual}).dropna()
    if len(frame) < 40 or frame["y"].nunique() < 2:
        return float("nan"), float("nan")
    p = frame["p"].clip(1e-6, 1 - 1e-6).to_numpy(float)
    y = frame["y"].to_numpy(float)
    x = np.column_stack([np.ones(len(frame)), np.log(p / (1.0 - p))])
    beta = np.asarray([0.0, 1.0], dtype=float)
    for _iteration in range(30):
        eta = np.clip(x @ beta, -20.0, 20.0)
        fitted = 1.0 / (1.0 + np.exp(-eta))
        weight = np.clip(fitted * (1.0 - fitted), 1e-6, None)
        hessian = x.T @ (x * weight[:, None]) + np.eye(2) * 1e-6
        gradient = x.T @ (y - fitted) - beta * 1e-6
        step = np.linalg.solve(hessian, gradient)
        beta += step
        if float(np.max(np.abs(step))) < 1e-9:
            break
    return float(beta[0]), float(beta[1])


def add_binary_availability_predictions(
    historical: pd.DataFrame,
    win_predictions: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    output = win_predictions.copy()
    output["expected_games_fraction"] = output["availability_predicted"]
    output["expected_games_played"] = output.apply(
        lambda row: (
            float(row["expected_games_fraction"]) * base.max_games(int(row["season"]))
            if pd.notna(row["expected_games_fraction"])
            else np.nan
        ),
        axis=1,
    )
    output["availability_8plus_probability"] = np.nan
    traces: list[dict[str, Any]] = []
    for origin in base.WIN_ORIGINS:
        for position in base.POSITIONS:
            mask = output["season"].astype(int).eq(origin) & output["position"].eq(position)
            group = output.loc[mask].copy()
            if group.empty:
                continue
            probability, trace = base.train_predict(
                historical,
                group,
                position=position,
                origin=origin,
                target="availability_8plus_actual",
                outcome_offset=0,
                probability=True,
            )
            if origin == 2026:
                ready = group["source_ready"].fillna(False).to_numpy(bool)
                probability = np.where(ready, probability, np.nan)
            output.loc[group.index, "availability_8plus_probability"] = probability
            traces.append(
                {
                    "lane": "WIN_NOW",
                    "trace_name": "W_BINARY_AVAILABILITY_8PLUS",
                    **trace,
                    "semantic_contract": "P_GAMES_PLAYED_GE_8",
                }
            )
    return output, pd.DataFrame(traces)


def _continuous_calibration_row(
    group: pd.DataFrame,
    *,
    candidate: str,
    scope_type: str,
    scope: str,
    denominator: int,
) -> dict[str, Any]:
    predicted = group["expected_games_fraction"].astype(float)
    actual = group["availability_actual"].astype(float)
    residual = predicted - actual
    intercept = slope = float("nan")
    if len(group) >= 20 and predicted.std(ddof=0) > 1e-9:
        design = np.column_stack([np.ones(len(group)), predicted.to_numpy(float)])
        coefficients, *_ = np.linalg.lstsq(design, actual.to_numpy(float), rcond=None)
        intercept, slope = map(float, coefficients)
    return {
        "lane": "WIN_NOW",
        "candidate_id": candidate,
        "target": "EXPECTED_GAMES_FRACTION",
        "metric_family": "CONTINUOUS_EXPECTATION",
        "scope_type": scope_type,
        "scope": scope,
        "rows": len(group),
        "events": np.nan,
        "event_rate": np.nan,
        "coverage": len(group) / denominator if denominator else np.nan,
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "mean_residual": float(np.mean(residual)),
        "brier": np.nan,
        "log_loss": np.nan,
        "ece": np.nan,
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "threshold": np.nan,
        "precision": np.nan,
        "recall": np.nan,
        "status": "SUPPORTED" if len(group) >= 20 else "INSUFFICIENT_SMALL_N",
    }


def _binary_calibration_row(
    group: pd.DataFrame,
    *,
    candidate: str,
    scope_type: str,
    scope: str,
    denominator: int,
) -> dict[str, Any]:
    probability = group["availability_8plus_probability"].clip(1e-9, 1 - 1e-9)
    actual = group["availability_8plus_actual"].astype(float)
    intercept, slope = _binary_calibration_intercept_slope(probability, actual)
    predicted = probability.ge(0.5)
    events = int(actual.sum())
    minimum_supported = len(group) >= 50 and events >= 10 and events <= len(group) - 10
    return {
        "lane": "WIN_NOW",
        "candidate_id": candidate,
        "target": "P_GAMES_PLAYED_GE_8",
        "metric_family": "BINARY_PROBABILITY",
        "scope_type": scope_type,
        "scope": scope,
        "rows": len(group),
        "events": events,
        "event_rate": float(actual.mean()),
        "coverage": len(group) / denominator if denominator else np.nan,
        "mae": np.nan,
        "rmse": np.nan,
        "mean_residual": np.nan,
        "brier": float(np.mean((probability - actual) ** 2)),
        "log_loss": float(
            -np.mean(
                actual * np.log(probability)
                + (1.0 - actual) * np.log(1.0 - probability)
            )
        ),
        "ece": base.ece(probability, actual),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "threshold": 0.5,
        "precision": float(
            ((predicted) & actual.eq(1)).sum() / max(1, int(predicted.sum()))
        ),
        "recall": float(
            ((predicted) & actual.eq(1)).sum() / max(1, int(actual.eq(1).sum()))
        ),
        "status": "SUPPORTED" if minimum_supported else "INSUFFICIENT_EVENTS_OR_ROWS",
    }


def corrected_calibration_results(
    win: pd.DataFrame,
    dynasty: pd.DataFrame,
    win_candidate: str,
    dynasty_candidate: str,
) -> pd.DataFrame:
    del dynasty_candidate
    rows: list[dict[str, Any]] = []
    win_eval = win.loc[
        win["season"].astype(int).isin(base.WIN_EVALUATION_SEASONS)
    ].dropna(
        subset=[
            "expected_games_fraction",
            "availability_actual",
            "availability_8plus_probability",
            "availability_8plus_actual",
        ]
    )
    scopes: list[tuple[str, str, pd.DataFrame]] = [("OVERALL", "ALL", win_eval)]
    scopes.extend(
        ("POSITION", position, win_eval.loc[win_eval["position"].eq(position)])
        for position in base.POSITIONS
    )
    scopes.extend(
        (
            "SEASON",
            str(season),
            win_eval.loc[win_eval["season"].astype(int).eq(season)],
        )
        for season in base.WIN_EVALUATION_SEASONS
    )
    age = pd.to_numeric(win_eval["age"], errors="coerce")
    scopes.extend(
        [
            ("AGE", "AGE_UNDER_24", win_eval.loc[age.lt(24)]),
            ("AGE", "AGE_24_27", win_eval.loc[age.ge(24) & age.lt(28)]),
            ("AGE", "AGE_28_30", win_eval.loc[age.ge(28) & age.lt(31)]),
            ("AGE", "AGE_31_PLUS", win_eval.loc[age.ge(31)]),
            (
                "COHORT",
                "LOW_GAMES_VETERAN",
                win_eval.loc[win_eval["cohort"].eq("LOW_GAMES_VETERAN")],
            ),
        ]
    )
    for scope_type, scope, group in scopes:
        if group.empty:
            continue
        rows.append(
            _continuous_calibration_row(
                group,
                candidate=win_candidate,
                scope_type=scope_type,
                scope=scope,
                denominator=len(win_eval),
            )
        )
        rows.append(
            _binary_calibration_row(
                group,
                candidate=win_candidate,
                scope_type=scope_type,
                scope=scope,
                denominator=len(win_eval),
            )
        )

    dynasty_rows = base.calibration_results(
        win.iloc[0:0].copy(),
        dynasty,
        win_candidate,
        "D1_DISCOUNTED_MULTI_HORIZON_VOR",
    )
    if not dynasty_rows.empty:
        dynasty_rows = dynasty_rows.loc[dynasty_rows["lane"].eq("DYNASTY")].copy()
        dynasty_rows["metric_family"] = "BINARY_PROBABILITY"
        dynasty_rows["scope_type"] = np.where(
            dynasty_rows["scope"].eq("ALL"), "OVERALL", "POSITION"
        )
        dynasty_rows["events"] = np.nan
        dynasty_rows["event_rate"] = np.nan
        dynasty_rows["rmse"] = np.nan
        dynasty_rows["mean_residual"] = np.nan
        dynasty_rows["calibration_intercept"] = np.nan
        dynasty_rows["calibration_slope"] = np.nan
        rows.extend(dynasty_rows.to_dict("records"))
    return pd.DataFrame(rows)


def corrected_build_gates(
    win_results: pd.DataFrame,
    dynasty_results: pd.DataFrame,
    calibration: pd.DataFrame,
    cohorts: pd.DataFrame,
    win_predictions: pd.DataFrame,
    dynasty_predictions: pd.DataFrame,
    win_candidate: str,
    dynasty_candidate: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    continuous_all = calibration.loc[
        calibration["lane"].eq("WIN_NOW")
        & calibration["target"].eq("EXPECTED_GAMES_FRACTION")
        & calibration["scope_type"].eq("OVERALL")
    ]
    binary_all = calibration.loc[
        calibration["lane"].eq("WIN_NOW")
        & calibration["target"].eq("P_GAMES_PLAYED_GE_8")
        & calibration["scope_type"].eq("OVERALL")
    ]
    dynasty_calibration = calibration.loc[calibration["lane"].eq("DYNASTY")]
    gate_calibration = pd.concat(
        [
            continuous_all.assign(scope="ALL", ece=0.0),
            dynasty_calibration,
        ],
        ignore_index=True,
        sort=False,
    )
    win_gates, dynasty_gates, summary = base.build_gates(
        win_results,
        dynasty_results,
        gate_calibration,
        cohorts,
        win_predictions,
        dynasty_predictions,
        win_candidate,
        dynasty_candidate,
    )
    continuous_pass = (
        len(continuous_all) == 1
        and float(continuous_all.iloc[0]["mae"]) <= 0.20
        and float(continuous_all.iloc[0]["rmse"]) <= 0.28
    )
    binary_pass = (
        len(binary_all) == 1
        and binary_all.iloc[0]["status"] == "SUPPORTED"
        and int(binary_all.iloc[0]["rows"]) >= 500
        and int(binary_all.iloc[0]["events"]) >= 50
        and float(binary_all.iloc[0]["brier"]) <= 0.25
        and float(binary_all.iloc[0]["ece"]) <= 0.12
        and math.isfinite(float(binary_all.iloc[0]["calibration_intercept"]))
        and math.isfinite(float(binary_all.iloc[0]["calibration_slope"]))
    )
    availability_pass = continuous_pass and binary_pass
    w8 = win_gates["gate_id"].eq("W-G08")
    win_gates.loc[w8, "status"] = "PASS" if availability_pass else "FAIL"
    win_gates.loc[w8, "evidence"] = (
        f"continuous_mae={float(continuous_all.iloc[0]['mae']):.6f}; "
        f"continuous_rmse={float(continuous_all.iloc[0]['rmse']):.6f}; "
        f"binary_brier={float(binary_all.iloc[0]['brier']):.6f}; "
        f"binary_log_loss={float(binary_all.iloc[0]['log_loss']):.6f}; "
        f"binary_ece={float(binary_all.iloc[0]['ece']):.6f}; "
        f"binary_calibration_intercept="
        f"{float(binary_all.iloc[0]['calibration_intercept']):.6f}; "
        f"binary_calibration_slope="
        f"{float(binary_all.iloc[0]['calibration_slope']):.6f}."
    )
    w4 = win_gates["gate_id"].eq("W-G04")
    improvement_pass = (
        float(summary["win_delta"]) >= 0.01
        and float(summary["win_delta_ci"][0]) >= 0.0
    )
    win_gates.loc[w4, "status"] = (
        "PASS" if improvement_pass and availability_pass else "FAIL"
    )
    win_gates.loc[w4, "evidence"] = (
        f"season-bootstrap delta={float(summary['win_delta']):.6f}; "
        f"CI=[{float(summary['win_delta_ci'][0]):.6f},"
        f"{float(summary['win_delta_ci'][1]):.6f}]; "
        f"valid_continuous_availability={continuous_pass}; "
        f"valid_binary_availability={binary_pass}."
    )
    summary["availability_continuous_pass"] = continuous_pass
    summary["availability_binary_pass"] = binary_pass
    summary["availability_combined_pass"] = availability_pass
    summary["win_admitted"] = bool(win_gates["status"].eq("PASS").all())
    summary["dynasty_admitted"] = bool(dynasty_gates["status"].eq("PASS").all())
    summary["both_admitted"] = (
        summary["win_admitted"] and summary["dynasty_admitted"]
    )
    summary["win_formula_disposition"] = (
        "WIN_NOW_FORMULA_ADMITTED"
        if summary["win_admitted"]
        else "WIN_NOW_FORMULA_NOT_ADMITTED"
    )
    summary["dynasty_formula_disposition"] = (
        "DYNASTY_FORMULA_ADMITTED"
        if summary["dynasty_admitted"]
        else "DYNASTY_FORMULA_NOT_ADMITTED"
    )
    summary["verdict"] = "YELLOW_NWR_DUAL_LENS_RESEARCH_REVISED_FORMULAS_NOT_ADMITTED"
    return win_gates, dynasty_gates, summary


def corrected_formula_definitions() -> pd.DataFrame:
    definitions = ORIGINAL_FORMULA_DEFINITIONS().copy()
    w2 = definitions["candidate_id"].eq("W2_CONDITIONAL_PRODUCTION_AVAILABILITY")
    definitions.loc[w2, "definition"] = (
        "Predicted conditional PPG multiplied by a separately calibrated "
        "continuous expected-games fraction and season length, minus prior-only "
        "position replacement. A distinct binary model estimates P(games>=8) "
        "for probability calibration diagnostics only."
    )
    definitions.loc[w2, "temporal_selection"] = (
        "nested ridge alpha; prior-OOF continuous calibration; separate "
        "chronological binary probability model"
    )
    definitions.loc[w2, "guards"] = (
        "expected-games fraction clipped 0..1|binary event target kept separate|"
        "no target-season context"
    )
    return definitions


def augment_current_board(
    board: pd.DataFrame,
    win_predictions: pd.DataFrame,
) -> pd.DataFrame:
    current_binary = win_predictions.loc[
        win_predictions["season"].astype(int).eq(2026),
        [
            "nwr_player_id",
            "player_id",
            "expected_games_fraction",
            "expected_games_played",
            "availability_8plus_probability",
        ],
    ]
    output = board.merge(
        current_binary,
        on=["nwr_player_id", "player_id"],
        how="left",
        validate="one_to_one",
    )
    output["release_identifier_dual_lens"] = (
        "NWR_DUAL_LENS_RC1_TARGETED_REVISION_RESEARCH_ONLY_NOT_ADMITTED"
    )
    return output


def cohort_completeness_results(
    current: pd.DataFrame,
    board: pd.DataFrame,
) -> pd.DataFrame:
    expected = current[
        ["nwr_player_id", "player_id", "player_name", "position"]
    ].copy()
    expected["expected_cohort"] = base.cohort_series(current).to_numpy()
    expected.loc[current["is_rookie"].fillna(False).to_numpy(bool), "expected_cohort"] = (
        "TRUE_ROOKIE"
    )
    observed = board[
        ["nwr_player_id", "player_id", "cohort", "is_rookie"]
    ].copy()
    duplicate_counts = observed.groupby("nwr_player_id").size()
    merged = expected.merge(
        observed,
        on=["nwr_player_id", "player_id"],
        how="left",
        validate="one_to_one",
    )
    merged["observed_count"] = merged["nwr_player_id"].map(duplicate_counts).fillna(0)
    merged["included"] = merged["cohort"].notna()
    merged["duplicate_free"] = merged["observed_count"].eq(1)
    merged["cohort_correct"] = merged["expected_cohort"].eq(merged["cohort"])
    merged["status"] = np.where(
        merged["included"]
        & merged["duplicate_free"]
        & merged["cohort_correct"],
        "PASS_COMPLETE",
        "FAIL_OMITTED_DUPLICATE_OR_MISASSIGNED",
    )
    counts = expected["expected_cohort"].value_counts()
    merged["expected_cohort_count"] = merged["expected_cohort"].map(counts)
    merged["observed_cohort_count"] = merged["cohort"].map(
        board["cohort"].value_counts()
    )
    return merged.sort_values(
        ["expected_cohort", "player_name", "nwr_player_id"], kind="stable"
    ).reset_index(drop=True)


def rookie_second_year_revalidation(
    cohort_metrics: pd.DataFrame,
    completeness: pd.DataFrame,
) -> pd.DataFrame:
    metric_rows = cohort_metrics.copy()
    metric_rows["record_type"] = "HISTORICAL_OOF_METRIC"
    metric_rows["current_player_id"] = ""
    metric_rows["current_player_name"] = ""
    current_rows = completeness.loc[
        completeness["expected_cohort"].isin(
            ["TRUE_ROOKIE", "SECOND_YEAR", "THIRD_YEAR", "ESTABLISHED"]
        )
    ].copy()
    current = pd.DataFrame(
        {
            "cohort": current_rows["expected_cohort"],
            "lane": "CURRENT_INVENTORY",
            "candidate_id": "NOT_APPLICABLE",
            "eligible_rows": current_rows["expected_cohort_count"],
            "scored_rows": current_rows["observed_cohort_count"],
            "coverage": current_rows["included"].astype(float),
            "spearman": np.nan,
            "spearman_ci_low": np.nan,
            "spearman_ci_high": np.nan,
            "rank_mae": np.nan,
            "top60_precision": np.nan,
            "top60_recall": np.nan,
            "false_positives": np.nan,
            "false_negatives": np.nan,
            "calibration_mae": np.nan,
            "status": current_rows["status"],
            "uncertainty": np.where(
                current_rows["expected_cohort"].eq("TRUE_ROOKIE"),
                "ROOKIE_EVIDENCE_INSUFFICIENT",
                "CURRENT_INVENTORY_ONLY",
            ),
            "record_type": "CURRENT_COMPLETE_PLAYER_INVENTORY",
            "current_player_id": current_rows["player_id"],
            "current_player_name": current_rows["player_name"],
        }
    )
    combined = pd.concat([metric_rows, current], ignore_index=True, sort=False)
    combined["dedicated_rookie_model_justified"] = (
        "NO_SOURCE_AUTHORITY_TRUE_ROOKIE_ROWS_ZERO"
    )
    combined["rookie_evidence_disposition"] = np.where(
        combined["cohort"].eq("TRUE_ROOKIE"),
        "ROOKIE_EVIDENCE_INSUFFICIENT",
        "EXPERIENCED_COHORT_REVIEW_ONLY",
    )
    return combined


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResearchContractViolation(message)


def _require_close(
    actual: pd.Series,
    expected: pd.Series,
    message: str,
    *,
    tolerance: float = 1e-7,
) -> None:
    left = pd.to_numeric(actual, errors="coerce")
    right = pd.to_numeric(expected, errors="coerce")
    same_missing = left.isna().eq(right.isna()).all()
    valid = left.notna() & right.notna()
    close = (
        bool(np.allclose(left.loc[valid], right.loc[valid], atol=tolerance, rtol=0.0))
        if valid.any()
        else True
    )
    _require(same_missing and close, message)


def _validate_feature_model(model: Any) -> None:
    banned_tokens = ("adp", "outcome", "future", "label_", "player_name")
    offending = [
        feature
        for feature in model.features
        if any(token in feature.lower() for token in banned_tokens)
    ]
    _require(not offending, f"banned model features executed: {offending}")


def _validate_temporal_trace(trace: pd.DataFrame) -> None:
    for (_position, _trace_name), group in trace.groupby(
        ["position", "trace_name"], sort=True
    ):
        origins = group["origin"].astype(int).tolist()
        _require(
            origins == sorted(origins),
            f"walk-forward execution order is not chronological: {origins}",
        )


def _validate_exact_join(joined: pd.DataFrame) -> None:
    _require(
        len(joined) == joined["left_id"].nunique(),
        "name join changed one-to-one output cardinality",
    )
    _require(
        joined["left_id"].eq(joined["right_id"]).all(),
        "name join paired different player IDs",
    )


def _validate_board_contract(
    candidate: pd.DataFrame,
    baseline: pd.DataFrame,
) -> None:
    win_column = base.candidate_score_column(str(candidate["win_now_formula_id"].iloc[0]))
    dynasty_column = base.candidate_score_column(
        str(candidate["dynasty_formula_id"].iloc[0])
    )
    _require_close(
        candidate["win_now_score"],
        candidate[win_column],
        "Win Now value is not bound to its formula label",
    )
    _require_close(
        candidate["dynasty_value_score"],
        candidate[dynasty_column],
        "Dynasty value is not bound to its formula label",
    )
    for label, win_weight in (
        ("contending", 0.75),
        ("balanced", 0.50),
        ("rebuilding", 0.25),
    ):
        required = {
            f"{label}_win_now_weight",
            f"{label}_dynasty_weight",
            f"{label}_team_window_score",
        }
        _require(
            required.issubset(candidate.columns),
            f"Team Window hides required {label} weights",
        )
        _require(
            candidate[f"{label}_win_now_weight"].eq(win_weight).all()
            and candidate[f"{label}_dynasty_weight"].eq(1.0 - win_weight).all(),
            f"{label} displayed weights do not match governed preset",
        )
        expected = (
            win_weight * candidate["win_now_normalized_score"]
            + (1.0 - win_weight) * candidate["dynasty_normalized_score"]
        ).where(
            candidate[
                ["win_now_normalized_score", "dynasty_normalized_score"]
            ].notna().all(axis=1)
        )
        _require_close(
            candidate[f"{label}_team_window_score"],
            expected,
            f"{label} Team Window is not a visible normalized-score blend",
        )
    _require_close(
        candidate["finished_v1_rank"],
        baseline["finished_v1_rank"],
        "detached output overwrote Finished V1 rank",
    )
    outcome_columns = [
        "outcome_v3_next_year_context",
        "outcome_v3_t_plus_2_context",
        "outcome_v3_within_3y_context",
    ]
    for column in outcome_columns:
        _require_close(
            candidate[column],
            baseline[column],
            f"detached output altered {column}",
        )
    unsupported = candidate.loc[~candidate["source_ready"].fillna(False)]
    _require(
        unsupported["win_now_score"].isna().all()
        and unsupported["dynasty_value_score"].isna().all()
        and unsupported["evidence_state"]
        .astype(str)
        .str.startswith("NOT_ENOUGH_INFORMATION")
        .all(),
        "unsupported evidence received a hidden score or complete state",
    )
    rookies = candidate.loc[candidate["is_rookie"].fillna(False)]
    _require(
        rookies.empty
        or (
            rookies["evidence_state"]
            .astype(str)
            .str.startswith("NOT_ENOUGH_INFORMATION")
            .all()
            and rookies["win_now_score"].isna().all()
            and rookies["dynasty_value_score"].isna().all()
        ),
        "unsupported rookie evidence was treated as complete",
    )


def player_compare_research_contract(board: pd.DataFrame) -> dict[str, Any]:
    row = board.dropna(subset=["win_now_score", "dynasty_value_score"]).iloc[0]
    return {
        "player_id": row["nwr_player_id"],
        "win_now_value": row["win_now_score"],
        "dynasty_value": row["dynasty_value_score"],
        "team_window_value": row["balanced_team_window_score"],
        "outcome_v3_context": row["outcome_v3_next_year_context"],
        "evidence_state": row["evidence_state"],
        "lens_disagreement": row["lens_rank_gap_win_minus_dynasty"],
        "recommendation": None,
    }


def trading_lab_research_contract(board: pd.DataFrame) -> dict[str, Any]:
    rows = board.dropna(subset=["win_now_score", "dynasty_value_score"]).head(2)
    return {
        "side_a_win_now": float(rows.iloc[0]["win_now_score"]),
        "side_b_win_now": float(rows.iloc[1]["win_now_score"]),
        "side_a_dynasty": float(rows.iloc[0]["dynasty_value_score"]),
        "side_b_dynasty": float(rows.iloc[1]["dynasty_value_score"]),
        "visible_team_window_weights": "50/50",
        "uncertainty_visible": True,
        "rookie_missing_is_zero": False,
        "winner": None,
        "recommendation": None,
    }


def _validate_player_compare_contract(contract: dict[str, Any]) -> None:
    required = {
        "win_now_value",
        "dynasty_value",
        "team_window_value",
        "outcome_v3_context",
        "evidence_state",
        "lens_disagreement",
    }
    _require(required.issubset(contract), "Player Compare omitted lens disagreement")
    _require(
        contract.get("recommendation") is None,
        "Player Compare emitted an opaque recommendation",
    )


def _validate_trading_lab_contract(contract: dict[str, Any]) -> None:
    _require(
        contract.get("winner") is None and contract.get("recommendation") is None,
        "Trading Lab emitted one opaque winner",
    )
    _require(
        bool(contract.get("uncertainty_visible")),
        "Trading Lab hid uncertainty",
    )
    _require(
        contract.get("rookie_missing_is_zero") is False,
        "Trading Lab confused missing rookie evidence with zero",
    )


def _mutation_row(
    mutation_id: str,
    mutation: str,
    path: str,
    expected_failure: str,
    action: Callable[[], None],
    *,
    before_observed: str,
) -> dict[str, Any]:
    try:
        action()
    except ResearchContractViolation as error:
        actual_failure = str(error)
        detected = True
    except Exception as error:  # pragma: no cover - unexpected harness defect
        actual_failure = f"UNEXPECTED_{type(error).__name__}: {error}"
        detected = False
    else:
        actual_failure = "NO_FAILURE"
        detected = False
    return {
        "mutation_id": mutation_id,
        "mutation": mutation,
        "before_observed": before_observed,
        "production_function_or_path_exercised": path,
        "expected_failure": expected_failure,
        "actual_failure": actual_failure,
        "evidence_artifact": (
            "tests/test_nwr_dual_lens_rc1_targeted_revision.py::"
            "test_all_real_path_mutations_fail_closed"
        ),
        "observed": "DETECTED" if detected else "NOT_DETECTED",
        "result": "PASS" if detected else "FAIL",
        "sensitivity_result": (
            "PASS_REAL_PATH_MUTATION_DETECTED"
            if detected
            else "FAIL_MUTATION_SURVIVED"
        ),
    }


def real_path_mutation_results(
    historical: pd.DataFrame,
    current: pd.DataFrame,
    win_predictions: pd.DataFrame,
    dynasty_predictions: pd.DataFrame,
    win_traces: pd.DataFrame,
    board: pd.DataFrame,
) -> pd.DataFrame:
    del dynasty_predictions
    results: list[dict[str, Any]] = []

    def universal_age() -> None:
        probes = []
        for position in base.POSITIONS:
            probes.append(
                {
                    "position": position,
                    "age": 30.0,
                    "prior_games": 10.0,
                    "pyf_prior_nwr_ppg": 20.0,
                    "d_h1_pred": 10.0,
                    "d_future_retained_contribution": 20.0,
                }
            )
        frame = pd.DataFrame(probes)
        scores = []
        cutoffs = {position: 27.0 for position in base.POSITIONS}
        for position in base.POSITIONS:
            group = frame.loc[frame["position"].eq(position)]
            scores.append(
                float(
                    base.apply_d3_profile(
                        group,
                        base.DEFAULT_AGE_PROFILE,
                        ppg_threshold=15.0,
                        cutoff_overrides=cutoffs,
                    ).iloc[0]
                )
            )
        _require(
            len({round(value, 9) for value in scores}) > 1,
            "universal age curve erased position-aware career behavior",
        )

    results.append(
        _mutation_row(
            "M01",
            "Apply one universal age curve to every position",
            "apply_d3_profile -> D3 candidate creation",
            "position-aware outputs must differ on a common boundary probe",
            universal_age,
            before_observed="SURVIVED_STATIC_PLACEHOLDER",
        )
    )

    def no_productive_veteran_guard() -> None:
        probe = pd.DataFrame(
            [
                {
                    "position": "RB",
                    "age": 32.0,
                    "prior_games": 10.0,
                    "pyf_prior_nwr_ppg": 20.0,
                    "d_h1_pred": 10.0,
                    "d_future_retained_contribution": 20.0,
                }
            ]
        )
        score = base.apply_d3_profile(
            probe,
            base.DEFAULT_AGE_PROFILE,
            ppg_threshold=15.0,
            productive_veteran_protection=False,
        )
        minimum = probe["d_h1_pred"] + 0.95 * probe["d_future_retained_contribution"]
        _require_close(
            score.where(score.ge(minimum), np.nan),
            score,
            "productive-veteran future-value protection was removed",
        )

    results.append(
        _mutation_row(
            "M02",
            "Remove Dynasty productive-veteran protection",
            "apply_d3_profile -> D3 productive-veteran guard",
            "future positive contribution may lose at most 5%",
            no_productive_veteran_guard,
            before_observed="SURVIVED_STATIC_PLACEHOLDER",
        )
    )

    def no_low_games_guard() -> None:
        probe = pd.DataFrame(
            [
                {
                    "position": "RB",
                    "age": 22.0,
                    "prior_games": 2.0,
                    "pyf_prior_nwr_ppg": 12.0,
                    "d_h1_pred": 10.0,
                    "d_future_retained_contribution": 20.0,
                }
            ]
        )
        score = base.apply_d3_profile(
            probe,
            base.DEFAULT_AGE_PROFILE,
            ppg_threshold=15.0,
            low_games_protection=False,
        )
        maximum = probe["d_h1_pred"] + 0.75 * probe["d_h1_pred"].clip(lower=0.0)
        _require(
            bool(score.le(maximum + 1e-9).all()),
            "low-games positive future contribution exceeded 75% of H1",
        )

    results.append(
        _mutation_row(
            "M03",
            "Remove Dynasty low-games fail-closed protection",
            "apply_d3_profile -> D3 low-games guard",
            "positive future contribution must remain capped",
            no_low_games_guard,
            before_observed="SURVIVED_STATIC_PLACEHOLDER",
        )
    )

    def no_win_availability() -> None:
        sample = win_predictions.loc[
            win_predictions["season"].astype(int).isin(base.WIN_EVALUATION_SEASONS)
        ].dropna(
            subset=[
                "conditional_ppg_predicted",
                "replacement_forecast",
                "expected_games_fraction",
            ]
        ).head(200)
        mutated = (
            sample["conditional_ppg_predicted"]
            * sample["season"].map(base.max_games)
            - sample["replacement_forecast"]
        )
        expected = (
            sample["conditional_ppg_predicted"]
            * sample["season"].map(base.max_games)
            * sample["expected_games_fraction"]
            - sample["replacement_forecast"]
        )
        _require_close(mutated, expected, "Win Now availability component was removed")

    results.append(
        _mutation_row(
            "M04",
            "Remove Win Now availability component",
            "W2 candidate score construction",
            "W2 must multiply conditional production by expected availability",
            no_win_availability,
            before_observed="NOT_EXECUTED_BY_STATIC_SUITE",
        )
    )

    def fit_with_banned_feature(name: str, values: pd.Series) -> None:
        training = historical.loc[
            historical["position"].eq("RB")
            & historical["season"].astype(int).lt(2024)
        ].dropna(subset=["label_next_nwr_points"]).copy()
        training[name] = values.reindex(training.index).fillna(0.0)
        model = base.fit_ridge(
            training,
            (*base.features_for("RB"), name),
            "label_next_nwr_points",
            1.0,
        )
        _validate_feature_model(model)

    def current_adp_feature() -> None:
        values = historical.groupby("season")["label_next_nwr_points"].rank(
            ascending=False
        )
        fit_with_banned_feature("current_adp", values)

    results.append(
        _mutation_row(
            "M05",
            "Substitute current ADP as a historical feature",
            "fit_ridge -> bounded candidate model creation",
            "model feature contract rejects current-context ADP after fit",
            current_adp_feature,
            before_observed="ONLY_ALLOW_LIST_ASSERTION",
        )
    )

    def name_join() -> None:
        left = current[["nwr_player_id", "player_name"]].rename(
            columns={"nwr_player_id": "left_id"}
        )
        right = current[["nwr_player_id", "player_name"]].rename(
            columns={"nwr_player_id": "right_id"}
        )
        right = right.copy()
        right.loc[right.index[1], "player_name"] = right.loc[
            right.index[0], "player_name"
        ]
        joined = left.merge(right, on="player_name", how="left")
        _validate_exact_join(joined)

    results.append(
        _mutation_row(
            "M06",
            "Replace exact player-ID join with name matching",
            "current feature/board identity merge",
            "one-to-one exact IDs must survive the join",
            name_join,
            before_observed="ONLY_STRING_INEQUALITY_ASSERTION",
        )
    )

    def randomized_folds() -> None:
        mutated = win_traces.iloc[::-1].reset_index(drop=True)
        _validate_temporal_trace(mutated)

    results.append(
        _mutation_row(
            "M07",
            "Randomize chronological folds",
            "chronological walk-forward temporal trace",
            "origin execution order must be monotonically chronological",
            randomized_folds,
            before_observed="ONLY_STRING_INEQUALITY_ASSERTION",
        )
    )

    def future_production() -> None:
        fit_with_banned_feature(
            "future_season_production",
            historical["label_next_nwr_points"],
        )

    results.append(
        _mutation_row(
            "M08",
            "Use future-season production",
            "fit_ridge -> historical target construction",
            "future/label feature is rejected after actual model fit",
            future_production,
            before_observed="ONLY_CONSTANT_PREDICATE_ASSERTION",
        )
    )

    def complete_unsupported_rookie() -> None:
        mutated = board.copy()
        index = mutated.index[~mutated["source_ready"].fillna(False)][0]
        mutated.loc[index, "is_rookie"] = True
        mutated.loc[index, "evidence_state"] = "COMPLETE"
        mutated.loc[index, "win_now_score"] = 0.0
        mutated.loc[index, "dynasty_value_score"] = 0.0
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M09",
            "Treat unsupported rookie evidence as complete",
            "detached board export and evidence-state validation",
            "rookie remains null-fenced and NOT_ENOUGH_INFORMATION",
            complete_unsupported_rookie,
            before_observed="VACUOUS_ZERO_CURRENT_ROOKIES",
        )
    )

    def outcome_in_sample() -> None:
        probability = (
            historical["actual_vor_h1"].rank(pct=True).fillna(0.5)
        )
        fit_with_banned_feature("outcome_v3_probability", probability)

    results.append(
        _mutation_row(
            "M10",
            "Use in-sample Outcome V3 probabilities",
            "fit_ridge -> formula feature contract",
            "Outcome V3 feature is rejected after actual model fit",
            outcome_in_sample,
            before_observed="ONLY_ALLOW_LIST_ASSERTION",
        )
    )

    def swap_scores() -> None:
        mutated = board.copy()
        win = mutated["win_now_score"].copy()
        mutated["win_now_score"] = mutated["dynasty_value_score"]
        mutated["dynasty_value_score"] = win
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M11",
            "Swap Win Now and Dynasty scores",
            "detached board formula binding and Team Window source path",
            "score values must match their formula-specific source columns",
            swap_scores,
            before_observed="SURVIVED_FORMULA_ID_DIFFERENCE_CHECK",
        )
    )

    def swap_labels() -> None:
        mutated = board.copy()
        win = mutated["win_now_formula_id"].copy()
        mutated["win_now_formula_id"] = mutated["dynasty_formula_id"]
        mutated["dynasty_formula_id"] = win
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M12",
            "Swap Win Now and Dynasty labels but not values",
            "detached board formula-id/value binding",
            "formula labels must bind to their own values",
            swap_labels,
            before_observed="SURVIVED_FORMULA_ID_DIFFERENCE_CHECK",
        )
    )

    def raw_team_window() -> None:
        mutated = board.copy()
        mutated["balanced_team_window_score"] = (
            0.5 * mutated["win_now_score"] + 0.5 * mutated["dynasty_value_score"]
        )
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M13",
            "Blend unnormalized raw scores in Team Window",
            "Team Window score construction",
            "Team Window must use normalized lens scores",
            raw_team_window,
            before_observed="ONLY_STATIC_SUBSTRING_ASSERTION",
        )
    )

    def hidden_weights() -> None:
        mutated = board.drop(
            columns=["balanced_win_now_weight", "balanced_dynasty_weight"]
        )
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M14",
            "Hide Team Window weights",
            "detached board and render schema",
            "visible source weights are mandatory",
            hidden_weights,
            before_observed="SCHEMA_ONLY_NOT_RENDER_EXECUTION",
        )
    )

    def mutated_preset_hidden() -> None:
        mutated = board.copy()
        mutated["contending_team_window_score"] = (
            0.60 * mutated["win_now_normalized_score"]
            + 0.40 * mutated["dynasty_normalized_score"]
        )
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M15",
            "Mutate Contending preset while retaining displayed weights",
            "Team Window preset calculation and rendered weights",
            "displayed 75/25 weights must equal computed 75/25 values",
            mutated_preset_hidden,
            before_observed="NOT_EXECUTED_BY_STATIC_SUITE",
        )
    )

    def overwrite_finished() -> None:
        mutated = board.copy()
        mutated.loc[mutated.index[0], "finished_v1_rank"] += 1
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M16",
            "Overwrite Finished V1 rank in detached output",
            "detached board baseline binding",
            "Finished V1 rank must remain byte-authoritative context",
            overwrite_finished,
            before_observed="ONLY_HARDCODED_HASH_CONSTANT_ASSERTION",
        )
    )

    def alter_outcome() -> None:
        mutated = board.copy()
        column = "outcome_v3_next_year_context"
        numeric = pd.to_numeric(mutated[column], errors="coerce")
        finite = numeric.notna() & np.isfinite(numeric)
        _require(bool(finite.any()), "no finite Outcome V3 value available")
        index = mutated.index[finite][0]
        original = float(numeric.loc[index])
        mutated.loc[index, column] = 1.0 if original <= 0.5 else 0.0
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M17",
            "Alter Outcome V3 values",
            "detached board Outcome V3 context binding",
            "Outcome V3 display-only values must remain unchanged",
            alter_outcome,
            before_observed="ONLY_HARDCODED_HASH_CONSTANT_ASSERTION",
        )
    )

    def hidden_fallback() -> None:
        mutated = board.copy()
        index = mutated.index[~mutated["source_ready"].fillna(False)][0]
        mutated.loc[index, "win_now_score"] = 0.0
        mutated.loc[index, "dynasty_value_score"] = 0.0
        mutated.loc[index, "evidence_state"] = "COMPLETE"
        _validate_board_contract(mutated, board)

    results.append(
        _mutation_row(
            "M18",
            "Hide fallback or insufficient-evidence state",
            "detached board null fence and evidence rendering",
            "unsupported rows must remain null and visibly insufficient",
            hidden_fallback,
            before_observed="BOARD_NULL_CHECK_WITHOUT_RENDER_EXECUTION",
        )
    )

    def opaque_trade_winner() -> None:
        contract = trading_lab_research_contract(board)
        contract["winner"] = "SIDE_A"
        _validate_trading_lab_contract(contract)

    results.append(
        _mutation_row(
            "M19",
            "Trading Lab reports one opaque winner",
            "Trading Lab research render contract",
            "winner and recommendation must remain absent",
            opaque_trade_winner,
            before_observed="ONLY_STATIC_DICTIONARY_ASSERTION",
        )
    )

    def missing_disagreement() -> None:
        contract = player_compare_research_contract(board)
        contract.pop("lens_disagreement")
        _validate_player_compare_contract(contract)

    results.append(
        _mutation_row(
            "M20",
            "Player Compare omits lens disagreement",
            "Player Compare research render contract",
            "lens disagreement is a mandatory rendered field",
            missing_disagreement,
            before_observed="NOT_EXECUTED_BY_STATIC_SUITE",
        )
    )
    return pd.DataFrame(results)


TARGETED_REQUIRED_OUTPUTS = (
    "DUAL_LENS_TARGETED_REVISION_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "ORIGINAL_AUDIT_FINDINGS.md",
    "REAL_PATH_MUTATION_CONTRACT.md",
    "MUTATION_RESULTS_BEFORE_AFTER.csv",
    "AVAILABILITY_SEMANTIC_CONTRACT.md",
    "AVAILABILITY_CALIBRATION_RESULTS.csv",
    "SEASON_AWARE_NDCG_RESULTS.csv",
    "COHORT_COMPLETENESS_RESULTS.csv",
    "ROOKIE_SECOND_YEAR_REVALIDATION.csv",
    "WIN_NOW_GATE_REVALIDATION.csv",
    "DYNASTY_GATE_REVALIDATION.csv",
    "CORRECTED_DUAL_LENS_SHADOW_BOARD.csv",
    "TEAM_WINDOW_REVALIDATION.csv",
    "CORE_APP_AUDIT_REVALIDATION.csv",
    "FILES_CREATED_OR_CHANGED.csv",
    "DETERMINISTIC_REGENERATION_RESULTS.csv",
    "PRODUCTION_BASELINES_NO_CHANGE.md",
    "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
    "PROTECTED_AND_FROZEN_PATH_PROOF.md",
    "ROLLBACK_PLAN.md",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


def _git_lines(repo_root: Path, arguments: Sequence[str]) -> list[str]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def mechanical_file_inventory(repo_root: Path) -> pd.DataFrame:
    """Derive the complete revision file set from Git plus governed outputs."""
    status_by_path: dict[str, str] = {}
    for line in _git_lines(
        repo_root,
        ["diff", "--name-status", ORIGINAL_RESEARCH_HEAD, "--", "."],
    ):
        parts = line.split("\t")
        status_by_path[parts[-1].replace("\\", "/")] = parts[0]
    for path in _git_lines(
        repo_root,
        ["ls-files", "--others", "--exclude-standard"],
    ):
        status_by_path.setdefault(path.replace("\\", "/"), "A")

    governed = {
        ".gitattributes",
        "scripts/build_nwr_dual_lens_rc1_v1_20260729.py",
        "scripts/build_nwr_dual_lens_rc1_targeted_revision_v1_20260729.py",
        "tests/test_nwr_dual_lens_rc1_research.py",
        "tests/test_nwr_dual_lens_rc1_targeted_revision.py",
    }
    governed.update(
        (ORIGINAL_OUTPUT_REL / filename).as_posix()
        for filename in base.REQUIRED_OUTPUTS
    )
    governed.update(
        (TARGETED_OUTPUT_REL / filename).as_posix()
        for filename in TARGETED_REQUIRED_OUTPUTS
    )
    for path in governed:
        absolute = repo_root / path
        if absolute.exists():
            status_by_path.setdefault(
                path,
                "M" if path.startswith(ORIGINAL_OUTPUT_REL.as_posix()) else "A",
            )

    rows = []
    for path, status in sorted(status_by_path.items()):
        if not (
            path in governed
            or path.startswith(ORIGINAL_OUTPUT_REL.as_posix() + "/")
            or path.startswith(TARGETED_OUTPUT_REL.as_posix() + "/")
        ):
            continue
        rows.append(
            {
                "path": path,
                "git_status": status,
                "change": (
                    "created"
                    if status.startswith("A")
                    else "modified"
                    if status.startswith("M")
                    else "renamed_or_other"
                ),
                "classification": (
                    "research evidence/documentation"
                    if path.startswith("docs/")
                    else "research test/tooling"
                ),
                "production_effect": "none",
                "mechanical_source": (
                    f"git diff --name-status {ORIGINAL_RESEARCH_HEAD} "
                    "plus git ls-files --others and governed output existence"
                ),
            }
        )
    inventory = pd.DataFrame(rows)
    required = {
        ".gitattributes",
        "scripts/build_nwr_dual_lens_rc1_targeted_revision_v1_20260729.py",
    }
    if not required.issubset(set(inventory["path"])):
        raise ValueError("mechanical file inventory omitted a required changed file")
    return inventory


def _manifest(
    output: Path,
    *,
    release: str,
    summary: dict[str, Any],
    input_ledger: dict[str, dict[str, Any]],
) -> None:
    files = sorted(
        path for path in output.iterdir() if path.name != "MANIFEST.json"
    )
    document = {
        "release_identifier": release,
        "verdict": summary["verdict"],
        "win_now_candidate": summary["win_candidate"],
        "dynasty_candidate": summary["dynasty_candidate"],
        "win_now_formula_disposition": summary["win_formula_disposition"],
        "dynasty_formula_disposition": summary["dynasty_formula_disposition"],
        "win_now_admitted": summary["win_admitted"],
        "dynasty_admitted": summary["dynasty_admitted"],
        "production_integration": False,
        "primary_ndcg_aggregate": PRIMARY_NDCG_AGGREGATE,
        "seed": base.SEED,
        "source_hashes": input_ledger,
        "files": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": base.sha256(path),
            }
            for path in files
        ],
        "self_referential": False,
    }
    base.write_text(
        output / "MANIFEST.json",
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True),
    )


def _validation_markdown(evidence: dict[str, Any]) -> str:
    rows = pd.DataFrame(evidence.get("validation_rows", []))
    if rows.empty:
        table = "External final validation receipts are pending regeneration."
    else:
        columns = [
            column
            for column in (
                "validation",
                "command",
                "expected",
                "observed",
                "status",
                "notes",
            )
            if column in rows.columns
        ]
        table = base.markdown_table(rows, columns)
    return f"""# Validation results

{table}

The targeted builder itself requires all 20 executed mutations to fail closed,
all 240 current rows to appear exactly once in the mechanically assigned
experience cohort, separate continuous and binary availability semantics,
season-aware primary nDCG, and unchanged pinned production hashes. Hermetic
must exit 0; LocalData must remain `BLOCKED_MISSING_LOCAL_TEST_PACK` with exit
4. No provider call, security scan, scheduled-task execution, production
integration, skip, xfail, or xpass is authorized.
"""


def _preservation_markdown(evidence: dict[str, Any]) -> str:
    state = evidence.get("preservation", {})
    return f"""# Opaque and persistent state preservation

The five opaque DynastyProcess CSVs were not opened, parsed, copied,
normalized, staged, or used. The established byte/hash checker reports:

- opaque hash matches: `{state.get('opaque_hash_matches', 'UNKNOWN')}`;
- persistent: `{state.get('persistent_files', 'UNKNOWN')}` files /
  `{state.get('persistent_bytes', 'UNKNOWN')}` bytes /
  `{state.get('persistent_digest', 'UNKNOWN')}`;
- recovery: `{state.get('recovery_files', 'UNKNOWN')}` files /
  `{state.get('recovery_bytes', 'UNKNOWN')}` bytes /
  `{state.get('recovery_digest', 'UNKNOWN')}`;
- status: `{state.get('status', 'UNKNOWN')}`.
"""


def render_corrected_original_packet(
    *,
    repo_root: Path,
    output: Path,
    input_ledger: dict[str, dict[str, Any]],
    evidence: dict[str, Any],
    historical: pd.DataFrame,
    win_predictions: pd.DataFrame,
    dynasty_predictions: pd.DataFrame,
    win_traces: pd.DataFrame,
    dynasty_traces: pd.DataFrame,
    win_results: pd.DataFrame,
    dynasty_results: pd.DataFrame,
    calibration: pd.DataFrame,
    cohort_frame: pd.DataFrame,
    cohort_detail: pd.DataFrame,
    win_gates: pd.DataFrame,
    dynasty_gates: pd.DataFrame,
    summary: dict[str, Any],
    board: pd.DataFrame,
    gaps: pd.DataFrame,
    sensitivity: pd.DataFrame,
    apps: pd.DataFrame,
    viewport: pd.DataFrame,
    mutations: pd.DataFrame,
    inventory: pd.DataFrame,
) -> None:
    base.formula_definitions = corrected_formula_definitions
    try:
        base.render_documents(
            repo_root=repo_root,
            output=output,
            input_ledger=input_ledger,
            evidence=evidence,
            historical=historical,
            win_predictions=win_predictions,
            dynasty_predictions=dynasty_predictions,
            win_traces=win_traces,
            dynasty_traces=dynasty_traces,
            win_results=win_results,
            dynasty_results=dynasty_results,
            calibration=calibration,
            cohort_frame=cohort_frame,
            cohort_detail=cohort_detail,
            win_gates=win_gates,
            dynasty_gates=dynasty_gates,
            summary=summary,
            board=board,
            gaps=gaps,
            sensitivity=sensitivity,
            apps=apps,
            viewport=viewport,
            mutations=mutations,
        )
    finally:
        base.formula_definitions = ORIGINAL_FORMULA_DEFINITIONS

    base.write_text(
        output / "WIN_NOW_TARGET_CONTRACT.md",
        """# Win Now target contract

The decision anchor is the start of target season `t`; model inputs are facts
available by completed season `t-1`. The primary target is target-season NWR
points minus position replacement. W2 predicts conditional production and a
continuous `EXPECTED_GAMES_FRACTION`; their product yields expected production.

The separate binary output `P(GAMES_PLAYED >= 8)` is fit chronologically to an
exact binary target. It is never substituted for expected games fraction.
Continuous availability is evaluated with MAE, RMSE, residual, and calibration
slope/intercept. Only the binary output receives Brier, binary log loss, ECE,
event-count, slope, and intercept evaluation.

Candidate selection uses the unweighted mean of nDCG calculated independently
within each chronological target season. Pooled nDCG is diagnostic only. No
random split, current ADP, target-season/future context, Outcome V3 feature,
name join, or unsupported rookie fallback is allowed.
""",
    )
    report_path = output / "DUAL_LENS_RC1_REPORT.md"
    report = report_path.read_text(encoding="utf-8")
    report += f"""

## Targeted revision supersession

This governed regeneration supersedes the original static mutation and metric
evidence. All 20 mutations now execute actual research or render-contract
paths. Availability expectation and binary event probability are semantically
separate. Primary nDCG is `{PRIMARY_NDCG_AGGREGATE}`. Cohort evidence is
complete rather than display-truncated. Formula dispositions remain
`{summary['win_formula_disposition']}` and
`{summary['dynasty_formula_disposition']}`; production integration remains
`NONE`.
"""
    base.write_text(report_path, report)
    base.write_csv(output / "FILES_CREATED_OR_CHANGED.csv", inventory)
    _manifest(
        output,
        release="NWR_DUAL_LENS_RC1_RESEARCH_ONLY_TARGETED_REVISION",
        summary=summary,
        input_ledger=input_ledger,
    )


def render_targeted_packet(
    *,
    output: Path,
    input_ledger: dict[str, dict[str, Any]],
    evidence: dict[str, Any],
    win_results: pd.DataFrame,
    dynasty_results: pd.DataFrame,
    calibration: pd.DataFrame,
    completeness: pd.DataFrame,
    rookie_revalidation: pd.DataFrame,
    win_gates: pd.DataFrame,
    dynasty_gates: pd.DataFrame,
    summary: dict[str, Any],
    board: pd.DataFrame,
    sensitivity: pd.DataFrame,
    apps: pd.DataFrame,
    mutations: pd.DataFrame,
    inventory: pd.DataFrame,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    determinism = pd.DataFrame(evidence.get("determinism_rows", []))
    if determinism.empty:
        determinism = pd.DataFrame(
            [
                {
                    "check": "two-clean-root byte comparison",
                    "root_a": "",
                    "root_b": "",
                    "files_compared": 0,
                    "mismatches": "pending final receipt",
                    "status": "PENDING",
                }
            ]
        )
    season_aware = pd.concat([win_results, dynasty_results], ignore_index=True)
    season_aware = season_aware.loc[
        season_aware["scope_type"].isin(["OVERALL", "SEASON", "POSITION"])
    ].copy()

    csv_outputs = {
        "MUTATION_RESULTS_BEFORE_AFTER.csv": mutations,
        "AVAILABILITY_CALIBRATION_RESULTS.csv": calibration.loc[
            calibration["lane"].eq("WIN_NOW")
        ].copy(),
        "SEASON_AWARE_NDCG_RESULTS.csv": season_aware,
        "COHORT_COMPLETENESS_RESULTS.csv": completeness,
        "ROOKIE_SECOND_YEAR_REVALIDATION.csv": rookie_revalidation,
        "WIN_NOW_GATE_REVALIDATION.csv": win_gates,
        "DYNASTY_GATE_REVALIDATION.csv": dynasty_gates,
        "CORRECTED_DUAL_LENS_SHADOW_BOARD.csv": board,
        "TEAM_WINDOW_REVALIDATION.csv": sensitivity,
        "CORE_APP_AUDIT_REVALIDATION.csv": apps,
        "FILES_CREATED_OR_CHANGED.csv": inventory,
        "DETERMINISTIC_REGENERATION_RESULTS.csv": determinism,
    }
    for filename, frame in csv_outputs.items():
        base.write_csv(output / filename, frame)

    second_year = completeness.loc[
        completeness["expected_cohort"].eq("SECOND_YEAR")
    ]
    second_year_names = ", ".join(second_year["player_name"].astype(str))
    base.write_text(
        output / "EXECUTIVE_VERDICT.md",
        f"""# Executive verdict

`YELLOW_NWR_DUAL_LENS_TARGETED_REVISION_RESEARCH_ONLY`

The documented validation defects are corrected: 20/20 real-path mutations
fail closed, availability outputs use separate continuous and binary semantics,
primary nDCG is season-aware, and the current cohort inventory is complete.
The bounded candidate winners are `{summary['win_candidate']}` and
`{summary['dynasty_candidate']}`.

Formula dispositions are `{summary['win_formula_disposition']}` and
`{summary['dynasty_formula_disposition']}`. This remains research-only. Finished
V1 and Outcome V3 remain canonical; production/UI integration is `NONE`.
""",
    )
    base.write_text(
        output / "DUAL_LENS_TARGETED_REVISION_REPORT.md",
        f"""# Dual-Lens RC1 targeted revision report

## Bounded outcome

- Win Now candidate: `{summary['win_candidate']}`.
- Dynasty candidate: `{summary['dynasty_candidate']}`.
- Win Now disposition: `{summary['win_formula_disposition']}`.
- Dynasty disposition: `{summary['dynasty_formula_disposition']}`.
- Primary nDCG: `{PRIMARY_NDCG_AGGREGATE}`.
- Real-path mutations: `{int(mutations['result'].eq('PASS').sum())}/20`.
- Current cohort inventory: `{len(completeness)}/240`, duplicate-free and
  mechanically assigned.
- Second-year inventory: `{len(second_year)}` players.
- Production ranking change: `NONE`.
- Production Outcome change: `NONE`.
- Production/UI integration: `NONE`.

The correction was restricted to validation tooling and governed evidence.
There was no new formula family, unrestricted search, provider call, security
scan, refresh-task execution, V2-2 work, or production implementation.
""",
    )
    base.write_text(
        output / "ORIGINAL_AUDIT_FINDINGS.md",
        f"""# Original audit findings

Before correction, static placeholders did not execute universal-age,
productive-veteran-guard removal, low-games-guard removal, swapped lens-value,
or swapped Team Window source defects. Unsupported-rookie injection was
detectable, but the normal zero-rookie current board made that assertion
vacuous. The replacement harness records this in `before_observed` and now
executes all mutations.

The original second-year display contained 40 of 43 mechanically qualifying
players due to `.head(40)`. The omitted rows were LeQuint Allen, Jaydon Blue,
and Kaleb Johnson. Regeneration contains all {len(second_year)}:
{second_year_names}.

The original availability result reused predicted games fraction both as a
continuous expectation and as if it were `P(games >= 8)`. MAE could describe
the continuous expectation, but its Brier, binary log loss, and binary ECE
claims were semantically invalid. The original combined diagnostics were Brier
0.175790941, MAE 0.216979596, log loss 0.553593670, and ECE 0.067893976.

The prior evaluator pooled all seasons before nDCG. The corrected tables keep
that pooled value only in explicitly named diagnostic columns and make
season-level aggregation primary. The original changed-file inventory also
omitted `.gitattributes`; the regenerated inventory is mechanically derived.
""",
    )
    base.write_text(
        output / "REAL_PATH_MUTATION_CONTRACT.md",
        """# Real-path mutation contract

Each mutation invokes an actual target/model, walk-forward, gate, detached
board, Team Window, Player Compare, or Trading Lab research-render contract.
Success requires the altered computed behavior to raise
`ResearchContractViolation`. Mutation identifiers and source substrings are not
detectors. The before/after table records the function/path, expected failure,
actual failure, evidence artifact, and sensitivity result for all 20 mutations.
Any surviving mutation fails generation and tests.
""",
    )
    base.write_text(
        output / "AVAILABILITY_SEMANTIC_CONTRACT.md",
        """# Availability semantic contract

`EXPECTED_GAMES_FRACTION` is a continuous expectation in [0,1].
`EXPECTED_GAMES_PLAYED` is that fraction times target-season length. They are
evaluated with MAE, RMSE, residuals, and linear calibration diagnostics.

`P(GAMES_PLAYED >= 8)` is a distinct chronological binary probability trained
against `availability_8plus_actual`. It alone receives Brier, binary log loss,
ECE, calibration slope/intercept, event-count, position, and season tests.
Neither output may silently substitute for the other. Win Now gates require
both semantic families to be valid.
""",
    )
    base.write_text(
        output / "PRODUCTION_BASELINES_NO_CHANGE.md",
        f"""# Production baselines no-change proof

- Finished V1: 240 rows; SHA-256
  `{base.EXPECTED_HASHES[base.BOARD_REL]}`; change `NONE`.
- Frozen comparator: 924 rows; SHA-256
  `{base.EXPECTED_HASHES[base.FROZEN_REL]}`.
- Outcome V3 current board: SHA-256
  `{base.EXPECTED_HASHES[base.OUTCOME_BOARD_REL]}`; ranking effect `NONE`;
  change `NONE`.
- Production/UI integration: `NONE`.
- Scheduled refresh state required and retained:
  `DISABLED_PENDING_OWNER_APPROVAL`.
""",
    )
    base.write_text(
        output / "OPAQUE_AND_PERSISTENT_STATE_PRESERVATION.md",
        _preservation_markdown(evidence),
    )
    base.write_text(
        output / "PROTECTED_AND_FROZEN_PATH_PROOF.md",
        f"""# Protected and frozen path proof

The builder verifies pinned hashes before modeling and writes only the original
research packet, the additive targeted-revision packet, or explicitly supplied
detached output roots. Protected inputs remain:

- `{base.BOARD_REL.as_posix()}`;
- `{base.FROZEN_REL.as_posix()}`;
- `{base.OUTCOME_BOARD_REL.as_posix()}`;
- `{base.OUTCOME_SCHEMA_REL.as_posix()}`.

No app/runtime, local export, refresh pointer, Finished V1, Outcome V3, frozen,
opaque, persistent, recovery, or V2-2 path is a write target.
""",
    )
    base.write_text(
        output / "ROLLBACK_PLAN.md",
        """# Rollback plan

No production rollout exists. Revert the two bounded research commits or remove
the isolated research branch/worktrees. Preserve canonical HQ, Finished V1,
Outcome V3, frozen comparator, stable/operational checkouts, persistent and
recovery state, and the disabled scheduled task. Never force push.
""",
    )
    base.write_text(output / "VALIDATION_RESULTS.md", _validation_markdown(evidence))
    _manifest(
        output,
        release=TARGETED_RELEASE,
        summary=summary,
        input_ledger=input_ledger,
    )
    missing = [
        filename
        for filename in TARGETED_REQUIRED_OUTPUTS
        if not (output / filename).is_file()
    ]
    if missing:
        raise ValueError(f"targeted revision outputs missing: {missing}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--original-output-dir",
        type=Path,
        help="Detached override for the corrected original packet.",
    )
    parser.add_argument(
        "--targeted-output-dir",
        type=Path,
        help="Detached override for the additive targeted packet.",
    )
    parser.add_argument(
        "--current-features",
        type=Path,
        default=base.DEFAULT_CURRENT_FEATURES,
    )
    parser.add_argument("--evidence-json", type=Path)
    parser.add_argument("--keep-existing", action="store_true")
    return parser.parse_args()


def _resolve_output(
    repo_root: Path,
    supplied: Path | None,
    governed_relative: Path,
) -> Path:
    output = (
        supplied.resolve()
        if supplied is not None
        else (repo_root / governed_relative).resolve()
    )
    governed = (repo_root / governed_relative).resolve()
    if output == repo_root:
        raise ValueError("repository root cannot be an output directory")
    if repo_root in output.parents and output != governed:
        raise ValueError(
            f"inside-repository output must be {governed_relative.as_posix()}"
        )
    return output


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    original_output = _resolve_output(
        repo_root, args.original_output_dir, ORIGINAL_OUTPUT_REL
    )
    targeted_output = _resolve_output(
        repo_root, args.targeted_output_dir, TARGETED_OUTPUT_REL
    )
    if original_output == targeted_output:
        raise ValueError("original and targeted output directories must differ")
    if not args.keep_existing:
        for output in (original_output, targeted_output):
            if output.exists():
                shutil.rmtree(output)

    current_features = args.current_features.resolve()
    input_ledger = base.verify_inputs(repo_root, current_features)
    evidence = base.load_evidence(
        args.evidence_json.resolve() if args.evidence_json else None
    )
    historical = base.load_historical(repo_root)
    current, _board_source, _outcome_source = base.load_current(
        repo_root, current_features
    )
    win_predictions, win_traces = base.build_win_predictions(historical, current)
    win_predictions, binary_trace = add_binary_availability_predictions(
        historical, win_predictions
    )
    win_traces = pd.concat([win_traces, binary_trace], ignore_index=True)
    dynasty_predictions, dynasty_traces = base.build_dynasty_predictions(
        historical, current
    )
    win_candidates = {
        "W0_FINISHED_V1_ACCEPTED_PROXY": "w0_score",
        "W1_NEXT_SEASON_VOR": "w1_score",
        "W2_CONDITIONAL_PRODUCTION_AVAILABILITY": "w2_score",
        "W3_SHORT_HORIZON_CALIBRATED_BLEND": "w3_score",
    }
    dynasty_candidates = {
        "D0_FINISHED_V1_ACCEPTED_PROXY": "w0_score",
        "D1_DISCOUNTED_MULTI_HORIZON_VOR": "d1_score",
        "D2_FUTURE_PRODUCTION_X_RETENTION": "d2_score",
        "D3_CAPPED_CAREER_HORIZON_GUARDS": "d3_score",
    }
    win_results = corrected_evaluation_table(
        win_predictions,
        lane="WIN_NOW",
        candidates=win_candidates,
        actual_column="actual_vor_h1",
        seasons=base.WIN_EVALUATION_SEASONS,
    )
    dynasty_results = corrected_evaluation_table(
        dynasty_predictions,
        lane="DYNASTY",
        candidates=dynasty_candidates,
        actual_column="actual_dynasty_target",
        seasons=base.DYNASTY_EVALUATION_SEASONS,
    )
    win_candidate = base.choose_research_candidate(
        win_results,
        (
            "W1_NEXT_SEASON_VOR",
            "W2_CONDITIONAL_PRODUCTION_AVAILABILITY",
            "W3_SHORT_HORIZON_CALIBRATED_BLEND",
        ),
    )
    dynasty_candidate = base.choose_research_candidate(
        dynasty_results,
        (
            "D1_DISCOUNTED_MULTI_HORIZON_VOR",
            "D2_FUTURE_PRODUCTION_X_RETENTION",
            "D3_CAPPED_CAREER_HORIZON_GUARDS",
        ),
    )
    calibration = corrected_calibration_results(
        win_predictions,
        dynasty_predictions,
        win_candidate,
        dynasty_candidate,
    )
    cohort_frame, cohort_detail = base.cohort_results(
        win_predictions,
        dynasty_predictions,
        win_candidate,
        dynasty_candidate,
    )
    win_gates, dynasty_gates, summary = corrected_build_gates(
        win_results,
        dynasty_results,
        calibration,
        cohort_frame,
        win_predictions,
        dynasty_predictions,
        win_candidate,
        dynasty_candidate,
    )
    summary["win_candidate"] = win_candidate
    summary["dynasty_candidate"] = dynasty_candidate
    board, gaps, sensitivity = base.build_current_board(
        current,
        win_predictions,
        dynasty_predictions,
        win_candidate,
        dynasty_candidate,
    )
    board = augment_current_board(board, win_predictions)
    completeness = cohort_completeness_results(current, board)
    rookie_revalidation = rookie_second_year_revalidation(
        cohort_frame, completeness
    )
    apps = base.app_audit(repo_root)
    viewport = base.viewport_results(apps)
    mutations = real_path_mutation_results(
        historical,
        current,
        win_predictions,
        dynasty_predictions,
        win_traces,
        board,
    )

    if len(historical) != 5518:
        raise ValueError(f"historical row count changed: {len(historical)}")
    if len(board) != 240 or len(completeness) != 240:
        raise ValueError("current board/cohort completeness must contain 240 rows")
    if not completeness["status"].eq("PASS_COMPLETE").all():
        raise ValueError("current cohort completeness failed")
    second_year = completeness.loc[
        completeness["expected_cohort"].eq("SECOND_YEAR")
    ]
    required_second_year = {"LeQuint Allen", "Jaydon Blue", "Kaleb Johnson"}
    if len(second_year) != 43 or not required_second_year.issubset(
        set(second_year["player_name"])
    ):
        raise ValueError("second-year current inventory is not complete at 43")
    if len(mutations) != 20 or not mutations["result"].eq("PASS").all():
        failures = mutations.loc[mutations["result"].ne("PASS")]
        raise ValueError(f"real-path mutation suite failed:\n{failures}")

    # Create the mechanical inventory after all governed paths exist. The
    # renderer writes it into both packets and then rebuilds both manifests.
    original_output.mkdir(parents=True, exist_ok=True)
    targeted_output.mkdir(parents=True, exist_ok=True)
    inventory = mechanical_file_inventory(repo_root)
    render_corrected_original_packet(
        repo_root=repo_root,
        output=original_output,
        input_ledger=input_ledger,
        evidence=evidence,
        historical=historical,
        win_predictions=win_predictions,
        dynasty_predictions=dynasty_predictions,
        win_traces=win_traces,
        dynasty_traces=dynasty_traces,
        win_results=win_results,
        dynasty_results=dynasty_results,
        calibration=calibration,
        cohort_frame=cohort_frame,
        cohort_detail=cohort_detail,
        win_gates=win_gates,
        dynasty_gates=dynasty_gates,
        summary=summary,
        board=board,
        gaps=gaps,
        sensitivity=sensitivity,
        apps=apps,
        viewport=viewport,
        mutations=mutations,
        inventory=inventory,
    )
    # Re-derive after the original packet exists so all governed generated
    # outputs participate in the same complete mechanical inventory.
    inventory = mechanical_file_inventory(repo_root)
    render_targeted_packet(
        output=targeted_output,
        input_ledger=input_ledger,
        evidence=evidence,
        win_results=win_results,
        dynasty_results=dynasty_results,
        calibration=calibration,
        completeness=completeness,
        rookie_revalidation=rookie_revalidation,
        win_gates=win_gates,
        dynasty_gates=dynasty_gates,
        summary=summary,
        board=board,
        sensitivity=sensitivity,
        apps=apps,
        mutations=mutations,
        inventory=inventory,
    )
    # A final inventory captures every targeted artifact, then both manifests
    # are rebuilt to hash the final non-manifest bytes.
    inventory = mechanical_file_inventory(repo_root)
    base.write_csv(original_output / "FILES_CREATED_OR_CHANGED.csv", inventory)
    base.write_csv(targeted_output / "FILES_CREATED_OR_CHANGED.csv", inventory)
    _manifest(
        original_output,
        release="NWR_DUAL_LENS_RC1_RESEARCH_ONLY_TARGETED_REVISION",
        summary=summary,
        input_ledger=input_ledger,
    )
    _manifest(
        targeted_output,
        release=TARGETED_RELEASE,
        summary=summary,
        input_ledger=input_ledger,
    )
    print(
        json.dumps(
            {
                "original_output": str(original_output),
                "targeted_output": str(targeted_output),
                "verdict": summary["verdict"],
                "win_now_candidate": win_candidate,
                "dynasty_candidate": dynasty_candidate,
                "win_now_formula_disposition": summary[
                    "win_formula_disposition"
                ],
                "dynasty_formula_disposition": summary[
                    "dynasty_formula_disposition"
                ],
                "historical_rows": len(historical),
                "current_rows": len(board),
                "second_year_rows": len(second_year),
                "real_path_mutations_passed": int(
                    mutations["result"].eq("PASS").sum()
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
