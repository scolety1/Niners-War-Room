from __future__ import annotations

import pandas as pd

from src.services.nfl_usage_target_backtest_service import (
    FEATURE_FIELDS,
    ablation_rows,
    backtest_result_rows,
    build_joined_backtest_panel,
    leakage_report_rows,
    position_summary_rows,
    promotion_recommendation_rows,
)


def _features_fixture() -> pd.DataFrame:
    rows = []
    for idx in range(30):
        rows.append(
            {
                "season": 2023,
                "player_id": f"p{idx}",
                "player_name": f"Player {idx}",
                "position": "RB" if idx < 15 else "WR",
                "team": "SF",
                "targets": idx,
                "carries": 30 - idx,
                "receptions": idx // 2,
                "touches": 30,
                "opportunities": 30,
                "rushing_yards": 300 - idx,
                "receiving_yards": idx * 10,
                "receiving_air_yards": idx * 8,
                "receiving_yards_after_catch": idx * 5,
                "rushing_first_downs": 10,
                "receiving_first_downs": idx // 3,
                "offense_snaps": 400,
                "offense_pct": 0.5,
                "red_zone_carries": idx % 5,
                "red_zone_targets": idx % 4,
                "red_zone_touches": idx % 6,
                "inside_10_carries": idx % 3,
                "inside_10_targets": idx % 2,
                "inside_10_touches": idx % 4,
                "inside_5_carries": idx % 2,
                "inside_5_targets": idx % 2,
                "inside_5_touches": idx % 3,
            }
        )
    return pd.DataFrame(rows)


def _labels_fixture() -> pd.DataFrame:
    rows = []
    for idx in range(30):
        rows.append(
            {
                "target_season": 2024,
                "player_id": f"p{idx}",
                "player_name": f"Player {idx}",
                "position": "RB" if idx < 15 else "WR",
                "next_season_nwr_points": float(idx * 10),
                "next_season_nwr_points_per_game": float(idx),
                "next_season_games": 10,
                "next_season_position_rank": 30 - idx,
                "next_season_top_qb12": 0,
                "next_season_top_rb12": 1 if idx < 12 else 0,
                "next_season_top_rb24": 1 if idx < 15 else 0,
                "next_season_top_wr12": 1 if 15 <= idx < 27 else 0,
                "next_season_top_wr24": 1 if idx >= 15 else 0,
                "next_season_top_wr36": 1 if idx >= 15 else 0,
                "next_season_top_te12": 0,
                "next_season_starter_level_by_position": "RB1" if idx < 12 else "DEPTH",
                "next_season_flex_relevant_rb_wr_te": 1,
            }
        )
    return pd.DataFrame(rows)


def test_backtest_join_enforces_feature_season_n_to_target_n_plus_1() -> None:
    joined = build_joined_backtest_panel(_features_fixture(), _labels_fixture())

    assert not joined.empty
    assert (joined["target_season"] == joined["feature_season"] + 1).all()
    assert joined["leakage_status"].eq("PASS_FEATURE_SEASON_N_TARGET_N_PLUS_1").all()
    assert joined["model_input_allowed"].eq("no").all()
    assert joined["app_wiring_allowed"].eq("no").all()


def test_backtest_results_and_reports_have_valid_review_only_statuses() -> None:
    joined = build_joined_backtest_panel(_features_fixture(), _labels_fixture())
    results = pd.DataFrame(backtest_result_rows(joined))

    assert set(FEATURE_FIELDS) <= set(results["field_name"])
    assert results["leakage_status"].eq("PASS").all()
    assert results["model_input_allowed"].eq("no").all()

    ablation = pd.DataFrame(ablation_rows(results))
    leakage = pd.DataFrame(leakage_report_rows(joined))
    position = pd.DataFrame(position_summary_rows(joined))
    recommendations = pd.DataFrame(promotion_recommendation_rows(results))

    assert not ablation.empty
    assert leakage["status"].eq("PASS").all()
    assert not position.empty
    assert recommendations["model_input_allowed"].eq("no").all()
    assert recommendations["app_wiring_allowed"].eq("no").all()
    assert recommendations["model_candidate_status"].eq("NO_ACTIVE_MODEL_CANDIDATE").all()
