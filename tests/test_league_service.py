from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import src.services.league_service as league_service
from src.data.validators import ValidatedDataPack
from src.services.league_service import build_league_intel

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_league_intel_uses_sample_pack_keeper_pressure() -> None:
    board = build_league_intel(SAMPLE_PACK)

    assert board.snapshot_date == "2026-08-01"
    assert board.pressure_rows == [
        {
            "team": "Niners",
            "pressure_level": "Medium",
                "pressure_count": 2,
            "forced_release_count": 1,
            "official_top_five_count": 5,
                "roster_count": 24,
            "protect_limit": 23,
        }
    ]
    assert [row["player"] for row in board.default_release_rows] == [
        "Luther Burden"
    ]
    assert {row["signal"] for row in board.shield_rows} == {"Shield"}


def test_league_intel_sorts_pressure_and_uses_official_rankings(
    monkeypatch: MonkeyPatch,
) -> None:
    rows_by_table = {
        "rosters": [
            *_team_rows("alpha", "Alpha", 1, 5),
            *_team_rows("bravo", "Bravo", 6, 2),
        ],
        "official_rankings": [
            {"player_id": f"alpha_{index}", "official_rank": index}
            for index in range(1, 6)
        ],
        "model_outputs": [
            _output(f"alpha_{index}", 70 + index) for index in range(1, 6)
        ]
        + [_output(f"bravo_{index}", 80 + index) for index in range(6, 8)],
    }
    monkeypatch.setattr(
        league_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="in-memory",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_league_intel("in-memory", protect_limit=4)

    assert [row["team"] for row in board.pressure_rows] == ["Alpha", "Bravo"]
    assert board.pressure_rows[0]["pressure_count"] == 2
    assert board.pressure_rows[1]["pressure_count"] == 0
    assert board.pressure_levels == ["Medium", "Low"]


def _team_rows(
    team_id: str,
    team_name: str,
    first_player_number: int,
    count: int,
) -> list[dict[str, object]]:
    return [
        {
            "team_id": team_id,
            "team_name": team_name,
            "player_id": f"{team_id}_{index}",
            "player_name": f"{team_name} {index}",
            "position": "RB",
            "roster_status": "rostered",
            "official_rank": None,
        }
        for index in range(first_player_number, first_player_number + count)
    ]


def _output(player_id: str, private_score: float) -> dict[str, object]:
    return {
        "player_id": player_id,
        "private_score": private_score,
        "market_score": private_score,
        "confidence_score": 0.7,
    }
