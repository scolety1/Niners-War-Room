from __future__ import annotations

import py_compile
from pathlib import Path

import pandas as pd

from src.services.draft_day_app_v1_service import (
    EXPECTED_ROW_COUNT,
    REPO_SAFE_APP_PROP_ROOT,
    REPO_SAFE_FROZEN_BOARD_ROOT,
    REQUIRED_VISIBLE_FIELDS,
    display_board_frame,
    display_lane_prop_frame,
    extract_prop_status,
    hidden_sort_columns,
    lane_prop_status_rows,
    load_frozen_board,
    load_lane_prop_file,
    normalize_board_frame,
    validate_frozen_board,
)


def test_frozen_board_loader_contract_is_green_in_local_hq_context() -> None:
    bundle = load_frozen_board()

    assert bundle.loaded
    assert bundle.row_count == EXPECTED_ROW_COUNT
    assert not bundle.errors
    for field in REQUIRED_VISIBLE_FIELDS:
        assert field in bundle.frame.columns
    assert "source_file" not in bundle.frame.columns


def test_hidden_sort_and_private_value_columns_are_blocked() -> None:
    columns = ["player", "final_board_rank", "hidden_sort_key", "private_value_score"]

    assert hidden_sort_columns(columns) == ("hidden_sort_key", "private_value_score")


def test_lane_prop_status_parser_handles_direct_and_heading_formats() -> None:
    assert extract_prop_status("Status: YELLOW-HOLD\n") == "YELLOW-HOLD"
    assert extract_prop_status("Verdict: GREEN\n") == "GREEN"
    assert extract_prop_status("## Verdict\n\nGREEN\n") == "GREEN"


def test_lane_prop_display_hides_technical_guardrail_columns() -> None:
    frame = pd.DataFrame(
        [
            {
                "player": "Example Player",
                "position": "WR",
                "tier_movement_note": "same tier",
                "final_board_rank_override_allowed": "false",
                "hidden_sort_field_created": "false",
                "private_value_created": "false",
            }
        ]
    )

    display = display_lane_prop_frame(frame)

    assert "tier_movement_note" in display.columns
    assert "hidden_sort_field_created" not in display.columns
    assert "private_value_created" not in display.columns
    assert "final_board_rank_override_allowed" not in display.columns


def test_normalized_display_frame_uses_visible_board_fields_only() -> None:
    frame = pd.DataFrame(
        [
            {
                "final_board_rank": 2,
                "final_tier": "T2",
                "position_rank": "WR1",
                "player": "Example WR",
                "position": "WR",
                "nfl_team": "SF",
                "model_posture_used": "safe_no_snap_no_depth_rank",
                "candidate_status": "RESEARCH_CANDIDATE_ONLY",
                "risk_notes": "manual check",
                "needs_manual_review": "true",
                "source_file": r"C:\NWR_SHARED_DATA\local.csv",
            }
        ]
    )

    normalized = normalize_board_frame(frame)
    display = display_board_frame(normalized)

    assert "source_file" not in normalized.columns
    assert "Final Board Rank" in display.columns
    assert "Risk Notes" in display.columns


def test_frozen_board_validation_requires_core_visible_fields() -> None:
    frame = pd.DataFrame({"final_board_rank": [1]})
    errors = validate_frozen_board(frame)

    assert any("Expected 66 frozen board rows" in error for error in errors)
    assert any("Missing required visible fields" in error for error in errors)


def test_draft_day_v1_pages_compile() -> None:
    for path in Path("app/pages").glob("*_v1.py"):
        py_compile.compile(str(path), doraise=True)


def test_lane_prop_status_uses_primary_context_files_when_available() -> None:
    rows = {row["lane"]: row for row in lane_prop_status_rows()}

    assert rows["outcome_columns"]["primary_file"] == "outcome_player_context.csv"
    assert rows["trading_lab"]["primary_file"] == "trade_helper_context.csv"
    assert rows["mock_draft"]["primary_file"] == "availability_context.csv"


def test_specific_lane_prop_file_loader_handles_present_and_missing_files() -> None:
    frame, path = load_lane_prop_file("outcome_columns", "outcome_player_context.csv")
    missing_frame, missing_path = load_lane_prop_file("outcome_columns", "missing.csv")

    assert path is not None
    assert frame.empty or "player" in frame.columns
    assert missing_path is not None
    assert missing_frame.empty


def test_repo_contained_fallback_mode_loads_board_and_props(monkeypatch) -> None:
    monkeypatch.setenv("NWR_DRAFT_DAY_DATA_ROOT", str(REPO_SAFE_FROZEN_BOARD_ROOT))
    monkeypatch.setenv("NWR_DRAFT_DAY_APP_PROPS_ROOT", str(REPO_SAFE_APP_PROP_ROOT))

    bundle = load_frozen_board()
    prop_rows = {row["lane"]: row for row in lane_prop_status_rows()}

    assert bundle.loaded
    assert bundle.row_count == EXPECTED_ROW_COUNT
    assert str(bundle.source_path).endswith("FINAL_DRAFT_BOARD_V1_FROZEN.csv")
    assert prop_rows["outcome_columns"]["status"] == "GREEN"
    assert prop_rows["trading_lab"]["status"] == "GREEN"
