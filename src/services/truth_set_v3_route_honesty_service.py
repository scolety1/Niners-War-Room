from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.truth_set_v3_usage_derivation_service import DEFAULT_REPORT_ROOT

ROUTE_HONESTY_HEADER = (
    "field_name",
    "requested_model_concept",
    "source_status",
    "free_public_status",
    "can_score_as_real_evidence",
    "allowed_proxy_fields",
    "confidence_effect",
    "notes",
)

ROUTE_HONESTY_SUMMARY_HEADER = ("metric", "value")

ROUTE_HONESTY_ROWS: tuple[dict[str, object], ...] = (
    {
        "field_name": "routes_run",
        "requested_model_concept": "true player routes run",
        "source_status": "unavailable_free_public",
        "free_public_status": "not available in current structured free source stack",
        "can_score_as_real_evidence": False,
        "allowed_proxy_fields": "snap_share|target_share",
        "confidence_effect": "lower role/usage confidence for route-dependent WR/TE calls",
        "notes": "Do not infer routes from snaps or targets.",
    },
    {
        "field_name": "route_participation",
        "requested_model_concept": "routes per team dropback/pass play",
        "source_status": "unavailable_free_public",
        "free_public_status": "not available in current structured free source stack",
        "can_score_as_real_evidence": False,
        "allowed_proxy_fields": "snap_share|target_share",
        "confidence_effect": "lower role/usage confidence for route-dependent WR/TE calls",
        "notes": "nflverse participation route tags are not a true route denominator.",
    },
    {
        "field_name": "targets_per_route_run",
        "requested_model_concept": "TPRR",
        "source_status": "missing_paid_or_charted_data",
        "free_public_status": "requires true routes run denominator",
        "can_score_as_real_evidence": False,
        "allowed_proxy_fields": "target_share|targets_per_game",
        "confidence_effect": "keep as review gap until legal charted route data exists",
        "notes": "Do not divide targets by snap counts and call it TPRR.",
    },
    {
        "field_name": "yards_per_route_run",
        "requested_model_concept": "YPRR",
        "source_status": "missing_paid_or_charted_data",
        "free_public_status": "requires true routes run denominator",
        "can_score_as_real_evidence": False,
        "allowed_proxy_fields": "receiving_yards|target_share|air_yards_share",
        "confidence_effect": "keep as review gap until legal charted route data exists",
        "notes": "Do not divide yards by snap counts and call it YPRR.",
    },
    {
        "field_name": "snap_target_route_proxy",
        "requested_model_concept": "route-context fallback",
        "source_status": "proxy_only_snap_target",
        "free_public_status": "available from nflverse snap counts and player stats",
        "can_score_as_real_evidence": False,
        "allowed_proxy_fields": "snap_share|target_share|targets_per_game|air_yards_share",
        "confidence_effect": "usable as proxy/context, not proof of route participation",
        "notes": "Proxy can explain uncertainty; it must not unlock full route confidence.",
    },
)


def route_honesty_rows() -> tuple[dict[str, object], ...]:
    return ROUTE_HONESTY_ROWS


def route_honesty_summary_rows() -> tuple[dict[str, object], ...]:
    unavailable = sum(
        1
        for row in ROUTE_HONESTY_ROWS
        if row["source_status"] in {"unavailable_free_public", "missing_paid_or_charted_data"}
    )
    proxy = sum(1 for row in ROUTE_HONESTY_ROWS if row["source_status"] == "proxy_only_snap_target")
    return (
        {"metric": "status", "value": "ready"},
        {"metric": "review_status", "value": "review_only"},
        {"metric": "route_fields_unavailable_or_missing", "value": unavailable},
        {"metric": "proxy_fields_available", "value": proxy},
        {"metric": "active_rankings_overwritten", "value": False},
        {"metric": "model_scores_changed", "value": False},
    )


def write_route_honesty_outputs(
    output_root: str | Path = DEFAULT_REPORT_ROOT,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "rows": root / "truth_set_v3_route_data_honesty.csv",
        "summary_csv": root / "truth_set_v3_route_data_honesty_summary.csv",
        "summary_json": root / "truth_set_v3_route_data_honesty_summary.json",
    }
    _write_csv(paths["rows"], ROUTE_HONESTY_HEADER, ROUTE_HONESTY_ROWS)
    summary_rows = route_honesty_summary_rows()
    _write_csv(paths["summary_csv"], ROUTE_HONESTY_SUMMARY_HEADER, summary_rows)
    paths["summary_json"].write_text(
        json.dumps({str(row["metric"]): row["value"] for row in summary_rows}, indent=2),
        encoding="utf-8",
    )
    return paths


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
