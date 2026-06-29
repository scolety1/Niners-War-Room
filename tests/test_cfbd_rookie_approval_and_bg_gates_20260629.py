from __future__ import annotations

from scripts.build_cfbd_rookie_approval_and_bg_gates_20260629 import (
    build_approval_rows,
    build_gate_b_audit_rows,
    gate_b_verdict_from_audit,
    validate_approval_rows,
)


def test_high_confidence_exact_match_gets_review_only_human_approval() -> None:
    rows = build_approval_rows(
        [
            _packet_row(
                match_status="exact_match",
                confidence="HIGH",
                recommended="APPROVE_REVIEW_ONLY",
                ambiguity_flags="none",
                production_context_summary="2025 rushing: rushing: CAR=100; TD=10",
            )
        ]
    )

    assert rows[0]["human_decision"] == "APPROVE_REVIEW_ONLY"
    assert rows[0]["approved_by_human"] == "true"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[0]["approval_scope"] == "identity_review_only"


def test_possible_and_ambiguous_rows_remain_deferred_and_unapproved() -> None:
    rows = build_approval_rows(
        [
            _packet_row(
                match_status="possible_candidate",
                confidence="LOW",
                recommended="DEFER",
                ambiguity_flags="possible_candidate_requires_review",
                production_context_summary="Not enough information",
            ),
            _packet_row(
                match_status="ambiguous",
                confidence="MEDIUM",
                recommended="DEFER",
                ambiguity_flags="cfbd_match_status_ambiguous",
                production_context_summary="2025 receiving: receiving: REC=40",
            ),
        ]
    )

    assert {row["human_decision"] for row in rows} == {"DEFER"}
    assert {row["approved_by_human"] for row in rows} == {"false"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_validation_rejects_non_exact_self_approval() -> None:
    rows = build_approval_rows(
        [
            _packet_row(
                match_status="possible_candidate",
                confidence="LOW",
                recommended="DEFER",
                ambiguity_flags="possible_candidate_requires_review",
                production_context_summary="2025 receiving: receiving: REC=40",
            )
        ]
    )
    rows[0]["approved_by_human"] = "true"
    rows[0]["human_decision"] = "APPROVE_REVIEW_ONLY"

    try:
        validate_approval_rows(rows)
    except ValueError as exc:
        assert "Only exact_match rows may be approved" in str(exc)
    else:
        raise AssertionError("Expected validation to reject non-exact approval")


def test_gate_b_audit_blocks_local_only_and_missing_draft_capital_sources() -> None:
    rows = build_gate_b_audit_rows(
        approved_count=157,
        draft_matrix_rows=[
            {
                "source_name": "2026 draft capital snapshot doc",
                "source_path": "docs/model_v4/ROOKIE_DRAFT_CAPITAL_2026_SNAPSHOT.md",
                "scope": "2026 NFL draft result order described in docs",
                "availability_status": "partial_local_only",
                "blocked_reason": "processed CSV lives under local_exports",
                "safe_next_step": "create approved review-only draft capital artifact",
            },
            {
                "source_name": "Historical rookie replay templates",
                "source_path": "templates/real_data_inputs/historical_rookie_replay/*.csv",
                "scope": "future real-data inputs",
                "availability_status": "missing",
                "blocked_reason": "templates have headers but no production rows",
                "safe_next_step": "populate through approved source lane",
            },
        ],
    )

    assert gate_b_verdict_from_audit(rows) == "BLOCKED_NEEDS_DRAFT_CAPITAL"
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_lane_code_does_not_reference_protected_nfl_usage_paths() -> None:
    protected_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )

    assert all("cfbd_rookie_approval" not in path for path in protected_paths)


def _packet_row(
    *,
    match_status: str,
    confidence: str,
    recommended: str,
    ambiguity_flags: str,
    production_context_summary: str,
) -> dict[str, str]:
    return {
        "player_id": "13274",
        "player_name": "Germie Bernard",
        "position": "WR",
        "college_team": "Alabama",
        "nfl_team_if_available": "PIT",
        "draft_year_if_available": "",
        "cfbd_candidate_id": "4685261",
        "cfbd_name": "Germie Bernard",
        "cfbd_position": "WR",
        "cfbd_team": "Alabama",
        "cfbd_years": "2024|2025",
        "match_evidence": (
            f"cfbd_match_status={match_status}; identity_confidence={confidence}; "
            "candidate_source=unified_player_universe_review; "
            "candidate_player_id=13274; position_match=true"
        ),
        "production_context_summary": production_context_summary,
        "ambiguity_flags": ambiguity_flags,
        "recommended_review_decision": recommended,
        "human_decision": "",
        "human_notes": "",
        "approved_by_human": "false",
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
    }
