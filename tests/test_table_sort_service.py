from __future__ import annotations

from src.services.command_board_service import (
    TEAM_FORCED_RELEASE_SORT,
    TEAM_ROSTER_SORT,
    TEAM_TOP_FIVE_SORT,
    WAR_BOARD_ACTION_QUEUE_SORT,
    WAR_BOARD_SORT,
    build_team_command_board,
    build_war_board,
)
from src.services.draft_service import (
    DRAFT_ASSET_SORT,
    DRAFT_PICK_SORT,
    DRAFT_RELEASE_TARGET_SORT,
    DRAFT_TEAM_TOTAL_SORT,
    build_draft_room,
)
from src.services.league_service import (
    LEAGUE_DEFAULT_RELEASE_SORT,
    LEAGUE_PRESSURE_SORT,
    LEAGUE_TARGET_SORT,
    build_league_intel,
)
from src.services.table_sort_service import sort_caption
from src.services.trade_service import (
    TRADE_PICK_PATH_SORT,
    TRADE_PLAYER_SORT,
    build_trade_central,
)

SAMPLE_PACK = "sample_data/2026_pre_declaration"
ROOKIE_MODEL_DIR = "sample_data/rookie_model_v1"


def test_sort_caption_is_human_readable() -> None:
    caption = sort_caption(WAR_BOARD_SORT)

    assert caption.startswith("Sorted by Best overall rank")
    assert "Best overall model rank appears first" in caption


def test_war_board_declares_and_uses_best_overall_default_sort() -> None:
    board = build_war_board(SAMPLE_PACK)

    assert board.sort_metadata["rows"] == WAR_BOARD_SORT
    assert board.sort_metadata["action_queue_rows"] == WAR_BOARD_ACTION_QUEUE_SORT
    assert WAR_BOARD_SORT.sort_columns == ("overall_rank", "player")
    assert WAR_BOARD_SORT.directions == ("asc", "asc")
    assert _is_sorted(
        board.rows,
        key=lambda row: (
            _int(row["overall_rank"], 9999),
            str(row["player"]),
        ),
    )
    assert WAR_BOARD_ACTION_QUEUE_SORT.sort_columns == ("action", "overall_rank", "player")
    assert WAR_BOARD_ACTION_QUEUE_SORT.directions == ("custom", "asc", "asc")


def test_my_team_tables_declare_and_use_intended_sorts() -> None:
    board = build_team_command_board(SAMPLE_PACK)

    assert board.sort_metadata["roster_rows"] == TEAM_ROSTER_SORT
    assert board.sort_metadata["top_five_rows"] == TEAM_TOP_FIVE_SORT
    assert board.sort_metadata["forced_release_rows"] == TEAM_FORCED_RELEASE_SORT
    assert TEAM_ROSTER_SORT.sort_columns == (
        "team_section",
        "recommendation",
        "cut_risk",
        "keep_priority",
        "league_rank",
        "player",
    )
    assert _is_sorted(board.roster_rows, key=_team_roster_sort_key)
    assert _is_sorted(
        board.top_five_rows,
        key=lambda row: (_int(row["league_rank"], 999), str(row["player"])),
    )
    assert _is_sorted(
        board.forced_release_rows,
        key=lambda row: (
            _float(row["keep_priority"]),
            -_float(row["cut_risk"]),
            _int(row["league_rank"], 999),
            str(row["player"]),
        ),
    )


def test_league_intel_tables_declare_and_use_intended_sorts() -> None:
    board = build_league_intel(SAMPLE_PACK)

    assert board.sort_metadata["pressure_rows"] == LEAGUE_PRESSURE_SORT
    assert board.sort_metadata["default_release_rows"] == LEAGUE_DEFAULT_RELEASE_SORT
    assert board.sort_metadata["target_rows"] == LEAGUE_TARGET_SORT
    assert _is_sorted(
        board.pressure_rows,
        key=lambda row: (
            -_float(row["forced_release_pain"]),
            -_float(row["release_decision_difficulty"]),
            str(row["team"]),
        ),
    )
    assert _is_sorted(
        board.default_release_rows,
        key=lambda row: (
            -_float(row["acquisition_value"]),
            str(row["team"]),
        ),
    )
    assert _is_sorted(
        board.target_rows,
        key=lambda row: (
            _league_target_category_order(str(row["target_category"])),
            -_float(row["acquisition_value"]),
            -_float(row["market_edge"]),
            str(row["player"]),
        ),
    )


def test_draft_room_tables_declare_and_use_intended_sorts() -> None:
    board = build_draft_room(SAMPLE_PACK, rookie_model_dir=ROOKIE_MODEL_DIR)

    assert board.sort_metadata["pick_rows"] == DRAFT_PICK_SORT
    assert board.sort_metadata["team_rows"] == DRAFT_TEAM_TOTAL_SORT
    assert board.sort_metadata["asset_rows"] == DRAFT_ASSET_SORT
    assert board.sort_metadata["release_target_rows"] == DRAFT_RELEASE_TARGET_SORT
    assert _is_sorted(
        board.pick_rows,
        key=lambda row: (
            str(row["current_team"]),
            _int(row["pick_year"]),
            _int(row["overall_pick"], 999),
        ),
    )
    assert _is_sorted(
        board.team_rows,
        key=lambda row: (-_float(row["snapshot_value"]), str(row["team"])),
    )
    assert _is_sorted(
        board.asset_rows,
        key=lambda row: (
            -_float(row["acquisition_value"]),
            -_float(row["all_asset_value"]),
            str(row["asset_id"]),
        ),
    )
    assert _is_sorted(
        board.release_target_rows,
        key=lambda row: (
            -_float(row["reacquisition_priority"]),
            -_float(row["opponent_release_target_score"]),
            str(row["player"]),
        ),
    )


def test_trade_central_tables_declare_and_use_intended_sorts() -> None:
    board = build_trade_central(SAMPLE_PACK)

    assert board.sort_metadata["player_rows"] == TRADE_PLAYER_SORT
    assert board.sort_metadata["path_rows"] == TRADE_PICK_PATH_SORT
    assert TRADE_PLAYER_SORT.sort_columns == ("signal", "trade_value", "player")
    assert "private_lve_value" in board.player_rows[0]
    assert "trade_liquidity" in board.player_rows[0]
    assert _is_sorted(
        board.player_rows,
        key=lambda row: (
            _trade_signal_order(str(row["signal"])),
            -_float(row["trade_value"]),
            str(row["player"]),
        ),
    )
    assert _is_sorted(
        board.path_rows,
        key=lambda row: (abs(_float(row["value_gap"])), str(row["pick"])),
    )


def _is_sorted(rows: list[dict[str, object]], *, key) -> bool:
    keys = [key(row) for row in rows]
    return keys == sorted(keys)


def _team_roster_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        _team_section_order(str(row["team_section"])),
        _recommendation_order(str(row["recommendation"])),
        -_float(row["cut_risk"]),
        -_float(row["keep_priority"]),
        _int(row["league_rank"], 999),
        str(row["player"]),
    )


def _team_section_order(section: str) -> int:
    order = {
        "Core Holds": 0,
        "Forced-Release Decision": 1,
        "Bubble Players": 2,
        "Shop Candidates": 3,
        "Bench/Stash": 4,
    }
    return order.get(section, 99)


def _recommendation_order(recommendation: str) -> int:
    order = {
        "shop/release": 0,
        "release": 1,
        "drop": 1,
        "release/drop": 1,
        "shop": 2,
        "bubble": 3,
        "review": 4,
        "hold": 5,
        "risk": 6,
        "keep": 7,
    }
    return order.get(recommendation.lower(), 99)


def _trade_signal_order(signal: str) -> int:
    return {
        "Roster Context Review": 0,
        "Manual Roster Review": 1,
        "Hold Value Context": 2,
        "Watch": 3,
    }.get(signal, 99)


def _war_action_order(action: str) -> int:
    return {
        "shop/release": 0,
        "release": 1,
        "drop": 1,
        "release/drop": 1,
        "shop": 2,
        "bubble": 3,
        "review": 4,
        "risk": 5,
        "hold": 6,
        "keep": 7,
    }.get(action.lower(), 99)


def _league_target_category_order(category: str) -> int:
    order = {
        "Likely Forced Releases": 0,
        "Cheap Targets": 1,
        "Expensive Targets": 2,
        "Model vs Market Targets": 3,
        "Avoid": 4,
    }
    return order.get(category, 99)


def _float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _int(value: object, default: int = 0) -> int:
    if value is None or value == "":
        return default
    return int(value)
