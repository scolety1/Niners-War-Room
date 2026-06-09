from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.asset_board_service import build_unified_asset_board
from src.services.forced_release_strategy_service import build_forced_release_strategy
from src.services.player_lifecycle_service import add_lifecycle_fields
from src.services.table_sort_service import SortSpec

DRAFT_PICK_SORT = SortSpec(
    table_key="draft_picks",
    label="Current team, pick year, then overall pick",
    sort_columns=("current_team", "pick_year", "overall_pick"),
    directions=("asc", "asc", "asc"),
    meaning="Picks are grouped by current owner and then ordered by draft slot.",
)
DRAFT_TEAM_TOTAL_SORT = SortSpec(
    table_key="draft_team_totals",
    label="Snapshot pick value descending, then team",
    sort_columns=("snapshot_value", "team"),
    directions=("desc", "asc"),
    meaning="Teams with the most current pick value appear first.",
)
DRAFT_ASSET_SORT = SortSpec(
    table_key="draft_assets",
    label="Acquisition value descending, then all-asset value",
    sort_columns=("acquisition_value", "all_asset_value", "asset_id"),
    directions=("desc", "desc", "asc"),
    meaning="The unified asset board shows highest acquisition value first.",
)
DRAFT_RELEASE_TARGET_SORT = SortSpec(
    table_key="draft_release_targets",
    label="Reacquisition or opponent target priority descending",
    sort_columns=("reacquisition_priority", "opponent_release_target_score", "player"),
    directions=("desc", "desc", "asc"),
    meaning="Forced-release draft targets with the highest priority appear first.",
)
DRAFT_ROOKIE_SORT = SortSpec(
    table_key="draft_rookies",
    label="Draft value descending, then player",
    sort_columns=("draft_value", "player"),
    directions=("desc", "asc"),
    meaning="Rookies are ordered by their rookie model draft value.",
)
DRAFT_AVAILABLE_VETERAN_SORT = SortSpec(
    table_key="draft_available_veterans",
    label="Draft value descending, then availability",
    sort_columns=("draft_value", "availability", "player"),
    directions=("desc", "asc", "asc"),
    meaning="Only actually available released veterans and free agents appear here.",
)
DRAFT_COMBINED_SORT = SortSpec(
    table_key="draft_combined",
    label="Draft value descending, then confidence",
    sort_columns=("draft_value", "confidence", "player"),
    directions=("desc", "desc", "asc"),
    meaning="The mixed offline board ranks rookies against available veterans and free agents.",
)
DRAFT_BEST_AVAILABLE_SORT = SortSpec(
    table_key="draft_best_available",
    label="Pick, then reach label, then draft value",
    sort_columns=("overall_pick", "reach_rank", "draft_value", "player"),
    directions=("asc", "asc", "desc", "asc"),
    meaning=(
        "Each pick shows the best currently available assets and whether they "
        "are value, fair, reach, or avoid."
    ),
)
DRAFT_ROOKIE_VETERAN_COMPARISON_SORT = SortSpec(
    table_key="draft_rookie_veteran_comparisons",
    label="Rookie value descending",
    sort_columns=("rookie_value", "value_gap", "rookie"),
    directions=("desc", "desc", "asc"),
    meaning="Top rookies are compared against nearby available veteran alternatives.",
)


@dataclass(frozen=True)
class DraftRoomBoard:
    snapshot_date: str | None
    pick_rows: list[dict[str, object]]
    my_pick_rows: list[dict[str, object]]
    team_rows: list[dict[str, object]]
    asset_rows: list[dict[str, object]]
    rookie_rows: list[dict[str, object]]
    released_veteran_rows: list[dict[str, object]]
    manual_draftable_rows: list[dict[str, object]]
    available_pool_source_rows: list[dict[str, object]]
    combined_rows: list[dict[str, object]]
    best_available_rows: list[dict[str, object]]
    rookie_veteran_comparison_rows: list[dict[str, object]]
    release_target_rows: list[dict[str, object]]
    available_pool_warnings: list[str]
    teams: list[str]
    certainties: list[str]
    asset_types: list[str]
    positions: list[str]
    asset_recommendations: list[str]
    reach_labels: list[str]
    sort_metadata: dict[str, SortSpec]


def build_draft_room(
    data_pack_path: str | Path,
    *,
    rookie_model_dir: str | Path | None = None,
    rookie_output_path: str | Path | None = None,
    team_id: str = "niners",
) -> DraftRoomBoard:
    validated = validate_data_pack(data_pack_path)
    asset_board = build_unified_asset_board(
        data_pack_path,
        rookie_model_dir=rookie_model_dir,
    )
    release_strategy = build_forced_release_strategy(data_pack_path)
    pick_values = _pick_values_by_key(validated.rows_by_table.get("pick_values", []))
    pick_rows = sorted(
        [
            _draft_pick_row(row, pick_values)
            for row in validated.rows_by_table.get("future_picks", [])
        ],
        key=lambda row: (
            str(row["current_team"]),
            int(row["pick_year"]),
            int(row["overall_pick"] or 999),
        ),
    )
    my_pick_rows = _my_pick_rows(pick_rows, validated.rows_by_table, team_id)
    protected_player_ids = _protected_player_ids(validated.rows_by_table.get("rosters", []))
    rookie_rows = _draft_rookie_rows(
        data_pack_path,
        asset_board.rows,
        rookie_output_path=rookie_output_path,
        protected_player_ids=protected_player_ids,
    )
    released_veteran_rows = _available_veteran_rows(
        data_pack_path,
        asset_board.rows,
        protected_player_ids=protected_player_ids,
    )
    manual_draftable_rows = _manual_draftable_rows(
        data_pack_path,
        protected_player_ids=protected_player_ids,
    )
    combined_rows = _combined_rows(
        rookie_rows,
        released_veteran_rows,
        manual_draftable_rows,
    )
    best_available_rows = _best_available_by_pick(my_pick_rows, combined_rows)
    rookie_veteran_comparison_rows = _rookie_veteran_comparisons(
        rookie_rows,
        released_veteran_rows,
    )
    return DraftRoomBoard(
        snapshot_date=validated.snapshot_date,
        pick_rows=pick_rows,
        my_pick_rows=my_pick_rows,
        team_rows=_team_rows(pick_rows),
        asset_rows=asset_board.rows,
        rookie_rows=rookie_rows,
        released_veteran_rows=released_veteran_rows,
        manual_draftable_rows=manual_draftable_rows,
        available_pool_source_rows=_available_pool_source_rows(
            data_pack_path,
            rookie_rows=rookie_rows,
            released_veteran_rows=released_veteran_rows,
            manual_draftable_rows=manual_draftable_rows,
        ),
        combined_rows=combined_rows,
        best_available_rows=best_available_rows,
        rookie_veteran_comparison_rows=rookie_veteran_comparison_rows,
        release_target_rows=release_strategy.draft_target_rows,
        available_pool_warnings=_available_pool_warnings(
            rookie_rows=rookie_rows,
            released_veteran_rows=released_veteran_rows,
            manual_draftable_rows=manual_draftable_rows,
        ),
        teams=sorted({str(row["current_team"]) for row in pick_rows if row["current_team"]}),
        certainties=sorted({str(row["certainty"]) for row in pick_rows if row["certainty"]}),
        asset_types=asset_board.asset_types,
        positions=asset_board.positions,
        asset_recommendations=asset_board.recommendations,
        reach_labels=_ordered_reach_labels(
            {str(row["reach_label"]) for row in best_available_rows}
        ),
        sort_metadata={
            "pick_rows": DRAFT_PICK_SORT,
            "my_pick_rows": DRAFT_PICK_SORT,
            "team_rows": DRAFT_TEAM_TOTAL_SORT,
            "asset_rows": DRAFT_ASSET_SORT,
            "rookie_rows": DRAFT_ROOKIE_SORT,
            "released_veteran_rows": DRAFT_AVAILABLE_VETERAN_SORT,
            "combined_rows": DRAFT_COMBINED_SORT,
            "best_available_rows": DRAFT_BEST_AVAILABLE_SORT,
            "rookie_veteran_comparison_rows": DRAFT_ROOKIE_VETERAN_COMPARISON_SORT,
            "release_target_rows": DRAFT_RELEASE_TARGET_SORT,
        },
    )


def _pick_values_by_key(
    rows: list[dict[str, object]],
) -> dict[tuple[int, str], dict[str, object]]:
    return {
        (int(row["pick_year"]), str(row["pick_label"])): row
        for row in rows
        if row.get("pick_year") is not None and row.get("pick_label")
    }


def _draft_pick_row(
    row: dict[str, object],
    pick_values: dict[tuple[int, str], dict[str, object]],
) -> dict[str, object]:
    pick_year = int(row["pick_year"])
    pick_label = str(row["pick_label"])
    value_row = pick_values.get((pick_year, pick_label), {})
    final_value = _optional_float(value_row.get("final_pick_value"))
    base_value = _optional_float(value_row.get("base_value_1000"))
    return {
        "pick": pick_label,
        "current_team": row.get("current_team_name") or row.get("current_team_id"),
        "original_team": row.get("original_team_name") or row.get("original_team_id"),
        "pick_year": pick_year,
        "round": row.get("round"),
        "overall_pick": row.get("overall_pick") or value_row.get("overall_pick"),
        "certainty": row.get("certainty") or "unknown",
        "base_value": base_value,
        "snapshot_value": final_value,
        "future_discount": _optional_float(value_row.get("future_discount")),
        "certainty_factor": _optional_float(value_row.get("certainty_adjustment")),
        "bucket": value_row.get("bucket"),
    }


def _team_rows(pick_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows_by_team: dict[str, list[dict[str, object]]] = {}
    for row in pick_rows:
        rows_by_team.setdefault(str(row["current_team"]), []).append(row)

    team_rows: list[dict[str, object]] = []
    for team, rows in rows_by_team.items():
        valued_rows = [row for row in rows if row["snapshot_value"] is not None]
        team_rows.append(
            {
                "team": team,
                "picks": len(rows),
                "snapshot_value": round(
                    sum(float(row["snapshot_value"]) for row in valued_rows),
                    1,
                ),
                "highest_pick": _highest_pick_label(rows),
            }
        )
    return sorted(
        team_rows,
        key=lambda row: (-float(row["snapshot_value"]), str(row["team"])),
    )


def _highest_pick_label(rows: list[dict[str, object]]) -> str | None:
    ordered = sorted(rows, key=lambda row: int(row["overall_pick"] or 999))
    if not ordered:
        return None
    return str(ordered[0]["pick"])


def _my_pick_rows(
    pick_rows: list[dict[str, object]],
    rows_by_table: dict[str, list[dict[str, object]]],
    team_id: str,
) -> list[dict[str, object]]:
    resolved_team = _resolve_team_name(rows_by_table, team_id)
    rows = [
        row
        for row in pick_rows
        if _same_team(str(row.get("current_team") or ""), team_id, resolved_team)
    ]
    return rows or [
        row
        for row in pick_rows
        if _same_team(str(row.get("current_team") or ""), team_id, None)
    ]


def _draft_rookie_rows(
    data_pack_path: str | Path,
    asset_rows: list[dict[str, object]],
    *,
    rookie_output_path: str | Path | None,
    protected_player_ids: set[str],
) -> list[dict[str, object]]:
    _ = asset_rows
    _ = rookie_output_path
    explicit_path = Path(data_pack_path) / "fact_rookie_draftables.csv"
    if explicit_path.exists():
        return _rookie_rows_from_csv(
            explicit_path,
            protected_player_ids=protected_player_ids,
        )
    return []


def _available_veteran_rows(
    data_pack_path: str | Path,
    asset_rows: list[dict[str, object]],
    *,
    protected_player_ids: set[str],
) -> list[dict[str, object]]:
    _ = asset_rows
    explicit_path = Path(data_pack_path) / "fact_available_veterans.csv"
    rows = (
        _available_veteran_rows_from_csv(
            explicit_path,
            protected_player_ids=protected_player_ids,
        )
        if explicit_path.exists()
        else []
    )
    return sorted(
        rows,
        key=lambda row: (
            -float(row["draft_value"]),
            str(row["availability"]),
            str(row["player"]),
        ),
    )


def _combined_rows(
    rookie_rows: list[dict[str, object]],
    released_veteran_rows: list[dict[str, object]],
    manual_draftable_rows: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    rows = sorted(
        [*rookie_rows, *released_veteran_rows, *(manual_draftable_rows or [])],
        key=lambda row: (-float(row["draft_value"]), -float(row["confidence"]), str(row["player"])),
    )
    return [
        {
            **row,
            "draft_rank": rank,
        }
        for rank, row in enumerate(rows, start=1)
    ]


def _best_available_by_pick(
    my_pick_rows: list[dict[str, object]],
    combined_rows: list[dict[str, object]],
    *,
    candidates_per_pick: int = 10,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current_year = min((int(row["pick_year"]) for row in my_pick_rows), default=None)
    for pick in my_pick_rows:
        if current_year is not None and int(pick["pick_year"]) != current_year:
            continue
        pick_value = _pick_value_100(pick.get("snapshot_value"))
        overall_pick = int(pick.get("overall_pick") or 999)
        for asset in combined_rows[:candidates_per_pick]:
            draft_value = float(asset["draft_value"])
            value_gap = round(draft_value - pick_value, 2)
            reach_label = _reach_label(
                value_gap=value_gap,
                overall_pick=overall_pick,
                earliest_pick=asset.get("do_not_draft_before_pick"),
            )
            rows.append(
                {
                    "pick": pick["pick"],
                    "overall_pick": overall_pick,
                    "pick_value": pick_value,
                    "asset_type": asset["asset_type"],
                    "player": asset["player"],
                    "position": asset["position"],
                    "availability": asset["availability"],
                    "draft_value": draft_value,
                    "value_gap": value_gap,
                    "reach_label": reach_label,
                    "reach_rank": _reach_rank(reach_label),
                    "compare_note": _pick_compare_note(reach_label, value_gap),
                    "recommended_range": asset.get("recommended_range"),
                    "do_not_draft_before_pick": asset.get("do_not_draft_before_pick"),
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            int(row["overall_pick"]),
            int(row["reach_rank"]),
            -float(row["draft_value"]),
            str(row["player"]),
        ),
    )


def _rookie_veteran_comparisons(
    rookie_rows: list[dict[str, object]],
    released_veteran_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rookie in rookie_rows[:20]:
        veteran = _best_veteran_alternative(rookie, released_veteran_rows)
        if veteran is None:
            continue
        gap = round(float(rookie["draft_value"]) - float(veteran["draft_value"]), 2)
        preferred = str(rookie["player"]) if gap >= 0 else str(veteran["player"])
        rows.append(
            {
                "rookie": rookie["player"],
                "position": rookie["position"],
                "rookie_value": rookie["draft_value"],
                "veteran": veteran["player"],
                "veteran_type": veteran["availability"],
                "veteran_value": veteran["draft_value"],
                "value_gap": gap,
                "preferred": preferred,
                "comparison": _rookie_veteran_note(gap),
            }
        )
    return sorted(rows, key=lambda row: (-float(row["rookie_value"]), -float(row["value_gap"])))


def _draft_asset_row(
    row: dict[str, object],
    *,
    availability: str,
    asset_type_label: str,
    why_available: str,
) -> dict[str, object]:
    model_value = _first_float(
        row.get("all_asset_value"),
        row.get("acquisition_value"),
        row.get("keeper_adjusted_value"),
    )
    market_value = _first_float(row.get("trade_liquidity_value"), row.get("market_value"))
    draft_value = _first_float(row.get("acquisition_value"), model_value)
    return {
        "asset_id": row.get("asset_id"),
        "asset_type": row.get("asset_type"),
        "asset_type_label": asset_type_label,
        "player": row.get("player"),
        "position": row.get("position"),
        "team": row.get("team"),
        "availability": availability,
        "why_available": why_available,
        "draft_value": round(draft_value, 2),
        "model_value": round(model_value, 2),
        "market_value": round(market_value, 2),
        "market_edge": round(model_value - market_value, 2),
        "confidence": _first_float(row.get("confidence")),
        "pick_equivalent": row.get("pick_equivalent"),
        "recommendation": row.get("recommendation"),
        "recommended_range": row.get("recommended_range"),
        "do_not_draft_before_pick": row.get("do_not_draft_before_pick"),
        "source": row.get("source"),
    }


def _rookie_rows_from_output(rookie_output_path: str | Path | None) -> list[dict[str, object]]:
    path = _existing_rookie_output_path(rookie_output_path)
    if path is None:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            final_score = _first_float(raw.get("final_decision_score"))
            trade_score = _first_float(raw.get("trade_insulation_score"), final_score)
            rows.append(
                add_lifecycle_fields({
                    "asset_id": f"rookie:{raw.get('player_id')}",
                    "asset_type": "rookie",
                    "asset_type_label": "rookie",
                    "player": raw.get("player_name"),
                    "position": raw.get("position"),
                    "team": "Rookie Pool",
                    "availability": "rookie_pool",
                    "why_available": "Rookie pool entrant.",
                    "draft_value": round(final_score, 2),
                    "model_value": round(final_score, 2),
                    "market_value": round(trade_score, 2),
                    "market_edge": round(final_score - trade_score, 2),
                    "confidence": _first_float(raw.get("confidence_score")),
                    "pick_equivalent": raw.get("recommended_range_label")
                    or raw.get("pick_equivalent"),
                    "recommendation": "rookie_target" if final_score >= 74 else "rookie_stash",
                    "recommended_range": raw.get("recommended_range_label"),
                    "do_not_draft_before_pick": _optional_int(
                        raw.get("do_not_draft_before_pick")
                    ),
                    "source": str(path),
                })
            )
    return rows


def _rookie_rows_from_csv(
    path: Path,
    *,
    protected_player_ids: set[str],
) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            player_id = str(raw.get("player_id") or "").strip()
            if player_id in protected_player_ids:
                continue
            draft_value = _first_float(
                raw.get("draft_value"),
                raw.get("stats_model_value"),
                raw.get("model_value"),
            )
            market_value = _first_float(raw.get("market_value"), draft_value)
            rows.append(
                add_lifecycle_fields({
                    "asset_id": f"rookie:{player_id or raw.get('player_name')}",
                    "asset_type": "rookie",
                    "asset_type_label": "rookie",
                    "player": raw.get("player_name") or player_id,
                    "position": raw.get("position") or "",
                    "team": raw.get("nfl_team") or raw.get("team") or "Rookie Pool",
                    "availability": "rookie_pool",
                    "why_available": raw.get("why_available")
                    or "Current-year rookie pool entrant.",
                    "draft_value": round(draft_value, 2),
                    "model_value": round(draft_value, 2),
                    "market_value": round(market_value, 2),
                    "market_edge": round(draft_value - market_value, 2),
                    "confidence": _first_float(raw.get("confidence"), 50.0),
                    "pick_equivalent": raw.get("pick_equivalent"),
                    "recommendation": raw.get("recommendation") or "rookie_target",
                    "recommended_range": raw.get("recommended_range"),
                    "do_not_draft_before_pick": _optional_int(
                        raw.get("do_not_draft_before_pick")
                    ),
                    "source": str(path),
                })
            )
    return sorted(rows, key=lambda row: (-float(row["draft_value"]), str(row["player"])))


def _available_veteran_rows_from_csv(
    path: Path,
    *,
    protected_player_ids: set[str],
) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            player_id = str(raw.get("player_id") or "").strip()
            if player_id in protected_player_ids:
                continue
            asset_type = str(raw.get("asset_type") or "").strip().lower()
            if asset_type not in {"released_veteran", "free_agent"}:
                continue
            draft_value = _first_float(
                raw.get("draft_value"),
                raw.get("stats_model_value"),
                raw.get("model_value"),
            )
            market_value = _first_float(raw.get("market_value"), draft_value)
            rows.append(
                add_lifecycle_fields({
                    "asset_id": f"{asset_type}:{player_id or raw.get('player_name')}",
                    "asset_type": asset_type,
                    "asset_type_label": _asset_type_label(asset_type),
                    "player": raw.get("player_name") or player_id,
                    "position": raw.get("position") or "",
                    "team": raw.get("nfl_team") or raw.get("team") or "Available",
                    "availability": asset_type,
                    "why_available": raw.get("why_available") or _why_available(asset_type),
                    "draft_value": round(draft_value, 2),
                    "model_value": round(draft_value, 2),
                    "market_value": round(market_value, 2),
                    "market_edge": round(draft_value - market_value, 2),
                    "confidence": _first_float(raw.get("confidence"), 50.0),
                    "pick_equivalent": raw.get("pick_equivalent"),
                    "recommendation": raw.get("recommendation") or "available_veteran",
                    "recommended_range": raw.get("recommended_range"),
                    "do_not_draft_before_pick": _optional_int(
                        raw.get("do_not_draft_before_pick")
                    ),
                    "source": str(path),
                })
            )
    return sorted(rows, key=lambda row: (-float(row["draft_value"]), str(row["player"])))


def _manual_draftable_rows(
    data_pack_path: str | Path,
    *,
    protected_player_ids: set[str],
) -> list[dict[str, object]]:
    path = Path(data_pack_path) / "fact_manual_draftables.csv"
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            player_id = str(raw.get("player_id") or "").strip()
            manual_status = str(raw.get("manual_status") or "").strip().lower()
            if player_id in protected_player_ids and manual_status != "include":
                continue
            draft_value = _first_float(
                raw.get("draft_value"),
                raw.get("stats_model_value"),
                raw.get("model_value"),
            )
            market_value = _first_float(raw.get("market_value"), draft_value)
            rows.append(
                add_lifecycle_fields({
                    "asset_id": f"manual:{player_id or raw.get('player_name')}",
                    "asset_type": "manual",
                    "asset_type_label": "manual",
                    "asset_lifecycle": raw.get("asset_lifecycle") or "free_agent",
                    "player": raw.get("player_name") or player_id,
                    "position": raw.get("position") or "",
                    "team": raw.get("nfl_team") or raw.get("team") or "Manual",
                    "availability": "manual",
                    "why_available": raw.get("why_available")
                    or "Manually added as draftable.",
                    "draft_value": round(draft_value, 2),
                    "model_value": round(draft_value, 2),
                    "market_value": round(market_value, 2),
                    "market_edge": round(draft_value - market_value, 2),
                    "confidence": _first_float(raw.get("confidence"), 50.0),
                    "pick_equivalent": raw.get("pick_equivalent"),
                    "recommendation": raw.get("recommendation") or "manual_review",
                    "recommended_range": raw.get("recommended_range"),
                    "do_not_draft_before_pick": _optional_int(
                        raw.get("do_not_draft_before_pick")
                    ),
                    "source": str(path),
                })
            )
    return sorted(rows, key=lambda row: (-float(row["draft_value"]), str(row["player"])))


def _available_pool_source_rows(
    data_pack_path: str | Path,
    *,
    rookie_rows: list[dict[str, object]],
    released_veteran_rows: list[dict[str, object]],
    manual_draftable_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    root = Path(data_pack_path)
    rookie_explicit = root / "fact_rookie_draftables.csv"
    veteran_explicit = root / "fact_available_veterans.csv"
    manual_explicit = root / "fact_manual_draftables.csv"
    released_count = sum(
        1 for row in released_veteran_rows if row.get("asset_type") == "released_veteran"
    )
    free_agent_count = sum(
        1 for row in released_veteran_rows if row.get("asset_type") == "free_agent"
    )
    return [
        _pool_source_row(
            source="rookies",
            file_name=rookie_explicit.name,
            loaded=bool(rookie_rows),
            count=len(rookie_rows),
            required=True,
            review_only=_looks_like_fixture_rookie_pool(rookie_rows),
            file_exists=rookie_explicit.exists(),
        ),
        _pool_source_row(
            source="released veterans",
            file_name=veteran_explicit.name,
            loaded=released_count > 0,
            count=released_count,
            required=True,
            review_only=False,
            file_exists=veteran_explicit.exists(),
        ),
        _pool_source_row(
            source="free agents",
            file_name=veteran_explicit.name,
            loaded=free_agent_count > 0,
            count=free_agent_count,
            required=True,
            review_only=False,
            file_exists=veteran_explicit.exists(),
        ),
        _pool_source_row(
            source="manual draftables",
            file_name=manual_explicit.name,
            loaded=bool(manual_draftable_rows),
            count=len(manual_draftable_rows),
            required=False,
            review_only=False,
            file_exists=manual_explicit.exists(),
        ),
    ]


def _pool_source_row(
    *,
    source: str,
    file_name: str,
    loaded: bool,
    count: int,
    required: bool,
    review_only: bool,
    file_exists: bool,
) -> dict[str, object]:
    if loaded and review_only:
        status = "review_only_fixture"
    elif loaded:
        status = "loaded"
    elif required:
        status = "missing_required"
    else:
        status = "optional_missing"
    return {
        "source": source,
        "status": status,
        "count": count,
        "required": required,
        "file_name": file_name,
        "file_exists": file_exists,
        "review_only": review_only,
    }


def _protected_player_ids(roster_rows: list[dict[str, object]]) -> set[str]:
    protected_statuses = {"", "rostered", "protected", "keeper", "active"}
    return {
        str(row.get("player_id") or "")
        for row in roster_rows
        if str(row.get("roster_status") or "").strip().lower() in protected_statuses
    }


def _available_pool_warnings(
    *,
    rookie_rows: list[dict[str, object]],
    released_veteran_rows: list[dict[str, object]],
    manual_draftable_rows: list[dict[str, object]],
) -> list[str]:
    warnings: list[str] = []
    if not rookie_rows:
        warnings.append("Review needed: no rookies are loaded into the draft pool.")
    elif _looks_like_fixture_rookie_pool(rookie_rows):
        warnings.append(
            "Review needed: rookie pool appears to be fixture/demo data, not a full "
            "current-year rookie board."
        )
    released_count = sum(
        1 for row in released_veteran_rows if row.get("asset_type") == "released_veteran"
    )
    free_agent_count = sum(
        1 for row in released_veteran_rows if row.get("asset_type") == "free_agent"
    )
    if released_count == 0:
        warnings.append(
            "Draft warning: no released veterans are loaded yet. This does not block "
            "pre-declaration drop/shop review, but the mixed offline draft pool is "
            "incomplete until actual declared releases are imported."
        )
    if free_agent_count == 0:
        warnings.append(
            "Review needed: no free agents are loaded. Add the actual available free-agent "
            "pool before using the offline draft pool."
        )
    return warnings


def _looks_like_fixture_rookie_pool(rookie_rows: list[dict[str, object]]) -> bool:
    fixture_markers = (
        "Elite WR Profile",
        "High Capital Three-Down RB",
        "Elite Rushing QB",
        "Elite TE Exception",
        "Rookie Beats Veteran",
        "Good Pocket QB",
        "Rookie Loses To Veteran",
        "Satellite Receiving RB",
        "Older Raw WR",
        "Day 3 TE Suppressed",
    )
    names = {str(row.get("player") or "") for row in rookie_rows}
    return len(names.intersection(fixture_markers)) >= max(3, len(rookie_rows) // 2)


def _asset_type_label(value: object) -> str:
    labels = {
        "rookie": "rookie",
        "released_veteran": "released veteran",
        "free_agent": "free agent",
        "manual": "manual",
    }
    return labels.get(str(value or ""), str(value or "").replace("_", " "))


def _asset_player_id(row: dict[str, object]) -> str:
    asset_id = str(row.get("asset_id") or "")
    if ":" in asset_id:
        return asset_id.split(":", 1)[1]
    return str(row.get("player_id") or "")


def _why_available(value: object) -> str:
    if value == "released_veteran":
        return "Released veteran in the declared available pool."
    if value == "free_agent":
        return "Free agent in the available pool."
    return "Marked available by source data."


def _existing_rookie_output_path(path: str | Path | None) -> Path | None:
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    candidates.append(Path("local_exports/rookies/rookie_model_outputs.csv"))
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    return None


def _best_veteran_alternative(
    rookie: dict[str, object],
    veteran_rows: list[dict[str, object]],
) -> dict[str, object] | None:
    same_position = [
        row for row in veteran_rows if row.get("position") == rookie.get("position")
    ]
    pool = same_position or veteran_rows
    if not pool:
        return None
    return max(pool, key=lambda row: float(row["draft_value"]))


def _resolve_team_name(
    rows_by_table: dict[str, list[dict[str, object]]],
    team_id: str,
) -> str | None:
    target = _normalize_team(team_id)
    for table_name in ("rosters", "future_picks"):
        for row in rows_by_table.get(table_name, []):
            row_team_id = _normalize_team(row.get("team_id") or row.get("current_team_id"))
            if row_team_id == target:
                return str(row.get("team_name") or row.get("current_team_name") or "")
    return None


def _same_team(value: str, team_id: str, team_name: str | None) -> bool:
    normalized = _normalize_team(value)
    return normalized == _normalize_team(team_id) or (
        team_name is not None and normalized == _normalize_team(team_name)
    )


def _normalize_team(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _pick_value_100(snapshot_value: object) -> float:
    if snapshot_value is None or snapshot_value == "":
        return 0.0
    return round(min(max(float(snapshot_value) / 10.0, 0.0), 100.0), 2)


def _reach_label(
    *,
    value_gap: float,
    overall_pick: int,
    earliest_pick: object,
) -> str:
    if earliest_pick not in (None, "") and overall_pick < int(earliest_pick):
        return "Avoid"
    if value_gap >= 8:
        return "Value"
    if value_gap >= -4:
        return "Fair"
    if value_gap >= -12:
        return "Reach"
    return "Avoid"


def _reach_rank(label: str) -> int:
    return {"Value": 1, "Fair": 2, "Reach": 3, "Avoid": 4}.get(label, 99)


def _ordered_reach_labels(labels: set[str]) -> list[str]:
    return [label for label in ("Value", "Fair", "Reach", "Avoid") if label in labels]


def _pick_compare_note(label: str, value_gap: float) -> str:
    if label == "Value":
        return f"Model value is {value_gap:.1f} points above this pick slot."
    if label == "Fair":
        return "This fits the pick value window."
    if label == "Reach":
        return f"Model value is {abs(value_gap):.1f} points below this pick slot."
    return "Avoid at this pick unless roster context overrides the board."


def _rookie_veteran_note(value_gap: float) -> str:
    if value_gap >= 5:
        return "Rookie is clearly ahead of the available veteran alternative."
    if value_gap <= -5:
        return "Available veteran is clearly ahead of this rookie at current prices."
    return "Same tier; use position need, confidence, and roster construction."


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def _first_float(*values: object) -> float:
    for value in values:
        if value is not None and value != "":
            return float(value)
    return 0.0


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
