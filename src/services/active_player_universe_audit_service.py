from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.command_board_service import build_war_board
from src.services.draft_service import build_draft_room
from src.services.identity_audit_service import build_identity_audit
from src.services.warning_language_service import NO_ACTIVE_WARNING


@dataclass(frozen=True)
class ActivePlayerUniverseAuditReport:
    rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    blocker_rows: tuple[dict[str, object], ...]
    draft_pool_rows: tuple[dict[str, object], ...]
    draft_pool_summary_rows: tuple[dict[str, object], ...]


def build_active_player_universe_audit(
    data_pack_path: str | Path,
    *,
    source_root: str | Path | None = None,
    team_id: str = "niners",
) -> ActivePlayerUniverseAuditReport:
    validated = validate_data_pack(data_pack_path)
    identity = build_identity_audit(data_pack_path, source_root=source_root)
    identity_by_player_id = {str(row["player_id"]): row for row in identity.rows}
    war_board = build_war_board(data_pack_path)
    visible_ids = {str(row["player_id"]) for row in war_board.rows}
    roster_by_player_id = _roster_lookup(validated.rows_by_table.get("rosters", []))
    rows = tuple(
        _universe_row(
            player,
            roster_by_player_id.get(str(player.get("player_id") or ""), {}),
            identity_by_player_id.get(str(player.get("player_id") or ""), {}),
            visible_ids,
        )
        for player in validated.rows_by_table.get("players", [])
        if str(player.get("position") or "") in {"QB", "RB", "WR", "TE"}
    )

    draft_room = build_draft_room(data_pack_path, team_id=team_id)
    draft_pool_rows = tuple(_draft_pool_row(row) for row in draft_room.combined_rows)
    blocker_rows = tuple(
        row
        for row in rows
        if row["warning"] != NO_ACTIVE_WARNING
        or row["active_status"] in {"stale", "retired", "duplicate", "ambiguous"}
    )
    return ActivePlayerUniverseAuditReport(
        rows=rows,
        summary_rows=tuple(_summary_rows(rows)),
        blocker_rows=blocker_rows,
        draft_pool_rows=draft_pool_rows,
        draft_pool_summary_rows=tuple(_draft_pool_summary_rows(draft_pool_rows)),
    )


def write_active_player_universe_audit(
    export_dir: str | Path,
    report: ActivePlayerUniverseAuditReport,
) -> dict[str, Path]:
    destination = Path(export_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths = {
        "active_player_universe": destination / "active_player_universe.csv",
        "active_player_universe_summary": destination
        / "active_player_universe_summary.csv",
        "active_player_universe_blockers": destination
        / "active_player_universe_blockers.csv",
        "draftable_pool_universe": destination / "draftable_pool_universe.csv",
        "draftable_pool_summary": destination / "draftable_pool_summary.csv",
    }
    _write_csv(paths["active_player_universe"], list(report.rows))
    _write_csv(paths["active_player_universe_summary"], list(report.summary_rows))
    _write_csv(paths["active_player_universe_blockers"], list(report.blocker_rows))
    _write_csv(paths["draftable_pool_universe"], list(report.draft_pool_rows))
    _write_csv(paths["draftable_pool_summary"], list(report.draft_pool_summary_rows))
    return paths


def _universe_row(
    player: dict[str, object],
    roster: dict[str, object],
    identity: dict[str, object],
    visible_ids: set[str],
) -> dict[str, object]:
    player_id = str(player.get("player_id") or "")
    fantasy_team = str(roster.get("team_name") or "")
    rostered = bool(fantasy_team)
    active_status = _active_status(player, roster, identity)
    warning = _universe_warning(
        player_id=player_id,
        rostered=rostered,
        visible=player_id in visible_ids,
        active_status=active_status,
        identity=identity,
    )
    return {
        "player_id": player_id,
        "sleeper_id": player.get("sleeper_id") or identity.get("sleeper_id") or "",
        "gsis_id": identity.get("nflverse_gsis_id")
        or identity.get("sleeper_gsis_id")
        or "",
        "pfr_id": identity.get("pfr_id") or player.get("pfr_id") or "",
        "player_name": player.get("player_name") or identity.get("player") or "",
        "position": player.get("position") or identity.get("position") or "",
        "nfl_team": player.get("nfl_team") or roster.get("nfl_team") or "",
        "fantasy_team": fantasy_team,
        "roster_context": "rostered" if rostered else "not_rostered_in_pack",
        "active_status": active_status,
        "war_board_visible": player_id in visible_ids,
        "identity_status": identity.get("identity_status") or "missing_match",
        "identity_confidence": identity.get("identity_confidence") or "",
        "match_method": identity.get("match_method") or "",
        "warning": warning or NO_ACTIVE_WARNING,
        "ranking_allowed": player_id in visible_ids,
    }


def _draft_pool_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "asset_id": row.get("asset_id", ""),
        "player_id": _asset_player_id(row),
        "player_name": row.get("player", ""),
        "position": row.get("position", ""),
        "nfl_team": row.get("team", ""),
        "asset_type": row.get("asset_type", ""),
        "availability": row.get("availability", ""),
        "why_available": row.get("why_available", ""),
        "draft_value": row.get("draft_value", ""),
        "confidence": row.get("confidence", ""),
        "source": row.get("source", ""),
        "universe": "draftable_pool_only",
    }


def _active_status(
    player: dict[str, object],
    roster: dict[str, object],
    identity: dict[str, object],
) -> str:
    if identity.get("identity_status") == "stale_player":
        return "stale"
    active_flag = str(player.get("active_flag") or "").strip().lower()
    if active_flag in {"0", "false", "inactive", "stale"}:
        return "stale"
    if active_flag == "retired":
        return "retired"
    roster_status = str(roster.get("roster_status") or "").strip().lower()
    if roster_status in {"retired", "inactive", "stale", "deleted"}:
        return "retired" if roster_status == "retired" else "stale"
    if identity.get("identity_status") == "ambiguous_match":
        return "ambiguous"
    if roster:
        return "active_rostered"
    return "free_agent_or_unrostered"


def _universe_warning(
    *,
    player_id: str,
    rostered: bool,
    visible: bool,
    active_status: str,
    identity: dict[str, object],
) -> str:
    if active_status in {"stale", "retired"} and visible:
        return "stale_or_retired_player_visible_on_war_board"
    if active_status == "ambiguous" and visible:
        return "ambiguous_identity_visible_on_war_board"
    if not rostered and visible:
        return "unrostered_player_visible_on_war_board"
    if rostered and not visible and active_status == "active_rostered":
        return "rostered_player_missing_from_war_board"
    if identity.get("ranking_trust_status") == "blocked_identity_review":
        return "identity_blocker"
    if not player_id:
        return "missing_player_id"
    return ""


def _summary_rows(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    counts = Counter(str(row["active_status"]) for row in rows)
    visible = Counter(str(row["active_status"]) for row in rows if row["war_board_visible"])
    return [
        {
            "active_status": status,
            "player_count": counts[status],
            "visible_war_board_count": visible[status],
            "warning_count": sum(
                1
                for row in rows
                if row["active_status"] == status and row["warning"] != NO_ACTIVE_WARNING
            ),
        }
        for status in sorted(counts)
    ]


def _draft_pool_summary_rows(
    rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    counts = Counter(str(row["asset_type"]) for row in rows)
    return [
        {
            "asset_type": asset_type,
            "player_count": counts[asset_type],
            "review_or_low_confidence_count": sum(
                1
                for row in rows
                if row["asset_type"] == asset_type
                and _float(row.get("confidence")) < 60
            ),
        }
        for asset_type in sorted(counts)
    ]


def _roster_lookup(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _asset_player_id(row: dict[str, object]) -> str:
    asset_id = str(row.get("asset_id") or "")
    if ":" in asset_id:
        return asset_id.split(":", 1)[1]
    return str(row.get("player_id") or "")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = _fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _fieldnames(rows: list[dict[str, object]]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for field in row:
            if field not in seen:
                fields.append(field)
                seen.add(field)
    return fields or ["empty"]


def _float(value: object) -> float:
    try:
        text = str(value or "").strip()
        return float(text) if text else 0.0
    except (TypeError, ValueError):
        return 0.0
