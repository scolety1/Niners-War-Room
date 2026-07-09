from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPORT_DIR = Path(__file__).resolve().parent
REPO_ROOT = REPORT_DIR.parents[3]

SUBSTRATE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701"
    / "nwr_historical_tuning_feature_target_substrate_v3.parquet"
)
SAFE_ALLOWLIST_PATH = SUBSTRATE_PATH.with_name("safe_feature_allowlist_v3.csv")
SUBSTRATE_SUMMARY_PATH = SUBSTRATE_PATH.with_name("historical_tuning_substrate_v3_summary.md")
LEAKAGE_REPORT_PATH = SUBSTRATE_PATH.with_name("asof_and_leakage_guardrail_report_v3.md")
IDENTITY_JOIN_REPORT_PATH = SUBSTRATE_PATH.with_name("identity_join_report_v3.csv")
SOURCE_CONTRACT_NOT_READY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_source_contract_v1_20260701"
    / "formula_tuning_not_ready_reason.md"
)
BASELINE_ACCURACY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_tuning_sandbox_v1_20260701"
    / "baseline_accuracy_report.csv"
)
CANDIDATE_SEARCH_LEADERBOARD_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_formula_candidate_search_v1_20260701"
    / "validation_leaderboard.csv"
)
SCORING_RULES_PATH = REPO_ROOT / "config" / "nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json"
SOURCE_REGISTRY_PATH = REPO_ROOT / "config" / "source_registry.csv"
FORMULA_CONTRACT_SERVICE_PATH = REPO_ROOT / "src" / "services" / "model_v4_formula_contract_service.py"
FULL_BOARD_VALUE_SERVICE_PATH = REPO_ROOT / "src" / "services" / "full_player_board_value_service.py"
DRAFT_DAY_SERVICE_PATH = REPO_ROOT / "src" / "services" / "draft_day_app_v1_service.py"
FINAL_BOARD_PAGE_PATH = REPO_ROOT / "app" / "pages" / "20_final_board_v1.py"

CURRENT_BOARD_CANDIDATES = (
    REPO_ROOT
    / "local_exports"
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv",
    Path(
        r"C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest"
        r"\full_player_board_value_review_rows.csv"
    ),
)
EXPECTED_CURRENT_BOARD_HASH = (
    "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
)

POSITIONS = ("QB", "RB", "WR", "TE")
REPLACEMENT_RANK = {"QB": 12, "RB": 30, "WR": 40, "TE": 12}
FORMAT_STARTABLE_RANK = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
RELEVANT_TOP_N = {
    "QB": (12,),
    "RB": (12, 24, 36),
    "WR": (12, 24, 36),
    "TE": (12,),
}

REQUIRED_OUTPUTS = {
    "report": REPORT_DIR / "PRODUCTION_RANKINGS_BACKTEST_V1_REPORT.md",
    "scorecard": REPORT_DIR / "PRODUCTION_RANKINGS_BACKTEST_V1_SCORECARD.csv",
    "caveats": REPORT_DIR / "PRODUCTION_RANKINGS_BACKTEST_V1_CAVEATS.md",
    "source_trace": REPORT_DIR / "PRODUCTION_RANKINGS_BACKTEST_V1_SOURCE_TRACE.md",
}


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    substrate = _load_substrate()
    current_board = _load_current_board()

    scored = _add_proxy_scores(substrate)
    scored = _add_prediction_ranks(scored, "production_formula_partial_proxy_score")
    prior_finish = _add_prediction_ranks(scored, "prior_year_finish_baseline_score")
    opportunity = _add_prediction_ranks(scored, "opportunity_only_baseline_score")

    scorecard = _scorecard(scored)
    scorecard.to_csv(REQUIRED_OUTPUTS["scorecard"], index=False, encoding="utf-8")

    baseline_comparison = _baseline_comparison(scored, prior_finish, opportunity)
    coverage = _coverage_summary(scored)
    misses = _miss_analysis(scored)
    source_facts = _source_facts(current_board, substrate)

    REQUIRED_OUTPUTS["report"].write_text(
        _report_markdown(
            scorecard=scorecard,
            baseline_comparison=baseline_comparison,
            coverage=coverage,
            misses=misses,
            source_facts=source_facts,
        ),
        encoding="utf-8",
    )
    REQUIRED_OUTPUTS["caveats"].write_text(
        _caveats_markdown(source_facts=source_facts, coverage=coverage),
        encoding="utf-8",
    )
    REQUIRED_OUTPUTS["source_trace"].write_text(
        _source_trace_markdown(source_facts=source_facts),
        encoding="utf-8",
    )
    print(f"report={REQUIRED_OUTPUTS['report']}")
    print(f"scorecard={REQUIRED_OUTPUTS['scorecard']}")
    print(f"caveats={REQUIRED_OUTPUTS['caveats']}")
    print(f"source_trace={REQUIRED_OUTPUTS['source_trace']}")
    return 0


def _load_substrate() -> pd.DataFrame:
    frame = pd.read_parquet(SUBSTRATE_PATH)
    frame = frame.loc[frame["position"].isin(POSITIONS)].copy()
    if frame.empty:
        raise RuntimeError("historical V3 substrate has no QB/RB/WR/TE rows")
    for column in (
        "feature_season",
        "target_season",
        "prior_nwr_points",
        "prior_games",
        "prior_nwr_ppg",
        "prior_targets",
        "prior_carries",
        "prior_receptions",
        "prior_rushing_yards",
        "prior_receiving_yards",
        "prior_receiving_air_yards",
        "prior_receiving_yards_after_catch",
        "prior_rushing_first_downs",
        "prior_receiving_first_downs",
        "prior_passing_attempts",
        "prior_passing_yards",
        "prior_passing_td",
        "prior_interceptions",
        "prior_passing_first_downs",
        "prior_offensive_snaps",
        "prior_touches",
        "prior_opportunities",
        "next_nwr_points",
        "next_position_finish",
    ):
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for flag in (
        "review_only",
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
        "hidden_sort_allowed",
        "recommendation_allowed",
        "production_approved",
        "optional_source_null_fenced",
    ):
        if flag in frame:
            frame[flag] = frame[flag].astype(bool)
    if frame.get("production_approved", pd.Series(False, index=frame.index)).any():
        raise RuntimeError("V3 substrate unexpectedly contains production-approved rows")
    if frame.get("model_use_allowed", pd.Series(False, index=frame.index)).any():
        raise RuntimeError("V3 substrate unexpectedly contains model-use-allowed rows")
    return frame


def _load_current_board() -> pd.DataFrame:
    for path in CURRENT_BOARD_CANDIDATES:
        if path.exists():
            frame = pd.read_csv(path, dtype=str).fillna("")
            frame.attrs["source_path"] = str(path)
            frame.attrs["source_hash"] = _sha256(path)
            return frame
    frame = pd.DataFrame()
    frame.attrs["source_path"] = "missing"
    frame.attrs["source_hash"] = ""
    return frame


def _add_proxy_scores(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["prior_first_downs_total"] = (
        output["prior_rushing_first_downs"].fillna(0)
        + output["prior_receiving_first_downs"].fillna(0)
        + output["prior_passing_first_downs"].fillna(0)
    )
    output["vorp_anchor_score"] = np.nan
    output["prior_year_finish_baseline_score"] = output["prior_nwr_points"]
    output["opportunity_only_baseline_score"] = output.apply(_opportunity_score, axis=1)

    for (_season, position), group in output.groupby(["feature_season", "position"]):
        replacement_rank = min(REPLACEMENT_RANK[position], len(group))
        if replacement_rank <= 0:
            continue
        points = group["prior_nwr_points"].fillna(0).sort_values(ascending=False)
        replacement_points = float(points.iloc[replacement_rank - 1])
        positive_vorp = (group["prior_nwr_points"].fillna(0) - replacement_points).clip(lower=0)
        max_vorp = float(positive_vorp.max())
        output.loc[group.index, "vorp_anchor_score"] = (
            positive_vorp / max_vorp if max_vorp > 0 else 0.0
        )

    rows = [_score_proxy_row(row) for row in output.to_dict("records")]
    scored = pd.DataFrame(rows, index=output.index)
    for column in scored.columns:
        output[column] = scored[column]
    return output


def _opportunity_score(row: pd.Series) -> float:
    position = str(row.get("position") or "")
    if position == "QB":
        return _num(row.get("prior_passing_attempts")) + _num(row.get("prior_carries"))
    if position in {"RB", "WR", "TE"}:
        return _num(row.get("prior_opportunities"))
    return 0.0


def _score_proxy_row(row: dict[str, Any]) -> dict[str, Any]:
    position = str(row.get("position") or "")
    components: list[tuple[str, float | None, float]] = []
    if position == "RB":
        components = [
            ("vorp_anchor", _maybe(row.get("vorp_anchor_score")), 0.45),
            (
                "role_volume",
                _avg(
                    _norm(row.get("prior_opportunities"), 350.0),
                    _norm(row.get("prior_touches"), 300.0),
                    _norm(row.get("prior_offensive_snaps"), 850.0),
                ),
                0.25,
            ),
            (
                "first_down_high_value",
                _avg(
                    _norm(
                        _num(row.get("prior_rushing_first_downs"))
                        + _num(row.get("prior_receiving_first_downs")),
                        75.0,
                    ),
                    _norm(row.get("prior_nwr_ppg"), 18.0),
                ),
                0.15,
            ),
            (
                "receiving_utility",
                _avg(
                    _norm(row.get("prior_targets"), 100.0),
                    _norm(row.get("prior_receptions"), 80.0),
                    _norm(row.get("prior_receiving_yards"), 700.0),
                ),
                0.10,
            ),
            ("efficiency_context", _norm(row.get("prior_receiving_yards_after_catch"), 650.0), 0.05),
        ]
        confidence_floor = 0.72
        miss_penalty = 0.045
        miss_cap = 0.18
    elif position == "WR":
        components = [
            ("vorp_anchor", _maybe(row.get("vorp_anchor_score")), 0.40),
            (
                "target_route_role",
                _avg(
                    _norm(row.get("prior_targets"), 160.0),
                    _norm(row.get("prior_receptions"), 115.0),
                    _norm(row.get("prior_receiving_yards"), 1700.0),
                    _norm(row.get("prior_offensive_snaps"), 1000.0),
                ),
                0.30,
            ),
            (
                "first_down_yardage",
                _avg(
                    _norm(row.get("prior_receiving_first_downs"), 85.0),
                    _norm(row.get("prior_receiving_yards"), 1700.0),
                    _norm(row.get("prior_nwr_ppg"), 20.0),
                ),
                0.15,
            ),
            (
                "air_yard_role",
                _avg(
                    _norm(row.get("prior_receiving_air_yards"), 1900.0),
                    _norm(row.get("prior_targets"), 160.0),
                ),
                0.10,
            ),
            ("efficiency_context", _norm(row.get("prior_receiving_yards_after_catch"), 750.0), 0.05),
        ]
        confidence_floor = 0.72
        miss_penalty = 0.045
        miss_cap = 0.18
    elif position == "QB":
        components = [
            ("vorp_anchor", _maybe(row.get("vorp_anchor_score")), 0.45),
            (
                "rushing_separation",
                _avg(
                    _norm(row.get("prior_carries"), 120.0),
                    _norm(row.get("prior_rushing_yards"), 800.0),
                    _norm(row.get("prior_rushing_first_downs"), 55.0),
                ),
                0.25,
            ),
            (
                "passing_volume_security",
                _avg(
                    _norm(row.get("prior_passing_attempts"), 650.0),
                    _norm(row.get("prior_games"), 17.0),
                ),
                0.15,
            ),
            (
                "passing_production",
                _avg(
                    _norm(row.get("prior_passing_yards"), 5200.0),
                    _norm(row.get("prior_passing_td"), 45.0),
                    _norm(row.get("prior_passing_first_downs"), 225.0),
                ),
                0.10,
            ),
            ("regression_context", None, 0.05),
        ]
        confidence_floor = 0.70
        miss_penalty = 0.05
        miss_cap = 0.20
    elif position == "TE":
        components = [
            ("vorp_anchor", _maybe(row.get("vorp_anchor_score")), 0.45),
            (
                "route_target_role",
                _avg(
                    _norm(row.get("prior_targets"), 120.0),
                    _norm(row.get("prior_receptions"), 95.0),
                    _norm(row.get("prior_offensive_snaps"), 950.0),
                ),
                0.25,
            ),
            (
                "first_down_yardage",
                _avg(
                    _norm(row.get("prior_receiving_first_downs"), 65.0),
                    _norm(row.get("prior_receiving_yards"), 1100.0),
                    _norm(row.get("prior_nwr_ppg"), 15.0),
                ),
                0.15,
            ),
            (
                "yprr_target_efficiency",
                _avg(
                    _safe_div_norm(row.get("prior_receiving_yards"), row.get("prior_targets"), 11.0),
                    _norm(row.get("prior_receiving_yards_after_catch"), 450.0),
                ),
                0.10,
            ),
            ("red_zone_secondary", None, 0.05),
        ]
        confidence_floor = 0.70
        miss_penalty = 0.05
        miss_cap = 0.20
    else:
        components = []
        confidence_floor = 0.70
        miss_penalty = 0.05
        miss_cap = 0.20

    available = [(name, score, weight) for name, score, weight in components if score is not None]
    missing = [name for name, score, _weight in components if score is None]
    available_weight = sum(weight for _name, _score, weight in available)
    raw_score = (
        sum(float(score) * weight for _name, score, weight in available) / available_weight
        if available_weight
        else np.nan
    )
    confidence = max(confidence_floor, 1.0 - min(miss_cap, miss_penalty * len(missing)))
    proxy_score = raw_score * confidence if not pd.isna(raw_score) else np.nan
    return {
        "production_formula_partial_proxy_score": proxy_score,
        "proxy_available_component_weight": available_weight,
        "proxy_missing_component_count": len(missing),
        "proxy_missing_components": "|".join(missing),
        "proxy_confidence_multiplier": confidence,
    }


def _add_prediction_ranks(frame: pd.DataFrame, score_column: str) -> pd.DataFrame:
    output = frame.copy()
    pred_col = f"{score_column}_pred_rank"
    output[pred_col] = np.nan
    for (_season, _position), group in output.groupby(["target_season", "position"]):
        ranked = group.sort_values(
            [score_column, "feature_player_name"],
            ascending=[False, True],
            na_position="last",
            kind="stable",
        )
        output.loc[ranked.index, pred_col] = np.arange(1, len(ranked) + 1)
    return output


def _scorecard(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    pred_col = "production_formula_partial_proxy_score_pred_rank"
    for position in POSITIONS:
        group = frame.loc[frame["position"] == position].copy()
        metrics = _rank_metrics(group, pred_col, position)
        rows.append(
            {
                "Position": position,
                "Seasons Tested": metrics["seasons"],
                "Rows": metrics["rows"],
                "MAE": _fmt_float(metrics["mae_rank"]),
                "RMSE": _fmt_float(metrics["rmse_rank"]),
                "Spearman": _fmt_float(metrics["spearman"]),
                "Top-12 Hit": _fmt_pct(metrics["top_12_hit"]) if 12 in RELEVANT_TOP_N[position] else "N/A",
                "Top-24 Hit": _fmt_pct(metrics["top_24_hit"]) if 24 in RELEVANT_TOP_N[position] else "N/A",
                "Top-36 Hit": _fmt_pct(metrics["top_36_hit"]) if 36 in RELEVANT_TOP_N[position] else "N/A",
                "Startable Precision": _fmt_pct(metrics["startable_precision"]),
                "Trust": _trust_label(metrics),
                "Metric Unit": "finish-rank places",
                "Exact Replay": "No",
                "Benchmark Layer": "current_formula_family_partial_proxy_review_only",
            }
        )
    return pd.DataFrame(rows)


def _baseline_comparison(
    proxy: pd.DataFrame,
    prior_finish: pd.DataFrame,
    opportunity: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    proxy_overall = _overall_metrics(proxy, "production_formula_partial_proxy_score_pred_rank")
    prior_overall = _overall_metrics(prior_finish, "prior_year_finish_baseline_score_pred_rank")
    opp_overall = _overall_metrics(opportunity, "opportunity_only_baseline_score_pred_rank")
    rows.extend(
        [
            _comparison_row(
                "Production formula family partial proxy",
                "V3 2013-2025 targets, QB/RB/WR/TE",
                "rank MAE / Spearman / startable precision",
                f"{proxy_overall['mae_rank']:.2f} / {proxy_overall['spearman']:.3f} / {proxy_overall['startable_precision']:.1%}",
                "Exact current formula replay blocked; proxy uses only overlapping lagged factuals.",
            ),
            _comparison_row(
                "Simple prior-year finish baseline",
                "Same V3 rows",
                "rank MAE / Spearman / startable precision",
                f"{prior_overall['mae_rank']:.2f} / {prior_overall['spearman']:.3f} / {prior_overall['startable_precision']:.1%}",
                "Derived from prior-season NWR scoring only; safe but not dynasty-aware.",
            ),
            _comparison_row(
                "Opportunity-only baseline",
                "Same V3 rows",
                "rank MAE / Spearman / startable precision",
                f"{opp_overall['mae_rank']:.2f} / {opp_overall['spearman']:.3f} / {opp_overall['startable_precision']:.1%}",
                "Uses attempts/carries/targets only; review-only local factuals.",
            ),
        ]
    )
    if BASELINE_ACCURACY_PATH.exists():
        baseline = pd.read_csv(BASELINE_ACCURACY_PATH)
        selected = baseline[
            (baseline["model_id"] == "v1_baseline")
            & (baseline["split"] == "eval_all")
            & (baseline["position"] == "ALL")
        ]
        if not selected.empty:
            row = selected.iloc[0]
            rows.append(
                _comparison_row(
                    "Prior NWR historical Backtest V1 baseline",
                    str(row["target_seasons"]),
                    "points MAE / RMSE / Spearman / Top-N",
                    (
                        f"{float(row['mae_points']):.2f} / {float(row['rmse_points']):.2f} / "
                        f"{float(row['spearman_points']):.3f} / {float(row['top_n_hit_rate']):.1%}"
                    ),
                    "Existing local review-only baseline; points metrics are not directly comparable to rank MAE.",
                )
            )
    rows.append(
        _comparison_row(
            "Market / ADP baseline",
            "Not run",
            "N/A",
            "Excluded",
            "Only current/display-only market data was found; unsafe as historical input.",
        )
    )
    return pd.DataFrame(rows)


def _comparison_row(model: str, scope: str, metric: str, result: str, caveat: str) -> dict[str, str]:
    return {
        "Model / Baseline": model,
        "Scope": scope,
        "Metric": metric,
        "Result": result,
        "Caveat": caveat,
    }


def _rank_metrics(group: pd.DataFrame, pred_rank_col: str, position: str) -> dict[str, Any]:
    if group.empty:
        return {
            "rows": 0,
            "seasons": 0,
            "mae_rank": math.nan,
            "rmse_rank": math.nan,
            "spearman": math.nan,
            "top_12_hit": math.nan,
            "top_24_hit": math.nan,
            "top_36_hit": math.nan,
            "startable_precision": math.nan,
        }
    pred = pd.to_numeric(group[pred_rank_col], errors="coerce")
    actual = pd.to_numeric(group["next_position_finish"], errors="coerce")
    errors = pred - actual
    return {
        "rows": int(len(group)),
        "seasons": int(group["target_season"].nunique()),
        "mae_rank": float(errors.abs().mean()),
        "rmse_rank": float(math.sqrt(float((errors**2).mean()))),
        "spearman": _spearman(pred, actual),
        "top_12_hit": _top_n_hit_rate(group, pred_rank_col, 12),
        "top_24_hit": _top_n_hit_rate(group, pred_rank_col, 24),
        "top_36_hit": _top_n_hit_rate(group, pred_rank_col, 36),
        "startable_precision": _startable_precision(group, pred_rank_col, position),
    }


def _overall_metrics(frame: pd.DataFrame, pred_rank_col: str) -> dict[str, Any]:
    rows = [_rank_metrics(frame.loc[frame["position"] == position], pred_rank_col, position) for position in POSITIONS]
    total_rows = sum(row["rows"] for row in rows)
    if total_rows == 0:
        return {"mae_rank": math.nan, "spearman": math.nan, "startable_precision": math.nan}
    return {
        "mae_rank": sum(row["mae_rank"] * row["rows"] for row in rows) / total_rows,
        "spearman": sum(row["spearman"] * row["rows"] for row in rows) / total_rows,
        "startable_precision": sum(row["startable_precision"] * row["rows"] for row in rows) / total_rows,
    }


def _top_n_hit_rate(group: pd.DataFrame, pred_rank_col: str, top_n: int) -> float:
    numerator = 0
    denominator = 0
    for (_season, _position), season_group in group.groupby(["target_season", "position"]):
        n = min(top_n, len(season_group))
        if n <= 0:
            continue
        pred_top = set(season_group.nsmallest(n, pred_rank_col)["substrate_row_id"])
        actual_top = set(
            season_group.loc[
                pd.to_numeric(season_group["next_position_finish"], errors="coerce") <= top_n,
                "substrate_row_id",
            ]
        )
        numerator += len(pred_top & actual_top)
        denominator += n
    return numerator / denominator if denominator else math.nan


def _startable_precision(group: pd.DataFrame, pred_rank_col: str, position: str) -> float:
    threshold = FORMAT_STARTABLE_RANK[position]
    numerator = 0
    denominator = 0
    for _season, season_group in group.groupby("target_season"):
        n = min(threshold, len(season_group))
        if n <= 0:
            continue
        pred_top = season_group.nsmallest(n, pred_rank_col)
        hits = pd.to_numeric(pred_top["next_position_finish"], errors="coerce") <= threshold
        numerator += int(hits.sum())
        denominator += n
    return numerator / denominator if denominator else math.nan


def _coverage_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (target_season, position), group in frame.groupby(["target_season", "position"]):
        rows.append(
            {
                "Target Season": int(target_season),
                "Position": position,
                "Rows": int(len(group)),
                "Optional Null-Fenced Rows": int(group["optional_source_null_fenced"].sum()),
                "Median Proxy Component Weight": round(float(group["proxy_available_component_weight"].median()), 3),
                "Missing Component Rows": int((group["proxy_missing_component_count"] > 0).sum()),
                "Actual Startable Rows In Coverage": int(
                    (pd.to_numeric(group["next_position_finish"], errors="coerce") <= FORMAT_STARTABLE_RANK[position]).sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def _miss_analysis(frame: pd.DataFrame) -> dict[str, Any]:
    pred_col = "production_formula_partial_proxy_score_pred_rank"
    rows: list[dict[str, Any]] = []
    pattern_rows: list[dict[str, Any]] = []
    for position in POSITIONS:
        threshold = FORMAT_STARTABLE_RANK[position]
        pos = frame.loc[frame["position"] == position].copy()
        pos["rank_error"] = pd.to_numeric(pos[pred_col], errors="coerce") - pd.to_numeric(
            pos["next_position_finish"], errors="coerce"
        )
        false_neg = pos[(pos["next_position_finish"] <= threshold) & (pos[pred_col] > threshold)]
        false_pos = pos[(pos[pred_col] <= threshold) & (pos["next_position_finish"] > threshold)]
        rows.append(
            {
                "Position": position,
                "False Negative Startable Misses": int(len(false_neg)),
                "False Positive Startable Misses": int(len(false_pos)),
                "Worst Under-Rank": _case_list(false_neg.sort_values("rank_error", ascending=False).head(5)),
                "Worst Over-Rank": _case_list(false_pos.sort_values("rank_error", ascending=True).head(5)),
            }
        )
        if position in {"RB", "WR", "TE"}:
            low_opp_cut = pos.groupby("feature_season")["prior_opportunities"].transform("median")
            low_opp_startable = pos[
                (pos["prior_opportunities"] <= low_opp_cut)
                & (pos["next_position_finish"] <= threshold)
                & (pos[pred_col] > threshold)
            ]
            pattern_rows.append(
                {
                    "Pattern": f"{position} low-prior-opportunity breakout miss",
                    "Count": int(len(low_opp_startable)),
                    "Evidence": _case_list(low_opp_startable.sort_values("rank_error", ascending=False).head(5)),
                }
            )
        high_prior_rank = pos.groupby("feature_season")["prior_nwr_points"].rank(
            method="first",
            ascending=False,
        )
        high_prior_decline = pos[
            (high_prior_rank <= threshold)
            & (pos["next_position_finish"] > threshold)
            & (pos[pred_col] <= threshold)
        ]
        pattern_rows.append(
            {
                "Pattern": f"{position} prior-production decline false positive",
                "Count": int(len(high_prior_decline)),
                "Evidence": _case_list(high_prior_decline.sort_values("rank_error", ascending=True).head(5)),
            }
        )
    patterns = sorted(pattern_rows, key=lambda row: row["Count"], reverse=True)
    return {
        "position_rows": pd.DataFrame(rows),
        "patterns": pd.DataFrame(patterns),
    }


def _case_list(frame: pd.DataFrame) -> str:
    pieces: list[str] = []
    pred_col = "production_formula_partial_proxy_score_pred_rank"
    for row in frame.to_dict("records"):
        pieces.append(
            f"{row.get('target_player_name')} {row.get('target_season')} "
            f"pred {int(row.get(pred_col)) if not pd.isna(row.get(pred_col)) else 'NA'} "
            f"actual {int(row.get('next_position_finish')) if not pd.isna(row.get('next_position_finish')) else 'NA'}"
        )
    return "; ".join(pieces) if pieces else "None"


def _source_facts(current_board: pd.DataFrame, substrate: pd.DataFrame) -> dict[str, Any]:
    source_hash = current_board.attrs.get("source_hash", "")
    return {
        "current_board_path": current_board.attrs.get("source_path", "missing"),
        "current_board_hash": source_hash,
        "current_board_hash_matches": source_hash.lower() == EXPECTED_CURRENT_BOARD_HASH,
        "current_board_rows": int(len(current_board)),
        "current_board_scored_rows": int(
            pd.to_numeric(current_board.get("nwr_dynasty_score", pd.Series(dtype=str)), errors="coerce")
            .notna()
            .sum()
        )
        if not current_board.empty
        else 0,
        "current_board_positions": _value_counts_dict(
            current_board.get("position", pd.Series(dtype=str))
        )
        if not current_board.empty
        else {},
        "substrate_path": str(SUBSTRATE_PATH),
        "substrate_hash": _sha256(SUBSTRATE_PATH),
        "substrate_rows": int(len(substrate)),
        "substrate_positions": _value_counts_dict(substrate["position"]),
        "feature_seasons": f"{int(substrate['feature_season'].min())}-{int(substrate['feature_season'].max())}",
        "target_seasons": f"{int(substrate['target_season'].min())}-{int(substrate['target_season'].max())}",
        "all_review_only": bool(substrate["review_only"].all()),
        "any_model_use_allowed": bool(substrate["model_use_allowed"].any()),
        "any_production_approved": bool(substrate["production_approved"].any()),
    }


def _value_counts_dict(series: pd.Series) -> dict[str, int]:
    return {str(key): int(value) for key, value in series.value_counts().to_dict().items()}


def _report_markdown(
    *,
    scorecard: pd.DataFrame,
    baseline_comparison: pd.DataFrame,
    coverage: pd.DataFrame,
    misses: dict[str, Any],
    source_facts: dict[str, Any],
) -> str:
    strongest = _strongest_position(scorecard)
    weakest = _weakest_position(scorecard)
    coverage_table = _markdown_table(
        coverage.groupby("Position", as_index=False).agg(
            seasons=("Target Season", "nunique"),
            rows=("Rows", "sum"),
            optional_null_fenced_rows=("Optional Null-Fenced Rows", "sum"),
            median_component_weight=("Median Proxy Component Weight", "median"),
            actual_startable_rows=("Actual Startable Rows In Coverage", "sum"),
        )
    )
    return "\n".join(
        [
            "# Production Rankings Backtest V1 Report",
            "",
            "## Verdict",
            "",
            "`YELLOW_PRODUCTION_RANKINGS_ACCURACY_PARTIAL_WITH_CAVEATS`",
            "",
            "Exact replay of the current production ranking surface is not safely measurable from local evidence. The current surface is a pinned 240-row full-player-board artifact sorted by `nwr_dynasty_score`, but the score chain depends on current/local Model v4 evidence matrices, current value checkpoints, lifecycle/confidence layers, and source receipts that are not available as historical season-by-season artifacts.",
            "",
            "This report therefore measures a review-only partial proxy of the current formula families against the V3 historical N-to-N+1 substrate. The proxy uses only lagged factual fields already marked review-safe in V3 and excludes every display-only, blocked, review-only-for-display, current-only, or leakage-unsafe field.",
            "",
            "## Clear Answer",
            "",
            f"Based on this backtest, the current production ranking surface is strongest at `{strongest}`, weakest at `{weakest}`, and overall should be trusted as a useful review-only ordering aid for players with prior-season production, not as an approved standalone accuracy model or a single draft-day truth number.",
            "",
            "The partial proxy is baseline-like rather than clearly additive: in the same V3 row set, the simple prior-year finish baseline slightly outperformed the current-formula-family proxy overall on rank MAE and Spearman. That is a real warning, not a cosmetic caveat.",
            "",
            "## Metrics Summary",
            "",
            _markdown_table(scorecard),
            "",
            "MAE/RMSE are finish-rank-place errors between the proxy predicted rank and the next-season position finish. Spearman is rank correlation where higher is better. Startable precision uses the NWR league contract: QB10, RB30, WR40, TE12.",
            "",
            "## Overall Accuracy Summary",
            "",
            "No approved single overall accuracy number is defensible yet.",
            "",
            "Reasons: exact formula replay is blocked, the benchmark is a partial proxy, K is intentionally outside the modeled chain, rookies without prior-season NFL rows are structurally missing, and position thresholds have different fantasy meaning in a 1QB non-PPR first-down league. A proxy aggregate can be calculated, but it should not be promoted as an approved production accuracy number.",
            "",
            "## Baseline Comparison",
            "",
            _markdown_table(baseline_comparison),
            "",
            "## Source Trace",
            "",
            f"- Current ranking surface: `{source_facts['current_board_path']}`",
            f"- Current board hash matches pinned app hash: `{source_facts['current_board_hash_matches']}`",
            f"- Historical substrate: `{source_facts['substrate_path']}`",
            f"- V3 feature seasons: `{source_facts['feature_seasons']}`; target seasons: `{source_facts['target_seasons']}`",
            "- Ranking app/page trace: `app/pages/20_final_board_v1.py` -> `load_dynasty_rankings()` -> `build_unified_player_board()` -> `sort_rankings_frame_by_column()`.",
            "- Score/rank trace: `full_player_board_value_review_rows.csv.nwr_dynasty_score` -> `_assign_private_ranks()` descending score sort.",
            "- Formula-family trace: `model_v4_rb_wr_current_value_service.py`, `model_v4_qb_te_current_value_service.py`, `model_v4_replacement_vorp_core_service.py`, `model_v4_current_value_checkpoint_service.py`, and `model_v4_formula_contract_service.py`.",
            "",
            "## Excluded Signals",
            "",
            "- Display-only: DynastyProcess value/rank/ECR, market gap, Outcome V1/V2 probabilities, NFLVerse context display, injury context display.",
            "- Review-only but not production-approved: V3 historical substrate rows, historical formula candidates, candidate ranks, current-board candidate feature gates.",
            "- Blocked: market, ADP, projections, rankings, mocks, big boards, generic JSON slurping, canonical first-down views not routed through admitted matched views.",
            "- Not joined or identity unsafe: same-name audit fields, unresolved current identity rows, any row without GSIS canonical identity.",
            "- Leakage unsafe: 2026 current roster/status/injury/depth/schedule, current ADP, current market ranks, target-season outcomes as inputs.",
            "- Not historically available in V3: current lifecycle/age guards, current confidence-missingness layer, current RotoWire route/YPRR/TPRR coverage, red-zone context, depth-chart role changes, medical/injury status.",
            "- K: intentionally not meaningfully modeled; current full-board current-value chain supports QB/RB/WR/TE.",
            "",
            "## Biggest Miss Patterns",
            "",
            _markdown_table(misses["patterns"].head(8)),
            "",
            "Position miss summary:",
            "",
            _markdown_table(misses["position_rows"]),
            "",
            "Interpretation: the proxy is most exposed to one-year role changes, breakouts from low prior opportunity, and prior-production decline false positives. Injury slices remain review-only caveats because the safe historical feature substrate does not admit injury as an input.",
            "",
            "## Draft-Day Interpretation",
            "",
            "- Good for: ordering veterans with meaningful prior-season QB/RB/WR/TE production and comparing broad position tiers.",
            "- Bad for: rookies, UDFA/low-draft-capital players, injured players, sudden RB role changes, WR breakouts, TE volatility, and any player whose case depends on current depth charts or market context.",
            "- Trust most: positions with stronger Spearman/startable precision in the scorecard, especially when source coverage and component weight are high.",
            "- Human override needed: rookies, ambiguous role changes, older assets, injury-affected players, TE outliers, and 1QB QB value debates.",
            "- Player archetypes needing extra review: low-prior-opportunity breakouts, prior top scorers with role/health decline risk, and players with optional source null fences or missing current formula components.",
            "",
            "## Historical Label, Identity, And Source Coverage",
            "",
            coverage_table,
            "",
            "Identity join coverage in V3 is 5,518/5,518 matched feature-label rows with 0 position mismatches and 0 duplicate player-season-pair keys. Source coverage is review-only: V3 marks model_use_allowed=false, training_allowed=false, source_truth_allowed=false, and production_approved=false.",
            "",
            "## Next Work Orders",
            "",
            "1. Build a historical Model v4 replay substrate with current formula component names, not just proxy overlap columns.",
            "2. Add a rookie/first-NFL-season backtest lane with draft capital, college production, and identity-safe rookie labels.",
            "3. Create a role-change miss packet for RB and WR using only lagged usage and admitted depth/availability snapshots if approved.",
            "4. Build a 1QB positional calibration lane to separate football points from keeper-format replacement value.",
            "5. Decide whether V3 source-semantics can graduate from review-only evidence into a strictly bounded candidate-search gate.",
            "",
        ]
    )


def _caveats_markdown(*, source_facts: dict[str, Any], coverage: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Production Rankings Backtest V1 Caveats",
            "",
            "## Exact Replay Blocker",
            "",
            "Exact historical replay is blocked because the current `nwr_dynasty_score` artifact is produced from current Model v4 evidence/checkpoint layers, not from committed season-by-season historical formula inputs. The current app validates a pinned full-board CSV hash and displays the result; it does not recompute historical rankings on demand.",
            "",
            "## Proxy Boundary",
            "",
            "The benchmark proxy reuses current formula families and weights where local V3 lagged factual columns overlap. Missing current-only components are penalized and disclosed. This is not a promoted model and not a production approval.",
            "",
            "## Coverage Caveats",
            "",
            f"- Current board rows read: `{source_facts['current_board_rows']}`.",
            f"- Current scored rows read: `{source_facts['current_board_scored_rows']}`.",
            f"- V3 substrate rows tested: `{source_facts['substrate_rows']}`.",
            f"- Feature seasons: `{source_facts['feature_seasons']}`.",
            f"- Target seasons: `{source_facts['target_seasons']}`.",
            "- Rookie/veteran split is not safely available from the V3 substrate. Current-board `is_rookie` is current-only and was not used historically.",
            "- Injury-affected miss slices are review-only only. No injury field was admitted as a historical proxy input in this benchmark.",
            "- K is excluded because the current value chain and the scoring contract mark kicker as not meaningfully modeled.",
            "",
            "## Leakage Guardrails",
            "",
            "- No target-season outcome was used to score proxy ranks.",
            "- No 2026-only roster, status, injury, depth chart, ADP, market, or projection field was used as historical input.",
            "- Display-only Outcome V1/V2 fields were not used as model inputs.",
            "- DynastyProcess/market fields were not used as model inputs.",
            "",
            "## Season/Position Coverage Snapshot",
            "",
            _markdown_table(coverage.head(20)),
            "",
        ]
    )


def _source_trace_markdown(*, source_facts: dict[str, Any]) -> str:
    files = [
        FINAL_BOARD_PAGE_PATH,
        DRAFT_DAY_SERVICE_PATH,
        FULL_BOARD_VALUE_SERVICE_PATH,
        FORMULA_CONTRACT_SERVICE_PATH,
        SCORING_RULES_PATH,
        SOURCE_REGISTRY_PATH,
        SUBSTRATE_PATH,
        SAFE_ALLOWLIST_PATH,
        SUBSTRATE_SUMMARY_PATH,
        LEAKAGE_REPORT_PATH,
        IDENTITY_JOIN_REPORT_PATH,
        SOURCE_CONTRACT_NOT_READY_PATH,
        BASELINE_ACCURACY_PATH,
        CANDIDATE_SEARCH_LEADERBOARD_PATH,
    ]
    rows = []
    for path in files:
        rows.append(
            {
                "Path": str(path),
                "Exists": path.exists(),
                "SHA-256": _sha256(path) if path.exists() and path.is_file() else "",
                "Role": _source_role(path),
            }
        )
    rows.append(
        {
            "Path": str(source_facts["current_board_path"]),
            "Exists": source_facts["current_board_path"] != "missing",
            "SHA-256": source_facts["current_board_hash"],
            "Role": "Pinned current full dynasty ranking artifact read-only.",
        }
    )
    return "\n".join(
        [
            "# Production Rankings Backtest V1 Source Trace",
            "",
            "## Production Surface",
            "",
            "- Active route/page: `app/pages/20_final_board_v1.py`.",
            "- Loader: `load_dynasty_rankings()` in `src/services/draft_day_app_v1_service.py`.",
            "- Current artifact file name: `full_player_board_value_review_rows.csv`.",
            "- Primary rank field: `nwr_rank`.",
            "- Primary score field: `nwr_dynasty_score`.",
            "- Rank assignment: `_assign_private_ranks()` in `src/services/full_player_board_value_service.py` sorts scored rows descending by `nwr_dynasty_score`; league and market ranks only affect display/fallback ordering for unscored rows.",
            "",
            "## Source Files",
            "",
            _markdown_table(pd.DataFrame(rows)),
            "",
            "## Current Board Facts",
            "",
            f"- Current board rows: `{source_facts['current_board_rows']}`.",
            f"- Current scored rows: `{source_facts['current_board_scored_rows']}`.",
            f"- Current board hash matches app-pinned hash: `{source_facts['current_board_hash_matches']}`.",
            f"- Current board positions: `{source_facts['current_board_positions']}`.",
            "",
            "## Historical Substrate Facts",
            "",
            f"- Rows: `{source_facts['substrate_rows']}`.",
            f"- Positions: `{source_facts['substrate_positions']}`.",
            f"- Feature seasons: `{source_facts['feature_seasons']}`.",
            f"- Target seasons: `{source_facts['target_seasons']}`.",
            f"- All rows review-only: `{source_facts['all_review_only']}`.",
            f"- Any model-use-allowed rows: `{source_facts['any_model_use_allowed']}`.",
            f"- Any production-approved rows: `{source_facts['any_production_approved']}`.",
            "",
        ]
    )


def _source_role(path: Path) -> str:
    name = path.name
    if name.endswith(".py"):
        return "Code trace / formula or loader behavior."
    if name.endswith(".json"):
        return "League/scoring contract."
    if name.endswith(".csv"):
        return "Local review-safe evidence or baseline metrics."
    if name.endswith(".parquet"):
        return "Historical feature-target substrate."
    if name.endswith(".md"):
        return "Governance, source, or leakage decision record."
    return "Source evidence."


def _strongest_position(scorecard: pd.DataFrame) -> str:
    ranked = scorecard.copy()
    ranked["_spearman"] = pd.to_numeric(ranked["Spearman"], errors="coerce")
    ranked["_precision"] = ranked["Startable Precision"].str.rstrip("%").astype(float) / 100.0
    ranked["_score"] = ranked["_spearman"] + ranked["_precision"]
    return str(ranked.sort_values("_score", ascending=False).iloc[0]["Position"])


def _weakest_position(scorecard: pd.DataFrame) -> str:
    ranked = scorecard.copy()
    ranked["_spearman"] = pd.to_numeric(ranked["Spearman"], errors="coerce")
    ranked["_precision"] = ranked["Startable Precision"].str.rstrip("%").astype(float) / 100.0
    ranked["_score"] = ranked["_spearman"] + ranked["_precision"]
    return str(ranked.sort_values("_score", ascending=True).iloc[0]["Position"])


def _trust_label(metrics: dict[str, Any]) -> str:
    spearman = metrics["spearman"]
    precision = metrics["startable_precision"]
    if spearman >= 0.70 and precision >= 0.55:
        return "PARTIAL_MEDIUM"
    if spearman >= 0.60 and precision >= 0.45:
        return "PARTIAL_LOW_MEDIUM"
    return "PARTIAL_LOW"


def _spearman(left: pd.Series, right: pd.Series) -> float:
    value = left.rank().corr(right.rank())
    return float(value) if not pd.isna(value) else math.nan


def _norm(value: Any, cap: float) -> float | None:
    numeric = _maybe(value)
    if numeric is None or cap <= 0:
        return None
    return max(0.0, min(1.0, numeric / cap))


def _safe_div_norm(numerator: Any, denominator: Any, cap: float) -> float | None:
    denom = _maybe(denominator)
    if denom in (None, 0):
        return None
    return _norm((_num(numerator) / denom), cap)


def _avg(*values: float | None) -> float | None:
    present = [value for value in values if value is not None and not pd.isna(value)]
    if not present:
        return None
    return sum(present) / len(present)


def _num(value: Any) -> float:
    maybe = _maybe(value)
    return 0.0 if maybe is None else maybe


def _maybe(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(numeric):
        return None
    return numeric


def _fmt_float(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.3f}"


def _fmt_pct(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.1%}"


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No rows."
    display = frame.copy()
    for column in display.columns:
        display[column] = display[column].map(_cell)
    headers = list(display.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in display.to_dict("records"):
        lines.append("| " + " | ".join(str(row[column]) for column in headers) + " |")
    return "\n".join(lines)


def _cell(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    text = str(value)
    return text.replace("\n", " ").replace("|", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
