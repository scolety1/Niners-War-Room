from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_rookie_calibration_candidate_plan_service import (
    CANDIDATE_HEADER,
    build_rookie_calibration_candidate_plan,
    write_rookie_calibration_candidate_plan_outputs,
)


def test_rookie_calibration_candidate_plan_builds_required_candidates() -> None:
    result = build_rookie_calibration_candidate_plan()
    candidate_ids = {row["candidate_id"] for row in result.candidate_rows}
    candidate_tests = {row["candidate_test"] for row in result.candidate_rows}

    assert len(result.candidate_rows) >= 6
    assert "C01" in candidate_ids
    assert "capital_anchor_rebalance" in candidate_tests
    assert "stricter_low_evidence_confidence_cap" in candidate_tests
    assert "not_implemented_review_only_candidate" in {
        row["implementation_status"] for row in result.candidate_rows
    }


def test_rookie_calibration_candidate_plan_uses_baseline_context() -> None:
    result = build_rookie_calibration_candidate_plan()

    assert "Draft-capital-only Top 20 strict starter rate" in result.doc_text
    assert "Simple hybrid Top 20 strict starter rate" in result.doc_text
    assert "Do not tune live formulas yet" in result.doc_text


def test_rookie_calibration_candidate_plan_writes_outputs(tmp_path: Path) -> None:
    paths = write_rookie_calibration_candidate_plan_outputs(
        output_root=tmp_path / "out",
        doc_path=tmp_path / "doc.md",
    )

    assert _header(paths["candidates"]) == CANDIDATE_HEADER
    assert (
        paths["doc"]
        .read_text(encoding="utf-8")
        .startswith("# Model v4.3.6 Rookie Calibration Candidate Plan")
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
