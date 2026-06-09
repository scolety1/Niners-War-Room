from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

from src.services.truth_set_v3_production_import_service import (
    DEFAULT_LOCAL_PLAYER_STATS_SOURCE,
    DEFAULT_TRUTH_SET_SOURCE,
    build_truth_set_v3_production_preview,
)

PBP_URL_PATTERN = (
    "https://github.com/nflverse/nflverse-data/releases/download/pbp/"
    "play_by_play_{season}.csv.gz"
)
DEFAULT_DOWNLOAD_ROOT = Path("local_exports/truth_set_lab/v3/downloads")
DEFAULT_REPORT_ROOT = Path("local_exports/truth_set_lab/v3/reports")

PBP_USE_COLUMNS = {
    "season",
    "week",
    "posteam",
    "play_type",
    "pass_attempt",
    "rush_attempt",
    "no_play",
    "yardline_100",
    "ydstogo",
    "rusher_player_id",
    "rusher_player_name",
    "receiver_player_id",
    "receiver_player_name",
}

V3_USAGE_WEEK_HEADER = (
    "truth_set_player_name",
    "matched_player_name",
    "player_id",
    "season",
    "week",
    "team",
    "position",
    "targets",
    "team_targets",
    "target_share",
    "rb_target_share",
    "rushing_attempts",
    "team_rushing_attempts",
    "rb_carry_share",
    "weighted_opportunities",
    "red_zone_carries",
    "red_zone_targets",
    "goal_line_carries",
    "goal_line_targets",
    "short_yardage_carries",
    "source_status",
    "source_name",
    "source_url",
    "source_date",
    "notes",
)

V3_USAGE_SEASON_HEADER = (
    "truth_set_player_name",
    "matched_player_name",
    "player_id",
    "season",
    "games_with_usage",
    "team",
    "position",
    "targets",
    "team_targets",
    "target_share",
    "rb_target_share",
    "rushing_attempts",
    "team_rushing_attempts",
    "rb_carry_share",
    "weighted_opportunities",
    "red_zone_carries",
    "red_zone_targets",
    "goal_line_carries",
    "goal_line_targets",
    "short_yardage_carries",
    "source_status",
    "source_name",
    "source_url",
    "source_date",
    "notes",
)

V3_USAGE_MISSING_HEADER = (
    "truth_set_player_name",
    "position",
    "nfl_team",
    "match_status",
    "source_status",
    "reason",
    "notes",
)

V3_USAGE_SUMMARY_HEADER = (
    "metric",
    "value",
)


@dataclass(frozen=True)
class UsagePlayer:
    truth_set_player_name: str
    matched_player_name: str
    player_id: str
    position: str
    nfl_team: str


@dataclass(frozen=True)
class UsagePlayerWeek:
    player_id: str
    season: int
    week: int
    team: str


@dataclass(frozen=True)
class TruthSetV3UsageResult:
    week_rows: tuple[dict[str, object], ...]
    season_rows: tuple[dict[str, object], ...]
    missing_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_truth_set_v3_usage_preview(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET_SOURCE,
    player_stats_path: str | Path = DEFAULT_LOCAL_PLAYER_STATS_SOURCE,
    pbp_download_root: str | Path = DEFAULT_DOWNLOAD_ROOT,
    seasons: set[int] | None = None,
    download_if_missing: bool = True,
) -> TruthSetV3UsageResult:
    production = build_truth_set_v3_production_preview(
        truth_set_path=truth_set_path,
        player_stats_path=player_stats_path,
        download_if_missing=False,
        seasons=seasons,
    )
    requested_seasons = (
        seasons
        or {
            int(season)
            for season in str(production.summary.get("requested_seasons", "")).split("|")
            if season
        }
    )
    players = _players_from_production_rows(production.week_rows)
    player_weeks = _player_weeks_from_production_rows(production.week_rows)
    truth_players = _truth_players(truth_set_path)

    pbp_rows: list[dict[str, object]] = []
    source_paths: list[Path] = []
    for season in sorted(requested_seasons):
        path = Path(pbp_download_root) / f"play_by_play_{season}.csv.gz"
        if not path.exists() and download_if_missing:
            _download_pbp(path, season=season)
        if not path.exists():
            continue
        source_paths.append(path)
        pbp_rows.extend(_read_pbp_rows(path))

    week_rows = derive_usage_week_rows_from_pbp_rows(
        pbp_rows,
        players=players,
        player_weeks=player_weeks,
        source_paths=source_paths,
    )
    season_rows = aggregate_usage_season_rows(week_rows)
    missing_rows = _missing_rows(truth_players, players)
    summary = _summary(
        truth_players=truth_players,
        players=players,
        pbp_rows=pbp_rows,
        week_rows=week_rows,
        season_rows=season_rows,
        missing_rows=missing_rows,
        requested_seasons=requested_seasons,
        source_paths=source_paths,
    )
    return TruthSetV3UsageResult(
        week_rows=tuple(week_rows),
        season_rows=tuple(season_rows),
        missing_rows=tuple(missing_rows),
        summary=summary,
    )


def derive_usage_week_rows_from_pbp_rows(
    pbp_rows: list[dict[str, object]],
    *,
    players: list[UsagePlayer],
    player_weeks: list[UsagePlayerWeek] | None = None,
    source_paths: list[Path] | None = None,
) -> list[dict[str, object]]:
    players_by_id = {player.player_id: player for player in players if player.player_id}
    team_week: dict[tuple[int, int, str], dict[str, float]] = {}
    player_week: dict[tuple[str, int, int, str], dict[str, float]] = {}
    for active_week in player_weeks or []:
        if active_week.player_id in players_by_id:
            _player_bucket(
                player_week,
                active_week.player_id,
                active_week.season,
                active_week.week,
                active_week.team,
            )

    for row in pbp_rows:
        if _float(row.get("no_play")) == 1:
            continue
        season = _int(row.get("season"))
        week = _int(row.get("week"))
        team = str(row.get("posteam") or "").strip()
        if not season or not week or not team:
            continue

        team_key = (season, week, team)
        team_bucket = team_week.setdefault(
            team_key,
            {"team_targets": 0.0, "team_rushing_attempts": 0.0},
        )

        is_rush = _float(row.get("rush_attempt")) == 1
        is_target = (
            _float(row.get("pass_attempt")) == 1
            and bool(str(row.get("receiver_player_id") or "").strip())
        )
        yardline = _float(row.get("yardline_100"))
        ydstogo = _float(row.get("ydstogo"))

        if is_target:
            team_bucket["team_targets"] += 1
            player_id = str(row.get("receiver_player_id") or "").strip()
            if player_id in players_by_id:
                bucket = _player_bucket(player_week, player_id, season, week, team)
                bucket["targets"] += 1
                if yardline <= 20:
                    bucket["red_zone_targets"] += 1
                if yardline <= 5:
                    bucket["goal_line_targets"] += 1
        if is_rush:
            team_bucket["team_rushing_attempts"] += 1
            player_id = str(row.get("rusher_player_id") or "").strip()
            if player_id in players_by_id:
                bucket = _player_bucket(player_week, player_id, season, week, team)
                bucket["rushing_attempts"] += 1
                if yardline <= 20:
                    bucket["red_zone_carries"] += 1
                if yardline <= 5:
                    bucket["goal_line_carries"] += 1
                if ydstogo <= 2:
                    bucket["short_yardage_carries"] += 1

    source_date = _latest_source_date(source_paths or [])
    rows: list[dict[str, object]] = []
    for (player_id, season, week, team), stats in sorted(
        player_week.items(),
        key=lambda item: (item[0][1], item[0][2], item[0][3], item[0][0]),
    ):
        player = players_by_id[player_id]
        team_stats = team_week.get((season, week, team), {})
        team_targets = team_stats.get("team_targets", 0.0)
        team_rushes = team_stats.get("team_rushing_attempts", 0.0)
        targets = stats["targets"]
        carries = stats["rushing_attempts"]
        weighted_opps = carries + (1.15 * targets)
        rows.append(
            {
                "truth_set_player_name": player.truth_set_player_name,
                "matched_player_name": player.matched_player_name,
                "player_id": player.player_id,
                "season": season,
                "week": week,
                "team": team,
                "position": player.position,
                "targets": _clean_number(targets),
                "team_targets": _clean_number(team_targets),
                "target_share": _ratio(targets, team_targets),
                "rb_target_share": _ratio(targets, team_targets)
                if player.position == "RB"
                else "",
                "rushing_attempts": _clean_number(carries),
                "team_rushing_attempts": _clean_number(team_rushes),
                "rb_carry_share": _ratio(carries, team_rushes)
                if player.position == "RB"
                else "",
                "weighted_opportunities": _clean_number(weighted_opps),
                "red_zone_carries": _clean_number(stats["red_zone_carries"]),
                "red_zone_targets": _clean_number(stats["red_zone_targets"]),
                "goal_line_carries": _clean_number(stats["goal_line_carries"]),
                "goal_line_targets": _clean_number(stats["goal_line_targets"]),
                "short_yardage_carries": _clean_number(stats["short_yardage_carries"]),
                "source_status": "derived_real_data",
                "source_name": "nflverse_play_by_play",
                "source_url": PBP_URL_PATTERN.format(season=season),
                "source_date": source_date,
                "notes": "routes_run|route_participation|tprr|yprr_not_estimated",
            }
        )
    return rows


def aggregate_usage_season_rows(
    week_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[tuple[str, int], list[dict[str, object]]] = {}
    for row in week_rows:
        grouped.setdefault(
            (str(row["truth_set_player_name"]), int(row["season"])),
            [],
        ).append(row)

    rows: list[dict[str, object]] = []
    count_fields = (
        "targets",
        "team_targets",
        "rushing_attempts",
        "team_rushing_attempts",
        "weighted_opportunities",
        "red_zone_carries",
        "red_zone_targets",
        "goal_line_carries",
        "goal_line_targets",
        "short_yardage_carries",
    )
    for (_, season), group in sorted(grouped.items(), key=lambda item: item[0]):
        latest = sorted(group, key=lambda row: int(row["week"]))[-1]
        totals = {field: sum(_float(row.get(field)) for row in group) for field in count_fields}
        rows.append(
            {
                "truth_set_player_name": latest["truth_set_player_name"],
                "matched_player_name": latest["matched_player_name"],
                "player_id": latest["player_id"],
                "season": season,
                "games_with_usage": len({int(row["week"]) for row in group}),
                "team": latest["team"],
                "position": latest["position"],
                "targets": _clean_number(totals["targets"]),
                "team_targets": _clean_number(totals["team_targets"]),
                "target_share": _ratio(totals["targets"], totals["team_targets"]),
                "rb_target_share": _ratio(totals["targets"], totals["team_targets"])
                if latest["position"] == "RB"
                else "",
                "rushing_attempts": _clean_number(totals["rushing_attempts"]),
                "team_rushing_attempts": _clean_number(totals["team_rushing_attempts"]),
                "rb_carry_share": _ratio(
                    totals["rushing_attempts"],
                    totals["team_rushing_attempts"],
                )
                if latest["position"] == "RB"
                else "",
                "weighted_opportunities": _clean_number(totals["weighted_opportunities"]),
                "red_zone_carries": _clean_number(totals["red_zone_carries"]),
                "red_zone_targets": _clean_number(totals["red_zone_targets"]),
                "goal_line_carries": _clean_number(totals["goal_line_carries"]),
                "goal_line_targets": _clean_number(totals["goal_line_targets"]),
                "short_yardage_carries": _clean_number(totals["short_yardage_carries"]),
                "source_status": "derived_real_data",
                "source_name": "nflverse_play_by_play",
                "source_url": PBP_URL_PATTERN.format(season=season),
                "source_date": latest["source_date"],
                "notes": "aggregated_from_player_week_usage;routes_not_estimated",
            }
        )
    return rows


def write_truth_set_v3_usage_outputs(
    output_root: str | Path,
    result: TruthSetV3UsageResult,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "week": root / "truth_set_v3_usage_player_week.csv",
        "season": root / "truth_set_v3_usage_player_season.csv",
        "missing": root / "truth_set_v3_usage_missing_players.csv",
        "summary_csv": root / "truth_set_v3_usage_summary.csv",
        "summary_json": root / "truth_set_v3_usage_summary.json",
    }
    _write_csv(paths["week"], V3_USAGE_WEEK_HEADER, result.week_rows)
    _write_csv(paths["season"], V3_USAGE_SEASON_HEADER, result.season_rows)
    _write_csv(paths["missing"], V3_USAGE_MISSING_HEADER, result.missing_rows)
    _write_csv(
        paths["summary_csv"],
        V3_USAGE_SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    paths["summary_json"].write_text(
        json.dumps(result.summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def _players_from_production_rows(
    production_week_rows: tuple[dict[str, object], ...],
) -> list[UsagePlayer]:
    players: dict[str, UsagePlayer] = {}
    for row in production_week_rows:
        player_id = str(row.get("player_id") or "").strip()
        if not player_id:
            continue
        players[player_id] = UsagePlayer(
            truth_set_player_name=str(row.get("truth_set_player_name") or ""),
            matched_player_name=str(row.get("matched_player_name") or ""),
            player_id=player_id,
            position=str(row.get("position") or ""),
            nfl_team=str(row.get("team") or ""),
        )
    return list(players.values())


def _player_weeks_from_production_rows(
    production_week_rows: tuple[dict[str, object], ...],
) -> list[UsagePlayerWeek]:
    weeks: dict[tuple[str, int, int, str], UsagePlayerWeek] = {}
    for row in production_week_rows:
        player_id = str(row.get("player_id") or "").strip()
        season = _int(row.get("season"))
        week = _int(row.get("week"))
        team = str(row.get("team") or "").strip()
        if not player_id or not season or not week or not team:
            continue
        weeks[(player_id, season, week, team)] = UsagePlayerWeek(
            player_id=player_id,
            season=season,
            week=week,
            team=team,
        )
    return list(weeks.values())


def _truth_players(path: str | Path) -> list[dict[str, str]]:
    _, rows = _read_csv(Path(path))
    return rows


def _missing_rows(
    truth_players: list[dict[str, str]],
    players: list[UsagePlayer],
) -> list[dict[str, object]]:
    matched = {_name_key(player.truth_set_player_name) for player in players}
    rows: list[dict[str, object]] = []
    for player in truth_players:
        name = str(player.get("player_name") or "").strip()
        if not name or _name_key(name) in matched:
            continue
        rows.append(
            {
                "truth_set_player_name": name,
                "position": str(player.get("position") or ""),
                "nfl_team": str(player.get("nfl_team") or ""),
                "match_status": "missing_play_by_play_usage",
                "source_status": "missing",
                "reason": (
                    "No matched nflverse production/player_id exists for this player, "
                    "so play-by-play usage could not be derived."
                ),
                "notes": "no_fake_usage_rows_created",
            }
        )
    return rows


def _summary(
    *,
    truth_players: list[dict[str, str]],
    players: list[UsagePlayer],
    pbp_rows: list[dict[str, object]],
    week_rows: list[dict[str, object]],
    season_rows: list[dict[str, object]],
    missing_rows: list[dict[str, object]],
    requested_seasons: set[int],
    source_paths: list[Path],
) -> dict[str, object]:
    return {
        "status": "ready" if source_paths else "blocked",
        "review_status": "review_only",
        "truth_set_players": len(truth_players),
        "matched_players_with_player_ids": len(players),
        "missing_players": len(missing_rows),
        "pbp_rows_seen": len(pbp_rows),
        "week_rows": len(week_rows),
        "season_rows": len(season_rows),
        "requested_seasons": "|".join(str(season) for season in sorted(requested_seasons)),
        "source_status": "derived_real_data",
        "routes_run_estimated": False,
        "route_participation_estimated": False,
        "tprr_estimated": False,
        "yprr_estimated": False,
        "source_files": "|".join(str(path) for path in source_paths),
        "active_rankings_overwritten": False,
        "model_scores_changed": False,
    }


def _read_pbp_rows(path: Path) -> list[dict[str, object]]:
    data = pd.read_csv(
        path,
        compression="gzip",
        usecols=lambda column: column in PBP_USE_COLUMNS,
        low_memory=False,
    )
    for column in PBP_USE_COLUMNS:
        if column not in data.columns:
            data[column] = ""
    return data.to_dict(orient="records")


def _download_pbp(path: Path, *, season: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    url = PBP_URL_PATTERN.format(season=season)
    request = Request(url, headers={"User-Agent": "niners-war-room-local-import"})
    with urlopen(request, timeout=120) as response:  # nosec B310 - explicit nflverse URL.
        path.write_bytes(response.read())


def _player_bucket(
    buckets: dict[tuple[str, int, int, str], dict[str, float]],
    player_id: str,
    season: int,
    week: int,
    team: str,
) -> dict[str, float]:
    return buckets.setdefault(
        (player_id, season, week, team),
        {
            "targets": 0.0,
            "rushing_attempts": 0.0,
            "red_zone_carries": 0.0,
            "red_zone_targets": 0.0,
            "goal_line_carries": 0.0,
            "goal_line_targets": 0.0,
            "short_yardage_carries": 0.0,
        },
    )


def _latest_source_date(paths: list[Path]) -> str:
    if not paths:
        return ""
    latest = max(path.stat().st_mtime for path in paths if path.exists())
    return datetime.fromtimestamp(latest).date().isoformat()


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


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


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
        text = str(value or "0")
        if text.lower() == "nan":
            return 0.0
        return float(text)
    except ValueError:
        return 0.0


def _name_key(value: str) -> str:
    normalized = value.lower()
    normalized = re.sub(r"['’`.\-]", "", normalized)
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()
