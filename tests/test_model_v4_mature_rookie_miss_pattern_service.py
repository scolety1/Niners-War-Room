from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_mature_rookie_miss_pattern_service import (
    MISS_PATTERN_HEADER,
    MISS_PATTERN_SUMMARY_HEADER,
    build_mature_miss_pattern_report,
    write_mature_miss_pattern_outputs,
)


def test_mature_miss_pattern_report_uses_only_mature_replay_rows() -> None:
    result = build_mature_miss_pattern_report()

    assert result.pattern_rows
    years = {int(row["draft_year"]) for row in result.pattern_rows}
    assert years <= {2021, 2022, 2023}
    assert "2024 and 2025 are excluded" in result.doc_text
    assert "No formula weights were changed" in result.doc_text


def test_mature_miss_pattern_report_emits_expected_pattern_families() -> None:
    result = build_mature_miss_pattern_report()
    groups = {row["pattern_group"] for row in result.pattern_rows}

    assert "high_ranked_misses" in groups
    assert "low_ranked_strict_starter_hits" in groups
    assert "low_evidence_overpromotion" in groups
    assert "day_three_rb_hits_worth_preserving" in groups


def test_mature_miss_pattern_outputs_write_csv_and_doc(tmp_path: Path) -> None:
    paths = write_mature_miss_pattern_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["rows"]) == MISS_PATTERN_HEADER
    assert _header(paths["summary"]) == MISS_PATTERN_SUMMARY_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith(
        "# Model v4.3.6 Mature Replay Miss-Pattern Report"
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
