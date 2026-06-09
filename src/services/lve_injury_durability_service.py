from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.nflverse_raw_import_service import validate_nflverse_raw_imports

INJURY_DURABILITY_HEADER = (
    "season",
    "player_id",
    "gsis_id",
    "sleeper_id",
    "player_name",
    "position",
    "team",
    "current_status_score",
    "availability_rate",
    "injury_report_weeks",
    "questionable_weeks",
    "doubtful_weeks",
    "out_weeks",
    "limited_practice_weeks",
    "dnp_practice_weeks",
    "same_area_recurrence_count",
    "lower_body_risk_score",
    "injury_durability_score",
    "confidence",
    "risk_flags",
    "warnings",
    "scoring_effect",
)

REPORT_STATUS_PENALTIES = {
    "": 0.0,
    "probable": 3.0,
    "questionable": 12.0,
    "doubtful": 28.0,
    "out": 42.0,
}
PRACTICE_STATUS_PENALTIES = {
    "": 0.0,
    "full": 0.0,
    "limited": 7.0,
    "did not participate": 12.0,
    "dnp": 12.0,
}


@dataclass(frozen=True)
class InjuryDurabilityDerivationResult:
    status: str
    rows: tuple[dict[str, object], ...]
    issues: tuple[str, ...]


def derive_lve_injury_durability_rows(
    source_root: str | Path,
) -> InjuryDurabilityDerivationResult:
    raw_report = validate_nflverse_raw_imports(source_root)
    if raw_report.status == "blocked":
        return InjuryDurabilityDerivationResult(
            status="blocked",
            rows=(),
            issues=tuple(
                f"{issue.file_name}: {issue.issue}"
                for issue in raw_report.issues
                if issue.severity == "error"
            ),
        )

    root = Path(source_root)
    _, injury_rows = _read_csv(root / "nflverse_injuries_weekly.csv")
    _, stat_rows = _read_csv(root / "nflverse_player_stats_weekly.csv")
    _, snap_rows = _read_csv(root / "nflverse_snap_counts_weekly.csv")

    keys = sorted(
        {
            _player_key(row)
            for row in (*injury_rows, *stat_rows, *snap_rows)
            if _player_key(row)[0]
        }
    )
    rows = tuple(
        _derive_player_injury_row(
            key,
            [row for row in injury_rows if _player_key(row) == key],
            [row for row in stat_rows if _player_key(row) == key],
            [row for row in snap_rows if _player_key(row) == key],
        )
        for key in keys
    )
    return InjuryDurabilityDerivationResult(
        status="review" if raw_report.status == "review" else "ready",
        rows=rows,
        issues=tuple(f"{issue.file_name}: {issue.issue}" for issue in raw_report.issues),
    )


def write_lve_injury_durability_rows(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INJURY_DURABILITY_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _derive_player_injury_row(
    key: tuple[str, str, str, str],
    injury_rows: list[dict[str, str]],
    stat_rows: list[dict[str, str]],
    snap_rows: list[dict[str, str]],
) -> dict[str, object]:
    player_id, player_name, position, team = key
    season = _first_value((*injury_rows, *stat_rows, *snap_rows), "season")
    gsis_id = _first_value((*injury_rows, *stat_rows, *snap_rows), "gsis_id")
    sleeper_id = _first_value((*injury_rows, *stat_rows, *snap_rows), "sleeper_id")
    latest = _latest_injury_row(injury_rows)
    current_status_penalty = _current_status_penalty(latest)
    questionable = _count_status(injury_rows, "questionable")
    doubtful = _count_status(injury_rows, "doubtful")
    out = _count_status(injury_rows, "out")
    limited = _count_practice(injury_rows, "limited")
    dnp = _count_practice(injury_rows, "did not participate") + _count_practice(injury_rows, "dnp")
    active_weeks = _active_weeks(stat_rows, snap_rows)
    week_values = {
        row.get("week", "")
        for row in (*injury_rows, *stat_rows, *snap_rows)
        if row.get("week", "")
    }
    possible_weeks = max(
        len(week_values),
        active_weeks,
        1,
    )
    availability_rate = 100.0 * active_weeks / possible_weeks
    same_area_recurrence = _same_area_recurrence_count(injury_rows)
    lower_body_risk = _lower_body_risk_score(injury_rows, position)
    missed_games_penalty = max(0.0, 100.0 - availability_rate) * 0.22
    report_history_penalty = (questionable * 2.0) + (doubtful * 5.0) + (out * 7.5)
    practice_penalty = (limited * 1.5) + (dnp * 3.0)
    recurrence_penalty = min(20.0, same_area_recurrence * 6.0)
    lower_body_penalty = (100.0 - lower_body_risk) * _lower_body_penalty_rate(position)
    durability = _score(
        100.0
        - current_status_penalty
        - missed_games_penalty
        - report_history_penalty
        - practice_penalty
        - recurrence_penalty
        - lower_body_penalty
    )
    confidence, warnings = _confidence_and_warnings(injury_rows, stat_rows, snap_rows)
    risk_flags = _risk_flags(
        latest,
        position,
        out,
        same_area_recurrence,
        lower_body_risk,
        durability,
    )
    return {
        "season": season,
        "player_id": player_id,
        "gsis_id": gsis_id,
        "sleeper_id": sleeper_id,
        "player_name": player_name,
        "position": position,
        "team": team,
        "current_status_score": round(_score(100.0 - current_status_penalty), 2),
        "availability_rate": round(availability_rate, 2),
        "injury_report_weeks": len(injury_rows),
        "questionable_weeks": questionable,
        "doubtful_weeks": doubtful,
        "out_weeks": out,
        "limited_practice_weeks": limited,
        "dnp_practice_weeks": dnp,
        "same_area_recurrence_count": same_area_recurrence,
        "lower_body_risk_score": round(lower_body_risk, 2),
        "injury_durability_score": round(durability, 2),
        "confidence": round(confidence, 2),
        "risk_flags": "|".join(sorted(risk_flags)),
        "warnings": "|".join(sorted(warnings)),
        "scoring_effect": "derived injury durability only; no model mutation",
    }


def _current_status_penalty(row: dict[str, str] | None) -> float:
    if row is None:
        return 0.0
    report_status = _status_key(row.get("report_status", ""))
    practice_status = _status_key(row.get("practice_status", ""))
    return max(
        REPORT_STATUS_PENALTIES.get(report_status, 8.0 if report_status else 0.0),
        PRACTICE_STATUS_PENALTIES.get(practice_status, 4.0 if practice_status else 0.0),
    )


def _same_area_recurrence_count(rows: list[dict[str, str]]) -> int:
    areas = [
        row.get("normalized_body_part", "").strip().lower()
        for row in rows
        if row.get("normalized_body_part", "").strip()
    ]
    if not areas:
        return 0
    return max(0, max(areas.count(area) for area in set(areas)) - 1)


def _lower_body_risk_score(rows: list[dict[str, str]], position: str) -> float:
    lower_body_events = sum(
        1
        for row in rows
        if _is_lower_body(row.get("normalized_body_part", ""))
        or _is_lower_body(row.get("report_primary_injury", ""))
        or _is_lower_body(row.get("practice_primary_injury", ""))
    )
    if lower_body_events == 0:
        return 100.0
    penalty = lower_body_events * {
        "RB": 13.0,
        "WR": 11.0,
        "QB": 7.0,
        "TE": 9.0,
    }.get(position, 9.0)
    return _score(100.0 - penalty)


def _lower_body_penalty_rate(position: str) -> float:
    return {
        "RB": 0.14,
        "WR": 0.12,
        "QB": 0.06,
        "TE": 0.09,
    }.get(position, 0.09)


def _risk_flags(
    latest: dict[str, str] | None,
    position: str,
    out_weeks: int,
    recurrence_count: int,
    lower_body_risk: float,
    durability: float,
) -> set[str]:
    flags: set[str] = set()
    latest_status = _status_key(latest.get("report_status", "")) if latest else ""
    if latest_status in {"out", "doubtful"}:
        flags.add("current_injury_uncertainty")
    if out_weeks:
        flags.add("missed_games_injury_history")
    if recurrence_count >= 2:
        flags.add("same_area_recurrence")
    if lower_body_risk < 90 and position in {"RB", "WR"}:
        flags.add("rb_wr_lower_body_risk")
    if lower_body_risk < 80 and position == "QB":
        flags.add("qb_rushing_ceiling_risk")
    if durability < 60:
        flags.add("low_injury_durability")
    return flags


def _confidence_and_warnings(
    injury_rows: list[dict[str, str]],
    stat_rows: list[dict[str, str]],
    snap_rows: list[dict[str, str]],
) -> tuple[float, set[str]]:
    confidence = 100.0
    warnings: set[str] = set()
    if not injury_rows:
        confidence -= 10.0
        warnings.add("no_injury_report_rows")
    if not stat_rows and not snap_rows:
        confidence -= 20.0
        warnings.add("no_activity_rows")
    return _score(confidence), warnings


def _latest_injury_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    if not rows:
        return None
    return sorted(
        rows,
        key=lambda row: (
            _safe_int(row.get("season")),
            _safe_int(row.get("week")),
            row.get("date_modified", ""),
        ),
    )[-1]


def _count_status(rows: list[dict[str, str]], status: str) -> int:
    return sum(1 for row in rows if _status_key(row.get("report_status", "")) == status)


def _count_practice(rows: list[dict[str, str]], status: str) -> int:
    return sum(1 for row in rows if _status_key(row.get("practice_status", "")) == status)


def _active_weeks(
    stat_rows: list[dict[str, str]],
    snap_rows: list[dict[str, str]],
) -> int:
    active = {
        row.get("week", "")
        for row in snap_rows
        if _float(row.get("offense_snaps")) > 0
    }
    active.update(
        row.get("week", "")
        for row in stat_rows
        if _stat_activity(row) > 0
    )
    return len({week for week in active if week})


def _stat_activity(row: dict[str, str]) -> float:
    return sum(
        _float(row.get(column))
        for column in (
            "passing_yards",
            "rushing_attempts",
            "targets",
            "receptions",
            "receiving_yards",
        )
    )


def _player_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    player_id = row.get("player_id") or row.get("gsis_id") or row.get("sleeper_id") or ""
    return (
        player_id,
        row.get("player_name", ""),
        row.get("position", ""),
        row.get("team", ""),
    )


def _first_value(rows, column: str) -> str:
    for row in rows:
        value = row.get(column, "")
        if value:
            return value
    return ""


def _status_key(value: str) -> str:
    return value.strip().lower().replace("_", " ")


def _is_lower_body(value: str) -> bool:
    text = value.lower()
    return any(
        token in text
        for token in (
            "knee",
            "acl",
            "mcl",
            "meniscus",
            "ankle",
            "foot",
            "toe",
            "achilles",
            "hamstring",
            "quad",
            "calf",
            "groin",
            "lower_body",
        )
    )


def _safe_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)
