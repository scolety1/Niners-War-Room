from __future__ import annotations

from src.services.command_board_service import (
    build_import_review_board,
    build_team_command_board,
    build_war_board,
)

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_import_review_board_exposes_validation_warnings_and_row_counts() -> None:
    board = build_import_review_board(SAMPLE_PACK)

    assert board.data_pack_name == "2026_pre_declaration"
    assert board.issue_counts["error"] == 0
    assert board.issue_counts["warning"] == 0
    assert {"table": "rosters", "rows": 24} in board.row_counts


def test_team_command_board_shows_niners_top_five_and_forced_release() -> None:
    board = build_team_command_board(SAMPLE_PACK)

    assert board.rules.protect_limit == 23
    assert board.rules.official_top_five_keep_limit == 4
    assert [row["player"] for row in board.top_five_rows] == [
        "De'Von Achane",
        "Lamar Jackson",
        "Chase Brown",
        "Luther Burden",
        "Brian Thomas",
    ]
    assert [row["player"] for row in board.forced_release_rows] == ["Luther Burden"]
    assert board.keeper_board.pressure.forced_release_count == 1


def test_team_command_board_roster_rows_include_keeper_drop_shop_actions() -> None:
    board = build_team_command_board(SAMPLE_PACK)
    recommendations = {row["recommendation"] for row in board.roster_rows}

    assert "keep" in recommendations
    assert "shop/release" in recommendations


def test_war_board_is_sorted_and_filter_metadata_is_available() -> None:
    board = build_war_board(SAMPLE_PACK)

    assert [row["player"] for row in board.rows[:2]] == [
        "De'Von Achane",
        "Lamar Jackson",
    ]
    assert board.positions == ["QB", "RB", "TE", "WR"]
    assert board.teams == ["Niners"]
    assert board.recommendations == [
        "bubble",
        "drop",
        "hold",
        "keep",
        "risk",
        "shop",
    ]
