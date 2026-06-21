from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_backtest_dataset_v1 import (
    V1_BASELINE_FEATURES_BY_POSITION,
    V1_CLEAN_EXPANDED_FEATURES_BY_POSITION,
    build_backtest_v1_dataset,
)
from scripts.run_backtest_v1 import BacktestRunError, _validate_inputs_v1


def test_v1_position_whitelists_exclude_inappropriate_role_fields() -> None:
    assert "receiving_yards" not in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION["QB"]
    assert "passing_yards" not in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION["RB"]
    assert "passing_yards" not in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION["WR"]
    assert "rushing_yards" not in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION["TE"]
    assert "punt_return_yards" not in V1_BASELINE_FEATURES_BY_POSITION["RB"]
    assert "kickoff_return_yards" not in V1_CLEAN_EXPANDED_FEATURES_BY_POSITION["WR"]


def test_v1_dataset_creates_missingness_indicators_and_blocks_leakage(tmp_path: Path) -> None:
    seasons = [2018, 2019, 2020, 2021, 2022]
    result = build_backtest_v1_dataset(
        seasons=seasons,
        output_root=tmp_path,
        run_label="fake_v1",
        frames={
            "season_stats": _season_stats(seasons),
            "rosters": _rosters(seasons[:-1]),
            "weekly_rosters": _weekly_rosters(seasons[:-1]),
            "snap_counts": pd.DataFrame(),
            "depth_charts": pd.DataFrame(),
            "draft_picks": pd.DataFrame(),
            "team_stats": pd.DataFrame(),
            "opportunity_pass": pd.DataFrame(),
            "opportunity_rush": pd.DataFrame(),
        },
    )

    baseline = pd.read_csv(result.baseline_path)
    clean = pd.read_csv(result.clean_expanded_path)
    missingness = pd.read_csv(result.missingness_path)
    whitelist = pd.read_csv(result.whitelist_path)
    excluded = pd.read_csv(result.excluded_features_path)

    assert not baseline.empty
    assert not clean.empty
    expected_missing = {
        "age_missing",
        "draft_capital_missing",
        "snap_pct_missing",
        "air_yards_missing",
    }
    assert expected_missing.issubset(clean.columns)
    joined_columns = ",".join(clean.columns).lower()
    assert "adp" not in joined_columns
    assert "market" not in joined_columns
    assert "fantasy_points" not in joined_columns
    assert "fantasy_points_ppr" not in joined_columns
    assert set(missingness["missing_indicator"]) == {
        "age_missing",
        "draft_capital_missing",
        "snap_pct_missing",
        "air_yards_missing",
    }
    assert {"position", "feature_set", "feature"}.issubset(whitelist.columns)
    assert "inappropriate_qb_receiving_role_feature" in set(excluded["reason"])
    assert not (tmp_path / "fake_v1" / "latest_approved.json").exists()


def test_v1_runner_rejects_blocked_feature_columns() -> None:
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
        }
    )
    baseline = pd.DataFrame({"player_id": ["p1"], "target_season": [2021], "adp_std": [1]})
    clean = pd.DataFrame({"player_id": ["p1"], "target_season": [2021], "safe": [1]})

    try:
        _validate_inputs_v1(baseline, clean, labels)
    except BacktestRunError as exc:
        assert "blocked feature" in str(exc)
    else:
        raise AssertionError("expected blocked feature rejection")


def _season_stats(seasons: list[int]) -> pd.DataFrame:
    rows = []
    players = [
        ("p1", "QB One", "QB", "SF"),
        ("p2", "RB One", "RB", "SF"),
        ("p3", "WR One", "WR", "SF"),
        ("p4", "TE One", "TE", "SF"),
    ]
    for season in seasons:
        for player_id, player_name, position, team in players:
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": player_name,
                    "player_display_name": player_name,
                    "position": position,
                    "season": season,
                    "recent_team": team,
                    "games": 10,
                    "completions": 60 * (position == "QB"),
                    "attempts": 100 * (position == "QB"),
                    "passing_yards": 1000 * (position == "QB"),
                    "passing_tds": 10 * (position == "QB"),
                    "passing_interceptions": 3 * (position == "QB"),
                    "passing_first_downs": 40 * (position == "QB"),
                    "carries": 100 * (position == "RB") + 20 * (position == "QB"),
                    "rushing_yards": 500 * (position == "RB") + 100 * (position == "QB"),
                    "rushing_tds": 5 * (position == "RB") + 1 * (position == "QB"),
                    "rushing_first_downs": 20 * (position in {"RB", "QB"}),
                    "targets": 80 * (position == "WR") + 50 * (position == "TE"),
                    "receptions": 50 * (position == "WR") + 30 * (position == "TE"),
                    "receiving_yards": 700 * (position == "WR") + 350 * (position == "TE"),
                    "receiving_tds": 6 * (position == "WR") + 3 * (position == "TE"),
                    "receiving_first_downs": 25 * (position in {"WR", "TE"}),
                    "receiving_air_yards": 900 * (position == "WR") + 400 * (position == "TE"),
                    "receiving_yards_after_catch": (
                        200 * (position == "WR") + 100 * (position == "TE")
                    ),
                    "passing_2pt_conversions": 0,
                    "rushing_2pt_conversions": 0,
                    "receiving_2pt_conversions": 0,
                    "punt_return_yards": 0,
                    "kickoff_return_yards": 0,
                    "special_teams_tds": 0,
                    "sack_fumbles_lost": 0,
                    "rushing_fumbles_lost": 1,
                    "receiving_fumbles_lost": 0,
                    "sacks_suffered": 20 * (position == "QB"),
                    "sack_yards_lost": 100 * (position == "QB"),
                    "sack_fumbles": 2 * (position == "QB"),
                }
            )
    return pd.DataFrame(rows)


def _rosters(seasons: list[int]) -> pd.DataFrame:
    rows = []
    for season in seasons:
        for player_id, name, position in (
            ("p1", "QB One", "QB"),
            ("p2", "RB One", "RB"),
            ("p3", "WR One", "WR"),
            ("p4", "TE One", "TE"),
        ):
            rows.append(
                {
                    "season": season,
                    "gsis_id": player_id,
                    "full_name": name,
                    "position": position,
                    "birth_date": "2000-01-01",
                    "years_exp": season - 2017,
                }
            )
    return pd.DataFrame(rows)


def _weekly_rosters(seasons: list[int]) -> pd.DataFrame:
    rows = []
    for season in seasons:
        for week in (1, 2):
            for player_id in ("p1", "p2", "p3", "p4"):
                rows.append(
                    {
                        "season": season,
                        "week": week,
                        "gsis_id": player_id,
                        "status": "ACT",
                    }
                )
    return pd.DataFrame(rows)
