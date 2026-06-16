from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.mock_draft_full_pool_overlay_service import (
    build_full_pool_visibility_overlay,
    write_full_pool_visibility_overlay,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fixture_roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    run = tmp_path / "run"
    combined = tmp_path / "combined"
    kit = tmp_path / "kit"
    run.mkdir()
    combined.mkdir()
    kit.mkdir()
    _write_csv(
        combined / "combined_available_pool_review_rows.csv",
        [
            {
                "asset_id": "frozen_rookie:alpha:rank1",
                "player": "Alpha Rookie",
                "position": "RB",
                "source_label": "frozen_rookie",
                "draft_rank": 1,
                "stats_model_value": "0.0",
                "rank": "1",
                "tier": "Tier 1",
                "draft_action": "target",
                "warning_severity": "none",
                "draft_room_note": "Frozen note",
                "source_overall_rank": "",
                "source_team": "",
                "source_manager": "",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
                "review_flags": "frozen_rookie_guidance_read_only",
            },
            {
                "asset_id": "frozen_rookie:beta:rank2",
                "player": "Beta Rookie",
                "position": "WR",
                "source_label": "frozen_rookie",
                "draft_rank": 2,
                "stats_model_value": "0.0",
                "rank": "2",
                "tier": "Tier 1",
                "draft_action": "target",
                "warning_severity": "none",
                "draft_room_note": "Frozen note two",
                "source_overall_rank": "",
                "source_team": "",
                "source_manager": "",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
                "review_flags": "frozen_rookie_guidance_read_only",
            },
            {
                "asset_id": "declared_drop:brockpurdy:seq1:instance1",
                "player": "Brock Purdy",
                "position": "QB",
                "source_label": "declared_drop",
                "draft_rank": 90,
                "stats_model_value": "0.0",
                "rank": "",
                "tier": "",
                "draft_action": "",
                "warning_severity": "",
                "draft_room_note": "",
                "source_overall_rank": "90",
                "source_team": "WhoDat?",
                "source_manager": "Thomas Ackeret",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
                "review_flags": "value_neutral|declared_drop|duplicate_drop_review_required",
            },
            {
                "asset_id": "free_agent:wr:row1",
                "player": "Free Agent WR",
                "position": "WR",
                "source_label": "free_agent",
                "draft_rank": 115,
                "stats_model_value": "0.0",
                "rank": "",
                "tier": "",
                "draft_action": "",
                "warning_severity": "",
                "draft_room_note": "",
                "source_overall_rank": "115",
                "source_team": "",
                "source_manager": "",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
                "review_flags": "value_neutral|free_agent",
            },
        ],
    )
    _write_csv(
        run / "mock_draft_pick_by_pick_review_rows.csv",
        [
            {
                "overall_pick": 1,
                "pick_label": "1.01",
                "selected_asset_id": "frozen_rookie:alpha:rank1",
                "selected_player": "Alpha Rookie",
                "selection_mode": "opponent_behavior_placeholder",
            },
            {
                "overall_pick": 3,
                "pick_label": "1.03",
                "selected_asset_id": "",
                "selected_player": "",
                "selection_mode": "Tim_review_pick",
            },
        ],
    )
    (run / "mock_draft_run_manifest.json").write_text(
        json.dumps(
            {
                "review_only": True,
                "upstream_review_flags": {
                    "future_placeholder_pick_review_required": 4,
                },
            }
        ),
        encoding="utf-8",
    )
    _write_csv(
        kit / "tim_pick_windows_quick_sheet.csv",
        [
            {
                "overall_pick": 3,
                "round": 1,
                "pick_label": "1.03",
                "owning_team": "Niners",
                "manager": "Mike Colety",
            }
        ],
    )
    return run, combined, kit


def test_overlay_shows_full_pool_sections_without_blended_ranking(tmp_path) -> None:
    run, combined, kit = _fixture_roots(tmp_path)

    overlay = build_full_pool_visibility_overlay(
        run_root=run,
        combined_root=combined,
        kit_root=kit,
    )

    assert overlay.manifest["tim_pick_window_count"] == 1
    assert overlay.manifest["frozen_rookie_option_rows"] == 1
    assert overlay.manifest["declared_drop_rows"] == 1
    assert overlay.manifest["free_agent_rows"] == 1
    assert {row["section"] for row in overlay.overlay_rows} == {
        "frozen_rookie_options",
        "declared_drop_value_neutral",
        "free_agent_value_neutral",
    }
    value_rows = [row for row in overlay.value_neutral_rows if row["player"] == "Brock Purdy"]
    assert value_rows[0]["value_status"] == "value_neutral"
    assert "not ranked against rookies" in value_rows[0]["ranking_policy"]


def test_overlay_preserves_review_flags_and_placeholder_pick_review(tmp_path) -> None:
    run, combined, kit = _fixture_roots(tmp_path)

    overlay = build_full_pool_visibility_overlay(
        run_root=run,
        combined_root=combined,
        kit_root=kit,
    )

    review_types = {row["review_type"] for row in overlay.review_required_rows}
    assert "duplicate_drop_review_required" in review_types
    assert "future_placeholder_pick_review_required" in review_types
    duplicate = next(
        row
        for row in overlay.review_required_rows
        if row["review_type"] == "duplicate_drop_review_required"
    )
    assert duplicate["player"] == "Brock Purdy"
    assert "do not silently dedupe" in duplicate["review_note"]


def test_overlay_does_not_invent_numeric_score_or_use_market_as_value(tmp_path) -> None:
    run, combined, kit = _fixture_roots(tmp_path)

    overlay = build_full_pool_visibility_overlay(
        run_root=run,
        combined_root=combined,
        kit_root=kit,
    )

    assert all(float(row["stats_model_value"] or 0) == 0.0 for row in overlay.overlay_rows)
    assert "No numeric NWR score is invented" in overlay.manifest["score_policy"]
    assert "not used by the overlay as NWR value" in overlay.manifest["market_policy"]
    rookie = next(row for row in overlay.rookie_rows if row["player"] == "Beta Rookie")
    assert rookie["review_flags"] == "frozen_rookie_guidance_read_only"
    assert rookie["visibility_note"] == "Frozen rookie guidance is copied read-only."


def test_write_overlay_outputs_requested_local_files(tmp_path) -> None:
    run, combined, kit = _fixture_roots(tmp_path)
    overlay = write_full_pool_visibility_overlay(
        build_full_pool_visibility_overlay(
            run_root=run,
            combined_root=combined,
            kit_root=kit,
        ),
        output_root=tmp_path / "full_pool_visibility_overlay_20260616",
    )

    assert overlay.artifact_paths["full_pool_overlay"].exists()
    assert overlay.artifact_paths["value_neutral_veterans"].exists()
    assert overlay.artifact_paths["frozen_rookies"].exists()
    assert overlay.artifact_paths["review_required"].exists()
    assert overlay.artifact_paths["manifest"].exists()
    manifest = json.loads(overlay.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert "window-level visibility rows" in manifest["count_semantics"]
    assert "not unique-player counts" in manifest["count_semantics"]
    assert manifest["promotion_status"] == (
        "local_full_pool_visibility_overlay_only_not_app_wired_not_promoted"
    )
