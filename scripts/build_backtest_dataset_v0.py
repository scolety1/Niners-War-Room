from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\backtests")
DEFAULT_SEASONS = list(range(2018, 2026))
CORE_POSITIONS = ("QB", "RB", "WR", "TE")
BLOCKED_FEATURE_TOKENS = (
    "adp",
    "market",
    "ranking",
    "projection",
    "fantasy_points",
    "fantasy_points_ppr",
    "trade_calculator",
    "sleeper_adp",
)
YELLOW_CHALLENGER_TOKENS = (
    "epa",
    "cpoe",
    "wopr",
    "pacr",
    "racr",
    "share",
    "_exp",
    "expected",
    "_diff",
)
YELLOW_CHALLENGER_ALLOWED_EXACT = {"years_exp"}
IDENTITY_COLUMNS = [
    "player_id",
    "feature_season",
    "target_season",
    "player_name",
    "position",
    "recent_team",
]
BASELINE_NUMERIC_COLUMNS = [
    "feature_games",
    "feature_nwr_points",
    "feature_nwr_ppg",
    "completions",
    "attempts",
    "passing_yards",
    "passing_tds",
    "passing_interceptions",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
    "passing_2pt_conversions",
    "rushing_2pt_conversions",
    "receiving_2pt_conversions",
    "punt_return_yards",
    "kickoff_return_yards",
    "special_teams_tds",
    "punt_returns",
    "kickoff_returns",
    "fumbles_lost",
    "offense_snaps",
    "offense_pct",
]
EXPANDED_EXTRA_COLUMNS = [
    "age_at_season_end",
    "years_exp",
    "draft_round",
    "draft_pick",
    "draft_pick_log",
    "is_active_any_week",
    "active_weeks",
    "depth_chart_best_rank",
    "passing_air_yards",
    "receiving_air_yards",
    "passing_yards_after_catch",
    "receiving_yards_after_catch",
    "rushing_first_downs_per_carry",
    "receiving_first_downs_per_target",
    "receiving_first_downs_per_reception",
    "rushes_inside_20",
    "rushes_inside_10",
    "rushes_inside_5",
    "targets_inside_20",
    "targets_inside_10",
    "targets_inside_5",
    "goal_to_go_rushes",
    "goal_to_go_targets",
    "red_zone_tds",
    "red_zone_first_downs",
    "qb_carries",
    "qb_rushing_yards",
    "qb_rushing_tds",
    "qb_scrambles",
    "sacks_suffered",
    "sack_fumbles",
    "sack_yards_lost",
    "team_plays",
    "team_pass_rate",
    "team_run_rate",
    "team_offensive_tds",
]
LABEL_COLUMNS = [
    "player_id",
    "target_season",
    "target_player_name",
    "target_position",
    "target_team",
    "target_games",
    "next_nwr_points",
    "next_nwr_ppg",
    "qb_t12",
    "rb_t12",
    "rb_t24",
    "wr_t12",
    "wr_t24",
    "wr_t36",
    "te_t12",
]


class BacktestBuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class BacktestDatasetResult:
    output_dir: Path
    baseline_path: Path
    expanded_path: Path
    labels_path: Path
    manifest_path: Path
    seasons_used: list[int]
    target_seasons: list[int]
    row_count: int
    warnings: list[str]


def calculate_nwr_points(frame: pd.DataFrame) -> pd.Series:
    return (
        _num(frame, "passing_yards") / 30
        + _num(frame, "passing_tds") * 3
        - _num(frame, "passing_interceptions")
        + _num(frame, "rushing_yards") / 10
        + _num(frame, "receiving_yards") / 10
        + _num(frame, "rushing_tds") * 4
        + _num(frame, "receiving_tds") * 4
        + _num(frame, "rushing_first_downs") * 0.4
        + _num(frame, "receiving_first_downs") * 0.4
        + (_num(frame, "punt_return_yards") + _num(frame, "kickoff_return_yards")) / 30
        + _num(frame, "special_teams_tds") * 4
        + (
            _num(frame, "passing_2pt_conversions")
            + _num(frame, "rushing_2pt_conversions")
            + _num(frame, "receiving_2pt_conversions")
        )
        * 2
        - (
            _num(frame, "sack_fumbles_lost")
            + _num(frame, "rushing_fumbles_lost")
            + _num(frame, "receiving_fumbles_lost")
        )
    )


def build_backtest_dataset(
    *,
    seasons: list[int],
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    run_label: str | None = None,
    loader_module: Any | None = None,
    frames: dict[str, pd.DataFrame] | None = None,
) -> BacktestDatasetResult:
    if len(seasons) < 5:
        raise BacktestBuildError("at least five seasons are required for four-plus test seasons")
    if any(seasons[index] + 1 != seasons[index + 1] for index in range(len(seasons) - 1)):
        raise BacktestBuildError("seasons must be consecutive for Backtest V0")

    label = run_label or f"backtest_v0_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    output_dir = output_root / label
    output_dir.mkdir(parents=True, exist_ok=False)

    frames = frames or _load_frames(loader_module or _import_nflreadpy(), seasons)
    warnings = _source_warnings(frames)
    feature_seasons = seasons[:-1]

    season_stats = _prepare_season_stats(frames["season_stats"], feature_seasons)
    labels = _build_labels(frames["season_stats"], seasons[1:])
    baseline = _build_baseline_features(season_stats)
    expanded = _build_expanded_features(
        baseline=baseline,
        season_stats=season_stats,
        rosters=frames.get("rosters", pd.DataFrame()),
        weekly_rosters=frames.get("weekly_rosters", pd.DataFrame()),
        snap_counts=frames.get("snap_counts", pd.DataFrame()),
        depth_charts=frames.get("depth_charts", pd.DataFrame()),
        draft_picks=frames.get("draft_picks", pd.DataFrame()),
        opportunity_pass=frames.get("opportunity_pass", pd.DataFrame()),
        opportunity_rush=frames.get("opportunity_rush", pd.DataFrame()),
        team_stats=frames.get("team_stats", pd.DataFrame()),
    )

    keys = ["player_id", "target_season"]
    label_keys = labels[keys].drop_duplicates()
    baseline = baseline.merge(label_keys, on=keys, how="inner")
    expanded = expanded.merge(label_keys, on=keys, how="inner")
    labels = labels.merge(baseline[keys].drop_duplicates(), on=keys, how="inner")

    _validate_feature_columns(baseline.columns)
    _validate_feature_columns(expanded.columns)
    if len(labels["target_season"].unique()) < 4:
        raise BacktestBuildError("fewer than four target seasons assembled")

    baseline_path = output_dir / "feature_dataset_baseline.csv"
    expanded_path = output_dir / "feature_dataset_expanded.csv"
    labels_path = output_dir / "labels.csv"
    _write_csv(baseline_path, baseline)
    _write_csv(expanded_path, expanded)
    _write_csv(labels_path, labels)

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "run_label": label,
        "purpose": "local_only_backtest_v0_dataset",
        "approval_status": "backtest_only_not_model_approved",
        "seasons_used": seasons,
        "feature_seasons": feature_seasons,
        "target_seasons": sorted(int(season) for season in labels["target_season"].unique()),
        "positions": list(CORE_POSITIONS),
        "row_count": len(labels),
        "feature_sets": {
            "baseline": BASELINE_NUMERIC_COLUMNS,
            "expanded_extra": EXPANDED_EXTRA_COLUMNS,
        },
        "blocked_features_enforced": list(BLOCKED_FEATURE_TOKENS),
        "yellow_challenger_features_excluded": list(YELLOW_CHALLENGER_TOKENS),
        "forbidden_use": [
            "private_value",
            "rankings",
            "hidden_sort",
            "recommendations",
            "simulations",
            "final_draft_decisions",
            "deployment",
            "latest_approved",
        ],
        "files": {
            "feature_dataset_baseline.csv": _file_record(baseline_path),
            "feature_dataset_expanded.csv": _file_record(expanded_path),
            "labels.csv": _file_record(labels_path),
        },
        "warnings": warnings,
    }
    manifest_path = output_dir / "build_manifest.json"
    _write_json(manifest_path, manifest)
    return BacktestDatasetResult(
        output_dir=output_dir,
        baseline_path=baseline_path,
        expanded_path=expanded_path,
        labels_path=labels_path,
        manifest_path=manifest_path,
        seasons_used=seasons,
        target_seasons=manifest["target_seasons"],
        row_count=len(labels),
        warnings=warnings,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build local-only Backtest V0 feature and label datasets. Does not create "
            "Lane Exchange packages or approvals."
        )
    )
    parser.add_argument("--seasons", nargs="+", type=int, default=DEFAULT_SEASONS)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-label", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build_backtest_dataset(
            seasons=args.seasons,
            output_root=args.output_root,
            run_label=args.run_label,
        )
    except Exception as exc:
        print(f"Backtest V0 dataset build failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"output_dir={result.output_dir}")
    print(f"baseline={result.baseline_path}")
    print(f"expanded={result.expanded_path}")
    print(f"labels={result.labels_path}")
    print(f"manifest={result.manifest_path}")
    print(f"target_seasons={','.join(str(season) for season in result.target_seasons)}")
    print(f"rows={result.row_count}")
    for warning in result.warnings:
        print(f"warning={warning}")
    return 0


def _load_frames(nflreadpy: Any, seasons: list[int]) -> dict[str, pd.DataFrame]:
    feature_seasons = seasons[:-1]
    return {
        "season_stats": _to_pandas(nflreadpy.load_player_stats(seasons, summary_level="reg")),
        "rosters": _safe_load(lambda: nflreadpy.load_rosters(feature_seasons)),
        "weekly_rosters": _safe_load(lambda: nflreadpy.load_rosters_weekly(feature_seasons)),
        "snap_counts": _safe_load(lambda: nflreadpy.load_snap_counts(feature_seasons)),
        "depth_charts": _safe_load(lambda: nflreadpy.load_depth_charts(feature_seasons)),
        "draft_picks": _safe_load(lambda: nflreadpy.load_draft_picks(seasons)),
        "team_stats": _safe_load(
            lambda: nflreadpy.load_team_stats(feature_seasons, summary_level="reg")
        ),
        "opportunity_pass": _safe_load(
            lambda: nflreadpy.load_ff_opportunity(feature_seasons, stat_type="pbp_pass")
        ),
        "opportunity_rush": _safe_load(
            lambda: nflreadpy.load_ff_opportunity(feature_seasons, stat_type="pbp_rush")
        ),
    }


def _import_nflreadpy() -> Any:
    try:
        return importlib.import_module("nflreadpy")
    except ModuleNotFoundError as exc:
        raise BacktestBuildError(
            "nflreadpy is unavailable. Use the approved local-only nflverse runtime via "
            "PYTHONPATH, not repo dependencies."
        ) from exc


def _safe_load(loader: Any) -> pd.DataFrame:
    try:
        return _to_pandas(loader())
    except Exception:
        return pd.DataFrame()


def _to_pandas(frame: Any) -> pd.DataFrame:
    if isinstance(frame, pd.DataFrame):
        return frame.copy()
    if hasattr(frame, "to_dicts"):
        return pd.DataFrame(frame.to_dicts())
    if hasattr(frame, "to_pandas"):
        return frame.to_pandas()
    if isinstance(frame, list):
        return pd.DataFrame(frame)
    raise BacktestBuildError(f"unsupported frame type: {type(frame).__name__}")


def _prepare_season_stats(frame: pd.DataFrame, feature_seasons: list[int]) -> pd.DataFrame:
    data = frame.copy()
    data["season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    data = data[data["season"].isin(feature_seasons)]
    data = data[data["position"].isin(CORE_POSITIONS)].copy()
    data["feature_season"] = data["season"].astype(int)
    data["target_season"] = data["feature_season"] + 1
    data["feature_games"] = _num(data, "games")
    data["feature_nwr_points"] = calculate_nwr_points(data)
    data["feature_nwr_ppg"] = _safe_div(data["feature_nwr_points"], data["feature_games"])
    data["fumbles_lost"] = (
        _num(data, "sack_fumbles_lost")
        + _num(data, "rushing_fumbles_lost")
        + _num(data, "receiving_fumbles_lost")
    )
    return data


def _build_labels(frame: pd.DataFrame, target_seasons: list[int]) -> pd.DataFrame:
    labels = frame.copy()
    labels["season"] = pd.to_numeric(labels["season"], errors="coerce").astype("Int64")
    labels = labels[labels["season"].isin(target_seasons)]
    labels = labels[labels["position"].isin(CORE_POSITIONS)].copy()
    labels["target_season"] = labels["season"].astype(int)
    labels["target_games"] = _num(labels, "games")
    labels["next_nwr_points"] = calculate_nwr_points(labels)
    labels["next_nwr_ppg"] = _safe_div(labels["next_nwr_points"], labels["target_games"])
    labels["target_player_name"] = labels.get("player_display_name", labels.get("player_name", ""))
    labels["target_position"] = labels["position"]
    labels["target_team"] = labels.get("recent_team", labels.get("team", ""))
    labels = _add_finish_buckets(labels)
    return labels[LABEL_COLUMNS].copy()


def _build_baseline_features(season_stats: pd.DataFrame) -> pd.DataFrame:
    baseline = season_stats[IDENTITY_COLUMNS].copy()
    for column in BASELINE_NUMERIC_COLUMNS:
        baseline[column] = _num(season_stats, column)
    baseline["position"] = baseline["position"].astype(str)
    return baseline


def _build_expanded_features(
    *,
    baseline: pd.DataFrame,
    season_stats: pd.DataFrame,
    rosters: pd.DataFrame,
    weekly_rosters: pd.DataFrame,
    snap_counts: pd.DataFrame,
    depth_charts: pd.DataFrame,
    draft_picks: pd.DataFrame,
    opportunity_pass: pd.DataFrame,
    opportunity_rush: pd.DataFrame,
    team_stats: pd.DataFrame,
) -> pd.DataFrame:
    expanded = baseline.copy()
    expanded = _merge_on_keys(expanded, _roster_features(rosters), ["player_id", "feature_season"])
    expanded = _merge_on_keys(
        expanded, _weekly_roster_features(weekly_rosters), ["player_id", "feature_season"]
    )
    expanded = _merge_on_keys(
        expanded,
        _snap_features(snap_counts),
        ["player_name_norm", "position", "recent_team", "feature_season"],
    )
    expanded = _merge_on_keys(
        expanded, _depth_features(depth_charts), ["player_id", "feature_season"]
    )
    expanded = _merge_on_keys(expanded, _draft_features(draft_picks), ["player_id"])
    expanded = _merge_on_keys(
        expanded,
        _red_zone_features(opportunity_pass, opportunity_rush),
        ["player_id", "feature_season"],
    )
    expanded = _merge_on_keys(
        expanded,
        _team_environment_features(team_stats),
        ["recent_team", "feature_season"],
    )

    expanded["rushing_first_downs_per_carry"] = _safe_div(
        expanded["rushing_first_downs"], expanded["carries"]
    )
    expanded["receiving_first_downs_per_target"] = _safe_div(
        expanded["receiving_first_downs"], expanded["targets"]
    )
    expanded["receiving_first_downs_per_reception"] = _safe_div(
        expanded["receiving_first_downs"], expanded["receptions"]
    )
    for column in EXPANDED_EXTRA_COLUMNS:
        if column not in expanded:
            expanded[column] = 0.0
    expanded = expanded[IDENTITY_COLUMNS + BASELINE_NUMERIC_COLUMNS + EXPANDED_EXTRA_COLUMNS].copy()
    return expanded.fillna(0)


def _add_finish_buckets(labels: pd.DataFrame) -> pd.DataFrame:
    labels = labels.copy()
    for column in ("qb_t12", "rb_t12", "rb_t24", "wr_t12", "wr_t24", "wr_t36", "te_t12"):
        labels[column] = 0
    for (_season, position), group in labels.groupby(["target_season", "position"]):
        ranked = group.sort_values("next_nwr_points", ascending=False)
        thresholds = {
            "QB": [("qb_t12", 12)],
            "RB": [("rb_t12", 12), ("rb_t24", 24)],
            "WR": [("wr_t12", 12), ("wr_t24", 24), ("wr_t36", 36)],
            "TE": [("te_t12", 12)],
        }
        for column, top_n in thresholds.get(str(position), []):
            labels.loc[ranked.head(top_n).index, column] = 1
    return labels


def _roster_features(rosters: pd.DataFrame) -> pd.DataFrame:
    if rosters.empty or "gsis_id" not in rosters:
        return pd.DataFrame(
            columns=["player_id", "feature_season", "age_at_season_end", "years_exp"]
        )
    data = rosters.copy()
    data["player_id"] = data["gsis_id"].astype(str)
    data["feature_season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    data["years_exp"] = _num(data, "years_exp")
    data["age_at_season_end"] = _age_at_season_end(
        data.get("birth_date", ""), data["feature_season"]
    )
    return (
        data.sort_values(["player_id", "feature_season"])
        .groupby(["player_id", "feature_season"], as_index=False)
        .agg({"age_at_season_end": "max", "years_exp": "max"})
    )


def _weekly_roster_features(weekly_rosters: pd.DataFrame) -> pd.DataFrame:
    if weekly_rosters.empty or "gsis_id" not in weekly_rosters:
        return pd.DataFrame(
            columns=["player_id", "feature_season", "is_active_any_week", "active_weeks"]
        )
    data = weekly_rosters.copy()
    data["player_id"] = data["gsis_id"].astype(str)
    data["feature_season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    status = (
        data["status"].astype(str).str.upper()
        if "status" in data
        else pd.Series("", index=data.index)
    )
    data["is_active_row"] = status.isin({"ACT", "ACTIVE"}).astype(int)
    return (
        data.groupby(["player_id", "feature_season"], as_index=False)
        .agg(is_active_any_week=("is_active_row", "max"), active_weeks=("is_active_row", "sum"))
    )


def _snap_features(snap_counts: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "player_name_norm",
        "position",
        "recent_team",
        "feature_season",
        "offense_snaps",
        "offense_pct",
    ]
    if snap_counts.empty or "player" not in snap_counts:
        return pd.DataFrame(columns=columns)
    data = snap_counts.copy()
    data["player_name_norm"] = data["player"].map(_norm_name)
    data["recent_team"] = data.get("team", "")
    data["feature_season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    data["offense_snaps"] = _num(data, "offense_snaps")
    data["offense_pct_weighted"] = _num(data, "offense_pct") * data["offense_snaps"]
    grouped = data.groupby(
        ["player_name_norm", "position", "recent_team", "feature_season"],
        as_index=False,
    ).agg(
        offense_snaps=("offense_snaps", "sum"),
        offense_pct_weighted=("offense_pct_weighted", "sum"),
    )
    grouped["offense_pct"] = _safe_div(grouped["offense_pct_weighted"], grouped["offense_snaps"])
    return grouped[columns]


def _depth_features(depth_charts: pd.DataFrame) -> pd.DataFrame:
    columns = ["player_id", "feature_season", "depth_chart_best_rank"]
    if depth_charts.empty or "gsis_id" not in depth_charts:
        return pd.DataFrame(columns=columns)
    data = depth_charts.copy()
    data["player_id"] = data["gsis_id"].astype(str)
    data["feature_season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    rank_column = "pos_rank" if "pos_rank" in data else "depth_team" if "depth_team" in data else ""
    if not rank_column:
        return pd.DataFrame(columns=columns)
    data["depth_chart_best_rank"] = _num(data, rank_column)
    return data.groupby(["player_id", "feature_season"], as_index=False).agg(
        depth_chart_best_rank=("depth_chart_best_rank", "min")
    )


def _draft_features(draft_picks: pd.DataFrame) -> pd.DataFrame:
    columns = ["player_id", "draft_round", "draft_pick", "draft_pick_log"]
    if draft_picks.empty or "gsis_id" not in draft_picks:
        return pd.DataFrame(columns=columns)
    data = draft_picks.copy()
    data = data[data["gsis_id"].notna()].copy()
    data["player_id"] = data["gsis_id"].astype(str)
    data["draft_round"] = _num(data, "round")
    data["draft_pick"] = _num(data, "pick")
    data["draft_pick_log"] = data["draft_pick"].map(
        lambda value: math.log1p(value) if value > 0 else 0
    )
    return (
        data.sort_values(["player_id", "draft_pick"])
        .groupby("player_id", as_index=False)
        .first()[columns]
    )


def _red_zone_features(pass_rows: pd.DataFrame, rush_rows: pd.DataFrame) -> pd.DataFrame:
    pass_features = _pass_red_zone_features(pass_rows)
    rush_features = _rush_red_zone_features(rush_rows)
    if pass_features.empty:
        output = rush_features
        output["red_zone_tds"] = _num(output, "red_zone_tds_rush")
        output["red_zone_first_downs"] = _num(output, "red_zone_first_downs_rush")
        return output
    if rush_features.empty:
        output = pass_features
        output["red_zone_tds"] = _num(output, "red_zone_tds_pass")
        output["red_zone_first_downs"] = _num(output, "red_zone_first_downs_pass")
        return output
    features = pass_features.merge(rush_features, on=["player_id", "feature_season"], how="outer")
    features["red_zone_tds"] = _num(features, "red_zone_tds_pass") + _num(
        features, "red_zone_tds_rush"
    )
    features["red_zone_first_downs"] = _num(features, "red_zone_first_downs_pass") + _num(
        features, "red_zone_first_downs_rush"
    )
    return features.fillna(0)


def _pass_red_zone_features(pass_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "player_id",
        "feature_season",
        "targets_inside_20",
        "targets_inside_10",
        "targets_inside_5",
        "goal_to_go_targets",
        "red_zone_tds_pass",
        "red_zone_first_downs_pass",
    ]
    if pass_rows.empty or "receiver_player_id" not in pass_rows:
        return pd.DataFrame(columns=columns)
    data = pass_rows[pass_rows["receiver_player_id"].notna()].copy()
    data["player_id"] = data["receiver_player_id"].astype(str)
    data["feature_season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    yardline = _num(data, "yardline_100")
    data["targets_inside_20"] = (yardline <= 20).astype(int)
    data["targets_inside_10"] = (yardline <= 10).astype(int)
    data["targets_inside_5"] = (yardline <= 5).astype(int)
    data["goal_to_go_targets"] = _num(data, "goal_to_go").gt(0).astype(int)
    data["red_zone_tds_pass"] = (
        data["targets_inside_20"] * _num(data, "pass_touchdown")
    ).astype(float)
    data["red_zone_first_downs_pass"] = (
        data["targets_inside_20"] * _num(data, "first_down")
    ).astype(float)
    return data.groupby(["player_id", "feature_season"], as_index=False)[columns[2:]].sum()


def _rush_red_zone_features(rush_rows: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "player_id",
        "feature_season",
        "rushes_inside_20",
        "rushes_inside_10",
        "rushes_inside_5",
        "goal_to_go_rushes",
        "red_zone_tds_rush",
        "red_zone_first_downs_rush",
        "qb_carries",
        "qb_rushing_yards",
        "qb_rushing_tds",
        "qb_scrambles",
    ]
    if rush_rows.empty or "rusher_player_id" not in rush_rows:
        return pd.DataFrame(columns=columns)
    data = rush_rows[rush_rows["rusher_player_id"].notna()].copy()
    data["player_id"] = data["rusher_player_id"].astype(str)
    data["feature_season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    yardline = _num(data, "yardline_100")
    data["rushes_inside_20"] = (yardline <= 20).astype(int)
    data["rushes_inside_10"] = (yardline <= 10).astype(int)
    data["rushes_inside_5"] = (yardline <= 5).astype(int)
    data["goal_to_go_rushes"] = _num(data, "goal_to_go").gt(0).astype(int)
    data["red_zone_tds_rush"] = (
        data["rushes_inside_20"] * _num(data, "rush_touchdown")
    ).astype(float)
    data["red_zone_first_downs_rush"] = (
        data["rushes_inside_20"] * _num(data, "first_down")
    ).astype(float)
    is_qb = (
        data["position"].astype(str).eq("QB")
        if "position" in data
        else pd.Series(False, index=data.index)
    )
    data["qb_carries"] = is_qb.astype(int) * _num(data, "rush_attempt")
    data["qb_rushing_yards"] = is_qb.astype(int) * _num(data, "rushing_yards")
    data["qb_rushing_tds"] = is_qb.astype(int) * _num(data, "rush_touchdown")
    data["qb_scrambles"] = is_qb.astype(int) * _num(data, "qb_scramble")
    grouped = data.groupby(["player_id", "feature_season"], as_index=False)[columns[2:]].sum()
    grouped["red_zone_tds"] = _num(grouped, "red_zone_tds_rush")
    grouped["red_zone_first_downs"] = _num(grouped, "red_zone_first_downs_rush")
    return grouped


def _team_environment_features(team_stats: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "recent_team",
        "feature_season",
        "team_plays",
        "team_pass_rate",
        "team_run_rate",
        "team_offensive_tds",
    ]
    if team_stats.empty or "team" not in team_stats:
        return pd.DataFrame(columns=columns)
    data = team_stats.copy()
    data["recent_team"] = data["team"].astype(str)
    data["feature_season"] = pd.to_numeric(data["season"], errors="coerce").astype("Int64")
    attempts = _num(data, "attempts")
    carries = _num(data, "carries")
    sacks = _num(data, "sacks_suffered")
    data["team_plays"] = attempts + carries + sacks
    data["team_pass_rate"] = _safe_div(attempts + sacks, data["team_plays"])
    data["team_run_rate"] = _safe_div(carries, data["team_plays"])
    data["team_offensive_tds"] = _num(data, "passing_tds") + _num(data, "rushing_tds")
    return data[columns]


def _merge_on_keys(left: pd.DataFrame, right: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    output = left.copy()
    if "player_name_norm" in keys and "player_name_norm" not in output:
        output["player_name_norm"] = output["player_name"].map(_norm_name)
    if right.empty:
        return output
    available_keys = [key for key in keys if key in output.columns and key in right.columns]
    if len(available_keys) != len(keys):
        return output
    merged = output.merge(right, on=available_keys, how="left", suffixes=("", "__new"))
    for column in list(merged.columns):
        if not column.endswith("__new"):
            continue
        original = column.removesuffix("__new")
        if original in merged:
            merged[original] = merged[column].combine_first(merged[original])
            merged = merged.drop(columns=[column])
        else:
            merged = merged.rename(columns={column: original})
    if "player_name_norm" in merged and "player_name_norm" not in IDENTITY_COLUMNS:
        merged = merged.drop(columns=["player_name_norm"])
    return merged


def _source_warnings(frames: dict[str, pd.DataFrame]) -> list[str]:
    warnings: list[str] = []
    for name, frame in frames.items():
        if frame.empty and name != "season_stats":
            warnings.append(
                f"YELLOW: optional source `{name}` was unavailable and features are zero-filled."
            )
    warnings.append("YELLOW challenger fields were excluded from Backtest V0 main feature sets.")
    warnings.append("K/DST/IDP were excluded from Backtest V0 core positions.")
    return warnings


def _validate_feature_columns(columns: Any) -> None:
    for column in columns:
        lower = str(column).lower()
        if any(token in lower for token in BLOCKED_FEATURE_TOKENS):
            raise BacktestBuildError(f"blocked feature column present: {column}")
        if lower not in YELLOW_CHALLENGER_ALLOWED_EXACT and any(
            token in lower for token in YELLOW_CHALLENGER_TOKENS
        ):
            raise BacktestBuildError(f"YELLOW challenger feature leaked into main set: {column}")


def _age_at_season_end(birth_date: Any, seasons: pd.Series) -> pd.Series:
    dates = pd.to_datetime(birth_date, errors="coerce")
    season_end = pd.to_datetime(seasons.astype("Int64").astype(str) + "-12-31", errors="coerce")
    age_days = (season_end - dates).dt.days
    return (age_days / 365.25).fillna(0)


def _num(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def _safe_div(numerator: Any, denominator: Any) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce").fillna(0.0)
    den = pd.to_numeric(denominator, errors="coerce").fillna(0.0)
    return (num / den.replace(0, pd.NA)).fillna(0.0)


def _norm_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_record(path: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {
        "path": str(path),
        "row_count": _csv_row_count(path),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


if __name__ == "__main__":
    raise SystemExit(main())
