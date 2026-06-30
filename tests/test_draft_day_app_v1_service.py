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
    assert rows["Drake Maye"]["dynasty_asset_tier"] == "Tier 1A: core on-clock candidates"
    assert rows["Drake Maye"]["dynasty_asset_rank"] == "4"
    assert rows["Drake Maye"]["on_clock_decision_rank"] == "4"
    assert "1QB" in rows["Drake Maye"]["on_clock_warning"]
    assert rows["Tyreek Hill"]["final_board_rank"] == "Not on frozen board"
    assert rows["Tyreek Hill"]["dynasty_asset_tier"] == "Tier 3: discount / depth / risky"
    assert rows["Tyreek Hill"]["on_clock_decision_rank"] == "18"
    assert "LOUD WARNING" in rows["Tyreek Hill"]["on_clock_warning"]
    assert rows["Jeremiyah Love"]["dynasty_asset_tier"] == "Tier 1A: core on-clock candidates"
    assert rows["Zay Flowers"]["on_clock_decision_rank"] == "1"
    assert rows["Zay Flowers"]["dynasty_asset_rank"] == "1"


def test_available_pool_adp_pick_equivalent_is_display_only_timing_context() -> None:
    bundle = load_frozen_board()
    expanded = load_expanded_draftable_player_pool(bundle.frame)
    rows = {str(row["player"]): row for row in expanded.to_dict("records")}

    assert rows["Jeremiyah Love"]["available_pool_adp_rank"] == "1"
    assert rows["Jeremiyah Love"]["pool_adp_pick_equivalent"] == "1.01"
    assert rows["Drake Maye"]["pool_adp_pick_equivalent"] == "1.02"
    assert rows["Carnell Tate"]["pool_adp_pick_equivalent"] == "1.04"
    assert rows["Tyreek Hill"]["pool_adp_pick_equivalent"] == "4.04"


def test_verified_rookie_birthdate_audit_fills_age_but_conflicts_stay_missing() -> None:
    bundle = load_frozen_board()
    expanded = load_expanded_draftable_player_pool(bundle.frame)
    rows = {str(row["player"]): row for row in expanded.to_dict("records")}

    assert rows["Jeremiyah Love"]["age"] != OUTCOME_NOT_ENOUGH_INFORMATION
    assert rows["KC Concepcion"]["age"] == OUTCOME_NOT_ENOUGH_INFORMATION


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
    wr_targets = outcome_targets_for_positions(["WR"])
    rb_targets = outcome_targets_for_positions(["RB"])

    assert all(
        column in wr_targets
        for column in (
            "outcome_v2_status_display_only",
            "outcome_v2_availability_context_status",
            "outcome_v2_caveat_display_only",
        )
    )
    assert tuple(
        column for column in wr_targets if column in {
            "wr_t12_display_only",
            "wr_t24_display_only",
            "wr_t36_display_only",
        }
    ) == (
        "wr_t12_display_only",
        "wr_t24_display_only",
        "wr_t36_display_only",
    )
    assert "outcome_v2_wr_t6_this_year_display_only" in wr_targets
    assert "outcome_v2_wr_t36_within_5y_display_only" in wr_targets
    assert "outcome_v2_rb_t24_within_5y_display_only" in rb_targets
    assert "outcome_v2_rb_t6_within_5y_display_only" not in rb_targets
    assert "outcome_v2_rb_t12_within_5y_display_only" not in rb_targets
    qb_targets = outcome_targets_for_positions(["QB"])
    te_targets = outcome_targets_for_positions(["TE"])
    assert "qb_t12_display_only" in qb_targets
    assert "outcome_v2_qb_t6_this_year_display_only" in qb_targets
    assert "outcome_v2_qb_t12_within_5y_display_only" in qb_targets
    assert "te_t12_display_only" in te_targets
    assert "outcome_v2_te_t12_within_5y_display_only" in te_targets


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


def test_full_dynasty_player_board_default_display_is_product_clean() -> None:
    frame = pd.DataFrame(
        [
            {
                "nwr_rank": "1",
                "cross_asset_candidate_rank": "99",
                "cross_asset_candidate_value": "44.0",
                "final_board_rank": "7",
                "final_tier": "T2",
                "source_coverage": "Full Dynasty source + Frozen Baseline",
                "asset_type_display": "Veteran",
                "player_name": "Example WR",
                "position": "WR",
                "nfl_team": "",
                "age": "",
                "nwr_position_rank": "WR1",
                "candidate_value_band": "Priority candidate",
                "nwr_dynasty_score": "88.8",
                "trust_status": "Scored",
                    "confidence_band": "Medium",
                    "available_pool_adp_range": "90s",
                    "candidate_key_caveat": "",
                    "outcome_availability_display_only": "",
                    "wr_t12_display_only": "",
                "wr_t24_display_only": "74%",
                "wr_t36_display_only": "88%",
                "rb_t12_display_only": "N/A",
                "rb_t24_display_only": "N/A",
                "qb_t12_display_only": "N/A",
                "te_t12_display_only": "N/A",
            }
        ]
    )

    display = display_unified_player_board_frame(
        frame,
        view_mode=FULL_DYNASTY_VIEW,
        outcome_mode=OUTCOME_DISPLAY_MODE_HIDE,
        selected_positions=["WR"],
    )

    assert display.columns.tolist() == [
        "Dynasty Rank",
        "Player",
        "Pos",
        "NFL Team",
        "Age",
        "NWR Dynasty Score",
        "Position Rank",
        "Value Band (Review-Only)",
        "Data Trust",
        "Confidence",
        "Main Caveat",
    ]
    assert display.loc[0, "NFL Team"] == OUTCOME_NOT_ENOUGH_INFORMATION
    assert display.loc[0, "Age"] == OUTCOME_NOT_ENOUGH_INFORMATION
    assert display.loc[0, "Main Caveat"] == OUTCOME_NOT_ENOUGH_INFORMATION
    for blocked in (
        "Final Board Rank",
        "Final Tier",
        "Source Coverage",
        "Asset Type",
        "Outcome Availability (Display-Only)",
        "WR T12 (Display-Only)",
        "WR T24 (Display-Only)",
        "WR T36 (Display-Only)",
        "WR T12 This Year (Outcome V2 / Display-Only)",
        "Tuned V2 Candidate Rank (Review-Only)",
        "Tuned V2 Candidate Value (Review-Only)",
        "Available-Pool ADP Range (Display-Only)",
    ):
        assert blocked not in display.columns


def test_nwr_position_rank_display_is_derived_without_overwriting_nwr_rank() -> None:
    frame = pd.DataFrame(
        [
            {"nwr_rank": "12", "player_name": "Zay Flowers", "position": "WR"},
            {"nwr_rank": "1", "player_name": "Puka Nacua", "position": "WR"},
            {"nwr_rank": "3", "player_name": "Bijan Robinson", "position": "RB"},
            {"nwr_rank": "", "player_name": "Missing Rank", "position": "TE"},
        ]
    )

    ranked = draft_day_service.add_nwr_position_rank_display(frame)

    rows = {row["player_name"]: row for row in ranked.to_dict("records")}
    assert rows["Puka Nacua"]["nwr_rank"] == "1"
    assert rows["Puka Nacua"]["nwr_position_rank"] == "WR1"
    assert rows["Zay Flowers"]["nwr_rank"] == "12"
    assert rows["Zay Flowers"]["nwr_position_rank"] == "WR2"
    assert rows["Bijan Robinson"]["nwr_position_rank"] == "RB1"
    assert rows["Missing Rank"]["nwr_position_rank"] == OUTCOME_NOT_ENOUGH_INFORMATION


def test_outcome_column_mode_resolves_columns_for_selected_positions() -> None:
    columns = outcome_columns_for_display(
        outcome_mode="Position-applicable only",
        selected_positions=["WR", "TE"],
    )
    assert "wr_t12_display_only" in columns
    assert "wr_t36_display_only" in columns
    assert "te_t12_display_only" in columns
    assert "outcome_v2_wr_t6_this_year_display_only" in columns
    assert "outcome_v2_te_t12_within_5y_display_only" in columns
    assert "outcome_v2_rb_t24_within_5y_display_only" not in columns
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


def test_outcome_v2_display_artifact_loads_by_player_id_and_keeps_missing_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "outcome_v2_current_player_display.csv"
    pd.DataFrame(
        [
            _outcome_v2_artifact_row(
                "1",
                "Puka Nacua",
                "WR",
                "eligible_veteran_feature_covered",
                {"WR T12 This Year": "43.4%", "WR T36 Within 5Y": "94.5%"},
            ),
            _outcome_v2_artifact_row(
                "2",
                "Rookie WR",
                "WR",
                "out_of_scope_rookie_or_prospect",
                {},
            ),
            _outcome_v2_artifact_row(
                "3",
                "Missing RB",
                "RB",
                "missing_current_feature_coverage",
                {},
            ),
        ]
    ).to_csv(artifact_path, index=False)
    monkeypatch.setattr(
        draft_day_service,
        "OUTCOME_V2_CURRENT_PLAYER_DISPLAY_PATH",
        artifact_path,
    )
    monkeypatch.setattr(
        draft_day_service,
        "EXPECTED_OUTCOME_V2_CURRENT_PLAYER_DISPLAY_HASH",
        draft_day_service.file_sha256(artifact_path),
    )

    frame = pd.DataFrame(
        [
            {"player_id": "1", "player_name": "Puka Nacua", "position": "WR"},
            {"player_id": "2", "player_name": "Rookie WR", "position": "WR"},
            {"player_id": "3", "player_name": "Missing RB", "position": "RB"},
        ]
    )

    enriched = draft_day_service.integrate_outcome_v2_display_context(frame)
    puka = enriched.loc[enriched["player_id"].eq("1")].iloc[0]
    rookie = enriched.loc[enriched["player_id"].eq("2")].iloc[0]
    missing = enriched.loc[enriched["player_id"].eq("3")].iloc[0]

    assert puka["outcome_v2_status_display_only"] == "Available"
    assert puka["outcome_v2_wr_t12_this_year_display_only"] == "43.4%"
    assert puka["outcome_v2_wr_t36_within_5y_display_only"] == "94.5%"
    assert puka["injury_context_available_display_only"] == "true"
    assert puka["injury_context_limited_recent_sample_display_only"] == "false"
    assert (
        puka["injury_context_not_enough_information_reason_display_only"]
        == "Outcome V2 probabilities are unchanged; injury context is a review-only "
        "availability caveat, not a model input."
    )
    assert rookie["outcome_v2_status_display_only"] == "out_of_scope_rookie_or_prospect"
    assert rookie["outcome_v2_wr_t12_this_year_display_only"] == OUTCOME_NOT_ENOUGH_INFORMATION
    assert missing["outcome_v2_status_display_only"] == "missing_current_feature_coverage"
    assert missing["outcome_v2_rb_t24_within_5y_display_only"] == OUTCOME_NOT_ENOUGH_INFORMATION
    assert "outcome_v2_rb_t6_within_5y_display_only" not in enriched.columns
    assert "outcome_v2_rb_t12_within_5y_display_only" not in enriched.columns

    clean_display = display_unified_player_board_frame(
        enriched,
        view_mode=FULL_DYNASTY_VIEW,
        outcome_mode=OUTCOME_DISPLAY_MODE_HIDE,
        selected_positions=["WR", "RB"],
    )
    outcome_lens_display = display_unified_player_board_frame(
        enriched,
        view_mode=FULL_DYNASTY_VIEW,
        selected_positions=["WR", "RB"],
        include_injury_context=True,
    )

    assert "Availability Caveat" not in clean_display.columns
    assert "Limited Recent Sample" not in clean_display.columns
    assert "Availability Caveat" in outcome_lens_display.columns
    assert "Last Materially Active Season" in outcome_lens_display.columns
    assert "Not Enough Information Reason" in outcome_lens_display.columns
    assert outcome_lens_display.loc[0, "WR T12 This Year (Outcome V2 / Display-Only)"] == "43.4%"


def _outcome_v2_artifact_row(
    player_id: str,
    player_name: str,
    position: str,
    eligibility_status: str,
    probabilities: dict[str, str],
) -> dict[str, str]:
    row = {
        "nwr_player_id": player_id,
        "sleeper_id": player_id,
        "gsis_id": f"00-test-{player_id}",
        "player_name": player_name,
        "position": position,
        "team": "SF",
        "eligibility_status": eligibility_status,
        "identity_status": "matched_exact",
        "feature_coverage_status": (
            "feature_covered_2025_regular_season"
            if eligibility_status == "eligible_veteran_feature_covered"
            else eligibility_status
        ),
        "scoring_mode": "partial_exact_first_down_scoring_missing_sack_fumbles_lost",
        "outcome_v2_version": "test",
        "as_of_context": "2026-pre-draft",
        "this_year_definition": "2026 NFL season",
        "display_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "market_used_as_input": "false",
        "dynastyprocess_used_as_input": "false",
        "adp_used_as_input": "false",
        "cfbd_used_as_input": "false",
        "data_coverage_status": "partial_2025_feature_source_approval",
        "availability_context_status": "partial_availability_context_missing_games",
        "caveat_summary": (
            "Display-only; games missing; no row is Not enough information, "
            "not clean health."
        ),
        "injury_context_available": "true",
        "most_recent_injury_context_season": "2025",
        "prior_season_injury_context_available": "true",
        "prior_season_injury_report_weeks": "2",
        "prior_season_out_or_doubtful_weeks": "1",
        "prior_season_questionable_weeks": "1",
        "missed_prior_season_context_flag": "review_required_prior_out_or_doubtful_context",
        "limited_recent_sample": "false",
        "last_materially_active_season": "2025",
        "seasons_since_material_activity": "1",
        "availability_caveat": (
            "Review-only injury context: 2 report weeks in 2025; 1 out/doubtful weeks. "
            "This is not a medical projection and does not change Outcome probabilities."
        ),
        "not_enough_information_reason": (
            "Outcome V2 probabilities are unchanged; injury context is a review-only "
            "availability caveat, not a model input."
        ),
        "injury_context_source_status": "review_only_nflreadpy_injury_context",
        "injury_context_review_only": "true",
        "injury_used_as_model_input": "false",
        "medical_projection_made": "false",
        "validated_field_status": "validated_position_fields_only",
    }
    for source, _target, _label, _position in draft_day_service.APPROVED_OUTCOME_V2_DISPLAY_FIELDS:
        row[source] = probabilities.get(source, OUTCOME_NOT_ENOUGH_INFORMATION)
    return row


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
        "Full Dynasty source + Frozen Baseline",
        "Frozen Baseline only",
    }
    board_only = display.loc[display["Player"].eq("Draft Prospect")].iloc[0]
    assert board_only["Dynasty Rank"] == "Frozen-baseline only"
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
