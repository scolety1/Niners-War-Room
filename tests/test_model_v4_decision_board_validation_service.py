from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_decision_board_validation_service import (
    FOCUS_HEADER,
    build_decision_board_validation,
    write_decision_board_validation,
)


def test_decision_board_validation_keeps_board_review_only() -> None:
    result = build_decision_board_validation()

    assert result.summary["verdict"] == (
        "sprint_1_complete_ready_for_morning_human_review"
    )
    assert result.summary["decision_rows"] == 105
    assert result.summary["roster_rows"] == 24
    assert result.summary["pick_rows"] == 5
    assert result.summary["rookie_candidate_rows"] == 76
    assert result.summary["receipt_coverage_rows"] == 105
    assert result.summary["component_coverage_rows"] == 105
    assert result.summary["safe_allowed_use_rows"] == 105
    assert result.summary["safe_blocked_use_rows"] == 105
    assert result.summary["final_recommendations_created"] is False
    assert result.summary["blocker_warnings"] == 0


def test_decision_board_validation_focus_rows_include_morning_work() -> None:
    result = build_decision_board_validation()
    focus_by_entity = {
        (row["decision_area"], row["entity_label"], row["related_pick_label"]): row
        for row in result.focus_rows
    }

    assert (
        "pick_trade_defer_context",
        "2026 1.03",
        "2026 1.03",
    ) in focus_by_entity
    assert ("roster_pressure_trade_context", "Kaleb Johnson", "") in focus_by_entity
    assert (
        "rookie_pick_window_context",
        "Jeremiyah Love",
        "2026 1.03",
    ) in focus_by_entity
    assert {
        row["blocked_use"] for row in result.focus_rows
    } == {"do_not_use_as_final_cut_keep_trade_or_draft_recommendation"}


def test_decision_board_validation_writes_outputs(tmp_path: Path) -> None:
    result = build_decision_board_validation()
    paths = write_decision_board_validation(
        output_root=tmp_path / "validation",
        doc_path=tmp_path / "SPRINT_1_DECISION_BOARD_VALIDATION.md",
        result=result,
    )

    assert _header(paths.focus_rows) == FOCUS_HEADER
    assert paths.summary.exists()
    assert paths.area_rows.exists()
    assert paths.warnings.exists()
    doc_text = paths.doc.read_text(encoding="utf-8")
    assert "does not create final cut" in doc_text
    assert result.summary["verdict"] in doc_text


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
