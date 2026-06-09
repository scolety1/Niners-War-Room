from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.command_board_service import build_war_board
from src.services.draft_service import build_draft_room
from src.services.ranking_surface_service import (
    DRAFT_AVAILABLE,
    FORCED_RELEASE_PAIN,
    KEEPER_DECISION,
    PURE_MODEL_VALUE,
    SURFACE_ORDER,
    TRADE_LIQUIDITY,
    apply_ranking_surface,
    surface_for_id,
)


@dataclass(frozen=True)
class RankingSurfaceAuditReport:
    surface_rows: tuple[dict[str, object], ...]
    excluded_rows: tuple[dict[str, object], ...]
    leakage_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]


WAR_BOARD_SURFACES: tuple[str, ...] = (
    PURE_MODEL_VALUE,
    KEEPER_DECISION,
    TRADE_LIQUIDITY,
    FORCED_RELEASE_PAIN,
)


def build_ranking_surface_audit(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
) -> RankingSurfaceAuditReport:
    validated = validate_data_pack(data_pack_path)
    protected_ids = _protected_player_ids(validated.rows_by_table.get("rosters", []))
    rostered_ids = _rostered_player_ids(validated.rows_by_table.get("rosters", []))
    war_board = build_war_board(data_pack_path)
    draft_room = build_draft_room(data_pack_path, team_id=team_id)

    surface_rows: list[dict[str, object]] = []
    excluded_rows: list[dict[str, object]] = []
    leakage_rows: list[dict[str, object]] = []

    for surface_id in WAR_BOARD_SURFACES:
        included = apply_ranking_surface(war_board.rows, surface_id)
        surface_rows.extend(
            _included_row(surface_id, row, source_board="War Board")
            for row in included
        )
        included_keys = {_player_key(row) for row in included}
        excluded_rows.extend(
            _excluded_row(surface_id, row, reason=_war_exclusion_reason(surface_id, row))
            for row in war_board.rows
            if _player_key(row) not in included_keys
        )

    draft_rows = _draft_surface_source_rows(draft_room.combined_rows)
    draft_included = apply_ranking_surface(draft_rows, DRAFT_AVAILABLE)
    surface_rows.extend(
        _included_row(DRAFT_AVAILABLE, row, source_board="Draft Board")
        for row in draft_included
    )
    draft_included_keys = {_player_key(row) for row in draft_included}
    excluded_rows.extend(
        _excluded_row(DRAFT_AVAILABLE, row, reason=_draft_exclusion_reason(row))
        for row in draft_rows
        if _player_key(row) not in draft_included_keys
    )

    leakage_rows.extend(
        _leakage_checks(
            war_rows=war_board.rows,
            draft_rows=draft_included,
            protected_ids=protected_ids,
            rostered_ids=rostered_ids,
        )
    )

    return RankingSurfaceAuditReport(
        surface_rows=tuple(surface_rows),
        excluded_rows=tuple(excluded_rows),
        leakage_rows=tuple(leakage_rows),
        summary_rows=tuple(_summary_rows(surface_rows, excluded_rows, leakage_rows)),
    )


def write_ranking_surface_audit(
    export_dir: str | Path,
    report: RankingSurfaceAuditReport,
) -> dict[str, Path]:
    destination = Path(export_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths = {
        "ranking_surface_rows": destination / "ranking_surface_rows.csv",
        "ranking_surface_excluded_rows": destination
        / "ranking_surface_excluded_rows.csv",
        "ranking_surface_leakage_rows": destination / "ranking_surface_leakage_rows.csv",
        "ranking_surface_summary": destination / "ranking_surface_summary.csv",
    }
    _write_csv(paths["ranking_surface_rows"], list(report.surface_rows))
    _write_csv(paths["ranking_surface_excluded_rows"], list(report.excluded_rows))
    _write_csv(paths["ranking_surface_leakage_rows"], list(report.leakage_rows))
    _write_csv(paths["ranking_surface_summary"], list(report.summary_rows))
    return paths


def _included_row(
    surface_id: str,
    row: dict[str, object],
    *,
    source_board: str,
) -> dict[str, object]:
    surface = surface_for_id(surface_id)
    return {
        "board_name": surface.label,
        "surface_id": surface.surface_id,
        "source_board": source_board,
        "surface_rank": row.get("surface_rank") or row.get("overall_rank") or "",
        "sort_column": surface.sort_description,
        "rank_source": surface.rank_source,
        "intended_use": surface.intended_use,
        "included_player_id": _row_player_id(row),
        "included_player": _row_player(row),
        "position": row.get("pos") or row.get("position") or "",
        "fantasy_team": row.get("team") or "",
        "asset_type": row.get("asset_type") or "",
        "draft_status": row.get("draft_status") or "",
        "league_rank": row.get("league_rank") or "",
        "model_value": row.get("stats_value") or row.get("stats_model_value") or "",
        "market_value": row.get("market_value") or "",
        "market_edge": row.get("market_edge") or "",
        "included_reason": _included_reason(surface_id),
        "review_status": "review_only",
    }


def _excluded_row(
    surface_id: str,
    row: dict[str, object],
    *,
    reason: str,
) -> dict[str, object]:
    surface = surface_for_id(surface_id)
    return {
        "board_name": surface.label,
        "surface_id": surface.surface_id,
        "excluded_player_id": _row_player_id(row),
        "excluded_player": _row_player(row),
        "position": row.get("pos") or row.get("position") or "",
        "fantasy_team": row.get("team") or "",
        "asset_type": row.get("asset_type") or "",
        "draft_status": row.get("draft_status") or "",
        "league_rank": row.get("league_rank") or "",
        "excluded_reason": reason,
        "intended_use": surface.intended_use,
    }


def _leakage_checks(
    *,
    war_rows: list[dict[str, object]],
    draft_rows: list[dict[str, object]],
    protected_ids: set[str],
    rostered_ids: set[str],
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for row in draft_rows:
        player_id = _row_player_id(row)
        if player_id in protected_ids:
            issues.append(
                _leakage_row(
                    "protected_roster_player_on_draft_available",
                    row,
                    "Protected roster players must not appear as draftable.",
                )
            )
    for row in war_rows:
        player_id = _row_player_id(row)
        if player_id and player_id not in rostered_ids:
            issues.append(
                _leakage_row(
                    "unrostered_player_on_rostered_surface",
                    row,
                    "Free agents/unrostered players must not appear on rostered ranking surfaces.",
                )
            )
    pure_surface = surface_for_id(PURE_MODEL_VALUE)
    if "market" in pure_surface.rank_source.lower():
        issues.append(
            {
                "leak_type": "market_rank_source_on_pure_model_value",
                "player_id": "",
                "player": "",
                "surface": pure_surface.label,
                "detail": "Pure Model Value rank source mentions market data.",
            }
        )
    forced_rows = apply_ranking_surface(war_rows, FORCED_RELEASE_PAIN)
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in war_rows:
        team = str(row.get("team") or "")
        grouped.setdefault(team, []).append(row)
    top_five_keys = {
        _player_key(row)
        for team_rows in grouped.values()
        for row in sorted(
            [
                candidate
                for candidate in team_rows
                if candidate.get("league_rank") not in (None, "")
            ],
            key=lambda candidate: (
                int(candidate.get("league_rank") or 999999),
                str(candidate.get("player") or ""),
            ),
        )[:5]
    }
    for row in forced_rows:
        if _player_key(row) not in top_five_keys:
            issues.append(
                _leakage_row(
                    "non_top_five_player_on_forced_release_pain",
                    row,
                    "Forced-release pain must rank only league-rank top-five candidates.",
                )
            )
    return issues


def _leakage_row(
    leak_type: str,
    row: dict[str, object],
    detail: str,
) -> dict[str, object]:
    return {
        "leak_type": leak_type,
        "player_id": _row_player_id(row),
        "player": _row_player(row),
        "surface": row.get("surface") or row.get("source_board") or "",
        "detail": detail,
    }


def _summary_rows(
    included_rows: list[dict[str, object]],
    excluded_rows: list[dict[str, object]],
    leakage_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    surface_ids = list(SURFACE_ORDER)
    for surface_id in surface_ids:
        included_count = sum(1 for row in included_rows if row["surface_id"] == surface_id)
        excluded_count = sum(1 for row in excluded_rows if row["surface_id"] == surface_id)
        leakage_count = sum(
            1 for row in leakage_rows if str(row.get("surface_id") or "") == surface_id
        )
        surface = surface_for_id(surface_id)
        rows.append(
            {
                "board_name": surface.label,
                "surface_id": surface.surface_id,
                "sort_column": surface.sort_description,
                "rank_source": surface.rank_source,
                "included_players": included_count,
                "excluded_players": excluded_count,
                "leakage_count": leakage_count,
                "intended_use": surface.intended_use,
                "review_status": "review_only",
            }
        )
    rows.append(
        {
            "board_name": "Leakage Checks",
            "surface_id": "all",
            "sort_column": "",
            "rank_source": "",
            "included_players": "",
            "excluded_players": "",
            "leakage_count": len(leakage_rows),
            "intended_use": "Cross-surface leak checks.",
            "review_status": "review_only",
        }
    )
    return rows


def _draft_surface_source_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            **row,
            "player_id": _asset_player_id(row),
            "draft_status": row.get("draft_status") or "available",
            "stats_model_value": row.get("model_value") or row.get("draft_value"),
            "market_value": row.get("market_value"),
            "market_edge": row.get("market_edge"),
        }
        for row in rows
    ]


def _included_reason(surface_id: str) -> str:
    if surface_id == DRAFT_AVAILABLE:
        return "Player is in the explicit draftable pool and has not been drafted in this state."
    if surface_id == FORCED_RELEASE_PAIN:
        return (
            "Player is inside that roster's five highest league-ranked players."
        )
    return "Player is a visible rostered asset for this surface."


def _war_exclusion_reason(surface_id: str, row: dict[str, object]) -> str:
    if surface_id == FORCED_RELEASE_PAIN:
        return (
            "Excluded from primary forced-release pain because this row is not inside "
            "that roster's five highest league-ranked players."
        )
    return "No exclusion expected for this rostered-player surface."


def _draft_exclusion_reason(row: dict[str, object]) -> str:
    if str(row.get("draft_status") or "") == "drafted":
        return "Already drafted in this mock/live draft state."
    return "Excluded from draftable view by draft-pool availability rules."


def _protected_player_ids(roster_rows: list[dict[str, object]]) -> set[str]:
    protected_statuses = {"", "rostered", "protected", "keeper", "active"}
    return {
        str(row.get("player_id") or "")
        for row in roster_rows
        if str(row.get("roster_status") or "").strip().lower() in protected_statuses
    }


def _rostered_player_ids(roster_rows: list[dict[str, object]]) -> set[str]:
    return {
        str(row.get("player_id") or "")
        for row in roster_rows
        if row.get("player_id")
    }


def _asset_player_id(row: dict[str, object]) -> str:
    asset_id = str(row.get("asset_id") or "")
    if ":" in asset_id:
        return asset_id.split(":", 1)[1]
    return str(row.get("player_id") or "")


def _row_player_id(row: dict[str, object]) -> str:
    return str(row.get("player_id") or _asset_player_id(row) or "")


def _row_player(row: dict[str, object]) -> str:
    return str(row.get("player") or row.get("player_name") or "")


def _player_key(row: dict[str, object]) -> str:
    player_id = _row_player_id(row)
    if player_id:
        return f"id:{player_id}"
    return f"name:{_row_player(row).lower()}|team:{row.get('team') or ''}"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = _fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _fieldnames(rows: list[dict[str, object]]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for field in row:
            if field not in seen:
                fields.append(field)
                seen.add(field)
    return fields or ["empty"]
