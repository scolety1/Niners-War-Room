from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

PROJECTION_FEATURE_HEADER = (
    "season",
    "week",
    "projection_scope",
    "projection_source_status",
    "source_id",
    "source_player_id",
    "sleeper_id",
    "gsis_id",
    "player_name",
    "position",
    "team",
    "projected_rushing_first_downs",
    "projected_receiving_first_downs",
    "lve_projected_points",
    "lve_projected_ppg",
    "lve_projection_score",
    "first_down_estimation_method",
    "projection_source_count",
    "projection_freshness_score",
    "missing_projection_penalty",
    "confidence",
    "warnings",
    "scoring_effect",
)

FIRST_DOWN_ESTIMATION_RATES = {
    "QB": {"rush": 0.25, "target": 0.00},
    "RB": {"rush": 0.23, "target": 0.30},
    "WR": {"rush": 0.10, "target": 0.40},
    "TE": {"rush": 0.05, "target": 0.36},
}

PROJECTION_SOURCE_INDEPENDENT = "independent_projection"
PROJECTION_SOURCE_LOCAL_BASELINE = "local_baseline_projection"
PROJECTION_SOURCE_MISSING = "missing_projection"
PROJECTION_SOURCE_DISABLED = "disabled_projection"

LOCAL_BASELINE_PROJECTION_MARKERS = {
    "local_baseline_recent_lve",
    "local_baseline_from_imported_nflverse_stats",
    "LVE_baseline_from_actual_recent_stats",
}
DISABLED_PROJECTION_MARKERS = {
    "disabled_projection",
    "projection_disabled",
    "disabled",
}


@dataclass(frozen=True)
class ProjectionImportIssue:
    severity: str
    row_number: int | None
    player_name: str
    issue: str
    suggested_fix: str


@dataclass(frozen=True)
class ProjectionImportResult:
    status: str
    rows: tuple[dict[str, object], ...]
    issues: tuple[ProjectionImportIssue, ...]


def derive_lve_projection_feature_rows(
    source_root: str | Path,
) -> ProjectionImportResult:
    projection_path = Path(source_root) / "projection_raw_import.csv"
    header, rows = _read_csv(projection_path)
    issues: list[ProjectionImportIssue] = []
    expected_header = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["projection_raw_import.csv"]
    if header != expected_header:
        return ProjectionImportResult(
            status="blocked",
            rows=(),
            issues=(
                ProjectionImportIssue(
                    "error",
                    None,
                    "",
                    "Projection import header does not match the Phase 7 contract.",
                    "Regenerate projection_raw_import.csv from the template.",
                ),
            ),
        )
    derived_rows: list[dict[str, object]] = []
    for row_number, row in enumerate(rows, start=2):
        row_issues = _validate_projection_row(row, row_number)
        issues.extend(row_issues)
        if any(issue.severity == "error" for issue in row_issues):
            continue
        derived_rows.append(_derive_projection_row(row))
    status = _status_from_issues(issues)
    return ProjectionImportResult(
        status=status,
        rows=tuple(derived_rows),
        issues=tuple(issues),
    )


def write_lve_projection_feature_rows(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROJECTION_FEATURE_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def projection_import_summary_rows(
    rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    by_position: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_position.setdefault(str(row.get("position") or ""), []).append(row)
    output: list[dict[str, object]] = []
    for position in sorted(by_position):
        position_rows = by_position[position]
        avg_points = sum(
            float(row["lve_projected_points"]) for row in position_rows
        ) / len(position_rows)
        output.append(
            {
                "position": position,
                "rows": len(position_rows),
                "avg_lve_projected_points": round(avg_points, 2),
                "estimated_first_down_rows": sum(
                    1
                    for row in position_rows
                    if row["first_down_estimation_method"] == "estimated"
                ),
                "scoring_effect": "projection rescore only; no model mutation",
            }
        )
    return output


def _derive_projection_row(row: dict[str, str]) -> dict[str, object]:
    position = row.get("position", "")
    projection_source_status = projection_source_status_from_row(row)
    rush_fds, rec_fds, fd_method, warnings = _projected_first_downs(row, position)
    lve_points = _lve_projected_points(row, rush_fds, rec_fds)
    games = max(_float(row.get("projected_games")), 1.0)
    missing_penalty = _missing_projection_penalty(row, fd_method)
    confidence = _confidence(row, fd_method, missing_penalty)
    if fd_method == "estimated":
        warnings.add("first_downs_estimated")
    if not row.get("source_updated_at"):
        warnings.add("missing_source_updated_at")
    return {
        "season": row.get("season", ""),
        "week": row.get("week", ""),
        "projection_scope": row.get("projection_scope", ""),
        "projection_source_status": projection_source_status,
        "source_id": row.get("source_id", ""),
        "source_player_id": row.get("source_player_id", ""),
        "sleeper_id": row.get("sleeper_id", ""),
        "gsis_id": row.get("gsis_id", ""),
        "player_name": row.get("player_name", ""),
        "position": position,
        "team": row.get("team", ""),
        "projected_rushing_first_downs": round(rush_fds, 2),
        "projected_receiving_first_downs": round(rec_fds, 2),
        "lve_projected_points": round(lve_points, 2),
        "lve_projected_ppg": round(lve_points / games, 2),
        "lve_projection_score": round(_projection_score(lve_points / games, position), 2),
        "first_down_estimation_method": fd_method,
        "projection_source_count": 1,
        "projection_freshness_score": 100 if row.get("source_updated_at") else 70,
        "missing_projection_penalty": round(missing_penalty, 2),
        "confidence": round(confidence, 2),
        "warnings": "|".join(sorted(warnings)),
        "scoring_effect": "projection rescore only; no model mutation",
    }


def projection_source_status_from_row(row: dict[str, object]) -> str:
    if not row:
        return PROJECTION_SOURCE_MISSING
    explicit = str(row.get("projection_source_status") or "").strip()
    if explicit in {
        PROJECTION_SOURCE_INDEPENDENT,
        PROJECTION_SOURCE_LOCAL_BASELINE,
        PROJECTION_SOURCE_MISSING,
        PROJECTION_SOURCE_DISABLED,
    }:
        return explicit
    markers = {
        str(row.get("projection_scope") or ""),
        str(row.get("source_id") or ""),
        str(row.get("source_scoring_format") or ""),
    }
    if markers.intersection(DISABLED_PROJECTION_MARKERS):
        return PROJECTION_SOURCE_DISABLED
    if markers.intersection(LOCAL_BASELINE_PROJECTION_MARKERS):
        return PROJECTION_SOURCE_LOCAL_BASELINE
    return PROJECTION_SOURCE_INDEPENDENT


def _lve_projected_points(
    row: dict[str, str],
    projected_rush_first_downs: float,
    projected_rec_first_downs: float,
) -> float:
    return (
        (LVE_SCORING["passing_yard"] * _float(row.get("projected_passing_yards")))
        + (LVE_SCORING["passing_td"] * _float(row.get("projected_passing_tds")))
        + (LVE_SCORING["interception"] * _float(row.get("projected_interceptions")))
        + (LVE_SCORING["rushing_yard"] * _float(row.get("projected_rushing_yards")))
        + (LVE_SCORING["rushing_td"] * _float(row.get("projected_rushing_tds")))
        + (LVE_SCORING["receiving_yard"] * _float(row.get("projected_receiving_yards")))
        + (LVE_SCORING["receiving_td"] * _float(row.get("projected_receiving_tds")))
        + (LVE_SCORING["rushing_receiving_first_down"] * projected_rush_first_downs)
        + (LVE_SCORING["rushing_receiving_first_down"] * projected_rec_first_downs)
        + (LVE_SCORING["fumble_lost"] * _float(row.get("projected_fumbles_lost")))
    )


def _projected_first_downs(
    row: dict[str, str],
    position: str,
) -> tuple[float, float, str, set[str]]:
    warnings: set[str] = set()
    direct_rush = (
        row.get("projected_rushing_first_downs", "")
        or row.get("projected_rush_first_downs", "")
    ).strip()
    direct_rec = (
        row.get("projected_receiving_first_downs", "")
        or row.get("projected_rec_first_downs", "")
    ).strip()
    if direct_rush or direct_rec:
        return _float(direct_rush), _float(direct_rec), "direct_partial", warnings
    rates = FIRST_DOWN_ESTIMATION_RATES.get(position, {"rush": 0.12, "target": 0.35})
    rush_fds = _float(row.get("projected_rushing_attempts")) * rates["rush"]
    rec_fds = _float(row.get("projected_targets")) * rates["target"]
    return rush_fds, rec_fds, "estimated", warnings


def _projection_score(ppg: float, position: str) -> float:
    anchors = {
        "QB": 24.0,
        "RB": 16.0,
        "WR": 15.0,
        "TE": 11.0,
    }
    return _score(ppg / anchors.get(position, 14.0) * 100.0)


def _missing_projection_penalty(row: dict[str, str], fd_method: str) -> float:
    penalty = 0.0
    if fd_method == "estimated":
        penalty += 4.0
    if not row.get("projected_games"):
        penalty += 3.0
    if not row.get("source_updated_at"):
        penalty += 2.0
    if not row.get("source_id"):
        penalty += 4.0
    return min(15.0, penalty)


def _confidence(row: dict[str, str], fd_method: str, missing_penalty: float) -> float:
    confidence = _float(row.get("confidence")) if row.get("confidence") else 82.0
    if fd_method == "estimated":
        confidence -= 7.0
    if not row.get("source_updated_at"):
        confidence -= 4.0
    return _score(confidence - missing_penalty)


def _validate_projection_row(
    row: dict[str, str],
    row_number: int,
) -> list[ProjectionImportIssue]:
    issues: list[ProjectionImportIssue] = []
    player_name = row.get("player_name", "")
    for column in ("season", "source_id", "player_name", "position"):
        if not row.get(column, "").strip():
            issues.append(
                ProjectionImportIssue(
                    "error",
                    row_number,
                    player_name,
                    f"Missing required value for {column}.",
                    f"Populate {column} before projection derivation.",
                )
            )
    for column in _numeric_projection_columns():
        value = row.get(column, "").strip()
        if value and not _is_float(value):
            issues.append(
                ProjectionImportIssue(
                    "error",
                    row_number,
                    player_name,
                    f"{column} must be numeric.",
                    f"Replace {column} with a numeric value or leave it blank.",
                )
            )
    if row.get("position") not in {"QB", "RB", "WR", "TE"}:
        issues.append(
            ProjectionImportIssue(
                "warning",
                row_number,
                player_name,
                "Unsupported position for LVE veteran projection scoring.",
                "Keep unsupported positions as raw context only.",
            )
        )
    return issues


def _numeric_projection_columns() -> tuple[str, ...]:
    return (
        "season",
        "week",
        "projected_games",
        "projected_starts",
        "projected_passing_yards",
        "projected_passing_tds",
        "projected_interceptions",
        "projected_rushing_attempts",
        "projected_rushing_yards",
        "projected_rushing_tds",
        "projected_targets",
        "projected_receptions",
        "projected_receiving_yards",
        "projected_receiving_tds",
        "projected_rushing_first_downs",
        "projected_receiving_first_downs",
        "projected_fumbles_lost",
        "source_projected_points",
        "confidence",
    )


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    if not path.exists():
        return (), []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _status_from_issues(issues: list[ProjectionImportIssue]) -> str:
    if any(issue.severity == "error" for issue in issues):
        return "blocked"
    if issues:
        return "review"
    return "ready"


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _score(value: float) -> float:
    return max(0.0, min(100.0, value))
