from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import src.services.trade_service as trade_service
from src.data.validators import ValidatedDataPack
from src.models.trade_scores import trade_asset_value, trade_path_signal, trade_value_gap
from src.services.trade_service import build_trade_central

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_trade_asset_value_uses_pick_adjusted_value_and_confidence() -> None:
    assert trade_asset_value(830, 0.68) == 564.4
    assert trade_asset_value(830, 1.25) == 830.0
    assert trade_asset_value(None, 0.8) == 0.0


def test_trade_value_gap_and_path_signal_are_deterministic() -> None:
    assert trade_value_gap(581.4, 564.4) == 17.0
    assert trade_path_signal(17.0) == "Even"
    assert trade_path_signal(195.6) == "Ask+"
    assert trade_path_signal(-204.4) == "Short"


def test_trade_central_uses_sample_pack_players_and_picks() -> None:
    board = build_trade_central(SAMPLE_PACK)

    assert board.snapshot_date == "2026-08-01"
    assert board.player_rows[0]["player"] == "Luther Burden III"
    assert board.player_rows[0]["signal"] == "Shop"
    assert board.player_rows[0]["trade_value"] == 564.4
    assert board.path_rows[0] == {
        "player": "Luther Burden III",
        "signal": "Shop",
        "trade_value": 564.4,
        "pick": "2027 1.04",
        "certainty": "projected",
        "pick_value": 581.4,
        "value_gap": 17.0,
        "path_signal": "Even",
    }


def test_trade_central_uses_official_ranking_file_when_roster_rank_is_blank(
    monkeypatch: MonkeyPatch,
) -> None:
    rows_by_table = {
        "rosters": [
            _roster("p1", "One"),
            _roster("p2", "Two"),
            _roster("p3", "Three"),
            _roster("p4", "Four"),
            _roster("p5", "Five"),
        ],
        "official_rankings": [
            {"player_id": "p1", "official_rank": 1},
            {"player_id": "p2", "official_rank": 2},
            {"player_id": "p3", "official_rank": 3},
            {"player_id": "p4", "official_rank": 4},
            {"player_id": "p5", "official_rank": 5},
        ],
        "model_outputs": [
            _output("p1", "One", 91, 950, 0.84),
            _output("p2", "Two", 89, 920, 0.88),
            _output("p3", "Three", 84, 820, 0.72),
            _output("p4", "Four", 82, 830, 0.68),
            _output("p5", "Five", 87, 900, 0.80),
        ],
        "future_picks": [],
        "pick_values": [],
    }
    monkeypatch.setattr(
        trade_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="in-memory",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_trade_central("in-memory")

    shop_rows = [row for row in board.player_rows if row["signal"] == "Shop"]
    assert [row["player"] for row in shop_rows] == ["Four"]


def _roster(player_id: str, player_name: str) -> dict[str, object]:
    return {
        "team_id": "niners",
        "team_name": "Niners",
        "player_id": player_id,
        "player_name": player_name,
        "position": "RB",
        "roster_status": "rostered",
        "official_rank": None,
    }


def _output(
    player_id: str,
    player_name: str,
    private_score: float,
    pick_adjusted_value: float,
    confidence_score: float,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "private_score": private_score,
        "market_score": private_score,
        "war_score": private_score,
        "pick_adjusted_value": pick_adjusted_value,
        "confidence_score": confidence_score,
        "risk_level": "medium",
        "recommendation": "keep",
    }
