from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_truth_set_coverage_audit_service import (
    TRUTH_SET_COVERAGE_AUDIT_HEADER,
    build_model_v4_truth_set_coverage_audit,
)


def test_truth_set_coverage_audit_reports_current_truth_set() -> None:
    audit = build_model_v4_truth_set_coverage_audit()

    assert len(audit.rows) == 80
    assert set(audit.rows[0]) == set(TRUTH_SET_COVERAGE_AUDIT_HEADER)
    assert audit.summary["truth_set_players"] == "80"


def test_truth_set_coverage_audit_marks_incoming_rookie_production_not_blocking(
    tmp_path: Path,
) -> None:
    truth_path = tmp_path / "truth.csv"
    _write_rows(
        truth_path,
        [
            "player_name",
            "position",
            "nfl_team",
            "truth_set_group",
            "reason_included",
            "lifecycle_expected",
            "roster_context",
            "source_priority",
        ],
        [
            {
                "player_name": "Test Rookie",
                "position": "RB",
                "nfl_team": "TST",
                "truth_set_group": "incoming_rookie",
                "reason_included": "test",
                "lifecycle_expected": "incoming_rookie",
                "roster_context": "draft_room_control",
                "source_priority": "critical",
            }
        ],
    )
    young_path = tmp_path / "young.csv"
    _write_rows(
        young_path,
        ["player_name", "draft_capital_prior_score"],
        [{"player_name": "Test Rookie", "draft_capital_prior_score": "90"}],
    )

    audit = build_model_v4_truth_set_coverage_audit(
        truth_set_path=truth_path,
        v3_2_root=tmp_path / "missing_v3_2",
        active_source_root=tmp_path / "missing_active",
        young_bridge_path=young_path,
        roster_rank_path=tmp_path / "missing_roster.csv",
    )

    row = audit.rows[0]
    assert "missing_production" not in row["formula_rebuild_blockers"]
    assert "missing_young_prior" not in row["formula_rebuild_blockers"]
    assert row["young_prior_coverage"] == "preview_only"


def test_truth_set_coverage_audit_blocks_core_nfl_player_missing_evidence(
    tmp_path: Path,
) -> None:
    truth_path = tmp_path / "truth.csv"
    _write_rows(
        truth_path,
        [
            "player_name",
            "position",
            "nfl_team",
            "truth_set_group",
            "reason_included",
            "lifecycle_expected",
            "roster_context",
            "source_priority",
        ],
        [
            {
                "player_name": "Missing Veteran",
                "position": "WR",
                "nfl_team": "TST",
                "truth_set_group": "test",
                "reason_included": "test",
                "lifecycle_expected": "established_veteran",
                "roster_context": "league_context",
                "source_priority": "critical",
            }
        ],
    )

    audit = build_model_v4_truth_set_coverage_audit(
        truth_set_path=truth_path,
        v3_2_root=tmp_path / "missing_v3_2",
        active_source_root=tmp_path / "missing_active",
        young_bridge_path=tmp_path / "missing_young.csv",
        roster_rank_path=tmp_path / "missing_roster.csv",
    )

    row = audit.rows[0]
    assert row["readiness_for_fixture_testing"] == "blocked_missing_input"
    assert "missing_identity" in row["formula_rebuild_blockers"]
    assert "missing_production" in row["formula_rebuild_blockers"]
    assert "missing_first_downs" in row["formula_rebuild_blockers"]
    assert "missing_usage" in row["formula_rebuild_blockers"]


def test_truth_set_coverage_audit_writes_csv_and_markdown(tmp_path: Path) -> None:
    csv_path = tmp_path / "audit.csv"
    md_path = tmp_path / "audit.md"

    build_model_v4_truth_set_coverage_audit(
        output_csv_path=csv_path,
        output_md_path=md_path,
    )

    assert csv_path.exists()
    assert md_path.exists()
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(TRUTH_SET_COVERAGE_AUDIT_HEADER)
        assert len(list(reader)) == 80
    assert "Formula Rebuild Blockers" in md_path.read_text(encoding="utf-8")


def _write_rows(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
