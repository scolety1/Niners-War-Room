from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.mock_draft_combined_state_service import (
    ROOKIE_BOARD_FILE,
    ROOKIE_QUICK_SHEET_FILE,
    build_and_write_combined_simulator_state,
    build_combined_simulator_state,
)
from src.services.mock_draft_simulator_service import build_review_mock_draft_scenario


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _rookie_kit_root(tmp_path: Path) -> Path:
    root = tmp_path / "rookie_final_manual_kit_20260615"
    root.mkdir()
    board_rows = [
        {
            "rank": 1,
            "tier": "Tier 1",
            "player": "Alpha Rookie",
            "position": "RB",
            "position_rank": "RB1",
            "draft_action": "priority_review",
            "warning_severity": "green",
            "trap_caution_warning": "",
            "main_positive_reason": "Frozen positive reason",
            "main_risk_manual_question": "Frozen manual question",
            "draft_room_note": "Frozen note",
            "unmatched_neutral_feature_flag": "",
            "model_formula_version": "frozen_20260615",
            "main_ranking_formula_changed": "false",
            "board_order_changed": "false",
            "production_allowed": "false",
            "promotion_status": "frozen_review_only",
        },
        {
            "rank": 2,
            "tier": "Tier 2",
            "player": "Beta Rookie",
            "position": "WR",
            "position_rank": "WR1",
            "draft_action": "manual_review",
            "warning_severity": "yellow",
            "trap_caution_warning": "Trap text",
            "main_positive_reason": "Second positive reason",
            "main_risk_manual_question": "Second question",
            "draft_room_note": "Second note",
            "unmatched_neutral_feature_flag": "",
            "model_formula_version": "frozen_20260615",
            "main_ranking_formula_changed": "false",
            "board_order_changed": "false",
            "production_allowed": "false",
            "promotion_status": "frozen_review_only",
        },
    ]
    _write_csv(root / ROOKIE_BOARD_FILE, board_rows)
    _write_csv(
        root / ROOKIE_QUICK_SHEET_FILE,
        [
            {
                "rank": row["rank"],
                "player": row["player"],
                "position": row["position"],
                "tier": row["tier"],
                "draft_action": row["draft_action"],
                "warning_severity": row["warning_severity"],
                "manual_question": row["main_risk_manual_question"],
                "draft_room_note": row["draft_room_note"],
            }
            for row in board_rows
        ],
    )
    return root


def _snapshot_root(tmp_path: Path) -> Path:
    root = tmp_path / "lve_rosters_061326"
    root.mkdir()
    (root / "extraction_manifest.json").write_text(
        json.dumps(
            {
                "review_only": True,
                "roster_rows": 2,
                "draft_pick_rows": 4,
                "free_agent_rows": 1,
                "declared_drop_rows": 2,
                "declared_drop_unique_players": 1,
                "duplicate_declared_drops": {"brockpurdy": 2},
            }
        ),
        encoding="utf-8",
    )
    _write_csv(
        root / "roster_rows_normalized_review.csv",
        [
            {
                "team_name": "WhoDat?",
                "manager": "Thomas Ackeret",
                "player_name": "Brock Purdy",
                "position": "QB",
                "nfl_team": "SF",
                "overall_rank": 90,
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "team_name": "Niners",
                "manager": "Tim Pounders",
                "player_name": "Placeholder",
                "position": "WR",
                "nfl_team": "SF",
                "overall_rank": 200,
                "input_status": "pdf_table_extraction_review_required",
            },
        ],
    )
    _write_csv(
        root / "draft_pick_rows_normalized_review.csv",
        [
            {
                "current_owner": "Other",
                "manager": "Other",
                "pick_label": "1.01",
                "season": "2026",
                "round_text": "1st Round",
                "asset_type": "DP",
                "original_owner": "Other",
                "is_niners_pick": "False",
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "pick_label": "1.03",
                "season": "2026",
                "round_text": "1st Round",
                "asset_type": "DP",
                "original_owner": "Golden Boy Productions",
                "is_niners_pick": "True",
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "pick_label": "5.04",
                "season": "2026",
                "round_text": "5th Round",
                "asset_type": "DP",
                "original_owner": "Niners",
                "is_niners_pick": "True",
                "input_status": "pdf_table_extraction_review_required",
            },
            {
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "pick_label": "1.00",
                "season": "2027",
                "round_text": "1st Round",
                "asset_type": "DP",
                "original_owner": "Mighty Canucks",
                "is_niners_pick": "True",
                "input_status": "pdf_table_extraction_review_required",
            },
        ],
    )
    _write_csv(
        root / "free_agent_rows_normalized_review.csv",
        [
            {
                "player_name": "Free Agent WR",
                "nfl_team": "MIA",
                "position": "WR",
                "overall_rank": 115,
                "position_rank": 48,
                "input_status": "pdf_table_extraction_review_required",
            }
        ],
    )
    _write_csv(
        root / "declared_top_five_drops_20260616.csv",
        [
            {
                "declared_drop_sequence": 1,
                "player_name": "Brock Purdy",
                "normalized_player_key": "brockpurdy",
                "duplicate_declared_count": 2,
                "duplicate_instance": 1,
                "matched_roster_team": "WhoDat?",
                "matched_roster_manager": "Thomas Ackeret",
                "matched_position": "QB",
                "matched_nfl_team": "SF",
                "matched_overall_rank": 90,
                "matched_free_agent": "False",
                "input_status": "manual_declared_top_five_drop_review_required",
            },
            {
                "declared_drop_sequence": 2,
                "player_name": "Brock Purdy",
                "normalized_player_key": "brockpurdy",
                "duplicate_declared_count": 2,
                "duplicate_instance": 2,
                "matched_roster_team": "WhoDat?",
                "matched_roster_manager": "Thomas Ackeret",
                "matched_position": "QB",
                "matched_nfl_team": "SF",
                "matched_overall_rank": 90,
                "matched_free_agent": "False",
                "input_status": "manual_declared_top_five_drop_review_required",
            },
        ],
    )
    return root


def test_combined_state_preserves_sources_duplicates_and_placeholder_review(tmp_path) -> None:
    state = build_combined_simulator_state(
        rookie_kit_root=_rookie_kit_root(tmp_path),
        snapshot_root=_snapshot_root(tmp_path),
    )

    assert state.source_counts == {
        "frozen_rookie": 2,
        "declared_drop": 2,
        "free_agent": 1,
    }
    assert [row["pick_label"] for row in state.pick_rows] == ["1.01", "1.03", "5.04"]
    assert "1.00" not in {row["pick_label"] for row in state.pick_rows}
    assert state.review_flags["duplicate_drop_review_required"] == 2
    assert state.review_flags["future_placeholder_pick_review_required"] == 1
    brock_rows = [row for row in state.available_rows if row["player"] == "Brock Purdy"]
    assert len(brock_rows) == 2


def test_rookie_guidance_is_read_only_and_no_numeric_score_is_invented(tmp_path) -> None:
    state = build_combined_simulator_state(
        rookie_kit_root=_rookie_kit_root(tmp_path),
        snapshot_root=_snapshot_root(tmp_path),
    )
    rookie = next(row for row in state.available_rows if row["source_label"] == "frozen_rookie")

    assert rookie["player"] == "Alpha Rookie"
    assert rookie["rank"] == "1"
    assert rookie["tier"] == "Tier 1"
    assert rookie["draft_action"] == "priority_review"
    assert rookie["model_formula_version"] == "frozen_20260615"
    assert rookie["nwr_guidance_available"] is True
    assert rookie["nwr_numeric_value_available"] is False
    assert rookie["stats_model_value"] == 0.0
    assert "frozen_rookie_guidance_read_only" in rookie["review_flags"]
    assert state.manifest["nwr_numeric_private_value_rows"] == 0
    assert state.manifest["frozen_rookie_guidance_rows"] == 2
    assert "No numeric NWR score is invented" in state.manifest["nwr_score_policy"]


def test_snapshot_only_players_remain_value_neutral(tmp_path) -> None:
    state = build_combined_simulator_state(
        rookie_kit_root=_rookie_kit_root(tmp_path),
        snapshot_root=_snapshot_root(tmp_path),
    )
    snapshot_rows = [
        row
        for row in state.available_rows
        if row["source_label"] in {"declared_drop", "free_agent"}
    ]

    assert len(snapshot_rows) == 3
    assert all(row["value_status"] == "value_neutral" for row in snapshot_rows)
    assert all(row["stats_model_value"] == 0.0 for row in snapshot_rows)
    assert all(row["nwr_numeric_value_available"] is False for row in snapshot_rows)
    assert state.manifest["value_neutral_rows"] == 3


def test_adp_market_timing_cannot_change_combined_guidance_or_value_fields(tmp_path) -> None:
    state = build_combined_simulator_state(
        rookie_kit_root=_rookie_kit_root(tmp_path),
        snapshot_root=_snapshot_root(tmp_path),
    )
    original_by_asset = {
        row["asset_id"]: {
            "stats_model_value": row["stats_model_value"],
            "rank": row["rank"],
            "tier": row["tier"],
            "draft_action": row["draft_action"],
            "warning_severity": row["warning_severity"],
        }
        for row in state.available_rows
    }

    scenario = build_review_mock_draft_scenario(
        state.draft_state,
        market_context_rows=[
            {
                "asset_id": "frozen_rookie:betarookie:rank2",
                "player": "Beta Rookie",
                "market_adp": 1.0,
                "stats_model_value": 99.0,
                "nwr_quality_score": 99.0,
            }
        ],
    )

    assert scenario.quality_score_firewall_passed is True
    assert any("Ignored market context score/value fields" in row for row in scenario.warnings)
    assert original_by_asset["frozen_rookie:betarookie:rank2"] == {
        "stats_model_value": 0.0,
        "rank": "2",
        "tier": "Tier 2",
        "draft_action": "manual_review",
        "warning_severity": "yellow",
    }


def test_write_combined_state_artifacts_are_local_review_outputs(tmp_path) -> None:
    output_root = tmp_path / "combined_simulator_state_20260616"

    state = build_and_write_combined_simulator_state(
        rookie_kit_root=_rookie_kit_root(tmp_path),
        snapshot_root=_snapshot_root(tmp_path),
        output_root=output_root,
    )

    assert state.artifact_paths["available_pool"].exists()
    assert state.artifact_paths["pick_rows"].exists()
    assert state.artifact_paths["review_flags"].exists()
    assert state.artifact_paths["manifest"].exists()
    manifest = json.loads(state.artifact_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["review_only"] is True
    assert manifest["promotion_status"] == "local_review_input_only_not_promoted"
    assert manifest["source_counts"] == {
        "declared_drop": 2,
        "free_agent": 1,
        "frozen_rookie": 2,
    }
