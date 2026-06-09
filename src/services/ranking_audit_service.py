from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.command_board_service import build_team_command_board, build_war_board
from src.services.draft_service import build_draft_room
from src.services.league_service import build_league_intel
from src.services.ranking_surface_service import (
    FORCED_RELEASE_PAIN,
    KEEPER_DECISION,
    PURE_MODEL_VALUE,
    TRADE_LIQUIDITY,
    apply_ranking_surface,
    surface_for_id,
)
from src.services.trade_service import build_trade_central


@dataclass(frozen=True)
class RankingAuditReport:
    rows: list[dict[str, object]]
    pages: list[str]
    sources: list[str]
    rank_columns: list[str]


def build_ranking_audit(
    data_pack_path: str | Path,
    *,
    rookie_model_dir: str | Path | None = None,
) -> RankingAuditReport:
    model_lookup = _model_lookup(data_pack_path)
    rows: list[dict[str, object]] = []
    rows.extend(_war_board_rows(data_pack_path, model_lookup))
    rows.extend(_my_team_rows(data_pack_path, model_lookup))
    rows.extend(_league_intel_rows(data_pack_path, model_lookup))
    rows.extend(_draft_board_rows(data_pack_path, model_lookup, rookie_model_dir))
    rows.extend(_trade_central_rows(data_pack_path, model_lookup))
    return RankingAuditReport(
        rows=rows,
        pages=sorted({str(row["page"]) for row in rows}),
        sources=sorted({str(row["source"]) for row in rows}),
        rank_columns=sorted({str(row["rank_column"]) for row in rows}),
    )


def ranking_audit_summary_rows(report: RankingAuditReport) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for page in report.pages:
        page_rows = [row for row in report.rows if row["page"] == page]
        rows.append(
            {
                "page": page,
                "rows": len(page_rows),
                "rank_columns": ", ".join(
                    sorted({str(row["rank_column"]) for row in page_rows})
                ),
                "sources": ", ".join(sorted({str(row["source"]) for row in page_rows})),
            }
        )
    return rows


def _war_board_rows(
    data_pack_path: str | Path,
    model_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    board = build_war_board(data_pack_path)
    rows: list[dict[str, object]] = []
    for surface_id in (
        PURE_MODEL_VALUE,
        KEEPER_DECISION,
        TRADE_LIQUIDITY,
        FORCED_RELEASE_PAIN,
    ):
        surface = surface_for_id(surface_id)
        rows.extend(
            _audit_row(
                page="War Board",
                source=f"war_board:{surface.surface_id}",
                displayed_rank=index,
                row=row,
                rank_column=surface.rank_source,
                rank_value=row.get("surface_rank"),
                sort_direction=surface.sort_description,
                tie_breakers="player asc",
                model_lookup=model_lookup,
                surface=surface.label,
                intended_use=surface.intended_use,
            )
            for index, row in enumerate(
                apply_ranking_surface(board.rows, surface_id),
                start=1,
            )
        )
    return rows


def _my_team_rows(
    data_pack_path: str | Path,
    model_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    board = build_team_command_board(data_pack_path)
    rows: list[dict[str, object]] = []
    rows.extend(
        _audit_row(
            page="My Team",
            source="roster_command_table",
            displayed_rank=index,
            row=row,
            rank_column="source_roster_order",
            rank_value=index,
            sort_direction="source_order",
            tie_breakers="none",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.roster_rows, start=1)
    )
    rows.extend(
        _audit_row(
            page="My Team",
            source="league_rank_top_five",
            displayed_rank=index,
            row=row,
            rank_column="league_rank",
            rank_value=row.get("league_rank"),
            sort_direction="asc",
            tie_breakers="player asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.top_five_rows, start=1)
    )
    rows.extend(
        _audit_row(
            page="My Team",
            source="forced_release_table",
            displayed_rank=index,
            row=row,
            rank_column="drop_score",
            rank_value=row.get("drop_score"),
            sort_direction="desc",
            tie_breakers="keeper_score asc, league_rank asc, player asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.forced_release_rows, start=1)
    )
    return rows


def _league_intel_rows(
    data_pack_path: str | Path,
    model_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    board = build_league_intel(data_pack_path)
    rows: list[dict[str, object]] = []
    rows.extend(
        _audit_row(
            page="League Intel",
            source="keeper_pressure_by_team",
            displayed_rank=index,
            row={
                "player": "",
                "pos": "",
                "team": row.get("team"),
                "confidence": "",
                "warning_status": "",
            },
            rank_column="pressure_count",
            rank_value=row.get("pressure_count"),
            sort_direction="desc",
            tie_breakers="team asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.pressure_rows, start=1)
    )
    rows.extend(
        _audit_row(
            page="League Intel",
            source="default_release_candidates",
            displayed_rank=index,
            row=row,
            rank_column="acquisition_value",
            rank_value=row.get("acquisition_value"),
            sort_direction="desc",
            tie_breakers="team asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.default_release_rows, start=1)
    )
    rows.extend(
        _audit_row(
            page="League Intel",
            source="league_targets",
            displayed_rank=index,
            row=row,
            rank_column="target_category,acquisition_value",
            rank_value=f"{row.get('target_category')}|{row.get('acquisition_value')}",
            sort_direction="target category asc, acquisition_value desc",
            tie_breakers="market_edge desc, player asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.target_rows, start=1)
    )
    return rows


def _draft_board_rows(
    data_pack_path: str | Path,
    model_lookup: dict[str, dict[str, object]],
    rookie_model_dir: str | Path | None,
) -> list[dict[str, object]]:
    board = build_draft_room(data_pack_path, rookie_model_dir=rookie_model_dir)
    rows: list[dict[str, object]] = []
    rows.extend(
        _audit_row(
            page="Draft Board",
            source="unified_asset_board",
            displayed_rank=index,
            row={
                "player": row.get("player"),
                "pos": row.get("position"),
                "team": row.get("team"),
                "confidence": row.get("confidence"),
                "warning_status": "",
                "recommendation": row.get("recommendation"),
            },
            rank_column="acquisition_value",
            rank_value=row.get("acquisition_value"),
            sort_direction="desc",
            tie_breakers="all_asset_value desc, asset_id asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.asset_rows, start=1)
    )
    rows.extend(
        _audit_row(
            page="Draft Board",
            source="offline_release_targets",
            displayed_rank=index,
            row=row,
            rank_column="reacquisition_or_opponent_target_score",
            rank_value=max(
                _float(row.get("reacquisition_priority")),
                _float(row.get("opponent_release_target_score")),
            ),
            sort_direction="desc",
            tie_breakers="player asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.release_target_rows, start=1)
    )
    rows.extend(
        _audit_row(
            page="Draft Board",
            source="pick_value_table",
            displayed_rank=index,
            row={
                "player": row.get("pick"),
                "pos": "PICK",
                "team": row.get("current_team"),
                "confidence": "",
                "warning_status": "",
            },
            rank_column="current_team,pick_year,overall_pick",
            rank_value=row.get("overall_pick"),
            sort_direction="asc",
            tie_breakers="current_team asc, pick_year asc, overall_pick asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.pick_rows, start=1)
    )
    return rows


def _trade_central_rows(
    data_pack_path: str | Path,
    model_lookup: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    board = build_trade_central(data_pack_path)
    rows: list[dict[str, object]] = []
    rows.extend(
        _audit_row(
            page="Trade Lab",
            source="player_signals",
            displayed_rank=index,
            row=row,
            rank_column="signal_order,trade_value",
            rank_value=f"{row.get('signal')}|{row.get('trade_value')}",
            sort_direction="signal_order asc, trade_value desc",
            tie_breakers="player asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.player_rows, start=1)
    )
    rows.extend(
        _audit_row(
            page="Trade Lab",
            source="pick_paths",
            displayed_rank=index,
            row=row,
            rank_column="absolute_value_gap",
            rank_value=abs(_float(row.get("value_gap"))),
            sort_direction="asc",
            tie_breakers="pick asc",
            model_lookup=model_lookup,
        )
        for index, row in enumerate(board.path_rows, start=1)
    )
    return rows


def _audit_row(
    *,
    page: str,
    source: str,
    displayed_rank: int,
    row: dict[str, object],
    rank_column: str,
    rank_value: object,
    sort_direction: str,
    tie_breakers: str,
    model_lookup: dict[str, dict[str, object]],
    surface: str = "",
    intended_use: str = "",
) -> dict[str, object]:
    model = _lookup_model_row(row, model_lookup)
    confidence = _first_present(row.get("confidence"), model.get("confidence_score"))
    return {
        "page": page,
        "source": source,
        "displayed_rank": displayed_rank,
        "player": _first_present(row.get("player"), row.get("asset"), ""),
        "position": _first_present(row.get("pos"), row.get("position"), ""),
        "team": _first_present(row.get("team"), ""),
        "rank_column": rank_column,
        "rank_value": rank_value,
        "sort_direction": sort_direction,
        "tie_breakers": tie_breakers,
        "surface": surface,
        "intended_use": intended_use,
        "model_version": model.get("model_version", ""),
        "confidence": confidence,
        "warning_status": _first_present(
            row.get("warning_status"),
            model.get("warning_status"),
            "",
        ),
        "recommendation": _first_present(row.get("recommendation"), row.get("signal"), ""),
    }


def _model_lookup(data_pack_path: str | Path) -> dict[str, dict[str, object]]:
    validated = validate_data_pack(data_pack_path)
    lookup: dict[str, dict[str, object]] = {}
    for row in validated.rows_by_table.get("model_outputs", []):
        player_id = str(row.get("player_id") or "")
        player_name = str(row.get("player_name") or "")
        if player_id:
            lookup[f"id:{player_id}"] = row
        if player_name:
            lookup[f"name:{_normalize_name(player_name)}"] = row
    return lookup


def _lookup_model_row(
    row: dict[str, object],
    model_lookup: dict[str, dict[str, object]],
) -> dict[str, object]:
    player_id = str(row.get("player_id") or row.get("asset_id") or "")
    if player_id and f"id:{player_id}" in model_lookup:
        return model_lookup[f"id:{player_id}"]
    player = str(_first_present(row.get("player"), row.get("asset"), ""))
    if player and f"name:{_normalize_name(player)}" in model_lookup:
        return model_lookup[f"name:{_normalize_name(player)}"]
    return {}


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return ""


def _normalize_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)
