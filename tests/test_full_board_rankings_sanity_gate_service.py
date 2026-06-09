from __future__ import annotations

from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_rankings_sanity_gate_service import (
    DEFAULT_QB_SANITY_DOC,
    DEFAULT_SANITY_ISSUE_QUEUE,
    DEFAULT_SOURCE_QUARANTINE_CSV,
    DEFAULT_SOURCE_QUARANTINE_DOC,
    DEFAULT_TE_SANITY_DOC,
    QB_ANCHORS,
    TE_ANCHORS,
    build_rankings_sanity_gate,
    write_rankings_sanity_gate,
)
from src.services.full_board_score_movement_audit_service import DEFAULT_MOVEMENT_AUDIT_ROWS
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)


pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists()
    or not DEFAULT_FULL_PLAYER_BOARD_ROWS.exists()
    or not DEFAULT_MOVEMENT_AUDIT_ROWS.exists(),
    reason="local active pack and full-board audit rows are required",
)


def test_source_quarantine_excludes_resolved_historical_team_mismatch_anchors() -> None:
    result = build_rankings_sanity_gate()
    names = {row["player"] for row in result.source_quarantine_rows}

    assert "Jaylen Waddle" not in names
    assert "Kenneth Walker III" not in names
    assert "Mike Evans" not in names


def test_remaining_source_quarantine_rows_are_not_cleanly_trusted() -> None:
    result = build_rankings_sanity_gate()

    assert result.source_quarantine_rows
    assert all(row["trust_status"] != "Scored" for row in result.source_quarantine_rows)
    assert all(
        row["should_rank_normally"] == "no_source_quarantine_visible"
        for row in result.source_quarantine_rows
    )


def test_qb_and_te_reports_include_named_anchors() -> None:
    result = build_rankings_sanity_gate()

    for player in QB_ANCHORS:
        assert player in result.qb_doc
    for player in TE_ANCHORS:
        assert player in result.te_doc


def test_issue_queue_contains_buckets_severity_and_no_action_recommendations() -> None:
    result = build_rankings_sanity_gate()

    assert result.issue_rows
    assert {row["severity"] for row in result.issue_rows} <= {"high", "medium", "low"}
    assert any(row["issue_bucket"] == "qb_1qb_format_sanity" for row in result.issue_rows)
    assert any(row["issue_bucket"] == "te_no_premium_format_sanity" for row in result.issue_rows)
    forbidden = ("trade", "cut", "draft", "buy", "sell", "start", "sit", "target", "defer")
    for row in result.issue_rows:
        action = str(row["recommended_next_action"]).lower()
        assert not any(word in action for word in forbidden)


def test_sentinels_and_contamination_guardrails_hold() -> None:
    result = build_rankings_sanity_gate()

    assert result.summary["sentinels_safe"] is True
    assert result.summary["contamination_safe"] is True
    assert result.summary["qb_rb_wr_te_scored"] == 232
    assert result.summary["unscored_kickers"] == 8


def test_write_rankings_sanity_gate_creates_all_artifacts(tmp_path: Path) -> None:
    paths = write_rankings_sanity_gate(
        source_quarantine_csv=tmp_path / DEFAULT_SOURCE_QUARANTINE_CSV.name,
        source_quarantine_doc=tmp_path / DEFAULT_SOURCE_QUARANTINE_DOC.name,
        qb_sanity_doc=tmp_path / DEFAULT_QB_SANITY_DOC.name,
        te_sanity_doc=tmp_path / DEFAULT_TE_SANITY_DOC.name,
        issue_queue_csv=tmp_path / DEFAULT_SANITY_ISSUE_QUEUE.name,
    )

    assert paths.source_quarantine_csv.exists()
    assert paths.source_quarantine_doc.exists()
    assert paths.qb_sanity_doc.exists()
    assert paths.te_sanity_doc.exists()
    assert paths.issue_queue_csv.exists()
    assert "full_board_source_quarantine" in paths.source_quarantine_csv.name
    assert "issue_bucket" in paths.issue_queue_csv.read_text(encoding="utf-8")
