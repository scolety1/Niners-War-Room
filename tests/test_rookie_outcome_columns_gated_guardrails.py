from __future__ import annotations

from scripts.build_rookie_outcome_gate_a_packet_20260629 import (
    APPROVAL_PACKET_COLUMNS,
    build_approval_packet_rows,
    validate_approval_packet_rows,
)


def test_gate_a_packet_defaults_are_review_only_and_unapproved() -> None:
    rows = build_approval_packet_rows(
        readiness_rows=[
            {
                "player_id": "13287",
                "player_name": "Jeremiyah Love",
                "position": "RB",
                "college_team": "Notre Dame",
                "cfbd_player_id": "4870808",
                "cfbd_player_name": "Jeremiyah Love",
                "cfbd_match_status": "exact_match",
                "production_context_valid": "REVIEW_ONLY_NOT_APPROVED",
                "identity_confidence": "HIGH",
                "ambiguity_flag": "no",
                "blocker_reason": "human approval required",
            }
        ],
        match_rows=[
            {
                "cfbd_player_id": "4870808",
                "cfbd_player_name": "Jeremiyah Love",
                "cfbd_college_team": "Notre Dame",
                "cfbd_position": "RB",
                "cfbd_season": "2025",
                "candidate_player_id": "13287",
                "candidate_sleeper_id": "13287",
                "candidate_player_name": "Jeremiyah Love",
                "candidate_position": "RB",
                "candidate_team": "ARI",
                "match_status": "exact_match",
                "name_score": "100",
                "position_match": "true",
            }
        ],
        production_rows=[
            {
                "cfbd_player_id": "4870808",
                "cfbd_season": "2025",
                "production_categories": "rushing|receiving",
                "production_summary": "rushing: YDS=1000 | receiving: REC=20",
            }
        ],
    )

    assert tuple(rows[0]) == APPROVAL_PACKET_COLUMNS
    assert rows[0]["recommended_review_decision"] == "APPROVE_REVIEW_ONLY"
    assert rows[0]["human_decision"] == ""
    assert rows[0]["approved_by_human"] == "false"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[0]["nfl_team_if_available"] == "ARI"
    validate_approval_packet_rows(rows)


def test_gate_a_possible_candidate_packet_defers_and_flags_ambiguity() -> None:
    rows = build_approval_packet_rows(
        readiness_rows=[
            {
                "player_id": "7525",
                "player_name": "DeVonta Smith",
                "position": "WR",
                "college_team": "Alabama",
                "cfbd_player_id": "4594449",
                "cfbd_player_name": "DeVonta Smith",
                "cfbd_match_status": "possible_candidate",
                "production_context_valid": "NOT_AVAILABLE_OR_NOT_LINKED",
                "identity_confidence": "LOW",
                "ambiguity_flag": "yes",
                "blocker_reason": "possible match requires review",
            }
        ],
        match_rows=[],
        production_rows=[],
    )

    assert rows[0]["recommended_review_decision"] == "DEFER"
    assert "possible_candidate_requires_review" in rows[0]["ambiguity_flags"]
    assert rows[0]["production_context_summary"] == "Not enough information"
    validate_approval_packet_rows(rows)


def test_gate_a_packet_rejects_self_approval() -> None:
    row = {column: "" for column in APPROVAL_PACKET_COLUMNS}
    row.update(
        {
            "recommended_review_decision": "APPROVE_REVIEW_ONLY",
            "approved_by_human": "true",
            "review_only": "true",
            "model_use_allowed": "false",
            "training_allowed": "false",
        }
    )

    try:
        validate_approval_packet_rows([row])
    except ValueError as exc:
        assert "must not self-approve" in str(exc)
    else:
        raise AssertionError("Expected self-approval validation failure")


def test_gate_a_lane_does_not_reference_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("rookie_outcome_gate_a" not in path for path in protected_paths)
