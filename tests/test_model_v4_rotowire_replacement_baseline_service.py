from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.model_v4_rotowire_replacement_baseline_service import (
    BASELINE_HEADER,
    build_rotowire_replacement_baselines,
    write_rotowire_replacement_baseline_outputs,
)


def test_rotowire_replacement_baselines_use_locked_lineup_shape() -> None:
    result = build_rotowire_replacement_baselines()
    rows = {row["position"]: row for row in result.baseline_rows}

    assert rows["QB"]["required_starters"] == 10
    assert rows["RB"]["required_starters"] == 20
    assert rows["WR"]["required_starters"] == 30
    assert rows["TE"]["required_starters"] == 10
    assert sum(int(row["flex_selected"]) for row in result.baseline_rows) == 20
    assert result.summary["projection_rows_used"] == 0
    assert result.summary["market_rows_used"] == 0
    assert result.summary["league_rank_used"] is False


def test_rotowire_replacement_baselines_allocate_flex_by_skill_pool_value(
    tmp_path: Path,
) -> None:
    stats_path = tmp_path / "stats.csv"
    _write_rows(stats_path)

    result = build_rotowire_replacement_baselines(player_stats_path=stats_path)
    rows = {row["position"]: row for row in result.baseline_rows}

    assert rows["QB"]["replacement_rank"] == 10
    assert rows["RB"]["replacement_rank"] == 30
    assert rows["WR"]["replacement_rank"] == 40
    assert rows["TE"]["replacement_rank"] == 10
    assert rows["RB"]["flex_selected"] == 10
    assert rows["WR"]["flex_selected"] == 10
    assert rows["TE"]["flex_selected"] == 0


def test_rotowire_replacement_baselines_include_labeled_first_down_estimates() -> None:
    result = build_rotowire_replacement_baselines()
    rows = {row["position"]: row for row in result.baseline_rows}

    assert result.summary["first_down_source_status"] == "estimated_from_history"
    assert rows["RB"]["replacement_first_down_source_status"] == "estimated_from_history"
    assert float(rows["RB"]["replacement_estimated_first_down_points"]) > 0
    assert float(rows["RB"]["replacement_first_down_adjusted_points"]) > float(
        rows["RB"]["replacement_lve_base_points"]
    )


def test_rotowire_replacement_baselines_write_outputs(tmp_path: Path) -> None:
    result = build_rotowire_replacement_baselines()
    paths = write_rotowire_replacement_baseline_outputs(tmp_path, result)

    assert paths["baselines"].exists()
    with paths["baselines"].open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == BASELINE_HEADER


def _write_rows(path: Path) -> None:
    header = (
        "season",
        "source_family",
        "source_detail",
        "player_name",
        "nfl_team",
        "position",
        "metrics_json",
    )
    rows: list[dict[str, str]] = []
    source_specs = (("QB", 12, 300), ("RB", 30, 220), ("WR", 50, 210), ("TE", 15, 120))
    for position, count, base in source_specs:
        for index in range(1, count + 1):
            rows.append(
                {
                    "season": "2025",
                    "source_family": position.lower(),
                    "source_detail": "fantasy",
                    "player_name": f"{position} Player {index}",
                    "nfl_team": "TST",
                    "position": position,
                    "metrics_json": json.dumps({"rushing_yds": base - index}),
                }
            )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
