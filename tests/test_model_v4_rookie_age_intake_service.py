from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rookie_age_intake_service import (
    ROOKIE_AGE_HEADER,
    build_rookie_age_rows,
    write_rookie_age_outputs,
)


def test_rookie_age_intake_parses_user_source_without_using_rank_as_value() -> None:
    result = build_rookie_age_rows()
    by_name = {row["player"]: row for row in result.rows}

    assert len(result.rows) == 240
    assert not result.warning_rows
    assert by_name["Jeremiyah Love"]["age_total_months"] == 255
    assert by_name["Jeremiyah Love"]["age_years_decimal"] == 21.25
    assert by_name["Puka Nacua"]["age_total_months"] == 303
    assert by_name["A.J. Brown"]["nfl_team"] == "PHI"
    assert by_name["Carnell Tate"]["position"] == "WR"
    assert by_name["Omar Cooper Jr."]["normalized_player_name"] == "omarcooper"
    assert {row["allowed_use"] for row in result.rows} == {
        "prospect_lifecycle_age_evidence_not_ranking_input"
    }


def test_rookie_age_intake_writes_csv_and_doc(tmp_path: Path) -> None:
    output, doc = write_rookie_age_outputs(
        output_path=tmp_path / "rookie_age_2026.csv",
        doc_path=tmp_path / "ROOKIE_AGE_INTAKE.md",
    )

    with output.open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == ROOKIE_AGE_HEADER
    assert "source ranking/order" in doc.read_text(encoding="utf-8")
