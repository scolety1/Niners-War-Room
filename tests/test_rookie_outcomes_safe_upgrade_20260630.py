from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_outcomes_safe_upgrade_20260630 import (
    DISPLAY_COLUMNS,
    FEATURE_COLUMNS,
    GATE_COLUMNS,
    OUTPUT_ROOT,
    SOURCE_COLUMNS,
)

ROOT = Path(__file__).resolve().parents[1]


def test_gate_matrix_keeps_all_release_gates_closed() -> None:
    rows = _rows("rookie_safe_upgrade_gate_matrix.csv")
    by_gate = {row["gate_or_area"]: row for row in rows}

    assert set(rows[0]) == set(GATE_COLUMNS)
    assert by_gate["drafted_only_outcome_review"]["current_status"] == (
        "YELLOW_DRAFTED_ONLY_REVIEW_READY"
    )
    assert by_gate["udfa_modeling"]["current_status"] == (
        "BLOCKED_NO_APPROVED_UDFA_SOURCE"
    )
    assert by_gate["gate_g"]["current_status"] == (
        "BLOCKED_NEEDS_RANKINGS_WIRING_APPROVAL"
    )
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}


def test_source_policy_blocks_udfa_inference_and_blocked_sources() -> None:
    rows = _rows("rookie_safe_upgrade_source_policy_matrix.csv")
    by_source = {row["source_name"]: row for row in rows}

    assert set(rows[0]) == set(SOURCE_COLUMNS)
    assert by_source["nflverse draft_picks"]["model_use_allowed"] == "false"
    assert "UDFA confirmation from absence" in by_source["nflverse draft_picks"]["blocked_use"]
    assert by_source["CFBD review artifacts"]["source_policy_status"] == (
        "candidate_only_review_only"
    )
    assert by_source["Gmail / vendor / RotoWire / FantasyPros / FootballDB"][
        "source_policy_status"
    ] == "blocked"
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["source_truth_allowed"] for row in rows} == {"false"}


def test_feature_policy_has_no_probability_columns_or_fake_round_eight() -> None:
    rows = _rows("rookie_safe_upgrade_feature_policy_matrix.csv")
    by_feature = {row["feature_name"]: row for row in rows}
    text = (OUTPUT_ROOT / "rookie_safe_upgrade_feature_policy_matrix.csv").read_text(
        encoding="utf-8"
    )

    assert set(rows[0]) == set(FEATURE_COLUMNS)
    assert by_feature["draft_capital_bucket"]["missing_value_policy"] == (
        "Not enough information"
    )
    assert by_feature["likely_udfa_needs_review"]["allowed_for_review_reporting"] == (
        "false"
    )
    assert by_feature["CFBD production"]["model_use_allowed"] == "false"
    assert by_feature["future NFL production / Outcome labels"]["training_allowed"] == "false"
    assert {row["active_probability_column_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert "round_8" not in text
    assert "0%" not in text


def test_display_audit_is_review_only_and_does_not_release_gate_g() -> None:
    rows = _rows("rookie_safe_upgrade_display_artifact_audit.csv")
    row = rows[0]

    assert set(row) == set(DISPLAY_COLUMNS)
    assert row["row_count"] == "157"
    assert row["drafted_review_rate_rows"] == "117"
    assert row["confirmed_udfa_status_only_rows"] == "28"
    assert row["not_enough_information_rows"] == "10"
    assert row["wrong_universe_blocked_rows"] == "2"
    assert row["rankings_wiring_allowed_rows"] == "0"
    assert row["model_use_allowed_rows"] == "0"
    assert row["training_allowed_rows"] == "0"
    assert row["active_probability_columns_created"] == "0"
    assert row["review_only"] == "true"
    assert row["model_use_allowed"] == "false"
    assert row["training_allowed"] == "false"


def test_summary_and_blockers_keep_gate_f_gate_g_closed() -> None:
    summary = (OUTPUT_ROOT / "safe_upgrade_summary.md").read_text(encoding="utf-8")
    blockers = (OUTPUT_ROOT / "remaining_blockers.md").read_text(encoding="utf-8")
    manifest = (OUTPUT_ROOT / "artifact_manifest.md").read_text(encoding="utf-8")

    assert "YELLOW_SAFE_UPGRADE_REVIEW_ONLY" in manifest
    assert "No active rookie probability columns" in summary
    assert "Gate F model-ready release remains blocked" in blockers
    assert "Gate G / Rankings wiring remains blocked" in blockers
    assert "Draft absence cannot confirm UDFA" in blockers
    assert "Fake round 8 is not allowed" in blockers


def test_no_forbidden_or_protected_paths_changed_by_lane() -> None:
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
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
    with (OUTPUT_ROOT / file_name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
