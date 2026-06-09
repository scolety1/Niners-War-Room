from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.nflverse_raw_import_service import validate_nflverse_raw_imports

ROLE_USAGE_FEATURE_HEADER = (
    "season",
    "player_id",
    "gsis_id",
    "sleeper_id",
    "player_name",
    "position",
    "team",
    "games_active_score",
    "snap_share_score",
    "starter_week_score",
    "depth_chart_role_score",
    "route_role_score",
    "targets_per_route_proxy_score",
    "workload_earning_score",
    "target_earning_stability_score",
    "target_earning_source_detail",
    "role_security",
    "role_fragility_risk_score",
    "confidence",
    "warnings",
    "scoring_effect",
)

STARTER_SNAP_THRESHOLDS = {
    "QB": 70.0,
    "RB": 45.0,
    "WR": 65.0,
    "TE": 60.0,
}


@dataclass(frozen=True)
class RoleUsageDerivationResult:
    status: str
    rows: tuple[dict[str, object], ...]
    issues: tuple[str, ...]


def derive_lve_role_usage_feature_rows(
    source_root: str | Path,
) -> RoleUsageDerivationResult:
    raw_report = validate_nflverse_raw_imports(source_root)
    if raw_report.status == "blocked":
        return RoleUsageDerivationResult(
            status="blocked",
            rows=(),
            issues=tuple(
                f"{issue.file_name}: {issue.issue}"
                for issue in raw_report.issues
                if issue.severity == "error"
            ),
        )

    root = Path(source_root)
    _, stat_rows = _read_csv(root / "nflverse_player_stats_weekly.csv")
    _, snap_rows = _read_csv(root / "nflverse_snap_counts_weekly.csv")
    _, participation_rows = _read_csv(root / "nflverse_participation_player_weekly.csv")
    _, depth_rows = _read_csv(root / "nflverse_depth_chart_weekly.csv")

    keys = sorted(
        {
            _player_key(row)
            for row in (*stat_rows, *snap_rows, *participation_rows, *depth_rows)
            if _player_key(row)[0]
        }
    )
    rows = tuple(
        _derive_player_role_row(
            key,
            [row for row in stat_rows if _player_key(row) == key],
            [row for row in snap_rows if _player_key(row) == key],
            [row for row in participation_rows if _player_key(row) == key],
            [row for row in depth_rows if _player_key(row) == key],
        )
        for key in keys
    )
    return RoleUsageDerivationResult(
        status="review" if raw_report.status == "review" else "ready",
        rows=rows,
        issues=tuple(f"{issue.file_name}: {issue.issue}" for issue in raw_report.issues),
    )


def write_lve_role_usage_feature_rows(
    output_path: str | Path,
    rows: tuple[dict[str, object], ...],
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROLE_USAGE_FEATURE_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _derive_player_role_row(
    key: tuple[str, str, str, str],
    stat_rows: list[dict[str, str]],
    snap_rows: list[dict[str, str]],
    participation_rows: list[dict[str, str]],
    depth_rows: list[dict[str, str]],
) -> dict[str, object]:
    player_id, player_name, position, team = key
    source_rows = (*stat_rows, *snap_rows, *participation_rows, *depth_rows)
    player_name = _latest_value(source_rows, "player_name") or player_name
    position = _latest_value(source_rows, "position") or position
    team = _latest_value(source_rows, "team") or team
    season = _latest_value(source_rows, "season")
    gsis_id = _first_value(source_rows, "gsis_id")
    sleeper_id = _first_value(
        source_rows,
        "sleeper_id",
    )
    games_active = _games_active(stat_rows, snap_rows)
    week_values = {
        row.get("week", "")
        for row in (*stat_rows, *snap_rows, *participation_rows)
        if row.get("week", "")
    }
    possible_games = max(
        len(week_values),
        games_active,
        1,
    )
    avg_snap_share = _avg(row.get("offense_pct") for row in snap_rows)
    starter_week_rate = _starter_week_rate(position, snap_rows, depth_rows)
    depth_score = _depth_chart_score(position, depth_rows)
    route_role = _avg(row.get("route_participation_proxy") for row in participation_rows)
    tprr_proxy = _avg(row.get("targets_per_dropback_snap_proxy") for row in participation_rows)
    workload = _workload_earning(position, stat_rows, participation_rows, avg_snap_share)
    target_earning = _target_earning(position, stat_rows, participation_rows)
    target_earning_detail = _target_earning_source_detail(
        position,
        stat_rows,
        participation_rows,
    )
    games_active_score = _score(100.0 * games_active / possible_games)
    snap_share_score = _score(avg_snap_share)
    starter_week_score = _score(starter_week_rate)
    route_role_score = _score(route_role)
    tprr_score = _score(tprr_proxy * 100 if tprr_proxy <= 1 else tprr_proxy)
    workload_score = _score(workload)
    target_score = _score(target_earning)
    role_security = _role_security(
        position,
        games_active_score,
        snap_share_score,
        starter_week_score,
        depth_score,
        route_role_score,
        tprr_score,
        workload_score,
        target_score,
    )
    confidence, warnings = _confidence_and_warnings(
        snap_rows,
        participation_rows,
        depth_rows,
        route_role_score,
        position,
    )
    return {
        "season": season,
        "player_id": player_id,
        "gsis_id": gsis_id,
        "sleeper_id": sleeper_id,
        "player_name": player_name,
        "position": position,
        "team": team,
        "games_active_score": round(games_active_score, 2),
        "snap_share_score": round(snap_share_score, 2),
        "starter_week_score": round(starter_week_score, 2),
        "depth_chart_role_score": round(depth_score, 2),
        "route_role_score": round(route_role_score, 2),
        "targets_per_route_proxy_score": round(tprr_score, 2),
        "workload_earning_score": round(workload_score, 2),
        "target_earning_stability_score": round(target_score, 2),
        "target_earning_source_detail": target_earning_detail,
        "role_security": round(role_security, 2),
        "role_fragility_risk_score": round(_score(100 - role_security), 2),
        "confidence": round(confidence, 2),
        "warnings": "|".join(sorted(warnings)),
        "scoring_effect": "derived role/usage features only; no model mutation",
    }


def _role_security(
    position: str,
    games_active_score: float,
    snap_share_score: float,
    starter_week_score: float,
    depth_score: float,
    route_role_score: float,
    tprr_score: float,
    workload_score: float,
    target_score: float,
) -> float:
    if position == "QB":
        return _score(
            (0.45 * starter_week_score)
            + (0.25 * snap_share_score)
            + (0.20 * depth_score)
            + (0.10 * games_active_score)
        )
    if position == "RB":
        return _score(
            (0.30 * workload_score)
            + (0.20 * snap_share_score)
            + (0.20 * starter_week_score)
            + (0.15 * target_score)
            + (0.10 * depth_score)
            + (0.05 * games_active_score)
        )
    if position == "WR":
        return _score(
            (0.35 * route_role_score)
            + (0.25 * target_score)
            + (0.15 * snap_share_score)
            + (0.15 * starter_week_score)
            + (0.10 * depth_score)
        )
    role = _score(
        (0.40 * route_role_score)
        + (0.25 * target_score)
        + (0.15 * snap_share_score)
        + (0.10 * starter_week_score)
        + (0.10 * depth_score)
    )
    if route_role_score < 30:
        return min(role, 40.0)
    if route_role_score < 45:
        return min(role, 55.0)
    return role


def _workload_earning(
    position: str,
    stat_rows: list[dict[str, str]],
    participation_rows: list[dict[str, str]],
    avg_snap_share: float,
) -> float:
    rushes = sum(_float(row.get("rushing_attempts")) for row in stat_rows)
    targets = sum(_float(row.get("targets")) for row in stat_rows)
    if not stat_rows:
        targets = sum(_float(row.get("targets")) for row in participation_rows)
    if position == "RB":
        games = max(len(stat_rows), 1)
        weighted_opps_per_game = ((rushes + (1.15 * targets)) / games)
        return _score((weighted_opps_per_game / 18.0 * 70.0) + (avg_snap_share * 0.30))
    if position in {"WR", "TE"}:
        games = max(len(stat_rows), 1)
        return _score((targets / games) * 10.0)
    return avg_snap_share


def _target_earning(
    position: str,
    stat_rows: list[dict[str, str]],
    participation_rows: list[dict[str, str]],
) -> float:
    targets = sum(_float(row.get("targets")) for row in stat_rows)
    if not stat_rows:
        targets = sum(_float(row.get("targets")) for row in participation_rows)
    games = max(len(stat_rows), len(participation_rows), 1)
    if position == "RB":
        target_volume_score = _score((targets / games) * 16.0)
        target_share_score = _avg_rate_score(stat_rows, "target_share", anchor=16.0)
        weighted_parts = ((target_volume_score, 0.70),)
        if target_share_score is not None:
            weighted_parts = (*weighted_parts, (target_share_score, 0.30))
        return _weighted_score(*weighted_parts)
    if position == "TE":
        return _receiving_target_earning_score(
            stat_rows,
            targets_per_game=targets / games,
            target_volume_multiplier=18.0,
            target_share_anchor=22.0,
            wopr_anchor=55.0,
            air_yards_share_anchor=25.0,
        )
    if position == "WR":
        return _receiving_target_earning_score(
            stat_rows,
            targets_per_game=targets / games,
            target_volume_multiplier=12.0,
            target_share_anchor=30.0,
            wopr_anchor=75.0,
            air_yards_share_anchor=40.0,
        )
    return 50.0


def _receiving_target_earning_score(
    stat_rows: list[dict[str, str]],
    *,
    targets_per_game: float,
    target_volume_multiplier: float,
    target_share_anchor: float,
    wopr_anchor: float,
    air_yards_share_anchor: float,
) -> float:
    volume_score = _score(targets_per_game * target_volume_multiplier)
    target_share_score = _avg_rate_score(
        stat_rows,
        "target_share",
        anchor=target_share_anchor,
    )
    wopr_score = _avg_rate_score(stat_rows, "wopr", anchor=wopr_anchor)
    air_yards_score = _avg_rate_score(
        stat_rows,
        "air_yards_share",
        anchor=air_yards_share_anchor,
    )
    weighted_parts: tuple[tuple[float, float], ...] = ((volume_score, 0.35),)
    if target_share_score is not None:
        weighted_parts = (*weighted_parts, (target_share_score, 0.35))
    if wopr_score is not None:
        weighted_parts = (*weighted_parts, (wopr_score, 0.20))
    if air_yards_score is not None:
        weighted_parts = (*weighted_parts, (air_yards_score, 0.10))
    return _weighted_score(*weighted_parts)


def _target_earning_source_detail(
    position: str,
    stat_rows: list[dict[str, str]],
    participation_rows: list[dict[str, str]],
) -> str:
    games = max(len(stat_rows), len(participation_rows), 1)
    targets = sum(_float(row.get("targets")) for row in stat_rows)
    if not stat_rows:
        targets = sum(_float(row.get("targets")) for row in participation_rows)
    detail = [f"targets_per_game={round(targets / games, 2)}"]
    if position in {"RB", "WR", "TE"}:
        target_share = _avg_rate_raw(stat_rows, "target_share")
        if target_share is not None:
            detail.append(f"target_share={round(target_share, 3)}")
    if position in {"WR", "TE"}:
        air_yards_share = _avg_rate_raw(stat_rows, "air_yards_share")
        wopr = _avg_rate_raw(stat_rows, "wopr")
        if air_yards_share is not None:
            detail.append(f"air_yards_share={round(air_yards_share, 3)}")
        if wopr is not None:
            detail.append(f"wopr={round(wopr, 3)}")
    return ";".join(detail)


def _games_active(
    stat_rows: list[dict[str, str]],
    snap_rows: list[dict[str, str]],
) -> int:
    active_weeks = {
        row.get("week", "")
        for row in snap_rows
        if _float(row.get("offense_snaps")) > 0
    }
    active_weeks.update(
        row.get("week", "")
        for row in stat_rows
        if _stat_activity(row) > 0
    )
    return len({week for week in active_weeks if week})


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


def _starter_week_rate(
    position: str,
    snap_rows: list[dict[str, str]],
    depth_rows: list[dict[str, str]],
) -> float:
    threshold = STARTER_SNAP_THRESHOLDS.get(position, 65.0)
    snap_starts = sum(1 for row in snap_rows if _float(row.get("offense_pct")) >= threshold)
    depth_start_weeks = {
        row.get("week", "")
        for row in depth_rows
        if _float(row.get("pos_rank")) == 1
    }
    denominator = max(len({row.get("week", "") for row in (*snap_rows, *depth_rows)}), 1)
    return _score(100.0 * max(snap_starts, len(depth_start_weeks)) / denominator)


def _depth_chart_score(position: str, depth_rows: list[dict[str, str]]) -> float:
    ranks = [_float(row.get("pos_rank")) for row in depth_rows if row.get("pos_rank")]
    if not ranks:
        return 50.0
    avg_rank = sum(ranks) / len(ranks)
    if position == "RB":
        mapping = {1: 100.0, 2: 78.0, 3: 55.0}
    else:
        mapping = {1: 100.0, 2: 70.0, 3: 45.0}
    return mapping.get(int(round(avg_rank)), 30.0)


def _confidence_and_warnings(
    snap_rows: list[dict[str, str]],
    participation_rows: list[dict[str, str]],
    depth_rows: list[dict[str, str]],
    route_role_score: float,
    position: str,
) -> tuple[float, set[str]]:
    warnings: set[str] = set()
    confidence = 100.0
    if not snap_rows:
        confidence -= 20.0
        warnings.add("missing_snap_counts")
    if not participation_rows:
        confidence -= 18.0
        warnings.add("missing_participation_proxy")
    if not depth_rows:
        confidence -= 8.0
        warnings.add("missing_depth_chart")
    if position == "TE" and route_role_score < 45:
        warnings.add("te_route_role_gate")
    return _score(confidence), warnings


def _player_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    player_id = row.get("player_id") or row.get("gsis_id") or row.get("sleeper_id") or ""
    return (
        player_id,
        "",
        "",
        "",
    )


def _first_value(rows, column: str) -> str:
    for row in rows:
        value = row.get(column, "")
        if value:
            return value
    return ""


def _latest_value(rows, column: str) -> str:
    latest_sort_key = (-1, -1)
    latest_value = ""
    for row in rows:
        value = row.get(column, "")
        if not value:
            continue
        sort_key = (
            int(_float(row.get("season"))),
            int(_float(row.get("week"))),
        )
        if sort_key >= latest_sort_key:
            latest_sort_key = sort_key
            latest_value = value
    return latest_value


def _avg(values) -> float:
    numbers = [_float(value) for value in values if str(value or "").strip()]
    if not numbers:
        return 50.0
    return sum(numbers) / len(numbers)


def _avg_rate_score(
    rows: list[dict[str, str]],
    column: str,
    *,
    anchor: float,
) -> float | None:
    values = [
        _float(row.get(column))
        for row in rows
        if str(row.get(column) or "").strip()
    ]
    if not values:
        return None
    value = sum(values) / len(values)
    if abs(value) <= 1:
        value *= 100
    return _score((value / anchor) * 100.0)


def _avg_rate_raw(rows: list[dict[str, str]], column: str) -> float | None:
    values = [
        _float(row.get(column))
        for row in rows
        if str(row.get(column) or "").strip()
    ]
    if not values:
        return None
    return sum(values) / len(values)


def _weighted_score(*parts: tuple[float, float]) -> float:
    denominator = sum(weight for _, weight in parts)
    if denominator <= 0:
        return 50.0
    return _score(sum(score * weight for score, weight in parts) / denominator)


def _score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)
