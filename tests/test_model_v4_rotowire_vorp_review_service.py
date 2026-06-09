from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rotowire_vorp_review_service import (
    VORP_HEADER,
    build_rotowire_vorp_review,
    write_rotowire_vorp_review_outputs,
)


def test_rotowire_vorp_review_builds_truth_set_rows_after_baseline_generation() -> None:
    result = build_rotowire_vorp_review()
    rows = {row["player_name"]: row for row in result.vorp_rows}

    assert "Bijan Robinson" in rows
    assert rows["Bijan Robinson"]["vorp_status"] == "available"
    assert rows["Bijan Robinson"]["first_down_source_status"] == "estimated_from_history"
    assert "estimated" in str(rows["Bijan Robinson"]["warning"])
    assert float(rows["Bijan Robinson"]["estimated_first_down_points"]) > 0
    assert float(rows["Bijan Robinson"]["first_down_adjusted_points"]) > float(
        rows["Bijan Robinson"]["current_lve_base_points"]
    )
    assert result.summary["projection_rows_used"] == 0
    assert result.summary["market_rows_used"] == 0
    assert result.summary["league_rank_used"] is False


def test_rotowire_vorp_review_keeps_missing_lve_base_as_review() -> None:
    result = build_rotowire_vorp_review()
    rows = {row["player_name"]: row for row in result.vorp_rows}

    assert rows["Jeremiyah Love"]["vorp_status"] == "review"
    assert rows["Jeremiyah Love"]["warning"] == "missing_lve_base_production"


def test_rotowire_vorp_review_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_vorp_review()
    paths = write_rotowire_vorp_review_outputs(tmp_path, result)

    assert paths["vorp"].exists()
    with paths["vorp"].open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == VORP_HEADER
