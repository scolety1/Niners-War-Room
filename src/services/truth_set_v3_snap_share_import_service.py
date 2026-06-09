from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

from src.services.nflverse_player_stats_import_service import (
    OFFICIAL_SNAP_COUNTS_URL_PATTERN,
)
from src.services.truth_set_v3_production_import_service import (
    DEFAULT_TRUTH_SET_SOURCE,
)
from src.services.truth_set_v3_usage_derivation_service import DEFAULT_REPORT_ROOT

DEFAULT_DOWNLOAD_ROOT = Path("local_exports/truth_set_lab/v3/downloads")
DEFAULT_PRODUCTION_WEEK_SOURCE = DEFAULT_REPORT_ROOT / "truth_set_v3_production_player_week.csv"
DEFAULT_IDENTITY_MAP_SOURCE = Path(
    "local_exports/nflverse/preview/sprint2_phase7_public_20260514/raw/nflverse_identity_map.csv"
)
EXISTING_SNAP_SEARCH_ROOT = Path("local_exports/nflverse/preview")

V3_SNAP_WEEK_HEADER = (
    "truth_set_player_name",
    "matched_player_name",
    "match_status",
    "match_method",
    "identity_warning",
    "player_id",
    "gsis_id",
    "sleeper_id",
    "pfr_player_id",
    "season",
    "week",
    "game_id",
    "team",
    "position",
    "offense_snaps",
    "offense_pct",
    "snap_share",
    "game_with_offensive_snaps",
    "source_status",
    "source_name",
    "source_url",
    "source_date",
    "notes",
)

V3_SNAP_SEASON_HEADER = (
    "truth_set_player_name",
    "matched_player_name",
    "match_status",
    "match_method",
    "identity_warning",
    "player_id",
    "gsis_id",
    "sleeper_id",
    "pfr_player_id",
    "season",
    "games",
    "games_with_offensive_snaps",
    "team",
    "position",
    "offense_snaps",
    "avg_offense_pct",
    "avg_snap_share",
    "source_status",
    "source_name",
    "source_url",
    "source_date",
    "notes",
)

V3_SNAP_MISSING_HEADER = (
    "truth_set_player_name",
    "position",
    "nfl_team",
    "match_status",
    "source_status",
    "reason",
    "notes",
)

V3_SNAP_SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class SnapPlayer:
    truth_set_player_name: str
    matched_player_name: str
    player_id: str
    position: str
    nfl_team: str


@dataclass(frozen=True)
class TruthSetV3SnapResult:
    week_rows: tuple[dict[str, object], ...]
    season_rows: tuple[dict[str, object], ...]
    missing_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def build_truth_set_v3_snap_share_preview(
    *,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET_SOURCE,
    production_week_path: str | Path = DEFAULT_PRODUCTION_WEEK_SOURCE,
    snap_download_root: str | Path = DEFAULT_DOWNLOAD_ROOT,
    identity_map_path: str | Path | None = DEFAULT_IDENTITY_MAP_SOURCE,
    seasons: set[int] | None = None,
    download_if_missing: bool = True,
) -> TruthSetV3SnapResult:
    truth_players = _truth_players(truth_set_path)
    _, production_rows = _read_csv(Path(production_week_path))
    players = _players_from_production_rows(production_rows)
    requested_seasons = seasons or _seasons_from_production_rows(production_rows)
    identity_rows = _identity_rows(identity_map_path)

    snap_rows: list[dict[str, str]] = []
    source_paths: list[Path] = []
    for season in sorted(requested_seasons):
        path = _snap_source_path(
            Path(snap_download_root),
            season=season,
            download_if_missing=download_if_missing,
        )
        if not path:
            continue
        source_paths.append(path)
        _, rows = _read_csv(path)
        snap_rows.extend(rows)

    week_rows = build_snap_week_rows_from_source_rows(
        snap_rows,
        players=players,
        identity_rows=identity_rows,
        seasons=requested_seasons,
        source_paths=source_paths,
    )
    season_rows = aggregate_snap_season_rows(week_rows)
    missing_rows = _missing_rows(truth_players, week_rows, players)
    summary = _summary(
        truth_players=truth_players,
        players=players,
        snap_rows=snap_rows,
        week_rows=week_rows,
        season_rows=season_rows,
        missing_rows=missing_rows,
        requested_seasons=requested_seasons,
        source_paths=source_paths,
    )
    return TruthSetV3SnapResult(
        week_rows=tuple(week_rows),
        season_rows=tuple(season_rows),
        missing_rows=tuple(missing_rows),
        summary=summary,
    )


def build_snap_week_rows_from_source_rows(
    source_rows: list[dict[str, str]],
    *,
    players: list[SnapPlayer],
    identity_rows: list[dict[str, str]] | None = None,
    seasons: set[int] | None = None,
    source_paths: list[Path] | None = None,
) -> list[dict[str, object]]:
    season_filter = {str(season) for season in seasons} if seasons else None
    identity_by_pfr = {
        str(row.get("pfr_id") or "").strip(): row
        for row in identity_rows or []
        if str(row.get("pfr_id") or "").strip()
    }
    resolver = _SnapPlayerResolver(players)
    source_date = _latest_source_date(source_paths or [])
    output: list[dict[str, object]] = []

    for row in source_rows:
        season = str(row.get("season") or "").strip()
        if season_filter and season not in season_filter:
            continue
        if str(row.get("game_type") or "").strip() not in {"", "REG"}:
            continue
        position = str(row.get("position") or "").strip().upper()
        if position not in {"QB", "RB", "WR", "TE"}:
            continue

        player, match_method = resolver.resolve(row)
        if not player:
            continue
        pfr_id = str(row.get("pfr_player_id") or "").strip()
        identity = identity_by_pfr.get(pfr_id, {})
        identity_warning = _identity_warning(row, identity)
        offense_pct = _percent_to_float(row.get("offense_pct"))
        offense_snaps = _int(row.get("offense_snaps"))
        output.append(
            {
                "truth_set_player_name": player.truth_set_player_name,
                "matched_player_name": str(row.get("player") or player.matched_player_name),
                "match_status": "matched",
                "match_method": match_method,
                "identity_warning": identity_warning,
                "player_id": player.player_id,
                "gsis_id": str(identity.get("gsis_id") or ""),
                "sleeper_id": str(identity.get("sleeper_id") or ""),
                "pfr_player_id": pfr_id,
                "season": _int(season),
                "week": _int(row.get("week")),
                "game_id": str(row.get("game_id") or ""),
                "team": str(row.get("team") or ""),
                "position": player.position or position,
                "offense_snaps": offense_snaps,
                "offense_pct": offense_pct,
                "snap_share": offense_pct,
                "game_with_offensive_snaps": int(offense_snaps > 0),
                "source_status": "imported_real_data",
                "source_name": "nflverse_snap_counts",
                "source_url": OFFICIAL_SNAP_COUNTS_URL_PATTERN.format(season=_int(season)),
                "source_date": source_date,
                "notes": "snap_share_only_not_route_participation",
            }
        )

    return sorted(
        output,
        key=lambda item: (
            int(item["season"]),
            int(item["week"]),
            str(item["team"]),
            str(item["truth_set_player_name"]),
        ),
    )


def aggregate_snap_season_rows(
    week_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    buckets: dict[tuple[str, int], dict[str, object]] = {}
    for row in week_rows:
        key = (str(row["player_id"]), int(row["season"]))
        bucket = buckets.setdefault(
            key,
            {
                "truth_set_player_name": row["truth_set_player_name"],
                "matched_player_name": row["matched_player_name"],
                "match_status": row["match_status"],
                "match_method": row["match_method"],
                "identity_warning": row["identity_warning"],
                "player_id": row["player_id"],
                "gsis_id": row["gsis_id"],
                "sleeper_id": row["sleeper_id"],
                "pfr_player_id": row["pfr_player_id"],
                "season": row["season"],
                "games": 0,
                "games_with_offensive_snaps": 0,
                "teams": {},
                "position": row["position"],
                "offense_snaps": 0,
                "offense_pct_total": 0.0,
                "source_status": "imported_real_data",
                "source_name": "nflverse_snap_counts",
                "source_url": row["source_url"],
                "source_date": row["source_date"],
                "notes": "season_average_snap_share_only_not_route_participation",
            },
        )
        bucket["games"] = int(bucket["games"]) + 1
        bucket["games_with_offensive_snaps"] = int(bucket["games_with_offensive_snaps"]) + int(
            row["game_with_offensive_snaps"]
        )
        bucket["offense_snaps"] = int(bucket["offense_snaps"]) + int(row["offense_snaps"])
        bucket["offense_pct_total"] = float(bucket["offense_pct_total"]) + float(
            row["offense_pct"]
        )
        teams = bucket["teams"]
        assert isinstance(teams, dict)
        teams[str(row["team"])] = teams.get(str(row["team"]), 0) + 1

    rows: list[dict[str, object]] = []
    for bucket in buckets.values():
        games = int(bucket["games"])
        avg_share = round(float(bucket.pop("offense_pct_total")) / games, 4) if games else 0.0
        teams = bucket.pop("teams")
        assert isinstance(teams, dict)
        bucket["team"] = max(teams.items(), key=lambda item: item[1])[0] if teams else ""
        bucket["avg_offense_pct"] = avg_share
        bucket["avg_snap_share"] = avg_share
        rows.append(bucket)

    return sorted(
        rows,
        key=lambda item: (int(item["season"]), str(item["truth_set_player_name"])),
    )


def write_truth_set_v3_snap_outputs(
    output_root: str | Path,
    result: TruthSetV3SnapResult,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "week": root / "truth_set_v3_snap_share_player_week.csv",
        "season": root / "truth_set_v3_snap_share_player_season.csv",
        "missing": root / "truth_set_v3_snap_share_missing_players.csv",
        "summary_csv": root / "truth_set_v3_snap_share_summary.csv",
        "summary_json": root / "truth_set_v3_snap_share_summary.json",
    }
    _write_csv(paths["week"], V3_SNAP_WEEK_HEADER, result.week_rows)
    _write_csv(paths["season"], V3_SNAP_SEASON_HEADER, result.season_rows)
    _write_csv(paths["missing"], V3_SNAP_MISSING_HEADER, result.missing_rows)
    _write_csv(
        paths["summary_csv"],
        V3_SNAP_SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    paths["summary_json"].write_text(
        json.dumps(result.summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


class _SnapPlayerResolver:
    def __init__(self, players: list[SnapPlayer]) -> None:
        self.by_name_position: dict[tuple[str, str], list[SnapPlayer]] = {}
        self.by_name_position_team: dict[tuple[str, str, str], list[SnapPlayer]] = {}
        for player in players:
            for name in {player.truth_set_player_name, player.matched_player_name}:
                name_key = _name_key(name)
                if not name_key:
                    continue
                name_position = (name_key, player.position)
                self.by_name_position.setdefault(name_position, []).append(player)
                team_key = (name_key, player.position, _team_key(player.nfl_team))
                self.by_name_position_team.setdefault(team_key, []).append(player)

    def resolve(self, source_row: dict[str, str]) -> tuple[SnapPlayer | None, str]:
        name_key = _name_key(str(source_row.get("player") or ""))
        position = str(source_row.get("position") or "").strip().upper()
        team = _team_key(str(source_row.get("team") or ""))
        exact = _unique(self.by_name_position_team.get((name_key, position, team), []))
        if exact:
            return exact, "name_position_team_match"
        name_position = _unique(self.by_name_position.get((name_key, position), []))
        if name_position:
            return name_position, "name_position_match"
        return None, "unmatched"


def _players_from_production_rows(rows: list[dict[str, str]]) -> list[SnapPlayer]:
    players: dict[str, SnapPlayer] = {}
    for row in rows:
        player_id = str(row.get("player_id") or "").strip()
        if not player_id:
            continue
        players[player_id] = SnapPlayer(
            truth_set_player_name=str(row.get("truth_set_player_name") or ""),
            matched_player_name=str(row.get("matched_player_name") or ""),
            player_id=player_id,
            position=str(row.get("position") or ""),
            nfl_team=str(row.get("team") or ""),
        )
    return list(players.values())


def _seasons_from_production_rows(rows: list[dict[str, str]]) -> set[int]:
    return {
        _int(row.get("season"))
        for row in rows
        if _int(row.get("season"))
    }


def _truth_players(path: str | Path) -> list[dict[str, str]]:
    _, rows = _read_csv(Path(path))
    return rows


def _identity_rows(path: str | Path | None) -> list[dict[str, str]]:
    if not path:
        return []
    source = Path(path)
    if not source.exists():
        return []
    _, rows = _read_csv(source)
    return rows


def _missing_rows(
    truth_players: list[dict[str, str]],
    week_rows: list[dict[str, object]],
    players: list[SnapPlayer],
) -> list[dict[str, object]]:
    players_with_snap = {_name_key(str(row["truth_set_player_name"])) for row in week_rows}
    players_with_ids = {_name_key(player.truth_set_player_name) for player in players}
    output: list[dict[str, object]] = []
    for player in truth_players:
        name = str(player.get("player_name") or "").strip()
        key = _name_key(name)
        if not name or key in players_with_snap:
            continue
        if key in players_with_ids:
            reason = "Matched nflverse player ID, but no official snap-count rows were found."
            status = "missing_snap_counts"
        else:
            reason = "No matched nflverse production/player_id exists for this player."
            status = "missing_player_id"
        output.append(
            {
                "truth_set_player_name": name,
                "position": str(player.get("position") or ""),
                "nfl_team": str(player.get("nfl_team") or ""),
                "match_status": status,
                "source_status": "missing",
                "reason": reason,
                "notes": "no_fake_snap_share_rows_created",
            }
        )
    return output


def _summary(
    *,
    truth_players: list[dict[str, str]],
    players: list[SnapPlayer],
    snap_rows: list[dict[str, str]],
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
        "snap_rows_seen": len(snap_rows),
        "week_rows": len(week_rows),
        "season_rows": len(season_rows),
        "requested_seasons": "|".join(str(season) for season in sorted(requested_seasons)),
        "source_status": "imported_real_data",
        "snap_share_label": "snap_share_only",
        "route_participation_estimated": False,
        "tprr_estimated": False,
        "yprr_estimated": False,
        "identity_warning_rows": sum(1 for row in week_rows if row["identity_warning"]),
        "source_files": "|".join(str(path) for path in source_paths),
        "active_rankings_overwritten": False,
        "model_scores_changed": False,
    }


def _snap_source_path(
    download_root: Path,
    *,
    season: int,
    download_if_missing: bool,
) -> Path | None:
    target = download_root / f"snap_counts_{season}.csv"
    if target.exists():
        return target
    existing = _existing_snap_path(season)
    if existing:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(existing, target)
        return target
    if download_if_missing:
        _download_snap_counts(target, season=season)
        return target if target.exists() else None
    return None


def _existing_snap_path(season: int) -> Path | None:
    candidates = sorted(
        EXISTING_SNAP_SEARCH_ROOT.glob(f"*/downloads/snap_counts_{season}.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _download_snap_counts(path: Path, *, season: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    url = OFFICIAL_SNAP_COUNTS_URL_PATTERN.format(season=season)
    request = Request(url, headers={"User-Agent": "niners-war-room-local-import"})
    with urlopen(request, timeout=120) as response:  # nosec B310 - explicit nflverse URL.
        path.write_bytes(response.read())


def _latest_source_date(paths: list[Path]) -> str:
    if not paths:
        return ""
    latest = max(path.stat().st_mtime for path in paths if path.exists())
    return datetime.fromtimestamp(latest).date().isoformat()


def _identity_warning(row: dict[str, str], identity: dict[str, str]) -> str:
    if not str(row.get("pfr_player_id") or "").strip():
        return "missing_pfr_player_id"
    if not identity:
        return "pfr_id_not_in_identity_map"
    if str(identity.get("review_status") or "") not in {"", "ready"}:
        return "identity_map_not_ready"
    return ""


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


def _unique(players: list[SnapPlayer]) -> SnapPlayer | None:
    unique = {player.player_id: player for player in players if player.player_id}
    if len(unique) == 1:
        return next(iter(unique.values()))
    return None


def _percent_to_float(value: object) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        if text.endswith("%"):
            return round(float(text[:-1]) / 100, 4)
        number = float(text)
        if number > 1:
            return round(number / 100, 4)
        return round(number, 4)
    except ValueError:
        return 0.0


def _int(value: object) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def _name_key(value: str) -> str:
    normalized = value.lower()
    normalized = re.sub(r"['â€™`.\-]", "", normalized)
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _team_key(value: str) -> str:
    team = str(value or "").strip().upper()
    aliases = {
        "LA": "LAR",
        "JAC": "JAX",
        "ARZ": "ARI",
    }
    return aliases.get(team, team)
