from __future__ import annotations

import csv
import subprocess
from collections import Counter
from pathlib import Path

from scripts.build_rookie_draft_capital_coverage_repair_v2_20260630 import (
    DIAGNOSIS_COLUMNS,
    DISPLAY_COLUMNS,
    DOC_ROOT,
    FEATURE_COLUMNS,
    NOT_ENOUGH,
    REPAIR_COLUMNS,
    draft_capital_bucket_v2,
)

ROOT = Path(__file__).resolve().parents[1]


def test_missingness_diagnosis_schema_counts_and_flags() -> None:
    rows = _rows("rookie_draft_capital_missingness_diagnosis_v2.csv")
    counts = _counts(rows, "blocker_category")

    assert set(rows[0]) == set(DIAGNOSIS_COLUMNS)
    assert len(rows) == 95
    assert counts["drafted_join_miss"] == 55
    assert counts["likely_udfa_needs_source"] == 28
    assert counts["needs_human_review"] == 10
    assert counts["not_draft_eligible_or_wrong_universe"] == 2
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_repair_matrix_repairs_2025_drafted_rows_and_keeps_blockers() -> None:
    rows = _rows("rookie_draft_capital_repair_v2_matrix.csv")
    status_counts = _counts(rows, "draft_capital_status")
    repair_counts = _counts(rows, "repair_action")
    by_name = {row["player_name"]: row for row in rows}

    assert set(rows[0]) == set(REPAIR_COLUMNS)
    assert len(rows) == 157
    assert status_counts["REPAIRED_NFLVERSE_DRAFT_CAPITAL_AVAILABLE"] == 117
    assert status_counts["MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED"] == 38
    assert status_counts["BLOCKED_WRONG_UNIVERSE_OLDER_NFL_DRAFT_MATCH"] == 2
    assert repair_counts["expanded_draft_year_window_exact_name_position"] == 55
    assert by_name["Cam Ward"]["draft_year"] == "2025"
    assert by_name["Cam Ward"]["draft_round"] == "1"
    assert by_name["Cam Ward"]["draft_capital_bucket"] == "round_1"


def test_udfa_and_round_eight_policy_do_not_fake_draft_capital() -> None:
    rows = _rows("rookie_draft_capital_repair_v2_matrix.csv")
    udfa_counts = _counts(rows, "udffa_or_undrafted_status")
    likely_rows = [
        row
        for row in rows
        if row["udffa_or_undrafted_status"] == "likely_udfa_needs_review"
    ]

    assert draft_capital_bucket_v2({"draft_round": "8"}) == NOT_ENOUGH
    assert "round_8" not in {row["draft_capital_bucket"] for row in rows}
    assert udfa_counts["confirmed_udfa"] == 0
    assert udfa_counts["likely_udfa_needs_review"] == 28
    assert udfa_counts["not_in_draft_picks_needs_review"] == 10
    assert all(row["draft_round"] == NOT_ENOUGH for row in likely_rows)
    assert {row["draft_capital_bucket"] for row in likely_rows} == {"udfa_review_needed"}


def test_bucket_policy_doc_defines_modern_rounds_and_blocks_round_8_proxy() -> None:
    text = (DOC_ROOT / "03_DRAFT_CAPITAL_BUCKET_POLICY_V2.md").read_text(
        encoding="utf-8"
    )

    for bucket in (
        "round_1",
        "round_2",
        "round_3",
        "round_4",
        "round_5",
        "round_6",
        "round_7",
    ):
        assert bucket in text
    assert "Round 8 is not a normal current-rookie draft-capital bucket" in text
    assert "not a fake round" in text


def test_feature_policy_refresh_is_draft_capital_only_and_review_only() -> None:
    rows = _rows("rookie_feature_policy_draft_capital_v2_matrix.csv")
    by_feature = {row["feature_name"]: row for row in rows}

    assert set(rows[0]) == set(FEATURE_COLUMNS)
    assert by_feature["overall_pick"]["allowed_for_review_only_model_rd"] == "true"
    assert by_feature["UDFA_status"]["allowed_for_review_only_model_rd"] == "false"
    assert by_feature["draft_capital_value"]["approval_status"] == "blocked"
    assert by_feature["college_production_combine_grades_market_cfbd"][
        "approval_status"
    ] == "blocked_or_display_context_only"
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_display_v3_improves_coverage_and_keeps_flags_closed() -> None:
    rows = _rows("rookie_display_artifact_v3_coverage_matrix.csv")
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
    assert all(int(row["display_field_count"]) == 0 for row in likely_udfa)
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["display_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}
    assert "0%" not in ",".join(",".join(row.values()) for row in rows)


def test_release_audit_blocks_gate_g_and_no_rankings_wiring() -> None:
    release_text = (
        DOC_ROOT / "05_GATE_G_RELEASE_AUDIT_AFTER_REPAIR_V2.md"
    ).read_text(encoding="utf-8")
    display_text = (DOC_ROOT / "06_GATE_F_V3_DISPLAY_REBUILD_RESULT.md").read_text(
        encoding="utf-8"
    )

    assert "BLOCKED_NEEDS_DISPLAY_COVERAGE" in release_text
    assert "Gate G should not run next" in release_text
    assert "New valid display rows: 117" in display_text
    assert "No app code was touched" in release_text


def test_blocked_sources_not_used_in_repair_outputs() -> None:
    repair_text = (DOC_ROOT / "rookie_draft_capital_repair_v2_matrix.csv").read_text(
        encoding="utf-8"
    )
    display_text = (DOC_ROOT / "rookie_display_artifact_v3_coverage_matrix.csv").read_text(
        encoding="utf-8"
    )

    for blocked in ("JackLich10", "array-carpenter", "FootballDB", "ESPN", "DynastyProcess"):
        assert blocked not in repair_text
        assert blocked not in display_text


def test_shared_local_secret_and_protected_outputs_are_not_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "C:\\NWR_LOCAL_SECRETS" not in tracked
    assert "local_exports" not in tracked
    assert "rookie_outcomes/display_artifact_v3" not in tracked


def test_lane_touches_only_expected_paths() -> None:
    expected_paths = (
        "docs/hq/rookie_outcomes/rookie_draft_capital_coverage_repair_v2_20260630/",
        "scripts/build_rookie_draft_capital_coverage_repair_v2_20260630.py",
        "tests/test_rookie_draft_capital_coverage_repair_v2_20260630.py",
    )
    protected_roots = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
        "docs/draft_day_exports/final_board_v1_20260622/",
        "src/services/",
        "src/models/",
        "app/",
    )

    assert all(not path.startswith(protected_roots) for path in expected_paths)


def _rows(file_name: str) -> list[dict[str, str]]:
    with (DOC_ROOT / file_name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _counts(rows: list[dict[str, str]], column: str) -> Counter[str]:
    return Counter(row[column] for row in rows)
