from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.nfl_usage_target_label_service import (
    APP_WIRING_ALLOWED,
    MODEL_INPUT_ALLOWED,
    SCORING_FORMULA,
    TARGET_LABELS,
    coverage_summary_rows,
    derive_target_labels,
    target_manifest_rows,
    target_source_audit_rows,
)


def _player_stats_fixture() -> pd.DataFrame:
    return pd.DataFrame(
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
            },
            {
                "player_id": "p2",
                "player_display_name": "Receiver Two",
                "position": "WR",
                "season": 2024,
                "recent_team": "SF",
                "games": 10,
                "receiving_yards": 900,
                "receiving_tds": 6,
                "receiving_first_downs": 45,
                "receptions": 70,
            },
        ]
    )


def test_target_scoring_formulas_are_documented_and_non_ppr() -> None:
    assert SCORING_FORMULA["passing_yards"] == "passing_yards / 30"
    assert (
        SCORING_FORMULA["rushing_receiving_first_downs"]
        == "(rushing_first_downs + receiving_first_downs) * 0.4"
    )
    assert "receptions" not in SCORING_FORMULA


def test_target_labels_derive_from_factual_player_stats() -> None:
    labels = derive_target_labels(_player_stats_fixture(), "test_run")
    runner = labels.loc[labels["player_id"] == "p1"].iloc[0]

    assert runner["next_season_nwr_points"] == 176.0
    assert runner["next_season_nwr_points_per_game"] == 17.6
    assert runner["next_season_top_rb12"] == 1
    assert runner["next_season_starter_level_by_position"] == "RB1"
    assert labels["model_input_allowed"].eq(MODEL_INPUT_ALLOWED).all()
    assert labels["app_wiring_allowed"].eq(APP_WIRING_ALLOWED).all()


def test_target_source_audit_blocks_market_rank_projection_and_cfbd() -> None:
    audit = pd.DataFrame(target_source_audit_rows("test_run"))
    blocked_names = set(audit.loc[audit["allowed_as_target"] == "no", "source_name"])

    assert {
        "ADP",
        "market rank",
        "DynastyProcess rank/value",
        "projections",
        "CFBD",
    } <= blocked_names
    assert audit["model_input_allowed"].eq("no").all()
    assert audit["app_wiring_allowed"].eq("no").all()


def test_target_manifest_and_coverage_summary_load() -> None:
    labels = derive_target_labels(_player_stats_fixture(), "test_run")
    manifest = pd.DataFrame(target_manifest_rows(labels, "test_run", Path("shared.csv")))
    coverage = pd.DataFrame(coverage_summary_rows(labels, "test_run", Path("shared.csv")))

    assert set(TARGET_LABELS) <= set(manifest["label_name"])
    assert not coverage.empty
    assert manifest["target_status"].eq("APPROVED_REVIEW_ONLY_TARGET_LABEL").all()
    assert manifest["model_input_allowed"].eq("no").all()
    assert coverage["app_wiring_allowed"].eq("no").all()
