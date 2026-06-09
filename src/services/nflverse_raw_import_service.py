from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

RAW_NFLVERSE_FILES = (
    "nflverse_player_stats_weekly.csv",
    "nflverse_snap_counts_weekly.csv",
    "nflverse_participation_player_weekly.csv",
    "nflverse_depth_chart_weekly.csv",
    "nflverse_injuries_weekly.csv",
)
DEFAULT_NFLVERSE_RAW_IMPORT_ROOT = Path("local_exports/nflverse/raw")

RAW_FILE_CONTRACTS: dict[str, dict[str, tuple[str, ...]]] = {
    "nflverse_player_stats_weekly.csv": {
        "required": (
            "season",
            "week",
            "player_id",
            "player_name",
            "position",
        ),
        "numeric": (
            "season",
            "week",
            "passing_yards",
            "passing_tds",
            "interceptions",
            "rushing_attempts",
            "rushing_yards",
            "rushing_tds",
            "rushing_first_downs",
            "targets",
            "receptions",
            "receiving_yards",
            "receiving_tds",
            "receiving_first_downs",
            "passing_first_downs",
            "passing_epa",
            "rushing_epa",
            "receiving_epa",
            "receiving_air_yards",
            "target_share",
            "air_yards_share",
            "wopr",
            "return_yards",
            "return_tds",
            "kick_return_yards",
            "kick_return_tds",
            "punt_return_yards",
            "punt_return_tds",
            "fumbles_lost",
        ),
    },
    "nflverse_snap_counts_weekly.csv": {
        "required": ("season", "week", "game_id", "player_name", "position"),
        "numeric": (
            "season",
            "week",
            "offense_snaps",
            "offense_pct",
            "st_snaps",
            "st_pct",
        ),
    },
    "nflverse_participation_player_weekly.csv": {
        "required": ("season", "week", "player_name", "position"),
        "numeric": (
            "season",
            "week",
            "offensive_plays_on_field",
            "team_offensive_plays",
            "dropbacks_on_field",
            "team_dropbacks",
            "route_participation_proxy",
            "targets",
            "targets_per_dropback_snap_proxy",
            "red_zone_on_field",
            "short_yardage_on_field",
            "confidence",
        ),
    },
    "nflverse_depth_chart_weekly.csv": {
        "required": ("season", "week", "player_name", "position", "team"),
        "numeric": ("season", "week", "pos_rank", "depth_chart_role_score"),
    },
    "nflverse_injuries_weekly.csv": {
        "required": ("season", "week", "player_name", "position", "team"),
        "numeric": ("season", "week", "source_confidence"),
    },
}


@dataclass(frozen=True)
class NflverseRawImportIssue:
    severity: str
    file_name: str
    row_number: int | None
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class NflverseRawImportValidationReport:
    root: Path
    status: str
    row_counts: dict[str, int]
    issues: tuple[NflverseRawImportIssue, ...]


def validate_nflverse_raw_imports(
    source_root: str | Path,
) -> NflverseRawImportValidationReport:
    root = Path(source_root)
    row_counts: dict[str, int] = {}
    issues: list[NflverseRawImportIssue] = []

    for file_name in RAW_NFLVERSE_FILES:
        path = root / file_name
        if not path.exists():
            row_counts[file_name] = 0
            issues.append(
                NflverseRawImportIssue(
                    "error",
                    file_name,
                    None,
                    "Required raw nflverse CSV is missing.",
                    f"Add {file_name} from the nflverse_stats_upgrade template/export.",
                )
            )
            continue
        header, rows = _read_csv(path)
        row_counts[file_name] = len(rows)
        expected_header = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[file_name]
        if header != expected_header:
            issues.append(
                NflverseRawImportIssue(
                    "error",
                    file_name,
                    None,
                    "CSV header does not match the raw nflverse import contract.",
                    "Regenerate the file from the Phase 3 template headers.",
                )
            )
            continue
        issues.extend(_validate_rows(file_name, rows))

    status = _status_from_issues(issues)
    return NflverseRawImportValidationReport(
        root=root,
        status=status,
        row_counts=row_counts,
        issues=tuple(issues),
    )


def nflverse_raw_import_readiness_rows(
    report: NflverseRawImportValidationReport,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for file_name in RAW_NFLVERSE_FILES:
        errors = [
            issue for issue in report.issues
            if issue.file_name == file_name and issue.severity == "error"
        ]
        warnings = [
            issue for issue in report.issues
            if issue.file_name == file_name and issue.severity == "warning"
        ]
        if errors:
            status = "blocked"
            next_action = errors[0].suggested_fix
        elif warnings:
            status = "review"
            next_action = "Review warnings before deriving normalized features."
        else:
            status = "ready"
            next_action = "Ready for later derivation; still review-only."
        rows.append(
            {
                "file_name": file_name,
                "rows": report.row_counts.get(file_name, 0),
                "status": status,
                "errors": len(errors),
                "warnings": len(warnings),
                "scoring_effect": "none; raw import contract only",
                "next_action": next_action,
            }
        )
    return rows


def nflverse_raw_import_summary_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    statuses = ("ready", "review", "blocked")
    return [
        {
            "status": status,
            "files": sum(1 for row in rows if row["status"] == status),
            "blocking": status == "blocked" and any(row["status"] == status for row in rows),
            "next_action": _summary_next_action(status),
        }
        for status in statuses
    ]


def _validate_rows(
    file_name: str,
    rows: list[dict[str, str]],
) -> list[NflverseRawImportIssue]:
    contract = RAW_FILE_CONTRACTS[file_name]
    issues: list[NflverseRawImportIssue] = []
    for row_number, row in enumerate(rows, start=2):
        for column in contract["required"]:
            if not row.get(column, "").strip():
                issues.append(
                    NflverseRawImportIssue(
                        "error",
                        file_name,
                        row_number,
                        f"Missing required value for {column}.",
                        f"Populate {column} before derivation.",
                    )
                )
        for column in contract["numeric"]:
            value = row.get(column, "").strip()
            if value and not _is_float(value):
                issues.append(
                    NflverseRawImportIssue(
                        "error",
                        file_name,
                        row_number,
                        f"{column} must be numeric.",
                        f"Replace {column} with a numeric value or leave it blank.",
                    )
                )
        position = row.get("position", "").strip()
        if position and position not in {"QB", "RB", "WR", "TE"}:
            issues.append(
                NflverseRawImportIssue(
                    "warning",
                    file_name,
                    row_number,
                    "Unsupported position for scored model import.",
                    "Keep unsupported positions as raw context only; do not score them.",
                )
            )
    return issues


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _status_from_issues(issues: list[NflverseRawImportIssue]) -> str:
    if any(issue.severity == "error" for issue in issues):
        return "blocked"
    if issues:
        return "review"
    return "ready"


def _summary_next_action(status: str) -> str:
    if status == "ready":
        return "Raw files are schema-valid; proceed to LVE derivation in later phases."
    if status == "review":
        return "Resolve warnings or confirm they are intentionally raw-only."
    return "Fix missing files, headers, or numeric errors before derivation."


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True
