from __future__ import annotations

import pandas as pd

from src.services.rb_intermediate_5y_diagnostic_service import (
    NOT_ENOUGH_INFORMATION,
    build_rb_intermediate_dataset,
    run_rb_intermediate_5y_diagnostic,
)


def test_intermediate_targets_are_built_from_position_finish() -> None:
    dataset = build_rb_intermediate_dataset(
        _anchor_rows(player_count=2, seasons=range(2012, 2014)),
        _season_rows(player_count=2, seasons=range(2012, 2020)),
    )
    row = dataset[(dataset["player_id"] == "rb-0") & (dataset["anchor_season"] == 2012)].iloc[
        0
    ]

    assert bool(row["rb_t15_within_5y_window_complete"]) is True
    assert row["rb_t15_within_5y_hit"] == "hit"
    assert row["rb_t18_within_5y_hit"] == "hit"
    assert row["rb_t24_within_5y_hit"] == "hit"


def test_incomplete_five_year_windows_are_censored_not_misses() -> None:
    dataset = build_rb_intermediate_dataset(
        _anchor_rows(player_count=1, seasons=range(2018, 2020)),
        _season_rows(player_count=1, seasons=range(2018, 2021)),
    )
    recent = dataset[dataset["anchor_season"] == 2018].iloc[0]

    assert bool(recent["rb_t18_within_5y_window_complete"]) is False
    assert recent["rb_t18_within_5y_hit"] == NOT_ENOUGH_INFORMATION
    assert recent["rb_t18_within_5y_hit"] != 0
    assert recent["rb_t18_within_5y_hit"] is not False


def test_last_materially_active_season_and_sample_flags_are_factual_only() -> None:
    seasons = pd.DataFrame(
        [
            _season_row("rb-1", 2019, position_finish=20, games=12, points=140),
            _season_row("rb-1", 2020, position_finish=80, games=2, points=20),
            _season_row("rb-1", 2021, position_finish=81, games=0, points=0),
            _season_row("rb-1", 2022, position_finish=82, games=1, points=5),
            _season_row("rb-1", 2023, position_finish=83, games=1, points=5),
            _season_row("rb-1", 2024, position_finish=84, games=1, points=5),
            _season_row("rb-1", 2025, position_finish=85, games=1, points=5),
            _season_row("rb-1", 2026, position_finish=86, games=1, points=5),
        ]
    )
    anchors = pd.DataFrame(
        [
            {
                "player_id": "rb-1",
                "player_name": "RB One",
                "position": "RB",
                "anchor_season": 2022,
                "team": "SF",
            }
        ]
    )
    dataset = build_rb_intermediate_dataset(anchors, seasons)
    row = dataset.iloc[0]

    assert row["last_materially_active_season"] == 2019
    assert row["limited_recent_sample_flag"] == "true"
    assert row["missed_prior_season_flag"] == "true"
    assert row["medical_inference_used"] == "false"
    assert "healthy" not in row["availability_caveat"].lower()


def test_diagnostic_outputs_intermediate_recommendations_without_app_wiring() -> None:
    dataset = build_rb_intermediate_dataset(
        _anchor_rows(player_count=60, seasons=range(2012, 2020)),
        _season_rows(player_count=60, seasons=range(2012, 2025)),
    )
    _target_summary, metrics, calibration, error_slices, recommendations = (
        run_rb_intermediate_5y_diagnostic(dataset)
    )

    assert {row["field_id"] for row in recommendations} == {
        "RB_T12_WITHIN_5Y",
        "RB_T15_WITHIN_5Y",
        "RB_T18_WITHIN_5Y",
        "RB_T20_WITHIN_5Y",
        "RB_T24_WITHIN_5Y",
    }
    assert metrics
    assert calibration
    assert error_slices
    assert {row["app_wiring_allowed"] for row in recommendations} == {"false"}
    assert {row["display_only"] for row in recommendations} == {"true"}
    assert {
        row["recommendation_status"] for row in recommendations
    } <= {"safe_for_display_candidate", "test_only", "keep_blocked"}


def _anchor_rows(player_count: int, seasons: range) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": f"rb-{player}",
                "player_name": f"RB {player}",
                "position": "RB",
                "anchor_season": season,
                "team": "SF",
            }
            for season in seasons
            for player in range(player_count)
        ]
    )


def _season_rows(player_count: int, seasons: range) -> pd.DataFrame:
    rows = []
    for season in seasons:
        for player in range(player_count):
            finish = (player % 36) + 1
            rows.append(
                _season_row(
                    f"rb-{player}",
                    season,
                    position_finish=finish,
                    games=12 + (player % 5),
                    points=240 - finish * 3,
                )
            )
    return pd.DataFrame(rows)


def _season_row(
    player_id: str,
    season: int,
    *,
    position_finish: int,
    games: int,
    points: float,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_id.upper(),
        "position": "RB",
        "season": season,
        "team": "SF",
        "scoring_mode": "exact_verified_first_downs",
        "fantasy_points": points,
        "position_finish": position_finish,
        "games_played": games,
        "top_6_hit": "hit" if position_finish <= 6 else "miss",
        "top_12_hit": "hit" if position_finish <= 12 else "miss",
        "top_24_hit": "hit" if position_finish <= 24 else "miss",
        "top_36_hit": "hit" if position_finish <= 36 else "miss",
        "data_quality_status": "complete_factual_player_stats",
        "approval_status": "review_only_historical_labels",
        "model_input_allowed": "no",
        "training_allowed": "no",
        "app_wiring_allowed": "no",
    }
