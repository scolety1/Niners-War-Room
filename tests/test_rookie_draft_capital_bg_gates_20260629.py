from __future__ import annotations

from scripts.build_rookie_draft_capital_bg_gates_20260629 import (
    GATE_B_VERDICT,
    GATE_C_VERDICT,
    NOT_ENOUGH,
    build_draft_capital_review_rows,
    build_gate_b_source_audit_rows,
    build_gate_c_label_coverage_rows,
    build_missingness_rows,
    parse_draft_capital_text,
    validate_draft_capital_rows,
    validate_review_flag_rows,
)


def test_parse_draft_capital_text_extracts_round_and_pick() -> None:
    assert parse_draft_capital_text("round=1; pick=3") == {
        "draft_round": "1",
        "overall_pick": "3",
    }
    assert parse_draft_capital_text("unavailable") == {}


def test_draft_capital_review_rows_are_partial_and_review_only() -> None:
    approval_rows = [_approval_row("13287", "Jeremiyah Love"), _approval_row("999", "Missing")]
    overlay_rows = [
        {
            "player": "Jeremiyah Love",
            "position": "RB",
            "nfl_team": "ARI",
            "nfl_draft_capital_display_only": "round=1; pick=3",
        }
    ]

    rows = build_draft_capital_review_rows(
        approval_rows=approval_rows,
        overlay_rows=overlay_rows,
        source_file="docs/tracked.csv",
    )

    assert rows[0]["draft_year"] == "2026"
    assert rows[0]["draft_round"] == "1"
    assert rows[0]["overall_pick"] == "3"
    assert rows[0]["drafted_team"] == "ARI"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[1]["draft_round"] == NOT_ENOUGH
    assert rows[1]["overall_pick"] == NOT_ENOUGH
    assert "0%" not in ",".join(rows[1].values())


def test_validate_draft_capital_rows_rejects_open_model_flag() -> None:
    rows = [_minimal_draft_row(str(index)) for index in range(157)]
    rows[0]["model_use_allowed"] = "true"

    try:
        validate_draft_capital_rows(rows)
    except ValueError as exc:
        assert "model_use_allowed=false" in str(exc)
    else:
        raise AssertionError("Expected validation to reject model-use flag")


def test_missingness_and_source_audit_keep_review_flags_closed() -> None:
    rows = [_minimal_draft_row(str(index)) for index in range(157)]
    for index in range(49):
        rows[index]["overall_pick"] = str(index + 1)
        rows[index]["draft_round"] = "1"
        rows[index]["drafted_team"] = "ARI"
        rows[index]["draft_year"] = "2026"
        rows[index]["udfa_status"] = "false"
        rows[index]["nfl_entry_status"] = "drafted_review_only"
        rows[index]["rookie_class_year"] = "2026"

    missingness = build_missingness_rows(rows)
    source_audit = build_gate_b_source_audit_rows(draft_rows=rows, overlay_rows=[{}] * 54)

    assert next(row for row in missingness if row["field_name"] == "overall_pick")[
        "available_rows"
    ] == "49"
    assert source_audit[0]["gate_b_use_status"] == GATE_B_VERDICT
    validate_review_flag_rows(missingness)
    validate_review_flag_rows(source_audit)


def test_gate_c_label_coverage_blocks_historical_labels() -> None:
    rows = [_minimal_draft_row(str(index)) for index in range(157)]
    coverage = build_gate_c_label_coverage_rows(rows)

    assert any(row["availability_status"] == "missing" for row in coverage)
    assert {row["approved_for_label_build"] for row in coverage} == {"false"}
    assert GATE_C_VERDICT == "BLOCKED_NEEDS_HISTORICAL_LABELS"
    validate_review_flag_rows(coverage)


def test_lane_code_does_not_reference_protected_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("rookie_draft_capital_bg" not in path for path in protected_paths)


def _approval_row(player_id: str, player_name: str) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "RB",
        "gate_a_status": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
        "human_decision": "APPROVE_REVIEW_ONLY",
        "approved_by_human": "true",
    }


def _minimal_draft_row(player_id: str) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": f"Player {player_id}",
        "position": "RB",
        "cfbd_identity_approval_status": "GREEN_REVIEW_ONLY_IDENTITY_APPROVAL",
        "human_decision": "APPROVE_REVIEW_ONLY",
        "draft_year": NOT_ENOUGH,
        "draft_round": NOT_ENOUGH,
        "overall_pick": NOT_ENOUGH,
        "drafted_team": NOT_ENOUGH,
        "udfa_status": NOT_ENOUGH,
        "nfl_entry_status": NOT_ENOUGH,
        "rookie_class_year": NOT_ENOUGH,
        "age_at_draft": NOT_ENOUGH,
        "source_file": NOT_ENOUGH,
        "source_status": "missing_tracked_draft_capital_for_identity",
        "source_provenance": "No tracked draft-capital row matched this approved identity.",
        "data_quality_status": "MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED",
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "blocker_reason": "No tracked review-only draft year/round/pick/team found.",
    }
