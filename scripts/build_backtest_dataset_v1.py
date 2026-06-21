from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_backtest_dataset_v0 import (
    BASELINE_NUMERIC_COLUMNS,
    BLOCKED_FEATURE_TOKENS,
    CORE_POSITIONS,
    EXPANDED_EXTRA_COLUMNS,
    IDENTITY_COLUMNS,
    YELLOW_CHALLENGER_ALLOWED_EXACT,
    YELLOW_CHALLENGER_TOKENS,
    BacktestBuildError,
    _build_baseline_features,
    _build_expanded_features,
    _build_labels,
    _import_nflreadpy,
    _load_frames,
    _merge_on_keys,
    _norm_name,
    _num,
    _prepare_season_stats,
    _safe_div,
    _snap_features,
    _source_warnings,
)

DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\backtests")
DEFAULT_RUN_LABEL = "backtest_v1_feature_cleanup_20260621"
DEFAULT_SEASONS = list(range(2018, 2026))

V1_METADATA_FEATURES = [
    "age_at_season_end",
    "years_exp",
    "draft_round",
    "draft_pick",
    "draft_pick_log",
    "age_missing",
    "draft_capital_missing",
    "snap_pct_missing",
    "air_yards_missing",
]
V1_AVAILABILITY_FEATURES = [
    "is_active_any_week",
    "active_weeks",
    "depth_chart_best_rank",
]
V1_SNAP_FEATURES = [
    "offense_snaps",
    "offense_pct",
]
V1_TEAM_ENVIRONMENT_FEATURES = [
    "team_plays",
    "team_pass_rate",
    "team_run_rate",
    "team_offensive_tds",
]
V1_QB_BASELINE_FEATURES = [
    "feature_games",
    "feature_nwr_points",
    "feature_nwr_ppg",
    "completions",
    "attempts",
    "passing_yards",
    "passing_tds",
    "passing_interceptions",
    "passing_first_downs",
    "passing_2pt_conversions",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "rushing_2pt_conversions",
    "fumbles_lost",
]
V1_RB_BASELINE_FEATURES = [
    "feature_games",
    "feature_nwr_points",
    "feature_nwr_ppg",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "rushing_2pt_conversions",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
    "receiving_2pt_conversions",
    "fumbles_lost",
    "offense_snaps",
    "offense_pct",
]
V1_RECEIVING_BASELINE_FEATURES = [
    "feature_games",
    "feature_nwr_points",
    "feature_nwr_ppg",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
    "receiving_2pt_conversions",
    "fumbles_lost",
    "offense_snaps",
    "offense_pct",
]
V1_DERIVED_RATE_FEATURES = [
    "rushing_first_downs_per_carry",
    "receiving_first_downs_per_target",
    "receiving_first_downs_per_reception",
    "rushing_yards_per_carry",
    "receiving_yards_per_target",
    "receiving_yards_per_reception",
    "yards_per_target",
    "air_yards_per_target",
    "yac_per_reception",
]
V1_QB_CLEAN_EXTRAS = [
    "sacks_suffered",
    "sack_yards_lost",
    "sack_fumbles",
    "sack_fumbles_lost",
    "qb_carries",
    "qb_rushing_yards",
    "qb_rushing_tds",
    "qb_scrambles",
    *V1_TEAM_ENVIRONMENT_FEATURES,
]
V1_RB_CLEAN_EXTRAS = [
    "rushes_inside_20",
    "rushes_inside_10",
    "rushes_inside_5",
    "goal_to_go_rushes",
    "red_zone_tds",
    "red_zone_first_downs",
]
V1_RECEIVER_CLEAN_EXTRAS = [
    "receiving_air_yards",
    "receiving_yards_after_catch",
]

V1_BASELINE_FEATURES_BY_POSITION = {
    "QB": V1_QB_BASELINE_FEATURES,
    "RB": V1_RB_BASELINE_FEATURES,
    "WR": V1_RECEIVING_BASELINE_FEATURES,
    "TE": V1_RECEIVING_BASELINE_FEATURES,
}
V1_CLEAN_EXPANDED_FEATURES_BY_POSITION = {
    "QB": [
        *V1_QB_BASELINE_FEATURES,
        *V1_METADATA_FEATURES,
        *V1_AVAILABILITY_FEATURES,
        *V1_QB_CLEAN_EXTRAS,
        "rushing_first_downs_per_carry",
        "rushing_yards_per_carry",
    ],
    "RB": [
        *V1_RB_BASELINE_FEATURES,
        *V1_METADATA_FEATURES,
        *V1_AVAILABILITY_FEATURES,
        *V1_RB_CLEAN_EXTRAS,
        "rushing_first_downs_per_carry",
        "receiving_first_downs_per_target",
        "receiving_first_downs_per_reception",
        "rushing_yards_per_carry",
        "receiving_yards_per_target",
        "receiving_yards_per_reception",
        "yards_per_target",
    ],
    "WR": [
        *V1_RECEIVING_BASELINE_FEATURES,
        *V1_METADATA_FEATURES,
        *V1_AVAILABILITY_FEATURES,
        *V1_RECEIVER_CLEAN_EXTRAS,
        "receiving_first_downs_per_target",
        "receiving_first_downs_per_reception",
        "receiving_yards_per_target",
        "receiving_yards_per_reception",
        "yards_per_target",
        "air_yards_per_target",
        "yac_per_reception",
    ],
    "TE": [
        *V1_RECEIVING_BASELINE_FEATURES,
        *V1_METADATA_FEATURES,
        *V1_AVAILABILITY_FEATURES,
        *V1_RECEIVER_CLEAN_EXTRAS,
        "receiving_first_downs_per_target",
        "receiving_first_downs_per_reception",
        "receiving_yards_per_target",
        "receiving_yards_per_reception",
        "yards_per_target",
        "air_yards_per_target",
        "yac_per_reception",
    ],
}


@dataclass(frozen=True)
class BacktestV1DatasetResult:
    output_dir: Path
    baseline_path: Path
    clean_expanded_path: Path
    labels_path: Path
    missingness_path: Path
    whitelist_path: Path
    excluded_features_path: Path
    manifest_path: Path
    seasons_used: list[int]
    target_seasons: list[int]
    row_count: int
    warnings: list[str]


def build_backtest_v1_dataset(
    *,
    seasons: list[int],
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    run_label: str = DEFAULT_RUN_LABEL,
    loader_module: Any | None = None,
    frames: dict[str, pd.DataFrame] | None = None,
) -> BacktestV1DatasetResult:
    _validate_seasons(seasons)
    output_dir = output_root / run_label
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = frames or _load_frames(loader_module or _import_nflreadpy(), seasons)
    warnings = _source_warnings(frames)
    warnings.append("Backtest V1 uses position-specific whitelists and metadata missingness flags.")
    feature_seasons = seasons[:-1]

    season_stats = _prepare_season_stats(frames["season_stats"], feature_seasons)
    labels = _build_labels(frames["season_stats"], seasons[1:])
    baseline = _build_baseline_features(season_stats)
    baseline = _add_snap_display_name_join_key(baseline, season_stats)
    snap_features = _snap_features(frames.get("snap_counts", pd.DataFrame()))
    baseline = _merge_on_keys(
        baseline,
        snap_features,
        ["player_name_norm", "position", "recent_team", "feature_season"],
    )
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
    expanded = _add_snap_display_name_join_key(expanded, season_stats)
    expanded = _merge_on_keys(
        expanded,
        snap_features,
        ["player_name_norm", "position", "recent_team", "feature_season"],
    )
    expanded = _merge_on_keys(
        expanded,
        _season_stat_extras(season_stats),
        ["player_id", "feature_season"],
    )
    expanded = _add_v1_rates_and_missingness(expanded)

    keys = ["player_id", "target_season"]
    label_keys = labels[keys].drop_duplicates()
    baseline = baseline.merge(label_keys, on=keys, how="inner")
    expanded = expanded.merge(label_keys, on=keys, how="inner")
    labels = labels.merge(baseline[keys].drop_duplicates(), on=keys, how="inner")

    baseline_columns = IDENTITY_COLUMNS + _unique(
        [
            *BASELINE_NUMERIC_COLUMNS,
            *_union_feature_columns(V1_BASELINE_FEATURES_BY_POSITION),
        ]
    )
    clean_columns = IDENTITY_COLUMNS + _union_feature_columns(
        V1_CLEAN_EXPANDED_FEATURES_BY_POSITION
    )
    baseline = _select_with_defaults(baseline, baseline_columns)
    clean_expanded = _select_with_defaults(expanded, clean_columns)

    _validate_v1_feature_columns(baseline.columns)
    _validate_v1_feature_columns(clean_expanded.columns)
    if len(labels["target_season"].unique()) < 4:
        raise BacktestBuildError("fewer than four target seasons assembled")

    missingness = _feature_missingness_summary(clean_expanded)
    whitelist = _feature_whitelist_table()
    available_columns = _unique(
        BASELINE_NUMERIC_COLUMNS + EXPANDED_EXTRA_COLUMNS + list(expanded.columns)
    )
    excluded = _excluded_feature_table(available_columns=available_columns)

    baseline_path = output_dir / "feature_dataset_v1_baseline.csv"
    clean_path = output_dir / "feature_dataset_v1_clean_expanded.csv"
    labels_path = output_dir / "labels_v1.csv"
    missingness_path = output_dir / "feature_missingness_summary_v1.csv"
    whitelist_path = output_dir / "feature_whitelist_by_position_v1.csv"
    excluded_path = output_dir / "excluded_features_v1.csv"
    manifest_path = output_dir / "build_manifest_v1.json"

    _write_csv(baseline_path, baseline)
    _write_csv(clean_path, clean_expanded)
    _write_csv(labels_path, labels)
    _write_csv(missingness_path, missingness)
    _write_csv(whitelist_path, whitelist)
    _write_csv(excluded_path, excluded)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "run_label": run_label,
        "purpose": "local_only_backtest_v1_feature_cleanup_dataset",
        "approval_status": "backtest_only_not_model_approved",
        "seasons_used": seasons,
        "feature_seasons": feature_seasons,
        "target_seasons": sorted(int(season) for season in labels["target_season"].unique()),
        "positions": list(CORE_POSITIONS),
        "row_count": len(labels),
        "feature_sets": [
            "v0_baseline_reference",
            "v1_baseline",
            "v1_clean_expanded",
        ],
        "v1_baseline_features_by_position": V1_BASELINE_FEATURES_BY_POSITION,
        "v1_clean_expanded_features_by_position": V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
        "imputation_rules": {
            "role_and_stat_absence": "zero_filled_when no usage or unavailable optional source",
            "metadata_absence": "zero_filled with explicit missing indicator",
            "rate_denominators": "zero when denominator is zero or missing",
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
            path.name: _file_record(path)
            for path in (
                baseline_path,
                clean_path,
                labels_path,
                missingness_path,
                whitelist_path,
                excluded_path,
            )
        },
        "warnings": warnings,
    }
    _write_json(manifest_path, manifest)
    return BacktestV1DatasetResult(
        output_dir=output_dir,
        baseline_path=baseline_path,
        clean_expanded_path=clean_path,
        labels_path=labels_path,
        missingness_path=missingness_path,
        whitelist_path=whitelist_path,
        excluded_features_path=excluded_path,
        manifest_path=manifest_path,
        seasons_used=seasons,
        target_seasons=manifest["target_seasons"],
        row_count=len(labels),
        warnings=warnings,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build local-only Backtest V1 feature-cleanup datasets."
    )
    parser.add_argument("--seasons", nargs="+", type=int, default=DEFAULT_SEASONS)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-label", default=DEFAULT_RUN_LABEL)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build_backtest_v1_dataset(
            seasons=args.seasons,
            output_root=args.output_root,
            run_label=args.run_label,
        )
    except Exception as exc:
        print(f"Backtest V1 dataset build failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"output_dir={result.output_dir}")
    print(f"baseline={result.baseline_path}")
    print(f"clean_expanded={result.clean_expanded_path}")
    print(f"labels={result.labels_path}")
    print(f"missingness={result.missingness_path}")
    print(f"whitelist={result.whitelist_path}")
    print(f"excluded_features={result.excluded_features_path}")
    print(f"manifest={result.manifest_path}")
    print(f"target_seasons={','.join(str(season) for season in result.target_seasons)}")
    print(f"rows={result.row_count}")
    for warning in result.warnings:
        print(f"warning={warning}")
    return 0


def _validate_seasons(seasons: list[int]) -> None:
    if len(seasons) < 5:
        raise BacktestBuildError("at least five seasons are required for four-plus test seasons")
    if any(seasons[index] + 1 != seasons[index + 1] for index in range(len(seasons) - 1)):
        raise BacktestBuildError("seasons must be consecutive for Backtest V1")


def _season_stat_extras(season_stats: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "player_id",
        "feature_season",
        "passing_first_downs",
        "passing_air_yards",
        "receiving_air_yards",
        "passing_yards_after_catch",
        "receiving_yards_after_catch",
        "sacks_suffered",
        "sack_fumbles",
        "sack_fumbles_lost",
        "sack_yards_lost",
    ]
    extras = season_stats[["player_id", "feature_season"]].copy()
    for column in columns[2:]:
        extras[column] = _num(season_stats, column)
    return extras[columns]


def _add_snap_display_name_join_key(
    frame: pd.DataFrame, season_stats: pd.DataFrame
) -> pd.DataFrame:
    display_names = season_stats[["player_id", "feature_season"]].copy()
    display_names["player_name_norm"] = season_stats.get(
        "player_display_name", season_stats.get("player_name", "")
    ).map(_norm_name)
    display_names = display_names.drop_duplicates(["player_id", "feature_season"])
    output = frame.drop(columns=["player_name_norm"], errors="ignore").merge(
        display_names, on=["player_id", "feature_season"], how="left"
    )
    output["player_name_norm"] = output["player_name_norm"].fillna(
        output["player_name"].map(_norm_name)
    )
    return output


def _add_v1_rates_and_missingness(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["rushing_yards_per_carry"] = _safe_div(output["rushing_yards"], output["carries"])
    output["receiving_yards_per_target"] = _safe_div(output["receiving_yards"], output["targets"])
    output["receiving_yards_per_reception"] = _safe_div(
        output["receiving_yards"], output["receptions"]
    )
    output["yards_per_target"] = output["receiving_yards_per_target"]
    output["air_yards_per_target"] = _safe_div(output["receiving_air_yards"], output["targets"])
    output["yac_per_reception"] = _safe_div(
        output["receiving_yards_after_catch"], output["receptions"]
    )
    output["age_missing"] = _num(output, "age_at_season_end").le(0).astype(int)
    output["draft_capital_missing"] = _num(output, "draft_pick").le(0).astype(int)
    output["snap_pct_missing"] = (
        _num(output, "offense_pct").le(0) & _num(output, "offense_snaps").le(0)
    ).astype(int)
    output["air_yards_missing"] = (
        _num(output, "receiving_air_yards").le(0) & _num(output, "targets").gt(0)
    ).astype(int)
    return output.fillna(0)


def _select_with_defaults(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    output = frame.copy()
    for column in columns:
        if column not in output:
            output[column] = 0.0
    return output[columns].copy()


def _validate_v1_feature_columns(columns: Any) -> None:
    for column in columns:
        lower = str(column).lower()
        if any(token in lower for token in BLOCKED_FEATURE_TOKENS):
            raise BacktestBuildError(f"blocked feature column present: {column}")
        if lower not in YELLOW_CHALLENGER_ALLOWED_EXACT and any(
            token in lower for token in YELLOW_CHALLENGER_TOKENS
        ):
            raise BacktestBuildError(f"YELLOW challenger feature leaked into main set: {column}")


def _feature_missingness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    indicator_columns = [
        "age_missing",
        "draft_capital_missing",
        "snap_pct_missing",
        "air_yards_missing",
    ]
    for position, group in frame.groupby("position"):
        for column in indicator_columns:
            values = pd.to_numeric(group.get(column, 0), errors="coerce").fillna(0)
            rows.append(
                {
                    "position": position,
                    "missing_indicator": column,
                    "row_count": len(group),
                    "missing_count": int(values.sum()),
                    "missing_rate": float(values.mean()) if len(group) else 0.0,
                    "imputation_rule": _missingness_rule(column),
                }
            )
    return pd.DataFrame(rows)


def _feature_whitelist_table() -> pd.DataFrame:
    rows = []
    for position in CORE_POSITIONS:
        for feature_set, mapping in (
            ("v1_baseline", V1_BASELINE_FEATURES_BY_POSITION),
            ("v1_clean_expanded", V1_CLEAN_EXPANDED_FEATURES_BY_POSITION),
        ):
            for feature in mapping[position]:
                rows.append(
                    {
                        "position": position,
                        "feature_set": feature_set,
                        "feature": feature,
                        "feature_group": _feature_group(feature),
                    }
                )
    return pd.DataFrame(rows)


def _excluded_feature_table(*, available_columns: list[str]) -> pd.DataFrame:
    rows = []
    for position in CORE_POSITIONS:
        allowed = set(V1_CLEAN_EXPANDED_FEATURES_BY_POSITION[position])
        for column in available_columns:
            if column in IDENTITY_COLUMNS or column in allowed:
                continue
            reason = _exclusion_reason(position, column)
            rows.append(
                {
                    "position": position,
                    "feature": column,
                    "excluded_from": "v1_clean_expanded",
                    "reason": reason,
                }
            )
    return pd.DataFrame(rows)


def _exclusion_reason(position: str, column: str) -> str:
    lower = column.lower()
    if any(token in lower for token in BLOCKED_FEATURE_TOKENS):
        return "blocked_leakage_or_market_feature"
    if lower not in YELLOW_CHALLENGER_ALLOWED_EXACT and any(
        token in lower for token in YELLOW_CHALLENGER_TOKENS
    ):
        return "yellow_challenger_or_advanced_field_not_in_primary_v1"
    if any(token in lower for token in ("punt", "kickoff", "return", "special_teams")):
        return "return_or_special_teams_usage_excluded_from_primary_role_features"
    if position == "QB" and any(token in lower for token in ("receiving", "targets", "receptions")):
        return "inappropriate_qb_receiving_role_feature"
    if position in {"WR", "TE"} and any(
        token in lower for token in ("passing", "rushing", "carries")
    ):
        return "inappropriate_receiver_rushing_or_passing_feature"
    if position == "RB" and "passing" in lower:
        return "inappropriate_rb_passing_feature"
    if column in V1_TEAM_ENVIRONMENT_FEATURES and position != "QB":
        return "team_environment_limited_to_qb_in_primary_v1"
    return "not_in_position_specific_v1_whitelist"


def _missingness_rule(column: str) -> str:
    rules = {
        "age_missing": "age is zero-filled only with explicit missing indicator",
        "draft_capital_missing": (
            "draft capital is zero-filled only with explicit missing indicator"
        ),
        "snap_pct_missing": (
            "snap percentage is zero when no usage/source row, flagged when no snaps"
        ),
        "air_yards_missing": (
            "air yards are zero-filled, flagged for receiving-usage rows without air yards"
        ),
    }
    return rules[column]


def _feature_group(feature: str) -> str:
    lower = feature.lower()
    if feature in V1_METADATA_FEATURES:
        return "metadata_or_missingness"
    if feature in V1_AVAILABILITY_FEATURES:
        return "availability_or_depth_context"
    if feature in V1_SNAP_FEATURES:
        return "playing_time"
    if feature in V1_TEAM_ENVIRONMENT_FEATURES:
        return "team_environment"
    if feature in V1_DERIVED_RATE_FEATURES:
        return "safe_prior_season_rate"
    if any(token in lower for token in ("inside", "goal_to_go", "red_zone")):
        return "red_zone_or_goal_line"
    if any(token in lower for token in ("sack", "scramble")):
        return "qb_pressure_or_sack_context"
    if any(token in lower for token in ("passing", "attempts", "completions")):
        return "passing_production"
    if any(token in lower for token in ("rushing", "carries")):
        return "rushing_production"
    if any(token in lower for token in ("receiving", "targets", "receptions", "air_yards", "yac")):
        return "receiving_production"
    return "baseline_context"


def _union_feature_columns(mapping: dict[str, list[str]]) -> list[str]:
    return _unique([feature for features in mapping.values() for feature in features])


def _unique(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


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
