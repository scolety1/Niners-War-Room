from __future__ import annotations

from pathlib import Path

import pytest
from pytest import MonkeyPatch

import src.services.asset_board_service as asset_board_service
from src.data.validators import ValidatedDataPack
from src.services.asset_board_service import (
    AssetConversionInputs,
    acquisition_value,
    all_asset_value,
    build_unified_asset_board,
    compare_pick_to_player,
    compare_rookie_to_veteran,
    convert_asset_value,
    liquidity_penalty,
    package_math,
    pick_all_asset_value,
    pick_equivalent,
    public_market_score_capped,
    rookie_all_asset_value,
    trade_package_score,
)

SAMPLE_PACK = "sample_data/2026_pre_declaration"
ROOKIE_DIR = "sample_data/rookie_model_v1"


def test_asset_value_formulas_are_deterministic() -> None:
    assert all_asset_value(
        win_now_value=80,
        dynasty_hold_value=75,
        trade_liquidity_value=70,
        keeper_adjusted_value=75,
        replacement_value=72,
    ) == pytest.approx(75.2)
    assert rookie_all_asset_value(
        final_decision_score=90,
        long_term_dynasty_score=85,
        trade_insulation_score=80,
        rookie_opportunity_score=70,
        league_fit_score=88,
    ) == pytest.approx(84.55)
    assert pick_all_asset_value(63, 2026) == pytest.approx(65.0)
    assert pick_all_asset_value(63, 2027) == pytest.approx(58.7)
    assert acquisition_value(70, confidence_score=50, roster_spot_cost=4) == pytest.approx(64.0)
    assert acquisition_value(
        70,
        current_cost_value=60,
        accessibility_bonus=4,
        roster_spot_cost=2,
    ) == pytest.approx(62.0)


def test_asset_conversion_refactor_uses_shared_intermediary_scores() -> None:
    result = convert_asset_value(
        AssetConversionInputs(
            private_base_score=80,
            year1_score=80,
            long_horizon_score=75,
            age_curve_score=75,
            format_fit_score=72,
            role_security_score=75,
            replacement_gap_score=72,
            public_market_score=70,
            liquidity_score=70,
            confidence_score=75,
        )
    )

    assert result.replacement_value == pytest.approx(72.6)
    assert result.win_now_value == pytest.approx(76.2)
    assert result.dynasty_hold_value == pytest.approx(76.75)
    assert result.trade_liquidity_value == pytest.approx(71.0)
    assert result.keeper_adjusted_value == pytest.approx(76.06)
    assert result.all_asset_value == pytest.approx(75.55)
    assert result.acquisition_value == pytest.approx(75.55)


def test_asset_conversion_caps_market_drift_in_blended_value() -> None:
    low_market = convert_asset_value(
        AssetConversionInputs(
            private_base_score=80,
            year1_score=80,
            long_horizon_score=78,
            age_curve_score=78,
            format_fit_score=76,
            role_security_score=80,
            replacement_gap_score=76,
            public_market_score=0,
            liquidity_score=0,
            confidence_score=82,
        )
    )
    high_market = convert_asset_value(
        AssetConversionInputs(
            private_base_score=80,
            year1_score=80,
            long_horizon_score=78,
            age_curve_score=78,
            format_fit_score=76,
            role_security_score=80,
            replacement_gap_score=76,
            public_market_score=100,
            liquidity_score=100,
            confidence_score=82,
        )
    )

    assert low_market.keeper_adjusted_value == high_market.keeper_adjusted_value
    assert high_market.trade_liquidity_value > low_market.trade_liquidity_value
    assert high_market.all_asset_value - low_market.all_asset_value <= 8.0


def test_public_market_and_liquidity_are_capped_for_lve_format() -> None:
    assert public_market_score_capped(
        95,
        private_base_score=72,
        position="QB",
    ) == pytest.approx(83.0)
    assert public_market_score_capped(
        95,
        private_base_score=72,
        position="WR",
    ) == pytest.approx(84.0)
    assert liquidity_penalty(65) == pytest.approx(0.0)
    assert liquidity_penalty(50) == pytest.approx(3.0)
    assert liquidity_penalty(30) == pytest.approx(6.0)
    assert liquidity_penalty(20) == pytest.approx(10.0)


def test_pick_equivalent_bands() -> None:
    assert pick_equivalent(96) == "1.01-1.03"
    assert pick_equivalent(92) == "1.04-1.06"
    assert pick_equivalent(87) == "1.07-1.10"
    assert pick_equivalent(82) == "2.01-2.05"
    assert pick_equivalent(77) == "2.06-2.10"
    assert pick_equivalent(70) == "3.01-3.07"
    assert pick_equivalent(65) == "3.08-4.04"
    assert pick_equivalent(58) == "4.05-5.01"
    assert pick_equivalent(53) == "5.02-5.10"
    assert pick_equivalent(51) == "UDFA"


def test_unified_asset_board_combines_veterans_picks_and_rookies() -> None:
    board = build_unified_asset_board(SAMPLE_PACK, rookie_model_dir=ROOKIE_DIR)

    assert {"veteran", "pick", "rookie"}.issubset(set(board.asset_types))
    assert board.rows[0]["acquisition_value"] >= board.rows[-1]["acquisition_value"]
    assert any(row["asset_type"] == "rookie" for row in board.rows)
    assert any(row["asset_type"] == "pick" for row in board.rows)
    assert any(row["player"] == "Chase Brown" for row in board.rows)
    chase_brown = next(row for row in board.rows if row["player"] == "Chase Brown")
    assert chase_brown["replacement_context"] == "steady_state"
    assert chase_brown["replacement_baseline"] == "steady_state:RB"
    assert chase_brown["replacement_position_rank"] == 2


def test_unified_asset_board_quarantines_legacy_active_pack_score(
    monkeypatch: MonkeyPatch,
) -> None:
    rows_by_table = {
        "rosters": [
            {
                "team_id": "niners",
                "team_name": "Niners",
                "player_id": "1479",
                "player_name": "Keenan Allen",
                "position": "WR",
                "roster_status": "rostered",
            }
        ],
        "official_rankings": [],
        "model_outputs": [
            {
                "snapshot_date": "2026-05-30",
                "player_id": "1479",
                "player_name": "Keenan Allen",
                "position": "WR",
                "private_score": "82.4",
                "keeper_score": "82.4",
                "market_score": "82.4",
                "confidence_score": "0.7",
                "model_version": "veteran_lve_stats_first_v1_0_0",
            }
        ],
        "future_picks": [],
        "pick_values": [],
    }
    monkeypatch.setattr(
        asset_board_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="legacy-pack",
            snapshot_date="2026-05-30",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_unified_asset_board("legacy-pack")
    row = board.rows[0]

    assert row["player"] == "Keenan Allen"
    assert row["primary_review_score"] == ""
    assert row["legacy_active_pack_score"] == pytest.approx(82.4)
    assert row["score_lineage_class"] == "legacy_active_pack"
    assert row["score_source_column"] == "private_score"
    assert row["legacy_formula_warning"] is True
    assert row["stale_or_legacy_formula_warning"] is True


def test_rookie_veteran_and_pick_player_comparisons() -> None:
    board = build_unified_asset_board(SAMPLE_PACK, rookie_model_dir=ROOKIE_DIR)
    assets = {row["asset_id"]: row for row in board.rows}
    rookie = next(row for row in board.rows if row["asset_type"] == "rookie")
    veteran = next(row for row in board.rows if row["player"] == "Luther Burden")
    pick = next(row for row in board.rows if row["asset_type"] == "pick")

    typed_assets = _typed_assets(board)
    rookie_result = compare_rookie_to_veteran(
        typed_assets[str(rookie["asset_id"])],
        typed_assets[str(veteran["asset_id"])],
    )
    pick_result = compare_pick_to_player(
        typed_assets[str(pick["asset_id"])],
        typed_assets[str(veteran["asset_id"])],
    )

    assert rookie_result.recommendation in {"rookie", "veteran", "tier_tiebreak"}
    assert pick_result.recommendation in {"pick_optionality", "player", "pick_tiebreak"}
    assert assets[str(rookie_result.preferred_asset_id)]


def test_package_math_and_trade_package_helpers() -> None:
    board = build_unified_asset_board(SAMPLE_PACK, rookie_model_dir=ROOKIE_DIR)
    typed_assets = _typed_assets(board)
    package_assets = tuple(list(typed_assets.values())[:2])

    math = package_math(package_assets)
    assert math.raw_asset_value > math.package_value - 8
    assert math.roster_spot_penalty == 4
    assert math.stud_tax_penalty >= 0

    score = trade_package_score((package_assets[0],), (package_assets[1],))
    assert score.label in {"OFFER", "CONSIDER", "HOLD", "DECLINE", "AVOID", "POLITICAL RISK"}


def _typed_assets(board):
    from src.services.asset_board_service import UnifiedAsset

    return {
        str(row["asset_id"]): UnifiedAsset(
            asset_id=str(row["asset_id"]),
            asset_type=str(row["asset_type"]),
            player_id="",
            player_name=str(row["player"]),
            position=str(row["position"]),
            team=str(row["team"]),
            all_asset_value=float(row["all_asset_value"]),
            acquisition_value=float(row["acquisition_value"]),
            keeper_adjusted_value=float(row["keeper_adjusted_value"]),
            trade_liquidity_value=float(row["trade_liquidity_value"]),
            win_now_value=float(row["win_now_value"]),
            dynasty_hold_value=float(row["dynasty_hold_value"]),
            replacement_value=float(row["replacement_value"]),
            confidence_score=float(row["confidence"]),
            pick_equivalent=str(row["pick_equivalent"]),
            recommendation=str(row["recommendation"]),
            source=str(row["source"]),
        )
        for row in board.rows
    }
