from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.rb_elite_5y_outcome_diagnostic_service import (
    NOT_ENOUGH_INFORMATION,
    build_rb_diagnostic_dataset,
    run_rb_elite_5y_diagnostic,
    split_error_and_recommendation_rows,
    validate_source_paths,
)


def test_rb_t10_within_5y_target_is_constructed_from_future_finishes() -> None:
    anchors = pd.DataFrame([_anchor("p1", 2012)])
    seasons = pd.DataFrame(
        [
            _season("p1", 2012, finish=30, points=80, games=12),
            _season("p1", 2013, finish=20, points=90, games=12),
            _season("p1", 2014, finish=15, points=110, games=12),
            _season("p1", 2015, finish=10, points=150, games=12),
            _season("p1", 2016, finish=14, points=120, games=12),
            _season("p1", 2017, finish=18, points=100, games=12),
        ]
    )

    dataset = build_rb_diagnostic_dataset(anchors, seasons)
    row = dataset.iloc[0]

    assert row["rb_t6_within_5y_hit"] == "miss"
    assert row["rb_t10_within_5y_hit"] == "hit"
    assert row["rb_t12_within_5y_hit"] == "hit"
    assert bool(row["rb_t10_within_5y_window_complete"]) is True


def test_incomplete_5y_window_stays_censored_not_miss() -> None:
    anchors = pd.DataFrame([_anchor("p1", 2012)])
    seasons = pd.DataFrame(
        [
            _season("p1", 2012, finish=30, points=80, games=12),
            _season("p1", 2013, finish=20, points=90, games=12),
            _season("p1", 2014, finish=15, points=110, games=12),
            # 2015 is intentionally missing.
            _season("p1", 2016, finish=14, points=120, games=12),
            _season("p1", 2017, finish=18, points=100, games=12),
        ]
    )

    dataset = build_rb_diagnostic_dataset(anchors, seasons)
    row = dataset.iloc[0]

    assert row["rb_t10_within_5y_hit"] == NOT_ENOUGH_INFORMATION
    assert bool(row["rb_t10_within_5y_window_complete"]) is False
    assert row["rb_t10_within_5y_censoring_status"] == "missing_target_data_not_fabricated"


def test_last_materially_active_and_missed_prior_flags_use_non_medical_language() -> None:
    anchors = pd.DataFrame([_anchor("p1", 2020)])
    seasons = pd.DataFrame(
        [
            _season("p1", 2018, finish=15, points=130, games=12),
            _season("p1", 2019, finish=90, points=0, games=0),
            _season("p1", 2020, finish=80, points=20, games=2),
            _season("p1", 2021, finish=50, points=60, games=6),
            _season("p1", 2022, finish=40, points=70, games=7),
            _season("p1", 2023, finish=30, points=80, games=8),
            _season("p1", 2024, finish=25, points=85, games=8),
            _season("p1", 2025, finish=28, points=82, games=8),
        ]
    )

    dataset = build_rb_diagnostic_dataset(anchors, seasons)
    row = dataset.iloc[0]

    assert int(row["last_materially_active_season"]) == 2018
    assert row["missed_prior_season_flag"] == "true"
    assert row["limited_recent_sample_flag"] == "true"
    assert "medical" in row["availability_caveat"]
    forbidden_terms = ("injury", "healthy", "recovery", "medical_projection")
    assert not any(
        term in column.lower()
        for term in forbidden_terms
        for column in dataset.columns
    )


def test_diagnostic_model_outputs_remain_review_only_recommendations() -> None:
    anchors = []
    seasons = []
    for season in range(2012, 2020):
        for index in range(14):
            player_id = f"rb-{index}"
            anchors.append(_anchor(player_id, season, player_name=f"RB {index}"))
            seasons.append(
                _season(
                    player_id,
                    season,
                    finish=index + 20,
                    points=80 + index,
                    games=12,
                    player_name=f"RB {index}",
                )
            )
    for season in range(2020, 2025):
        for index in range(14):
            player_id = f"rb-{index}"
            seasons.append(
                _season(
                    player_id,
                    season,
                    finish=5 if index < 4 else 30,
                    points=180 if index < 4 else 80,
                    games=12,
                    player_name=f"RB {index}",
                )
            )

    dataset = build_rb_diagnostic_dataset(pd.DataFrame(anchors), pd.DataFrame(seasons))
    _summary, _metrics, _calibration, combined = run_rb_elite_5y_diagnostic(dataset)
    _error_rows, recommendations = split_error_and_recommendation_rows(combined)

    assert recommendations
    assert {row["row_type"] for row in recommendations} == {"recommendation"}
    assert {row["review_only"] for row in recommendations} == {"true"}
    assert {row["app_wiring_allowed"] for row in recommendations} == {"false"}
    assert {row["model_use_allowed"] for row in recommendations} == {"false"}


def test_blocked_source_tokens_are_detected() -> None:
    rows = validate_source_paths({"blocked_adp": Path(r"C:\tmp\adp_source.csv")})

    assert rows[0]["blocked_source_scan"] == "blocked"


def _anchor(player_id: str, season: int, player_name: str = "Example RB") -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "RB",
        "anchor_season": season,
        "team": "SF",
    }


def _season(
    player_id: str,
    season: int,
    *,
    finish: int,
    points: float,
    games: int,
    player_name: str = "Example RB",
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "RB",
        "season": season,
        "team": "SF",
        "scoring_mode": "exact_verified_first_downs",
        "fantasy_points": points,
        "position_finish": finish,
        "games_played": games,
    }
