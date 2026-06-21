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

from scripts.build_backtest_dataset_v0 import CORE_POSITIONS
from scripts.build_backtest_dataset_v1 import (
    V1_BASELINE_FEATURES_BY_POSITION,
    V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
)

DEFAULT_INPUT_DATASET_DIR = Path(
    r"C:\NWR_SHARED_DATA\backtests\backtest_v1_feature_cleanup_20260621"
)
DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v0_20260621")
DEFAULT_VENDOR_ARCHIVE_ROOT = Path(
    r"C:\NWR_SHARED_DATA\vendor_archive_recovery\rotowire_fantasypros_stats_organized_20260621_v2"
)
DEFAULT_SNAP_AUDIT_DOC = Path(r"docs\hq\parallel_lanes\NWR_BACKTEST_V1_SNAP_JOIN_AUDIT_20260621.md")

IDENTITY_COLUMNS = {
    "player_id",
    "feature_season",
    "target_season",
    "player_name",
    "position",
    "recent_team",
}
LABEL_COLUMNS = {
    "target_player_name",
    "target_position",
    "target_team",
    "target_games",
    "next_nwr_points",
    "next_nwr_ppg",
}
SNAP_COLUMNS = {"offense_snaps", "offense_pct", "snap_pct_missing"}

FEATURE_FAMILIES = (
    "SAFE_BASELINE",
    "SAFE_EXPANDED",
    "SAFE_NO_SNAP",
    "SAFE_SNAP_FIXED",
    "YELLOW_CHALLENGER",
    "VENDOR_YELLOW_CHALLENGER",
    "BLOCKED",
)

BLOCKED_FIELD_PATTERNS = (
    "adp",
    "ecr",
    "ranking",
    "rankings",
    "projection",
    "projected",
    "fantasy_points",
    "fantasy_points_ppr",
    "trade_calculator",
    "trade_value",
    "market",
    "private_value",
    "hidden_sort",
    "fantasypros_rk",
    "fantasypros_rtg",
    "rotowire_qbr",
    "rotowire_rating",
)
BLOCKED_EXACT_FIELDS = {
    "adp",
    "ecr",
    "rk",
    "rtg",
    "rank",
    "rating",
    "qbr",
    "fantasy_points",
    "fantasy_points_ppr",
}

VENDOR_CHALLENGER_FAMILIES = [
    {
        "variant_id": "vendor_rotowire_receiving_routes_yellow",
        "position": "WR",
        "candidate_fields": [
            "routes_run",
            "tprr_pct",
            "yprr",
            "team_target_pct",
            "team_air_yards_pct",
            "yac_pct",
        ],
        "description": (
            "RotoWire route and advanced receiving role fields; isolated YELLOW "
            "research only."
        ),
    },
    {
        "variant_id": "vendor_rotowire_receiving_routes_yellow",
        "position": "TE",
        "candidate_fields": [
            "routes_run",
            "tprr_pct",
            "yprr",
            "team_target_pct",
            "team_air_yards_pct",
            "yac_pct",
        ],
        "description": (
            "RotoWire route and advanced receiving role fields; isolated YELLOW "
            "research only."
        ),
    },
    {
        "variant_id": "vendor_rotowire_redzone_yellow",
        "position": "QB",
        "candidate_fields": ["red_zone_attempts", "red_zone_completions", "red_zone_tds"],
        "description": (
            "RotoWire red-zone usage fields when definitions are clear; isolated "
            "YELLOW research only."
        ),
    },
    {
        "variant_id": "vendor_rotowire_redzone_yellow",
        "position": "RB",
        "candidate_fields": ["red_zone_carries", "goal_line_carries", "red_zone_tds"],
        "description": (
            "RotoWire red-zone and goal-line usage fields; isolated YELLOW "
            "research only."
        ),
    },
    {
        "variant_id": "vendor_rotowire_rushing_advanced_yellow",
        "position": "RB",
        "candidate_fields": ["yards_after_contact", "broken_tackles", "goal_line_carries"],
        "description": (
            "RotoWire rushing advanced fields when definitions are clear; isolated "
            "YELLOW research only."
        ),
    },
    {
        "variant_id": "vendor_fantasypros_factual_advanced_yellow",
        "position": "QB",
        "candidate_fields": ["advanced_factual_non_rank_fields_only"],
        "description": (
            "FantasyPros factual advanced fields only; RK, RTG, ranks, ratings, "
            "and scores blocked."
        ),
    },
]


class OvernightTuneBuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class OvernightTuneDatasetResult:
    output_root: Path
    feature_registry_path: Path
    blocked_registry_path: Path
    variant_plan_path: Path
    manifest_path: Path
    snap_status: str
    vendor_archive_status: str


def build_overnight_tune_dataset_v0(
    *,
    input_dataset_dir: Path = DEFAULT_INPUT_DATASET_DIR,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    vendor_archive_root: Path = DEFAULT_VENDOR_ARCHIVE_ROOT,
    snap_audit_doc: Path = DEFAULT_SNAP_AUDIT_DOC,
) -> OvernightTuneDatasetResult:
    output_root.mkdir(parents=True, exist_ok=True)
    baseline = _read_required_csv(input_dataset_dir / "feature_dataset_v1_baseline.csv")
    clean_expanded = _read_required_csv(input_dataset_dir / "feature_dataset_v1_clean_expanded.csv")
    labels = _read_required_csv(input_dataset_dir / "labels_v1.csv")
    _validate_required_inputs(baseline, clean_expanded, labels)

    snap_summary = _snap_summary(clean_expanded, snap_audit_doc)
    vendor_archive_status = "available" if vendor_archive_root.exists() else "missing"
    feature_registry = _feature_registry(baseline, clean_expanded, snap_summary["status"])
    blocked_registry = _blocked_registry()
    variant_plan = _variant_plan(baseline, clean_expanded, snap_summary)

    feature_registry_path = output_root / "feature_registry_v0.csv"
    blocked_registry_path = output_root / "blocked_field_registry_v0.csv"
    variant_plan_path = output_root / "dataset_variant_plan_v0.csv"
    manifest_path = output_root / "tune_input_manifest_v0.json"

    _write_csv(feature_registry_path, feature_registry)
    _write_csv(blocked_registry_path, blocked_registry)
    _write_csv(variant_plan_path, variant_plan)

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "purpose": "local_only_overnight_model_tune_v0_readiness_scaffold",
        "approval_status": "dry_run_scaffold_only_not_model_approved",
        "input_dataset_dir": str(input_dataset_dir),
        "output_root": str(output_root),
        "vendor_archive_root": str(vendor_archive_root),
        "vendor_archive_status": vendor_archive_status,
        "snap_status": snap_summary,
        "positions": list(CORE_POSITIONS),
        "evaluation_seasons": [2021, 2022, 2023, 2024, 2025],
        "feature_families": list(FEATURE_FAMILIES),
        "blocked_field_patterns": list(BLOCKED_FIELD_PATTERNS),
        "blocked_exact_fields": sorted(BLOCKED_EXACT_FIELDS),
        "local_only_outputs": [
            "feature_registry_v0.csv",
            "blocked_field_registry_v0.csv",
            "dataset_variant_plan_v0.csv",
            "dry_run_predictions.csv",
            "dry_run_metrics_by_position.csv",
            "dry_run_metrics_by_year.csv",
            "dry_run_winner_report.csv",
            "OVERNIGHT_TUNE_V0_DRY_RUN_REPORT.md",
        ],
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
        "files": {
            path.name: _file_record(path)
            for path in (feature_registry_path, blocked_registry_path, variant_plan_path)
        },
    }
    _write_json(manifest_path, manifest)
    return OvernightTuneDatasetResult(
        output_root=output_root,
        feature_registry_path=feature_registry_path,
        blocked_registry_path=blocked_registry_path,
        variant_plan_path=variant_plan_path,
        manifest_path=manifest_path,
        snap_status=str(snap_summary["status"]),
        vendor_archive_status=vendor_archive_status,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build local-only Overnight Model Tune V0 registries and variant plan."
    )
    parser.add_argument("--input-dataset-dir", type=Path, default=DEFAULT_INPUT_DATASET_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--vendor-archive-root", type=Path, default=DEFAULT_VENDOR_ARCHIVE_ROOT)
    parser.add_argument("--snap-audit-doc", type=Path, default=DEFAULT_SNAP_AUDIT_DOC)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build_overnight_tune_dataset_v0(
            input_dataset_dir=args.input_dataset_dir,
            output_root=args.output_root,
            vendor_archive_root=args.vendor_archive_root,
            snap_audit_doc=args.snap_audit_doc,
        )
    except Exception as exc:
        print(
            f"Overnight Tune V0 dataset scaffold failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    print(f"output_root={result.output_root}")
    print(f"feature_registry={result.feature_registry_path}")
    print(f"blocked_registry={result.blocked_registry_path}")
    print(f"variant_plan={result.variant_plan_path}")
    print(f"manifest={result.manifest_path}")
    print(f"snap_status={result.snap_status}")
    print(f"vendor_archive_status={result.vendor_archive_status}")
    return 0


def _read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise OvernightTuneBuildError(f"missing required input CSV: {path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise OvernightTuneBuildError(f"required input CSV is empty: {path}")
    return frame


def _validate_required_inputs(
    baseline: pd.DataFrame, clean_expanded: pd.DataFrame, labels: pd.DataFrame
) -> None:
    for name, frame in {"baseline": baseline, "clean_expanded": clean_expanded}.items():
        missing_identity = sorted(IDENTITY_COLUMNS.difference(frame.columns))
        if missing_identity:
            raise OvernightTuneBuildError(f"{name} missing identity columns: {missing_identity}")
        _scan_blocked_columns(
            [column for column in frame.columns if column not in IDENTITY_COLUMNS],
            context=name,
        )
    missing_labels = sorted(
        {"player_id", "target_season"}.union(LABEL_COLUMNS).difference(labels.columns)
    )
    if missing_labels:
        raise OvernightTuneBuildError(f"labels missing columns: {missing_labels}")


def _snap_summary(clean_expanded: pd.DataFrame, snap_audit_doc: Path) -> dict[str, Any]:
    has_audit_doc = snap_audit_doc.exists()
    has_snap_columns = {"offense_snaps", "offense_pct"}.issubset(clean_expanded.columns)
    rows: list[dict[str, Any]] = []
    if has_snap_columns:
        for position, group in clean_expanded.groupby("position"):
            populated = pd.to_numeric(group["offense_snaps"], errors="coerce").fillna(0).gt(
                0
            ) | pd.to_numeric(group["offense_pct"], errors="coerce").fillna(0).gt(0)
            rows.append(
                {
                    "position": position,
                    "rows": int(len(group)),
                    "populated_rows": int(populated.sum()),
                    "coverage_rate": float(populated.mean()) if len(group) else 0.0,
                }
            )
    min_coverage = min((row["coverage_rate"] for row in rows), default=0.0)
    if has_audit_doc and has_snap_columns and min_coverage >= 0.5:
        status = "snap_fixed_available"
    elif has_audit_doc and has_snap_columns:
        status = "snap_fixed_supported_regeneration_required"
    elif has_audit_doc:
        status = "snap_fix_doc_present_but_current_artifact_missing_snap_columns"
    else:
        status = "snap_unresolved_yellow"
    return {
        "status": status,
        "snap_audit_doc_present": has_audit_doc,
        "current_artifact_has_snap_columns": has_snap_columns,
        "current_artifact_coverage_by_position": rows,
        "minimum_position_coverage_rate": min_coverage,
    }


def _feature_registry(
    baseline: pd.DataFrame, clean_expanded: pd.DataFrame, snap_status: str
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.extend(
        _registry_rows(
            family="SAFE_BASELINE",
            source_variant="safe_baseline",
            source_frame=baseline,
            mapping=V1_BASELINE_FEATURES_BY_POSITION,
            status="ready",
        )
    )
    rows.extend(
        _registry_rows(
            family="SAFE_EXPANDED",
            source_variant="safe_expanded",
            source_frame=clean_expanded,
            mapping=V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
            status="ready",
        )
    )
    no_snap_mapping = {
        position: [feature for feature in features if feature not in SNAP_COLUMNS]
        for position, features in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION.items()
    }
    rows.extend(
        _registry_rows(
            family="SAFE_NO_SNAP",
            source_variant="safe_no_snap",
            source_frame=clean_expanded,
            mapping=no_snap_mapping,
            status="ready",
        )
    )
    snap_status_label = (
        "ready"
        if snap_status == "snap_fixed_available"
        else "requires_regenerated_snap_fixed_dataset"
    )
    rows.extend(
        _registry_rows(
            family="SAFE_SNAP_FIXED",
            source_variant="safe_snap_fixed",
            source_frame=clean_expanded,
            mapping=V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
            status=snap_status_label,
        )
    )
    for item in VENDOR_CHALLENGER_FAMILIES:
        for feature in item["candidate_fields"]:
            rows.append(
                {
                    "feature_family": "VENDOR_YELLOW_CHALLENGER",
                    "variant_id": item["variant_id"],
                    "position": item["position"],
                    "feature": feature,
                    "available_in_current_dataset": False,
                    "status": "isolated_research_only_not_safe_model_input",
                    "reason": item["description"],
                }
            )
    rows.append(
        {
            "feature_family": "YELLOW_CHALLENGER",
            "variant_id": "non_vendor_yellow_challenger_placeholder",
            "position": "ALL",
            "feature": "epa_cpoe_wopr_expected_share_family",
            "available_in_current_dataset": False,
            "status": "planned_research_only_not_primary_safe_input",
            "reason": "advanced non-vendor challenger family reserved for isolated tests only",
        }
    )
    for _, row in _blocked_registry().iterrows():
        rows.append(
            {
                "feature_family": "BLOCKED",
                "variant_id": "blocked_fields",
                "position": "ALL",
                "feature": row["field_or_pattern"],
                "available_in_current_dataset": False,
                "status": "blocked",
                "reason": row["reason"],
            }
        )
    return pd.DataFrame(rows)


def _registry_rows(
    *,
    family: str,
    source_variant: str,
    source_frame: pd.DataFrame,
    mapping: dict[str, list[str]],
    status: str,
) -> list[dict[str, Any]]:
    rows = []
    for position in CORE_POSITIONS:
        for feature in mapping[position]:
            rows.append(
                {
                    "feature_family": family,
                    "variant_id": source_variant,
                    "position": position,
                    "feature": feature,
                    "available_in_current_dataset": feature in source_frame.columns,
                    "status": status,
                    "reason": _feature_reason(feature, family),
                }
            )
    return rows


def _variant_plan(
    baseline: pd.DataFrame, clean_expanded: pd.DataFrame, snap_summary: dict[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    variant_specs = [
        (
            "safe_baseline",
            "SAFE_BASELINE",
            "feature_dataset_v1_baseline.csv",
            V1_BASELINE_FEATURES_BY_POSITION,
            True,
            "safe baseline V1 feature set",
        ),
        (
            "safe_expanded",
            "SAFE_EXPANDED",
            "feature_dataset_v1_clean_expanded.csv",
            V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
            True,
            "safe expanded factual V1 feature set",
        ),
        (
            "safe_no_snap",
            "SAFE_NO_SNAP",
            "feature_dataset_v1_clean_expanded.csv",
            {
                position: [feature for feature in features if feature not in SNAP_COLUMNS]
                for position, features in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION.items()
            },
            True,
            "safe expanded features with snap fields removed",
        ),
        (
            "safe_snap_fixed",
            "SAFE_SNAP_FIXED",
            "feature_dataset_v1_clean_expanded.csv",
            V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
            snap_summary["status"] == "snap_fixed_available",
            "snap-fixed feature set; requires regenerated artifact if current snap coverage is low",
        ),
    ]
    source_frames = {
        "feature_dataset_v1_baseline.csv": baseline,
        "feature_dataset_v1_clean_expanded.csv": clean_expanded,
    }
    for variant_id, family, source_file, mapping, include, description in variant_specs:
        frame = source_frames[source_file]
        for position in CORE_POSITIONS:
            columns = [feature for feature in mapping[position] if feature in frame.columns]
            _scan_blocked_columns(columns, context=f"{variant_id}:{position}")
            rows.append(
                {
                    "variant_id": variant_id,
                    "feature_family": family,
                    "position": position,
                    "source_dataset": source_file,
                    "feature_columns_json": json.dumps(columns),
                    "feature_count": len(columns),
                    "include_in_dry_run": include,
                    "status": "ready" if include else "planned_not_ready",
                    "requires_vendor_join": False,
                    "requires_regenerated_snap_dataset": variant_id == "safe_snap_fixed"
                    and snap_summary["status"] != "snap_fixed_available",
                    "candidate_label_allowed": "SAFE_CANDIDATE_REPORT_ONLY",
                    "description": description,
                }
            )
    for item in VENDOR_CHALLENGER_FAMILIES:
        rows.append(
            {
                "variant_id": item["variant_id"],
                "feature_family": "VENDOR_YELLOW_CHALLENGER",
                "position": item["position"],
                "source_dataset": "vendor_archive_local_only_not_joined",
                "feature_columns_json": json.dumps(item["candidate_fields"]),
                "feature_count": len(item["candidate_fields"]),
                "include_in_dry_run": False,
                "status": "planned_isolated_yellow_research_only",
                "requires_vendor_join": True,
                "requires_regenerated_snap_dataset": False,
                "candidate_label_allowed": "VENDOR_RESEARCH_CANDIDATE_ONLY",
                "description": item["description"],
            }
        )
    return pd.DataFrame(rows)


def _blocked_registry() -> pd.DataFrame:
    rows = [
        ("ADP", "market/ranking signal blocked as model input"),
        ("ECR", "expert consensus ranking blocked as market/ranking input"),
        ("rankings", "ranking fields blocked"),
        ("projections", "projection fields blocked"),
        ("trade values/calculators", "trade market fields blocked"),
        ("market values", "market fields blocked"),
        ("fantasy_points", "target/leakage field blocked as input"),
        ("fantasy_points_ppr", "target/leakage field blocked as input"),
        ("private value fields", "private value fields blocked"),
        ("hidden sort fields", "hidden sorting fields blocked"),
        ("RotoWire QBR/rating", "ranking-like or unclear aggregate blocked pending source review"),
        ("FantasyPros RK", "vendor rank field blocked"),
        ("FantasyPros RTG", "vendor rating field blocked"),
        (
            "vendor rank/rating/score/aggregate",
            "unclear vendor aggregates blocked pending definition review",
        ),
    ]
    return pd.DataFrame(
        {"field_or_pattern": field, "feature_family": "BLOCKED", "reason": reason}
        for field, reason in rows
    )


def _scan_blocked_columns(columns: list[str], *, context: str) -> None:
    for column in columns:
        reason = blocked_field_reason(column)
        if reason:
            raise OvernightTuneBuildError(f"blocked field in {context}: {column} ({reason})")


def blocked_field_reason(column: str) -> str | None:
    normalized = _normalize_column(column)
    if normalized in BLOCKED_EXACT_FIELDS:
        return "exact blocked field"
    for pattern in BLOCKED_FIELD_PATTERNS:
        if pattern in normalized:
            return f"matched blocked pattern '{pattern}'"
    if normalized.endswith("_rk") or normalized.endswith("_rtg"):
        return "vendor rank/rating suffix blocked"
    return None


def _normalize_column(column: str) -> str:
    normalized = str(column).strip().lower()
    for char in (" ", "-", "/", "%", "."):
        normalized = normalized.replace(char, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _feature_reason(feature: str, family: str) -> str:
    if family == "SAFE_NO_SNAP":
        return "safe factual V1 feature with snap columns excluded"
    if feature in SNAP_COLUMNS:
        return "snap feature; safe only after regenerated snap-fixed dataset coverage is verified"
    return "safe factual historical feature from nflverse/Sleeper pipeline"


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_record(path: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {
        "path": str(path),
        "row_count": _csv_row_count(path) if path.suffix.lower() == ".csv" else None,
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


if __name__ == "__main__":
    raise SystemExit(main())
