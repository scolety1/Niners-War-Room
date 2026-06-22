from __future__ import annotations

import py_compile
from pathlib import Path

import pandas as pd

import src.services.draft_day_app_v1_service as draft_day_service
from src.services.draft_day_app_v1_service import (
    EXPECTED_DYNASTY_ROW_COUNT,
    EXPECTED_ROW_COUNT,
    FULL_DYNASTY_VIEW,
    OUTCOME_DISPLAY_MODE_ALL,
    OUTCOME_DISPLAY_MODE_HIDE,
    OUTCOME_NOT_APPLICABLE,
    OUTCOME_NOT_ENOUGH_INFORMATION,
    REPO_SAFE_APP_PROP_ROOT,
    REPO_SAFE_FROZEN_BOARD_ROOT,
    REQUIRED_VISIBLE_FIELDS,
    ROOKIES_DRAFT_BOARD_VIEW,
    build_unified_player_board,
    display_board_frame,
    display_dynasty_rankings_frame,
    display_lane_prop_frame,
    display_unified_player_board_frame,
    extract_prop_status,
    frozen_board_outcome_support_counts,
    hidden_sort_columns,
    lane_prop_status_rows,
    load_cross_asset_candidate_board,
    load_expanded_draftable_player_pool,
    load_frozen_board,
    load_lane_prop_file,
    load_pdf_free_agent_pool,
    normalize_board_frame,
    outcome_columns_for_display,
    outcome_display_coverage_counts,
    outcome_prop_match_counts,
    outcome_targets_for_positions,
    sort_unified_player_board_for_view,
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


def test_tuned_v2_overlay_updates_review_only_candidate_context() -> None:
    candidate = load_cross_asset_candidate_board()
    rows = {
        str(row["player"]): row
        for row in candidate.loc[
            candidate["player"].isin(
                [
                    "Jeremiyah Love",
                    "Zay Flowers",
                    "Chris Olave",
                    "Jameson Williams",
                    "Drake Maye",
                    "Dak Prescott",
                    "Keenan Allen",
                    "Darren Waller",
                ]
            )
        ].to_dict("records")
    }

    assert rows["Jeremiyah Love"]["cross_asset_candidate_rank"] == "1"
    assert rows["Zay Flowers"]["cross_asset_candidate_rank"] == "2"
    assert rows["Chris Olave"]["cross_asset_candidate_rank"] == "3"
    assert rows["Jameson Williams"]["cross_asset_candidate_rank"] == "6"
    assert rows["Drake Maye"]["cross_asset_candidate_rank"] == "20"
    assert rows["Dak Prescott"]["cross_asset_candidate_rank"] == "53"
    assert rows["Keenan Allen"]["cross_asset_candidate_rank"] == "64"
    assert rows["Darren Waller"]["cross_asset_candidate_rank"] == "66"
    assert "Tuned V2 Candidate / Review-Only" in rows["Zay Flowers"]["source_note"]
    assert rows["Zay Flowers"]["horizon_next5y_band"] == "Priority"


def test_frozen_board_keeps_final_rank_with_tuned_v2_candidate_context() -> None:
    bundle = load_frozen_board()
    zay = bundle.frame.loc[bundle.frame["player"].astype(str).eq("Zay Flowers")].iloc[0]
    maye = bundle.frame.loc[bundle.frame["player"].astype(str).eq("Drake Maye")].iloc[0]

    assert int(zay["final_board_rank"]) == 31
    assert str(zay["cross_asset_candidate_rank"]) == "2"
    assert int(maye["final_board_rank"]) == 40
    assert str(maye["cross_asset_candidate_rank"]) == "20"


def test_pdf_free_agent_pool_loads_verified_page_three_rows() -> None:
    pool = load_pdf_free_agent_pool()

    assert not pool.empty
    assert {"player", "pos", "include_default", "source_group"}.issubset(pool.columns)
    rows = {str(row["player"]): row for row in pool.to_dict("records")}
    assert rows["Tyreek Hill"]["source_group"] == "LVE PDF Free Agent"
    assert rows["Tyreek Hill"]["include_default"] == "yes"
    assert rows["Evan McPherson"]["include_default"] == "no"


def test_expanded_draftable_pool_adds_pdf_free_agents_without_mutating_frozen_count() -> None:
    bundle = load_frozen_board()
    expanded = load_expanded_draftable_player_pool(bundle.frame)

    assert bundle.row_count == EXPECTED_ROW_COUNT
    assert expanded.shape[0] > EXPECTED_ROW_COUNT
    tyreek = expanded.loc[expanded["player"].astype(str).eq("Tyreek Hill")].iloc[0]
    assert tyreek["final_board_rank"] == "Not on frozen board"
    assert tyreek["source_group"] == "LVE PDF Free Agent"
    assert tyreek["source_label_display_only"] == "PDF Free Agent / Draftable"


def test_on_clock_decision_layer_keeps_frozen_rank_and_adds_emergency_anchors() -> None:
    bundle = load_frozen_board()
    expanded = load_expanded_draftable_player_pool(bundle.frame)
    rows = {str(row["player"]): row for row in expanded.to_dict("records")}

    assert rows["Drake Maye"]["final_board_rank"] == 40
    assert rows["Drake Maye"]["cross_asset_candidate_rank"] == "21"
    assert rows["Drake Maye"]["on_clock_decision_rank"] == "4"
    assert "1QB" in rows["Drake Maye"]["on_clock_warning"]
    assert rows["Tyreek Hill"]["final_board_rank"] == "Not on frozen board"
    assert rows["Tyreek Hill"]["on_clock_decision_rank"] == "18"
    assert "LOUD WARNING" in rows["Tyreek Hill"]["on_clock_warning"]
    assert rows["Zay Flowers"]["on_clock_decision_rank"] == "1"


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


def test_outcome_prop_match_counts_uses_match_status() -> None:
    frame = pd.DataFrame(
        [
            {"player": "Matched Player", "match_status": "matched_name_position"},
            {"player": "Unmatched Player", "match_status": "unmatched_no_outcome_row"},
        ]
    )

    assert outcome_prop_match_counts(frame) == {"rows": 2, "matched": 1, "unmatched": 1}


def test_outcome_prop_match_counts_holds_without_match_status() -> None:
    frame = pd.DataFrame([{"player": "Unknown Player"}])

    assert outcome_prop_match_counts(frame) == {"rows": 1, "matched": 0, "unmatched": 1}


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
    assert prop_rows["outcome_columns"]["status"] == "YELLOW-HOLD"
    assert prop_rows["trading_lab"]["status"] == "GREEN"


def test_full_dynasty_rankings_loader_uses_approved_artifact_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    rows = [
        {
            "nwr_rank": str(index + 1),
            "player_name": f"Player {index + 1}",
            "position": "WR" if index % 2 else "RB",
            "nwr_dynasty_score": "50.0",
            "is_rookie": "1" if index < 10 else "0",
            "player_id": str(1000 + index),
        }
        for index in range(EXPECTED_DYNASTY_ROW_COUNT)
    ]
    root = tmp_path / "dynasty"
    root.mkdir()
    path = root / draft_day_service.DYNASTY_BOARD_FILE_NAME
    pd.DataFrame(rows).to_csv(path, index=False)
    source_hash = draft_day_service.file_sha256(path)
    outcome_path = tmp_path / draft_day_service.OUTCOME_NUMERIC_DISPLAY_FILE_NAME
    outcome_rows = [
        {
            "player_id": str(1000 + index),
            "player_display_name": f"Player {index + 1}",
            "position": "WR" if index % 2 else "RB",
            "outcome_status": "available",
            "qb_t12_display_pct": "",
            "rb_t12_display_pct": "20%" if index % 2 == 0 else "",
            "rb_t24_display_pct": "40%" if index % 2 == 0 else "",
            "wr_t12_display_pct": "30%" if index % 2 else "",
            "wr_t24_display_pct": "50%" if index % 2 else "",
            "wr_t36_display_pct": "70%" if index % 2 else "",
            "te_t12_display_pct": "",
        }
        for index in range(EXPECTED_DYNASTY_ROW_COUNT)
    ]
    pd.DataFrame(outcome_rows).to_csv(outcome_path, index=False)
    outcome_hash = draft_day_service.file_sha256(outcome_path)
    monkeypatch.setenv("NWR_DYNASTY_RANKINGS_ROOT", str(root))
    monkeypatch.setattr(draft_day_service, "EXPECTED_DYNASTY_RANKINGS_HASH", source_hash)
    monkeypatch.setattr(draft_day_service, "OUTCOME_NUMERIC_DISPLAY_PATH", outcome_path)
    monkeypatch.setattr(draft_day_service, "EXPECTED_OUTCOME_NUMERIC_DISPLAY_HASH", outcome_hash)

    bundle = draft_day_service.load_dynasty_rankings()

    assert bundle.loaded
    assert bundle.row_count == EXPECTED_DYNASTY_ROW_COUNT
    assert bundle.veteran_count > 0
    assert bundle.rookie_count > 0
    assert bundle.source_hash == source_hash
    assert outcome_display_coverage_counts(bundle.frame) == {
        "rows": EXPECTED_DYNASTY_ROW_COUNT,
        "available": EXPECTED_DYNASTY_ROW_COUNT,
        "not_enough_information": 0,
    }
    display = display_dynasty_rankings_frame(bundle.frame)
    assert "QB T12" in display.columns
    assert display["RB T12"].isin({"20%", OUTCOME_NOT_APPLICABLE}).all()


def test_full_dynasty_rankings_display_hides_source_bookkeeping() -> None:
    frame = pd.DataFrame(
        [
            {
                "nwr_rank": "1",
                "player_name": "Example Veteran",
                "position": "WR",
                "age": "25",
                "nfl_team": "SF",
                "nwr_dynasty_score": "80.0",
                "trust_status": "Scored",
                "warning_flags": "missing_role_evidence|partial_first_down_confidence_cap",
                "market_rank": "99",
                "league_rank": "88",
                "pool_status": "AVAILABLE",
                "data_needed": "None",
                "outcome_availability_display_only": "Available",
                "qb_t12_display_only": OUTCOME_NOT_ENOUGH_INFORMATION,
                "rb_t12_display_only": OUTCOME_NOT_ENOUGH_INFORMATION,
                "rb_t24_display_only": OUTCOME_NOT_ENOUGH_INFORMATION,
                "wr_t12_display_only": "65%",
                "wr_t24_display_only": "86%",
                "wr_t36_display_only": "93%",
                "te_t12_display_only": OUTCOME_NOT_ENOUGH_INFORMATION,
                "source_path": r"C:\local\source.csv",
                "blocked_use": "draft_sort_override",
                "candidate_evidence_fields_used": "technical",
            }
        ]
    )
    display = display_dynasty_rankings_frame(frame)

    assert "Dynasty Rank" in display.columns
    assert "Player" in display.columns
    assert "NWR Dynasty Score" in display.columns
    assert "Market Rank (Display-Only)" in display.columns
    assert "Outcome Availability (Display-Only)" in display.columns
    assert "WR T12" in display.columns
    assert display.loc[0, "WR T12"] == "65%"
    assert "source_path" not in display.columns
    assert "blocked_use" not in display.columns
    assert "candidate_evidence_fields_used" not in display.columns


def test_position_aware_outcome_targets_follow_player_position() -> None:
    assert outcome_targets_for_positions(["WR"]) == (
        "wr_t12_display_only",
        "wr_t24_display_only",
        "wr_t36_display_only",
    )
    assert outcome_targets_for_positions(["RB"]) == (
        "rb_t12_display_only",
        "rb_t24_display_only",
    )
    assert outcome_targets_for_positions(["QB"]) == ("qb_t12_display_only",)
    assert outcome_targets_for_positions(["TE"]) == ("te_t12_display_only",)


def test_position_aware_display_hides_wrong_position_columns_by_mode() -> None:
    frame = pd.DataFrame(
        [
            {
                "nwr_rank": "1",
                "player_name": "Example WR",
                "position": "WR",
                "nfl_team": "SF",
                "wr_t12_display_only": "65%",
                "wr_t24_display_only": "86%",
                "wr_t36_display_only": "93%",
                "rb_t12_display_only": OUTCOME_NOT_APPLICABLE,
                "rb_t24_display_only": OUTCOME_NOT_APPLICABLE,
                "qb_t12_display_only": OUTCOME_NOT_APPLICABLE,
                "te_t12_display_only": OUTCOME_NOT_APPLICABLE,
            }
        ]
    )

    position_display = display_unified_player_board_frame(
        frame,
        view_mode=FULL_DYNASTY_VIEW,
        selected_positions=["WR"],
    )
    all_display = display_unified_player_board_frame(
        frame,
        view_mode=FULL_DYNASTY_VIEW,
        outcome_mode=OUTCOME_DISPLAY_MODE_ALL,
        selected_positions=["WR"],
    )
    hidden_display = display_unified_player_board_frame(
        frame,
        view_mode=FULL_DYNASTY_VIEW,
        outcome_mode=OUTCOME_DISPLAY_MODE_HIDE,
        selected_positions=["WR"],
    )

    assert "WR T12 (Display-Only)" in position_display.columns
    assert "WR T36 (Display-Only)" in position_display.columns
    assert "RB T12 (Display-Only)" not in position_display.columns
    assert all_display.loc[0, "RB T12 (Display-Only)"] == OUTCOME_NOT_APPLICABLE
    assert all_display.loc[0, "QB T12 (Display-Only)"] == OUTCOME_NOT_APPLICABLE
    assert "WR T12 (Display-Only)" not in hidden_display.columns
    assert "Outcome Availability (Display-Only)" not in hidden_display.columns


def test_outcome_column_mode_resolves_columns_for_selected_positions() -> None:
    assert outcome_columns_for_display(
        outcome_mode="Position-applicable only",
        selected_positions=["WR", "TE"],
    ) == (
        "wr_t12_display_only",
        "wr_t24_display_only",
        "wr_t36_display_only",
        "te_t12_display_only",
    )
    assert outcome_columns_for_display(
        outcome_mode=OUTCOME_DISPLAY_MODE_HIDE,
        selected_positions=["WR"],
    ) == ()


def test_outcome_display_context_uses_not_enough_information_for_missing_values() -> None:
    frame = pd.DataFrame(
        [
            {
                "outcome_availability_display_only": OUTCOME_NOT_ENOUGH_INFORMATION,
                "qb_t12_display_only": OUTCOME_NOT_ENOUGH_INFORMATION,
            }
        ]
    )

    counts = outcome_display_coverage_counts(frame)

    assert counts == {"rows": 1, "available": 0, "not_enough_information": 1}


def test_unified_player_board_preserves_dynasty_and_board_only_truths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    outcome_path = tmp_path / draft_day_service.OUTCOME_NUMERIC_DISPLAY_FILE_NAME
    pd.DataFrame(
        [
            {
                "player_id": "dyn_1",
                "player_display_name": "Dynasty Veteran",
                "position": "WR",
                "outcome_status": "available",
                "qb_t12_display_pct": "",
                "rb_t12_display_pct": "",
                "rb_t24_display_pct": "",
                "wr_t12_display_pct": "65%",
                "wr_t24_display_pct": "86%",
                "wr_t36_display_pct": "93%",
                "te_t12_display_pct": "",
            }
        ]
    ).to_csv(outcome_path, index=False)
    outcome_hash = draft_day_service.file_sha256(outcome_path)
    monkeypatch.setattr(draft_day_service, "OUTCOME_NUMERIC_DISPLAY_PATH", outcome_path)
    monkeypatch.setattr(draft_day_service, "EXPECTED_OUTCOME_NUMERIC_DISPLAY_HASH", outcome_hash)
    dynasty = pd.DataFrame(
        [
            {
                "player_id": "dyn_1",
                "nwr_rank": "1",
                "player_name": "Dynasty Veteran",
                "position": "WR",
                "age": "25",
                "nfl_team": "SF",
                "nwr_dynasty_score": "88.8",
                "trust_status": "Scored",
                "pool_status": "AVAILABLE",
                "warning_flags": "",
                "data_needed": "",
            }
        ]
    )
    dynasty = draft_day_service.integrate_outcome_display_context(dynasty)
    board = pd.DataFrame(
        [
            {
                "player_id": "dyn_1",
                "final_board_rank": "4",
                "final_tier": "T1",
                "position_rank": "WR1",
                "player": "Dynasty Veteran",
                "position": "WR",
                "nfl_team": "SF",
                "model_posture_used": "frozen",
                "candidate_status": "READY",
                "risk_notes": "",
                "needs_manual_review": "false",
            },
            {
                "player_id": "board_1",
                "final_board_rank": "5",
                "final_tier": "T1",
                "position_rank": "RB1",
                "player": "Draft Prospect",
                "position": "RB",
                "nfl_team": "",
                "model_posture_used": "frozen",
                "candidate_status": "READY",
                "risk_notes": "manual check",
                "needs_manual_review": "true",
            },
        ]
    )

    unified = build_unified_player_board(dynasty, board)
    display = display_unified_player_board_frame(unified)

    assert unified.shape[0] == 2
    assert set(unified["source_coverage"]) == {
        "Full Dynasty source + Frozen Board",
        "Frozen Draft Board only",
    }
    board_only = display.loc[display["Player"].eq("Draft Prospect")].iloc[0]
    assert board_only["Dynasty Rank"] == "Draft-board only"
    assert board_only["NWR Dynasty Score"] == OUTCOME_NOT_ENOUGH_INFORMATION
    assert "Outcome Availability (Display-Only)" not in display.columns
    assert "player_id" not in display.columns
    assert "WR T12 (Display-Only)" in display.columns
    assert frozen_board_outcome_support_counts(board) == {
        "rows": 2,
        "supported": 1,
        "unsupported": 1,
    }


def test_unified_player_board_default_sort_uses_dynasty_rank_before_source_coverage() -> None:
    dynasty = pd.DataFrame(
        [
            {
                "player_id": "puka",
                "nwr_rank": "1",
                "player_name": "Puka Nacua",
                "position": "WR",
                "nfl_team": "LAR",
            },
            {
                "player_id": "zay",
                "nwr_rank": "12",
                "player_name": "Zay Flowers",
                "position": "WR",
                "nfl_team": "BAL",
            },
        ]
    )
    board = pd.DataFrame(
        [
            {
                "player_id": "zay",
                "final_board_rank": "1",
                "player": "Zay Flowers",
                "position": "WR",
                "nfl_team": "BAL",
            },
            {
                "player_id": "rookie",
                "final_board_rank": "2",
                "player": "Jeremiyah Love",
                "position": "RB",
                "nfl_team": "ARI",
            },
        ]
    )

    unified = build_unified_player_board(dynasty, board)
    display = display_unified_player_board_frame(unified, view_mode=FULL_DYNASTY_VIEW)

    assert unified["player_name"].tolist() == [
        "Puka Nacua",
        "Zay Flowers",
        "Jeremiyah Love",
    ]
    assert display.columns[0] == "Dynasty Rank"
    assert display.columns[1] == "Player"
    assert "Final Board Rank" not in display.columns
    assert "Final Tier" not in display.columns
    assert "Source Coverage" not in display.columns
    assert all(not column.startswith("_") for column in display.columns)

    frozen_display = display_unified_player_board_frame(
        unified,
        view_mode=ROOKIES_DRAFT_BOARD_VIEW,
    )
    frozen_view = sort_unified_player_board_for_view(unified, ROOKIES_DRAFT_BOARD_VIEW)

    assert frozen_display.columns[0] == "Final Board Rank"
    assert frozen_view["player_name"].tolist()[:2] == ["Zay Flowers", "Jeremiyah Love"]
