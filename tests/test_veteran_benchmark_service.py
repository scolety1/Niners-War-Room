from __future__ import annotations

from pathlib import Path

import pytest

from src.models.rookie_scores import Position, RookieInput, score_rookie
from src.services.rookie_model_service import (
    generated_veteran_benchmark_rows,
    run_rookie_model_from_dir,
)
from src.services.veteran_benchmark_service import (
    derive_veteran_benchmarks,
    load_veteran_assets,
)

SAMPLE_DIR = Path("sample_data/rookie_model_v1")


def test_actual_veteran_pool_derives_same_position_and_flex_benchmarks() -> None:
    assets = load_veteran_assets(SAMPLE_DIR / "veteran_opportunity_assets.csv")
    benchmarks = {item.position: item for item in derive_veteran_benchmarks(assets)}

    assert benchmarks[Position.QB].benchmark_score == 72
    assert benchmarks[Position.RB].same_position_score == pytest.approx(70)
    assert benchmarks[Position.WR].same_position_score == pytest.approx(72)
    assert benchmarks[Position.TE].same_position_score == pytest.approx(66)
    assert benchmarks[Position.RB].flex_pool_score == pytest.approx(72.5)
    assert benchmarks[Position.RB].benchmark_score == pytest.approx(70.75)
    assert benchmarks[Position.WR].benchmark_score == pytest.approx(72.15)
    assert benchmarks[Position.TE].benchmark_score == pytest.approx(68.93)


def test_protected_or_inactive_assets_do_not_enter_benchmarks() -> None:
    rows = generated_veteran_benchmark_rows(SAMPLE_DIR)
    wr_row = next(row for row in rows if row["position"] == "WR")

    assert wr_row["benchmark_score"] < 90
    assert wr_row["asset_count"] == 8


def test_rookie_model_uses_actual_pool_when_asset_table_exists() -> None:
    run = run_rookie_model_from_dir(SAMPLE_DIR)
    wr_score = next(score for score in run.scores if score.player_id == "rookie_wr_vet_drag")

    assert wr_score.veteran_benchmark_score == pytest.approx(72.15)
    assert wr_score.veteran_opportunity_adjustment == pytest.approx(-3.47)
    assert "veteran_opportunity_drag" in wr_score.risk_flags


def test_veteran_benchmark_changes_do_not_mutate_main_prospect_score() -> None:
    rookie = RookieInput(
        player_id="wr",
        player_name="WR",
        position=Position.WR,
        class_year=2026,
        model_mode="post_draft",
        source_snapshot_id="test",
        source_name="test",
        source_date="2026-05-05",
        features={
            "draft_capital": 66,
            "target_earning": 58,
            "efficiency_dominance": 64,
            "age_trajectory": 72,
            "chain_moving": 58,
        },
        rookie_opportunity_score=52,
        veteran_benchmark_score=50,
    )
    easier_market = score_rookie(rookie)
    harder_market = score_rookie(
        RookieInput(
            **{
                **rookie.__dict__,
                "veteran_benchmark_score": 90,
            }
        )
    )

    assert easier_market.main_prospect_score == harder_market.main_prospect_score
    assert easier_market.final_decision_score > harder_market.final_decision_score
