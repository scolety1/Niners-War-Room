from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.lve_scoring import LVE_SCORING
from src.services.nflverse_raw_import_service import validate_nflverse_raw_imports

LVE_WEEKLY_SCORING_HEADER = (
    "season",
    "week",
    "player_id",
    "gsis_id",
    "sleeper_id",
    "player_name",
    "position",
    "team",
    "passing_points",
    "rushing_points",
    "receiving_points",
    "first_down_points",
    "return_points",
    "turnover_points",
    "lve_points",
    "rush_rec_first_downs",
    "return_yards",
    "return_tds",
    "touches",
    "targets",
    "source",
    "scoring_effect",
)


@dataclass(frozen=True)
class LveScoringDerivationResult:
    status: str
    rows: tuple[dict[str, object], ...]
    issues: tuple[str, ...]


def derive_lve_weekly_scoring_rows(
    source_root: str | Path,
) -> LveScoringDerivationResult:
    raw_report = validate_nflverse_raw_imports(source_root)
    if raw_report.status == "blocked":
        return LveScoringDerivationResult(
            status="blocked",
            rows=(),
            issues=tuple(
                f"{issue.file_name}: {issue.issue}"
                for issue in raw_report.issues
                if issue.severity == "error"
            ),
        )

    stats_path = Path(source_root) / "nflverse_player_stats_weekly.csv"
    _, stats_rows = _read_csv(stats_path)
    derived_rows = tuple(_derive_player_week(row) for row in stats_rows)
    status = "review" if raw_report.status == "review" else "ready"
    return LveScoringDerivationResult(
        status=status,
        rows=derived_rows,
        issues=tuple(
            f"{issue.file_name}: {issue.issue}"
            for issue in raw_report.issues
        ),
    )


def write_lve_weekly_scoring_rows(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LVE_WEEKLY_SCORING_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def lve_weekly_scoring_summary_rows(
    rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    by_position: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_position.setdefault(str(row.get("position") or ""), []).append(row)
    output: list[dict[str, object]] = []
    for position in sorted(by_position):
        position_rows = by_position[position]
        total_points = sum(float(row["lve_points"]) for row in position_rows)
        output.append(
            {
                "position": position,
                "rows": len(position_rows),
                "total_lve_points": round(total_points, 2),
                "avg_lve_points": round(total_points / len(position_rows), 2),
                "scoring_effect": "derived weekly scoring only; no model mutation",
            }
        )
    return output


def _derive_player_week(row: dict[str, str]) -> dict[str, object]:
    passing_points = (
        (_float(row.get("passing_yards")) * LVE_SCORING["passing_yard"])
        + (_float(row.get("passing_tds")) * LVE_SCORING["passing_td"])
    )
    rushing_points = (
        (_float(row.get("rushing_yards")) * LVE_SCORING["rushing_yard"])
        + (_float(row.get("rushing_tds")) * LVE_SCORING["rushing_td"])
    )
    receiving_points = (
        (_float(row.get("receiving_yards")) * LVE_SCORING["receiving_yard"])
        + (_float(row.get("receiving_tds")) * LVE_SCORING["receiving_td"])
    )
    rush_rec_first_downs = (
        _float(row.get("rushing_first_downs"))
        + _float(row.get("receiving_first_downs"))
    )
    first_down_points = (
        rush_rec_first_downs * LVE_SCORING["rushing_receiving_first_down"]
    )
    return_yards = _return_total(row, "return_yards", "kick_return_yards", "punt_return_yards")
    return_tds = _return_total(row, "return_tds", "kick_return_tds", "punt_return_tds")
    return_points = (
        (return_yards * LVE_SCORING["return_yard"])
        + (return_tds * LVE_SCORING["return_td"])
    )
    turnover_points = (
        (_float(row.get("interceptions")) * LVE_SCORING["interception"])
        + (_float(row.get("fumbles_lost")) * LVE_SCORING["fumble_lost"])
    )
    lve_points = (
        passing_points
        + rushing_points
        + receiving_points
        + first_down_points
        + return_points
        + turnover_points
    )
    touches = (
        _float(row.get("rushing_attempts"))
        + _float(row.get("receptions"))
    )
    return {
        "season": row.get("season", ""),
        "week": row.get("week", ""),
        "player_id": row.get("player_id", ""),
        "gsis_id": row.get("gsis_id", ""),
        "sleeper_id": row.get("sleeper_id", ""),
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "team": row.get("team", ""),
        "passing_points": round(passing_points, 2),
        "rushing_points": round(rushing_points, 2),
        "receiving_points": round(receiving_points, 2),
        "first_down_points": round(first_down_points, 2),
        "return_points": round(return_points, 2),
        "turnover_points": round(turnover_points, 2),
        "lve_points": round(lve_points, 2),
        "rush_rec_first_downs": round(rush_rec_first_downs, 2),
        "return_yards": round(return_yards, 2),
        "return_tds": round(return_tds, 2),
        "touches": round(touches, 2),
        "targets": round(_float(row.get("targets")), 2),
        "source": "nflverse_player_stats_weekly",
        "scoring_effect": "derived weekly scoring only; no model mutation",
    }


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _return_total(
    row: dict[str, str],
    total_key: str,
    kick_key: str,
    punt_key: str,
) -> float:
    if str(row.get(total_key) or "").strip():
        return _float(row.get(total_key))
    return _float(row.get(kick_key)) + _float(row.get(punt_key))
