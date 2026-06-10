from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_edge_evaluation_harness_service import (
    HARNESS_ROW_HEADER,
    OUTCOME_USE_POLICY,
    build_model_edge_evaluation_harness,
    write_model_edge_evaluation_harness_outputs,
)


def test_model_edge_harness_builds_leakage_safe_rows() -> None:
    result = build_model_edge_evaluation_harness()

    assert result.rows
    first = result.rows[0]
    assert first["evaluation_lane"] == "historical_rookie_replay"
    assert first["outcome_use_policy"] == OUTCOME_USE_POLICY
    assert "active_private_score_input" in str(first["blocked_use"])
    assert "draft_recommendation" in str(first["blocked_use"])
    assert first["feature_leakage_status"] == "no_future_outcome_inputs_detected"
    assert "outcome_columns_present_for_after_the_fact_review" in str(
        first["leakage_risk_flags"]
    )


def test_model_edge_harness_includes_rank_pick_and_position_buckets() -> None:
    result = build_model_edge_evaluation_harness()

    assert {row["rank_bucket"] for row in result.rows} >= {"top_5", "top_20"}
    assert {row["pick_range_bucket"] for row in result.rows} >= {
        "round_1",
        "round_2",
        "day_3_or_later",
    }
    assert {row["position_rank_bucket"] for row in result.rows} >= {
        "position_top_3",
        "position_outside_top_10",
    }


def test_model_edge_harness_maps_league_outcome_labels() -> None:
    result = build_model_edge_evaluation_harness()
    labels = {row["league_outcome_label"] for row in result.rows}

    assert "Difference-maker" in labels
    assert "Strong starter" in labels
    assert "Useful starter/flex" in labels
    assert "Bust" in labels
    assert "Too early to call" in labels


def test_model_edge_harness_position_summary_supports_position_analysis() -> None:
    result = build_model_edge_evaluation_harness()
    positions = {row["position"] for row in result.position_summary_rows}

    assert positions == {"QB", "RB", "TE", "WR"}
    assert all("harness_version" in row for row in result.position_summary_rows)
    assert any(
        "no-TE-premium" in str(row["primary_read"])
        for row in result.position_summary_rows
        if row["position"] == "TE"
    )


def test_model_edge_harness_outputs_write_without_touching_active_rankings(
    tmp_path: Path,
) -> None:
    active_path = Path(
        "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
    )
    before = active_path.read_bytes()

    paths = write_model_edge_evaluation_harness_outputs(output_root=tmp_path)

    assert _header(paths["rows"]) == HARNESS_ROW_HEADER
    assert active_path.read_bytes() == before


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
