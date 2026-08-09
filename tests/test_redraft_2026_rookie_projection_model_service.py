from __future__ import annotations

import pandas as pd

from src.services.redraft_2026_rookie_projection_model_service import (
    MODEL_STAT_COLUMNS,
    aggregate_backtest,
    attach_exact_identities,
    build_current_rookie_candidate,
    normalize_name,
    temporal_backtest,
    uncertainty_from_predictions,
)


def _stat_row(**overrides: float) -> dict[str, float]:
    row = {column: 0.0 for column in MODEL_STAT_COLUMNS}
    row.update(overrides)
    return row


def _history() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for season in range(2012, 2016):
        for index in range(2):
            rows.append(
                {
                    "season": season,
                    "player_id": f"{season}-{index}",
                    "pfr_player_name": f"Rookie {season}-{index}",
                    "position": "RB",
                    "round": 1,
                    "pick": index + 1,
                    **_stat_row(
                        games=10 + index,
                        carries=100 + (10 * index),
                        rushing_yards=500 + (100 * index),
                        rushing_tds=4 + index,
                    ),
                }
            )
    rows.append(
        {
            "season": 2016,
            "player_id": "2016-1",
            "pfr_player_name": "Target Rookie",
            "position": "RB",
            "round": 1,
            "pick": 1,
            **_stat_row(games=12, carries=120, rushing_yards=650, rushing_tds=5),
        }
    )
    return pd.DataFrame(rows)


def test_name_normalization_is_exact_and_suffix_safe() -> None:
    assert normalize_name("Ted Hurst III") == normalize_name("Ted Hurst")
    assert normalize_name("De'Zhaun Stribling") == "dezhaunstribling"


def test_exact_identity_prefers_pfr_bridge_and_records_method() -> None:
    players = pd.DataFrame(
        [
            {
                "gsis_id": "00-1",
                "display_name": "Ted Hurst III",
                "pfr_id": "HursTe00",
                "position": "WR",
            }
        ]
    )
    draft = pd.DataFrame(
        [
            {
                "pfr_player_id": "HursTe00",
                "pfr_player_name": "Ted Hurst",
                "position": "WR",
            }
        ]
    )
    result = attach_exact_identities(draft, players).iloc[0]
    assert result["player_id"] == "00-1"
    assert result["identity_method"] == "EXACT_PFR_ID_BRIDGE"
    assert not bool(result["identity_conflict"])


def test_temporal_backtest_uses_only_prior_classes_and_component_medians() -> None:
    predictions, summaries = temporal_backtest(_history(), seasons=[2016])
    prediction = predictions.iloc[0]
    assert prediction["training_max_season"] == 2015
    assert prediction["cohort_scope"] == "POSITION_ROUND"
    assert prediction["cohort_rows"] == 8
    # Historical medians: 550 rushing yards and 4.5 touchdowns = 82 half-PPR points.
    assert prediction["predicted_points"] == 82.0
    assert summaries.iloc[-1]["season"] == 2016


def test_current_position_conflict_blocks_instead_of_coercing_projection() -> None:
    draft = pd.DataFrame(
        [
            {
                "season": 2026,
                "round": 5,
                "pick": 159,
                "team": "MIN",
                "gsis_id": None,
                "pfr_player_id": "BredMa00",
                "pfr_player_name": "Max Bredeson",
                "position": "TE",
                "college": "Michigan",
                "age": 23,
            }
        ]
    )
    players = pd.DataFrame(
        [
            {
                "gsis_id": "00-5",
                "display_name": "Max Bredeson",
                "pfr_id": "BredMa00",
                "position": "RB",
                "latest_team": "MIN",
                "status": "ACT",
                "rookie_season": 2026,
                "last_season": 2026,
            }
        ]
    )
    history = _history()
    result = build_current_rookie_candidate(
        draft,
        players,
        history,
        season=2026,
        source_as_of="2026-07-30",
        uncertainty_by_position={"TE": 20.0},
    )
    assert result.projections.empty
    assert len(result.blocked) == 1
    assert "position conflicts" in result.blocked.iloc[0]["block_reason"]


def test_uncertainty_and_aggregate_are_position_specific() -> None:
    predictions, _ = temporal_backtest(_history(), seasons=[2016])
    uncertainty = uncertainty_from_predictions(predictions)
    aggregate = aggregate_backtest(predictions)
    assert set(uncertainty) == {"RB"}
    assert uncertainty["RB"] >= 0
    assert aggregate.iloc[0]["position"] == "RB"
