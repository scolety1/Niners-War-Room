from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_first_down_projection_estimator_service import (
    FIRST_DOWN_ESTIMATE_HEADER,
    FIRST_DOWN_RATE_HEADER,
    build_first_down_estimator_preview,
    build_position_first_down_rate_rows,
    write_first_down_estimator_outputs,
)

PROJECTION_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "projected_rushing_attempts",
    "projected_targets",
    "projected_receptions",
    "projected_rushing_first_downs",
    "projected_receiving_first_downs",
    "source_url",
    "notes",
)

HISTORICAL_HEADER = (
    "player_name",
    "position",
    "rushing_attempts",
    "rushing_first_downs",
    "targets",
    "receptions",
    "receiving_first_downs",
)


def test_position_first_down_rates_are_derived_from_historical_rows() -> None:
    rates = build_position_first_down_rate_rows(
        [
            {
                "position": "RB",
                "rushing_attempts": "100",
                "rushing_first_downs": "25",
                "targets": "50",
                "receptions": "40",
                "receiving_first_downs": "20",
            },
            {
                "position": "RB",
                "rushing_attempts": "100",
                "rushing_first_downs": "15",
                "targets": "50",
                "receptions": "30",
                "receiving_first_downs": "10",
            },
        ],
        source="fixture",
    )

    rb_rate = next(row for row in rates if row["position"] == "RB")

    assert rb_rate["rushing_first_downs_per_rush"] == 0.2
    assert rb_rate["receiving_first_downs_per_target"] == 0.3
    assert rb_rate["receiving_first_downs_per_reception"] == 0.4286
    assert rb_rate["rate_source_status"] == "historical_nflverse_player_stats"


def test_projection_first_down_estimates_use_position_specific_history(
    tmp_path: Path,
) -> None:
    projections = tmp_path / "projections.csv"
    historical = tmp_path / "historical.csv"
    _write_rows(
        projections,
        PROJECTION_HEADER,
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "nfl_team": "DET",
                "projected_rushing_attempts": "200",
                "projected_targets": "40",
                "projected_receptions": "30",
            }
        ],
    )
    _write_rows(
        historical,
        HISTORICAL_HEADER,
        [
            {
                "player_name": "Historical RB",
                "position": "RB",
                "rushing_attempts": "100",
                "rushing_first_downs": "25",
                "targets": "50",
                "receptions": "40",
                "receiving_first_downs": "20",
            }
        ],
    )

    result = build_first_down_estimator_preview(projections, historical)
    row = result.estimate_rows[0]

    assert row["first_down_estimate_status"] == "estimated_from_history"
    assert row["rushing_first_down_rate"] == 0.25
    assert row["receiving_first_down_rate_basis"] == "targets"
    assert row["receiving_first_down_rate"] == 0.4
    assert row["preview_rushing_first_downs"] == 50.0
    assert row["preview_receiving_first_downs"] == 16.0
    assert row["preview_first_down_points"] == 26.4
    assert row["model_usage_status"] == "preview_only_not_active_scoring"


def test_projection_first_down_estimates_prefer_player_history_before_position(
    tmp_path: Path,
) -> None:
    projections = tmp_path / "projections.csv"
    historical = tmp_path / "historical.csv"
    _write_rows(
        projections,
        PROJECTION_HEADER,
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "nfl_team": "DET",
                "projected_rushing_attempts": "100",
                "projected_targets": "10",
                "projected_receptions": "8",
            }
        ],
    )
    _write_rows(
        historical,
        HISTORICAL_HEADER,
        [
            {
                "player_name": "Runner One",
                "position": "RB",
                "rushing_attempts": "100",
                "rushing_first_downs": "10",
                "targets": "10",
                "receptions": "8",
                "receiving_first_downs": "5",
            },
            {
                "player_name": "Other RB",
                "position": "RB",
                "rushing_attempts": "100",
                "rushing_first_downs": "50",
                "targets": "90",
                "receptions": "80",
                "receiving_first_downs": "9",
            },
        ],
    )

    row = build_first_down_estimator_preview(projections, historical).estimate_rows[0]

    assert row["first_down_estimate_status"] == "estimated_from_history"
    assert row["rushing_first_down_rate"] == 0.1
    assert row["rushing_first_down_rate_scope"] == "player_recent"
    assert row["receiving_first_down_rate"] == 0.5
    assert row["receiving_first_down_rate_scope"] == "player_recent"
    assert row["preview_rushing_first_downs"] == 10.0
    assert row["preview_receiving_first_downs"] == 5.0
    assert row["preview_first_down_points"] == 6.0


def test_direct_first_down_projection_wins_over_estimate(tmp_path: Path) -> None:
    projections = tmp_path / "projections.csv"
    historical = tmp_path / "historical.csv"
    _write_rows(
        projections,
        PROJECTION_HEADER,
        [
            {
                "player_name": "Direct One",
                "position": "WR",
                "nfl_team": "SF",
                "projected_targets": "100",
                "projected_receiving_first_downs": "45",
            }
        ],
    )
    _write_rows(
        historical,
        HISTORICAL_HEADER,
        [
            {
                "position": "WR",
                "targets": "100",
                "receptions": "70",
                "receiving_first_downs": "10",
            }
        ],
    )

    row = build_first_down_estimator_preview(projections, historical).estimate_rows[0]

    assert row["first_down_estimate_status"] == "direct_first_down_projection"
    assert row["preview_receiving_first_downs"] == 45.0
    assert row["preview_first_down_points"] == 18.0
    assert row["rate_source_status"] == "direct_source_projection"


def test_missing_history_keeps_first_down_projection_missing(tmp_path: Path) -> None:
    projections = tmp_path / "projections.csv"
    historical = tmp_path / "historical.csv"
    _write_rows(
        projections,
        PROJECTION_HEADER,
        [
            {
                "player_name": "No History",
                "position": "RB",
                "nfl_team": "DET",
                "projected_rushing_attempts": "200",
            }
        ],
    )
    _write_rows(historical, HISTORICAL_HEADER, [])

    row = build_first_down_estimator_preview(projections, historical).estimate_rows[0]

    assert row["first_down_estimate_status"] == "missing_first_down_projection"
    assert row["preview_first_down_points"] == 0.0
    assert row["warning_flags"] == "missing_historical_rate"


def test_missing_rushing_rate_stays_blank_without_crashing(tmp_path: Path) -> None:
    projections = tmp_path / "projections.csv"
    historical = tmp_path / "historical.csv"
    _write_rows(
        projections,
        PROJECTION_HEADER,
        [
            {
                "player_name": "Gadget WR",
                "position": "WR",
                "nfl_team": "KC",
                "projected_rushing_attempts": "10",
                "projected_targets": "100",
            }
        ],
    )
    _write_rows(
        historical,
        HISTORICAL_HEADER,
        [
            {
                "player_name": "Historical WR",
                "position": "WR",
                "rushing_attempts": "0",
                "rushing_first_downs": "0",
                "targets": "100",
                "receptions": "70",
                "receiving_first_downs": "40",
            }
        ],
    )

    row = build_first_down_estimator_preview(projections, historical).estimate_rows[0]

    assert row["first_down_estimate_status"] == "estimated_from_history"
    assert row["rushing_first_down_rate"] == ""
    assert row["receiving_first_down_rate"] == 0.4
    assert row["warning_flags"] == "missing_rushing_first_down_rate"


def test_first_down_estimator_writes_stable_headers(tmp_path: Path) -> None:
    projections = tmp_path / "projections.csv"
    historical = tmp_path / "historical.csv"
    _write_rows(projections, PROJECTION_HEADER, [])
    _write_rows(historical, HISTORICAL_HEADER, [])
    result = build_first_down_estimator_preview(projections, historical)
    estimate_path = tmp_path / "estimates.csv"
    rate_path = tmp_path / "rates.csv"
    summary_path = tmp_path / "summary.csv"

    write_first_down_estimator_outputs(
        estimate_path=estimate_path,
        rate_path=rate_path,
        summary_path=summary_path,
        result=result,
    )

    assert _header(estimate_path) == FIRST_DOWN_ESTIMATE_HEADER
    assert _header(rate_path) == FIRST_DOWN_RATE_HEADER


def _write_rows(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
