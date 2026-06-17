from __future__ import annotations

import csv
import json

from src.services.mock_draft_scenario_comparison_service import (
    build_scenario_comparison_kit,
    write_scenario_comparison_artifacts,
)


def _availability_rows() -> list[dict[str, object]]:
    return [
        {
            "scenario_name": "baseline_placeholder_behavior",
            "overall_pick": 2,
            "pick_label": "1.02",
            "availability_rank": 1,
            "asset_id": "rookie:alpha",
            "player": "Alpha Rookie",
            "position": "RB",
            "player_source": "frozen_rookie",
            "rank": "1",
            "tier": "Tier 1",
            "draft_action": "target",
            "warning_severity": "green",
            "review_flags": "frozen_rookie_guidance_read_only",
            "nwr_score_status": "no_numeric_score_exposed_guidance_only",
            "value_status": "frozen_rookie_guidance_no_numeric_score",
            "stats_model_value": 0.0,
        },
        {
            "scenario_name": "rookie_front_run_behavior",
            "overall_pick": 2,
            "pick_label": "1.02",
            "availability_rank": 1,
            "asset_id": "rookie:alpha",
            "player": "Alpha Rookie",
            "position": "RB",
            "player_source": "frozen_rookie",
            "rank": "1",
            "tier": "Tier 1",
            "draft_action": "target",
            "warning_severity": "green",
            "review_flags": "frozen_rookie_guidance_read_only",
            "nwr_score_status": "no_numeric_score_exposed_guidance_only",
            "value_status": "frozen_rookie_guidance_no_numeric_score",
            "stats_model_value": 0.0,
        },
        {
            "scenario_name": "baseline_placeholder_behavior",
            "overall_pick": 2,
            "pick_label": "1.02",
            "availability_rank": 2,
            "asset_id": "rookie:beta",
            "player": "Beta Rookie",
            "position": "WR",
            "player_source": "frozen_rookie",
            "rank": "2",
            "tier": "Tier 2",
            "draft_action": "manual_review",
            "warning_severity": "yellow",
            "review_flags": "frozen_rookie_guidance_read_only",
            "nwr_score_status": "no_numeric_score_exposed_guidance_only",
            "value_status": "frozen_rookie_guidance_no_numeric_score",
            "stats_model_value": 0.0,
        },
        {
            "scenario_name": "baseline_placeholder_behavior",
            "overall_pick": 2,
            "pick_label": "1.02",
            "availability_rank": 3,
            "asset_id": "free_agent:gamma",
            "player": "Gamma Free Agent",
            "position": "RB",
            "player_source": "free_agent",
            "review_flags": "value_neutral|free_agent",
            "nwr_score_status": "not_populated_from_snapshot_rank",
            "value_status": "value_neutral",
            "stats_model_value": 0.0,
        },
    ]


def _pick_rows() -> list[dict[str, object]]:
    return [
        {
            "scenario_name": "baseline_placeholder_behavior",
            "overall_pick": 2,
            "pick_label": "1.02",
            "selection_mode": "Tim_review_pick",
        },
        {
            "scenario_name": "rookie_front_run_behavior",
            "overall_pick": 2,
            "pick_label": "1.02",
            "selection_mode": "Tim_review_pick",
        },
    ]


def test_comparison_labels_stable_and_fragile_availability_not_value() -> None:
    kit = build_scenario_comparison_kit(
        availability_rows=_availability_rows(),
        pick_rows=_pick_rows(),
    )

    assert len(kit.matrix_rows) == 2
    assert kit.matrix_rows[0]["tim_manual_review_only"] is True
    assert len(kit.stable_rookie_rows) == 1
    assert kit.stable_rookie_rows[0]["player"] == "Alpha Rookie"
    assert kit.stable_rookie_rows[0]["availability_label"] == (
        "stable_available_all_scenarios"
    )
    assert len(kit.fragile_rookie_rows) == 1
    assert kit.fragile_rookie_rows[0]["player"] == "Beta Rookie"
    assert "not NWR quality labels" in kit.manifest["availability_label_policy"]


def test_value_neutral_visibility_is_not_ranked_against_rookies() -> None:
    kit = build_scenario_comparison_kit(
        availability_rows=_availability_rows(),
        pick_rows=_pick_rows(),
    )

    assert len(kit.value_neutral_rows) == 1
    row = kit.value_neutral_rows[0]
    assert row["value_status"] == "value_neutral"
    assert "visibility only" in row["visibility_only_note"].lower()
    assert row["stats_model_value"] == 0.0
    assert "not ranked against frozen rookies" in kit.manifest["value_neutral_policy"]


def test_comparison_preserves_guidance_and_does_not_invent_scores() -> None:
    kit = build_scenario_comparison_kit(
        availability_rows=_availability_rows(),
        pick_rows=_pick_rows(),
    )

    stable = kit.stable_rookie_rows[0]
    assert stable["rank"] == "1"
    assert stable["tier"] == "Tier 1"
    assert stable["draft_action"] == "target"
    assert stable["warning_severity"] == "green"
    assert stable["stats_model_value"] == 0.0
    assert "does not invent numeric NWR scores" in kit.manifest["nwr_score_policy"]
    assert "manual-review only" in kit.manifest["tim_pick_policy"]


def test_write_scenario_comparison_artifacts_are_local_review_outputs(tmp_path) -> None:
    kit = write_scenario_comparison_artifacts(
        build_scenario_comparison_kit(
            availability_rows=_availability_rows(),
            pick_rows=_pick_rows(),
        ),
        output_root=tmp_path / "scenario_comparison_20260617",
    )

    assert kit.artifact_paths["scenario_matrix"].exists()
    assert kit.artifact_paths["stable_rookies"].exists()
    assert kit.artifact_paths["fragile_rookies"].exists()
    assert kit.artifact_paths["value_neutral_visibility"].exists()
    with kit.artifact_paths["scenario_matrix"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    manifest = json.loads(kit.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert manifest["promotion_status"] == "local_review_output_only_not_app_wired_not_promoted"
