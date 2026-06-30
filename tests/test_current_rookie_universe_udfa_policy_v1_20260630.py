from __future__ import annotations

import csv
import subprocess
from collections import Counter
from pathlib import Path

from scripts.build_current_rookie_universe_udfa_policy_v1_20260630 import (
    DIAGNOSIS_COLUMNS,
    DISPLAY_COLUMNS,
    DOC_ROOT,
    NOT_ENOUGH,
    UNIVERSE_COLUMNS,
)

ROOT = Path(__file__).resolve().parents[1]


def test_current_rookie_universe_matrix_schema_counts_and_flags() -> None:
    rows = _rows("current_rookie_universe_matrix_v1.csv")
    counts = _counts(rows, "current_rookie_universe_status")

    assert set(rows[0]) == set(UNIVERSE_COLUMNS)
    assert len(rows) == 157
    assert counts["drafted_with_valid_draft_capital"] == 117
    assert counts["current_rookie_likely_udfa_review"] == 28
    assert counts["current_rookie_unknown_needs_human_review"] == 10
    assert counts["wrong_universe_name_collision"] == 2
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_udfa_source_policy_is_partial_and_does_not_confirm_udfas() -> None:
    policy_text = (DOC_ROOT / "02_UDFA_SOURCE_POLICY_GATE.md").read_text(
        encoding="utf-8"
    )
    universe = _rows("current_rookie_universe_matrix_v1.csv")

    assert "PARTIAL_UDFA_SOURCE_POLICY" in policy_text
    assert "Confirmed UDFA rows allowed by this policy: 0" in policy_text
    assert "not prove confirmed UDFA source truth" in policy_text
    assert "confirmed_udfa" not in {
        row["current_rookie_universe_status"] for row in universe
    }


def test_udfa_wrong_universe_diagnosis_schema_and_recommendations() -> None:
    rows = _rows("udfa_wrong_universe_diagnosis_v1.csv")
    udfa_counts = _counts(rows, "udfa_status_recommendation")
    wrong_counts = _counts(rows, "wrong_universe_recommendation")

    assert set(rows[0]) == set(DIAGNOSIS_COLUMNS)
    assert len(rows) == 30
    assert udfa_counts["likely_udfa_needs_review"] == 28
    assert udfa_counts["unknown_keep_not_enough_information"] == 2
    assert wrong_counts["wrong_universe_remove_from_rookie_artifact"] == 2
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_wrong_universe_rows_are_blocked_and_name_collision_flagged() -> None:
    universe = _rows("current_rookie_universe_matrix_v1.csv")
    display = _rows("rookie_display_artifact_v4_coverage_matrix.csv")
    wrong_universe = [row for row in universe if row["wrong_universe_flag"] == "true"]
    wrong_display = [row for row in display if row["wrong_universe_flag"] == "true"]

    assert len(wrong_universe) == 2
    assert {row["player_name"] for row in wrong_universe} == {"Elijah Moore"}
    assert {row["name_collision_flag"] for row in wrong_universe} == {"true"}
    assert {row["display_status"] for row in wrong_display} == {NOT_ENOUGH}
    assert {row["display_field_count"] for row in wrong_display} == {"0"}


def test_udfa_bucket_policy_has_no_round_eight_proxy() -> None:
    policy_text = (DOC_ROOT / "04_UDFA_BUCKET_DISPLAY_POLICY.md").read_text(
        encoding="utf-8"
    )
    display_text = (
        DOC_ROOT / "rookie_display_artifact_v4_coverage_matrix.csv"
    ).read_text(encoding="utf-8")

    assert "never fake round 8" in policy_text
    assert "round_8" not in display_text
    assert "0%" not in display_text


def test_display_v4_preserves_coverage_and_closed_flags() -> None:
    rows = _rows("rookie_display_artifact_v4_coverage_matrix.csv")
    valid = [row for row in rows if int(row["display_field_count"]) > 0]
    missing = [row for row in rows if row["display_status"] == NOT_ENOUGH]
    likely_udfa = [
        row
        for row in rows
        if row["udffa_or_undrafted_status"] == "likely_udfa_needs_review"
    ]

    assert set(rows[0]) == set(DISPLAY_COLUMNS)
    assert len(rows) == 157
    assert len(valid) == 117
    assert len(missing) == 40
    assert len(likely_udfa) == 28
    assert {row["display_field_count"] for row in likely_udfa} == {"0"}
    assert {row["udfa_display_status"] for row in likely_udfa} == {
        "likely_udfa_review_needed"
    }
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["display_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}


def test_gate_g_release_audit_blocks_next_gate() -> None:
    release_text = (
        DOC_ROOT / "05_GATE_G_RELEASE_AUDIT_AFTER_UDFA_REPAIR.md"
    ).read_text(encoding="utf-8")
    display_text = (DOC_ROOT / "06_GATE_F_V4_DISPLAY_REBUILD_RESULT.md").read_text(
        encoding="utf-8"
    )

    assert "BLOCKED_NEEDS_UDFA_REVIEW" in release_text
    assert "Gate G should not run next" in release_text
    assert "New valid display rows: 117" in display_text
    assert "Confirmed UDFA rows: 0" in display_text


def test_blocked_sources_not_used_in_outputs() -> None:
    output_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in DOC_ROOT.glob("*.csv")
    )

    for blocked in ("JackLich", "array-carpenter", "FootballDB", "ESPN", "DynastyProcess"):
        assert blocked not in output_text


def test_shared_local_secret_and_app_paths_are_not_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "C:\\NWR_LOCAL_SECRETS" not in tracked
    assert "local_exports" not in tracked
    assert "rookie_outcomes/display_artifact_v4" not in tracked
    assert "app/" not in status.replace("\\", "/")
    assert "src/services/" not in status.replace("\\", "/")
    assert "docs/draft_day_exports/final_board_v1_20260622/" not in status.replace(
        "\\",
        "/",
    )


def _rows(file_name: str) -> list[dict[str, str]]:
    with (DOC_ROOT / file_name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _counts(rows: list[dict[str, str]], column: str) -> Counter[str]:
    return Counter(row[column] for row in rows)
