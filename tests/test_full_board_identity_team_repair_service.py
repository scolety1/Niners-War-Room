from __future__ import annotations

from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_identity_team_repair_service import (
    DEFAULT_REPAIR_AUDIT_CSV,
    DEFAULT_REPAIR_REPORT,
    build_identity_team_repair_audit,
    write_identity_team_repair_audit,
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


def test_identity_team_source_precedence_report_exists_in_result() -> None:
    result = build_identity_team_repair_audit()

    assert "Current NFL team/status priority" in result.report_text
    assert "rotowire_nfl_team_status" in result.report_text
    assert "fact_rosters.nfl_team" in result.report_text
    assert "fact_official_rankings.nfl_team" in result.report_text
    assert "old 80-row checkpoint teams" in result.report_text


def test_known_mismatch_rows_are_in_repair_audit_as_historical_context() -> None:
    result = build_identity_team_repair_audit()
    rows = {row["player"]: row for row in result.rows}

    for player in ("Jaylen Waddle", "Kenneth Walker III", "Mike Evans"):
        row = rows[player]
        assert row["team_resolution_status"] == "resolved_historical_team_only"
        assert row["is_historical_only_mismatch"] == "1"
        assert row["is_current_source_conflict"] == "0"
        assert row["should_remain_quarantined"] == "0"


def test_unresolved_missing_current_team_rows_remain_quarantined() -> None:
    result = build_identity_team_repair_audit()
    unresolved = [
        row
        for row in result.rows
        if row["team_resolution_status"] == "unresolved_missing_current_team_source"
    ]

    assert unresolved
    assert all(row["should_remain_quarantined"] == "1" for row in unresolved)
    assert all(row["chosen_canonical_team"] == "" for row in unresolved)


def test_warning_flags_preserve_raw_model_warning_receipts() -> None:
    result = build_identity_team_repair_audit()
    waddle = next(row for row in result.rows if row["player"] == "Jaylen Waddle")

    assert "team_mismatch_or_missing_model_team" in waddle["warning_flags_before"]
    assert "rotowire_current_team_status_warning" in waddle["warning_flags_after"]
    assert "team_mismatch_or_missing_model_team" not in waddle["warning_flags_after"]


def test_write_identity_team_repair_audit_creates_csv_and_report(tmp_path: Path) -> None:
    paths = write_identity_team_repair_audit(
        audit_csv=tmp_path / DEFAULT_REPAIR_AUDIT_CSV.name,
        report_path=tmp_path / DEFAULT_REPAIR_REPORT.name,
    )

    assert paths.audit_csv.exists()
    assert paths.report.exists()
    assert "team_resolution_status" in paths.audit_csv.read_text(encoding="utf-8")
    assert "Canonical Source Precedence" in paths.report.read_text(encoding="utf-8")
