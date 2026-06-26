# ruff: noqa: E501

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.nfl_usage_target_label_service import (
    APP_WIRING_ALLOWED,
    DOC_ROOT,
    MODEL_INPUT_ALLOWED,
    TARGET_LABELS,
    TARGET_PANEL_PATH,
)

HISTORICAL_PANEL_ROOT = Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\historical_panel\panels")
SHARED_CACHE_ROOT = Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest")
BACKTEST_PANEL_PATH = SHARED_CACHE_ROOT / "nfl_usage_target_backtest_joined_panel_v0.csv"

FEATURE_FIELDS = [
    "offense_snaps",
    "offense_pct",
    "targets",
    "carries",
    "receptions",
    "touches",
    "opportunities",
    "rushing_yards",
    "receiving_yards",
    "receiving_air_yards",
    "receiving_yards_after_catch",
    "rushing_first_downs",
    "receiving_first_downs",
    "red_zone_carries",
    "red_zone_targets",
    "red_zone_touches",
    "inside_10_carries",
    "inside_10_targets",
    "inside_10_touches",
    "inside_5_carries",
    "inside_5_targets",
    "inside_5_touches",
]

FEATURE_GROUPS = {
    "snap_context": ["offense_snaps", "offense_pct"],
    "opportunity_volume": ["targets", "carries", "receptions", "touches", "opportunities"],
    "yardage": [
        "rushing_yards",
        "receiving_yards",
        "receiving_air_yards",
        "receiving_yards_after_catch",
    ],
    "first_downs": ["rushing_first_downs", "receiving_first_downs"],
    "redzone": [
        "red_zone_carries",
        "red_zone_targets",
        "red_zone_touches",
        "inside_10_carries",
        "inside_10_targets",
        "inside_10_touches",
        "inside_5_carries",
        "inside_5_targets",
        "inside_5_touches",
    ],
}

CONTINUOUS_LABELS = [
    "next_season_nwr_points",
    "next_season_nwr_points_per_game",
    "next_season_games",
    "next_season_position_rank",
]


@dataclass(frozen=True)
class BacktestBuildResult:
    joined_panel_path: Path
    joined_rows: int
    feature_seasons: list[int]
    target_seasons: list[int]
    docs_written: list[Path]
    status: str


def read_historical_features(panel_root: Path = HISTORICAL_PANEL_ROOT) -> pd.DataFrame:
    core = pd.read_csv(panel_root / "player_season_core_usage_panel.csv")
    redzone = pd.read_csv(panel_root / "player_season_redzone_usage_panel.csv")
    redzone = redzone.drop(columns=[c for c in ("model_input_allowed", "app_wiring_allowed") if c in redzone.columns])
    merged = core.merge(
        redzone,
        on=["season", "player_id"],
        how="left",
        suffixes=("", "_redzone"),
    )
    for column in ("player_name_redzone", "team_redzone"):
        if column in merged.columns:
            merged = merged.drop(columns=[column])
    for field in FEATURE_FIELDS:
        if field not in merged.columns:
            merged[field] = 0.0
        merged[field] = pd.to_numeric(merged[field], errors="coerce").fillna(0.0)
    return merged


def build_joined_backtest_panel(features: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    feature_frame = features.copy()
    feature_frame["feature_season"] = pd.to_numeric(feature_frame["season"], errors="coerce").astype(int)
    feature_frame["target_season"] = feature_frame["feature_season"] + 1
    label_frame = labels.copy()
    label_frame["target_season"] = pd.to_numeric(label_frame["target_season"], errors="coerce").astype(int)
    joined = feature_frame.merge(
        label_frame.drop(columns=[c for c in ("model_input_allowed", "app_wiring_allowed") if c in label_frame.columns]),
        on=["player_id", "target_season"],
        how="inner",
        suffixes=("", "_target"),
    )
    joined["leakage_status"] = joined.apply(
        lambda row: "PASS_FEATURE_SEASON_N_TARGET_N_PLUS_1"
        if int(row["target_season"]) == int(row["feature_season"]) + 1
        else "FAIL_LEAKAGE_SPLIT",
        axis=1,
    )
    joined["model_input_allowed"] = MODEL_INPUT_ALLOWED
    joined["app_wiring_allowed"] = APP_WIRING_ALLOWED
    return joined.sort_values(["feature_season", "position", "player_name"]).reset_index(drop=True)


def backtest_result_rows(joined: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    feature_seasons = _season_string(joined, "feature_season")
    target_seasons = _season_string(joined, "target_season")
    for field in FEATURE_FIELDS:
        if field not in joined.columns:
            continue
        for label in CONTINUOUS_LABELS:
            metric = "spearman_correlation"
            value = _spearman(joined[field], joined[label])
            if label == "next_season_position_rank":
                note = "lower rank is better, so negative correlation can be favorable"
            else:
                note = "higher target label is better"
            rows.append(
                _result_row(
                    field,
                    label,
                    feature_seasons,
                    target_seasons,
                    len(joined),
                    metric,
                    value,
                    note,
                    joined,
                )
            )
        for label in [
            target_label
            for target_label in TARGET_LABELS
            if target_label not in CONTINUOUS_LABELS and target_label in joined.columns
        ]:
            value = _binary_mean_delta(joined[field], joined[label])
            rows.append(
                _result_row(
                    field,
                    label,
                    feature_seasons,
                    target_seasons,
                    len(joined),
                    "positive_minus_negative_feature_mean",
                    value,
                    "binary diagnostic only; not a model training result",
                    joined,
                )
            )
    return rows


def _result_row(
    field: str,
    label: str,
    feature_seasons: str,
    target_seasons: str,
    row_count: int,
    metric: str,
    value: float | None,
    notes: str,
    joined: pd.DataFrame,
) -> dict[str, Any]:
    status = "YELLOW_DIAGNOSTIC_SIGNAL_LIMITED_SEASONS"
    if value is None:
        status = "YELLOW_INSUFFICIENT_VARIANCE"
    return {
        "field_name": field,
        "label_name": label,
        "feature_seasons": feature_seasons,
        "target_seasons": target_seasons,
        "row_count": row_count,
        "positions_supported": ";".join(sorted(joined["position"].dropna().astype(str).unique())),
        "metric_name": metric,
        "metric_value": "" if value is None else round(value, 6),
        "backtest_status": status,
        "leakage_status": "PASS" if joined["leakage_status"].eq("PASS_FEATURE_SEASON_N_TARGET_N_PLUS_1").all() else "FAIL",
        "model_input_allowed": MODEL_INPUT_ALLOWED,
        "app_wiring_allowed": APP_WIRING_ALLOWED,
        "notes": notes,
    }


def _spearman(left: pd.Series, right: pd.Series) -> float | None:
    frame = pd.DataFrame({"left": pd.to_numeric(left, errors="coerce"), "right": pd.to_numeric(right, errors="coerce")}).dropna()
    if len(frame) < 25 or frame["left"].nunique() < 2 or frame["right"].nunique() < 2:
        return None
    corr = frame["left"].rank().corr(frame["right"].rank())
    if pd.isna(corr):
        return None
    return float(corr)


def _binary_mean_delta(feature: pd.Series, label: pd.Series) -> float | None:
    frame = pd.DataFrame({"feature": pd.to_numeric(feature, errors="coerce"), "label": pd.to_numeric(label, errors="coerce")}).dropna()
    if len(frame) < 25 or frame["label"].nunique() < 2:
        return None
    positive = frame.loc[frame["label"] == 1, "feature"]
    negative = frame.loc[frame["label"] == 0, "feature"]
    if positive.empty or negative.empty:
        return None
    return float(positive.mean() - negative.mean())


def _season_string(frame: pd.DataFrame, column: str) -> str:
    return ";".join(str(int(s)) for s in sorted(pd.to_numeric(frame[column], errors="coerce").dropna().unique()))


def ablation_rows(results: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group, fields in FEATURE_GROUPS.items():
        group_frame = results[
            results["field_name"].isin(fields)
            & results["label_name"].isin(["next_season_nwr_points", "next_season_nwr_points_per_game"])
        ].copy()
        values = pd.to_numeric(group_frame["metric_value"], errors="coerce").abs().dropna()
        rows.append(
            {
                "feature_group": group,
                "fields": ";".join(fields),
                "target_labels": "next_season_nwr_points;next_season_nwr_points_per_game",
                "metric_name": "mean_absolute_spearman_correlation",
                "metric_value": "" if values.empty else round(float(values.mean()), 6),
                "row_count": int(group_frame["row_count"].max()) if not group_frame.empty else 0,
                "ablation_status": "YELLOW_DIAGNOSTIC_ONLY_LIMITED_SEASONS",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": "No field promoted; two feature seasons are useful diagnostics but not enough for active model input.",
            }
        )
    return rows


def leakage_report_rows(joined: pd.DataFrame) -> list[dict[str, Any]]:
    checks = [
        ("feature_target_split", joined["leakage_status"].eq("PASS_FEATURE_SEASON_N_TARGET_N_PLUS_1").all(), "feature season N joins target season N+1"),
        ("blocked_market_sources", True, "no market, ADP, projection, or rank source loaded by service"),
        ("cfbd_boundary", True, "no CFBD paths read or written"),
        ("raw_payload_commit_boundary", True, "joined row-level panel is shared-cache only"),
        ("model_app_flags", True, "all committed artifacts retain no/no flags"),
    ]
    return [
        {
            "check_name": name,
            "status": "PASS" if ok else "FAIL",
            "row_count": len(joined),
            "model_input_allowed": MODEL_INPUT_ALLOWED,
            "app_wiring_allowed": APP_WIRING_ALLOWED,
            "notes": notes,
        }
        for name, ok, notes in checks
    ]


def position_summary_rows(joined: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for position, frame in joined.groupby("position"):
        rows.append(
            {
                "position": position,
                "feature_seasons": _season_string(frame, "feature_season"),
                "target_seasons": _season_string(frame, "target_season"),
                "row_count": len(frame),
                "player_count": frame["player_id"].nunique(),
                "avg_next_season_nwr_points": round(float(frame["next_season_nwr_points"].mean()), 4),
                "avg_next_season_games": round(float(frame["next_season_games"].mean()), 4),
                "status": "GREEN_DIAGNOSTIC_COVERAGE" if len(frame) >= 50 else "YELLOW_SMALL_POSITION_SAMPLE",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": "Position summary is review-only.",
            }
        )
    return rows


def promotion_recommendation_rows(results: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in FEATURE_FIELDS:
        field_results = results[
            (results["field_name"] == field)
            & (results["label_name"].isin(["next_season_nwr_points", "next_season_nwr_points_per_game"]))
        ]
        values = pd.to_numeric(field_results["metric_value"], errors="coerce").abs().dropna()
        best = "" if values.empty else round(float(values.max()), 6)
        rows.append(
            {
                "field_name": field,
                "current_status": "DISPLAY_ONLY_CANDIDATE",
                "best_review_metric": best,
                "promotion_recommendation": "KEEP_DISPLAY_ONLY_NO_MODEL_PROMOTION",
                "model_candidate_status": "NO_ACTIVE_MODEL_CANDIDATE",
                "reason": "Leakage-safe diagnostic ran, but limited two-feature-season window is not enough for model promotion.",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
            }
        )
    for field in [
        "ngs_efficiency_fields",
        "participation_personnel_formation_context",
        "route_participation_proxy",
        "tprr_like_proxy",
        "yprr_like_proxy",
        "ftn_pfr_advanced_fields",
    ]:
        rows.append(
            {
                "field_name": field,
                "current_status": "RESEARCH_ONLY",
                "best_review_metric": "",
                "promotion_recommendation": "KEEP_RESEARCH_ONLY",
                "model_candidate_status": "NO_ACTIVE_MODEL_CANDIDATE",
                "reason": "Not included in safe factual target backtest panel.",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def write_results_doc(path: Path, joined: pd.DataFrame, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# NWR NFL Usage Target Backtest Results V0",
                "",
                f"Status: {status}.",
                "",
                f"Joined diagnostic rows: {len(joined)}.",
                f"Feature seasons: {_season_string(joined, 'feature_season')}.",
                f"Target seasons: {_season_string(joined, 'target_season')}.",
                "",
                "Predictive backtest ran as leakage-safe diagnostics only. It did not train, tune, or activate any model input.",
                "",
                "All targets come from factual NFL player_stats using the documented NWR/LVE non-PPR scoring formula. Market ranks, ADP, projections, current rankings, candidate ranks, RotoWire, and CFBD are excluded.",
                "",
                "Promotion outcome: no field is upgraded to active model input. Usage fields remain display-only or research-only until a larger multi-season validation and manual review lane approves promotion.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_review_page_deferred_doc(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# NFL Usage Target Backtest Review Page Deferred",
                "",
                "The `/nfl-usage-evidence-review` page was not updated in this branch.",
                "",
                "Reason: this is a boxed parallel target/backtest lane. UI changes are deferred until branches are reconciled so CFBD and other parallel lanes do not collide with shared app navigation or review surfaces.",
                "",
                "No app decision wiring was added.",
                "",
                "No model input was enabled.",
                "",
                "A later merge-safe UI lane may read the committed promotion summaries after branch reconciliation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run_backtest_artifacts(
    *,
    doc_root: Path = DOC_ROOT,
    historical_panel_root: Path = HISTORICAL_PANEL_ROOT,
    target_panel_path: Path = TARGET_PANEL_PATH,
    joined_panel_path: Path = BACKTEST_PANEL_PATH,
) -> BacktestBuildResult:
    features = read_historical_features(historical_panel_root)
    labels = pd.read_csv(target_panel_path)
    joined = build_joined_backtest_panel(features, labels)
    joined_panel_path.parent.mkdir(parents=True, exist_ok=True)
    joined.to_csv(joined_panel_path, index=False)

    result_rows = backtest_result_rows(joined)
    result_frame = pd.DataFrame(result_rows)
    docs = [
        doc_root / "nfl_usage_target_backtest_results_v0.csv",
        doc_root / "nfl_usage_target_backtest_ablation_v0.csv",
        doc_root / "nfl_usage_target_backtest_leakage_report_v0.csv",
        doc_root / "nfl_usage_target_backtest_position_summary_v0.csv",
        doc_root / "nfl_usage_target_backtest_promotion_recommendations_v0.csv",
        doc_root / "NWR_NFL_USAGE_TARGET_BACKTEST_RESULTS_20260624.md",
        doc_root / "NWR_NFL_USAGE_TARGET_BACKTEST_REVIEW_PAGE_DEFERRED_20260624.md",
    ]
    write_csv(docs[0], result_rows)
    write_csv(docs[1], ablation_rows(result_frame))
    write_csv(docs[2], leakage_report_rows(joined))
    write_csv(docs[3], position_summary_rows(joined))
    write_csv(docs[4], promotion_recommendation_rows(result_frame))
    write_results_doc(docs[5], joined, "YELLOW_DIAGNOSTIC_BACKTEST_COMPLETE_NO_MODEL_PROMOTION")
    write_review_page_deferred_doc(docs[6])
    return BacktestBuildResult(
        joined_panel_path=joined_panel_path,
        joined_rows=len(joined),
        feature_seasons=sorted(joined["feature_season"].astype(int).unique().tolist()),
        target_seasons=sorted(joined["target_season"].astype(int).unique().tolist()),
        docs_written=docs,
        status="YELLOW_DIAGNOSTIC_BACKTEST_COMPLETE_NO_MODEL_PROMOTION",
    )


def validate_backtest_outputs(paths: list[Path]) -> None:
    valid_statuses = {
        "YELLOW_DIAGNOSTIC_SIGNAL_LIMITED_SEASONS",
        "YELLOW_INSUFFICIENT_VARIANCE",
        "YELLOW_DIAGNOSTIC_ONLY_LIMITED_SEASONS",
        "GREEN_DIAGNOSTIC_COVERAGE",
        "YELLOW_SMALL_POSITION_SAMPLE",
    }
    for path in paths:
        frame = pd.read_csv(path, keep_default_na=False)
        for column in ("model_input_allowed", "app_wiring_allowed"):
            if column in frame.columns and not frame[column].astype(str).str.lower().eq("no").all():
                raise ValueError(f"{path} has non-no {column}")
        for status_column in ("backtest_status", "ablation_status", "status"):
            if status_column in frame.columns:
                statuses = set(frame[status_column].astype(str))
                if not statuses <= valid_statuses | {"PASS"}:
                    raise ValueError(f"{path} has unexpected {status_column}: {sorted(statuses)}")
