from __future__ import annotations

from src.services.source_governance_service import build_source_governance_board


def test_source_governance_board_exposes_sources_notes_and_override_template() -> None:
    board = build_source_governance_board(
        "sample_data/2026_pre_declaration",
        veteran_model_dir="sample_data/veteran_model_v1",
    )

    assert board.data_pack_sources
    assert board.veteran_sources
    assert board.veteran_sources[0]["source_domain"] == "league_state"
    assert board.veteran_sources[0]["authority_tier"] == "tier_a_local_canonical"
    assert board.audit_notes
    assert board.manual_overrides == []
    assert board.override_template_rows[0]["target_field"] == "normalized_score"
    assert board.issue_rows == []
