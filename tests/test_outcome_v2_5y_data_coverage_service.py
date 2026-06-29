from __future__ import annotations

import pandas as pd

from src.services.outcome_v2_5y_data_coverage_service import (
    build_5y_coverage_summary,
    build_anchor_horizon_labels,
    build_season_outcome_labels,
    calculate_nwr_fantasy_points,
)


def test_calculate_nwr_points_uses_first_downs_returns_and_fumbles() -> None:
    frame = pd.DataFrame(
        [
            {
                "passing_yards": 300,
                "passing_tds": 2,
                "passing_interceptions": 1,
                "passing_2pt_conversions": 1,
                "rushing_yards": 40,
                "rushing_tds": 1,
                "rushing_first_downs": 5,
                "rushing_2pt_conversions": 0,
                "receiving_yards": 30,
                "receiving_tds": 1,
                "receiving_first_downs": 2,
                "receiving_2pt_conversions": 1,
                "punt_return_yards": 30,
                "kickoff_return_yards": 60,
                "special_teams_tds": 1,
                "sack_fumbles_lost": 1,
                "rushing_fumbles_lost": 1,
                "receiving_fumbles_lost": 1,
            }
        ]
    )

    points = calculate_nwr_fantasy_points(frame)

    assert round(float(points.iloc[0]), 4) == 40.8


def test_horizon_labels_do_not_convert_missing_future_to_miss() -> None:
    rows = [
        _stat_row("p1", "Example QB", "QB", 2012, 200),
        _stat_row("p1", "Example QB", "QB", 2013, 210),
        _stat_row("p1", "Example QB", "QB", 2014, 220),
        # 2015 missing on purpose.
        _stat_row("p1", "Example QB", "QB", 2016, 230),
        _stat_row("p1", "Example QB", "QB", 2017, 240),
    ]
    season_labels = build_season_outcome_labels(pd.DataFrame(rows))

    anchor_labels = build_anchor_horizon_labels(season_labels)
    anchor_2012 = anchor_labels[
        (anchor_labels["player_id"] == "p1")
        & (anchor_labels["anchor_season"] == 2012)
    ].iloc[0]

    assert anchor_2012["this_year_window_complete"]
    assert anchor_2012["next_year_window_complete"]
    assert not anchor_2012["within_5y_window_complete"]
    assert anchor_2012["within_5y_top_12_hit"] == "Not enough information"
    assert "within_5y_missing_or_right_censored" in anchor_2012["censoring_status"]


def test_5y_complete_window_records_hit_when_any_future_season_hits() -> None:
    rows = []
    for season in range(2012, 2018):
        rows.append(_stat_row("p1", "Alpha RB", "RB", season, 100 + season))
        rows.append(_stat_row("p2", "Beta RB", "RB", season, 90 + season))
        rows.append(_stat_row("p3", "Gamma RB", "RB", season, 10))
    season_labels = build_season_outcome_labels(pd.DataFrame(rows))

    anchor_labels = build_anchor_horizon_labels(season_labels)
    anchor_2012 = anchor_labels[
        (anchor_labels["player_id"] == "p1")
        & (anchor_labels["anchor_season"] == 2012)
    ].iloc[0]

    assert anchor_2012["within_5y_window_complete"]
    assert anchor_2012["within_5y_top_6_hit"] == "hit"
    assert anchor_2012["model_input_allowed"] == "no"
    assert anchor_2012["training_allowed"] == "no"
    assert anchor_2012["app_wiring_allowed"] == "no"


def test_coverage_summary_keeps_rows_review_only_and_position_specific() -> None:
    rows = []
    for season in range(2012, 2018):
        rows.append(_stat_row("p1", "Alpha TE", "TE", season, 80))
        rows.append(_stat_row("p2", "Beta TE", "TE", season, 10))
    season_labels = build_season_outcome_labels(pd.DataFrame(rows))
    anchor_labels = build_anchor_horizon_labels(season_labels)

    summary = build_5y_coverage_summary(anchor_labels)

    te_t6 = summary[
        (summary["position"] == "TE") & (summary["threshold"] == "T6")
    ].iloc[0]
    assert te_t6["complete_5y_rows_after"] == 2
    assert te_t6["app_validation_note"] == "coverage_only_not_validated"
    assert not ((summary["position"] == "TE") & (summary["threshold"] == "T24")).any()


def _stat_row(
    player_id: str,
    player_name: str,
    position: str,
    season: int,
    rushing_yards: float,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "player_display_name": player_name,
        "position": position,
        "season": season,
        "recent_team": "SF",
        "games": 17,
        "passing_yards": 0,
        "passing_tds": 0,
        "passing_interceptions": 0,
        "passing_first_downs": 0,
        "passing_2pt_conversions": 0,
        "carries": 1,
        "rushing_yards": rushing_yards,
        "rushing_tds": 0,
        "rushing_first_downs": 0,
        "rushing_2pt_conversions": 0,
        "rushing_fumbles_lost": 0,
        "receptions": 0,
        "receiving_yards": 0,
        "receiving_tds": 0,
        "receiving_first_downs": 0,
        "receiving_2pt_conversions": 0,
        "receiving_fumbles_lost": 0,
        "sack_fumbles_lost": 0,
        "punt_return_yards": 0,
        "kickoff_return_yards": 0,
        "special_teams_tds": 0,
    }
