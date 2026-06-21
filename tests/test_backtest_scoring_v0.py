from __future__ import annotations

import pandas as pd

from scripts.build_backtest_dataset_v0 import calculate_nwr_points


def test_nwr_scoring_formula_excludes_receptions_and_fantasy_points() -> None:
    frame = pd.DataFrame(
        [
            {
                "passing_yards": 300,
                "passing_tds": 2,
                "passing_interceptions": 1,
                "rushing_yards": 50,
                "receiving_yards": 20,
                "rushing_tds": 1,
                "receiving_tds": 1,
                "rushing_first_downs": 3,
                "receiving_first_downs": 2,
                "punt_return_yards": 30,
                "kickoff_return_yards": 30,
                "special_teams_tds": 1,
                "passing_2pt_conversions": 1,
                "rushing_2pt_conversions": 1,
                "receiving_2pt_conversions": 0,
                "sack_fumbles_lost": 1,
                "rushing_fumbles_lost": 1,
                "receiving_fumbles_lost": 0,
                "receptions": 99,
                "fantasy_points": 999,
                "fantasy_points_ppr": 999,
            }
        ]
    )

    assert calculate_nwr_points(frame).iloc[0] == 40.0
