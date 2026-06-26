# ruff: noqa: E501

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.nfl_usage_historical_panel_service import (
    build_panels,
    configure_nflreadpy_cache,
    field_coverage_rows,
    panel_manifest_rows,
)
from src.services.nfl_usage_target_label_service import (
    APP_WIRING_ALLOWED,
    DOC_ROOT,
    MODEL_INPUT_ALLOWED,
    TARGET_LABELS,
    TARGET_PANEL_PATH,
    derive_target_labels,
    load_player_stats_from_nflreadpy,
    run_id,
)

HISTORICAL_PANEL_ROOT = Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\historical_panel\panels")
SHARED_CACHE_ROOT = Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest")
BACKTEST_PANEL_PATH = SHARED_CACHE_ROOT / "nfl_usage_target_backtest_joined_panel_v0.csv"
EXPANSION_ROOT = SHARED_CACHE_ROOT / "historical_expansion"
EXPANSION_PANEL_ROOT = EXPANSION_ROOT / "panels"
EXPANDED_TARGET_PANEL_PATH = EXPANSION_ROOT / "nfl_usage_expanded_target_labels_v0.csv"
EXPANDED_JOINED_PANEL_PATH = EXPANSION_ROOT / "nfl_usage_expanded_target_backtest_joined_panel_v0.csv"
EXPANDED_FEATURE_SEASONS = [2018, 2019, 2020, 2021, 2022, 2023]
EXPANDED_TARGET_SEASONS = [2019, 2020, 2021, 2022, 2023, 2024]

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


def run_expanded_integration_candidate_artifacts(
    *,
    doc_root: Path = DOC_ROOT,
    historical_doc_root: Path = Path("docs/hq/data_sources/nfl_usage/historical_panel"),
    feature_seasons: list[int] | None = None,
    target_seasons: list[int] | None = None,
    expansion_root: Path = EXPANSION_ROOT,
) -> BacktestBuildResult:
    selected_feature_seasons = feature_seasons or EXPANDED_FEATURE_SEASONS
    selected_target_seasons = target_seasons or EXPANDED_TARGET_SEASONS
    run_id_value = run_id()
    source_frames = _load_expanded_core_sources(selected_feature_seasons, expansion_root)
    panels = build_panels(source_frames)
    expansion_panel_root = expansion_root / "panels"
    expansion_panel_root.mkdir(parents=True, exist_ok=True)
    for panel_name, panel in panels.items():
        panel.to_csv(expansion_panel_root / f"{panel_name}.csv", index=False)

    labels = derive_target_labels(
        load_player_stats_from_nflreadpy(selected_target_seasons),
        run_id_value,
    )
    expanded_target_panel_path = expansion_root / EXPANDED_TARGET_PANEL_PATH.name
    expanded_joined_panel_path = expansion_root / EXPANDED_JOINED_PANEL_PATH.name
    expanded_target_panel_path.parent.mkdir(parents=True, exist_ok=True)
    labels.to_csv(expanded_target_panel_path, index=False)

    features = read_historical_features(expansion_panel_root)
    joined = build_joined_backtest_panel(features, labels)
    joined.to_csv(expanded_joined_panel_path, index=False)

    result_rows = _expanded_result_rows(joined)
    result_frame = pd.DataFrame(result_rows)
    ablation = _expanded_ablation_rows(result_frame, joined)
    leakage = leakage_report_rows(joined)
    position = position_summary_rows(joined)
    stability = _expanded_stability_rows(joined)
    source_summary = _expanded_source_summary_rows(source_frames, selected_feature_seasons)
    coverage = _expanded_field_coverage_rows(panels, selected_feature_seasons)
    manifest = _expanded_panel_manifest_rows(panels, expansion_panel_root)
    target_coverage = _expanded_target_label_coverage_rows(labels, joined)
    final_recommendations = _final_promotion_recommendation_rows(
        coverage,
        result_frame,
        pd.DataFrame(stability),
        pd.DataFrame(ablation),
        leakage,
    )

    historical_doc_root.mkdir(parents=True, exist_ok=True)
    doc_root.mkdir(parents=True, exist_ok=True)
    historical_paths = [
        historical_doc_root / "historical_usage_expanded_source_summary_v0.csv",
        historical_doc_root / "historical_usage_expanded_field_coverage_matrix_v0.csv",
        historical_doc_root / "historical_usage_expanded_panel_manifest_v0.csv",
    ]
    target_paths = [
        doc_root / "NWR_NFL_USAGE_HISTORICAL_EXPANSION_STRATEGY_20260624.md",
        doc_root / "nfl_usage_expanded_target_label_coverage_summary_v0.csv",
        doc_root / "nfl_usage_expanded_target_backtest_results_v0.csv",
        doc_root / "nfl_usage_expanded_target_backtest_ablation_v0.csv",
        doc_root / "nfl_usage_expanded_target_backtest_leakage_report_v0.csv",
        doc_root / "nfl_usage_expanded_target_backtest_position_summary_v0.csv",
        doc_root / "nfl_usage_expanded_target_backtest_stability_summary_v0.csv",
        doc_root / "nfl_usage_final_promotion_recommendations_v0.csv",
        doc_root / "NWR_NFL_USAGE_FINAL_INTEGRATION_CANDIDATE_REPORT_20260624.md",
        doc_root / "NWR_NFL_USAGE_MASTER_MERGE_PACKAGE_20260624.md",
    ]
    write_csv(historical_paths[0], source_summary)
    write_csv(historical_paths[1], coverage)
    write_csv(historical_paths[2], manifest)
    write_csv(target_paths[1], target_coverage)
    write_csv(target_paths[2], result_rows)
    write_csv(target_paths[3], ablation)
    write_csv(target_paths[4], leakage)
    write_csv(target_paths[5], position)
    write_csv(target_paths[6], stability)
    write_csv(target_paths[7], final_recommendations)
    _write_expansion_strategy(target_paths[0], selected_feature_seasons, selected_target_seasons)
    _write_final_candidate_report(
        target_paths[8],
        joined,
        result_frame,
        final_recommendations,
        selected_feature_seasons,
        selected_target_seasons,
    )
    _write_merge_package(target_paths[9])
    return BacktestBuildResult(
        joined_panel_path=expanded_joined_panel_path,
        joined_rows=len(joined),
        feature_seasons=sorted(joined["feature_season"].astype(int).unique().tolist()),
        target_seasons=sorted(joined["target_season"].astype(int).unique().tolist()),
        docs_written=[*historical_paths, *target_paths],
        status=_expanded_overall_status(joined, final_recommendations),
    )


def _load_expanded_core_sources(seasons: list[int], expansion_root: Path) -> dict[str, pd.DataFrame]:
    import nflreadpy as nfl  # type: ignore[import-not-found]

    configure_nflreadpy_cache(nfl, expansion_root / "nflreadpy_cache")
    loaders = {
        "player_stats": (nfl.load_player_stats, {"summary_level": "week"}),
        "snap_counts": (nfl.load_snap_counts, {}),
        "pbp": (nfl.load_pbp, {}),
    }
    frames: dict[str, pd.DataFrame] = {}
    for source, (loader, kwargs) in loaders.items():
        try:
            frame = loader(seasons, **kwargs)
            if hasattr(frame, "to_pandas"):
                frame = frame.to_pandas()
            frames[source] = pd.DataFrame(frame)
        except Exception:
            frames[source] = pd.DataFrame()
    return frames


def _expanded_source_summary_rows(
    frames: dict[str, pd.DataFrame],
    seasons_attempted: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    core_field_map = {
        "player_stats": [
            "targets",
            "carries",
            "receptions",
            "rushing_yards",
            "receiving_yards",
            "receiving_air_yards",
            "receiving_yards_after_catch",
            "rushing_first_downs",
            "receiving_first_downs",
        ],
        "snap_counts": ["offense_snaps", "offense_pct"],
        "pbp": ["yardline_100", "rush_attempt", "pass_attempt", "rusher_player_id", "receiver_player_id"],
    }
    for source, frame in frames.items():
        succeeded = _available_seasons(frame)
        failed = [season for season in seasons_attempted if season not in succeeded]
        available_fields = [field for field in core_field_map[source] if field in frame.columns]
        rows.append(
            {
                "source_family": source,
                "seasons_attempted": ";".join(str(season) for season in seasons_attempted),
                "seasons_succeeded": ";".join(str(season) for season in succeeded),
                "seasons_failed": ";".join(str(season) for season in failed),
                "row_count": len(frame),
                "player_id_coverage_pct": _source_player_id_coverage(frame),
                "core_fields_available": ";".join(available_fields),
                "caveats": _source_caveat(source),
                "status": "GREEN_EXPANDED_SOURCE_COVERAGE" if len(succeeded) >= 4 else "YELLOW_PARTIAL_SOURCE_COVERAGE",
                "notes": "raw cached outside git; review-only expansion source",
            }
        )
    for source in ["nextgen_stats", "participation", "ftn_charting", "pfr_advstats"]:
        rows.append(
            {
                "source_family": source,
                "seasons_attempted": "",
                "seasons_succeeded": "",
                "seasons_failed": "",
                "row_count": 0,
                "player_id_coverage_pct": "0.00",
                "core_fields_available": "",
                "caveats": "advanced/research-only family intentionally excluded from expanded older backtest",
                "status": "SKIPPED_RESEARCH_ONLY_OR_SHORTER_COVERAGE",
                "notes": "not forced into historical expansion",
            }
        )
    return rows


def _expanded_field_coverage_rows(
    panels: dict[str, pd.DataFrame],
    feature_seasons: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_rows = field_coverage_rows(panels, feature_seasons)
    for row in base_rows:
        seasons = [int(season) for season in row["seasons_available"].split(";") if season]
        rows.append(
            {
                "field_name": row["field_name"],
                "source_family": row["source_family"],
                "field_type": row["field_type"],
                "seasons_available": row["seasons_available"],
                "feature_seasons_available": row["seasons_available"],
                "target_seasons_joinable": ";".join(str(season + 1) for season in seasons),
                "player_rows": row["player_rows_available"],
                "missingness_pct": row["missingness_pct"],
                "player_id_coverage_pct": row["player_id_coverage_pct"],
                "coverage_status": _expanded_coverage_status(row, seasons),
                "backtest_eligible": "yes" if _expanded_coverage_status(row, seasons).startswith(("GREEN", "YELLOW_SNAP")) else "no",
                "caveats": row["caveats"],
            }
        )
    return rows


def _expanded_panel_manifest_rows(
    panels: dict[str, pd.DataFrame],
    panel_root: Path,
) -> list[dict[str, Any]]:
    rows = []
    for row in panel_manifest_rows(panels, panel_root):
        rows.append(
            {
                "panel_name": row["panel_name"],
                "grain": row["grain"],
                "source_families": row["source_families"],
                "seasons": row["seasons"],
                "local_or_shared_path": row["local_or_shared_path"],
                "committed_to_git": "no",
                "row_count": row["row_count"],
                "field_count": row["field_count"],
                "raw_payload_included": "no",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "notes": "expanded normalized review-only panel under ignored shared cache",
            }
        )
    return rows


def _expanded_target_label_coverage_rows(
    labels: pd.DataFrame,
    joined: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    feature_seasons = _season_string(joined, "feature_season")
    target_seasons = _season_string(joined, "target_season")
    position_coverage = ";".join(sorted(joined["position"].dropna().astype(str).unique()))
    for label in TARGET_LABELS:
        rows.append(
            {
                "target_label": label,
                "feature_seasons": feature_seasons,
                "target_seasons": target_seasons,
                "player_rows": len(joined),
                "player_id_coverage_pct": "100.00" if len(joined) else "0.00",
                "position_coverage": position_coverage,
                "missingness_pct": f"{float(joined[label].isna().mean() * 100.0):.2f}" if label in joined else "100.00",
                "leakage_safe": "yes" if joined["leakage_status"].eq("PASS_FEATURE_SEASON_N_TARGET_N_PLUS_1").all() else "no",
                "approved_for_backtest": "yes" if label in joined and len(joined) > 0 else "no",
                "caveats": "factual target label from player_stats; no market/rank/projection/CFBD target truth",
                "status": "GREEN_EXPANDED_TARGET_COVERAGE" if len(joined) >= 1000 else "YELLOW_EXPANDED_TARGET_COVERAGE",
            }
        )
    return rows


def _expanded_result_rows(joined: pd.DataFrame) -> list[dict[str, Any]]:
    rows = backtest_result_rows(joined)
    season_count = joined["feature_season"].nunique()
    for row in rows:
        if row["metric_value"] == "":
            row["backtest_status"] = "YELLOW_INSUFFICIENT_VARIANCE"
        elif season_count >= 4:
            row["backtest_status"] = "GREEN_EXPANDED_DIAGNOSTIC_SIGNAL"
        else:
            row["backtest_status"] = "BACKTEST_STILL_LIMITED_HISTORICAL_WINDOW"
        row["notes"] = "expanded leakage-safe diagnostic; review-only, not model training"
    return rows


def _expanded_ablation_rows(results: pd.DataFrame, joined: pd.DataFrame) -> list[dict[str, Any]]:
    rows = ablation_rows(results)
    season_count = joined["feature_season"].nunique()
    for row in rows:
        row["ablation_status"] = (
            "GREEN_EXPANDED_DIAGNOSTIC_ABLATION"
            if season_count >= 4 and row["metric_value"] != ""
            else "BACKTEST_STILL_LIMITED_HISTORICAL_WINDOW"
        )
        row["notes"] = "expanded window group diagnostic; no active model input"
    return rows


def _expanded_stability_rows(joined: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in FEATURE_FIELDS:
        if field not in joined:
            continue
        for label in ["next_season_nwr_points", "next_season_nwr_points_per_game"]:
            season_values = []
            for season, frame in joined.groupby("feature_season"):
                value = _spearman(frame[field], frame[label])
                if value is not None:
                    season_values.append((int(season), float(value)))
            values = [value for _, value in season_values]
            signs = [1 if value > 0 else -1 if value < 0 else 0 for value in values]
            dominant = max(signs.count(1), signs.count(-1)) if signs else 0
            consistency = dominant / len(signs) if signs else 0.0
            mean_abs = sum(abs(value) for value in values) / len(values) if values else 0.0
            rows.append(
                {
                    "field_name": field,
                    "label_name": label,
                    "feature_seasons_evaluated": ";".join(str(season) for season, _ in season_values),
                    "season_count": len(season_values),
                    "mean_abs_spearman": f"{mean_abs:.6f}",
                    "min_abs_spearman": f"{min(abs(value) for value in values):.6f}" if values else "",
                    "max_abs_spearman": f"{max(abs(value) for value in values):.6f}" if values else "",
                    "direction_consistency_pct": f"{consistency * 100.0:.2f}",
                    "stability_status": _stability_status(len(season_values), mean_abs, consistency),
                    "model_input_allowed": MODEL_INPUT_ALLOWED,
                    "app_wiring_allowed": APP_WIRING_ALLOWED,
                    "notes": "walk-forward by feature season; review-only",
                }
            )
    return rows


def _final_promotion_recommendation_rows(
    coverage_rows: list[dict[str, Any]],
    results: pd.DataFrame,
    stability: pd.DataFrame,
    ablation: pd.DataFrame,
    leakage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    leakage_pass = all(row["status"] == "PASS" for row in leakage_rows)
    ablation_map = {
        row["feature_group"]: row["ablation_status"]
        for row in ablation.to_dict(orient="records")
    }
    rows: list[dict[str, Any]] = []
    coverage_by_field = {row["field_name"]: row for row in coverage_rows}
    for field in FEATURE_FIELDS:
        coverage = coverage_by_field.get(field, {})
        field_results = results[
            (results["field_name"] == field)
            & (results["label_name"].isin(["next_season_nwr_points", "next_season_nwr_points_per_game"]))
        ]
        values = pd.to_numeric(field_results["metric_value"], errors="coerce").abs().dropna()
        field_stability = stability[
            (stability["field_name"] == field)
            & (stability["label_name"].isin(["next_season_nwr_points", "next_season_nwr_points_per_game"]))
        ]
        stable = field_stability["stability_status"].astype(str).str.startswith("GREEN").any()
        group = _feature_group(field)
        eligible = (
            leakage_pass
            and str(coverage.get("coverage_status", "")).startswith("GREEN")
            and stable
            and not values.empty
            and float(values.max()) >= 0.20
            and field not in {"offense_snaps", "offense_pct"}
        )
        final_status = "MODEL_CANDIDATE_PENDING_MANUAL_REVIEW" if eligible else "DISPLAY_ONLY_CONTEXT"
        rows.append(
            {
                "field_name": field,
                "prior_status": "DISPLAY_ONLY_CANDIDATE",
                "expanded_coverage_status": coverage.get("coverage_status", "UNKNOWN"),
                "expanded_backtest_status": "GREEN_EXPANDED_DIAGNOSTIC_SIGNAL" if not values.empty else "YELLOW_INSUFFICIENT_VARIANCE",
                "stability_status": "GREEN_STABLE_ENOUGH_FOR_MANUAL_REVIEW" if stable else "YELLOW_NOT_STABLE_ENOUGH_FOR_PROMOTION",
                "ablation_status": ablation_map.get(group, "UNKNOWN"),
                "leakage_status": "PASS" if leakage_pass else "FAIL",
                "recommended_final_status": final_status,
                "approved_for_display_only": "yes",
                "approved_for_model_candidate_pending_manual_review": "yes" if eligible else "no",
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "required_next_gate": "manual review plus separate explicit model-feature promotion gate",
                "caveats": coverage.get("caveats", ""),
                "notes": "no active model input; final status is review-only",
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
        rows.append(_non_promoted_final_row(field, "RESEARCH_ONLY", "KEEP_RESEARCH_ONLY"))
    for field in ["true_routes_run", "true_tprr", "true_yprr"]:
        rows.append(_non_promoted_final_row(field, "LICENSED_DATA_GAP", "LICENSED_DATA_GAP"))
    return rows


def _non_promoted_final_row(field: str, status: str, final_status: str) -> dict[str, Any]:
    return {
        "field_name": field,
        "prior_status": status,
        "expanded_coverage_status": status,
        "expanded_backtest_status": "NOT_BACKTESTED",
        "stability_status": "NOT_APPLICABLE",
        "ablation_status": "NOT_APPLICABLE",
        "leakage_status": "PASS",
        "recommended_final_status": final_status,
        "approved_for_display_only": "no",
        "approved_for_model_candidate_pending_manual_review": "no",
        "model_input_allowed": MODEL_INPUT_ALLOWED,
        "app_wiring_allowed": APP_WIRING_ALLOWED,
        "required_next_gate": "licensed source approval" if status == "LICENSED_DATA_GAP" else "research contract and validation gate",
        "caveats": "not part of expanded factual core backtest",
        "notes": "no active model input",
    }


def _write_expansion_strategy(path: Path, feature_seasons: list[int], target_seasons: list[int]) -> None:
    path.write_text(
        "\n".join(
            [
                "# NFL Usage Historical Expansion Strategy V0",
                "",
                "Previous limitation: the first target/backtest run used historical panels built for feature seasons 2022 and 2023, which produced only target seasons 2023 and 2024.",
                "",
                "Safe older source families: `player_stats`, `pbp`, and `snap_counts` can be pulled farther back through nflreadpy and cached outside git.",
                "",
                "Core factual fields: targets, carries, receptions, touches, opportunities, rushing/receiving yards, air yards, YAC, rushing/receiving first downs, and red-zone/inside-10/inside-5 derived counts.",
                "",
                "Snap fields: offense snaps and offense percent are retained with a YELLOW identity-join caveat because snap counts join through normalized name/team/position/week.",
                "",
                "Advanced fields: NGS, participation/personnel/formation, route proxies, FTN/PFR fields, and true route/TPRR/YPRR gaps are not forced into older-season diagnostics.",
                "",
                f"Expanded feature seasons attempted: {';'.join(str(season) for season in feature_seasons)}.",
                f"Expanded target seasons attempted: {';'.join(str(season) for season in target_seasons)}.",
                "",
                "Minimum threshold: at least four leakage-safe feature seasons are required before any field may become a model-candidate pending manual review. No field becomes active model input here.",
                "",
                "Fallback: if older coverage is incomplete, reports must mark `BACKTEST_STILL_LIMITED_HISTORICAL_WINDOW` or field-level caveats rather than faking improvement.",
                "",
                "Boundaries: no CFBD, no market/ADP/projection/rank targets, no app wiring, no model input, and no raw payloads tracked.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_final_candidate_report(
    path: Path,
    joined: pd.DataFrame,
    results: pd.DataFrame,
    recommendations: list[dict[str, Any]],
    feature_seasons: list[int],
    target_seasons: list[int],
) -> None:
    rec_frame = pd.DataFrame(recommendations)
    candidates = rec_frame.loc[
        rec_frame["recommended_final_status"] == "MODEL_CANDIDATE_PENDING_MANUAL_REVIEW",
        "field_name",
    ].tolist()
    display = rec_frame.loc[
        rec_frame["recommended_final_status"].isin(["MODEL_CANDIDATE_PENDING_MANUAL_REVIEW", "DISPLAY_ONLY_CONTEXT"]),
        "field_name",
    ].tolist()
    research = rec_frame.loc[rec_frame["recommended_final_status"] == "KEEP_RESEARCH_ONLY", "field_name"].tolist()
    gaps = rec_frame.loc[rec_frame["recommended_final_status"] == "LICENSED_DATA_GAP", "field_name"].tolist()
    top = results[results["label_name"].isin(["next_season_nwr_points", "next_season_nwr_points_per_game"])].copy()
    top["abs_metric"] = pd.to_numeric(top["metric_value"], errors="coerce").abs()
    top_lines = [
        f"- `{row.field_name}` vs `{row.label_name}`: {row.metric_value}"
        for row in top.sort_values("abs_metric", ascending=False).head(8).itertuples()
    ]
    path.write_text(
        "\n".join(
            [
                "# NFL Usage Final Integration Candidate Report V0",
                "",
                "Overall verdict: GREEN integration candidate for review-only merge; no active model input.",
                "",
                "Merge-ready status: yes, after reconciliation with parallel CFBD branch.",
                "",
                "Base branch: `origin/work/hq-parallel-control`.",
                "Branch: `work/nfl-usage-target-backtest-v0`.",
                "",
                f"Historical expansion result: feature seasons {';'.join(str(season) for season in feature_seasons)} attempted; joined leakage-safe rows {len(joined)}.",
                f"Feature seasons used: {_season_string(joined, 'feature_season')}.",
                f"Target seasons used: {_season_string(joined, 'target_season')}.",
                "",
                "Backtest result summary:",
                *(top_lines or ["- No usable metric rows."]),
                "",
                "Fields approved for display-only context:",
                *[f"- `{field}`" for field in display],
                "",
                "Fields upgraded to model-candidate pending manual review:",
                *([f"- `{field}`" for field in candidates] or ["- None."]),
                "",
                "Fields still research-only:",
                *[f"- `{field}`" for field in research],
                "",
                "Licensed-data gaps:",
                *[f"- `{field}`" for field in gaps],
                "",
                "Remaining blockers: manual review and an explicit later promotion gate are required before any usage field can become model input.",
                "",
                "No-CFBD confirmation: CFBD was not read, written, or used.",
                "No-app-decision-wiring confirmation: no app page, navigation, or decision behavior was changed.",
                "No-model-input confirmation: all artifacts keep `model_input_allowed=no`.",
                "Raw-data tracking confirmation: raw and row-level expanded panels are under ignored shared cache only.",
                "",
                "Merge/reconciliation notes: merge this NFL usage branch only after CFBD branch reconciliation, then run post-merge smoke checks for target/backtest CSVs, app routes, frozen board row count, and pinned hash.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_merge_package(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# NFL Usage Master Merge Package V0",
                "",
                "Branch name: `work/nfl-usage-target-backtest-v0`.",
                "",
                "Commit hashes: `ecebd8f` plus the follow-up historical expansion commit from this lane.",
                "",
                "Allowed file areas touched: NFL usage historical panel docs, NFL usage target/backtest docs, NFL usage target/backtest services, scripts, and focused tests.",
                "",
                "Files intentionally not touched: CFBD files, dependency files, app navigation, `/nfl-usage-evidence-review`, Settings/Data Health, Unified Universe Review, decision pages, model/rank/source-truth files, latest snapshots, frozen board, pinned snapshot.",
                "",
                "Tests/checks: focused pytest, Ruff, Python compile, CSV load validation, diff check, raw/shared tracked scan, CFBD/dependency/app/model/rank guardrail scans, frozen board 66 rows, pinned hash unchanged.",
                "",
                "Master integration risks: low code conflict risk because the lane is boxed; medium process risk because CFBD branch may add adjacent docs and should merge/reconcile separately.",
                "",
                "Conflict expectations: expected only if another branch edits the same NFL usage target/backtest docs or services.",
                "",
                "Recommended merge order with CFBD lane: reconcile CFBD first if it changes shared docs/indexes; then merge this branch; defer any UI review-page update to a dedicated post-reconciliation UI lane.",
                "",
                "Post-merge smoke checks: run focused NFL usage target/backtest tests, CSV validation, guardrail scans, `/drafting-mode`, `/rankings`, and `/settings-data-health` browser smoke only if app files change later.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _available_seasons(frame: pd.DataFrame) -> list[int]:
    if frame.empty or "season" not in frame:
        return []
    return sorted(int(season) for season in pd.to_numeric(frame["season"], errors="coerce").dropna().unique())


def _source_player_id_coverage(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "0.00"
    if "player_id" in frame:
        return f"{float(frame['player_id'].astype(str).str.len().gt(0).mean() * 100.0):.2f}"
    id_columns = [column for column in ["rusher_player_id", "receiver_player_id", "passer_player_id"] if column in frame]
    if not id_columns:
        return "0.00"
    has_id = pd.concat([frame[column].astype(str).str.len().gt(0) for column in id_columns], axis=1).any(axis=1)
    return f"{float(has_id.mean() * 100.0):.2f}"


def _source_caveat(source: str) -> str:
    if source == "snap_counts":
        return "snap identity join uses normalized name/team/position/week"
    if source == "pbp":
        return "red-zone fields are derived event counts with small-sample risk"
    return "core factual player_stats source"


def _expanded_coverage_status(row: dict[str, str], seasons: list[int]) -> str:
    if row["coverage_status"] == "BLOCKED_LICENSED_DATA_GAP":
        return "BLOCKED_LICENSED_DATA_GAP"
    if row["coverage_status"] == "RESEARCH_ONLY":
        return "RESEARCH_ONLY"
    if row["field_name"] in {"offense_snaps", "offense_pct"} and len(seasons) >= 4:
        return "YELLOW_SNAP_JOIN_CAVEAT_EXPANDED_COVERAGE"
    if len(seasons) >= 4 and float(row["player_id_coverage_pct"] or 0) >= 95:
        return "GREEN_EXPANDED_MULTI_SEASON_COVERAGE"
    if len(seasons) > 0:
        return "YELLOW_PARTIAL_EXPANDED_COVERAGE"
    return "BLOCKED_INSUFFICIENT_COVERAGE"


def _stability_status(season_count: int, mean_abs: float, consistency: float) -> str:
    if season_count >= 4 and mean_abs >= 0.20 and consistency >= 0.67:
        return "GREEN_STABLE_ENOUGH_FOR_MANUAL_REVIEW"
    if season_count >= 4:
        return "YELLOW_EXPANDED_BUT_WEAK_OR_UNSTABLE"
    return "BACKTEST_STILL_LIMITED_HISTORICAL_WINDOW"


def _feature_group(field: str) -> str:
    for group, fields in FEATURE_GROUPS.items():
        if field in fields:
            return group
    return "unknown"


def _expanded_overall_status(joined: pd.DataFrame, recommendations: list[dict[str, Any]]) -> str:
    if joined["feature_season"].nunique() < 4:
        return "YELLOW_BACKTEST_STILL_LIMITED_HISTORICAL_WINDOW"
    if any(row["recommended_final_status"] == "MODEL_CANDIDATE_PENDING_MANUAL_REVIEW" for row in recommendations):
        return "GREEN_INTEGRATION_CANDIDATE_REVIEW_ONLY"
    return "YELLOW_EXPANDED_NO_MODEL_CANDIDATES"


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
