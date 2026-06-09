from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rookie_shadow_formula_experiment_service import (
    ROW_HEADER,
    SUMMARY_HEADER,
    VARIANTS,
    build_rookie_shadow_formula_experiment,
    write_rookie_shadow_formula_experiment_outputs,
)


def test_shadow_formula_experiment_builds_required_variants() -> None:
    result = build_rookie_shadow_formula_experiment()

    assert result.variant_rows
    assert {row["variant_name"] for row in result.variant_rows} == set(VARIANTS)
    assert {row["promoted_to_active_model"] for row in result.variant_rows} == {False}
    assert "No variant is promoted" in result.doc_text


def test_shadow_formula_experiment_includes_mature_and_shadow_cohorts() -> None:
    result = build_rookie_shadow_formula_experiment()
    cohorts = {row["cohort"] for row in result.summary_rows}

    assert "mature_2021_2023" in cohorts
    assert "partial_2024" in cohorts
    assert "rookie_shadow_2025" in cohorts


def test_shadow_formula_experiment_writes_outputs(tmp_path: Path) -> None:
    paths = write_rookie_shadow_formula_experiment_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["rows"]) == ROW_HEADER
    assert _header(paths["summary"]) == SUMMARY_HEADER
    assert paths["movement"].exists()
    assert paths["doc"].read_text(encoding="utf-8").startswith(
        "# Model v4.3.7 Rookie Shadow Formula Experiment"
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
