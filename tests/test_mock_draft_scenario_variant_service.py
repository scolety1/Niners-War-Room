from __future__ import annotations

import csv
import json

from src.services.mock_draft_combined_state_service import CombinedSimulatorState
from src.services.mock_draft_scenario_variant_service import (
    SCENARIO_NAMES,
    build_scenario_variant_outputs,
    write_scenario_variant_artifacts,
)


def _combined_state() -> CombinedSimulatorState:
    return CombinedSimulatorState(
        review_only=True,
        available_rows=(
            {
                "asset_id": "rookie:alpha",
                "player": "Alpha Rookie",
                "position": "RB",
                "source_label": "frozen_rookie",
                "draft_rank": 1,
                "stats_model_value": 0.0,
                "rank": "1",
                "tier": "Tier 1",
                "draft_action": "target",
                "warning_severity": "green",
                "draft_room_note": "Frozen note",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
            },
            {
                "asset_id": "rookie:beta",
                "player": "Beta Rookie",
                "position": "WR",
                "source_label": "frozen_rookie",
                "draft_rank": 2,
                "stats_model_value": 0.0,
                "rank": "2",
                "tier": "Tier 2",
                "draft_action": "manual_review",
                "warning_severity": "yellow",
                "draft_room_note": "Frozen beta note",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
            },
            {
                "asset_id": "declared_drop:gamma",
                "player": "Gamma Veteran",
                "position": "QB",
                "source_label": "declared_drop",
                "draft_rank": 90,
                "stats_model_value": 0.0,
                "rank": "",
                "tier": "",
                "draft_action": "",
                "warning_severity": "",
                "draft_room_note": "",
                "review_flags": "value_neutral|declared_drop",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
            },
            {
                "asset_id": "free_agent:delta",
                "player": "Delta Free Agent",
                "position": "RB",
                "source_label": "free_agent",
                "draft_rank": 120,
                "stats_model_value": 0.0,
                "rank": "",
                "tier": "",
                "draft_action": "",
                "warning_severity": "",
                "draft_room_note": "",
                "review_flags": "value_neutral|free_agent",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
            },
        ),
        pick_rows=(
            {
                "overall_pick": 1,
                "round": 1,
                "round_pick": 1,
                "pick_label": "1.01",
                "current_owner": "Opponent",
                "manager": "Other",
                "is_my_pick": False,
            },
            {
                "overall_pick": 2,
                "round": 1,
                "round_pick": 2,
                "pick_label": "1.02",
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "is_my_pick": True,
            },
        ),
        draft_state=None,
        manifest={},
        review_flags={},
        source_counts={"frozen_rookie": 2, "declared_drop": 1, "free_agent": 1},
        artifact_paths={},
    )


def test_scenario_variants_preserve_rookie_guidance_and_manual_tim_picks() -> None:
    outputs = build_scenario_variant_outputs(_combined_state(), tim_availability_limit=3)

    assert set(SCENARIO_NAMES) == {row["scenario_name"] for row in outputs.pick_rows}
    tim_rows = [row for row in outputs.pick_rows if row["selection_mode"] == "Tim_review_pick"]
    assert len(tim_rows) == len(SCENARIO_NAMES)
    assert all(row["selected_player"] == "" for row in tim_rows)
    beta_rows = [
        row for row in outputs.tim_availability_rows if row["player"] == "Beta Rookie"
    ]
    assert beta_rows
    assert all(row["rank"] == "2" for row in beta_rows)
    assert all(row["tier"] == "Tier 2" for row in beta_rows)
    assert all(row["draft_action"] == "manual_review" for row in beta_rows)
    assert all(row["warning_severity"] == "yellow" for row in beta_rows)


def test_scenarios_do_not_create_scores_or_remove_value_neutral_flags() -> None:
    outputs = build_scenario_variant_outputs(_combined_state(), tim_availability_limit=4)

    assert "do not invent numeric NWR scores" in outputs.manifest["nwr_score_policy"]
    assert all(
        row["stats_model_value"] == 0.0
        for row in outputs.tim_availability_rows
        if row["player"] in {"Alpha Rookie", "Beta Rookie"}
    )
    value_rows = [
        row
        for row in outputs.tim_availability_rows
        if row["player"] in {"Gamma Veteran", "Delta Free Agent"}
    ]
    assert value_rows
    assert all(row["value_status"] == "value_neutral" for row in value_rows)
    assert all("value_neutral" in str(row["review_flags"]) for row in value_rows)
    assert "not ranked against rookies" in outputs.manifest["value_neutral_policy"]


def test_fake_market_timing_variant_is_behavior_only() -> None:
    outputs = build_scenario_variant_outputs(
        _combined_state(),
        fake_market_rows=[
            {
                "asset_id": "declared_drop:gamma",
                "player": "Gamma Veteran",
                "source_name": "fake_contract_fixture",
                "source_type": "synthetic_market_timing",
                "market_adp": "1.0",
                "nwr_quality_score": "99",
            }
        ],
        tim_availability_limit=3,
        opponent_lookahead=1,
    )

    fake_first_pick = next(
        row
        for row in outputs.pick_rows
        if row["scenario_name"] == "fake_market_timing_behavior"
        and row["overall_pick"] == 1
    )
    assert fake_first_pick["selected_player"] == "Gamma Veteran"
    assert fake_first_pick["market_context_used"] is True
    assert fake_first_pick["stats_model_value"] == 0.0
    assert fake_first_pick["value_status"] == "value_neutral"
    assert "behavior notes only" in outputs.manifest["market_policy"]


def test_variant_artifacts_are_local_review_outputs(tmp_path) -> None:
    outputs = write_scenario_variant_artifacts(
        build_scenario_variant_outputs(_combined_state(), tim_availability_limit=2),
        output_root=tmp_path / "scenario_variants_20260617",
    )

    assert outputs.artifact_paths["pick_by_pick"].exists()
    assert outputs.artifact_paths["tim_availability"].exists()
    assert outputs.artifact_paths["behavior_notes"].exists()
    assert outputs.artifact_paths["manifest"].exists()
    with outputs.artifact_paths["tim_availability"].open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    manifest = json.loads(outputs.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert manifest["scenario_count"] == 4
    assert manifest["promotion_status"] == "local_review_output_only_not_app_wired_not_promoted"
