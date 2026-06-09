from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_workout_snapshot_service import (
    MAY25_COLLECTED_AT_UTC,
    build_may25_workout_snapshot,
    write_may25_workout_snapshot,
)


def test_may25_workout_snapshot_normalizes_latest_rotowire_exports() -> None:
    rows = build_may25_workout_snapshot()
    by_player = {row["player"]: row for row in rows}

    assert len(rows) == 2097
    assert by_player["Jeremiyah Love"]["position"] == "RB"
    assert by_player["Jeremiyah Love"]["draft_year"] == "2026"
    assert by_player["Carnell Tate"]["position"] == "WR"
    assert by_player["Fernando Mendoza"]["position"] == "QB"
    assert by_player["Kenyon Sadiq"]["position"] == "TE"
    assert {row["collected_at_utc"] for row in rows} == {MAY25_COLLECTED_AT_UTC}
    assert all("local_exports" in row["source_file"] for row in rows)


def test_may25_workout_snapshot_writes_csv_manifest_and_doc(tmp_path: Path) -> None:
    output, manifest, doc = write_may25_workout_snapshot(
        output_path=tmp_path / "workouts.csv",
        manifest_path=tmp_path / "manifest.csv",
        doc_path=tmp_path / "WORKOUTS.md",
        raw_dir=tmp_path / "raw",
    )

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with manifest.open(newline="", encoding="utf-8") as handle:
        manifest_rows = list(csv.DictReader(handle))

    assert rows[0]["collected_at_utc"] == MAY25_COLLECTED_AT_UTC
    assert len(manifest_rows) == 4
    assert "prospect-prior athletic context" in doc.read_text(encoding="utf-8")
