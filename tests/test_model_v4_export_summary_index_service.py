from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_export_summary_index_service import (
    INDEX_HEADER,
    build_export_summary_index,
    write_export_summary_index_outputs,
)


def test_export_summary_index_lists_existing_review_outputs() -> None:
    result = build_export_summary_index()

    assert result.rows
    assert all(Path(row["path"]).exists() for row in result.rows)
    assert all(int(row["row_count"]) > 0 for row in result.rows)
    assert all(str(row["review_only_status"]).startswith("review_only") for row in result.rows)


def test_export_summary_index_includes_required_surfaces() -> None:
    result = build_export_summary_index()
    names = {row["export_name"] for row in result.rows}

    assert {
        "Evidence Risk Player Summary",
        "Evidence Risk Raw Player Rows",
        "Model Edge Queue",
        "Warning Code Dictionary",
        "Pick Decision Lab",
        "Cut Cost",
        "Player Rank Explainer",
        "Startup Slot Board",
        "Rookie Draft Board",
    } <= names


def test_export_summary_index_keeps_raw_and_summary_exports() -> None:
    result = build_export_summary_index()
    export_types = {row["raw_or_summary"] for row in result.rows}

    assert {"raw", "summary"} <= export_types
    assert all(str(row["key_columns"]) for row in result.rows)
    assert all(str(row["review_first_when"]) for row in result.rows)


def test_export_summary_index_writes_outputs(tmp_path: Path) -> None:
    paths = write_export_summary_index_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["index"]) == INDEX_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith(
        "# Model v4.7 Raw Export Summary Index"
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
