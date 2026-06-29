from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from scripts.build_rookie_source_expansion_coverage_runner_v1_20260630 import (
    DOC_ROOT,
    DRAFT_REPAIR_COLUMNS,
    NOT_ENOUGH,
    draft_capital_bucket,
)

ROOT = Path(__file__).resolve().parents[1]


def test_source_policy_matrix_blocks_unlicensed_and_scraped_sources() -> None:
    rows = _rows("rookie_source_intake_policy_matrix_v1.csv")
    by_source = {row["source_name"]: row for row in rows}

    assert by_source["nflverse / nflreadpy"]["factual_fields_allowed"] == "true"
    assert by_source["nflverse / nflreadpy"]["model_use_allowed"] == "false"
    assert by_source["JackLich10/nfl-draft-data"]["source_policy_verdict"] == (
        "BLOCKED_NEEDS_LICENSE_REVIEW"
    )
    assert by_source["array-carpenter/nfl-draft-data"]["source_policy_verdict"] == (
        "BLOCKED_NEEDS_LICENSE_REVIEW"
    )
    assert by_source["FootballDB"]["automation_allowed"] == "false"
    assert by_source["FootballDB"]["notes"] == "No collector, scraper, or ingestion."


def test_draft_capital_repair_schema_flags_and_coverage() -> None:
    rows = _rows("rookie_draft_capital_repair_coverage_matrix_v1.csv")
    repaired = [row for row in rows if row["draft_capital_status"].startswith("REPAIRED")]
    missing = [row for row in rows if row["draft_capital_status"].startswith("MISSING")]

    assert set(DRAFT_REPAIR_COLUMNS) == set(rows[0])
    assert len(rows) == 157
    assert len(repaired) == 62
    assert len(missing) == 95
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert all(row["draft_capital_bucket"] != "not_enough_information" for row in repaired)


def test_round_8_placeholders_and_udfa_absence_are_not_guessed() -> None:
    rows = _rows("rookie_draft_capital_repair_coverage_matrix_v1.csv")
    missing_rows = [
        row
        for row in rows
        if row["draft_capital_status"].startswith("MISSING")
    ]
    repaired_names = {
        row["player_name"]
        for row in rows
        if row["draft_capital_status"].startswith("REPAIRED")
    }

    assert draft_capital_bucket({"draft_round": "8", "draft_pick": "237"}) == NOT_ENOUGH
    assert "Seth McGowan" in repaired_names
    assert "Deion Burks" in repaired_names
    assert {row["is_udfa"] for row in missing_rows} == {NOT_ENOUGH}


def test_combine_measurements_are_factual_review_only_context() -> None:
    rows = _rows("rookie_combine_measurements_coverage_matrix_v1.csv")
    available = [
        row
        for row in rows
        if row["measurement_status"] == "PARTIAL_COMBINE_MEASUREMENT_AVAILABLE"
    ]

    assert len(rows) == 157
    assert len(available) == 72
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert "grade" not in ",".join(rows[0])


def test_feature_policy_refresh_separates_model_rd_from_display_context() -> None:
    rows = _rows("rookie_feature_policy_refresh_matrix_v1.csv")
    by_feature = {row["feature_name"]: row for row in rows}

    assert by_feature["draft_round"]["allowed_for_review_only_model_rd"] == "true"
    assert by_feature["overall_pick"]["allowed_for_review_only_model_rd"] == "true"
    assert by_feature["height"]["allowed_for_review_only_model_rd"] == "false"
    assert by_feature["height"]["allowed_for_display_context"] == "true"
    assert by_feature["ESPN_NFL_grades"]["approval_status"] == "blocked"
    assert by_feature["college_production"]["approval_status"] == "blocked"
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}


def test_display_v2_rebuild_improves_coverage_but_keeps_gate_g_blocked() -> None:
    rows = _rows("rookie_display_artifact_v2_coverage_matrix.csv")
    valid = [row for row in rows if int(row["display_field_count"]) > 0]
    missing = [row for row in rows if row["display_status"] == NOT_ENOUGH]
    release_text = (DOC_ROOT / "08_GATE_G_RELEASE_AUDIT.md").read_text(encoding="utf-8")

    assert len(rows) == 157
    assert len(valid) == 62
    assert len(missing) == 95
    assert {row["review_only"] for row in rows} == {"true"}
    assert {row["display_only"] for row in rows} == {"true"}
    assert {row["model_use_allowed"] for row in rows} == {"false"}
    assert {row["training_allowed"] for row in rows} == {"false"}
    assert {row["rankings_wiring_allowed"] for row in rows} == {"false"}
    assert "0%" not in ",".join(",".join(row.values()) for row in rows)
    assert "BLOCKED_NEEDS_DISPLAY_COVERAGE" in release_text


def test_gate_docs_declare_partial_verdicts_and_no_rankings_wiring() -> None:
    docs = {
        path.name: path.read_text(encoding="utf-8")
        for path in DOC_ROOT.glob("*.md")
    }

    assert "PARTIAL_SOURCE_INTAKE_POLICY" in docs["01_SOURCE_INTAKE_POLICY_AUDIT.md"]
    assert "PARTIAL_DRAFT_CAPITAL_COVERAGE_REPAIR" in docs["02_DRAFT_CAPITAL_COVERAGE_REPAIR.md"]
    assert "PARTIAL_COMBINE_MEASUREMENTS_REVIEW_ONLY" in docs[
        "03_COMBINE_MEASUREMENTS_FEATURE_INTAKE.md"
    ]
    assert "PARTIAL_REVIEW_ONLY_DISPLAY_ARTIFACT_V2" in docs[
        "07_GATE_F_REBUILD_DISPLAY_ARTIFACT.md"
    ]
    assert "Rankings wiring" in docs["08_GATE_G_RELEASE_AUDIT.md"]


def test_shared_data_outputs_are_not_tracked() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)

    assert "C:\\NWR_SHARED_DATA" not in tracked
    assert "rookie_outcomes/draft_capital_repair_v1" not in tracked
    assert "rookie_outcomes/combine_measurements_v1" not in tracked
    assert "rookie_outcomes/display_artifact_v2" not in tracked
    assert "local_exports" not in tracked


def test_no_app_or_protected_paths_are_touched_by_runner_lane() -> None:
    allowed_changes = {
        "docs/hq/rookie_outcomes/rookie_source_expansion_coverage_runner_v1_20260630/",
        "scripts/build_rookie_source_expansion_coverage_runner_v1_20260630.py",
        "tests/test_rookie_source_expansion_coverage_runner_v1_20260630.py",
    }
    protected_prefixes = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
        "docs/draft_day_exports/final_board_v1_20260622/",
        "src/services/",
        "src/models/",
        "app/",
    )

    assert all(not path.startswith(protected_prefixes) for path in allowed_changes)


def _rows(file_name: str) -> list[dict[str, str]]:
    with (DOC_ROOT / file_name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))
