from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rookie_replay_baseline_comparison_service import (
    BASELINES,
    COMPARISON_HEADER,
    POSITION_SUMMARY_HEADER,
    SUMMARY_HEADER,
    build_rookie_replay_baseline_comparison,
    write_rookie_replay_baseline_comparison_outputs,
)


def test_rookie_replay_baseline_comparison_builds_all_baselines() -> None:
    result = build_rookie_replay_baseline_comparison()

    assert result.comparison_rows
    assert {row["baseline_name"] for row in result.comparison_rows} == set(BASELINES)
    assert {int(row["draft_year"]) for row in result.comparison_rows} <= {2021, 2022, 2023}
    assert "No formula weights were changed" in result.doc_text


def test_rookie_replay_baseline_summary_compares_current_and_draft_capital() -> None:
    result = build_rookie_replay_baseline_comparison()
    summary_keys = {
        (row["baseline_name"], row["draft_year"], row["window"])
        for row in result.summary_rows
    }

    assert ("current_model_score", "all_mature_years", "Top 20") in summary_keys
    assert ("draft_capital_only", "all_mature_years", "Top 20") in summary_keys
    assert "draft capital" in result.doc_text.lower()


def test_rookie_replay_baseline_outputs_write_expected_files(tmp_path: Path) -> None:
    paths = write_rookie_replay_baseline_comparison_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["comparison"]) == COMPARISON_HEADER
    assert _header(paths["summary"]) == SUMMARY_HEADER
    assert _header(paths["by_position"]) == POSITION_SUMMARY_HEADER
    assert paths["doc"].read_text(encoding="utf-8").startswith(
        "# Model v4.3.6 Rookie Replay Baseline Comparison"
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
