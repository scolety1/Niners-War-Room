from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import src.services.trade_service as trade_service
from src.data.validators import ValidatedDataPack
from src.models.trade_scores import (
    TradeAsset,
    TradeScoreInputs,
    acceptance_chance,
    keeper_impact_score,
    market_trade_score,
    niners_edge_score,
    opponent_benefit_score,
    private_trade_score,
    score_trade,
    trade_asset_value,
    trade_review_label,
    trade_value_gap,
)
from src.services.trade_service import build_trade_central

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_trade_asset_value_uses_pick_adjusted_value_and_confidence() -> None:
    assert trade_asset_value(830, 0.68) == 564.4
    assert trade_asset_value(830, 1.25) == 830.0
    assert trade_asset_value(None, 0.8) == 0.0


def test_trade_value_gap_is_deterministic() -> None:
    assert trade_value_gap(453.6, 564.4) == -110.8


def test_player_for_pick_trade_scores_use_hand_calculated_components() -> None:
    inputs = TradeScoreInputs(
        incoming_assets=(
            TradeAsset(
                name="2027 1.04",
                private_value=453.6,
                market_value=453.6,
                keeper_value=0.0,
            ),
        ),
        outgoing_assets=(
            TradeAsset(
                name="Luther Burden",
                private_value=564.4,
                market_value=585.1,
                keeper_value=85.0,
            ),
        ),
    )

    assert private_trade_score(inputs) == -110.8
    assert market_trade_score(inputs) == -131.5
    assert keeper_impact_score(inputs) == -85.0
    assert opponent_benefit_score(inputs) == 112.9
    assert (
        niners_edge_score(
            private_trade_score_value=-110.8,
            market_trade_score_value=-131.5,
            keeper_impact_score_value=-85.0,
        )
        == -107.2
    )
    assert (
        acceptance_chance(
            niners_edge_score_value=-107.2,
            opponent_benefit_score_value=112.9,
        )
        == 77.9
    )

    score = score_trade(inputs)
    assert score.private_trade_score == -110.8
    assert score.market_trade_score == -131.5
    assert score.keeper_impact_score == -85.0
    assert score.niners_edge_score == -107.2
    assert score.opponent_benefit_score == 112.9
    assert score.acceptance_chance == 77.9
    assert score.label == "DECLINE"


def test_shield_trade_scores_and_political_risk_are_hand_calculated() -> None:
    inputs = TradeScoreInputs(
        incoming_assets=(
            TradeAsset(
                name="Shield Player",
                private_value=260.0,
                market_value=240.0,
                keeper_value=90.0,
            ),
        ),
        outgoing_assets=(
            TradeAsset(
                name="2026 2.04",
                private_value=200.0,
                market_value=200.0,
                keeper_value=0.0,
            ),
        ),
    )

    score = score_trade(inputs)
    assert score.private_trade_score == 60.0
    assert score.market_trade_score == 40.0
    assert score.keeper_impact_score == 90.0
    assert score.niners_edge_score == 65.0
    assert score.opponent_benefit_score == -60.0
    assert score.acceptance_chance == 34.8
    assert score.label == "CONSIDER"

    risk_score = score_trade(
        TradeScoreInputs(
            incoming_assets=inputs.incoming_assets,
            outgoing_assets=inputs.outgoing_assets,
            political_risk=80.0,
        )
    )
    assert risk_score.acceptance_chance == 10.8
    assert risk_score.label == "POLITICAL RISK"


def test_trade_review_labels_remain_deterministic() -> None:
    cases = [
        (100, 10, -50, 35, 0, "OFFER"),
        (30, 0, -100, 15, 0, "CONSIDER"),
        (-10, 0, -200, 5, 0, "HOLD"),
        (-100, -20, 50, 80, 0, "DECLINE"),
        (-160, 0, 100, 100, 0, "AVOID"),
        (100, 10, 100, 100, 70, "POLITICAL RISK"),
    ]
    for edge, keeper, opponent, acceptance, risk, expected in cases:
        assert (
            trade_review_label(
                niners_edge_score_value=edge,
                keeper_impact_score_value=keeper,
                opponent_benefit_score_value=opponent,
                acceptance_chance_value=acceptance,
                political_risk=risk,
            )
            == expected
        )


def test_trade_central_uses_sample_pack_players_and_picks() -> None:
    board = build_trade_central(SAMPLE_PACK)

    assert board.snapshot_date == "2026-08-01"
    assert board.player_rows[0]["player"] == "Luther Burden"
    assert board.player_rows[0]["signal"] == "Shop"
    assert board.player_rows[0]["trade_value"] == 564.4
    luther_path = next(
        row
        for row in board.path_rows
        if row["player"] == "Luther Burden" and row["pick"] == "2027 1.04"
    )
    assert luther_path == {
        "player": "Luther Burden",
        "signal": "Shop",
        "trade_value": 564.4,
        "pick": "2027 1.04",
        "certainty": "projected",
        "pick_value": 453.6,
        "value_gap": -110.8,
        "private_trade_score": -110.8,
        "market_trade_score": -131.4,
        "keeper_impact_score": -85.0,
        "niners_edge_score": -107.2,
        "opponent_benefit_score": 112.8,
        "acceptance_chance": 74.9,
        "path_signal": "DECLINE",
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
