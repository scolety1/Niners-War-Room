from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.services.model_v4_historical_rookie_tuning_service import HISTORICAL_BACKTEST_MATRIX
from src.services.model_v4_sprint12_13_review_service import _normalize_name

PLAYER_STATS_PATH = Path(
    "local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/historical_rookie_outcomes/latest")
OUTCOME_VERSION = "model_v4_rookie_outcome_labels_0.1.0"
OUTCOME_HEADER = (
    "draft_year",
    "player",
    "normalized_player_name",
    "position",
    "nfl_team",
    "draft_round",
    "draft_pick",
    "rookie_year_points",
    "rookie_year_ppg",
    "year2_points",
    "year2_ppg",
    "year3_points",
    "year3_ppg",
    "best_3yr_ppg",
    "starter_threshold",
    "starter_level_seasons",
    "outcome_label",
    "outcome_maturity",
    "seasons_loaded",
    "source_status",
    "warning_flags",
    "outcome_version",
)


@dataclass(frozen=True)
class RookieOutcomeLabelResult:
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_rookie_outcome_labels(
    backtest_matrix_path: str | Path = HISTORICAL_BACKTEST_MATRIX,
    player_stats_path: str | Path = PLAYER_STATS_PATH,
) -> RookieOutcomeLabelResult:
    prospects = _read_rows(Path(backtest_matrix_path))
    season_stats = _season_stats(Path(player_stats_path))
    rows: list[dict[str, object]] = []
    seen: set[tuple[int, str]] = set()
    for prospect in prospects:
        position = str(prospect.get("position", ""))
        if position not in {"QB", "RB", "WR", "TE"}:
            continue
        draft_year = _int(prospect.get("draft_year"))
        player = str(prospect.get("prospect_name", ""))
        normalized = _normalize_name(player)
        if draft_year is None or not normalized:
            continue
        key = (draft_year, normalized)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            _outcome_row(
                prospect=prospect,
                season_stats=season_stats,
                draft_year=draft_year,
                normalized=normalized,
            )
        )
    summary = {
        "outcome_version": OUTCOME_VERSION,
        "rows": len(rows),
        "labels_loaded": sum(1 for row in rows if row["seasons_loaded"]),
        "years": "|".join(sorted({str(row["draft_year"]) for row in rows})),
        "source": str(player_stats_path),
        "model_scores_changed": False,
    }
    return RookieOutcomeLabelResult(rows=tuple(rows), summary=summary)


def write_rookie_outcome_label_outputs(
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: RookieOutcomeLabelResult | None = None,
) -> dict[str, Path]:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_rookie_outcome_labels()
    labels_path = output / "historical_rookie_outcome_labels.csv"
    summary_path = output / "historical_rookie_outcome_summary.csv"
    _write_csv(labels_path, OUTCOME_HEADER, result.rows)
    _write_csv(
        summary_path,
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in result.summary.items()),
    )
    return {"labels": labels_path, "summary": summary_path}


def _outcome_row(
    *,
    prospect: dict[str, str],
    season_stats: dict[tuple[int, str], dict[str, object]],
    draft_year: int,
    normalized: str,
) -> dict[str, object]:
    position = str(prospect.get("position", ""))
    yearly: list[dict[str, object] | None] = [
        season_stats.get((draft_year + offset, normalized)) for offset in range(3)
    ]
    ppgs = [_ppg(row) for row in yearly]
    points = [_points(row) for row in yearly]
    loaded_ppgs = [ppg for ppg in ppgs if ppg is not None]
    threshold = _starter_threshold(position)
    starter_seasons = sum(1 for ppg in loaded_ppgs if ppg >= threshold)
    best = max(loaded_ppgs) if loaded_ppgs else None
    warning_flags: list[str] = []
    if not loaded_ppgs:
        warning_flags.append("outcome_not_found_in_rotowire_stats")
    if draft_year == 2025:
        maturity = "rookie_year_only"
        warning_flags.append("outcome_too_early")
    elif draft_year == 2024:
        maturity = "partial_two_year_window"
        warning_flags.append("year3_not_available")
    else:
        maturity = "three_year_window_available"
    label = _label(position, best, starter_seasons, maturity)
    return {
        "draft_year": draft_year,
        "player": prospect.get("prospect_name", ""),
        "normalized_player_name": normalized,
        "position": position,
        "nfl_team": prospect.get("nfl_team", ""),
        "draft_round": prospect.get("draft_round", ""),
        "draft_pick": prospect.get("draft_pick", ""),
        "rookie_year_points": _blank(points[0]),
        "rookie_year_ppg": _blank(ppgs[0]),
        "year2_points": _blank(points[1]),
        "year2_ppg": _blank(ppgs[1]),
        "year3_points": _blank(points[2]),
        "year3_ppg": _blank(ppgs[2]),
        "best_3yr_ppg": _blank(best),
        "starter_threshold": threshold,
        "starter_level_seasons": starter_seasons,
        "outcome_label": label,
        "outcome_maturity": maturity,
        "seasons_loaded": len(loaded_ppgs),
        "source_status": "rotowire_imported_real_outcome_display_only",
        "warning_flags": "|".join(warning_flags),
        "outcome_version": OUTCOME_VERSION,
    }


def _season_stats(path: Path) -> dict[tuple[int, str], dict[str, object]]:
    rows = _read_rows(path)
    grouped: dict[tuple[int, str], dict[str, object]] = {}
    for row in rows:
        if row.get("source_detail") != "fantasy":
            continue
        name = _normalize_name(str(row.get("player_name", "")))
        season = _int(row.get("season"))
        if season is None or not name:
            continue
        metrics = _json(row.get("metrics_json"))
        points = _float(metrics.get("fantasy_pts"))
        games = _float(row.get("games"))
        if points is None or games is None or games <= 0:
            continue
        key = (season, name)
        existing = grouped.get(key)
        if existing is None or points > float(existing["points"]):
            grouped[key] = {
                "season": season,
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "team": row.get("nfl_team", ""),
                "points": points,
                "games": games,
                "ppg": round(points / games, 4),
            }
    return grouped


def _label(
    position: str,
    best_ppg: float | None,
    starter_seasons: int,
    maturity: str,
) -> str:
    if best_ppg is None:
        return "not_loaded"
    if maturity == "rookie_year_only":
        prefix = "too_early_"
    elif maturity == "partial_two_year_window":
        prefix = "partial_"
    else:
        prefix = ""
    if position == "QB":
        if best_ppg >= 18.0:
            return f"{prefix}difference_maker"
        if best_ppg >= 15.0:
            return f"{prefix}starter"
        if best_ppg >= 12.0:
            return f"{prefix}usable"
        return f"{prefix}miss"
    if position == "TE":
        if best_ppg >= 10.5 or starter_seasons >= 2:
            return f"{prefix}difference_maker"
        if best_ppg >= 8.0 or starter_seasons >= 1:
            return f"{prefix}starter"
        if best_ppg >= 5.5:
            return f"{prefix}usable"
        return f"{prefix}miss"
    if best_ppg >= 13.0 or starter_seasons >= 2:
        return f"{prefix}difference_maker"
    if best_ppg >= 10.0 or starter_seasons >= 1:
        return f"{prefix}starter"
    if best_ppg >= 7.5:
        return f"{prefix}usable"
    return f"{prefix}miss"


def _starter_threshold(position: str) -> float:
    if position == "QB":
        return 15.0
    if position == "TE":
        return 8.0
    return 10.0


def _ppg(row: dict[str, object] | None) -> float | None:
    if row is None:
        return None
    return round(float(row["ppg"]), 4)


def _points(row: dict[str, object] | None) -> float | None:
    if row is None:
        return None
    return round(float(row["points"]), 4)


def _blank(value: float | None) -> float | str:
    return "" if value is None else value


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _json(value: object) -> dict[str, Any]:
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _int(value: object) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def _float(value: object) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(str(value))
    except ValueError:
        return None
