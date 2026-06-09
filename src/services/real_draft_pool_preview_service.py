from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from src.data.validators import validate_data_pack
from src.services.sleeper_import_service import (
    DEFAULT_LEAGUE_ID,
    SleeperHttpClient,
    export_sleeper_snapshot,
)

OFFICIAL_DRAFT_PICKS_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "draft_picks/draft_picks.csv"
)
DYNASTYPROCESS_PLAYER_IDS_URL = (
    "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
)
DEFAULT_DRAFT_POOL_OUTPUT_ROOT = Path("local_exports/data_packs")
MODEL_POSITIONS = {"QB", "RB", "WR", "TE"}

ROOKIE_DRAFTABLE_HEADER = (
    "season",
    "player_id",
    "sleeper_id",
    "gsis_id",
    "pfr_id",
    "player_name",
    "position",
    "nfl_team",
    "asset_type",
    "draft_round",
    "draft_pick",
    "college",
    "draft_value",
    "market_value",
    "model_value",
    "confidence",
    "why_available",
    "source_name",
    "source_updated_at",
    "review_status",
    "recommendation",
    "recommended_range",
    "do_not_draft_before_pick",
)
AVAILABLE_VETERAN_HEADER = (
    "season",
    "player_id",
    "sleeper_id",
    "gsis_id",
    "pfr_id",
    "player_name",
    "position",
    "nfl_team",
    "asset_type",
    "previous_lve_team",
    "previous_roster_id",
    "availability_status",
    "draft_value",
    "market_value",
    "model_value",
    "confidence",
    "why_available",
    "source_name",
    "source_updated_at",
    "review_status",
    "recommendation",
    "recommended_range",
    "do_not_draft_before_pick",
)
MANUAL_DRAFTABLE_HEADER = (
    "season",
    "player_id",
    "sleeper_id",
    "gsis_id",
    "pfr_id",
    "player_name",
    "position",
    "nfl_team",
    "asset_type",
    "draft_value",
    "market_value",
    "model_value",
    "confidence",
    "why_available",
    "manual_reason",
    "entered_by",
    "entered_at",
    "review_status",
    "manual_status",
    "recommendation",
    "recommended_range",
    "do_not_draft_before_pick",
)


@dataclass(frozen=True)
class DraftPoolPreviewStep:
    step: str
    status: str
    output_path: str
    rows: int | str
    message: str


@dataclass(frozen=True)
class DraftPoolPreviewResult:
    preview_id: str
    output_pack_path: Path
    status: str
    steps: tuple[DraftPoolPreviewStep, ...]
    manifest_path: Path
    readiness_path: Path
    rookie_path: Path
    available_veteran_path: Path
    manual_path: Path


def build_real_draft_pool_preview(
    *,
    data_pack_path: str | Path,
    league_id: str = DEFAULT_LEAGUE_ID,
    output_root: str | Path = DEFAULT_DRAFT_POOL_OUTPUT_ROOT,
    draft_year: int | None = None,
    client: SleeperHttpClient | None = None,
    preview_id: str | None = None,
) -> DraftPoolPreviewResult:
    created_at = datetime.now(UTC)
    source_pack = Path(data_pack_path)
    resolved_preview_id = preview_id or created_at.strftime("draft_pool_%Y%m%d_%H%M%S")
    output_pack = Path(output_root) / f"{source_pack.name}_{resolved_preview_id}"
    if output_pack.exists():
        raise FileExistsError(f"Preview data pack already exists: {output_pack}")
    shutil.copytree(source_pack, output_pack)

    downloads_dir = output_pack / "draft_pool_downloads"
    reports_dir = output_pack / "draft_pool_reports"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    steps: list[DraftPoolPreviewStep] = []
    http = client or SleeperHttpClient()
    sleeper_result = export_sleeper_snapshot(
        league_id=league_id,
        output_root=downloads_dir / "sleeper",
        client=http,
        snapshot_name=resolved_preview_id,
    )
    steps.append(
        _step(
            "sleeper_snapshot",
            "ok",
            sleeper_result.output_dir,
            sleeper_result.counts.get("rosters", 0),
            "Sleeper snapshot refreshed for protected roster and free-agent checks.",
        )
    )

    sleeper_players = http.get_json("players/nfl")
    sleeper_rows = _sleeper_player_rows(sleeper_players)
    sleeper_players_csv = downloads_dir / "sleeper_players_nfl.csv"
    _write_csv(
        sleeper_players_csv,
        (
            "sleeper_id",
            "player_name",
            "position",
            "nfl_team",
            "status",
            "active",
            "search_rank",
            "depth_chart_order",
            "years_exp",
            "birth_date",
            "age",
            "gsis_id",
            "espn_id",
            "fantasy_data_id",
            "pfr_id",
        ),
        sleeper_rows,
    )
    steps.append(
        _step(
            "sleeper_players",
            "ok",
            sleeper_players_csv,
            len(sleeper_rows),
            "Sleeper player universe cached for free-agent and rookie identity matching.",
        )
    )

    draft_picks_path = downloads_dir / "nflverse_draft_picks.csv"
    _download_file(OFFICIAL_DRAFT_PICKS_URL, draft_picks_path)
    _, draft_pick_rows = _read_csv(draft_picks_path)
    resolved_draft_year = draft_year or _latest_draft_year(draft_pick_rows)
    steps.append(
        _step(
            "nflverse_draft_picks",
            "ok",
            draft_picks_path,
            len(draft_pick_rows),
            f"nflverse draft picks loaded; using draft year {resolved_draft_year}.",
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
            "DynastyProcess ID bridge loaded for rookie identity matching.",
        )
    )

    protected_ids = _protected_player_ids_from_pack(source_pack)
    sleeper_protected_ids = _protected_player_ids_from_sleeper_snapshot(
        sleeper_result.output_dir / "sleeper_rosters.csv"
    )
    protected_ids.update(sleeper_protected_ids)
    rookie_rows = build_rookie_draftable_rows(
        draft_pick_rows=draft_pick_rows,
        ffid_rows=ffid_rows,
        sleeper_rows=sleeper_rows,
        protected_player_ids=protected_ids,
        draft_year=resolved_draft_year,
        source_updated_at=created_at.isoformat(),
    )
    rookie_path = output_pack / "fact_rookie_draftables.csv"
    _write_csv(rookie_path, ROOKIE_DRAFTABLE_HEADER, rookie_rows)
    steps.append(
        _step(
            "rookie_draftables",
            "ok" if rookie_rows else "review",
            rookie_path,
            len(rookie_rows),
            "Current-year public rookie draftables written to preview pack.",
        )
    )

    rookie_sleeper_ids = {
        row["sleeper_id"] for row in rookie_rows if str(row.get("sleeper_id") or "")
    }
    free_agent_rows = build_free_agent_rows(
        sleeper_rows=sleeper_rows,
        protected_player_ids=protected_ids,
        rookie_sleeper_ids=rookie_sleeper_ids,
        season=resolved_draft_year,
        source_updated_at=created_at.isoformat(),
    )
    available_veteran_path = output_pack / "fact_available_veterans.csv"
    _write_csv(available_veteran_path, AVAILABLE_VETERAN_HEADER, free_agent_rows)
    steps.append(
        _step(
            "available_veterans",
            "review",
            available_veteran_path,
            len(free_agent_rows),
            (
                "Free agents are included; released veterans remain empty until "
                "official declarations are provided."
            ),
        )
    )

    manual_path = output_pack / "fact_manual_draftables.csv"
    _write_csv(manual_path, MANUAL_DRAFTABLE_HEADER, [])
    steps.append(
        _step(
            "manual_draftables",
            "optional",
            manual_path,
            0,
            "Manual draftables template created but not populated.",
        )
    )

    readiness_rows = draft_pool_readiness_rows(
        rookie_rows=rookie_rows,
        free_agent_rows=free_agent_rows,
        released_veteran_count=0,
        manual_count=0,
    )
    readiness_path = reports_dir / "draft_pool_readiness.csv"
    _write_csv(
        readiness_path,
        (
            "source",
            "status",
            "rows",
            "required",
            "review_only",
            "decision_effect",
            "next_action",
        ),
        readiness_rows,
    )
    manifest_path = output_pack / "draft_pool_preview_manifest.json"
    manifest = {
        "preview_id": resolved_preview_id,
        "created_at": created_at.isoformat(),
        "source_data_pack": str(source_pack),
        "output_pack": str(output_pack),
        "draft_year": resolved_draft_year,
        "status": "review",
        "decision_ready": False,
        "released_veterans": "empty_until_user_provides_official_releases",
        "protected_players_excluded": len(protected_ids),
        "rookie_rows": len(rookie_rows),
        "free_agent_rows": len(free_agent_rows),
        "manual_rows": 0,
        "notes": (
            "Preview draft pool only. This pack can be selected for mock "
            "draft UX, but it is not decision-ready."
        ),
        "steps": [step.__dict__ for step in steps],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    return DraftPoolPreviewResult(
        preview_id=resolved_preview_id,
        output_pack_path=output_pack,
        status="review",
        steps=tuple(steps),
        manifest_path=manifest_path,
        readiness_path=readiness_path,
        rookie_path=rookie_path,
        available_veteran_path=available_veteran_path,
        manual_path=manual_path,
    )


def build_rookie_draftable_rows(
    *,
    draft_pick_rows: list[dict[str, str]],
    ffid_rows: list[dict[str, str]],
    sleeper_rows: list[dict[str, str]],
    protected_player_ids: set[str],
    draft_year: int,
    source_updated_at: str,
) -> list[dict[str, object]]:
    ffids_by_pfr = {row.get("pfr_id", ""): row for row in ffid_rows if row.get("pfr_id")}
    ffids_by_gsis = {row.get("gsis_id", ""): row for row in ffid_rows if row.get("gsis_id")}
    sleeper_by_id = {row["sleeper_id"]: row for row in sleeper_rows if row["sleeper_id"]}
    sleeper_by_name_position = {
        (_name_key(row["player_name"]), row["position"]): row
        for row in sleeper_rows
        if row["player_name"] and row["position"]
    }
    rows: list[dict[str, object]] = []
    for raw in draft_pick_rows:
        if str(raw.get("season") or "") != str(draft_year):
            continue
        position = str(raw.get("position") or "").upper()
        if position not in MODEL_POSITIONS:
            continue
        pfr_id = str(raw.get("pfr_player_id") or "")
        gsis_id = str(raw.get("gsis_id") or "")
        ffid = ffids_by_pfr.get(pfr_id) or ffids_by_gsis.get(gsis_id) or {}
        sleeper_id = str(ffid.get("sleeper_id") or "")
        sleeper = sleeper_by_id.get(sleeper_id) if sleeper_id else None
        if sleeper is None:
            sleeper = sleeper_by_name_position.get(
                (_name_key(str(raw.get("pfr_player_name") or "")), position)
            )
            sleeper_id = str(sleeper.get("sleeper_id") or "") if sleeper else ""
        player_id = sleeper_id or pfr_id or str(raw.get("cfb_player_id") or "")
        if player_id in protected_player_ids or sleeper_id in protected_player_ids:
            continue
        draft_pick = _safe_int(raw.get("pick")) or 999
        draft_round = _safe_int(raw.get("round")) or 99
        draft_value = _rookie_draft_value(draft_pick, draft_round)
        confidence = 72 if sleeper_id and (gsis_id or pfr_id) else 58
        rows.append(
            {
                "season": draft_year,
                "player_id": player_id,
                "sleeper_id": sleeper_id,
                "gsis_id": gsis_id or str(ffid.get("gsis_id") or ""),
                "pfr_id": pfr_id,
                "player_name": raw.get("pfr_player_name") or "",
                "position": position,
                "nfl_team": raw.get("team") or "",
                "asset_type": "rookie",
                "draft_round": draft_round,
                "draft_pick": draft_pick,
                "college": raw.get("college") or "",
                "draft_value": draft_value,
                "market_value": "",
                "model_value": draft_value,
                "confidence": confidence,
                "why_available": "rookie_current_year",
                "source_name": "nflverse_draft_picks",
                "source_updated_at": source_updated_at,
                "review_status": "review_needed",
                "recommendation": "rookie_review",
                "recommended_range": "",
                "do_not_draft_before_pick": _draft_pick_floor(draft_value),
            }
        )
    return sorted(rows, key=lambda row: (-float(row["draft_value"]), str(row["player_name"])))


def build_free_agent_rows(
    *,
    sleeper_rows: list[dict[str, str]],
    protected_player_ids: set[str],
    rookie_sleeper_ids: set[str],
    season: int,
    source_updated_at: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in sleeper_rows:
        sleeper_id = raw["sleeper_id"]
        if sleeper_id in protected_player_ids or sleeper_id in rookie_sleeper_ids:
            continue
        position = str(raw.get("position") or "").upper()
        if position not in MODEL_POSITIONS:
            continue
        if not _looks_like_active_free_agent(raw):
            continue
        rows.append(
            {
                "season": season,
                "player_id": sleeper_id,
                "sleeper_id": sleeper_id,
                "gsis_id": raw.get("gsis_id") or "",
                "pfr_id": raw.get("pfr_id") or "",
                "player_name": raw.get("player_name") or sleeper_id,
                "position": position,
                "nfl_team": raw.get("nfl_team") or "",
                "asset_type": "free_agent",
                "previous_lve_team": "",
                "previous_roster_id": "",
                "availability_status": "sleeper_unrostered",
                "draft_value": 0,
                "market_value": "",
                "model_value": 0,
                "confidence": 35,
                "why_available": "sleeper_unrostered_free_agent",
                "source_name": "sleeper_players_minus_rosters",
                "source_updated_at": source_updated_at,
                "review_status": "review_needed",
                "recommendation": "free_agent_review",
                "recommended_range": "",
                "do_not_draft_before_pick": "",
            }
        )
    return sorted(rows, key=lambda row: (str(row["position"]), str(row["player_name"])))


def draft_pool_readiness_rows(
    *,
    rookie_rows: list[dict[str, object]],
    free_agent_rows: list[dict[str, object]],
    released_veteran_count: int,
    manual_count: int,
) -> list[dict[str, object]]:
    return [
        _readiness_row(
            source="rookies",
            rows=len(rookie_rows),
            required=True,
            review_only=False,
            status="loaded" if rookie_rows else "missing_required",
            next_action="Review rookie scores before using for money decisions.",
        ),
        _readiness_row(
            source="released veterans",
            rows=released_veteran_count,
            required=True,
            review_only=True,
            status="review_needed",
            next_action="Add official declared releases when the league provides them.",
            decision_effect="blocks_draft_ready_not_roster_declaration",
        ),
        _readiness_row(
            source="free agents",
            rows=len(free_agent_rows),
            required=True,
            review_only=False,
            status="loaded" if free_agent_rows else "missing_required",
            next_action="Review free-agent relevance; scores are placeholders until modeled.",
        ),
        _readiness_row(
            source="manual draftables",
            rows=manual_count,
            required=False,
            review_only=False,
            status="optional_missing" if manual_count == 0 else "loaded",
            next_action="Use only for commissioner exceptions or unusual cases.",
        ),
    ]


def _readiness_row(
    *,
    source: str,
    rows: int,
    required: bool,
    review_only: bool,
    status: str,
    next_action: str,
    decision_effect: str | None = None,
) -> dict[str, object]:
    blocking = required and status not in {"loaded"}
    return {
        "source": source,
        "status": status,
        "rows": rows,
        "required": required,
        "review_only": review_only,
        "decision_effect": decision_effect
        or ("blocks_decision_ready" if blocking else "review"),
        "next_action": next_action,
    }


def _protected_player_ids_from_pack(data_pack_path: Path) -> set[str]:
    validated = validate_data_pack(data_pack_path)
    protected_statuses = {"", "rostered", "protected", "keeper", "active"}
    return {
        str(row.get("player_id") or "")
        for row in validated.rows_by_table.get("rosters", [])
        if str(row.get("roster_status") or "").strip().lower() in protected_statuses
    }


def _protected_player_ids_from_sleeper_snapshot(rosters_path: Path) -> set[str]:
    if not rosters_path.exists():
        return set()
    with rosters_path.open(newline="", encoding="utf-8") as handle:
        return {
            str(row.get("player_id") or "")
            for row in csv.DictReader(handle)
            if str(row.get("roster_status") or "").strip().lower() == "rostered"
        }


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
                "nfl_team": str(raw_player.get("team") or ""),
                "status": str(raw_player.get("status") or ""),
                "active": str(raw_player.get("active") or ""),
                "search_rank": str(raw_player.get("search_rank") or ""),
                "depth_chart_order": str(raw_player.get("depth_chart_order") or ""),
                "years_exp": str(raw_player.get("years_exp") or ""),
                "birth_date": str(raw_player.get("birth_date") or ""),
                "age": str(raw_player.get("age") or ""),
                "gsis_id": str(raw_player.get("gsis_id") or ""),
                "espn_id": str(raw_player.get("espn_id") or ""),
                "fantasy_data_id": str(raw_player.get("fantasy_data_id") or ""),
                "pfr_id": str(raw_player.get("pfr_id") or ""),
            }
        )
    return rows


def _looks_like_active_free_agent(row: dict[str, str]) -> bool:
    status = str(row.get("status") or "").lower()
    team = str(row.get("nfl_team") or "")
    active = str(row.get("active") or "").lower() == "true"
    depth_chart_order = _safe_int(row.get("depth_chart_order"))
    years_exp = _safe_int(row.get("years_exp"))
    age = _safe_int(row.get("age"))
    if status in {"inactive", "injured reserve", "retired"}:
        return False
    if not active or not team:
        return False
    if depth_chart_order is not None:
        return True
    if years_exp is not None and years_exp <= 1:
        return True
    return bool(age is not None and age <= 24)


def _latest_draft_year(rows: list[dict[str, str]]) -> int:
    seasons = [_safe_int(row.get("season")) for row in rows]
    return max(season for season in seasons if season is not None)


def _rookie_draft_value(pick: int, round_number: int) -> float:
    if pick <= 8:
        return round(96 - ((pick - 1) * 1.1), 2)
    if pick <= 32:
        return round(88 - ((pick - 9) * 0.42), 2)
    if pick <= 100:
        return round(78 - ((pick - 33) * 0.22), 2)
    if pick <= 180:
        return round(62 - ((pick - 101) * 0.12), 2)
    if pick <= 260:
        return round(50 - ((pick - 181) * 0.08), 2)
    return max(30.0, 42.0 - round_number)


def _draft_pick_floor(draft_value: float) -> int:
    if draft_value >= 90:
        return 1
    if draft_value >= 84:
        return 4
    if draft_value >= 76:
        return 8
    if draft_value >= 66:
        return 16
    if draft_value >= 56:
        return 26
    return 40


def _download_file(url: str, path: Path) -> None:
    request = Request(url, headers={"User-Agent": "niners-war-room-draft-pool"})
    with urlopen(request, timeout=120) as response:  # nosec B310 - approved public sources.
        path.write_bytes(response.read())


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


def _name_key(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _safe_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _step(
    step: str,
    status: str,
    output_path: str | Path,
    rows: int | str,
    message: str,
) -> DraftPoolPreviewStep:
    return DraftPoolPreviewStep(
        step=step,
        status=status,
        output_path=str(output_path),
        rows=rows,
        message=message,
    )
