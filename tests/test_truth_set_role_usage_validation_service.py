from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_role_usage_validation_service import (
    TRUTH_SET_ROLE_USAGE_STRICT_HEADER,
    validate_truth_set_role_usage_export,
)


def test_clean_role_usage_export_passes_validation(tmp_path: Path) -> None:
    source = tmp_path / "role.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Clean Receiver",
                "position": "WR",
                "nfl_team": "SF",
                "season": "2025",
                "snap_share": "78.2",
                "route_participation": "82.1",
                "routes_run": "510",
                "target_share": "22.5%",
                "targets_per_route_run": "0.24",
                "yards_per_route_run": "2.1",
                "red_zone_touches": "12",
                "goal_line_touches": "2",
                "source_name": "Provider",
                "source_url": "https://example.com/role",
                "source_date": "2026-05-15",
                "confidence_0_100": "90",
                "notes": "Clean row.",
            }
        ],
    )

    result = validate_truth_set_role_usage_export(
        source,
        expected_players=("Clean Receiver",),
    )

    assert result.status == "valid_preview_ready"
    assert result.summary["header_status"] == "exact"
    assert result.flags == ()


def test_prose_rb_workload_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "role.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Prose RB",
                "position": "RB",
                "season": "2025",
                "rb_carry_share": "split backfield; about half",
                "weighted_opportunities": "heavy role",
                "source_name": "Provider",
                "source_url": "https://example.com/role",
            }
        ],
    )

    result = validate_truth_set_role_usage_export(source)
    flags = [flag for flag in result.flags if flag["flag"] == "prose_in_numeric_field"]

    assert result.status == "rejected"
    assert {flag["column"] for flag in flags} == {"rb_carry_share", "weighted_opportunities"}


def test_question_marks_and_urls_in_numeric_fields_are_rejected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "role.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Bad Role",
                "season": "2025",
                "target_share": "18?",
                "routes_run": "https://example.com/500",
                "source_name": "Provider",
                "source_url": "https://example.com/role",
            }
        ],
    )

    result = validate_truth_set_role_usage_export(source)
    flags = {flag["flag"] for flag in result.flags}

    assert "uncertain_numeric_marker" in flags
    assert "embedded_url_in_numeric_field" in flags


def test_shifted_source_columns_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "role.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Shifted Role",
                "season": "2025",
                "routes_run": "300",
                "source_name": "Provider https://example.com/role",
                "source_url": "manual extraction",
            }
        ],
    )

    result = validate_truth_set_role_usage_export(source)

    assert result.status == "rejected"
    assert sum(
        flag["flag"] == "source_field_not_separated" for flag in result.flags
    ) == 2


def test_header_mismatch_and_malformed_width_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "role.csv"
    source.write_text("player_name,routes_run\nToo,Short,300\n", encoding="utf-8")

    result = validate_truth_set_role_usage_export(source)
    flags = {flag["flag"] for flag in result.flags}

    assert result.status == "rejected"
    assert "header_mismatch" in flags
    assert "malformed_row_width" in flags


def test_expected_player_coverage_requires_one_row_per_player(tmp_path: Path) -> None:
    source = tmp_path / "role.csv"
    _write_rows(
        source,
        [
            {"player_name": "Duplicate Player", "season": "2025"},
            {"player_name": "Duplicate Player", "season": "2025"},
        ],
    )

    result = validate_truth_set_role_usage_export(
        source,
        expected_players=("Duplicate Player", "Missing Player"),
    )
    flags = {flag["flag"] for flag in result.flags}

    assert "duplicate_player_row" in flags
    assert "missing_expected_player" in flags


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRUTH_SET_ROLE_USAGE_STRICT_HEADER)
        writer.writeheader()
        for row in rows:
            stable = {field: "" for field in TRUTH_SET_ROLE_USAGE_STRICT_HEADER}
            stable.update(row)
            writer.writerow(stable)
