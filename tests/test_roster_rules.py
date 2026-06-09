from __future__ import annotations

import csv
from pathlib import Path

from src.models.keeper_scores import KeeperScoreInputs
from src.services.roster_service import (
    forced_release_candidate_names,
    keeper_inputs_from_rows,
    keeper_pressure_by_team,
    official_top_five_names,
)
from src.services.team_service import build_team_keeper_board


def test_niners_sample_identifies_expected_official_top_five() -> None:
    rows = _sample_roster_rows()

    assert official_top_five_names(rows) == [
        "De'Von Achane",
        "Lamar Jackson",
        "Chase Brown",
        "Luther Burden",
        "Brian Thomas",
    ]


def test_roster_service_builds_keeper_inputs_and_forced_release_candidate() -> None:
    rows = [
        {
            "player_id": "p1",
            "player_name": "One",
            "position": "RB",
            "official_rank": 1,
            "private_score": 90,
        },
        {
            "player_id": "p2",
            "player_name": "Two",
            "position": "WR",
            "official_rank": 2,
            "private_score": 70,
        },
        {
            "player_id": "p3",
            "player_name": "Three",
            "position": "QB",
            "official_rank": 3,
            "private_score": 86,
        },
        {
            "player_id": "p4",
            "player_name": "Four",
            "position": "TE",
            "official_rank": 4,
            "private_score": 82,
        },
        {
            "player_id": "p5",
            "player_name": "Five",
            "position": "RB",
            "official_rank": 5,
            "private_score": 84,
        },
    ]

    assert len(keeper_inputs_from_rows(rows)) == 5
    assert forced_release_candidate_names(rows) == ["Two"]


def test_forced_release_prefers_highest_drop_score_inside_top_five() -> None:
    players = [
        _keeper_input("p1", "Achane", "RB", 100, 10, 94),
        _keeper_input("p2", "Lamar", "QB", 100, 31, 92),
        KeeperScoreInputs(
            "p3",
            "Chase Brown",
            "RB",
            50,
            official_rank=35,
            long_term_private_value=86,
            next_2_year_starter_value=86,
            scarcity_bonus=86,
            trade_liquidity=86,
            age_curve=86,
            risk_adj=86,
            build_fit=86,
            roster_redundancy=10,
            decline_risk=0,
        ),
        KeeperScoreInputs(
            "p4",
            "Luther Burden",
            "WR",
            50,
            official_rank=56,
            long_term_private_value=85,
            next_2_year_starter_value=85,
            scarcity_bonus=85,
            trade_liquidity=85,
            age_curve=85,
            risk_adj=85,
            build_fit=85,
            roster_redundancy=0,
            decline_risk=0,
        ),
        _keeper_input("p5", "Brian Thomas", "WR", 100, 66, 90),
    ]

    board = build_team_keeper_board(players)

    assert [player.player_name for player in board.forced_release_candidates] == [
        "Chase Brown"
    ]


def _keeper_input(
    player_id: str,
    player_name: str,
    position: str,
    private_score: float,
    official_rank: int,
    keeper_value: float,
) -> KeeperScoreInputs:
    return KeeperScoreInputs(
        player_id,
        player_name,
        position,
        private_score,
        official_rank=official_rank,
        long_term_private_value=keeper_value,
        next_2_year_starter_value=keeper_value,
        scarcity_bonus=keeper_value,
        trade_liquidity=keeper_value,
        age_curve=keeper_value,
        risk_adj=keeper_value,
        build_fit=keeper_value,
    )


def test_keeper_pressure_by_team_returns_team_pressure() -> None:
    rows = [
        {"team_id": "niners", "team_name": "Niners", "official_rank": rank}
        for rank in range(1, 6)
    ]

    pressures = keeper_pressure_by_team(rows, protect_limit=4)

    assert len(pressures) == 1
    assert pressures[0].team_id == "niners"
    assert pressures[0].pressure_count == 2


def test_team_keeper_board_composes_top_five_best_keepers_and_pressure() -> None:
    players = [
        KeeperScoreInputs(f"p{i}", f"Player {i}", "RB", 80 + i, official_rank=i)
        for i in range(1, 7)
    ]

    board = build_team_keeper_board(players, protect_limit=3)

    assert [player.player_name for player in board.official_top_five] == [
        "Player 1",
        "Player 2",
        "Player 3",
        "Player 4",
        "Player 5",
    ]
    assert len(board.best_keepers) == 3
    assert board.pressure.pressure_count == 4


def _sample_roster_rows() -> list[dict[str, object]]:
    path = Path("sample_data/2026_pre_declaration/fact_rosters.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
