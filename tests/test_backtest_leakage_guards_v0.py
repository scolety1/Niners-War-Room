from __future__ import annotations

import pandas as pd

from scripts.build_backtest_dataset_v0 import BacktestBuildError, _validate_feature_columns
from scripts.run_backtest_v0 import BacktestRunError, _validate_inputs


def test_dataset_builder_rejects_blocked_and_yellow_feature_columns() -> None:
    for column in ("sleeper_adp", "market_rank", "fantasy_points", "passing_epa"):
        try:
            _validate_feature_columns(["player_id", column])
        except BacktestBuildError as exc:
            assert column in str(exc)
        else:
            raise AssertionError(f"expected blocked column failure for {column}")


def test_runner_rejects_blocked_features_before_modeling() -> None:
    baseline = pd.DataFrame(
        {
            "player_id": ["p1"],
            "target_season": [2021],
            "sleeper_adp": [1],
        }
    )
    expanded = pd.DataFrame({"player_id": ["p1"], "target_season": [2021], "safe": [1]})
    labels = pd.DataFrame(
        {
            "player_id": ["p1"],
            "target_season": [2021],
            "target_player_name": ["Player"],
            "target_position": ["QB"],
            "target_team": ["SF"],
            "target_games": [17],
            "next_nwr_points": [100],
            "next_nwr_ppg": [10],
            "qb_t12": [1],
            "rb_t12": [0],
            "rb_t24": [0],
            "wr_t12": [0],
            "wr_t24": [0],
            "wr_t36": [0],
            "te_t12": [0],
        }
    )

    try:
        _validate_inputs(baseline, expanded, labels)
    except BacktestRunError as exc:
        assert "blocked feature" in str(exc)
    else:
        raise AssertionError("expected runner leakage guard failure")
