from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_depth_chart_snapshot_service import (
    MAY22_COLLECTED_AT_UTC,
    MAY22_SOURCE_FILE,
    build_may22_depth_chart_rows,
    write_may22_depth_chart_snapshot,
)


def test_may22_depth_chart_snapshot_updates_timestamp_without_changing_roles() -> None:
    rows = build_may22_depth_chart_rows()
    by_player = {row["player"]: row for row in rows}

    assert len(rows) == 727
    assert by_player["Jeremiyah Love"]["team"] == "Cardinals"
    assert by_player["Jeremiyah Love"]["slot"] == "RB #1"
    assert by_player["Carnell Tate"]["slot"] == "WR #1"
    assert by_player["Kenyon Sadiq"]["slot"] == "TE #1"
    assert by_player["Jadarian Price"]["slot"] == "RB #2"
    assert {row["collected_at_utc"] for row in rows} == {MAY22_COLLECTED_AT_UTC}
    assert {row["source_file"] for row in rows} == {MAY22_SOURCE_FILE}


def test_may22_depth_chart_snapshot_writes_csv_and_doc(tmp_path: Path) -> None:
    output, doc = write_may22_depth_chart_snapshot(
        output_path=tmp_path / "depth.csv",
        doc_path=tmp_path / "DEPTH.md",
    )

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["collected_at_utc"] == MAY22_COLLECTED_AT_UTC
    assert "current role/context source" in doc.read_text(encoding="utf-8")
