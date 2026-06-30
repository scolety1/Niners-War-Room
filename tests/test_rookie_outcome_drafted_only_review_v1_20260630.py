from __future__ import annotations

import csv
import subprocess
from collections import Counter
from pathlib import Path

from scripts.build_rookie_outcome_drafted_only_review_v1_20260630 import (
    AUDIT_COLUMNS,
    COVERAGE_COLUMNS,
    ENTRY_STATUS_PATH,
    OUTPUT_ROOT,
)

ROOT = Path(__file__).resolve().parents[1]


def test_entry_status_dependency_exists_and_marks_drafted_rows() -> None:
    rows = _read_path(ENTRY_STATUS_PATH)
    counts = Counter(row["entry_status"] for row in rows)

    assert len(rows) == 4653
    assert counts["drafted"] == 1999
    assert counts["likely_udfa_needs_review"] == 2514
    assert counts["wrong_universe"] == 138
    assert counts["name_collision"] == 2
    assert counts["confirmed_udfa"] == 0
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_drafted_only_player_audit_schema_counts_and_flags() -> None:
    rows = _rows("drafted_only_outcome_player_audit.csv")
    statuses = Counter(row["outcome_window_status"] for row in rows)

    assert set(rows[0]) == set(AUDIT_COLUMNS)
    assert len(rows) == 1999
    assert {row["entry_status"] for row in rows} == {"drafted"}
    assert statuses["complete_5y_review_only_labels"] == 310
    assert statuses["partial_or_censored_review_only_labels"] == 587
    assert statuses["missing_outcome_label"] == 1102
    assert sum(row["has_rookie_year_label"] == "true" for row in rows) == 818
    assert sum(row["has_2y_label"] == "true" for row in rows) == 737
    assert sum(row["has_3y_label"] == "true" for row in rows) == 501
    assert sum(row["has_5y_label"] == "true" for row in rows) == 319
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_drafted_only_coverage_schema_and_year_position_groups() -> None:
    rows = _rows("drafted_only_outcome_coverage.csv")

    assert set(rows[0]) == set(COVERAGE_COLUMNS)
    assert len(rows) == 100
    assert sum(int(row["drafted_count"]) for row in rows) == 1999
    assert sum(int(row["rookie_year_label_count"]) for row in rows) == 818
    assert sum(int(row["2y_label_count"]) for row in rows) == 737
    assert sum(int(row["3y_label_count"]) for row in rows) == 501
    assert sum(int(row["5y_label_count"]) for row in rows) == 319
    assert sum(int(row["missing_label_count"]) for row in rows) == 1102
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_policy_docs_keep_model_app_and_udfa_gates_blocked() -> None:
    manifest = (OUTPUT_ROOT / "artifact_manifest.md").read_text(encoding="utf-8")
    gate_status = (OUTPUT_ROOT / "gate_f_gate_g_status.md").read_text(encoding="utf-8")
    udfa_report = (OUTPUT_ROOT / "udfa_blocker_report.md").read_text(encoding="utf-8")
    baseline = (OUTPUT_ROOT / "drafted_only_baseline_plan.md").read_text(
        encoding="utf-8"
    )

    assert "YELLOW_DRAFTED_ONLY_REVIEW_READY" in manifest
    assert "UDFA modeling remains blocked" in manifest
    assert "Gate G remains blocked" in gate_status
    assert "No app or Rankings wiring is approved" in gate_status
    assert "Confirmed UDFA count from hygiene artifact: 0" in udfa_report
    assert "Fake round 8 is not allowed" in udfa_report
    assert "No model was trained or tuned" in baseline


def test_no_udfa_rows_are_included_in_drafted_only_audit() -> None:
    text = (OUTPUT_ROOT / "drafted_only_outcome_player_audit.csv").read_text(
        encoding="utf-8"
    )

    assert "likely_udfa_needs_review" not in text
    assert "confirmed_udfa" not in text
    assert "round_8" not in text
    assert "0%" not in text


def test_forbidden_shared_local_secret_and_protected_paths_are_not_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    normalized_status = status.replace("\\", "/")

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "C:\\NWR_LOCAL_SECRETS" not in tracked
    assert "local_exports" not in tracked
    assert "app/" not in normalized_status
    assert "src/services/" not in normalized_status
    assert "docs/draft_day_exports/final_board_v1_20260622/" not in normalized_status
    assert "latest_candidate" not in normalized_status
    assert "latest_approved" not in normalized_status


def _rows(file_name: str) -> list[dict[str, str]]:
    return _read_path(OUTPUT_ROOT / file_name)


def _read_path(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
