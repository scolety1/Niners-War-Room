from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.build_backtest_dataset_v0 import build_backtest_dataset


def test_backtest_dataset_uses_season_s_features_for_season_s_plus_one_labels(
    tmp_path: Path,
) -> None:
    seasons = [2018, 2019, 2020, 2021, 2022]
    frames = {
        "season_stats": _season_stats(seasons),
        "rosters": _rosters(seasons[:-1]),
        "weekly_rosters": _weekly_rosters(seasons[:-1]),
        "snap_counts": pd.DataFrame(),
        "depth_charts": pd.DataFrame(),
        "draft_picks": pd.DataFrame(),
        "team_stats": pd.DataFrame(),
        "opportunity_pass": pd.DataFrame(),
        "opportunity_rush": pd.DataFrame(),
    }

    result = build_backtest_dataset(
        seasons=seasons,
        output_root=tmp_path,
        run_label="fake_backtest",
        frames=frames,
    )

    baseline = pd.read_csv(result.baseline_path)
    expanded = pd.read_csv(result.expanded_path)
    labels = pd.read_csv(result.labels_path)

    assert result.target_seasons == [2019, 2020, 2021, 2022]
    assert not baseline.empty
    assert not expanded.empty
    assert not labels.empty
    assert (baseline["target_season"] == baseline["feature_season"] + 1).all()
    assert (expanded["target_season"] == expanded["feature_season"] + 1).all()
    assert "fantasy_points" not in ",".join(baseline.columns).lower()
    assert "adp" not in ",".join(expanded.columns).lower()
    assert "age_at_season_end" in expanded.columns
    assert "is_active_any_week" in expanded.columns
    assert result.manifest_path.exists()


def _season_stats(seasons: list[int]) -> pd.DataFrame:
    rows = []
    players = [
        ("p1", "QB One", "QB", "SF"),
        ("p2", "RB One", "RB", "SF"),
        ("p3", "WR One", "WR", "SF"),
        ("p4", "TE One", "TE", "SF"),
    ]
    for season in seasons:
        for index, (player_id, player_name, position, team) in enumerate(players, start=1):
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": player_name,
                    "player_display_name": player_name,
                    "position": position,
                    "season": season,
                    "recent_team": team,
                    "games": 10 + index,
                    "attempts": 100 * (position == "QB"),
                    "passing_yards": 1000 * (position == "QB") + season % 10,
                    "passing_tds": 10 * (position == "QB"),
                    "passing_interceptions": 3 * (position == "QB"),
                    "carries": 100 * (position == "RB") + 20 * (position == "QB"),
                    "rushing_yards": 500 * (position == "RB") + 100 * (position == "QB"),
                    "rushing_tds": 5 * (position == "RB") + 1 * (position == "QB"),
                    "rushing_first_downs": 20 * (position in {"RB", "QB"}),
                    "targets": 80 * (position == "WR") + 50 * (position == "TE"),
                    "receptions": 50 * (position == "WR") + 30 * (position == "TE"),
                    "receiving_yards": 700 * (position == "WR") + 350 * (position == "TE"),
                    "receiving_tds": 6 * (position == "WR") + 3 * (position == "TE"),
                    "receiving_first_downs": 25 * (position in {"WR", "TE"}),
                    "passing_2pt_conversions": 0,
                    "rushing_2pt_conversions": 0,
                    "receiving_2pt_conversions": 0,
                    "punt_return_yards": 0,
                    "kickoff_return_yards": 0,
                    "special_teams_tds": 0,
                    "sack_fumbles_lost": 0,
                    "rushing_fumbles_lost": 1,
                    "receiving_fumbles_lost": 0,
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
