from __future__ import annotations

import csv
import json

from src.services.mock_draft_combined_state_service import CombinedSimulatorState
from src.services.mock_draft_run_report_service import (
    build_mock_draft_run_report,
    write_mock_draft_run_report_artifacts,
)


def _combined_state() -> CombinedSimulatorState:
    available_rows = (
        {
            "asset_id": "frozen_rookie:alpha:rank1",
            "player": "Alpha Rookie",
            "position": "RB",
            "source_label": "frozen_rookie",
            "draft_rank": 1,
            "stats_model_value": 0.0,
            "rank": "1",
            "tier": "Tier 1",
            "draft_action": "priority_review",
            "warning_severity": "green",
            "draft_room_note": "Frozen note",
            "review_flags": "frozen_rookie_guidance_read_only",
            "nwr_score_status": "no_numeric_score_exposed_guidance_only",
            "value_status": "frozen_rookie_guidance_no_numeric_score",
        },
        {
            "asset_id": "frozen_rookie:beta:rank2",
            "player": "Beta Rookie",
            "position": "WR",
            "source_label": "frozen_rookie",
            "draft_rank": 2,
            "stats_model_value": 0.0,
            "rank": "2",
            "tier": "Tier 2",
            "draft_action": "manual_review",
            "warning_severity": "yellow",
            "draft_room_note": "Frozen second note",
            "review_flags": "frozen_rookie_guidance_read_only",
            "nwr_score_status": "no_numeric_score_exposed_guidance_only",
            "value_status": "frozen_rookie_guidance_no_numeric_score",
        },
        {
            "asset_id": "declared_drop:brockpurdy:seq1:instance1",
            "player": "Brock Purdy",
            "position": "QB",
            "source_label": "declared_drop",
            "draft_rank": 90,
            "stats_model_value": 0.0,
            "rank": "",
            "tier": "",
            "draft_action": "",
            "warning_severity": "",
            "draft_room_note": "",
            "review_flags": "value_neutral|declared_drop|duplicate_drop_review_required",
            "nwr_score_status": "not_populated_from_snapshot_rank",
            "value_status": "value_neutral",
        },
        {
            "asset_id": "declared_drop:brockpurdy:seq2:instance2",
            "player": "Brock Purdy",
            "position": "QB",
            "source_label": "declared_drop",
            "draft_rank": 90,
            "stats_model_value": 0.0,
            "rank": "",
            "tier": "",
            "draft_action": "",
            "warning_severity": "",
            "draft_room_note": "",
            "review_flags": "value_neutral|declared_drop|duplicate_drop_review_required",
            "nwr_score_status": "not_populated_from_snapshot_rank",
            "value_status": "value_neutral",
        },
        {
            "asset_id": "free_agent:wr:row1",
            "player": "Free Agent WR",
            "position": "WR",
            "source_label": "free_agent",
            "draft_rank": 115,
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
    )
    pick_rows = (
        {
            "overall_pick": 1,
            "round": 1,
            "round_pick": 1,
            "pick_label": "1.01",
            "current_owner": "Other",
            "manager": "Other Manager",
            "is_my_pick": False,
        },
        {
            "overall_pick": 3,
            "round": 1,
            "round_pick": 3,
            "pick_label": "1.03",
            "current_owner": "Niners",
            "manager": "Mike Colety",
            "is_my_pick": True,
        },
        {
            "overall_pick": 4,
            "round": 1,
            "round_pick": 4,
            "pick_label": "1.04",
            "current_owner": "Other",
            "manager": "Other Manager",
            "is_my_pick": False,
        },
    )
    return CombinedSimulatorState(
        review_only=True,
        available_rows=available_rows,
        pick_rows=pick_rows,
        draft_state=None,
        manifest={},
        review_flags={
            "duplicate_drop_review_required": 2,
            "future_placeholder_pick_review_required": 1,
        },
        source_counts={"frozen_rookie": 2, "declared_drop": 2, "free_agent": 1},
        artifact_paths={},
    )


def test_run_report_creates_pick_rows_and_tim_shortlist_without_auto_pick() -> None:
    report = build_mock_draft_run_report(_combined_state(), shortlist_size=3)

    assert len(report.pick_rows) == 3
    tim_row = next(row for row in report.pick_rows if row["selection_mode"] == "Tim_review_pick")
    assert tim_row["selected_player"] == ""
    assert tim_row["review_flags"] == "tim_manual_review_required"
    assert len(report.tim_shortlist_rows) == 3
    assert report.tim_shortlist_rows[0]["player"] == "Beta Rookie"
    assert report.tim_shortlist_rows[0]["market_context_used"] is False
    assert "Frozen rookie guidance copied read-only" in (
        report.tim_shortlist_rows[0]["shortlist_reason"]
    )


def test_opponent_placeholder_behavior_preserves_guidance_and_value_neutral_rows() -> None:
    report = build_mock_draft_run_report(_combined_state(), shortlist_size=3)

    opponent_rows = [
        row for row in report.pick_rows if row["selection_mode"] == "opponent_behavior_placeholder"
    ]
    assert len(opponent_rows) == 2
    assert opponent_rows[0]["selected_player"] == "Alpha Rookie"
    assert opponent_rows[0]["stats_model_value"] == 0.0
    assert opponent_rows[0]["nwr_score_status"] == "no_numeric_score_exposed_guidance_only"
    assert opponent_rows[1]["selected_player"] == "Beta Rookie"
    assert report.manifest["opponent_selection_rows"] == 2
    assert "No numeric NWR score is invented" in report.manifest["nwr_score_policy"]


def test_adp_market_timing_is_behavior_only_and_score_fields_are_ignored() -> None:
    report = build_mock_draft_run_report(
        _combined_state(),
        market_context_rows=[
            {
                "asset_id": "declared_drop:brockpurdy:seq1:instance1",
                "market_adp": 1.0,
                "stats_model_value": 99.0,
                "nwr_quality_score": 99.0,
            }
        ],
        shortlist_size=3,
    )

    first_pick = report.pick_rows[0]
    assert first_pick["selection_mode"] == "opponent_behavior_market_timing"
    assert first_pick["selected_player"] == "Brock Purdy"
    assert first_pick["stats_model_value"] == 0.0
    assert first_pick["market_context_used"] is True
    assert report.opponent_behavior_notes[0]["ignored_market_score_fields"] == (
        "nwr_quality_score|stats_model_value"
    )
    assert report.review_flags["market_score_fields_ignored"] == 1


def test_duplicate_drops_and_placeholder_pick_flags_remain_in_report() -> None:
    report = build_mock_draft_run_report(_combined_state(), shortlist_size=5)

    assert report.review_flags["duplicate_drop_review_required"] >= 2
    assert report.review_flags["future_placeholder_pick_review_required"] == 1
    assert "1.00" not in {row["pick_label"] for row in report.pick_rows}
    duplicate_shortlist_rows = [
        row
        for row in report.tim_shortlist_rows
        if "duplicate_drop_review_required" in str(row["review_flags"])
    ]
    assert len(duplicate_shortlist_rows) == 2


def test_write_run_report_artifacts_are_local_review_outputs(tmp_path) -> None:
    report = write_mock_draft_run_report_artifacts(
        build_mock_draft_run_report(_combined_state(), shortlist_size=3),
        output_root=tmp_path / "mock_draft_run_20260616",
    )

    assert report.artifact_paths["pick_by_pick"].exists()
    assert report.artifact_paths["tim_shortlist"].exists()
    assert report.artifact_paths["opponent_behavior_notes"].exists()
    assert report.artifact_paths["manifest"].exists()
    with report.artifact_paths["tim_shortlist"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3
    manifest = json.loads(report.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert manifest["promotion_status"] == "local_review_output_only_not_app_wired_not_promoted"
    assert "output-row occurrences" in manifest["review_flag_count_semantics"]
    assert "not unique-player counts" in manifest["review_flag_count_semantics"]
