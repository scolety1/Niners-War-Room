from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.services.draft_service import DraftRoomBoard, build_draft_room
from src.services.player_lifecycle_service import (
    asset_lifecycle_for_row,
    asset_lifecycle_label,
)
from src.services.warning_language_service import confidence_explanation, confidence_label

DRAFT_ROUNDS = 5
DRAFT_TEAMS = 10
DRAFT_TOTAL_PICKS = DRAFT_ROUNDS * DRAFT_TEAMS

RANKINGS_COLUMN_LABELS: dict[str, str] = {
    "overall_rank": "Rank",
    "player": "Player",
    "position": "Position",
    "nfl_team": "NFL Team",
    "asset_type": "Asset Type",
    "asset_lifecycle_label": "Lifecycle",
    "why_available": "Why Available",
    "draft_status": "Status",
    "drafted_pick": "Drafted Pick",
    "stats_model_value": "Model Value",
    "market_value": "Trade Market",
    "market_edge": "Model vs Market",
    "confidence": "Confidence",
    "confidence_label": "Confidence Label",
    "confidence_explanation": "Confidence Why",
    "warning": "Warning",
}

RANKINGS_TABLE_COLUMNS: tuple[str, ...] = (
    "overall_rank",
    "player",
    "position",
    "nfl_team",
    "asset_type",
    "asset_lifecycle_label",
    "stats_model_value",
    "market_value",
    "market_edge",
    "confidence",
    "confidence_label",
    "warning",
    "why_available",
)


@dataclass(frozen=True)
class DraftUXContract:
    snapshot_date: str | None
    page_rows: list[dict[str, object]]
    workflow_rows: list[dict[str, object]]
    available_pool_rows: list[dict[str, object]]
    available_pool_source_rows: list[dict[str, object]]
    available_pool_warnings: list[str]
    pick_grid_rows: list[dict[str, object]]
    mock_state_rows: list[dict[str, object]]
    my_pick_rows: list[dict[str, object]]
    best_option_rows: list[dict[str, object]]
    issues: list[str]


@dataclass(frozen=True)
class DraftRankingsTable:
    rows: list[dict[str, object]]
    column_labels: dict[str, str]
    default_sort: str
    default_sort_direction: str
    review_only: bool


def build_draft_ux_contract(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
) -> DraftUXContract:
    draft_room = build_draft_room(data_pack_path, team_id=team_id)
    return DraftUXContract(
        snapshot_date=draft_room.snapshot_date,
        page_rows=_page_rows(),
        workflow_rows=_workflow_rows(),
        available_pool_rows=_available_pool_rows(draft_room),
        available_pool_source_rows=draft_room.available_pool_source_rows,
        available_pool_warnings=draft_room.available_pool_warnings,
        pick_grid_rows=_pick_grid_rows(draft_room),
        mock_state_rows=_mock_state_rows(),
        my_pick_rows=_my_pick_contract_rows(draft_room),
        best_option_rows=_best_option_contract_rows(draft_room),
        issues=_issues(draft_room),
    )


def build_rankings_table(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
    drafted_asset_ids: set[str] | None = None,
    review_only: bool = False,
) -> DraftRankingsTable:
    board = build_draft_room(data_pack_path, team_id=team_id)
    rows = _ranking_rows(
        board.combined_rows,
        drafted_asset_ids=drafted_asset_ids or set(),
        review_only=review_only,
    )
    return DraftRankingsTable(
        rows=rows,
        column_labels=RANKINGS_COLUMN_LABELS,
        default_sort="stats_model_value",
        default_sort_direction="desc",
        review_only=review_only,
    )


def filter_rankings_rows(
    rows: list[dict[str, object]],
    *,
    positions: set[str] | None = None,
    asset_types: set[str] | None = None,
    lifecycles: set[str] | None = None,
    statuses: set[str] | None = None,
    warnings: set[str] | None = None,
    min_confidence: float | None = None,
    search: str = "",
) -> list[dict[str, object]]:
    search_value = search.strip().lower()
    filtered: list[dict[str, object]] = []
    for row in rows:
        if positions and str(row["position"]) not in positions:
            continue
        if asset_types and str(row["asset_type"]) not in asset_types:
            continue
        if lifecycles and str(row["asset_lifecycle_label"]) not in lifecycles:
            continue
        if statuses and str(row["draft_status"]) not in statuses:
            continue
        if warnings and str(row["warning"]) not in warnings:
            continue
        if min_confidence is not None and float(row["confidence"]) < min_confidence:
            continue
        if search_value and search_value not in str(row["player"]).lower():
            continue
        filtered.append(row)
    return filtered


def draft_ux_summary_row(contract: DraftUXContract) -> dict[str, object]:
    total_available = sum(int(row["count"]) for row in contract.available_pool_rows)
    missing_required_sources = [
        row
        for row in contract.available_pool_source_rows
        if row["required"] and row["status"] != "loaded"
    ]
    only_released_veterans_missing = (
        bool(missing_required_sources)
        and all(row["source"] == "released veterans" for row in missing_required_sources)
        and not contract.issues
    )
    needs_data = bool(
        contract.issues
        or contract.available_pool_warnings
        or missing_required_sources
    )
    return {
        "snapshot": contract.snapshot_date or "unknown",
        "visible_pages": "Rankings|Draft Board",
        "draft_shape": f"{DRAFT_ROUNDS} rounds x {DRAFT_TEAMS} teams",
        "total_picks": DRAFT_TOTAL_PICKS,
        "available_pool_rows": total_available,
        "pool_warnings": len(contract.available_pool_warnings),
        "required_sources_ready": (
            len([row for row in contract.available_pool_source_rows if row["required"]])
            - len(missing_required_sources)
        ),
        "required_sources_total": len(
            [row for row in contract.available_pool_source_rows if row["required"]]
        ),
        "my_pick_count": len(contract.my_pick_rows),
        "status": "needs_data" if needs_data else "contract_ready",
        "next_phase": (
            "Import official released veterans when declarations are available; "
            "pre-declaration roster review can continue without them."
            if only_released_veterans_missing
            else (
            "Load the full rookie and available-veteran pool before draft use."
            if needs_data
            else "Draft rankings and board state are ready for mock use."
            )
        ),
    }


def _ranking_rows(
    combined_rows: list[dict[str, object]],
    *,
    drafted_asset_ids: set[str],
    review_only: bool,
) -> list[dict[str, object]]:
    sorted_rows = sorted(
        combined_rows,
        key=lambda row: (
            str(row.get("asset_id") or "") in drafted_asset_ids,
            -float(row.get("draft_value") or 0),
            -float(row.get("confidence") or 0),
            str(row.get("player") or ""),
        ),
    )
    rows: list[dict[str, object]] = []
    for rank, row in enumerate(sorted_rows, start=1):
        asset_id = str(row.get("asset_id") or "")
        draft_status = "drafted" if asset_id in drafted_asset_ids else "available"
        confidence = float(row.get("confidence") or 0)
        warning = _ranking_warning(
            confidence=confidence,
            review_only=review_only,
            draft_status=draft_status,
        )
        rows.append(
            {
                "overall_rank": rank,
                "asset_id": asset_id,
                "player": row.get("player") or "",
                "position": row.get("position") or "",
                "nfl_team": row.get("team") or "",
                "asset_type": row.get("asset_type_label")
                or _asset_type_label(row.get("asset_type")),
                "asset_lifecycle": row.get("asset_lifecycle")
                or asset_lifecycle_for_row(row),
                "asset_lifecycle_label": row.get("asset_lifecycle_label")
                or asset_lifecycle_label(asset_lifecycle_for_row(row)),
                "draft_status": draft_status,
                "drafted_pick": "",
                "drafted_owner": "",
                "why_available": row.get("why_available") or "",
                "stats_model_value": round(float(row.get("model_value") or 0), 2),
                "market_value": round(float(row.get("market_value") or 0), 2),
                "draft_value": round(float(row.get("draft_value") or 0), 2),
                "market_edge": round(float(row.get("market_edge") or 0), 2),
                "confidence": round(confidence, 2),
                "confidence_label": confidence_label(confidence),
                "confidence_explanation": confidence_explanation(confidence, warning),
                "warning": warning,
                "source": row.get("source") or "",
                "recommendation": row.get("recommendation") or "",
                "recommended_range": row.get("recommended_range") or "",
                "do_not_draft_before_pick": row.get("do_not_draft_before_pick") or "",
            }
        )
    return rows


def _asset_type_label(raw: object) -> str:
    labels = {
        "rookie": "Rookie",
        "released_veteran": "Released Veteran",
        "free_agent": "Free Agent",
    }
    return labels.get(str(raw or ""), str(raw or "Unknown").replace("_", " ").title())


def _ranking_warning(*, confidence: float, review_only: bool, draft_status: str) -> str:
    if draft_status == "drafted":
        return "Already drafted in this mock"
    if review_only:
        return "Review-only: calibration not passed"
    if confidence < 60:
        return "Low confidence"
    if confidence < 75:
        return "Review confidence"
    return ""


def _page_rows() -> list[dict[str, object]]:
    return [
        {
            "page": "Rankings",
            "route": "rankings",
            "purpose": "Fast draftable-player list.",
            "first_view": "One ranked table plus simple filters.",
            "must_not_show": "Old mixed-board audit tabs by default.",
        },
        {
            "page": "Draft Board",
            "route": "draft-board",
            "purpose": "Live/mock pick tracker.",
            "first_view": "Pick grid, current pick, and best available at my pick.",
            "must_not_show": "Raw source/debug tables by default.",
        },
    ]


def _workflow_rows() -> list[dict[str, object]]:
    return [
        {
            "step": 1,
            "action": "Open Rankings",
            "goal": "Check the available pool before or during a mock.",
        },
        {
            "step": 2,
            "action": "Open Draft Board",
            "goal": "Track picks as players come off the board.",
        },
        {
            "step": 3,
            "action": "When my pick is current",
            "goal": "Show best remaining options ranked for that exact pick.",
        },
        {
            "step": 4,
            "action": "Mock, undo, reset, save",
            "goal": "Practice scenarios without mutating source data.",
        },
    ]


def _available_pool_rows(board: DraftRoomBoard) -> list[dict[str, object]]:
    rows = [
        {
            "pool": "rookies",
            "count": len(board.rookie_rows),
            "source": "rookie model outputs or unified asset board",
            "phase": "Rankings Phase 2",
        },
        {
            "pool": "released veterans/free agents",
            "count": len(board.released_veteran_rows),
            "source": "actual available veteran/free-agent rows",
            "phase": "Available Pool Phase 7",
        },
        {
            "pool": "manual draftables",
            "count": len(board.manual_draftable_rows),
            "source": "fact_manual_draftables.csv if present",
            "phase": "Available Pool Phase 7",
        },
        {
            "pool": "combined available board",
            "count": len(board.combined_rows),
            "source": "rookies plus actually available veterans/free agents/manual rows",
            "phase": "Draft Board Phase 5",
        },
    ]
    return rows


def _pick_grid_rows(board: DraftRoomBoard) -> list[dict[str, object]]:
    pick_lookup = {
        int(row["overall_pick"]): row
        for row in board.pick_rows
        if row.get("overall_pick") not in (None, "")
    }
    rows: list[dict[str, object]] = []
    for overall_pick in range(1, DRAFT_TOTAL_PICKS + 1):
        pick = pick_lookup.get(overall_pick, {})
        round_number = ((overall_pick - 1) // DRAFT_TEAMS) + 1
        round_pick = ((overall_pick - 1) % DRAFT_TEAMS) + 1
        rows.append(
            {
                "overall_pick": overall_pick,
                "round": round_number,
                "round_pick": round_pick,
                "pick_label": pick.get("pick") or f"{round_number}.{round_pick:02d}",
                "current_owner": pick.get("current_team", ""),
                "original_owner": pick.get("original_team", ""),
                "is_my_pick": pick in board.my_pick_rows,
                "drafted_player": "",
                "drafted_position": "",
            }
        )
    return rows


def _mock_state_rows() -> list[dict[str, object]]:
    return [
        {
            "state_piece": "drafted picks",
            "phase": "Draft UX Phase 3",
            "storage": "Streamlit session state first; JSON export later.",
            "mutation_policy": "Never writes to data packs.",
        },
        {
            "state_piece": "available pool",
            "phase": "Draft UX Phase 3",
            "storage": "Derived from rankings minus drafted players.",
            "mutation_policy": "Recomputed after each pick.",
        },
        {
            "state_piece": "mock files",
            "phase": "Draft UX Phase 6",
            "storage": "local_exports/mock_drafts",
            "mutation_policy": "User-created mock artifacts only.",
        },
    ]


def _my_pick_contract_rows(board: DraftRoomBoard) -> list[dict[str, object]]:
    return [
        {
            "pick": row.get("pick"),
            "overall_pick": row.get("overall_pick"),
            "current_team": row.get("current_team"),
            "certainty": row.get("certainty"),
            "my_pick_detection": "current_team matches configured LVE team id/name",
        }
        for row in board.my_pick_rows
    ]


def _best_option_contract_rows(board: DraftRoomBoard) -> list[dict[str, object]]:
    if board.best_available_rows:
        return [
            {
                "pick": row.get("pick"),
                "player": row.get("player"),
                "position": row.get("position"),
                "asset_type": row.get("asset_type"),
                "draft_value": row.get("draft_value"),
                "reach_label": row.get("reach_label"),
                "logic": "available pool sorted by draft value after drafted players are removed",
            }
            for row in board.best_available_rows[:10]
        ]
    return [
        {
            "pick": "",
            "player": "",
            "position": "",
            "asset_type": "",
            "draft_value": "",
            "reach_label": "",
            "logic": "needs my current-year picks and non-empty available pool",
        }
    ]


def _issues(board: DraftRoomBoard) -> list[str]:
    issues: list[str] = []
    if not board.my_pick_rows:
        issues.append("No Niners picks were detected for the active draft board.")
    if not board.combined_rows:
        issues.append("No combined rookie/veteran available pool rows were detected.")
    return issues
