from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET_ROOT = (
    ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_identity_hardening_v1_20260630"
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_identity_review_packet_schema_and_guardrails() -> None:
    rows = _read_csv(PACKET_ROOT / "nflverse_player_context_identity_review_packet_v1.csv")

    expected_columns = [
        "row_id",
        "player_name",
        "normalized_player_name",
        "position",
        "team",
        "season",
        "current_identity_status",
        "candidate_nflverse_player_id",
        "candidate_gsis_id",
        "candidate_pfr_id",
        "candidate_sleeper_id",
        "candidate_nwr_player_id",
        "candidate_team",
        "candidate_position",
        "candidate_roster_years",
        "candidate_draft_year",
        "candidate_draft_team",
        "evidence_summary",
        "match_evidence_strength",
        "same_name_collision_flag",
        "position_mismatch_flag",
        "team_timeline_mismatch_flag",
        "many_to_one_join_flag",
        "one_to_many_join_flag",
        "recommended_decision",
        "recommended_reason",
        "human_decision",
        "approved_by_human",
        "review_only",
        "model_use_allowed",
        "training_allowed",
        "source_truth_allowed",
    ]
    assert list(rows[0]) == expected_columns
    assert len(rows) == 54

    allowed_decisions = {
        "RECOMMEND_APPROVE_REVIEW_ONLY",
        "RECOMMEND_KEEP_BLOCKED",
        "RECOMMEND_REJECT_WRONG_IDENTITY",
        "RECOMMEND_NEEDS_MORE_INFO",
        "RECOMMEND_HUMAN_REVIEW",
    }
    decision_counts: dict[str, int] = {}
    for row in rows:
        decision_counts[row["recommended_decision"]] = (
            decision_counts.get(row["recommended_decision"], 0) + 1
        )
        assert row["recommended_decision"] in allowed_decisions
        assert row["current_identity_status"] == "NEED_IDENTITY_REVIEW"
        assert row["human_decision"] in {"", "PENDING"}
        assert row["approved_by_human"] == "false"
        assert row["review_only"] == "true"
        assert row["model_use_allowed"] == "false"
        assert row["training_allowed"] == "false"
        assert row["source_truth_allowed"] == "false"

    assert decision_counts == {
        "RECOMMEND_APPROVE_REVIEW_ONLY": 43,
        "RECOMMEND_HUMAN_REVIEW": 4,
        "RECOMMEND_KEEP_BLOCKED": 7,
    }


def test_identity_resolution_matrix_is_display_only_and_human_pending() -> None:
    rows = _read_csv(
        PACKET_ROOT / "nflverse_player_context_identity_resolution_recommendations_v1.csv"
    )

    allowed_actions = {
        "display_with_review_only_identity_caveat",
        "display_as_not_enough_information",
        "keep_blocked",
        "reject_candidate",
        "needs_human_review",
    }
    assert len(rows) == 54

    action_counts: dict[str, int] = {}
    for row in rows:
        action_counts[row["safe_display_action"]] = (
            action_counts.get(row["safe_display_action"], 0) + 1
        )
        assert row["safe_display_action"] in allowed_actions
        assert row["requires_human_review"] == "true"
        assert row["review_only"] == "true"
        assert row["model_use_allowed"] == "false"
        assert row["training_allowed"] == "false"
        assert row["source_truth_allowed"] == "false"

    assert action_counts == {
        "display_with_review_only_identity_caveat": 43,
        "keep_blocked": 7,
        "needs_human_review": 4,
    }


def test_identity_hardening_docs_do_not_claim_active_approval() -> None:
    combined_docs = "\n".join(path.read_text(encoding="utf-8") for path in PACKET_ROOT.glob("*.md"))

    assert "Recommendations are not approvals" in combined_docs
    assert "approved_by_human=false" in combined_docs
    assert "model_use_allowed=false" in combined_docs
    assert "training_allowed=false" in combined_docs
    assert "source_truth_allowed=false" in combined_docs
    assert "No active player-context display artifact was rewritten" in combined_docs
