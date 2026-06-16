from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.mock_draft_room_kit_service import (
    build_draft_room_kit,
    write_draft_room_kit,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _run_root(tmp_path: Path) -> Path:
    root = tmp_path / "mock_draft_run_20260616"
    root.mkdir()
    _write_csv(
        root / "mock_draft_pick_by_pick_review_rows.csv",
        [
            {
                "overall_pick": 1,
                "round": 1,
                "round_pick": 1,
                "pick_label": "1.01",
                "owning_team": "Other",
                "manager": "Other",
                "is_tim_pick": "False",
                "selected_asset_id": "frozen_rookie:alpha:rank1",
                "selected_player": "Alpha Rookie",
                "selected_position": "RB",
                "selected_player_source": "frozen_rookie",
                "selection_mode": "opponent_behavior_placeholder",
                "selection_reason": "Placeholder behavior only.",
                "selection_basis": "placeholder_behavior_only_not_private_value",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
                "stats_model_value": "0.0",
                "market_adp": "",
                "market_context_used": "False",
            },
            {
                "overall_pick": 3,
                "round": 1,
                "round_pick": 3,
                "pick_label": "1.03",
                "owning_team": "Niners",
                "manager": "Mike Colety",
                "is_tim_pick": "True",
                "selected_asset_id": "",
                "selected_player": "",
                "selected_position": "",
                "selected_player_source": "",
                "selection_mode": "Tim_review_pick",
                "selection_reason": "Manual review required.",
                "selection_basis": "manual_shortlist_no_market_quality",
                "review_flags": "tim_manual_review_required",
                "nwr_score_status": "no_auto_selection",
                "value_status": "",
                "stats_model_value": "",
                "market_adp": "",
                "market_context_used": "False",
            },
        ],
    )
    _write_csv(
        root / "tim_pick_shortlist_review_rows.csv",
        [
            {
                "overall_pick": 3,
                "pick_label": "1.03",
                "owning_team": "Niners",
                "manager": "Mike Colety",
                "shortlist_rank": 1,
                "asset_id": "frozen_rookie:beta:rank2",
                "player": "Beta Rookie",
                "position": "WR",
                "player_source": "frozen_rookie",
                "rank": "2",
                "tier": "Tier 1",
                "draft_action": "target",
                "warning_severity": "none",
                "draft_room_note": "Frozen read-only note",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
                "stats_model_value": "0.0",
                "market_context_used": "False",
                "shortlist_reason": "Frozen rookie guidance copied read-only.",
            },
            {
                "overall_pick": 3,
                "pick_label": "1.03",
                "owning_team": "Niners",
                "manager": "Mike Colety",
                "shortlist_rank": 2,
                "asset_id": "declared_drop:brockpurdy:seq1:instance1",
                "player": "Brock Purdy",
                "position": "QB",
                "player_source": "declared_drop",
                "rank": "",
                "tier": "",
                "draft_action": "",
                "warning_severity": "",
                "draft_room_note": "",
                "review_flags": "value_neutral|declared_drop|duplicate_drop_review_required",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
                "stats_model_value": "0.0",
                "market_context_used": "False",
                "shortlist_reason": "Value-neutral available player.",
            },
        ],
    )
    _write_csv(
        root / "opponent_behavior_notes.csv",
        [
            {
                "overall_pick": 1,
                "pick_label": "1.01",
                "owning_team": "Other",
                "selected_player": "Alpha Rookie",
                "selected_player_source": "frozen_rookie",
                "note_type": "opponent_behavior_placeholder",
                "note": "Placeholder behavior only.",
                "market_context_used": "False",
                "ignored_market_score_fields": "",
            }
        ],
    )
    (root / "mock_draft_run_manifest.json").write_text(
        json.dumps(
            {
                "review_only": True,
                "pick_by_pick_rows": 2,
                "tim_pick_rows": 1,
                "tim_shortlist_rows": 2,
                "opponent_selection_rows": 1,
                "review_flag_count_semantics": "output-row occurrences, not unique-player counts",
                "upstream_review_flags": {
                    "duplicate_drop_review_required": 1,
                    "future_placeholder_pick_review_required": 4,
                    "value_neutral": 1,
                    "frozen_rookie_guidance_read_only": 2,
                },
            }
        ),
        encoding="utf-8",
    )
    return root


def test_kit_is_derived_from_review_run_artifacts_and_keeps_tim_manual(tmp_path) -> None:
    kit = build_draft_room_kit(run_root=_run_root(tmp_path))

    assert kit.review_only is True
    assert len(kit.tim_pick_windows) == 1
    assert kit.tim_pick_windows[0]["manual_review_status"] == (
        "manual_review_only_no_auto_best_pick"
    )
    assert kit.tim_pick_windows[0]["top_frozen_rookie_options"] == "Beta Rookie"
    assert kit.tim_pick_windows[0]["value_neutral_names"] == "Brock Purdy"
    assert "No numeric NWR score is invented" in kit.tim_pick_windows[0]["score_policy"]
    assert kit.manifest["source_run_manifest"].endswith("mock_draft_run_manifest.json")


def test_kit_preserves_value_neutral_and_review_flags(tmp_path) -> None:
    kit = build_draft_room_kit(run_root=_run_root(tmp_path))

    value_neutral = [
        row for row in kit.tim_shortlist_rows if row["value_status"] == "value_neutral"
    ]
    assert len(value_neutral) == 1
    assert value_neutral[0]["draft_room_use"].startswith("manual_review_option")
    flags = {row["flag"]: row for row in kit.review_flag_rows}
    assert flags["duplicate_drop_review_required"]["flag_type"] == (
        "Brock Purdy duplicate drop declaration"
    )
    assert flags["future_placeholder_pick_review_required"]["flag_type"] == (
        "future placeholder picks excluded from simulator"
    )
    assert flags["frozen_rookie_guidance_read_only"]["flag_type"] == (
        "frozen rookie guidance read-only"
    )
    assert flags["value_neutral"]["flag_type"] == "value-neutral veterans/free agents"


def test_kit_does_not_invent_numeric_score_or_use_market_as_value(tmp_path) -> None:
    kit = build_draft_room_kit(run_root=_run_root(tmp_path))

    assert all(float(row["stats_model_value"] or 0) == 0.0 for row in kit.tim_shortlist_rows)
    assert all(row["market_context_used"] == "False" for row in kit.tim_shortlist_rows)
    assert "No numeric NWR score is invented" in kit.manifest["score_policy"]
    assert "not used as NWR value" in kit.manifest["market_policy"]


def test_write_draft_room_kit_outputs_requested_local_files(tmp_path) -> None:
    kit = write_draft_room_kit(
        build_draft_room_kit(run_root=_run_root(tmp_path)),
        output_root=tmp_path / "draft_room_kit_20260616",
    )

    assert kit.artifact_paths["tim_pick_windows"].exists()
    assert kit.artifact_paths["tim_manual_shortlist"].exists()
    assert kit.artifact_paths["opponent_run_summary"].exists()
    assert kit.artifact_paths["review_flags"].exists()
    assert kit.artifact_paths["manifest"].exists()
    manifest = json.loads(kit.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert manifest["tim_pick_window_count"] == 1
    assert manifest["tim_shortlist_row_count"] == 2
    assert manifest["promotion_status"] == (
        "local_draft_room_review_kit_only_not_app_wired_not_promoted"
    )
