from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from src.data.validators import validate_data_pack
from src.services.nflverse_identity_service import (
    build_nflverse_identity_review_rows,
    nflverse_identity_review_summary_rows,
    validate_nflverse_identity_map,
)
from src.services.nflverse_player_stats_import_service import (
    OFFICIAL_DEPTH_CHARTS_URL_PATTERN,
    OFFICIAL_PLAYER_STATS_URL,
    OFFICIAL_SNAP_COUNTS_URL_PATTERN,
    transform_official_depth_chart_rows,
    transform_official_player_stats_rows,
    transform_official_snap_counts_rows,
)
from src.services.nflverse_raw_import_service import validate_nflverse_raw_imports
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)
from src.services.sleeper_import_service import (
    DEFAULT_LEAGUE_ID,
    SleeperHttpClient,
    export_sleeper_snapshot,
)

DEFAULT_PREVIEW_OUTPUT_ROOT = Path("local_exports/nflverse/preview")
OFFICIAL_NFLVERSE_PLAYERS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"
)
OFFICIAL_INJURIES_URL_PATTERN = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "injuries/injuries_{season}.csv"
)
DYNASTYPROCESS_PLAYER_IDS_URL = (
    "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
)
MODEL_POSITIONS = {"QB", "RB", "WR", "TE"}


@dataclass(frozen=True)
class PublicDataPreviewStep:
    step: str
    status: str
    output_path: str
    rows: int | str
    message: str


@dataclass(frozen=True)
class PublicDataPreviewImportResult:
    preview_id: str
    output_dir: Path
    raw_dir: Path
    status: str
    steps: tuple[PublicDataPreviewStep, ...]
    manifest_path: Path
    coverage_path: Path
    identity_map_path: Path
    critical_gap_path: Path


def run_public_data_preview_import(
    *,
    data_pack_path: str | Path,
    league_id: str = DEFAULT_LEAGUE_ID,
    output_root: str | Path = DEFAULT_PREVIEW_OUTPUT_ROOT,
    seasons: tuple[int, ...] = (2023, 2024, 2025),
    client: SleeperHttpClient | None = None,
    preview_id: str | None = None,
) -> PublicDataPreviewImportResult:
    created_at = datetime.now(UTC)
    resolved_preview_id = preview_id or created_at.strftime("public_data_%Y%m%d_%H%M%S")
    output_dir = Path(output_root) / resolved_preview_id
    downloads_dir = output_dir / "downloads"
    raw_dir = output_dir / "raw"
    reports_dir = output_dir / "reports"
    downloads_dir.mkdir(parents=True, exist_ok=False)
    raw_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    steps: list[PublicDataPreviewStep] = []
    http = client or SleeperHttpClient()

    sleeper_result = export_sleeper_snapshot(
        league_id=league_id,
        output_root=output_dir / "sleeper",
        client=http,
        snapshot_name=resolved_preview_id,
    )
    steps.append(
        _step(
            "sleeper_snapshot",
            "ok",
            sleeper_result.output_dir,
            sleeper_result.counts.get("rosters", 0),
            "Sleeper league rosters, teams, picks, and draft metadata refreshed locally.",
        )
    )

    sleeper_players = http.get_json("players/nfl")
    sleeper_players_path = downloads_dir / "sleeper_players_nfl.json"
    sleeper_players_path.write_text(
        json.dumps(sleeper_players, sort_keys=True),
        encoding="utf-8",
    )
    sleeper_player_rows = _sleeper_player_rows(sleeper_players)
    sleeper_players_csv_path = downloads_dir / "sleeper_players_nfl.csv"
    _write_csv(
        sleeper_players_csv_path,
        (
            "sleeper_id",
            "player_name",
            "position",
            "team",
            "status",
            "birth_date",
            "age",
            "gsis_id",
            "espn_id",
            "fantasy_data_id",
            "pfr_id",
        ),
        sleeper_player_rows,
    )
    steps.append(
        _step(
            "sleeper_players",
            "ok",
            sleeper_players_csv_path,
            len(sleeper_player_rows),
            "Sleeper player universe cached locally for identity review.",
        )
    )

    ffids_path = downloads_dir / "dynastyprocess_db_playerids.csv"
    _download_file(DYNASTYPROCESS_PLAYER_IDS_URL, ffids_path)
    _, ffid_rows = _read_csv(ffids_path)
    steps.append(
        _step(
            "dynastyprocess_ids",
            "ok",
            ffids_path,
            len(ffid_rows),
            "DynastyProcess player ID bridge downloaded locally.",
        )
    )

    players_path = downloads_dir / "nflverse_players.csv"
    _download_file(OFFICIAL_NFLVERSE_PLAYERS_URL, players_path)
    _, nflverse_player_rows = _read_csv(players_path)
    steps.append(
        _step(
            "nflverse_players",
            "ok",
            players_path,
            len(nflverse_player_rows),
            "nflverse player/bio file downloaded locally.",
        )
    )

    identity_map_path = raw_dir / "nflverse_identity_map.csv"
    identity_rows = build_identity_map_rows(
        data_pack_path=data_pack_path,
        sleeper_player_rows=sleeper_player_rows,
        ffid_rows=ffid_rows,
        nflverse_player_rows=nflverse_player_rows,
    )
    _write_csv(
        identity_map_path,
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_identity_map.csv"],
        identity_rows,
    )
    identity_report = validate_nflverse_identity_map(identity_map_path)
    steps.append(
        _step(
            "identity_bridge",
            identity_report.status,
            identity_map_path,
            len(identity_rows),
            "Sleeper-to-nflverse identity bridge built in preview mode.",
        )
    )

    player_stats_download = downloads_dir / "player_stats.csv"
    _download_file(OFFICIAL_PLAYER_STATS_URL, player_stats_download)
    _, player_stat_source_rows = _read_csv(player_stats_download)
    player_stats_rows = transform_official_player_stats_rows(
        player_stat_source_rows,
        seasons=set(seasons),
        season_type="REG",
    )
    player_stats_rows = _enrich_by_gsis(player_stats_rows, identity_rows)
    player_stats_path = raw_dir / "nflverse_player_stats_weekly.csv"
    _write_csv(
        player_stats_path,
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_player_stats_weekly.csv"],
        player_stats_rows,
    )
    steps.append(
        _step(
            "nflverse_player_stats",
            "ok",
            player_stats_path,
            len(player_stats_rows),
            f"Official player stats transformed for seasons {', '.join(map(str, seasons))}.",
        )
    )

    snap_rows: list[dict[str, str]] = []
    depth_rows: list[dict[str, str]] = []
    injury_rows: list[dict[str, str]] = []
    for season in seasons:
        snap_download = downloads_dir / f"snap_counts_{season}.csv"
        _download_file(OFFICIAL_SNAP_COUNTS_URL_PATTERN.format(season=season), snap_download)
        _, snap_source_rows = _read_csv(snap_download)
        snap_rows.extend(
            transform_official_snap_counts_rows(
                snap_source_rows,
                seasons={season},
                season_type="REG",
                identity_rows=identity_rows,
            )
        )

        depth_download = downloads_dir / f"depth_charts_{season}.csv"
        _download_file(
            OFFICIAL_DEPTH_CHARTS_URL_PATTERN.format(season=season),
            depth_download,
        )
        _, depth_source_rows = _read_csv(depth_download)
        depth_rows.extend(
            transform_official_depth_chart_rows(
                depth_source_rows,
                season=season,
                default_week=0,
                identity_rows=identity_rows,
            )
        )

        injury_download = downloads_dir / f"injuries_{season}.csv"
        _download_file(OFFICIAL_INJURIES_URL_PATTERN.format(season=season), injury_download)
        _, injury_source_rows = _read_csv(injury_download)
        injury_rows.extend(
            transform_official_injury_rows(
                injury_source_rows,
                season=season,
                identity_rows=identity_rows,
            )
        )

    snap_path = raw_dir / "nflverse_snap_counts_weekly.csv"
    _write_csv(
        snap_path,
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_snap_counts_weekly.csv"],
        snap_rows,
    )
    steps.append(
        _step(
            "nflverse_snap_counts",
            "ok",
            snap_path,
            len(snap_rows),
            "Official snap-count rows transformed with identity enrichment where possible.",
        )
    )

    depth_path = raw_dir / "nflverse_depth_chart_weekly.csv"
    _write_csv(
        depth_path,
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_depth_chart_weekly.csv"],
        depth_rows,
    )
    steps.append(
        _step(
            "nflverse_depth_charts",
            "ok",
            depth_path,
            len(depth_rows),
            "Official depth-chart rows transformed with role scores.",
        )
    )

    injury_path = raw_dir / "nflverse_injuries_weekly.csv"
    _write_csv(
        injury_path,
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS["nflverse_injuries_weekly.csv"],
        injury_rows,
    )
    steps.append(
        _step(
            "nflverse_injuries",
            "ok",
            injury_path,
            len(injury_rows),
            "Official injury/practice report rows transformed for preview use.",
        )
    )

    participation_path = raw_dir / "nflverse_participation_player_weekly.csv"
    _write_csv(
        participation_path,
        NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
            "nflverse_participation_player_weekly.csv"
        ],
        [],
    )
    steps.append(
        _step(
            "nflverse_participation",
            "review",
            participation_path,
            0,
            (
                "Participation/route proxy import is intentionally empty until a "
                "reviewed extractor is added."
            ),
        )
    )

    raw_report = validate_nflverse_raw_imports(raw_dir)
    identity_review_rows = build_nflverse_identity_review_rows(
        data_pack_path,
        identity_map_path,
    )
    identity_summary_rows = nflverse_identity_review_summary_rows(identity_review_rows)
    coverage_rows, critical_gap_rows = build_preview_coverage_rows(
        data_pack_path=data_pack_path,
        identity_rows=identity_rows,
        player_stats_rows=player_stats_rows,
        snap_rows=snap_rows,
        depth_rows=depth_rows,
        ffid_rows=ffid_rows,
        nflverse_player_rows=nflverse_player_rows,
    )

    coverage_path = reports_dir / "preview_import_coverage.csv"
    _write_csv(
        coverage_path,
        (
            "player_id",
            "player_name",
            "position",
            "team",
            "identity_status",
            "production_status",
            "role_usage_status",
            "age_bio_status",
            "missing_critical_buckets",
            "decision_effect",
        ),
        coverage_rows,
    )
    critical_gap_path = reports_dir / "preview_missing_critical_buckets.csv"
    _write_csv(
        critical_gap_path,
        (
            "player_id",
            "player_name",
            "position",
            "team",
            "missing_bucket",
            "decision_effect",
            "next_action",
        ),
        critical_gap_rows,
    )
    identity_review_path = reports_dir / "preview_identity_review.csv"
    _write_csv(
        identity_review_path,
        tuple(identity_review_rows[0].keys()) if identity_review_rows else (),
        identity_review_rows,
    )
    identity_summary_path = reports_dir / "preview_identity_summary.csv"
    _write_csv(
        identity_summary_path,
        tuple(identity_summary_rows[0].keys()) if identity_summary_rows else (),
        identity_summary_rows,
    )
    raw_readiness_rows = [
        {
            "file_name": file_name,
            "rows": raw_report.row_counts.get(file_name, 0),
            "status": "blocked"
            if any(
                issue.file_name == file_name and issue.severity == "error"
                for issue in raw_report.issues
            )
            else "review"
            if any(issue.file_name == file_name for issue in raw_report.issues)
            else "ready",
        }
        for file_name in sorted(raw_report.row_counts)
    ]
    raw_readiness_path = reports_dir / "preview_raw_readiness.csv"
    _write_csv(raw_readiness_path, ("file_name", "rows", "status"), raw_readiness_rows)

    steps.append(
        _step(
            "raw_validation",
            raw_report.status,
            raw_readiness_path,
            len(raw_report.issues),
            "Raw import contracts validated; scoring remains preview-only.",
        )
    )
    steps.append(
        _step(
            "coverage_report",
            "review" if critical_gap_rows else "ok",
            coverage_path,
            len(coverage_rows),
            "Coverage report generated for critical buckets.",
        )
    )

    manifest_path = output_dir / "preview_import_manifest.json"
    manifest = {
        "preview_id": resolved_preview_id,
        "created_at": created_at.isoformat(),
        "data_pack_path": str(Path(data_pack_path)),
        "league_id": league_id,
        "seasons": list(seasons),
        "status": "review",
        "model_promotion": "not_allowed",
        "decision_ready": False,
        "notes": (
            "Preview public-data import only. This run does not promote model "
            "outputs or mark rankings decision-ready."
        ),
        "files": {
            "raw_dir": str(raw_dir),
            "identity_map": str(identity_map_path),
            "coverage": str(coverage_path),
            "critical_gaps": str(critical_gap_path),
            "identity_review": str(identity_review_path),
            "raw_readiness": str(raw_readiness_path),
        },
        "step_statuses": [step.__dict__ for step in steps],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return PublicDataPreviewImportResult(
        preview_id=resolved_preview_id,
        output_dir=output_dir,
        raw_dir=raw_dir,
        status="review",
        steps=tuple(steps),
        manifest_path=manifest_path,
        coverage_path=coverage_path,
        identity_map_path=identity_map_path,
        critical_gap_path=critical_gap_path,
    )


def build_identity_map_rows(
    *,
    data_pack_path: str | Path,
    sleeper_player_rows: list[dict[str, str]],
    ffid_rows: list[dict[str, str]],
    nflverse_player_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    validated = validate_data_pack(data_pack_path)
    players = [
        row
        for row in validated.rows_by_table.get("players", [])
        if str(row.get("position") or "") in MODEL_POSITIONS
    ]
    sleeper_by_id = {row["sleeper_id"]: row for row in sleeper_player_rows if row["sleeper_id"]}
    ffid_by_sleeper = {row.get("sleeper_id", ""): row for row in ffid_rows if row.get("sleeper_id")}
    nflverse_by_gsis = {
        row.get("gsis_id", ""): row for row in nflverse_player_rows if row.get("gsis_id")
    }
    output: list[dict[str, str]] = []
    for player in players:
        player_id = str(player.get("player_id") or "")
        sleeper_id = str(player.get("sleeper_id") or player_id)
        ffid = ffid_by_sleeper.get(sleeper_id, {})
        sleeper = sleeper_by_id.get(sleeper_id, {})
        gsis_id = _first(ffid, sleeper, "gsis_id")
        nflverse = nflverse_by_gsis.get(gsis_id, {}) if gsis_id else {}
        pfr_id = _first(ffid, nflverse, sleeper, "pfr_id")
        espn_id = _first(ffid, nflverse, sleeper, "espn_id")
        fantasy_data_id = _first(ffid, sleeper, "fantasy_data_id")
        nfl_id = _first(ffid, nflverse, sleeper, "nfl_id")
        player_name = str(
            player.get("player_name")
            or ffid.get("name")
            or sleeper.get("player_name")
            or nflverse.get("display_name")
            or ""
        )
        position = str(
            player.get("position")
            or ffid.get("position")
            or sleeper.get("position")
            or ""
        )
        team = str(player.get("nfl_team") or ffid.get("team") or sleeper.get("team") or "")
        match_method, match_confidence, review_status, notes = _identity_status(
            sleeper_id=sleeper_id,
            gsis_id=gsis_id,
            pfr_id=pfr_id,
            espn_id=espn_id,
            fantasy_data_id=fantasy_data_id,
            ffid=ffid,
            sleeper=sleeper,
            nflverse=nflverse,
        )
        output.append(
            {
                "sleeper_id": sleeper_id,
                "gsis_id": gsis_id,
                "nfl_id": nfl_id,
                "espn_id": espn_id,
                "fantasy_data_id": fantasy_data_id,
                "pfr_id": pfr_id,
                "player_id": player_id,
                "player_name": player_name,
                "normalized_name": _name_key(player_name),
                "position": position,
                "team": team,
                "match_method": match_method,
                "match_confidence": str(match_confidence),
                "review_status": review_status,
                "notes": notes,
            }
        )
    return output


def transform_official_injury_rows(
    source_rows: list[dict[str, str]],
    *,
    season: int,
    identity_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    identity_by_gsis = {row.get("gsis_id", ""): row for row in identity_rows if row.get("gsis_id")}
    output: list[dict[str, str]] = []
    for row in source_rows:
        if str(row.get("season") or "") != str(season):
            continue
        if str(row.get("season_type") or row.get("game_type") or "REG") not in {"REG", ""}:
            continue
        position = str(row.get("position") or "").upper()
        if position not in MODEL_POSITIONS:
            continue
        gsis_id = str(row.get("gsis_id") or "")
        identity = identity_by_gsis.get(gsis_id, {})
        primary = str(row.get("report_primary_injury") or row.get("practice_primary_injury") or "")
        local_row = {
            column: ""
            for column in NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[
                "nflverse_injuries_weekly.csv"
            ]
        }
        local_row.update(
            {
                "season": str(row.get("season") or season),
                "week": str(row.get("week") or ""),
                "team": str(row.get("team") or ""),
                "gsis_id": gsis_id,
                "sleeper_id": str(identity.get("sleeper_id") or ""),
                "player_name": str(row.get("full_name") or ""),
                "position": position,
                "report_primary_injury": primary,
                "report_secondary_injury": str(row.get("report_secondary_injury") or ""),
                "report_status": str(row.get("report_status") or ""),
                "practice_primary_injury": str(row.get("practice_primary_injury") or ""),
                "practice_secondary_injury": str(row.get("practice_secondary_injury") or ""),
                "practice_status": str(row.get("practice_status") or ""),
                "normalized_body_part": _normalized_body_part(primary),
                "date_modified": str(row.get("date_modified") or ""),
                "source_confidence": "88",
            }
        )
        output.append(local_row)
    return output


def build_preview_coverage_rows(
    *,
    data_pack_path: str | Path,
    identity_rows: list[dict[str, str]],
    player_stats_rows: list[dict[str, str]],
    snap_rows: list[dict[str, str]],
    depth_rows: list[dict[str, str]],
    ffid_rows: list[dict[str, str]],
    nflverse_player_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    validated = validate_data_pack(data_pack_path)
    players = [
        row
        for row in validated.rows_by_table.get("players", [])
        if str(row.get("position") or "") in MODEL_POSITIONS
    ]
    ready_identity = {
        row["player_id"]: row
        for row in identity_rows
        if row.get("review_status") == "ready"
        and _safe_float(row.get("match_confidence")) >= 85
    }
    stats_gsis = {row.get("gsis_id", "") for row in player_stats_rows if row.get("gsis_id")}
    snap_ids = {
        row.get("sleeper_id", "") or row.get("gsis_id", "")
        for row in snap_rows
        if row.get("sleeper_id") or row.get("gsis_id")
    }
    depth_ids = {
        row.get("sleeper_id", "") or row.get("gsis_id", "")
        for row in depth_rows
        if row.get("sleeper_id") or row.get("gsis_id")
    }
    ffid_sleeper_birth = {
        row.get("sleeper_id", "")
        for row in ffid_rows
        if row.get("sleeper_id") and row.get("birthdate")
    }
    nflverse_gsis_birth = {
        row.get("gsis_id", "")
        for row in nflverse_player_rows
        if row.get("gsis_id") and row.get("birth_date")
    }
    coverage: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    for player in players:
        player_id = str(player.get("player_id") or "")
        identity = ready_identity.get(player_id)
        gsis_id = identity.get("gsis_id", "") if identity else ""
        sleeper_id = (
            identity.get("sleeper_id", "")
            if identity
            else str(player.get("sleeper_id") or player_id)
        )
        statuses = {
            "identity": "ready" if identity else "blocked",
            "production": "ready" if gsis_id and gsis_id in stats_gsis else "blocked",
            "role/usage": "ready"
            if (
                sleeper_id in snap_ids
                or gsis_id in snap_ids
                or sleeper_id in depth_ids
                or gsis_id in depth_ids
            )
            else "blocked",
            "age/bio": "ready"
            if sleeper_id in ffid_sleeper_birth or gsis_id in nflverse_gsis_birth
            else "blocked",
        }
        missing = [bucket for bucket, status in statuses.items() if status != "ready"]
        player_name = str(player.get("player_name") or "")
        position = str(player.get("position") or "")
        team = str(player.get("nfl_team") or "")
        coverage.append(
            {
                "player_id": player_id,
                "player_name": player_name,
                "position": position,
                "team": team,
                "identity_status": statuses["identity"],
                "production_status": statuses["production"],
                "role_usage_status": statuses["role/usage"],
                "age_bio_status": statuses["age/bio"],
                "missing_critical_buckets": "|".join(missing),
                "decision_effect": "blocks_decision_ready" if missing else "preview_ready",
            }
        )
        for bucket in missing:
            gaps.append(
                {
                    "player_id": player_id,
                    "player_name": player_name,
                    "position": position,
                    "team": team,
                    "missing_bucket": bucket,
                    "decision_effect": "blocks_decision_ready",
                    "next_action": _critical_gap_next_action(bucket),
                }
            )
    return coverage, gaps


def _download_file(url: str, path: Path) -> None:
    request = Request(url, headers={"User-Agent": "niners-war-room-preview-import"})
    with urlopen(request, timeout=120) as response:  # nosec B310 - approved public sources.
        path.write_bytes(response.read())


def _sleeper_player_rows(players: object) -> list[dict[str, str]]:
    if not isinstance(players, dict):
        return []
    rows: list[dict[str, str]] = []
    for sleeper_id, raw_player in players.items():
        if not isinstance(raw_player, dict):
            continue
        rows.append(
            {
                "sleeper_id": str(sleeper_id),
                "player_name": str(
                    raw_player.get("full_name")
                    or raw_player.get("search_full_name")
                    or raw_player.get("last_name")
                    or sleeper_id
                ),
                "position": str(raw_player.get("position") or ""),
                "team": str(raw_player.get("team") or ""),
                "status": str(raw_player.get("status") or ""),
                "birth_date": str(raw_player.get("birth_date") or ""),
                "age": str(raw_player.get("age") or ""),
                "gsis_id": str(raw_player.get("gsis_id") or ""),
                "espn_id": str(raw_player.get("espn_id") or ""),
                "fantasy_data_id": str(raw_player.get("fantasy_data_id") or ""),
                "pfr_id": str(raw_player.get("pfr_id") or ""),
            }
        )
    return rows


def _identity_status(
    *,
    sleeper_id: str,
    gsis_id: str,
    pfr_id: str,
    espn_id: str,
    fantasy_data_id: str,
    ffid: dict[str, str],
    sleeper: dict[str, str],
    nflverse: dict[str, str],
) -> tuple[str, int, str, str]:
    if ffid and gsis_id:
        return ("sleeper_id", 98, "ready", "Matched by DynastyProcess sleeper_id with GSIS.")
    if ffid and (pfr_id or espn_id or fantasy_data_id):
        return (
            "sleeper_id",
            92,
            "ready",
            "Matched by DynastyProcess sleeper_id with external IDs.",
        )
    if sleeper and gsis_id:
        return ("sleeper_id", 88, "ready", "Matched by Sleeper player id with GSIS.")
    if nflverse and gsis_id:
        return ("gsis_id", 88, "ready", "Matched by GSIS through nflverse players.")
    if sleeper_id and sleeper:
        return (
            "sleeper_id",
            72,
            "review",
            "Sleeper row exists, but no stable nflverse ID was found.",
        )
    return ("unmatched", 0, "blocked", "No deterministic identity bridge found.")


def _enrich_by_gsis(
    rows: list[dict[str, str]],
    identity_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    by_gsis = {row.get("gsis_id", ""): row for row in identity_rows if row.get("gsis_id")}
    output: list[dict[str, str]] = []
    for row in rows:
        identity = by_gsis.get(row.get("gsis_id", ""))
        if identity:
            row = dict(row)
            row["sleeper_id"] = identity.get("sleeper_id", "")
        output.append(row)
    return output


def _normalized_body_part(value: str) -> str:
    lowered = value.lower()
    if any(
        token in lowered
        for token in ("knee", "ankle", "hamstring", "foot", "leg", "quad", "calf")
    ):
        return "lower_body"
    if any(token in lowered for token in ("shoulder", "elbow", "hand", "wrist", "arm")):
        return "upper_body"
    if any(token in lowered for token in ("head", "concussion", "neck")):
        return "head_neck"
    if any(token in lowered for token in ("illness", "personal")):
        return "non_orthopedic"
    return "unknown" if value else ""


def _critical_gap_next_action(bucket: str) -> str:
    return {
        "identity": "Review identity_bridge.csv and resolve missing/low-confidence IDs.",
        "production": "Confirm GSIS mapping or import additional historical player stats.",
        "role/usage": "Confirm snap/depth ID mapping or add reviewed role source.",
        "age/bio": "Confirm DynastyProcess/nflverse birth-date mapping.",
    }.get(bucket, "Review the missing source bucket.")


def _first(*rows: dict[str, str], key: str | None = None) -> str:
    if key is None:
        *row_values, column = rows
        for row in row_values:
            value = str(row.get(str(column)) or "").strip()
            if value:
                return value
        return ""
    for row in rows:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _name_key(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _safe_float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(reader.fieldnames or ()), list(reader)


def _write_csv(path: Path, header: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(header), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _step(
    step: str,
    status: str,
    output_path: str | Path,
    rows: int | str,
    message: str,
) -> PublicDataPreviewStep:
    return PublicDataPreviewStep(
        step=step,
        status=status,
        output_path=str(output_path),
        rows=rows,
        message=message,
    )
