from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_projection_recompute_service import (
    TRUTH_SET_PROJECTION_RECOMPUTE_HEADER,
    recompute_truth_set_projection_rows,
    write_truth_set_projection_recompute,
)

PROJECTION_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "projection_source",
    "projection_date",
    "projected_games",
    "projected_starts",
    "projected_passing_yards",
    "projected_passing_tds",
    "projected_interceptions",
    "projected_rushing_attempts",
    "projected_rushing_yards",
    "projected_rushing_tds",
    "projected_targets",
    "projected_receptions",
    "projected_receiving_yards",
    "projected_receiving_tds",
    "projected_rushing_first_downs",
    "projected_receiving_first_downs",
    "projected_lve_points_if_calculable",
    "source_url",
    "export_method",
    "cost_status",
    "confidence_0_100",
    "notes",
)


def test_projection_recompute_uses_no_ppr_and_rejects_supplied_points(
    tmp_path: Path,
) -> None:
    source = tmp_path / "projections.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Receiver One",
                "position": "WR",
                "nfl_team": "SF",
                "projected_targets": "10",
                "projected_receptions": "8",
                "projected_receiving_yards": "100",
                "projected_receiving_tds": "1",
                "projected_lve_points_if_calculable": "999",
            }
        ],
    )

    result = recompute_truth_set_projection_rows(source)

    row = result.rows[0]
    assert row["receiving_points"] == 14.0
    assert row["recomputed_lve_points"] == 14.0
    assert row["recomputed_lve_points_no_first_downs"] == 14.0
    assert row["points_column_status"] == "supplied_points_rejected_not_lve"
    assert row["first_down_projection_status"] == "estimated_missing"
    assert row["projection_source_quality_status"] == "missing_first_down_projection"
    assert "missing_first_down_projection" in row["projection_source_quality_flags"]
    assert any(flag["flag"] == "supplied_points_rejected_not_lve" for flag in result.flags)


def test_projection_recompute_handles_qb_scoring_and_direct_first_downs(
    tmp_path: Path,
) -> None:
    source = tmp_path / "projections.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "QB One",
                "position": "QB",
                "nfl_team": "BAL",
                "projected_passing_yards": "250",
                "projected_passing_tds": "2",
                "projected_interceptions": "1",
                "projected_rushing_attempts": "8",
                "projected_rushing_yards": "50",
                "projected_rushing_tds": "1",
                "projected_rushing_first_downs": "4",
            }
        ],
    )

    row = recompute_truth_set_projection_rows(source).rows[0]

    assert row["passing_points"] == 14.33
    assert row["rushing_points"] == 9.0
    assert row["turnover_points"] == -1.0
    assert row["first_down_points"] == 1.6
    assert row["recomputed_lve_points"] == 23.93
    assert row["first_down_projection_status"] == "direct"


def test_projection_recompute_marks_missing_offensive_projection(tmp_path: Path) -> None:
    source = tmp_path / "projections.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Missing One",
                "position": "WR",
                "nfl_team": "LAC",
                "projection_source": "No projection",
            }
        ],
    )

    result = recompute_truth_set_projection_rows(source)

    row = result.rows[0]
    assert row["projection_availability_status"] == "missing_offensive_projection"
    assert row["first_down_projection_status"] == "missing"
    assert row["projection_source_quality_status"] == "missing_projection"
    assert "missing_projection" in row["projection_source_quality_flags"]
    assert row["points_column_status"] == "no_supplied_points"
    assert any(flag["flag"] == "missing_offensive_projection" for flag in result.flags)


def test_projection_recompute_flags_team_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "projections.csv"
    reference = tmp_path / "active.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Team Moved",
                "position": "WR",
                "nfl_team": "HOU",
                "projected_targets": "100",
                "projected_receiving_yards": "1000",
            }
        ],
    )
    _write_reference(reference, [{"player_name": "Team Moved", "team": "DET"}])

    result = recompute_truth_set_projection_rows(source, reference_player_path=reference)
    row = result.rows[0]

    assert row["reference_nfl_team"] == "DET"
    assert row["projection_source_quality_status"] == "team_mismatch"
    assert "team_mismatch" in row["projection_source_quality_flags"]
    assert any(flag["flag"] == "projection_team_mismatch" for flag in result.flags)


def test_projection_recompute_flags_high_value_missing_projection(
    tmp_path: Path,
) -> None:
    source = tmp_path / "projections.csv"
    reference = tmp_path / "active.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "High Value Missing",
                "position": "WR",
                "nfl_team": "SF",
            }
        ],
    )
    _write_reference(
        reference,
        [
            {
                "player_name": "High Value Missing",
                "team": "SF",
                "private_lve_value": "82",
            }
        ],
    )

    result = recompute_truth_set_projection_rows(source, reference_player_path=reference)
    row = result.rows[0]

    assert row["projection_source_quality_status"] == "review_needed"
    assert "missing_projection" in row["projection_source_quality_flags"]
    assert "high_active_value_missing_projection" in row["projection_source_quality_flags"]
    assert any(
        flag["flag"] == "high_active_value_missing_projection"
        for flag in result.flags
    )


def test_projection_recompute_write_uses_stable_header(tmp_path: Path) -> None:
    source = tmp_path / "projections.csv"
    _write_rows(
        source,
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "nfl_team": "DET",
                "projected_rushing_yards": "80",
                "projected_rushing_tds": "1",
            }
        ],
    )
    result = recompute_truth_set_projection_rows(source)
    output = tmp_path / "projection_recompute_preview.csv"

    write_truth_set_projection_recompute(output, result.rows)

    with output.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == TRUTH_SET_PROJECTION_RECOMPUTE_HEADER


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROJECTION_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _write_reference(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ("player_name", "team", "private_lve_value")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
