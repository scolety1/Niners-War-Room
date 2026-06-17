from __future__ import annotations

import csv
import json

from src.services.mock_draft_combined_state_service import CombinedSimulatorState
from src.services.mock_draft_manual_review_packet_service import (
    build_manual_review_packet,
    write_manual_review_packet_artifacts,
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
                "asset_id": "declared_drop:brockpurdy:seq1",
                "player": "Brock Purdy",
                "position": "QB",
                "source_label": "declared_drop",
                "draft_rank": 90,
                "stats_model_value": 0.0,
                "review_flags": "value_neutral|declared_drop|duplicate_drop_review_required",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
            },
            {
                "asset_id": "declared_drop:brockpurdy:seq2",
                "player": "Brock Purdy",
                "position": "QB",
                "source_label": "declared_drop",
                "draft_rank": 91,
                "stats_model_value": 0.0,
                "review_flags": "value_neutral|declared_drop|duplicate_drop_review_required",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
            },
            {
                "asset_id": "free_agent:gamma",
                "player": "Gamma Free Agent",
                "position": "WR",
                "source_label": "free_agent",
                "draft_rank": 120,
                "stats_model_value": 0.0,
                "review_flags": "value_neutral|free_agent",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
            },
        ),
        pick_rows=(
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
        review_flags={"future_placeholder_pick_review_required": 1},
        source_counts={"frozen_rookie": 1, "declared_drop": 2, "free_agent": 1},
        artifact_paths={},
    )


def test_manual_fields_are_blank_and_do_not_feed_value() -> None:
    packet = build_manual_review_packet(_combined_state(), options_per_pick=3)

    assert packet.manual_pick_rows
    for row in packet.manual_pick_rows:
        assert row["manual_decision"] == ""
        assert row["manual_notes"] == ""
        assert row["resolved_by"] == ""
        assert row["resolution_status"] == "manual_review_pending"
    assert "do not feed NWR value" in packet.manifest["manual_field_policy"]
    assert packet.manifest["nwr_score_policy"] == "No numeric NWR score is invented."


def test_duplicate_drops_are_preserved_and_placeholder_picks_excluded() -> None:
    packet = build_manual_review_packet(_combined_state(), options_per_pick=4)

    assert len(packet.brock_duplicate_rows) == 2
    assert {row["asset_id"] for row in packet.brock_duplicate_rows} == {
        "declared_drop:brockpurdy:seq1",
        "declared_drop:brockpurdy:seq2",
    }
    assert len(packet.placeholder_pick_rows) == 1
    assert packet.placeholder_pick_rows[0]["simulator_ready"] is False
    assert packet.placeholder_pick_rows[0]["resolution_status"] == (
        "excluded_review_required"
    )


def test_value_neutral_and_rookie_guidance_are_preserved() -> None:
    packet = build_manual_review_packet(_combined_state(), options_per_pick=4)

    value_rows = packet.value_neutral_rows
    assert len(value_rows) == 3
    assert all(row["value_status"] == "value_neutral" for row in value_rows)
    assert all("NWR quality" in row["visibility_only_note"] for row in value_rows)
    rookie = next(row for row in packet.manual_pick_rows if row["player"] == "Alpha Rookie")
    assert rookie["rank"] == "1"
    assert rookie["tier"] == "Tier 1"
    assert rookie["draft_action"] == "target"
    assert rookie["warning_severity"] == "green"
    assert packet.manifest["rookie_guidance_policy"] == (
        "Frozen rookie guidance remains read-only."
    )
    assert "ADP/market fields do not become NWR quality" in packet.manifest["market_policy"]


def test_write_manual_review_packet_artifacts_are_local_review_outputs(tmp_path) -> None:
    packet = write_manual_review_packet_artifacts(
        build_manual_review_packet(_combined_state(), options_per_pick=3),
        output_root=tmp_path / "manual_review_packet_20260617",
    )

    assert packet.artifact_paths["manual_pick_decision_packet"].exists()
    assert packet.artifact_paths["brock_purdy_duplicate_review"].exists()
    assert packet.artifact_paths["future_placeholder_pick_review"].exists()
    assert packet.artifact_paths["value_neutral_inventory"].exists()
    assert packet.artifact_paths["pre_draft_blocker_checklist"].exists()
    with packet.artifact_paths["brock_purdy_duplicate_review"].open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    manifest = json.loads(packet.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert manifest["promotion_status"] == "local_review_output_only_not_app_wired_not_promoted"
