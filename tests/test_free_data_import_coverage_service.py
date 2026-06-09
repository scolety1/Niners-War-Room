from __future__ import annotations

import csv
import shutil
from pathlib import Path

from src.services.free_data_import_coverage_service import (
    build_free_data_import_coverage_matrix,
    write_free_data_import_coverage_matrix,
)
from src.services.real_input_template_service import (
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)

TEMPLATE_ROOT = Path("templates/real_data_inputs/nflverse_stats_upgrade")


def test_free_data_coverage_matrix_marks_direct_partial_and_external_buckets() -> None:
    report = build_free_data_import_coverage_matrix(TEMPLATE_ROOT)
    by_bucket = {row["feature_bucket"]: row for row in report.coverage_rows}

    assert report.raw_import_status == "ready"
    assert by_bucket["production"]["support_status"] == "direct_free_import"
    assert by_bucket["production"]["validation_status"] == "ready"
    assert "passing_yards" in str(by_bucket["production"]["required_fields"])
    assert by_bucket["first-down/TD fit"]["support_status"] == "direct_free_import"
    assert "rushing_first_downs" in str(by_bucket["first-down/TD fit"]["required_fields"])
    assert by_bucket["role/usage"]["support_status"] == "partial_free_import"
    assert by_bucket["role/usage"]["validation_status"] == "review"
    assert by_bucket["projection"]["support_status"] == "external_csv_required"
    assert by_bucket["projection"]["validation_status"] == "external_required"
    assert by_bucket["market/liquidity"]["validation_status"] == "external_required"
    assert report.issues == ()


def test_free_data_field_matrix_proves_required_columns_exist() -> None:
    report = build_free_data_import_coverage_matrix(TEMPLATE_ROOT)
    field_rows = {
        (row["feature_bucket"], row["local_file"], row["field"]): row
        for row in report.field_rows
    }

    assert field_rows[
        ("opportunity", "nflverse_player_stats_weekly.csv", "air_yards_share")
    ]["template_column_present"] is True
    assert field_rows[
        ("opportunity", "nflverse_player_stats_weekly.csv", "wopr")
    ]["template_column_present"] is True
    assert field_rows[
        ("identity", "nflverse_identity_map.csv", "sleeper_id")
    ]["source_status"] == "import_contract_field"


def test_free_data_matrix_surfaces_missing_contract_fields(tmp_path: Path) -> None:
    source_root = tmp_path / "nflverse_stats_upgrade"
    shutil.copytree(TEMPLATE_ROOT, source_root)
    _rewrite_header_without(
        source_root / "nflverse_player_stats_weekly.csv",
        "receiving_first_downs",
    )

    report = build_free_data_import_coverage_matrix(source_root)
    by_bucket = {row["feature_bucket"]: row for row in report.coverage_rows}

    assert by_bucket["first-down/TD fit"]["validation_status"] == "blocked"
    assert "receiving_first_downs" in str(by_bucket["first-down/TD fit"]["missing_fields"])
    assert report.issues


def test_free_data_matrix_export_writes_auditable_csvs(tmp_path: Path) -> None:
    report = build_free_data_import_coverage_matrix(TEMPLATE_ROOT)
    paths = write_free_data_import_coverage_matrix(tmp_path / "export", report)

    assert set(paths) == {
        "coverage_matrix",
        "field_matrix",
        "adapter_matrix",
        "summary",
    }
    with paths["coverage_matrix"].open(newline="", encoding="utf-8") as handle:
        header = tuple(next(csv.reader(handle)))
    assert "feature_bucket" in header
    assert "scoring_effect" in header


def test_adapter_matrix_keeps_scraping_false_for_supported_free_sources() -> None:
    report = build_free_data_import_coverage_matrix(TEMPLATE_ROOT)
    by_file = {row["local_file"]: row for row in report.adapter_rows}

    assert by_file["nflverse_player_stats_weekly.csv"]["scraping_required"] == "false"
    assert by_file["nflverse_snap_counts_weekly.csv"]["scraping_required"] == "false"
    assert by_file["nflverse_depth_chart_weekly.csv"]["scraping_required"] == "false"
    assert "rushing_first_downs" in str(
        by_file["nflverse_player_stats_weekly.csv"]["key_fields"]
    )


def _rewrite_header_without(path: Path, removed_column: str) -> None:
    header = [
        column
        for column in NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[path.name]
        if column != removed_column
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
