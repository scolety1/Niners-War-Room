from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.nfl_usage_target_label_service import derive_target_labels
from src.services.outcome_v2_historical_label_factory import (
    NOT_ENOUGH_INFORMATION,
    POSITION_THRESHOLDS,
    build_anchor_horizon_labels,
    build_season_outcome_labels,
    validation_summary_rows,
    write_historical_label_artifacts,
)


def _target_labels_fixture() -> pd.DataFrame:
    rows = []
    for season, rank in [
        (2021, 8),
        (2022, 30),
        (2023, 10),
        (2024, 40),
        (2025, 5),
    ]:
        rows.append(
            {
                "target_season": season,
                "player_id": "rb1",
                "player_name": "Runner One",
                "position": "RB",
                "recent_team": "SF",
                "next_season_nwr_points": 100.0 + season,
                "next_season_games": 16,
                "next_season_position_rank": rank,
            }
        )
    rows.append(
        {
            "target_season": 2021,
            "player_id": "qb1",
            "player_name": "Quarterback One",
            "position": "QB",
            "recent_team": "SF",
            "next_season_nwr_points": 250.0,
            "next_season_games": 4,
            "next_season_position_rank": 20,
        }
    )
    rows.append(
        {
            "target_season": 2021,
            "player_id": "te1",
            "player_name": "Tight End One",
            "position": "TE",
            "recent_team": "SF",
            "next_season_nwr_points": 90.0,
            "next_season_games": 10,
            "next_season_position_rank": 9,
        }
    )
    return pd.DataFrame(rows)


def _anchor_panel_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "season": 2020,
                "player_id": "rb1",
                "player_name": "Runner One",
                "position": "RB",
                "team": "SF",
            },
            {
                "season": 2023,
                "player_id": "rb1",
                "player_name": "Runner One",
                "position": "RB",
                "team": "SF",
            },
            {
                "season": 2020,
                "player_id": "missing1",
                "player_name": "Missing Player",
                "position": "WR",
                "team": "SF",
            },
        ]
    )


def test_position_threshold_map_matches_outcome_v2_contract() -> None:
    assert POSITION_THRESHOLDS == {
        "QB": (6, 12),
        "RB": (6, 12, 24, 36),
        "WR": (6, 12, 24, 36),
        "TE": (6, 12),
    }


def test_season_outcome_labels_use_thresholds_and_not_applicable_values() -> None:
    labels = build_season_outcome_labels(_target_labels_fixture())
    rb_2021 = labels[(labels["player_id"] == "rb1") & (labels["season"] == 2021)].iloc[0]
    qb_2021 = labels[labels["player_id"] == "qb1"].iloc[0]
    te_2021 = labels[labels["player_id"] == "te1"].iloc[0]

    assert rb_2021["top_6_hit"] == "miss"
    assert rb_2021["top_12_hit"] == "hit"
    assert rb_2021["top_24_hit"] == "hit"
    assert qb_2021["top_24_hit"] == "not_applicable"
    assert te_2021["top_36_hit"] == "not_applicable"
    assert qb_2021["availability_context"] == "limited_availability_1_to_4_games"
    assert labels["scoring_mode"].eq("exact_verified_first_downs").all()
    assert labels["model_input_allowed"].eq("no").all()
    assert labels["app_wiring_allowed"].eq("no").all()


def test_scoring_values_can_flow_from_existing_nfl_usage_target_label_service() -> None:
    player_stats = pd.DataFrame(
        [
            {
                "player_id": "p1",
                "player_display_name": "Runner One",
                "position": "RB",
                "season": 2024,
                "recent_team": "SF",
                "games": 10,
                "rushing_yards": 1000,
                "rushing_tds": 10,
                "receiving_yards": 100,
                "receiving_tds": 1,
                "rushing_first_downs": 50,
                "receiving_first_downs": 5,
                "receptions": 20,
            }
        ]
    )
    target_labels = derive_target_labels(player_stats, "test_run")
    season_labels = build_season_outcome_labels(target_labels)

    assert season_labels.iloc[0]["fantasy_points"] == 176.0
    assert season_labels.iloc[0]["top_12_hit"] == "hit"


def test_anchor_horizon_labels_use_a_plus_1_a_plus_2_and_a_plus_1_through_a_plus_5() -> None:
    season_labels = build_season_outcome_labels(_target_labels_fixture())
    anchors = build_anchor_horizon_labels(_anchor_panel_fixture(), season_labels)
    rb_2020 = anchors[(anchors["player_id"] == "rb1") & (anchors["anchor_season"] == 2020)].iloc[0]

    assert rb_2020["this_year_top_12_hit"] == "hit"
    assert rb_2020["next_year_top_12_hit"] == "miss"
    assert rb_2020["within_5y_top_6_hit"] == "hit"
    assert rb_2020["within_5y_top_12_hit"] == "hit"
    assert rb_2020["within_5y_top_24_hit"] == "hit"
    assert rb_2020["this_year_window_complete"]
    assert rb_2020["next_year_window_complete"]
    assert rb_2020["within_5y_window_complete"]
    assert rb_2020["censoring_status"] == "complete"


def test_censored_and_missing_target_windows_are_not_false_misses() -> None:
    season_labels = build_season_outcome_labels(_target_labels_fixture())
    anchors = build_anchor_horizon_labels(_anchor_panel_fixture(), season_labels)
    rb_2023 = anchors[(anchors["player_id"] == "rb1") & (anchors["anchor_season"] == 2023)].iloc[0]
    missing = anchors[anchors["player_id"] == "missing1"].iloc[0]

    assert rb_2023["this_year_top_12_hit"] == "miss"
    assert rb_2023["next_year_top_12_hit"] == "hit"
    assert rb_2023["within_5y_top_12_hit"] == NOT_ENOUGH_INFORMATION
    assert not rb_2023["within_5y_window_complete"]
    assert "right_censored" in rb_2023["censoring_status"]
    assert missing["this_year_top_12_hit"] == NOT_ENOUGH_INFORMATION
    assert missing["next_year_top_12_hit"] == NOT_ENOUGH_INFORMATION
    assert missing["within_5y_top_12_hit"] == NOT_ENOUGH_INFORMATION
    assert "missing_target_data" in missing["censoring_status"]


def test_validation_summary_reports_counts_and_guardrails() -> None:
    season_labels = build_season_outcome_labels(_target_labels_fixture())
    anchors = build_anchor_horizon_labels(_anchor_panel_fixture(), season_labels)
    summary = pd.DataFrame(
        validation_summary_rows(
            {
                "player_season_panel": 3,
                "player_week_panel": 10,
                "target_labels": 7,
                "joined_panel": 2,
            },
            season_labels,
            anchors,
            {
                "player_season_panel": Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\safe.csv"),
                "player_week_panel": Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\safe_week.csv"),
                "target_labels": Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\target.csv"),
                "joined_panel": Path(r"C:\NWR_SHARED_DATA\nfl_usage_cache\joined.csv"),
            },
        )
    )
    metrics = dict(zip(summary["metric"], summary["value"], strict=True))

    assert metrics["season_label_rows"] == "7"
    assert metrics["anchor_horizon_rows"] == "3"
    assert metrics["blocked_source_scan"] == "pass"
    assert metrics["model_input_allowed"] == "no"
    assert metrics["training_allowed"] == "no"


def test_write_artifacts_uses_supplied_output_root(
    tmp_path: Path,
) -> None:
    player_season_path = tmp_path / "player_season.csv"
    player_week_path = tmp_path / "player_week.csv"
    target_labels_path = tmp_path / "target_labels.csv"
    joined_path = tmp_path / "joined.csv"

    _anchor_panel_fixture().to_csv(player_season_path, index=False)
    _anchor_panel_fixture().assign(week=1).to_csv(player_week_path, index=False)
    _target_labels_fixture().to_csv(target_labels_path, index=False)
    pd.DataFrame({"player_id": ["rb1"]}).to_csv(joined_path, index=False)

    result = write_historical_label_artifacts(
        tmp_path / "out",
        {
            "player_season_panel": player_season_path,
            "player_week_panel": player_week_path,
            "target_labels": target_labels_path,
            "joined_panel": joined_path,
        },
    )

    assert result.validation_status == "GREEN_REVIEW_ONLY_LABELS_BUILT"
    assert result.season_rows == 7
    assert result.anchor_rows == 3
    assert result.season_label_path.exists()
    assert result.anchor_label_path.exists()
    assert result.manifest_path.exists()
    assert result.validation_path.exists()
