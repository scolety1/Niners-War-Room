from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")
PACKAGE_NAMES = (
    "stats_context/player_weekly_stats_display_context",
    "stats_context/player_season_stats_display_context",
    "stats_context/player_usage_context",
    "stats_context/player_stats_crosscheck_report",
)
DISPLAY_ALLOWED_USE = [
    "display_stat_context_only",
    "source_audit",
    "identity_crosscheck",
    "future_latest_candidate_review",
]
FORBIDDEN_USE = [
    "private_value",
    "veteran_private_values",
    "hidden_sort",
    "hidden_rank",
    "draft_recommendation",
    "final_draft_decision",
    "model_training",
    "simulation",
    "production_deployment",
    "latest_approved",
]
BLOCKED_USE_TEXT = (
    "private_value,hidden_sort,draft_recommendation,final_draft_decision,"
    "model_training"
)
IDENTITY_COLUMNS = [
    "player_id",
    "player_name",
    "player_display_name",
    "player",
    "full_name",
    "position",
    "position_group",
    "team",
    "recent_team",
    "opponent",
    "opponent_team",
    "season",
    "week",
    "season_type",
    "game_type",
]
BASIC_STAT_COLUMNS = [
    "completions",
    "attempts",
    "passing_attempts",
    "passing_yards",
    "passing_tds",
    "passing_interceptions",
    "passing_first_downs",
    "carries",
    "rushing_attempts",
    "rushing_yards",
    "rushing_tds",
    "rushing_first_downs",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_first_downs",
]
USAGE_COLUMNS = [
    "offense_snaps",
    "offense_pct",
    "defense_snaps",
    "defense_pct",
    "st_snaps",
    "st_pct",
    "routes",
    "route",
    "route_participation",
    "pass_routes",
    "run_block_snaps",
    "pass_block_snaps",
]
QUARANTINE_PATTERNS = (
    "fantasy_points",
    "epa",
    "cpoe",
    "pacr",
    "racr",
    "wopr",
    "_exp",
    "_diff",
    "share",
    "rank",
    "ranking",
    "score",
    "value",
    "adp",
    "market",
    "tier",
    "sort",
    "probability",
    "projection",
)


class NormalizationError(ValueError):
    pass


@dataclass(frozen=True)
class Dataset:
    name: str
    file_name: str
    rows: list[dict[str, str]]
    fields: list[str]


@dataclass(frozen=True)
class PackageDraft:
    package_name: str
    data_file: str
    rows: list[dict[str, Any]]
    source_datasets: list[str]
    notes: str


@dataclass(frozen=True)
class NormalizeResult:
    snapshot_dir: Path
    report_path: Path
    packages: list[PackageDraft]
    warnings: list[str]
    quarantine_summary: dict[str, list[str]]
    wrote_candidates: bool
    candidate_paths: dict[str, Path]


def normalize_snapshot(
    *,
    snapshot_dir: Path,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    write_candidates: bool = False,
    snapshot_label: str | None = None,
) -> NormalizeResult:
    metadata = _read_optional_json(snapshot_dir / "snapshot_metadata.json") or {}
    label = snapshot_label or _snapshot_label(snapshot_dir, metadata)
    datasets = _read_datasets(snapshot_dir, metadata)
    warnings = _source_warnings(metadata)
    quarantine_summary = {
        dataset.name: _quarantined_fields(dataset.fields) for dataset in datasets.values()
    }

    packages = _build_packages(datasets, quarantine_summary, warnings)
    candidate_paths: dict[str, Path] = {}
    if write_candidates:
        for package in packages:
            candidate_paths[package.package_name] = _write_candidate_package(
                output_root=output_root,
                package=package,
                label=label,
                source_metadata=metadata,
                snapshot_dir=snapshot_dir,
                warnings=warnings,
                quarantine_summary=quarantine_summary,
            )

    report_path = snapshot_dir / "nflverse_normalizer_v0_report.md"
    report_path.write_text(
        _markdown_report(
            packages=packages,
            warnings=warnings,
            quarantine_summary=quarantine_summary,
            write_candidates=write_candidates,
            candidate_paths=candidate_paths,
            snapshot_dir=snapshot_dir,
            label=label,
        ),
        encoding="utf-8",
    )
    return NormalizeResult(
        snapshot_dir=snapshot_dir,
        report_path=report_path,
        packages=packages,
        warnings=warnings,
        quarantine_summary=quarantine_summary,
        wrote_candidates=write_candidates,
        candidate_paths=candidate_paths,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize local-only nflverse raw snapshots into display-only dry-run "
            "reports or explicit Lane Exchange latest_candidate packages. Never "
            "writes latest_approved."
        )
    )
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--write-candidates", action="store_true")
    parser.add_argument("--snapshot-label", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = normalize_snapshot(
            snapshot_dir=args.snapshot_dir,
            output_root=args.output_root,
            write_candidates=args.write_candidates,
            snapshot_label=args.snapshot_label,
        )
    except Exception as exc:
        print(f"nflverse normalizer failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"report_path={result.report_path}")
    print(f"write_candidates={result.wrote_candidates}")
    for package in result.packages:
        print(f"{package.package_name}: rows={len(package.rows)}")
    for package_name, path in result.candidate_paths.items():
        print(f"candidate={package_name} path={path}")
    return 0


def _read_datasets(snapshot_dir: Path, metadata: dict[str, Any]) -> dict[str, Dataset]:
    datasets: dict[str, Dataset] = {}
    metadata_rows = {
        str(row.get("name")): row
        for row in metadata.get("datasets", [])
        if isinstance(row, dict) and row.get("name")
    }
    possible = {
        "weekly_stats": "weekly_stats.csv",
        "season_stats": "season_stats.csv",
        "rosters": "rosters.csv",
        "weekly_rosters": "weekly_rosters.csv",
        "snap_counts": "snap_counts.csv",
        "participation": "participation.csv",
        "opportunity": "opportunity.csv",
    }
    for name, file_name in possible.items():
        path = snapshot_dir / file_name
        if not path.exists() or path.stat().st_size == 0:
            if name == "season_stats":
                continue
            if name in {"participation", "opportunity", "weekly_rosters", "rosters"}:
                continue
            metadata_row = metadata_rows.get(name)
            if metadata_row and metadata_row.get("status") in {"skipped", "warning"}:
                continue
            continue
        rows, fields = _read_csv(path)
        datasets[name] = Dataset(name=name, file_name=file_name, rows=rows, fields=fields)
    if "weekly_stats" not in datasets and "snap_counts" not in datasets:
        raise NormalizationError("snapshot has neither weekly_stats.csv nor snap_counts.csv")
    return datasets


def _build_packages(
    datasets: dict[str, Dataset],
    quarantine_summary: dict[str, list[str]],
    warnings: list[str],
) -> list[PackageDraft]:
    packages: list[PackageDraft] = []
    if "weekly_stats" in datasets:
        weekly = datasets["weekly_stats"]
        packages.append(
            PackageDraft(
                package_name="stats_context/player_weekly_stats_display_context",
                data_file="player_weekly_stats_display_context.csv",
                rows=_safe_stat_rows(
                    weekly,
                    allowed_columns=IDENTITY_COLUMNS + BASIC_STAT_COLUMNS,
                    context_type="weekly_stats_display",
                ),
                source_datasets=["weekly_stats"],
                notes=(
                    "Display-only weekly player stats. Quarantined advanced/value-like "
                    "fields are excluded from candidate data."
                ),
            )
        )
    if "season_stats" in datasets:
        season = datasets["season_stats"]
        packages.append(
            PackageDraft(
                package_name="stats_context/player_season_stats_display_context",
                data_file="player_season_stats_display_context.csv",
                rows=_safe_stat_rows(
                    season,
                    allowed_columns=IDENTITY_COLUMNS + BASIC_STAT_COLUMNS,
                    context_type="season_stats_display",
                ),
                source_datasets=["season_stats"],
                notes=(
                    "Display-only season player stats. Quarantined advanced/value-like "
                    "fields are excluded from candidate data."
                ),
            )
        )
    else:
        warnings.append("season_stats.csv missing; season display package skipped as YELLOW.")

    usage_sources = [
        name
        for name in ("snap_counts", "participation", "opportunity")
        if name in datasets
    ]
    if usage_sources:
        rows: list[dict[str, Any]] = []
        for name in usage_sources:
            rows.extend(
                _safe_stat_rows(
                    datasets[name],
                    allowed_columns=IDENTITY_COLUMNS + USAGE_COLUMNS + BASIC_STAT_COLUMNS,
                    context_type=f"{name}_display_usage",
                )
            )
        packages.append(
            PackageDraft(
                package_name="stats_context/player_usage_context",
                data_file="player_usage_context.csv",
                rows=rows,
                source_datasets=usage_sources,
                notes=(
                    "Display-only usage context from snap/participation/opportunity "
                    "datasets. No private value or hidden sorting use is approved."
                ),
            )
        )

    packages.append(
        PackageDraft(
            package_name="stats_context/player_stats_crosscheck_report",
            data_file="player_stats_crosscheck_report.csv",
            rows=_crosscheck_rows(datasets, quarantine_summary, warnings),
            source_datasets=sorted(datasets),
            notes=(
                "Source-audit crosscheck summary only. Contains row counts, field counts, "
                "and quarantine summaries, not full stats."
            ),
        )
    )
    return packages


def _safe_stat_rows(
    dataset: Dataset, *, allowed_columns: list[str], context_type: str
) -> list[dict[str, Any]]:
    allowed = [column for column in allowed_columns if column in dataset.fields]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(dataset.rows, start=1):
        safe = {
            "source_dataset": dataset.name,
            "source_file": dataset.file_name,
            "source_row_count": len(dataset.rows),
            "source_row_number": index,
            "context_type": context_type,
            "approval_status": "candidate",
            "allowed_use": "display_stat_context_only",
            "blocked_use": BLOCKED_USE_TEXT,
        }
        for column in allowed:
            if _is_quarantined(column):
                continue
            safe[column] = row.get(column, "")
        rows.append(safe)
    return rows


def _crosscheck_rows(
    datasets: dict[str, Dataset],
    quarantine_summary: dict[str, list[str]],
    warnings: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in sorted(datasets):
        dataset = datasets[name]
        rows.append(
            {
                "source_dataset": name,
                "source_file": dataset.file_name,
                "source_row_count": len(dataset.rows),
                "source_column_count": len(dataset.fields),
                "safe_display_field_count": len(
                    [
                        field
                        for field in dataset.fields
                        if _is_allowed_display_field(field) and not _is_quarantined(field)
                    ]
                ),
                "quarantined_field_count": len(quarantine_summary.get(name, [])),
                "quarantined_fields": ";".join(quarantine_summary.get(name, [])),
                "approval_status": "candidate",
                "allowed_use": "source_audit_and_display_context_review_only",
                "blocked_use": BLOCKED_USE_TEXT,
                "notes": "Quarantined fields are excluded from display candidate packages.",
            }
        )
    if "season_stats" not in datasets:
        rows.append(
            {
                "source_dataset": "season_stats",
                "source_file": "season_stats.csv",
                "source_row_count": 0,
                "source_column_count": 0,
                "safe_display_field_count": 0,
                "quarantined_field_count": 0,
                "quarantined_fields": "",
                "approval_status": "candidate",
                "allowed_use": "source_audit_only",
                "blocked_use": BLOCKED_USE_TEXT,
                "notes": "Optional season_stats.csv missing; package skipped.",
            }
        )
    for warning in warnings:
        rows.append(
            {
                "source_dataset": "normalizer_warning",
                "source_file": "",
                "source_row_count": 0,
                "source_column_count": 0,
                "safe_display_field_count": 0,
                "quarantined_field_count": 0,
                "quarantined_fields": "",
                "approval_status": "candidate",
                "allowed_use": "source_audit_only",
                "blocked_use": BLOCKED_USE_TEXT,
                "notes": warning,
            }
        )
    return rows


def _write_candidate_package(
    *,
    output_root: Path,
    package: PackageDraft,
    label: str,
    source_metadata: dict[str, Any],
    snapshot_dir: Path,
    warnings: list[str],
    quarantine_summary: dict[str, list[str]],
) -> Path:
    source_lane, short_name = package.package_name.split("/", 1)
    package_root = output_root / source_lane / short_name
    snapshot_path = package_root / label
    snapshot_path.mkdir(parents=True, exist_ok=False)
    data_path = snapshot_path / package.data_file
    _write_csv(data_path, package.rows)
    sha256 = _file_sha256(data_path)
    manifest = _manifest(
        package=package,
        label=label,
        source_metadata=source_metadata,
        snapshot_dir=snapshot_dir,
        sha256=sha256,
        warnings=warnings,
        quarantine_summary=quarantine_summary,
    )
    manifest_path = snapshot_path / "manifest.json"
    _write_json(manifest_path, manifest)
    pointer = {
        "pointer_type": "latest_candidate",
        "package_name": package.package_name,
        "approval_status": "candidate",
        "approval_scope": "display_stat_context_review_only",
        "snapshot_path": str(snapshot_path),
        "manifest_path": str(manifest_path),
        "data_file": package.data_file,
        "row_count": len(package.rows),
        "sha256": sha256,
        "updated_at": datetime.now(UTC).isoformat(),
        "allowed_use": DISPLAY_ALLOWED_USE,
        "forbidden_use": FORBIDDEN_USE,
        "notes": "latest_candidate only; latest_approved was not created or updated.",
    }
    _write_json(package_root / "latest_candidate.json", pointer)
    return snapshot_path


def _manifest(
    *,
    package: PackageDraft,
    label: str,
    source_metadata: dict[str, Any],
    snapshot_dir: Path,
    sha256: str,
    warnings: list[str],
    quarantine_summary: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        "source_lane": package.package_name.split("/", 1)[0],
        "source_repo": "nflverse/nflreadpy local raw snapshot",
        "source_branch": "local_only_scheduled_ingest",
        "source_head": str(snapshot_dir),
        "source_snapshot_label": source_metadata.get("snapshot_label") or snapshot_dir.name,
        "source_created_at": source_metadata.get("created_at", ""),
        "package_name": package.package_name,
        "schema_version": "nflverse_normalizer_v0",
        "data_file": package.data_file,
        "row_count": len(package.rows),
        "sha256": sha256,
        "created_at": datetime.now(UTC).isoformat(),
        "approval_status": "candidate",
        "approved_for": ["display_stat_context_review_only"],
        "allowed_use": DISPLAY_ALLOWED_USE,
        "forbidden_use": FORBIDDEN_USE,
        "contains_private_value": False,
        "contains_market_data": False,
        "contains_adp": False,
        "not_latest_approved": True,
        "not_final_draft_day_approval": True,
        "not_simulation_approval": True,
        "not_model_training_approval": True,
        "source_datasets": package.source_datasets,
        "quarantined_fields_by_dataset": quarantine_summary,
        "source_warnings": warnings,
        "notes": package.notes,
        "snapshot_label": label,
    }


def _markdown_report(
    *,
    packages: list[PackageDraft],
    warnings: list[str],
    quarantine_summary: dict[str, list[str]],
    write_candidates: bool,
    candidate_paths: dict[str, Path],
    snapshot_dir: Path,
    label: str,
) -> str:
    lines = [
        "# nflverse Normalizer V0 Report",
        "",
        "## Scope",
        "",
        "Display-only normalization report from a local nflverse raw snapshot. "
        "This does not create `latest_approved`, private value, hidden sort, "
        "model training, draft recommendations, simulations, or deployment.",
        "",
        "## Snapshot",
        "",
        f"- Snapshot dir: `{snapshot_dir}`",
        f"- Candidate label: `{label}`",
        f"- Write candidates: `{write_candidates}`",
        "",
        "## Package Counts",
        "",
        "| Package | Rows | Candidate path |",
        "| --- | ---: | --- |",
    ]
    for package in packages:
        path = candidate_paths.get(package.package_name)
        lines.append(
            f"| `{package.package_name}` | {len(package.rows)} | "
            f"{f'`{path}`' if path else 'dry-run only'} |"
        )
    lines.extend(["", "## Quarantine Summary", ""])
    for dataset, fields in sorted(quarantine_summary.items()):
        value = ", ".join(fields) if fields else "none"
        lines.append(f"- `{dataset}`: {value}")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Candidate data is display/stat context only.",
            "- Quarantined fields are excluded from display candidate CSVs.",
            "- `latest_approved` was not created.",
            "- Existing `latest_approved` packages were not overwritten.",
            "- No private value, hidden sort, model training, draft recommendation, "
            "simulation, or deployment is approved.",
        ]
    )
    return "\n".join(lines) + "\n"


def _source_warnings(metadata: dict[str, Any]) -> list[str]:
    warnings = list(metadata.get("warnings") or [])
    for dataset in metadata.get("datasets") or []:
        if not isinstance(dataset, dict):
            continue
        warning = dataset.get("warning")
        error = dataset.get("error")
        if warning:
            warnings.append(f"{dataset.get('name')}: {warning}")
        if error:
            warnings.append(f"{dataset.get('name')}: {error}")
    return warnings


def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = [str(field) for field in (reader.fieldnames or [])]
        return [dict(row) for row in reader], fields


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else None


def _snapshot_label(snapshot_dir: Path, metadata: dict[str, Any]) -> str:
    raw = str(metadata.get("snapshot_label") or snapshot_dir.name)
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _quarantined_fields(fields: list[str]) -> list[str]:
    return sorted({field for field in fields if _is_quarantined(field)})


def _is_quarantined(field: str) -> bool:
    lower = field.lower()
    return any(pattern in lower for pattern in QUARANTINE_PATTERNS)


def _is_allowed_display_field(field: str) -> bool:
    return field in set(IDENTITY_COLUMNS + BASIC_STAT_COLUMNS + USAGE_COLUMNS)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = _headers(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _headers(rows: list[dict[str, Any]]) -> list[str]:
    headers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                headers.append(key)
                seen.add(key)
    return headers or ["empty"]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
