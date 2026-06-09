from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from src.services.real_input_template_service import NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS

OFFICIAL_PLAYER_STATS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats.csv"
)
OFFICIAL_PLAYER_STATS_DOC_URL = "https://nflreadr.nflverse.com/reference/load_player_stats.html"
OFFICIAL_NFLVERSE_SCHEDULE_DOC_URL = (
    "https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html"
)
OFFICIAL_SNAP_COUNTS_URL_PATTERN = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "snap_counts/snap_counts_{season}.csv"
)
OFFICIAL_DEPTH_CHARTS_URL_PATTERN = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "depth_charts/depth_charts_{season}.csv"
)
LOCAL_PLAYER_STATS_FILE_NAME = "nflverse_player_stats_weekly.csv"
LOCAL_SNAP_COUNTS_FILE_NAME = "nflverse_snap_counts_weekly.csv"
LOCAL_DEPTH_CHARTS_FILE_NAME = "nflverse_depth_chart_weekly.csv"

SUPPORTED_MODEL_POSITIONS = ("QB", "RB", "WR", "TE")
LOCAL_PLAYER_STATS_HEADER = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
    LOCAL_PLAYER_STATS_FILE_NAME
]
LOCAL_SNAP_COUNTS_HEADER = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
    LOCAL_SNAP_COUNTS_FILE_NAME
]
LOCAL_DEPTH_CHARTS_HEADER = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
    LOCAL_DEPTH_CHARTS_FILE_NAME
]


@dataclass(frozen=True)
class NflversePlayerStatsTransformReport:
    status: str
    rows_seen: int
    rows_transformed: int
    rows_skipped: int
    output_path: Path | None
    warnings: tuple[str, ...]


def official_player_stats_source_rows() -> list[dict[str, object]]:
    return [
        {
            "source_name": "nflverse player stats",
            "source_url": OFFICIAL_PLAYER_STATS_URL,
            "documentation_url": OFFICIAL_PLAYER_STATS_DOC_URL,
            "access_method": "direct CSV release",
            "local_target": LOCAL_PLAYER_STATS_FILE_NAME,
            "scoring_effect": (
                "none until transformed, normalized, reviewed, and explicitly applied"
            ),
            "scraping_required": "false",
            "positions": "QB|RB|WR|TE",
            "key_fields": (
                "player_id|season|week|position|passing_yards|passing_tds|"
                "interceptions|carries|rushing_yards|rushing_tds|"
                "rushing_first_downs|targets|receptions|receiving_yards|"
                "receiving_tds|receiving_first_downs|target_share|"
                "air_yards_share|wopr|passing_epa|rushing_epa|receiving_epa"
            ),
            "identity_note": (
                "Use nflverse player_id first; bridge to Sleeper with ID map review."
            ),
            "limitations": (
                "This is historical weekly player-stat evidence. It does not solve "
                "current injuries, projections, route participation, or Sleeper identity "
                "matching by itself."
            ),
            "confidence": 95,
        },
        {
            "source_name": "nflverse snap counts",
            "source_url": OFFICIAL_SNAP_COUNTS_URL_PATTERN,
            "documentation_url": OFFICIAL_NFLVERSE_SCHEDULE_DOC_URL,
            "access_method": "direct season CSV release",
            "local_target": "nflverse_snap_counts_weekly.csv",
            "scoring_effect": (
                "none until PFR identity is bridged, then role features are reviewed"
            ),
            "scraping_required": "false",
            "positions": "QB|RB|WR|TE",
            "key_fields": (
                "game_id|season|game_type|week|player|pfr_player_id|position|"
                "team|opponent|offense_snaps|offense_pct|st_snaps|st_pct"
            ),
            "identity_note": (
                "Requires reviewed pfr_player_id to local/Sleeper/nflverse ID mapping."
            ),
            "limitations": (
                "Useful for role security and starter-week evidence, but should not be "
                "joined to players by name alone."
            ),
            "confidence": 88,
        },
        {
            "source_name": "nflverse depth charts",
            "source_url": OFFICIAL_DEPTH_CHARTS_URL_PATTERN,
            "documentation_url": OFFICIAL_NFLVERSE_SCHEDULE_DOC_URL,
            "access_method": "direct season CSV release",
            "local_target": "nflverse_depth_chart_weekly.csv",
            "scoring_effect": "none until transformed into reviewed role context",
            "scraping_required": "false",
            "positions": "QB|RB|WR|TE",
            "key_fields": (
                "dt|team|player_name|espn_id|gsis_id|pos_grp|pos_name|"
                "pos_abb|pos_slot|pos_rank"
            ),
            "identity_note": "GSIS and ESPN IDs are available; still review ambiguous rows.",
            "limitations": (
                "Depth chart data is roster-role context, not weekly route/touch evidence. "
                "It should remain below production, opportunity, and snap/usage inputs."
            ),
            "confidence": 78,
        },
    ]


def transform_official_player_stats_rows(
    source_rows: list[dict[str, str]],
    *,
    seasons: set[int] | None = None,
    season_type: str | None = "REG",
    positions: tuple[str, ...] = SUPPORTED_MODEL_POSITIONS,
) -> list[dict[str, str]]:
    season_filter = {str(season) for season in seasons} if seasons else None
    position_filter = {position.upper() for position in positions}
    transformed: list[dict[str, str]] = []

    for row in source_rows:
        if season_filter and str(row.get("season", "")).strip() not in season_filter:
            continue
        if season_type and row.get("season_type", "").strip() != season_type:
            continue

        position = row.get("position", "").strip().upper()
        if position not in position_filter:
            continue

        local_row = {column: "" for column in LOCAL_PLAYER_STATS_HEADER}
        local_row.update(
            {
                "season": _value(row, "season"),
                "week": _value(row, "week"),
                "player_id": _value(row, "player_id"),
                "gsis_id": _value(row, "player_id"),
                "sleeper_id": "",
                "player_name": _value(row, "player_display_name", "player_name"),
                "position": position,
                "team": _value(row, "recent_team"),
                "passing_yards": _value(row, "passing_yards"),
                "passing_tds": _value(row, "passing_tds"),
                "interceptions": _value(row, "interceptions"),
                "rushing_attempts": _value(row, "carries"),
                "rushing_yards": _value(row, "rushing_yards"),
                "rushing_tds": _value(row, "rushing_tds"),
                "rushing_first_downs": _value(row, "rushing_first_downs"),
                "targets": _value(row, "targets"),
                "receptions": _value(row, "receptions"),
                "receiving_yards": _value(row, "receiving_yards"),
                "receiving_tds": _value(row, "receiving_tds"),
                "receiving_first_downs": _value(row, "receiving_first_downs"),
                "passing_first_downs": _value(row, "passing_first_downs"),
                "passing_epa": _value(row, "passing_epa"),
                "rushing_epa": _value(row, "rushing_epa"),
                "receiving_epa": _value(row, "receiving_epa"),
                "receiving_air_yards": _value(row, "receiving_air_yards"),
                "target_share": _value(row, "target_share"),
                "air_yards_share": _value(row, "air_yards_share"),
                "wopr": _value(row, "wopr"),
                "return_yards": _value(row, "return_yards"),
                "return_tds": _value(row, "return_tds"),
                "kick_return_yards": _value(row, "kick_return_yards"),
                "kick_return_tds": _value(row, "kick_return_tds"),
                "punt_return_yards": _value(row, "punt_return_yards"),
                "punt_return_tds": _value(row, "punt_return_tds"),
                "fumbles_lost": _sum_numeric(
                    row,
                    "sack_fumbles_lost",
                    "rushing_fumbles_lost",
                    "receiving_fumbles_lost",
                ),
            }
        )
        transformed.append(local_row)

    return transformed


def transform_official_player_stats_csv(
    input_path: str | Path,
    output_path: str | Path,
    *,
    seasons: set[int] | None = None,
    season_type: str | None = "REG",
) -> NflversePlayerStatsTransformReport:
    source_rows = _read_csv(Path(input_path))
    transformed = transform_official_player_stats_rows(
        source_rows,
        seasons=seasons,
        season_type=season_type,
    )
    output = Path(output_path)
    write_local_player_stats_csv(output, transformed)
    skipped = len(source_rows) - len(transformed)
    return NflversePlayerStatsTransformReport(
        status="ready",
        rows_seen=len(source_rows),
        rows_transformed=len(transformed),
        rows_skipped=skipped,
        output_path=output,
        warnings=(),
    )


def transform_official_snap_counts_rows(
    source_rows: list[dict[str, str]],
    *,
    seasons: set[int] | None = None,
    season_type: str | None = "REG",
    positions: tuple[str, ...] = SUPPORTED_MODEL_POSITIONS,
    identity_rows: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    season_filter = {str(season) for season in seasons} if seasons else None
    position_filter = {position.upper() for position in positions}
    pfr_identity = _rows_by_key(identity_rows or [], "pfr_id")
    transformed: list[dict[str, str]] = []

    for row in source_rows:
        if season_filter and str(row.get("season", "")).strip() not in season_filter:
            continue
        if season_type and row.get("game_type", "").strip() != season_type:
            continue

        position = row.get("position", "").strip().upper()
        if position not in position_filter:
            continue

        identity = pfr_identity.get(_value(row, "pfr_player_id"), {})
        local_row = {column: "" for column in LOCAL_SNAP_COUNTS_HEADER}
        local_row.update(
            {
                "season": _value(row, "season"),
                "week": _value(row, "week"),
                "game_id": _value(row, "game_id"),
                "gsis_id": _value(identity, "gsis_id"),
                "sleeper_id": _value(identity, "sleeper_id"),
                "player_name": _value(row, "player"),
                "position": position,
                "team": _value(row, "team"),
                "opponent": _value(row, "opponent"),
                "offense_snaps": _value(row, "offense_snaps"),
                "offense_pct": _percent_to_number(_value(row, "offense_pct")),
                "st_snaps": _value(row, "st_snaps"),
                "st_pct": _percent_to_number(_value(row, "st_pct")),
            }
        )
        transformed.append(local_row)

    return transformed


def transform_official_snap_counts_csv(
    input_path: str | Path,
    output_path: str | Path,
    *,
    seasons: set[int] | None = None,
    season_type: str | None = "REG",
    identity_map_path: str | Path | None = None,
) -> NflversePlayerStatsTransformReport:
    source_rows = _read_csv(Path(input_path))
    identity_rows = _read_csv(Path(identity_map_path)) if identity_map_path else None
    transformed = transform_official_snap_counts_rows(
        source_rows,
        seasons=seasons,
        season_type=season_type,
        identity_rows=identity_rows,
    )
    output = Path(output_path)
    _write_csv(output, LOCAL_SNAP_COUNTS_HEADER, transformed)
    skipped = len(source_rows) - len(transformed)
    warnings = ()
    if identity_map_path is None:
        warnings = (
            "Snap counts transformed without identity map; GSIS/Sleeper IDs are blank.",
        )
    return NflversePlayerStatsTransformReport(
        status="ready",
        rows_seen=len(source_rows),
        rows_transformed=len(transformed),
        rows_skipped=skipped,
        output_path=output,
        warnings=warnings,
    )


def transform_official_depth_chart_rows(
    source_rows: list[dict[str, str]],
    *,
    season: int,
    default_week: int = 0,
    positions: tuple[str, ...] = SUPPORTED_MODEL_POSITIONS,
    identity_rows: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    position_filter = {position.upper() for position in positions}
    gsis_identity = _rows_by_key(identity_rows or [], "gsis_id")
    espn_identity = _rows_by_key(identity_rows or [], "espn_id")
    transformed: list[dict[str, str]] = []

    for row in source_rows:
        if _value(row, "game_type") and _value(row, "game_type") != "REG":
            continue

        position = _value(row, "pos_abb", "position").upper()
        if position not in position_filter:
            continue

        identity = (
            gsis_identity.get(_value(row, "gsis_id"))
            or espn_identity.get(_value(row, "espn_id"))
            or {}
        )
        pos_rank = _value(row, "pos_rank", "depth_team")
        local_row = {column: "" for column in LOCAL_DEPTH_CHARTS_HEADER}
        local_row.update(
            {
                "season": str(season),
                "week": _value(row, "week") or str(default_week),
                "team": _value(row, "team", "club_code"),
                "dt": _value(row, "dt"),
                "gsis_id": _value(row, "gsis_id") or _value(identity, "gsis_id"),
                "espn_id": _value(row, "espn_id") or _value(identity, "espn_id"),
                "sleeper_id": _value(identity, "sleeper_id"),
                "player_name": _value(row, "player_name", "full_name", "player"),
                "position": position,
                "pos_slot": _value(row, "pos_slot", "depth_position"),
                "pos_rank": pos_rank,
                "depth_chart_role_score": _depth_chart_role_score(pos_rank),
                "schema_version": "official_nflverse_depth_charts_v1",
            }
        )
        if not local_row["player_name"] or not local_row["team"]:
            continue
        transformed.append(local_row)

    return transformed


def transform_official_depth_chart_csv(
    input_path: str | Path,
    output_path: str | Path,
    *,
    season: int,
    default_week: int = 0,
    identity_map_path: str | Path | None = None,
) -> NflversePlayerStatsTransformReport:
    source_rows = _read_csv(Path(input_path))
    identity_rows = _read_csv(Path(identity_map_path)) if identity_map_path else None
    transformed = transform_official_depth_chart_rows(
        source_rows,
        season=season,
        default_week=default_week,
        identity_rows=identity_rows,
    )
    output = Path(output_path)
    _write_csv(output, LOCAL_DEPTH_CHARTS_HEADER, transformed)
    skipped = len(source_rows) - len(transformed)
    return NflversePlayerStatsTransformReport(
        status="ready",
        rows_seen=len(source_rows),
        rows_transformed=len(transformed),
        rows_skipped=skipped,
        output_path=output,
        warnings=(),
    )


def download_official_player_stats_csv(
    output_path: str | Path,
    *,
    url: str = OFFICIAL_PLAYER_STATS_URL,
) -> NflversePlayerStatsTransformReport:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "niners-war-room-local-import"})
    with urlopen(request, timeout=60) as response:  # nosec B310 - explicit user import URL.
        output.write_bytes(response.read())
    return NflversePlayerStatsTransformReport(
        status="downloaded",
        rows_seen=0,
        rows_transformed=0,
        rows_skipped=0,
        output_path=output,
        warnings=("Download only; transform and validate before model use.",),
    )


def download_official_snap_counts_csv(
    output_path: str | Path,
    *,
    season: int,
) -> NflversePlayerStatsTransformReport:
    return _download_csv(
        output_path,
        url=OFFICIAL_SNAP_COUNTS_URL_PATTERN.format(season=season),
        warning="Download only; transform and validate before model use.",
    )


def download_official_depth_chart_csv(
    output_path: str | Path,
    *,
    season: int,
) -> NflversePlayerStatsTransformReport:
    return _download_csv(
        output_path,
        url=OFFICIAL_DEPTH_CHARTS_URL_PATTERN.format(season=season),
        warning="Download only; transform and validate before model use.",
    )


def write_local_player_stats_csv(
    output_path: str | Path,
    rows: list[dict[str, str]],
) -> None:
    _write_csv(Path(output_path), LOCAL_PLAYER_STATS_HEADER, rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    output_path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _download_csv(
    output_path: str | Path,
    *,
    url: str,
    warning: str,
) -> NflversePlayerStatsTransformReport:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "niners-war-room-local-import"})
    with urlopen(request, timeout=60) as response:  # nosec B310 - explicit import URL.
        output.write_bytes(response.read())
    return NflversePlayerStatsTransformReport(
        status="downloaded",
        rows_seen=0,
        rows_transformed=0,
        rows_skipped=0,
        output_path=output,
        warnings=(warning,),
    )


def _rows_by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {
        str(row.get(key) or "").strip(): row
        for row in rows
        if str(row.get(key) or "").strip()
    }


def _value(row: dict[str, str], *columns: str) -> str:
    for column in columns:
        value = str(row.get(column, "")).strip()
        if value:
            return value
    return ""


def _percent_to_number(value: str) -> str:
    if not value:
        return ""
    stripped = value.strip()
    if stripped.endswith("%"):
        return f"{float(stripped[:-1]) / 100.0:.4f}".rstrip("0").rstrip(".")
    return stripped


def _depth_chart_role_score(pos_rank: str) -> str:
    if not pos_rank:
        return ""
    rank = int(float(pos_rank))
    score = max(0.0, min(100.0, 100.0 - ((rank - 1) * 18.0)))
    return f"{score:.1f}".rstrip("0").rstrip(".")


def _sum_numeric(row: dict[str, str], *columns: str) -> str:
    total = 0.0
    has_value = False
    for column in columns:
        value = str(row.get(column, "")).strip()
        if not value:
            continue
        total += float(value)
        has_value = True
    if not has_value:
        return ""
    if total.is_integer():
        return str(int(total))
    return f"{total:.3f}".rstrip("0").rstrip(".")
