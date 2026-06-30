from __future__ import annotations

import csv
import subprocess
from collections import Counter
from pathlib import Path

from scripts.build_apply_udfa_review_recommendations_v1_20260630 import (
    APPLICATION_COLUMNS,
    NOT_ENOUGH,
    OUTPUT_ROOT,
    RATE_COLUMNS,
    SHARED_DISPLAY_ROOT,
    V5_DISPLAY_COLUMNS,
)

ROOT = Path(__file__).resolve().parents[1]


def test_application_schema_counts_and_flags() -> None:
    rows = _rows("udfa_review_application_v1.csv")
    decisions = Counter(row["human_decision"] for row in rows)

    assert set(rows[0]) == set(APPLICATION_COLUMNS)
    assert len(rows) == 38
    assert decisions["CONFIRM_UDFA_REVIEW_ONLY"] == 28
    assert decisions["KEEP_UNKNOWN"] == 10
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["source_truth_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}


def test_approved_by_human_only_for_accepted_udfa_review_status() -> None:
    rows = _rows("udfa_review_application_v1.csv")
    accepted = [row for row in rows if row["human_decision"] == "CONFIRM_UDFA_REVIEW_ONLY"]
    unknown = [row for row in rows if row["human_decision"] == "KEEP_UNKNOWN"]

    assert len(accepted) == 28
    assert len(unknown) == 10
    assert {row["approved_by_human"] for row in accepted} == {"true"}
    assert {row["approval_scope"] for row in accepted} == {"udfa_status_review_only"}
    assert {row["udfa_status"] for row in accepted} == {"confirmed_udfa_review_only"}
    assert {row["approved_by_human"] for row in unknown} == {"false"}
    assert {row["approval_scope"] for row in unknown} == {"none"}
    assert {row["udfa_status"] for row in unknown} == {"unknown"}


def test_v5_display_schema_and_coverage_counts() -> None:
    rows = _rows("rookie_display_artifact_v5_coverage_matrix.csv")
    statuses = Counter(row["display_status"] for row in rows)
    udfa_statuses = Counter(row["udfa_status"] for row in rows)

    assert set(rows[0]) == set(V5_DISPLAY_COLUMNS)
    assert len(rows) == 157
    assert statuses["review_only_display_fields_available"] == 117
    assert statuses["confirmed_udfa_review_only_status_available"] == 28
    assert statuses[NOT_ENOUGH] == 10
    assert statuses["wrong_universe_blocked"] == 2
    assert udfa_statuses["confirmed_udfa_review_only"] == 28
    assert udfa_statuses["unknown"] == 10
    assert udfa_statuses["wrong_universe_blocked"] == 2
    assert sum(row["status_display_available"] == "true" for row in rows) == 145


def test_confirmed_udfa_rows_are_status_only_with_no_probabilities() -> None:
    rows = _rows("rookie_display_artifact_v5_coverage_matrix.csv")
    accepted = [row for row in rows if row["udfa_status"] == "confirmed_udfa_review_only"]

    assert len(accepted) == 28
    assert {row["display_field_count"] for row in accepted} == {"0"}
    assert {row["outcome_display_field_count"] for row in accepted} == {"0"}
    assert {row["status_display_available"] for row in accepted} == {"true"}
    assert {row["draft_capital_bucket"] for row in accepted} == {"udfa_review_only"}
    for row in accepted:
        assert all(row[column] == NOT_ENOUGH for column in RATE_COLUMNS)
        joined = ",".join(row.values()).lower()
        assert "probability" not in joined
        assert "0%" not in joined


def test_unknown_and_wrong_universe_rows_remain_blocked() -> None:
    rows = _rows("rookie_display_artifact_v5_coverage_matrix.csv")
    unknown = [row for row in rows if row["human_decision"] == "KEEP_UNKNOWN"]
    wrong = [row for row in rows if row["display_status"] == "wrong_universe_blocked"]

    assert len(unknown) == 10
    assert {row["display_status"] for row in unknown} == {NOT_ENOUGH}
    assert {row["approved_by_human"] for row in unknown} == {"false"}
    assert {row["status_display_available"] for row in unknown} == {"false"}
    assert len(wrong) == 2
    assert {row["wrong_universe_flag"] for row in wrong} == {"true"}
    assert {row["status_display_available"] for row in wrong} == {"false"}


def test_v5_display_flags_are_closed_and_have_no_fake_round_eight() -> None:
    rows = _rows("rookie_display_artifact_v5_coverage_matrix.csv")
    text = (OUTPUT_ROOT / "rookie_display_artifact_v5_coverage_matrix.csv").read_text(
        encoding="utf-8"
    )

    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["display_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["source_truth_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}
    assert "round_8" not in text
    assert "0%" not in text


def test_gate_g_audit_blocks_rankings_wiring() -> None:
    text = (
        OUTPUT_ROOT / "GATE_G_RELEASE_AUDIT_AFTER_UDFA_APPLICATION_V1.md"
    ).read_text(encoding="utf-8")

    assert "BLOCKED_NEEDS_RANKINGS_WIRING_APPROVAL" in text
    assert "Rankings wiring was not touched" in text
    assert "Gate G should not run next" in text


def test_shared_v5_outputs_exist_but_are_not_tracked() -> None:
    expected = {
        "rookie_outcome_review_only_display_artifact_v5.csv",
        "rookie_outcome_review_only_display_coverage_summary_v5.csv",
        "rookie_outcome_review_only_display_manifest_v5.csv",
    }
    actual = {path.name for path in SHARED_DISPLAY_ROOT.glob("*.csv")}
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)

    assert expected.issubset(actual)
    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "rookie_outcomes/display_artifact_v5" not in tracked


def test_blocked_sources_and_protected_paths_are_not_used() -> None:
    output_text = "\n".join(
        path.read_text(encoding="utf-8") for path in OUTPUT_ROOT.glob("*.csv")
    )
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    normalized_status = status.replace("\\", "/")

    for blocked in (
        "JackLich",
        "array-carpenter",
        "FootballDB",
        "ESPN",
        "DynastyProcess",
        "Gmail",
    ):
        assert blocked not in output_text
    assert "app/" not in normalized_status
    assert "src/services/" not in normalized_status
    assert "docs/draft_day_exports/final_board_v1_20260622/" not in normalized_status


def _rows(file_name: str) -> list[dict[str, str]]:
    with (OUTPUT_ROOT / file_name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
