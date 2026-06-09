from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_draft_capital_snapshot_service import (
    COLLECTED_AT_UTC,
    build_2026_draft_capital_rows,
    write_2026_draft_capital_snapshot,
)


def test_2026_draft_capital_snapshot_normalizes_pick_order() -> None:
    rows = build_2026_draft_capital_rows()
    by_player = {row["player"]: row for row in rows}

    assert len(rows) == 257
    assert by_player["Fernando Mendoza"]["round"] == "1"
    assert by_player["Fernando Mendoza"]["overall_pick"] == "1"
    assert by_player["Jeremiyah Love"]["overall_pick"] == "3"
    assert by_player["Carnell Tate"]["overall_pick"] == "4"
    assert by_player["Kenyon Sadiq"]["overall_pick"] == "16"
    assert by_player["Jadarian Price"]["overall_pick"] == "32"
    assert {row["collected_at_utc"] for row in rows} == {COLLECTED_AT_UTC}
    assert {row["allowed_use"] for row in rows} == {
        "prospect_prior_draft_capital_after_identity_validation"
    }


def test_2026_draft_capital_snapshot_writes_csv_manifest_and_doc(tmp_path: Path) -> None:
    output, manifest, doc = write_2026_draft_capital_snapshot(
        output_path=tmp_path / "draft_capital.csv",
        manifest_path=tmp_path / "manifest.csv",
        doc_path=tmp_path / "DRAFT.md",
    )

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with manifest.open(newline="", encoding="utf-8") as handle:
        manifest_rows = list(csv.DictReader(handle))

    assert len(rows) == 257
    assert manifest_rows[0]["rows"] == "257"
    assert "factual prospect-prior draft-capital evidence" in doc.read_text(
        encoding="utf-8"
    )
