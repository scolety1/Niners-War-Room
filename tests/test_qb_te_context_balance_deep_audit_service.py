from __future__ import annotations

from pathlib import Path

import pytest

from src.services.qb_te_context_balance_deep_audit_service import (
    DEEP_AUDIT_REPORT,
    PRODUCTION_PATCH_PROPOSAL,
    SHADOW_RANKINGS,
    build_context_balance_deep_audit,
    write_context_balance_deep_audit,
)

pytestmark = pytest.mark.skipif(
    not SHADOW_RANKINGS.exists(),
    reason="qb_te_context_balance_v1 shadow output is required",
)


def test_context_balance_deep_audit_preserves_active_baseline_hash() -> None:
    result = build_context_balance_deep_audit()

    assert result.active_hash_before == result.active_hash_after
    assert result.active_output_changed is False
    assert result.summary["sentinels_safe"] is True
    assert result.summary["contamination_safe"] is True
    assert result.summary["decision_board_blocked"] is True


def test_deep_audit_report_contains_required_sections() -> None:
    result = build_context_balance_deep_audit()
    report = result.deep_audit_report

    for section in (
        "## 1. Executive Summary",
        "## 7. QB-Specific Review",
        "## 8. TE-Specific Review",
        "## 9. RB/WR Collateral Review",
        "## 10. My Team Impact",
        "## Overcorrection Audit",
        "## 16. Recommendation Status",
    ):
        assert section in report
    assert "proposal-only audit" in report


def test_production_patch_proposal_is_proposal_only() -> None:
    result = build_context_balance_deep_audit()
    proposal = result.production_patch_proposal

    assert "No implementation or promotion occurred" in proposal
    assert "Do not promote shadow outputs directly" in proposal
    assert "User approval is required before any production patch" in proposal
    assert "Decision Board remains blocked" in proposal


def test_acceptance_criteria_are_broad_not_public_rank_targets() -> None:
    result = build_context_balance_deep_audit()
    proposal = result.production_patch_proposal
    forbidden = (
        "match fantasypros",
        "target rank",
        "public-rank target",
        "market-rank target",
        "league-rank target",
    )

    assert "## Candidate Acceptance Criteria For A Later Patch" in proposal
    assert not any(term in proposal.lower() for term in forbidden)
    assert "Top 25 should not be dominated by QBs" in proposal
    assert "RB/WR score values should not change" in proposal


def test_write_context_balance_deep_audit_creates_reports(tmp_path: Path) -> None:
    paths = write_context_balance_deep_audit(
        deep_audit_path=tmp_path / DEEP_AUDIT_REPORT.name,
        proposal_path=tmp_path / PRODUCTION_PATCH_PROPOSAL.name,
    )

    assert paths.deep_audit_report.exists()
    assert paths.production_patch_proposal.exists()
    assert "QB/TE Context Balance v1 Deep Audit" in paths.deep_audit_report.read_text(
        encoding="utf-8"
    )
    assert "Production Patch Proposal" in paths.production_patch_proposal.read_text(
        encoding="utf-8"
    )
