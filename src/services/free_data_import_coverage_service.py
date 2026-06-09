from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.nflverse_player_stats_import_service import (
    official_player_stats_source_rows,
)
from src.services.nflverse_raw_import_service import (
    RAW_NFLVERSE_FILES,
    validate_nflverse_raw_imports,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

FREE_DATA_BUCKETS = (
    "production",
    "opportunity",
    "role/usage",
    "first-down/TD fit",
    "age/bio",
    "injury",
    "identity",
    "projection",
    "market/liquidity",
)

FREE_DATA_COVERAGE_CONTRACT: dict[str, dict[str, object]] = {
    "production": {
        "support_status": "direct_free_import",
        "support_level": "direct",
        "local_files": ("nflverse_player_stats_weekly.csv",),
        "required_fields": (
            "passing_yards",
            "passing_tds",
            "interceptions",
            "rushing_attempts",
            "rushing_yards",
            "rushing_tds",
            "targets",
            "receptions",
            "receiving_yards",
            "receiving_tds",
        ),
        "free_sources": "nflverse player stats",
        "import_services": "nflverse_player_stats_import_service|lve_scoring_derivation_service",
        "model_usage": "historical LVE weekly and recent production features",
        "limitations": "Historical evidence only; not a forward projection.",
    },
    "opportunity": {
        "support_status": "partial_free_import",
        "support_level": "partial",
        "local_files": (
            "nflverse_player_stats_weekly.csv",
            "nflverse_participation_player_weekly.csv",
        ),
        "required_fields": (
            "targets",
            "rushing_attempts",
            "target_share",
            "air_yards_share",
            "wopr",
            "receiving_air_yards",
            "red_zone_on_field",
            "short_yardage_on_field",
        ),
        "free_sources": "nflverse player stats plus local participation proxy",
        "import_services": "nflverse_player_stats_import_service|lve_role_usage_service",
        "model_usage": "target earning, workload earning, air-yards/WOPR context",
        "limitations": (
            "Expected fantasy/opportunity model fields are not fully imported from a "
            "free direct adapter yet; participation rows may be proxy/manual."
        ),
    },
    "role/usage": {
        "support_status": "partial_free_import",
        "support_level": "partial",
        "local_files": (
            "nflverse_snap_counts_weekly.csv",
            "nflverse_depth_chart_weekly.csv",
            "nflverse_participation_player_weekly.csv",
        ),
        "required_fields": (
            "offense_snaps",
            "offense_pct",
            "pos_rank",
            "depth_chart_role_score",
            "route_participation_proxy",
            "targets_per_dropback_snap_proxy",
        ),
        "free_sources": "nflverse snap counts and depth charts; participation proxy if supplied",
        "import_services": "nflverse_player_stats_import_service|lve_role_usage_service",
        "model_usage": "role security, starter weeks, route/workload proxies",
        "limitations": (
            "Snap/depth are direct. Route participation is a local proxy contract, "
            "not a guaranteed direct free nflverse stat."
        ),
    },
    "first-down/TD fit": {
        "support_status": "direct_free_import",
        "support_level": "direct",
        "local_files": ("nflverse_player_stats_weekly.csv",),
        "required_fields": (
            "rushing_first_downs",
            "receiving_first_downs",
            "rushing_tds",
            "receiving_tds",
            "targets",
            "rushing_attempts",
        ),
        "free_sources": "nflverse player stats",
        "import_services": "nflverse_player_stats_import_service|lve_scoring_derivation_service",
        "model_usage": "LVE first-down bonus and TD scoring fit",
        "limitations": "No passing first-down bonus is used by LVE scoring.",
    },
    "age/bio": {
        "support_status": "direct_free_import",
        "support_level": "direct",
        "local_files": ("nflverse_identity_map.csv",),
        "required_fields": (
            "sleeper_id",
            "gsis_id",
            "player_id",
            "player_name",
            "position",
            "team",
        ),
        "free_sources": "Sleeper player universe, nflverse players, DynastyProcess/nflreadr IDs",
        "import_services": "nflverse_identity_service|identity_audit_service",
        "model_usage": "age/bio linkage, lifecycle, draft-year joins, team/position review",
        "limitations": (
            "The local identity-map template does not currently store birth date directly; "
            "age is carried through player/model input rows after identity review."
        ),
    },
    "injury": {
        "support_status": "direct_free_import",
        "support_level": "direct",
        "local_files": ("nflverse_injuries_weekly.csv",),
        "required_fields": (
            "report_primary_injury",
            "report_status",
            "practice_primary_injury",
            "practice_status",
            "normalized_body_part",
            "source_confidence",
        ),
        "free_sources": "nflverse injuries plus Sleeper current status where available",
        "import_services": "lve_injury_durability_service",
        "model_usage": "durability confidence and injury risk features",
        "limitations": "Recurrence and body-part normalization remain conservative proxies.",
    },
    "identity": {
        "support_status": "direct_free_import",
        "support_level": "direct",
        "local_files": ("nflverse_identity_map.csv",),
        "required_fields": (
            "sleeper_id",
            "gsis_id",
            "nfl_id",
            "espn_id",
            "fantasy_data_id",
            "pfr_id",
            "player_id",
            "match_method",
            "match_confidence",
            "review_status",
        ),
        "free_sources": "Sleeper API, nflverse players, DynastyProcess/nflreadr IDs",
        "import_services": "nflverse_identity_service|identity_audit_service",
        "model_usage": "blocks or permits trusted joins into stats-first rows",
        "limitations": "Ambiguous/name-only matches stay review-only.",
    },
    "projection": {
        "support_status": "external_csv_required",
        "support_level": "external",
        "local_files": ("projection_raw_import.csv",),
        "required_fields": (
            "projected_games",
            "projected_starts",
            "projected_passing_yards",
            "projected_passing_tds",
            "projected_interceptions",
            "projected_rushing_attempts",
            "projected_rushing_yards",
            "projected_rushing_tds",
            "projected_targets",
            "projected_receiving_yards",
            "projected_receiving_tds",
            "projected_rushing_first_downs",
            "projected_receiving_first_downs",
        ),
        "free_sources": "user-provided free/exportable projection CSV",
        "import_services": "lve_projection_import_service",
        "model_usage": "LVE-rescored projection feature after explicit import",
        "limitations": (
            "No built-in free projection feed is downloaded by this adapter. Missing first "
            "downs are estimated and penalized when a projection CSV is supplied."
        ),
    },
    "market/liquidity": {
        "support_status": "review_only_or_external",
        "support_level": "external",
        "local_files": (),
        "required_fields": (),
        "free_sources": "DynastyProcess/FantasyCalc-style exports when legally supplied",
        "import_services": "public_source_import_service",
        "model_usage": "trade liquidity only; locked out of private/stat value",
        "limitations": "Not required for private value and should never replace football stats.",
    },
}


@dataclass(frozen=True)
class FreeDataImportCoverageReport:
    coverage_rows: tuple[dict[str, object], ...]
    field_rows: tuple[dict[str, object], ...]
    adapter_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    issues: tuple[str, ...]
    raw_import_status: str
    raw_import_root: str


def build_free_data_import_coverage_matrix(
    raw_import_root: str | Path = "templates/real_data_inputs/nflverse_stats_upgrade",
) -> FreeDataImportCoverageReport:
    root = Path(raw_import_root)
    raw_report = validate_nflverse_raw_imports(root)
    coverage_rows = tuple(
        _coverage_row(bucket, contract, root, raw_report.row_counts)
        for bucket, contract in FREE_DATA_COVERAGE_CONTRACT.items()
    )
    field_rows = tuple(
        field_row
        for bucket, contract in FREE_DATA_COVERAGE_CONTRACT.items()
        for field_row in _field_rows(bucket, contract)
    )
    adapter_rows = tuple(_adapter_rows(raw_report.row_counts))
    summary_rows = tuple(_summary_rows(coverage_rows))
    issues = tuple(_coverage_issues(coverage_rows, raw_report))
    return FreeDataImportCoverageReport(
        coverage_rows=coverage_rows,
        field_rows=field_rows,
        adapter_rows=adapter_rows,
        summary_rows=summary_rows,
        issues=issues,
        raw_import_status=raw_report.status,
        raw_import_root=str(root),
    )


def write_free_data_import_coverage_matrix(
    export_dir: str | Path,
    report: FreeDataImportCoverageReport,
) -> dict[str, Path]:
    root = Path(export_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "coverage_matrix": root / "free_data_coverage_matrix.csv",
        "field_matrix": root / "free_data_field_matrix.csv",
        "adapter_matrix": root / "free_data_adapter_matrix.csv",
        "summary": root / "free_data_coverage_summary.csv",
    }
    _write_csv(paths["coverage_matrix"], report.coverage_rows)
    _write_csv(paths["field_matrix"], report.field_rows)
    _write_csv(paths["adapter_matrix"], report.adapter_rows)
    _write_csv(paths["summary"], report.summary_rows)
    return paths


def _coverage_row(
    bucket: str,
    contract: dict[str, object],
    root: Path,
    row_counts: dict[str, int],
) -> dict[str, object]:
    local_files = tuple(str(file_name) for file_name in contract["local_files"])
    required_fields = tuple(str(field) for field in contract["required_fields"])
    missing_files = [
        file_name
        for file_name in local_files
        if file_name in RAW_NFLVERSE_FILES and not (root / file_name).exists()
    ]
    headers = {file_name: _local_header(root, file_name) for file_name in local_files}
    missing_fields = [
        field
        for field in required_fields
        if not any(field in header for header in headers.values())
    ]
    row_count_summary = "|".join(
        f"{file_name}:{row_counts.get(file_name, 0)}"
        for file_name in local_files
        if file_name in row_counts
    )
    contract_ok = not missing_files and not missing_fields
    if not contract_ok:
        validation_status = "blocked"
    elif contract["support_status"] == "direct_free_import":
        validation_status = "ready"
    elif contract["support_status"] == "partial_free_import":
        validation_status = "review"
    else:
        validation_status = "external_required"
    return {
        "feature_bucket": bucket,
        "support_status": contract["support_status"],
        "support_level": contract["support_level"],
        "validation_status": validation_status,
        "free_public_sources": contract["free_sources"],
        "local_files": "|".join(local_files),
        "required_fields": "|".join(required_fields),
        "row_counts": row_count_summary,
        "missing_files": "|".join(missing_files),
        "missing_fields": "|".join(missing_fields),
        "import_services": contract["import_services"],
        "model_usage": contract["model_usage"],
        "limitations": contract["limitations"],
        "scoring_effect": "none until reviewed/derived/applied; no formula tuning",
        "next_action": _next_action(str(validation_status), bucket),
    }


def _field_rows(
    bucket: str,
    contract: dict[str, object],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    local_files = tuple(str(name) for name in contract["local_files"])
    headers = {
        file_name: NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS.get(file_name, ())
        for file_name in local_files
    }
    for field in tuple(str(field) for field in contract["required_fields"]):
        candidate_files = [
            file_name
            for file_name, header in headers.items()
            if field in header
        ]
        for file_name in candidate_files or [""]:
            rows.append(
                {
                    "feature_bucket": bucket,
                    "local_file": file_name,
                    "field": field,
                    "template_column_present": bool(candidate_files),
                    "source_status": (
                        "import_contract_field" if candidate_files else "missing_contract_field"
                    ),
                    "support_status": contract["support_status"],
                    "support_level": contract["support_level"],
                }
            )
    if not rows:
        rows.append(
            {
                "feature_bucket": bucket,
                "local_file": "",
                "field": "",
                "template_column_present": False,
                "source_status": "no_local_free_contract",
                "support_status": contract["support_status"],
                "support_level": contract["support_level"],
            }
        )
    return tuple(rows)


def _adapter_rows(row_counts: dict[str, int]) -> list[dict[str, object]]:
    official_sources = {
        str(row["local_target"]): row
        for row in official_player_stats_source_rows()
    }
    adapters = [
        {
            "adapter": "official_player_stats_transform",
            "local_file": "nflverse_player_stats_weekly.csv",
            "source_name": "nflverse player stats",
            "download_or_import": "download_and_transform",
        },
        {
            "adapter": "official_snap_counts_transform",
            "local_file": "nflverse_snap_counts_weekly.csv",
            "source_name": "nflverse snap counts",
            "download_or_import": "download_and_transform",
        },
        {
            "adapter": "official_depth_chart_transform",
            "local_file": "nflverse_depth_chart_weekly.csv",
            "source_name": "nflverse depth charts",
            "download_or_import": "download_and_transform",
        },
        {
            "adapter": "manual_or_external_participation_proxy",
            "local_file": "nflverse_participation_player_weekly.csv",
            "source_name": "participation/route proxy CSV",
            "download_or_import": "local_csv_contract_only",
        },
        {
            "adapter": "manual_or_external_injury_import",
            "local_file": "nflverse_injuries_weekly.csv",
            "source_name": "nflverse injuries",
            "download_or_import": "local_csv_contract_only",
        },
        {
            "adapter": "identity_map_import",
            "local_file": "nflverse_identity_map.csv",
            "source_name": "Sleeper/nflverse/DynastyProcess identity bridge",
            "download_or_import": "local_csv_contract_only",
        },
        {
            "adapter": "projection_csv_import",
            "local_file": "projection_raw_import.csv",
            "source_name": "user supplied projection export",
            "download_or_import": "local_csv_contract_only",
        },
    ]
    rows: list[dict[str, object]] = []
    for adapter in adapters:
        local_file = str(adapter["local_file"])
        source = official_sources.get(local_file, {})
        rows.append(
            {
                **adapter,
                "row_count": row_counts.get(local_file, ""),
                "scraping_required": source.get("scraping_required", "false"),
                "key_fields": source.get(
                    "key_fields",
                    "|".join(NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS.get(local_file, ())),
                ),
                "limitations": source.get(
                    "limitations",
                    "Local contract exists; populate from a legal export before scoring.",
                ),
                "confidence": source.get("confidence", _adapter_confidence(local_file)),
                "scoring_effect": "none until reviewed/derived/applied",
            }
        )
    return rows


def _summary_rows(
    coverage_rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    statuses = (
        "direct_free_import",
        "partial_free_import",
        "external_csv_required",
        "review_only_or_external",
    )
    for status in statuses:
        matches = [row for row in coverage_rows if row["support_status"] == status]
        rows.append(
            {
                "support_status": status,
                "feature_buckets": len(matches),
                "buckets": "|".join(str(row["feature_bucket"]) for row in matches),
                "ready": sum(1 for row in matches if row["validation_status"] == "ready"),
                "review": sum(1 for row in matches if row["validation_status"] == "review"),
                "external_required": sum(
                    1 for row in matches if row["validation_status"] == "external_required"
                ),
                "blocked": sum(1 for row in matches if row["validation_status"] == "blocked"),
            }
        )
    return rows


def _coverage_issues(
    coverage_rows: tuple[dict[str, object], ...],
    raw_report: object,
) -> list[str]:
    issues = [
        f"{row['feature_bucket']}: {row['missing_fields']}"
        for row in coverage_rows
        if row.get("missing_fields")
    ]
    issues.extend(
        f"{issue.file_name}: {issue.issue}"
        for issue in raw_report.issues
        if issue.severity == "error"
    )
    return issues


def _next_action(validation_status: str, bucket: str) -> str:
    if validation_status == "ready":
        return "Free import contract is ready; derive features in review-only mode."
    if validation_status == "review":
        return "Use this bucket, but keep proxy limits visible in receipts."
    if validation_status == "external_required":
        return "Supply a legal local export or keep this bucket as review/optional."
    return f"Fix the local import contract before trusting {bucket}."


def _adapter_confidence(local_file: str) -> int:
    if local_file == "nflverse_identity_map.csv":
        return 90
    if local_file == "projection_raw_import.csv":
        return 70
    if local_file == "nflverse_participation_player_weekly.csv":
        return 65
    if local_file == "nflverse_injuries_weekly.csv":
        return 80
    return 75


def _local_header(root: Path, file_name: str) -> tuple[str, ...]:
    path = root / file_name
    if not path.exists():
        return NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS.get(file_name, ())
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return tuple(next(reader, ()))


def _write_csv(path: Path, rows: tuple[dict[str, object], ...] | list[dict[str, object]]) -> None:
    fieldnames = tuple(rows[0].keys()) if rows else ("empty",)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
