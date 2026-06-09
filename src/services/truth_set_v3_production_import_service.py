from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

OFFICIAL_PLAYER_STATS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats.csv"
)
DEFAULT_TRUTH_SET_SOURCE = Path("local_exports/truth_set_lab/v1/source_clean/projections.csv")
DEFAULT_LOCAL_PLAYER_STATS_SOURCE = Path(
    "local_exports/nflverse/preview/sprint2_phase7_public_20260514/downloads/player_stats.csv"
)

V3_PRODUCTION_WEEK_HEADER = (
    "truth_set_player_name",
    "matched_player_name",
    "match_status",
    "player_id",
    "season",
    "week",
    "team",
    "position",
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
    "rushing_first_downs",
    "receiving_first_downs",
    "total_fumbles",
    "fumbles_lost",
    "source_status",
    "source_name",
    "source_url",
    "source_date",
    "notes",
)

V3_PRODUCTION_SEASON_HEADER = (
    "truth_set_player_name",
    "matched_player_name",
    "match_status",
    "player_id",
    "season",
    "games",
    "team",
    "position",
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
    "rushing_first_downs",
    "receiving_first_downs",
    "total_fumbles",
    "fumbles_lost",
    "source_status",
    "source_name",
    "source_url",
    "source_date",
    "notes",
)

V3_PRODUCTION_MISSING_HEADER = (
    "truth_set_player_name",
    "position",
    "nfl_team",
    "match_status",
    "source_status",
    "reason",
    "notes",
)

V3_PRODUCTION_SUMMARY_HEADER = (
    "metric",
    "value",
)

REQUIRED_SOURCE_FIELDS = (
    "player_id",
    "player_display_name",
    "position",
    "recent_team",
    "season",
    "week",
    "season_type",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "rushing_first_downs",
    "receiving_first_downs",
)

NUMERIC_SOURCE_FIELDS = (
    "season",
    "week",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "rushing_first_downs",
    "receiving_first_downs",
    "rushing_fumbles",
    "receiving_fumbles",
    "sack_fumbles",
    "rushing_fumbles_lost",
    "receiving_fumbles_lost",
    "sack_fumbles_lost",
)

PLAYER_NAME_ALIASES = {
    "hollywood brown": "marquise brown",
}


@dataclass(frozen=True)
class TruthSetPlayer:
    player_name: str
    position: str
    nfl_team: str


@dataclass(frozen=True)
class TruthSetV3ProductionResult:
    week_rows: tuple[dict[str, object], ...]
    season_rows: tuple[dict[str, object], ...]
    missing_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]
    validation_errors: tuple[str, ...]


def build_truth_set_v3_production_preview(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET_SOURCE,
    player_stats_path: str | Path = DEFAULT_LOCAL_PLAYER_STATS_SOURCE,
    download_if_missing: bool = True,
    seasons: set[int] | None = None,
    season_type: str = "REG",
    source_url: str = OFFICIAL_PLAYER_STATS_URL,
) -> TruthSetV3ProductionResult:
    truth_players = _read_truth_set_players(Path(truth_set_path))
    source_path = Path(player_stats_path)
    if not source_path.exists() and download_if_missing:
        _download_player_stats(source_path, source_url=source_url)

    source_header, source_rows = _read_csv(source_path)
    validation_errors = _validate_source_header_and_values(source_header, source_rows)
    if validation_errors:
        return TruthSetV3ProductionResult(
            week_rows=(),
            season_rows=(),
            missing_rows=(),
            summary={
                "status": "blocked",
                "truth_set_players": len(truth_players),
                "source_rows_seen": len(source_rows),
                "validation_errors": len(validation_errors),
                "active_rankings_overwritten": False,
                "review_status": "review_only",
            },
            validation_errors=tuple(validation_errors),
        )

    season_filter = seasons or _recent_available_seasons(source_rows, desired=3)
    source_date = _source_date(source_path)
    truth_by_key = {
        _canonical_name_key(player.player_name): player for player in truth_players
    }
    source_by_key: dict[str, list[dict[str, str]]] = {}
    for row in source_rows:
        if row.get("season_type") != season_type:
            continue
        if _int(row.get("season")) not in season_filter:
            continue
        if row.get("position") not in {"QB", "RB", "WR", "TE"}:
            continue
        key = _canonical_name_key(_player_name(row))
        if key in truth_by_key:
            source_by_key.setdefault(key, []).append(row)

    week_rows: list[dict[str, object]] = []
    missing_rows: list[dict[str, object]] = []
    for player in truth_players:
        rows = sorted(
            source_by_key.get(_canonical_name_key(player.player_name), []),
            key=lambda row: (_int(row.get("season")), _int(row.get("week"))),
        )
        if not rows:
            missing_rows.append(_missing_row(player, season_filter))
            continue
        for row in rows:
            week_rows.append(_week_row(player, row, source_url, source_date))

    season_rows = _season_rows(week_rows, source_url, source_date)
    summary = _summary(
        truth_players=truth_players,
        source_rows=source_rows,
        week_rows=week_rows,
        season_rows=season_rows,
        missing_rows=missing_rows,
        season_filter=season_filter,
        source_path=source_path,
    )
    return TruthSetV3ProductionResult(
        week_rows=tuple(week_rows),
        season_rows=tuple(season_rows),
        missing_rows=tuple(missing_rows),
        summary=summary,
        validation_errors=(),
    )


def write_truth_set_v3_production_outputs(
    output_root: str | Path,
    result: TruthSetV3ProductionResult,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "week": root / "truth_set_v3_production_player_week.csv",
        "season": root / "truth_set_v3_production_player_season.csv",
        "missing": root / "truth_set_v3_production_missing_players.csv",
        "summary_csv": root / "truth_set_v3_production_summary.csv",
        "summary_json": root / "truth_set_v3_production_summary.json",
    }
    _write_csv(paths["week"], V3_PRODUCTION_WEEK_HEADER, result.week_rows)
    _write_csv(paths["season"], V3_PRODUCTION_SEASON_HEADER, result.season_rows)
    _write_csv(paths["missing"], V3_PRODUCTION_MISSING_HEADER, result.missing_rows)
    _write_csv(
        paths["summary_csv"],
        V3_PRODUCTION_SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    paths["summary_json"].write_text(
        json.dumps(result.summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def _read_truth_set_players(path: Path) -> list[TruthSetPlayer]:
    _, rows = _read_csv(path)
    players: dict[str, TruthSetPlayer] = {}
    for row in rows:
        name = str(row.get("player_name", "")).strip()
        if not name:
            continue
        players[_canonical_name_key(name)] = TruthSetPlayer(
            player_name=name,
            position=str(row.get("position", "")).strip(),
            nfl_team=str(row.get("nfl_team", "")).strip(),
        )
    return list(players.values())


def _validate_source_header_and_values(
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> list[str]:
    errors: list[str] = []
    missing_fields = [field for field in REQUIRED_SOURCE_FIELDS if field not in header]
    first_down_fields = {"rushing_first_downs", "receiving_first_downs"}
    if not first_down_fields.issubset(set(header)):
        errors.append("source is missing required first-down fields")
    if missing_fields:
        errors.append(f"missing required source fields: {'|'.join(missing_fields)}")
        return errors

    for row_number, row in enumerate(rows, start=2):
        for field in NUMERIC_SOURCE_FIELDS:
            if field not in header:
                continue
            value = str(row.get(field, "")).strip()
            if value and not _is_float(value):
                errors.append(f"row {row_number}: {field} must be numeric or blank")
                if len(errors) >= 25:
                    return errors
    return errors


def _recent_available_seasons(
    rows: list[dict[str, str]],
    *,
    desired: int,
) -> set[int]:
    seasons = sorted({_int(row.get("season")) for row in rows if _int(row.get("season"))})
    return set(seasons[-desired:])


def _week_row(
    truth_player: TruthSetPlayer,
    source: dict[str, str],
    source_url: str,
    source_date: str,
) -> dict[str, object]:
    return {
        "truth_set_player_name": truth_player.player_name,
        "matched_player_name": _player_name(source),
        "match_status": "name_position_match",
        "player_id": source.get("player_id", ""),
        "season": _int(source.get("season")),
        "week": _int(source.get("week")),
        "team": source.get("recent_team", ""),
        "position": source.get("position", ""),
        "passing_yards": _num(source, "passing_yards"),
        "passing_tds": _num(source, "passing_tds"),
        "interceptions": _num(source, "interceptions"),
        "rushing_attempts": _num(source, "carries"),
        "rushing_yards": _num(source, "rushing_yards"),
        "rushing_tds": _num(source, "rushing_tds"),
        "targets": _num(source, "targets"),
        "receptions": _num(source, "receptions"),
        "receiving_yards": _num(source, "receiving_yards"),
        "receiving_tds": _num(source, "receiving_tds"),
        "rushing_first_downs": _num(source, "rushing_first_downs"),
        "receiving_first_downs": _num(source, "receiving_first_downs"),
        "total_fumbles": _sum(source, "rushing_fumbles", "receiving_fumbles", "sack_fumbles"),
        "fumbles_lost": _sum(
            source,
            "rushing_fumbles_lost",
            "receiving_fumbles_lost",
            "sack_fumbles_lost",
        ),
        "source_status": "imported_real_data",
        "source_name": "nflverse_player_stats",
        "source_url": source_url,
        "source_date": source_date,
        "notes": "native_nflverse_player_stats",
    }


def _season_rows(
    week_rows: list[dict[str, object]],
    source_url: str,
    source_date: str,
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int], list[dict[str, object]]] = {}
    for row in week_rows:
        grouped.setdefault(
            (str(row["truth_set_player_name"]), int(row["season"])),
            [],
        ).append(row)

    season_rows: list[dict[str, object]] = []
    stat_fields = (
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
        "rushing_first_downs",
        "receiving_first_downs",
        "total_fumbles",
        "fumbles_lost",
    )
    for (truth_name, season), rows in sorted(grouped.items(), key=lambda item: item[0]):
        latest = sorted(rows, key=lambda row: int(row["week"]))[-1]
        season_rows.append(
            {
                "truth_set_player_name": truth_name,
                "matched_player_name": latest["matched_player_name"],
                "match_status": latest["match_status"],
                "player_id": latest["player_id"],
                "season": season,
                "games": len({int(row["week"]) for row in rows}),
                "team": latest["team"],
                "position": latest["position"],
                **{
                    field: _clean_number(sum(float(row[field]) for row in rows))
                    for field in stat_fields
                },
                "source_status": "imported_real_data",
                "source_name": "nflverse_player_stats",
                "source_url": source_url,
                "source_date": source_date,
                "notes": "aggregated_from_native_nflverse_player_week_rows",
            }
        )
    return season_rows


def _missing_row(player: TruthSetPlayer, season_filter: set[int]) -> dict[str, object]:
    return {
        "truth_set_player_name": player.player_name,
        "position": player.position,
        "nfl_team": player.nfl_team,
        "match_status": "missing_nflverse_player_stats",
        "source_status": "missing",
        "reason": (
            "No native nflverse player_stats rows matched this truth-set player "
            "in requested seasons."
        ),
        "notes": f"requested_seasons={','.join(str(season) for season in sorted(season_filter))}",
    }


def _summary(
    *,
    truth_players: list[TruthSetPlayer],
    source_rows: list[dict[str, str]],
    week_rows: list[dict[str, object]],
    season_rows: list[dict[str, object]],
    missing_rows: list[dict[str, object]],
    season_filter: set[int],
    source_path: Path,
) -> dict[str, object]:
    matched_players = {row["truth_set_player_name"] for row in week_rows}
    first_down_rows = [
        row
        for row in week_rows
        if float(row["rushing_first_downs"]) != 0
        or float(row["receiving_first_downs"]) != 0
    ]
    return {
        "status": "ready",
        "review_status": "review_only",
        "truth_set_players": len(truth_players),
        "matched_players": len(matched_players),
        "missing_players": len(missing_rows),
        "source_rows_seen": len(source_rows),
        "week_rows": len(week_rows),
        "season_rows": len(season_rows),
        "latest_available_source_season": max(
            (_int(row.get("season")) for row in source_rows),
            default=0,
        ),
        "requested_seasons": "|".join(str(season) for season in sorted(season_filter)),
        "first_down_fields_present": True,
        "week_rows_with_first_downs": len(first_down_rows),
        "source_status": "imported_real_data",
        "source_path": str(source_path),
        "active_rankings_overwritten": False,
        "model_scores_changed": False,
    }


def _download_player_stats(path: Path, *, source_url: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(source_url, headers={"User-Agent": "niners-war-room-local-import"})
    with urlopen(request, timeout=60) as response:  # nosec B310 - explicit nflverse URL.
        path.write_bytes(response.read())


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _player_name(row: dict[str, str]) -> str:
    return str(row.get("player_display_name") or row.get("player_name") or "").strip()


def _name_key(value: str) -> str:
    normalized = value.lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"['’`.\-]", "", normalized)
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _canonical_name_key(value: str) -> str:
    key = _name_key(value)
    return PLAYER_NAME_ALIASES.get(key, key)


def _num(row: dict[str, str], field: str) -> float | int:
    return _clean_number(_float(row.get(field)))


def _sum(row: dict[str, str], *fields: str) -> float | int:
    return _clean_number(sum(_float(row.get(field)) for field in fields))


def _clean_number(value: float) -> float | int:
    if value.is_integer():
        return int(value)
    return round(value, 3)


def _int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _is_float(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _source_date(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    except OSError:
        return ""
