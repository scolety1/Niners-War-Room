from __future__ import annotations

from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_score_movement_audit_service import (
    DEFAULT_OLD_CHECKPOINT_ROWS,
    build_score_movement_audit,
    write_score_movement_audit,
)
from src.services.full_player_board_value_service import (
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
)

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)


pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists()
    or not DEFAULT_OLD_CHECKPOINT_ROWS.exists()
    or not DEFAULT_FULL_PLAYER_BOARD_ROWS.exists(),
    reason="local active pack and old/new Model v4 current-value rows are required",
)


def test_movement_audit_includes_every_old_checkpoint_row_matched_to_full_board() -> None:
    result = build_score_movement_audit()

    assert result.summary["old_new_matched_rows"] == 71
    assert len(result.rows) == result.summary["old_new_matched_rows"]
    assert all(row["score_delta"] != "" for row in result.rows)
    assert all(row["rank_delta"] != "" for row in result.rows)


def test_movement_audit_includes_buckets_severity_and_required_columns() -> None:
    result = build_score_movement_audit()
    first = result.rows[0]

    assert first["movement_bucket"]
    assert first["audit_severity"] in {"low", "medium", "high", "blocker"}
    assert first["requires_human_review"] in {"0", "1"}
    assert first["source_column_old"] == "checkpoint_review_score"
    assert first["source_column_new"] == "checkpoint_review_score"
    assert first["lineage_old"] == "review_v4_current_player"
    assert first["lineage_new"] == "review_v4_current_player"


def test_report_contains_required_readback_sections() -> None:
    result = build_score_movement_audit()
    report = result.report_text

    assert "# Full Board Score Movement Audit - 2026-06-08" in report
    assert "## Position Distribution Summary" in report
    assert "## Top 50 Full Board Players" in report
    assert "## Bottom 50 Scored Non-Kickers" in report
    assert "## My Team Movement" in report
    assert "## Sentinel And Contamination Checks" in report


def test_write_score_movement_audit_creates_csv_and_report(tmp_path: Path) -> None:
    rows_path = tmp_path / "full_board_score_movement_audit.csv"
    report_path = tmp_path / "FULL_BOARD_SCORE_MOVEMENT_AUDIT_20260608.md"

    paths = write_score_movement_audit(
        movement_rows_path=rows_path,
        report_path=report_path,
    )

    assert paths.movement_rows == rows_path
    assert paths.report == report_path
    assert "score_delta" in rows_path.read_text(encoding="utf-8")
    assert "full_board_rankings_ready_for_human_review" in report_path.read_text(
        encoding="utf-8"
    )


def test_sentinels_remain_comparison_only_and_current_lineage_is_admitted() -> None:
    result = build_score_movement_audit()

    assert result.summary["sentinel_lineage_ok"] is True
    assert result.summary["contamination_check_passed"] is True


def test_full_board_coverage_still_scores_only_qb_rb_wr_te_and_fails_kickers_closed() -> None:
    result = build_score_movement_audit()

    assert result.summary["active_rows"] == 240
    assert result.summary["qb_rb_wr_te_rows"] == 232
    assert result.summary["k_rows"] == 8
    assert result.summary["nwr_scored_rows"] == 232
    assert result.summary["no_private_score_rows"] == 8
    assert result.summary["source_repair_needed_rows"] == 8


def test_no_legacy_market_or_league_score_contamination_in_full_board_rows() -> None:
    result = build_score_movement_audit()

    assert result.summary["contamination_check_passed"] is True
    assert all(row["lineage_new"] == "review_v4_current_player" for row in result.rows)
    assert all(row["source_column_new"] == "checkpoint_review_score" for row in result.rows)
