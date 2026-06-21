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
    "stats_context/player_roster_display_context",
    "stats_context/player_weekly_roster_display_context",
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
DATASET_TIMING_POLICY = {
    "weekly_stats": {
        "source_timing_class": "live_draft_day_candidate",
        "live_use_allowed": True,
        "timing_notes": (
            "Weekly stats may be live/draft-day display candidates when refreshed; "
            "subject to stat corrections and stale-snapshot warnings."
        ),
    },
    "season_stats": {
        "source_timing_class": "unknown_timing_yellow",
        "live_use_allowed": False,
        "timing_notes": (
            "Season stats may be season-to-date live/in-season display candidates "
            "when built from a current player-stats source, but final season "
            "aggregates remain offseason/finalized context. Require explicit "
            "as-of/source freshness before live use."
        ),
    },
    "rosters": {
        "source_timing_class": "live_draft_day_candidate",
        "live_use_allowed": True,
        "timing_notes": (
            "Roster metadata may be live/draft-day display context when refreshed "
            "from the current source; stale data must be visible."
        ),
    },
    "weekly_rosters": {
        "source_timing_class": "live_draft_day_candidate",
        "live_use_allowed": True,
        "timing_notes": (
            "Weekly roster metadata may be live/draft-day display context when the "
            "current week/source supports it; stale data must be visible."
        ),
    },
    "snap_counts": {
        "source_timing_class": "live_draft_day_candidate",
        "live_use_allowed": True,
        "timing_notes": (
            "Snap counts may be refreshed after games and used as display-only "
            "historical/weekly context; they are not projections."
        ),
    },
    "participation": {
        "source_timing_class": "historical_backtest_only",
        "live_use_allowed": False,
        "timing_notes": (
            "Participation data from 2023 onward is courtesy of FTN via nflverse "
            "and is provided after all post-season games are completed; it does "
            "not update during the season."
        ),
    },
    "opportunity": {
        "source_timing_class": "unknown_timing_yellow",
        "live_use_allowed": False,
        "timing_notes": (
            "Opportunity timing requires source-specific freshness review before "
            "live use; keep display-only/backtest review until confirmed."
        ),
    },
    "normalizer_warning": {
        "source_timing_class": "display_only",
        "live_use_allowed": False,
        "timing_notes": "Normalizer warning/audit row only.",
    },
}
IDENTITY_COLUMNS = [
    "gsis_id",
    "player_id",
    "pfr_id",
    "pfr_player_id",
    "espn_id",
    "sportradar_id",
    "yahoo_id",
    "rotowire_id",
    "fantasy_data_id",
    "sleeper_id",
    "smart_id",
    "player_name",
    "player_display_name",
    "player",
    "full_name",
    "football_name",
    "first_name",
    "last_name",
    "position",
    "position_group",
    "ngs_position",
    "team",
    "recent_team",
    "posteam",
    "possession_team",
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
    "passing_2pt_conversions",
    "carries",
    "rushing_attempts",
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
    "air_yards",
    "passing_air_yards",
    "receiving_air_yards",
    "pass_air_yards",
    "rec_air_yards",
    "passing_yards_after_catch",
    "receiving_yards_after_catch",
    "yards_after_catch",
    "sacks",
    "sack_fumbles",
    "passing_sacks",
    "rushing_fumbles",
    "receiving_fumbles",
    "rushing_fumbles_lost",
    "receiving_fumbles_lost",
    "return_yards",
    "punt_returns",
    "punt_return_yards",
    "kickoff_returns",
    "kickoff_return_yards",
    "special_teams_tds",
    "pass_attempt",
    "rec_attempt",
    "rush_attempt",
    "pass_completions",
    "pass_yards_gained",
    "rec_yards_gained",
    "rush_yards_gained",
    "pass_touchdown",
    "rec_touchdown",
    "rush_touchdown",
    "pass_first_down",
    "rec_first_down",
    "rush_first_down",
    "pass_interception",
    "rec_interception",
    "rec_fumble_lost",
    "rush_fumble_lost",
    "total_yards_gained",
    "total_touchdown",
    "total_first_down",
]
USAGE_COLUMNS = [
    "game_id",
    "nflverse_game_id",
    "old_game_id",
    "play_id",
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
    "offense_formation",
    "offense_personnel",
    "players_on_play",
    "offense_players",
    "defense_players",
    "n_offense",
    "n_defense",
    "ngs_air_yards",
    "was_pressure",
    "offense_names",
    "defense_names",
    "offense_positions",
    "defense_positions",
    "offense_numbers",
    "defense_numbers",
]
ROSTER_COLUMNS = [
    *IDENTITY_COLUMNS,
    "depth_chart_position",
    "jersey_number",
    "status",
    "status_description_abbr",
    "birth_date",
    "height",
    "weight",
    "college",
    "years_exp",
    "entry_year",
    "rookie_year",
    "draft_club",
    "draft_number",
]
QUARANTINE_PATTERNS = (
    "fantasy_points",
    "headshot_url",
    "epa",
    "cpoe",
    "pacr",
    "racr",
    "wopr",
    "_exp",
    "expected",
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
QUARANTINE_ALLOWED_EXACT_FIELDS = {
    "years_exp",
}


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

    if "rosters" in datasets:
        roster = datasets["rosters"]
        packages.append(
            PackageDraft(
                package_name="stats_context/player_roster_display_context",
                data_file="player_roster_display_context.csv",
                rows=_safe_stat_rows(
                    roster,
                    allowed_columns=ROSTER_COLUMNS,
                    context_type="roster_display",
                ),
                source_datasets=["rosters"],
                notes=(
                    "Display-only player roster metadata. Age/experience fields are "
                    "context only and not private value."
                ),
            )
        )
    else:
        _append_missing_dataset_warning(
            warnings,
            "rosters",
            "player_roster_display_context",
        )

    if "weekly_rosters" in datasets:
        weekly_roster = datasets["weekly_rosters"]
        packages.append(
            PackageDraft(
                package_name="stats_context/player_weekly_roster_display_context",
                data_file="player_weekly_roster_display_context.csv",
                rows=_safe_stat_rows(
                    weekly_roster,
                    allowed_columns=ROSTER_COLUMNS,
                    context_type="weekly_roster_display",
                ),
                source_datasets=["weekly_rosters"],
                notes=(
                    "Display-only weekly roster/team/status context. No private value "
                    "or hidden sorting use is approved."
                ),
            )
        )
    else:
        _append_missing_dataset_warning(
            warnings,
            "weekly_rosters",
            "player_weekly_roster_display_context",
        )

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
    timing = _dataset_timing(dataset.name)
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
            "source_timing_class": timing["source_timing_class"],
            "live_use_allowed": timing["live_use_allowed"],
            "timing_notes": timing["timing_notes"],
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
        timing = _dataset_timing(name)
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
                "source_timing_class": timing["source_timing_class"],
                "live_use_allowed": timing["live_use_allowed"],
                "timing_notes": timing["timing_notes"],
                "notes": "Quarantined fields are excluded from display candidate packages.",
            }
        )
    if "season_stats" not in datasets:
        timing = _dataset_timing("season_stats")
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
                "source_timing_class": timing["source_timing_class"],
                "live_use_allowed": timing["live_use_allowed"],
                "timing_notes": timing["timing_notes"],
                "notes": "Optional season_stats.csv missing; package skipped.",
            }
        )
    for name in ("rosters", "weekly_rosters", "participation", "opportunity"):
        if name in datasets:
            continue
        timing = _dataset_timing(name)
        rows.append(
            {
                "source_dataset": name,
                "source_file": f"{name}.csv",
                "source_row_count": 0,
                "source_column_count": 0,
                "safe_display_field_count": 0,
                "quarantined_field_count": 0,
                "quarantined_fields": "",
                "approval_status": "candidate",
                "allowed_use": "source_audit_only",
                "blocked_use": BLOCKED_USE_TEXT,
                "source_timing_class": timing["source_timing_class"],
                "live_use_allowed": timing["live_use_allowed"],
                "timing_notes": timing["timing_notes"],
                "notes": f"YELLOW: Optional {name}.csv missing or unsupported; package skipped.",
            }
        )
    for warning in warnings:
        timing = _dataset_timing("normalizer_warning")
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
                "source_timing_class": timing["source_timing_class"],
                "live_use_allowed": timing["live_use_allowed"],
                "timing_notes": timing["timing_notes"],
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
        "source_timing_summary": _package_timing_summary(package.source_datasets),
        "source_timing_classes": _package_timing_classes(package.source_datasets),
        "live_use_allowed": _package_live_use_allowed(package.source_datasets),
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
        "source_timing_summary": _package_timing_summary(package.source_datasets),
        "source_timing_classes": _package_timing_classes(package.source_datasets),
        "live_use_allowed": _package_live_use_allowed(package.source_datasets),
        "timing_notes": _package_timing_notes(package.source_datasets),
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
        "| Package | Rows | Timing classes | Live use allowed | Candidate path |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for package in packages:
        path = candidate_paths.get(package.package_name)
        lines.append(
            f"| `{package.package_name}` | {len(package.rows)} | "
            f"`{', '.join(_package_timing_classes(package.source_datasets))}` | "
            f"{_package_live_use_allowed(package.source_datasets)} | "
            f"{f'`{path}`' if path else 'dry-run only'} |"
        )
    lines.extend(["", "## Source Timing Summary", ""])
    for dataset in sorted(quarantine_summary):
        timing = _dataset_timing(dataset)
        lines.append(
            f"- `{dataset}`: `{timing['source_timing_class']}`, "
            f"live_use_allowed={timing['live_use_allowed']}. "
            f"{timing['timing_notes']}"
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


def _dataset_timing(dataset_name: str) -> dict[str, Any]:
    return DATASET_TIMING_POLICY.get(
        dataset_name,
        {
            "source_timing_class": "unknown_timing_yellow",
            "live_use_allowed": False,
            "timing_notes": (
                "Dataset timing is not classified; keep display-only/backtest review "
                "until Tim/Master/QA approval."
            ),
        },
    )


def _package_timing_summary(source_datasets: list[str]) -> dict[str, dict[str, Any]]:
    return {dataset: _dataset_timing(dataset) for dataset in source_datasets}


def _package_timing_classes(source_datasets: list[str]) -> list[str]:
    return sorted(
        {
            str(_dataset_timing(dataset)["source_timing_class"])
            for dataset in source_datasets
        }
    )


def _package_live_use_allowed(source_datasets: list[str]) -> bool:
    if not source_datasets:
        return False
    return all(bool(_dataset_timing(dataset)["live_use_allowed"]) for dataset in source_datasets)


def _package_timing_notes(source_datasets: list[str]) -> list[str]:
    return [
        f"{dataset}: {_dataset_timing(dataset)['timing_notes']}"
        for dataset in source_datasets
    ]


def _append_missing_dataset_warning(
    warnings: list[str], dataset_name: str, package_short_name: str
) -> None:
    warnings.append(
        f"YELLOW: {dataset_name}.csv missing or unsupported; "
        f"{package_short_name} package skipped."
    )


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
    if lower in QUARANTINE_ALLOWED_EXACT_FIELDS:
        return False
    return any(pattern in lower for pattern in QUARANTINE_PATTERNS)


def _is_allowed_display_field(field: str) -> bool:
    return field in set(IDENTITY_COLUMNS + BASIC_STAT_COLUMNS + USAGE_COLUMNS + ROSTER_COLUMNS)


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
