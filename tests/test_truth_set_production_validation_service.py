from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_production_validation_service import (
    TRUTH_SET_PRODUCTION_STRICT_HEADER,
    validate_truth_set_production_export,
)


def test_clean_production_export_passes_validation(tmp_path: Path) -> None:
    source = tmp_path / "production.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Clean Player",
                "position": "WR",
                "nfl_team": "SF",
                "season": "2025",
                "games": "17",
                "targets": "100",
                "receptions": "70",
                "receiving_yards": "1000",
                "receiving_tds": "8",
                "receiving_first_downs": "52",
                "source_name": "NFL.com",
                "source_url": "https://www.nfl.com/stats/player-stats/",
                "source_date": "2026-05-15",
                "confidence_0_100": "95",
                "notes": "Clean row.",
            }
        ],
    )

    result = validate_truth_set_production_export(
        source,
        expected_players=("Clean Player",),
    )

    assert result.status == "valid_preview_ready"
    assert result.summary["header_status"] == "exact"
    assert result.flags == ()


def test_malformed_row_width_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "production.csv"
    source.write_text(
        ",".join(TRUTH_SET_PRODUCTION_STRICT_HEADER)
        + "\n"
        + "Too,Short,WR\n",
        encoding="utf-8",
    )

    result = validate_truth_set_production_export(source)

    assert result.status == "rejected"
    assert any(flag["flag"] == "malformed_row_width" for flag in result.flags)


def test_numeric_question_marks_and_embedded_urls_are_rejected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "production.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Bad Numeric",
                "position": "RB",
                "nfl_team": "DET",
                "season": "2025",
                "rushing_attempts": "??",
                "rushing_yards": "https://bad.example/123",
                "source_name": "NFL.com",
                "source_url": "https://www.nfl.com/stats/player-stats/",
            }
        ],
    )

    result = validate_truth_set_production_export(source)
    flags = {flag["flag"] for flag in result.flags}

    assert "uncertain_numeric_marker" in flags
    assert "embedded_url_in_numeric_field" in flags


def test_shifted_source_columns_are_rejected(tmp_path: Path) -> None:
    source = tmp_path / "production.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Shifted Source",
                "position": "WR",
                "nfl_team": "KC",
                "season": "2025",
                "targets": "90",
                "source_name": "NFL.com https://www.nfl.com/stats/",
                "source_url": "0 6 0 0",
            }
        ],
    )

    result = validate_truth_set_production_export(source)
    source_flags = [
        flag for flag in result.flags if flag["flag"] == "source_field_not_separated"
    ]

    assert result.status == "rejected"
    assert len(source_flags) == 2


def test_header_mismatch_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "production.csv"
    source.write_text("player_name,row_column_count\nMetadata Row,27\n", encoding="utf-8")

    result = validate_truth_set_production_export(source)

    assert result.status == "rejected"
    assert result.summary["header_status"] == "mismatch"
    assert any(flag["flag"] == "header_mismatch" for flag in result.flags)


def test_expected_player_coverage_requires_one_row_per_player(tmp_path: Path) -> None:
    source = tmp_path / "production.csv"
    _write_rows(
        source,
        [
            {"player_name": "Duplicate Player", "season": "2025"},
            {"player_name": "Duplicate Player", "season": "2025"},
        ],
    )

    result = validate_truth_set_production_export(
        source,
        expected_players=("Duplicate Player", "Missing Player"),
    )
    flags = {flag["flag"] for flag in result.flags}

    assert "duplicate_player_row" in flags
    assert "missing_expected_player" in flags


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRUTH_SET_PRODUCTION_STRICT_HEADER)
        writer.writeheader()
        for row in rows:
            stable = {field: "" for field in TRUTH_SET_PRODUCTION_STRICT_HEADER}
            stable.update(row)
            writer.writerow(stable)
