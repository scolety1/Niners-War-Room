from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_backtest_dataset_v0 import CORE_POSITIONS
from scripts.build_backtest_dataset_v1 import (
    V1_BASELINE_FEATURES_BY_POSITION,
    V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
)
from scripts.build_overnight_tune_dataset_v0 import blocked_field_reason

DEFAULT_INPUT_DATASET_DIR = Path(
    r"C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v0_20260621"
    r"\backtest_v1_snap_fixed_regenerated_20260621_0415"
)
DEFAULT_OUTPUT_ROOT = Path(
    r"C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v1_expanded_20260622"
)
DEFAULT_VENDOR_ARCHIVE_ROOT = Path(
    r"C:\NWR_SHARED_DATA\vendor_archive_recovery"
    r"\rotowire_fantasypros_stats_organized_20260621_v2"
)

IDENTITY_COLUMNS = {
    "player_id",
    "feature_season",
    "target_season",
    "player_name",
    "position",
    "recent_team",
}
SNAP_COLUMNS = {"offense_snaps", "offense_pct", "snap_pct_missing"}
EVALUATION_SEASONS = [2021, 2022, 2023, 2024, 2025]
FEATURE_FAMILIES = (
    "SAFE_BASELINE",
    "SAFE_EXPANDED",
    "SAFE_NO_SNAP",
    "SAFE_SNAP_FIXED",
    "YELLOW_CHALLENGER",
    "VENDOR_YELLOW_CHALLENGER",
    "BLOCKED",
)


class OvernightTuneV1BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class OvernightTuneV1BuildResult:
    output_root: Path
    input_manifest_path: Path
    grid_manifest_path: Path
    summary_path: Path
    planned_fit_count: int
    vendor_ready: bool


def build_overnight_tune_dataset_v1(
    *,
    input_dataset_dir: Path = DEFAULT_INPUT_DATASET_DIR,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    vendor_archive_root: Path = DEFAULT_VENDOR_ARCHIVE_ROOT,
) -> OvernightTuneV1BuildResult:
    output_root.mkdir(parents=True, exist_ok=True)
    baseline = _read_csv(input_dataset_dir / "feature_dataset_v1_baseline.csv")
    clean = _read_csv(input_dataset_dir / "feature_dataset_v1_clean_expanded.csv")
    labels = _read_csv(input_dataset_dir / "labels_v1.csv")
    _validate_base_inputs(baseline, clean, labels)

    diagnosis_path = output_root / "V0_SMALL_GRID_DIAGNOSIS.md"
    diagnosis_path.write_text(_v0_small_grid_diagnosis(), encoding="utf-8")

    player_keys = _player_join_keys(clean, labels)
    vendor = _build_vendor_feature_tables(
        vendor_archive_root=vendor_archive_root,
        player_keys=player_keys,
        output_root=output_root,
    )
    vendor_ready = bool(vendor["ready"])
    if not vendor_ready:
        raise OvernightTuneV1BuildError(
            "vendor challenger rows were not joined; stop before full V1 run"
        )

    safe_baseline = baseline.copy()
    safe_expanded = clean.copy()
    safe_no_snap = clean.drop(columns=[c for c in SNAP_COLUMNS if c in clean], errors="ignore")
    safe_snap_fixed = clean.copy()
    vendor_frame = _merge_vendor_features(clean, vendor["features"])

    datasets = {
        "safe_baseline": safe_baseline,
        "safe_expanded": safe_expanded,
        "safe_no_snap": safe_no_snap,
        "safe_snap_fixed": safe_snap_fixed,
        "vendor_joined": vendor_frame,
    }
    for name, frame in datasets.items():
        frame.to_csv(output_root / f"{name}_features_v1.csv", index=False, encoding="utf-8")
    labels.to_csv(output_root / "labels_v1.csv", index=False, encoding="utf-8")

    variant_plan = _variant_plan(safe_baseline, safe_expanded, safe_no_snap, vendor_frame)
    variant_plan.to_csv(output_root / "V1_EXPANDED_VARIANT_PLAN.csv", index=False)
    blocked_scan = _blocked_scan(variant_plan)
    leakage_scan = _leakage_scan(variant_plan)
    blocked_scan.to_csv(output_root / "V1_EXPANDED_BLOCKED_FIELD_SCAN.csv", index=False)
    leakage_scan.to_csv(output_root / "V1_EXPANDED_LEAKAGE_SCAN.csv", index=False)
    if not blocked_scan["scan_result"].eq("PASS").all():
        raise OvernightTuneV1BuildError("blocked-field pre-run scan failed")
    if not leakage_scan["scan_result"].eq("PASS").all():
        raise OvernightTuneV1BuildError("leakage pre-run scan failed")

    grid = _expanded_grid(variant_plan)
    grid_path = output_root / "V1_EXPANDED_PRE_RUN_GRID_MANIFEST.csv"
    grid.to_csv(grid_path, index=False, quoting=csv.QUOTE_MINIMAL)
    if len(grid) < 500:
        raise OvernightTuneV1BuildError(f"expanded grid too small: {len(grid)} planned fits")
    position_counts = grid.groupby("position").size().to_dict()
    low_positions = {pos: count for pos, count in position_counts.items() if count < 100}
    if low_positions:
        raise OvernightTuneV1BuildError(f"position fit count below 100: {low_positions}")

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "purpose": "local_only_overnight_model_tune_v1_expanded_inputs",
        "approval_status": "research_inputs_only_not_model_approved",
        "input_dataset_dir": str(input_dataset_dir),
        "output_root": str(output_root),
        "vendor_archive_root": str(vendor_archive_root),
        "positions": list(CORE_POSITIONS),
        "evaluation_seasons": EVALUATION_SEASONS,
        "feature_families": list(FEATURE_FAMILIES),
        "planned_fit_count": int(len(grid)),
        "planned_fit_count_by_position": {k: int(v) for k, v in position_counts.items()},
        "planned_fit_count_by_model_family": {
            k: int(v) for k, v in grid.groupby("model_family").size().to_dict().items()
        },
        "planned_fit_count_by_feature_family": {
            k: int(v) for k, v in grid.groupby("feature_family").size().to_dict().items()
        },
        "vendor_ready": vendor_ready,
        "vendor_feature_columns": vendor["feature_columns"],
        "blocked_field_scan": "PASS",
        "leakage_scan": "PASS",
        "forbidden_use": [
            "private_value",
            "rankings",
            "hidden_sort",
            "mock_draft",
            "recommendations",
            "simulations",
            "final_draft_decisions",
            "deployment",
            "latest_candidate",
            "latest_approved",
        ],
    }
    manifest_path = output_root / "tune_input_manifest_v1.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    summary_path = output_root / "V1_EXPANDED_PRE_RUN_SUMMARY.md"
    summary_path.write_text(
        _pre_run_summary(manifest, vendor, blocked_scan, leakage_scan), encoding="utf-8"
    )
    return OvernightTuneV1BuildResult(
        output_root=output_root,
        input_manifest_path=manifest_path,
        grid_manifest_path=grid_path,
        summary_path=summary_path,
        planned_fit_count=len(grid),
        vendor_ready=vendor_ready,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Overnight Tune V1 expanded inputs.")
    parser.add_argument("--input-dataset-dir", type=Path, default=DEFAULT_INPUT_DATASET_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--vendor-archive-root", type=Path, default=DEFAULT_VENDOR_ARCHIVE_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build_overnight_tune_dataset_v1(
            input_dataset_dir=args.input_dataset_dir,
            output_root=args.output_root,
            vendor_archive_root=args.vendor_archive_root,
        )
    except Exception as exc:
        print(f"Overnight Tune V1 build failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"output_root={result.output_root}")
    print(f"manifest={result.input_manifest_path}")
    print(f"grid_manifest={result.grid_manifest_path}")
    print(f"summary={result.summary_path}")
    print(f"planned_fit_count={result.planned_fit_count}")
    print(f"vendor_ready={result.vendor_ready}")
    return 0


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise OvernightTuneV1BuildError(f"missing input CSV: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise OvernightTuneV1BuildError(f"empty input CSV: {path}")
    return frame


def _validate_base_inputs(
    baseline: pd.DataFrame, clean: pd.DataFrame, labels: pd.DataFrame
) -> None:
    for name, frame in {"baseline": baseline, "clean": clean}.items():
        missing = sorted(IDENTITY_COLUMNS.difference(frame.columns))
        if missing:
            raise OvernightTuneV1BuildError(f"{name} missing identity columns: {missing}")
        for column in frame.columns:
            if column not in IDENTITY_COLUMNS and blocked_field_reason(column):
                raise OvernightTuneV1BuildError(f"blocked field in {name}: {column}")
    required_labels = {"player_id", "target_season", "target_player_name", "target_position"}
    missing_labels = sorted(required_labels.difference(labels.columns))
    if missing_labels:
        raise OvernightTuneV1BuildError(f"labels missing columns: {missing_labels}")


def _player_join_keys(clean: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    keys = clean[["player_id", "feature_season", "target_season", "position", "recent_team"]].merge(
        labels[["player_id", "target_season", "target_player_name"]],
        on=["player_id", "target_season"],
        how="left",
    )
    keys["player_name_norm"] = keys["target_player_name"].fillna("").map(_norm_name)
    keys["recent_team"] = keys["recent_team"].astype(str)
    return keys.drop_duplicates(["player_id", "feature_season"])


def _build_vendor_feature_tables(
    *, vendor_archive_root: Path, player_keys: pd.DataFrame, output_root: Path
) -> dict[str, Any]:
    canonical = vendor_archive_root / "02_canonical"
    if not canonical.exists():
        raise OvernightTuneV1BuildError(f"vendor canonical root missing: {canonical}")
    records: list[pd.DataFrame] = []
    field_rows: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []

    for year in range(2021, 2025):
        records.extend(
            [
                _rotowire_receiving_advanced(canonical, year, field_rows, blocked_rows),
                _rotowire_receiving_redzone(canonical, year, field_rows, blocked_rows),
                _rotowire_rushing_advanced(canonical, year, field_rows, blocked_rows),
                _rotowire_rushing_redzone(canonical, year, field_rows, blocked_rows),
            ]
        )
    for year in range(2018, 2025):
        for position in CORE_POSITIONS:
            records.append(
                _fantasypros_advanced(canonical, year, position, field_rows, blocked_rows)
            )
    parsed_records = [frame for frame in records if not frame.empty]
    if not parsed_records:
        raise OvernightTuneV1BuildError("no vendor feature rows parsed")
    vendor_raw = pd.concat(parsed_records, ignore_index=True)
    vendor_raw["player_name_norm"] = vendor_raw["player_name"].map(_norm_name)
    vendor_raw["team"] = vendor_raw["team"].astype(str)

    merged_team = player_keys.merge(
        vendor_raw,
        left_on=["feature_season", "position", "recent_team", "player_name_norm"],
        right_on=["feature_season", "position", "team", "player_name_norm"],
        how="left",
    )
    merged_name = player_keys.merge(
        vendor_raw,
        on=["feature_season", "position", "player_name_norm"],
        how="left",
        suffixes=("", "_vendor"),
    )
    merged = merged_team.copy()
    feature_columns = sorted([c for c in vendor_raw.columns if c.startswith("vendor_")])
    for column in feature_columns + ["vendor_family"]:
        if column not in merged:
            merged[column] = pd.NA
        if column in merged_name:
            merged[column] = merged[column].combine_first(merged_name[column])
    for column in feature_columns:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    keep = ["player_id", "feature_season", *feature_columns]
    vendor_features = merged[keep].groupby(["player_id", "feature_season"], as_index=False).max()

    coverage_rows = []
    for family, columns in _vendor_feature_groups().items():
        family_cols = [c for c in columns if c in vendor_features.columns]
        if not family_cols:
            continue
        joined = player_keys[["player_id", "feature_season", "position"]].merge(
            vendor_features[["player_id", "feature_season"] + family_cols],
            on=["player_id", "feature_season"],
            how="left",
        )
        for position, group in joined.groupby("position"):
            group_pop = group[family_cols].notna().any(axis=1)
            coverage_rows.append(
                {
                    "vendor_family": family,
                    "position": position,
                    "total_rows": len(group),
                    "joined_rows": int(group_pop.sum()),
                    "coverage_rate": float(group_pop.mean()) if len(group) else 0.0,
                }
            )
    coverage = pd.DataFrame(coverage_rows)
    field_classification = pd.DataFrame(field_rows).drop_duplicates()
    blocked = pd.DataFrame(blocked_rows).drop_duplicates()
    examples = (
        player_keys.merge(vendor_features, on=["player_id", "feature_season"], how="left")
        .dropna(subset=feature_columns, how="all")[
            ["feature_season", "position", "recent_team", "target_player_name", *feature_columns]
        ]
        .head(50)
    )
    coverage.to_csv(output_root / "VENDOR_FEATURE_JOIN_COVERAGE.csv", index=False)
    field_classification.to_csv(
        output_root / "VENDOR_FEATURE_FIELD_CLASSIFICATION.csv", index=False
    )
    examples.to_csv(output_root / "VENDOR_FEATURE_JOIN_EXAMPLES.csv", index=False)
    blocked.to_csv(output_root / "VENDOR_FEATURE_BLOCKED_FIELDS.csv", index=False)
    ready = (
        bool(feature_columns)
        and not coverage.empty
        and coverage[
            (coverage["vendor_family"].str.contains("rotowire_receiving", na=False))
            & (coverage["position"].isin(["WR", "TE"]))
        ]["joined_rows"].sum()
        > 0
        and not any(blocked_field_reason(column) for column in feature_columns)
    )
    readiness = _vendor_readiness_markdown(coverage, field_classification, blocked, ready)
    (output_root / "VENDOR_FEATURE_READINESS.md").write_text(readiness, encoding="utf-8")
    return {"features": vendor_features, "feature_columns": feature_columns, "ready": ready}


def _rotowire_receiving_advanced(
    canonical: Path, year: int, field_rows: list[dict[str, Any]], blocked_rows: list[dict[str, Any]]
) -> pd.DataFrame:
    path = (
        canonical / "rotowire" / str(year) / "receiving" / f"rotowire_{year}_receiving_advanced.csv"
    )
    mapping = {
        "Rts": "vendor_rw_rec_routes_run",
        "TPRR%": "vendor_rw_rec_tprr_pct",
        "YPRR": "vendor_rw_rec_yprr",
        "AY.1": "vendor_rw_rec_team_air_yards_pct",
        "TAR.1": "vendor_rw_rec_team_target_pct",
        "YAC%": "vendor_rw_rec_yac_pct",
        "Drop %": "vendor_rw_rec_drop_pct",
        "Catch %": "vendor_rw_rec_catch_pct",
    }
    return _rotowire_table(
        path, year, "rotowire_receiving_routes", mapping, field_rows, blocked_rows
    )


def _rotowire_receiving_redzone(
    canonical: Path, year: int, field_rows: list[dict[str, Any]], blocked_rows: list[dict[str, Any]]
) -> pd.DataFrame:
    path = (
        canonical / "rotowire" / str(year) / "receiving" / f"rotowire_{year}_receiving_redzone.csv"
    )
    mapping = {
        "In20": "vendor_rw_rec_rz_tgt_in20",
        "In10": "vendor_rw_rec_rz_tgt_in10",
        "In5": "vendor_rw_rec_rz_tgt_in5",
        "%Tm": "vendor_rw_rec_rz_team_pct",
    }
    return _rotowire_table(
        path, year, "rotowire_receiving_redzone", mapping, field_rows, blocked_rows
    )


def _rotowire_rushing_advanced(
    canonical: Path, year: int, field_rows: list[dict[str, Any]], blocked_rows: list[dict[str, Any]]
) -> pd.DataFrame:
    path = canonical / "rotowire" / str(year) / "rushing" / f"rotowire_{year}_rushing_advanced.csv"
    mapping = {
        "BT": "vendor_rw_rush_broken_tackles",
        "BT%": "vendor_rw_rush_broken_tackle_pct",
        "YDS.1": "vendor_rw_rush_yards_after_contact",
        "AVG": "vendor_rw_rush_yac_per_attempt",
        "%": "vendor_rw_rush_yac_pct",
        "Stuffed": "vendor_rw_rush_stuffed",
        "In%": "vendor_rw_rush_inside_pct",
    }
    return _rotowire_table(
        path, year, "rotowire_rushing_advanced", mapping, field_rows, blocked_rows
    )


def _rotowire_rushing_redzone(
    canonical: Path, year: int, field_rows: list[dict[str, Any]], blocked_rows: list[dict[str, Any]]
) -> pd.DataFrame:
    path = canonical / "rotowire" / str(year) / "rushing" / f"rotowire_{year}_rushing_redzone.csv"
    mapping = {
        "In20": "vendor_rw_rush_rz_att_in20",
        "In10": "vendor_rw_rush_rz_att_in10",
        "In5": "vendor_rw_rush_rz_att_in5",
        "%Tm": "vendor_rw_rush_rz_team_pct",
        "In20.1": "vendor_rw_rush_rz_td_in20",
        "In10.1": "vendor_rw_rush_rz_td_in10",
        "In5.1": "vendor_rw_rush_rz_td_in5",
    }
    return _rotowire_table(
        path, year, "rotowire_rushing_redzone", mapping, field_rows, blocked_rows
    )


def _rotowire_table(
    path: Path,
    year: int,
    family: str,
    mapping: dict[str, str],
    field_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path, header=1, encoding="utf-8-sig")
    return _vendor_table(
        frame=frame,
        year=year,
        family=family,
        name_column="Name",
        team_column="Team",
        position_column="Pos",
        mapping=mapping,
        field_rows=field_rows,
        blocked_rows=blocked_rows,
    )


def _fantasypros_advanced(
    canonical: Path,
    year: int,
    position: str,
    field_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    path = (
        canonical
        / "fantasypros"
        / str(year)
        / position
        / f"fantasypros_{year}_{position}_advanced.csv"
    )
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path, encoding="utf-8-sig")
    frame[["player_clean", "team_clean"]] = (
        frame["Player"].apply(_split_fantasypros_player).tolist()
    )
    mappings = {
        "QB": {
            "AIR": "vendor_fp_qb_air_yards",
            "AIR/A": "vendor_fp_qb_air_per_attempt",
            "PKT TIME": "vendor_fp_qb_pocket_time",
            "SACK": "vendor_fp_qb_sacks",
            "KNCK": "vendor_fp_qb_knockdowns",
            "HRRY": "vendor_fp_qb_hurries",
            "BLITZ": "vendor_fp_qb_blitzes",
            "POOR": "vendor_fp_qb_poor_throws",
            "DROP": "vendor_fp_qb_drops",
            "RZ ATT": "vendor_fp_qb_rz_att",
        },
        "RB": {
            "YBCON": "vendor_fp_rb_yards_before_contact",
            "YBCON/ATT": "vendor_fp_rb_ybc_per_att",
            "YACON": "vendor_fp_rb_yards_after_contact",
            "YACON/ATT": "vendor_fp_rb_yac_per_att",
            "BRKTKL": "vendor_fp_rb_broken_tackles",
            "TK LOSS": "vendor_fp_rb_tackles_for_loss",
            "RZ TGT": "vendor_fp_rb_rz_targets",
            "YACON.1": "vendor_fp_rb_rec_yards_after_contact",
        },
        "WR": _fantasypros_receiver_mapping("wr"),
        "TE": _fantasypros_receiver_mapping("te"),
    }
    return _vendor_table(
        frame=frame,
        year=year,
        family=f"fantasypros_{position.lower()}_advanced",
        name_column="player_clean",
        team_column="team_clean",
        position_column=None,
        mapping=mappings[position],
        field_rows=field_rows,
        blocked_rows=blocked_rows,
        forced_position=position,
        explicit_blocked=["RK", "RTG"],
    )


def _fantasypros_receiver_mapping(prefix: str) -> dict[str, str]:
    return {
        "YBC": f"vendor_fp_{prefix}_yards_before_catch",
        "YBC/R": f"vendor_fp_{prefix}_ybc_per_rec",
        "AIR": f"vendor_fp_{prefix}_air_yards",
        "AIR/R": f"vendor_fp_{prefix}_air_per_rec",
        "YAC": f"vendor_fp_{prefix}_yac",
        "YAC/R": f"vendor_fp_{prefix}_yac_per_rec",
        "YACON": f"vendor_fp_{prefix}_yards_after_contact",
        "YACON/R": f"vendor_fp_{prefix}_yacon_per_rec",
        "BRKTKL": f"vendor_fp_{prefix}_broken_tackles",
        "% TM": f"vendor_fp_{prefix}_team_target_pct",
        "CATCHABLE": f"vendor_fp_{prefix}_catchable_targets",
        "DROP": f"vendor_fp_{prefix}_drops",
        "RZ TGT": f"vendor_fp_{prefix}_rz_targets",
    }


def _vendor_table(
    *,
    frame: pd.DataFrame,
    year: int,
    family: str,
    name_column: str,
    team_column: str,
    position_column: str | None,
    mapping: dict[str, str],
    field_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    forced_position: str | None = None,
    explicit_blocked: list[str] | None = None,
) -> pd.DataFrame:
    explicit_blocked = explicit_blocked or []
    for column in explicit_blocked:
        if column in frame.columns:
            blocked_rows.append(
                {
                    "source_family": family,
                    "source_field": column,
                    "reason": "rank/rating field blocked",
                }
            )
    rows = pd.DataFrame(
        {
            "feature_season": year,
            "player_name": frame[name_column].astype(str),
            "team": frame[team_column].astype(str),
            "position": forced_position
            if forced_position
            else frame[position_column].astype(str)
            if position_column
            else "",
            "vendor_family": family,
        }
    )
    for source_field, target in mapping.items():
        if source_field not in frame.columns:
            continue
        if blocked_field_reason(target) or blocked_field_reason(source_field):
            blocked_rows.append(
                {
                    "source_family": family,
                    "source_field": source_field,
                    "target_field": target,
                    "reason": "blocked field pattern",
                }
            )
            continue
        rows[target] = frame[source_field].map(_to_number)
        field_rows.append(
            {
                "source_family": family,
                "source_field": source_field,
                "target_field": target,
                "classification": "VENDOR_YELLOW_CHALLENGER",
                "definition_status": "factual_non_rank_metric",
            }
        )
    return rows


def _merge_vendor_features(clean: pd.DataFrame, vendor_features: pd.DataFrame) -> pd.DataFrame:
    output = clean.merge(vendor_features, on=["player_id", "feature_season"], how="left")
    vendor_cols = [c for c in output.columns if c.startswith("vendor_")]
    for column in vendor_cols:
        output[column] = pd.to_numeric(output[column], errors="coerce").fillna(0)
    return output


def _variant_plan(
    baseline: pd.DataFrame, expanded: pd.DataFrame, no_snap: pd.DataFrame, vendor: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    safe_maps = {
        "safe_baseline": (
            "SAFE_BASELINE",
            "safe_baseline_features_v1.csv",
            V1_BASELINE_FEATURES_BY_POSITION,
        ),
        "safe_expanded": (
            "SAFE_EXPANDED",
            "safe_expanded_features_v1.csv",
            V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
        ),
        "safe_no_snap": (
            "SAFE_NO_SNAP",
            "safe_no_snap_features_v1.csv",
            {
                p: [f for f in features if f not in SNAP_COLUMNS]
                for p, features in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION.items()
            },
        ),
        "safe_snap_fixed": (
            "SAFE_SNAP_FIXED",
            "safe_snap_fixed_features_v1.csv",
            V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
        ),
    }
    frames = {
        "safe_baseline_features_v1.csv": baseline,
        "safe_expanded_features_v1.csv": expanded,
        "safe_no_snap_features_v1.csv": no_snap,
        "safe_snap_fixed_features_v1.csv": expanded,
        "vendor_joined_features_v1.csv": vendor,
    }
    for variant_id, (family, source, mapping) in safe_maps.items():
        for position in CORE_POSITIONS:
            cols = [c for c in mapping[position] if c in frames[source].columns]
            rows.append(_variant_row(variant_id, family, position, source, cols))

    ablations = {
        "role_usage_core": [
            "feature_games",
            "feature_nwr_points",
            "feature_nwr_ppg",
            "targets",
            "receptions",
            "carries",
            "offense_snaps",
            "offense_pct",
        ],
        "age_draft_only": [
            "age_at_season_end",
            "years_exp",
            "draft_round",
            "draft_pick",
            "draft_pick_log",
            "age_missing",
            "draft_capital_missing",
        ],
        "redzone_goal_line": [
            "rushes_inside_20",
            "rushes_inside_10",
            "rushes_inside_5",
            "goal_to_go_rushes",
            "red_zone_tds",
            "red_zone_first_downs",
        ],
        "team_environment": ["team_plays", "team_pass_rate", "team_run_rate", "team_offensive_tds"],
        "receiving_efficiency": [
            "receiving_yards_per_target",
            "receiving_yards_per_reception",
            "air_yards_per_target",
            "yac_per_reception",
        ],
        "rushing_efficiency": ["rushing_yards_per_carry", "rushing_first_downs_per_carry"],
    }
    for variant_id, wanted in ablations.items():
        for position in CORE_POSITIONS:
            base = V1_CLEAN_EXPANDED_FEATURES_BY_POSITION[position]
            cols = [c for c in [*base, *wanted] if c in expanded.columns and c in wanted]
            if len(cols) >= 2:
                rows.append(
                    _variant_row(
                        variant_id,
                        "YELLOW_CHALLENGER",
                        position,
                        "safe_snap_fixed_features_v1.csv",
                        cols,
                    )
                )

    vendor_groups = _vendor_feature_groups()
    for group_name, group_cols in vendor_groups.items():
        positions = (
            ["WR", "TE"]
            if "receiving" in group_name
            else ["RB"]
            if "rushing" in group_name
            else list(CORE_POSITIONS)
        )
        for position in positions:
            safe_cols = [
                c for c in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION[position] if c in vendor.columns
            ]
            vendor_cols = [c for c in group_cols if c in vendor.columns]
            if vendor_cols:
                rows.append(
                    _variant_row(
                        f"vendor_{group_name}",
                        "VENDOR_YELLOW_CHALLENGER",
                        position,
                        "vendor_joined_features_v1.csv",
                        [*safe_cols, *vendor_cols],
                    )
                )
    combined_vendor_cols = [c for c in vendor.columns if c.startswith("vendor_")]
    for position in CORE_POSITIONS:
        pos_vendor_cols = [
            c for c in combined_vendor_cols if _vendor_column_applies_to_position(c, position)
        ]
        if pos_vendor_cols:
            safe_cols = [
                c for c in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION[position] if c in vendor.columns
            ]
            rows.append(
                _variant_row(
                    "vendor_combined_advanced",
                    "VENDOR_YELLOW_CHALLENGER",
                    position,
                    "vendor_joined_features_v1.csv",
                    [*safe_cols, *pos_vendor_cols],
                )
            )
    plan = pd.DataFrame(rows)
    plan["feature_columns_json"] = plan["feature_columns"].map(json.dumps)
    plan = plan.drop(columns=["feature_columns"])
    return plan


def _variant_row(
    variant_id: str, family: str, position: str, source_dataset: str, columns: list[str]
) -> dict[str, Any]:
    unique_cols = []
    for column in columns:
        if column not in unique_cols and not blocked_field_reason(column):
            unique_cols.append(column)
    return {
        "variant_id": variant_id,
        "feature_family": family,
        "position": position,
        "source_dataset": source_dataset,
        "feature_count": len(unique_cols),
        "feature_columns": unique_cols,
        "status": "ready",
        "candidate_label_allowed": "VENDOR_RESEARCH_CANDIDATE_ONLY"
        if family == "VENDOR_YELLOW_CHALLENGER"
        else "SAFE_RESEARCH_CANDIDATE_ONLY",
    }


def _expanded_grid(variant_plan: pd.DataFrame) -> pd.DataFrame:
    model_configs = _model_configs()
    rows = []
    for phase in ("phase1_base_grid", "phase2_deepening", "phase3_stability_stress"):
        for _, variant in variant_plan.iterrows():
            for config in model_configs:
                config_phase = config["phase"]
                if phase == "phase1_base_grid" and config_phase != "phase1":
                    continue
                if phase == "phase2_deepening" and config_phase not in {"phase1", "phase2"}:
                    continue
                if phase == "phase3_stability_stress" and config_phase not in {"phase1", "phase3"}:
                    continue
                row = {
                    **config,
                    "phase": phase,
                    "model_config_phase": config_phase,
                    "fit_id": "",
                    "variant_id": variant["variant_id"],
                    "feature_family": variant["feature_family"],
                    "position": variant["position"],
                    "source_dataset": variant["source_dataset"],
                    "feature_columns_json": variant["feature_columns_json"],
                    "feature_count": int(variant["feature_count"]),
                }
                row["fit_id"] = _fit_id(row)
                rows.append(row)
    return pd.DataFrame(rows)


def _model_configs() -> list[dict[str, Any]]:
    configs: list[dict[str, Any]] = []
    for alpha in [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000]:
        configs.append(
            {
                "model_family": "numpy_ridge",
                "model_name": "numpy_ridge",
                "hyperparameters_json": json.dumps({"alpha": alpha}),
                "phase": "phase1",
            }
        )
        configs.append(
            {
                "model_family": "ridge",
                "model_name": "sklearn_ridge",
                "hyperparameters_json": json.dumps({"alpha": alpha}),
                "phase": "phase1",
            }
        )
    for alpha in [0.001, 0.01, 0.05, 0.1, 0.3, 1, 3]:
        for l1 in [0.05, 0.15, 0.3, 0.5, 0.75, 0.9]:
            configs.append(
                {
                    "model_family": "elastic_net",
                    "model_name": "sklearn_elastic_net",
                    "hyperparameters_json": json.dumps(
                        {"alpha": alpha, "l1_ratio": l1, "max_iter": 12000}
                    ),
                    "phase": "phase1",
                }
            )
    for model_name, family in [
        ("sklearn_random_forest", "random_forest"),
        ("sklearn_extra_trees", "extra_trees"),
    ]:
        for n in [80, 140]:
            for leaf in [2, 4, 8]:
                for depth in [None, 6, 10]:
                    for seed in [11, 42]:
                        configs.append(
                            {
                                "model_family": family,
                                "model_name": model_name,
                                "hyperparameters_json": json.dumps(
                                    {
                                        "n_estimators": n,
                                        "min_samples_leaf": leaf,
                                        "max_depth": depth,
                                        "random_state": seed,
                                        "max_features": "sqrt",
                                    }
                                ),
                                "phase": "phase1",
                            }
                        )
    for learning_rate in [0.03, 0.06, 0.1]:
        for depth in [2, 3]:
            for seed in [11, 42]:
                configs.append(
                    {
                        "model_family": "gradient_boosting",
                        "model_name": "sklearn_gradient_boosting",
                        "hyperparameters_json": json.dumps(
                            {
                                "n_estimators": 120,
                                "learning_rate": learning_rate,
                                "max_depth": depth,
                                "random_state": seed,
                            }
                        ),
                        "phase": "phase2",
                    }
                )
    for alpha in [0.0003, 0.0007, 0.002, 0.007, 0.02, 0.07, 0.2, 0.7, 2, 7, 20, 70, 200, 700]:
        configs.append(
            {
                "model_family": "ridge_deep",
                "model_name": "sklearn_ridge",
                "hyperparameters_json": json.dumps({"alpha": alpha}),
                "phase": "phase2",
            }
        )
    for seed in [3, 5, 7, 13, 17, 23]:
        configs.append(
            {
                "model_family": "stability_random_forest",
                "model_name": "sklearn_random_forest",
                "hyperparameters_json": json.dumps(
                    {
                        "n_estimators": 120,
                        "min_samples_leaf": 4,
                        "max_depth": None,
                        "random_state": seed,
                        "max_features": "sqrt",
                    }
                ),
                "phase": "phase3",
            }
        )
    return configs


def _blocked_scan(variant_plan: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in variant_plan.iterrows():
        cols = json.loads(row["feature_columns_json"])
        blocked = [c for c in cols if blocked_field_reason(c)]
        rows.append(
            {
                "variant_id": row["variant_id"],
                "feature_family": row["feature_family"],
                "position": row["position"],
                "blocked_field_count": len(blocked),
                "blocked_fields": ";".join(blocked),
                "scan_result": "PASS" if not blocked else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def _leakage_scan(variant_plan: pd.DataFrame) -> pd.DataFrame:
    leak_tokens = {
        "next_nwr_points",
        "next_nwr_ppg",
        "target_games",
        "fantasy_points",
        "fantasy_points_ppr",
    }
    rows = []
    for _, row in variant_plan.iterrows():
        cols = json.loads(row["feature_columns_json"])
        leaks = [c for c in cols if _norm_col(c) in leak_tokens]
        rows.append(
            {
                "variant_id": row["variant_id"],
                "feature_family": row["feature_family"],
                "position": row["position"],
                "leakage_field_count": len(leaks),
                "leakage_fields": ";".join(leaks),
                "scan_result": "PASS" if not leaks else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def _vendor_feature_groups() -> dict[str, list[str]]:
    return {
        "rotowire_receiving_routes": [
            "vendor_rw_rec_routes_run",
            "vendor_rw_rec_tprr_pct",
            "vendor_rw_rec_yprr",
            "vendor_rw_rec_team_air_yards_pct",
            "vendor_rw_rec_team_target_pct",
            "vendor_rw_rec_yac_pct",
        ],
        "rotowire_receiving_redzone": [
            "vendor_rw_rec_rz_tgt_in20",
            "vendor_rw_rec_rz_tgt_in10",
            "vendor_rw_rec_rz_tgt_in5",
            "vendor_rw_rec_rz_team_pct",
        ],
        "rotowire_rushing_advanced": [
            "vendor_rw_rush_broken_tackles",
            "vendor_rw_rush_broken_tackle_pct",
            "vendor_rw_rush_yards_after_contact",
            "vendor_rw_rush_yac_per_attempt",
            "vendor_rw_rush_yac_pct",
        ],
        "rotowire_rushing_redzone": [
            "vendor_rw_rush_rz_att_in20",
            "vendor_rw_rush_rz_att_in10",
            "vendor_rw_rush_rz_att_in5",
            "vendor_rw_rush_rz_team_pct",
        ],
        "fantasypros_advanced": [
            "vendor_fp_qb_air_yards",
            "vendor_fp_qb_air_per_attempt",
            "vendor_fp_qb_pocket_time",
            "vendor_fp_rb_yards_after_contact",
            "vendor_fp_rb_broken_tackles",
            "vendor_fp_wr_air_yards",
            "vendor_fp_wr_yac",
            "vendor_fp_wr_broken_tackles",
            "vendor_fp_te_air_yards",
            "vendor_fp_te_yac",
            "vendor_fp_te_broken_tackles",
        ],
    }


def _vendor_column_applies_to_position(column: str, position: str) -> bool:
    lower = column.lower()
    if "_qb_" in lower:
        return position == "QB"
    if "_rb_" in lower or "_rush_" in lower:
        return position == "RB"
    if "_wr_" in lower:
        return position == "WR"
    if "_te_" in lower:
        return position == "TE"
    if "_rec_" in lower:
        return position in {"WR", "TE"}
    return True


def _pre_run_summary(
    manifest: dict[str, Any],
    vendor: dict[str, Any],
    blocked_scan: pd.DataFrame,
    leakage_scan: pd.DataFrame,
) -> str:
    blocked_status = "PASS" if blocked_scan["scan_result"].eq("PASS").all() else "FAIL"
    leakage_status = "PASS" if leakage_scan["scan_result"].eq("PASS").all() else "FAIL"
    lines = [
        "# Overnight Model Tune V1 Expanded Pre-Run Summary",
        "",
        "Local-only pre-run validation. This does not approve private value, rankings, "
        "Mock Draft behavior, simulations, final draft advice, deployment, "
        "`latest_candidate`, or `latest_approved`.",
        "",
        f"- Planned total fits: `{manifest['planned_fit_count']}`",
        f"- Fits by position: `{manifest['planned_fit_count_by_position']}`",
        f"- Fits by model family: `{manifest['planned_fit_count_by_model_family']}`",
        f"- Fits by feature family: `{manifest['planned_fit_count_by_feature_family']}`",
        f"- Vendor ready: `{vendor['ready']}`",
        f"- Vendor feature columns: `{len(vendor['feature_columns'])}`",
        f"- Blocked-field scan: `{blocked_status}`",
        f"- Leakage pre-check: `{leakage_status}`",
        "- Expected runtime: larger than V0; bounded by 480 minutes and checkpointed.",
        "",
        "This is not the V0 small grid: V1 uses explicit hyperparameter grids, "
        "tree families, gradient boosting, phase-2 deepening, phase-3 stability "
        "stress rows, ablations, snap-fixed/no-snap controls, and actual joined "
        "vendor challenger features.",
    ]
    return "\n".join(lines) + "\n"


def _vendor_readiness_markdown(
    coverage: pd.DataFrame, fields: pd.DataFrame, blocked: pd.DataFrame, ready: bool
) -> str:
    lines = [
        "# Vendor Feature Readiness",
        "",
        "Local-only vendor challenger readiness. Raw vendor rows are not copied into repo docs.",
        "",
        f"- Ready for V1 run: `{ready}`",
        f"- Classified allowed fields: `{len(fields)}`",
        f"- Blocked vendor fields: `{len(blocked)}`",
        "",
        "## Coverage",
        "",
        "| Family | Position | Rows | Joined | Coverage |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for _, row in coverage.sort_values(["vendor_family", "position"]).iterrows():
        lines.append(
            f"| `{row['vendor_family']}` | `{row['position']}` | {int(row['total_rows'])} | "
            f"{int(row['joined_rows'])} | {row['coverage_rate']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def _v0_small_grid_diagnosis() -> str:
    return """# V0 Small Grid Diagnosis

V0 finished in roughly 56 seconds because it used a tiny finite grid:

- four safe feature variants by position
- four model names
- fixed hyperparameters for each sklearn model family
- no phase-2 deepening
- no phase-3 stability stress tests
- no actual vendor feature join

The V0 run produced 64 position-level result rows, which is useful as a smoke
test but not a meaningful overnight search. Vendor challenger rows were skipped
because the V0 variant plan marked them as planned local-only research rows
without model-ready joined feature columns.

V1 changes required before a full run:

- build actual vendor challenger feature tables from local canonical archives
- require nonzero vendor join coverage before full V1 run
- create a pre-run grid manifest with at least 500 planned position-level fits
- include expanded hyperparameter grids and multiple model families
- include phase-2 deepening and phase-3 stability stress configurations
- block startup if the grid collapses back to a V0-sized run
"""


def _fit_id(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row["phase"]),
            str(row["variant_id"]),
            str(row["position"]),
            str(row["model_name"]),
            str(row["hyperparameters_json"]),
        ]
    )


def _split_fantasypros_player(value: Any) -> list[str]:
    text = str(value).strip()
    match = re.match(r"^(.*)\s+([A-Z]{2,3})$", text)
    if not match:
        return [text, ""]
    return [match.group(1).strip(), match.group(2).strip()]


def _to_number(value: Any) -> float:
    if pd.isna(value):
        return math.nan
    text = str(value).replace(",", "").replace("%", "").strip()
    if text in {"", "-", "--"}:
        return math.nan
    try:
        return float(text)
    except ValueError:
        return math.nan


def _norm_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _norm_col(value: Any) -> str:
    text = str(value).strip().lower()
    for char in (" ", "-", "/", "%", "."):
        text = text.replace(char, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


if __name__ == "__main__":
    raise SystemExit(main())
