from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_decision_board_validation_service import (
    FOCUS_HEADER,
    build_decision_board_validation,
    write_decision_board_validation,
)
from src.services.model_v4_sprint14f_june15_decision_board_service import (
    COMPONENT_HEADER,
    DECISION_BOARD_HEADER,
    RECEIPT_HEADER,
)
from src.services.model_v4_sprint14f_june15_decision_board_service import (
    WARNING_HEADER as SOURCE_WARNING_HEADER,
)


def test_decision_board_validation_keeps_board_review_only(tmp_path: Path) -> None:
    board_root = _write_board_fixture(tmp_path)
    result = build_decision_board_validation(board_root=board_root)

    assert result.summary["verdict"] == (
        "sprint_1_complete_ready_for_morning_human_review"
    )
    assert result.summary["decision_rows"] == 3
    assert result.summary["roster_rows"] == 1
    assert result.summary["pick_rows"] == 1
    assert result.summary["rookie_candidate_rows"] == 1
    assert result.summary["receipt_coverage_rows"] == 3
    assert result.summary["component_coverage_rows"] == 3
    assert result.summary["safe_allowed_use_rows"] == 3
    assert result.summary["safe_blocked_use_rows"] == 3
    assert result.summary["roster_pressure_focus_rows"] == 1
    assert result.summary["final_recommendations_created"] is False
    assert result.summary["blocker_warnings"] == 0


def test_decision_board_validation_focus_rows_include_morning_work(tmp_path: Path) -> None:
    board_root = _write_board_fixture(tmp_path)
    result = build_decision_board_validation(board_root=board_root)
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


def test_decision_board_validation_reports_roster_pressure_guardrail(
    tmp_path: Path,
) -> None:
    board_root = _write_board_fixture(tmp_path)
    result = build_decision_board_validation(board_root=board_root)
    warnings_by_code = {row["warning_code"]: row for row in result.warning_rows}

    assert result.summary["roster_pressure_focus_rows"] == 1
    assert (
        warnings_by_code["roster_pressure_focus_review_only_guardrail"]["severity"]
        == "pass"
    )
    assert (
        "roster pressure focus rows retain review-only use"
        in warnings_by_code["roster_pressure_focus_review_only_guardrail"][
            "warning_detail"
        ]
    )


def test_decision_board_validation_blocks_unsafe_roster_pressure_focus(
    tmp_path: Path,
) -> None:
    board_root = _write_board_fixture(
        tmp_path,
        roster_allowed_use="final_action_candidate",
    )
    result = build_decision_board_validation(board_root=board_root)
    warnings_by_code = {row["warning_code"]: row for row in result.warning_rows}

    assert result.summary["verdict"] == "needs_repair_before_human_decision_review"
    assert result.summary["blocker_warnings"] == 2
    assert (
        warnings_by_code["unsafe_allowed_use_detected"]["severity"] == "blocker"
    )
    assert (
        warnings_by_code["roster_pressure_focus_review_only_guardrail"]["severity"]
        == "blocker"
    )


def test_decision_board_validation_writes_outputs(tmp_path: Path) -> None:
    board_root = _write_board_fixture(tmp_path)
    result = build_decision_board_validation(board_root=board_root)
    paths = write_decision_board_validation(
        output_root=tmp_path / "validation",
        board_root=board_root,
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
    assert "Roster pressure focus rows: 1" in doc_text


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))


def _write_board_fixture(
    tmp_path: Path,
    *,
    roster_allowed_use: str = "review_only_june15_decision_context_not_final_action",
) -> Path:
    board_root = tmp_path / "board"
    board_root.mkdir()
    rows = (
        _decision_row(
            decision_key="pick:2026_1_03",
            decision_area="pick_trade_defer_context",
            entity_label="2026 1.03",
            related_pick_label="2026 1.03",
            position="PICK",
            review_priority="95",
            primary_review_band="owned_pick_defer_context_review",
            source_review_score="93",
            secondary_review_score="5",
            next_review_step="Review keep/use/defer paths.",
        ),
        _decision_row(
            decision_key="roster:kaleb_johnson",
            decision_area="roster_pressure_trade_context",
            entity_label="Kaleb Johnson",
            related_pick_label="",
            position="RB",
            review_priority="88",
            primary_review_band="roster_pressure_line_review",
            source_review_score="40",
            secondary_review_score="12",
            next_review_step="Review roster pressure and trade market.",
            allowed_use=roster_allowed_use,
        ),
        _decision_row(
            decision_key="rookie:2026_1_03:jeremiyah_love",
            decision_area="rookie_pick_window_context",
            entity_label="Jeremiyah Love",
            related_pick_label="2026 1.03",
            position="RB",
            review_priority="84",
            primary_review_band="rookie_candidate_gap_context_review",
            source_review_score="86",
            secondary_review_score="-4",
            next_review_step="Review rookie candidate profile.",
        ),
    )
    _write_csv(
        board_root / "june15_decision_board_review_rows.csv",
        DECISION_BOARD_HEADER,
        rows,
    )
    _write_csv(
        board_root / "june15_decision_board_component_rows.csv",
        COMPONENT_HEADER,
        (
            _component_row("pick:2026_1_03"),
            _component_row("roster:kaleb_johnson"),
            _component_row("rookie:2026_1_03:jeremiyah_love"),
        ),
    )
    _write_csv(
        board_root / "june15_decision_board_receipts.csv",
        RECEIPT_HEADER,
        (
            _receipt_row("pick:2026_1_03", "pick receipt"),
            _receipt_row("roster:kaleb_johnson", "roster pressure receipt"),
            _receipt_row("rookie:2026_1_03:jeremiyah_love", "rookie receipt"),
        ),
    )
    _write_csv(
        board_root / "june15_decision_board_warnings.csv",
        SOURCE_WARNING_HEADER,
        (),
    )
    return board_root


def _decision_row(
    *,
    decision_key: str,
    decision_area: str,
    entity_label: str,
    related_pick_label: str,
    position: str,
    review_priority: str,
    primary_review_band: str,
    source_review_score: str,
    secondary_review_score: str,
    next_review_step: str,
    allowed_use: str = "review_only_june15_decision_context_not_final_action",
) -> dict[str, object]:
    return {
        "decision_key": decision_key,
        "decision_area": decision_area,
        "entity_label": entity_label,
        "related_pick_label": related_pick_label,
        "position": position,
        "review_priority": review_priority,
        "primary_review_band": primary_review_band,
        "source_review_score": source_review_score,
        "secondary_review_score": secondary_review_score,
        "review_context": "fixture review-only context",
        "next_review_step": next_review_step,
        "allowed_use": allowed_use,
        "blocked_use": "do_not_use_as_final_cut_keep_trade_or_draft_recommendation",
        "warning_flags": "",
        "formula_version": "fixture",
    }


def _component_row(decision_key: str) -> dict[str, object]:
    return {
        "decision_key": decision_key,
        "entity_label": decision_key,
        "component_layer": "fixture",
        "component_name": "fixture_component",
        "component_value": "1",
        "source_status": "fixture_source",
        "receipt_pointer": "fixture_receipt",
        "formula_version": "fixture",
    }


def _receipt_row(decision_key: str, pointer: str) -> dict[str, object]:
    return {
        "decision_key": decision_key,
        "entity_label": decision_key,
        "receipt_layer": "fixture",
        "receipt_pointer": pointer,
        "source_status": "fixture_source",
        "formula_version": "fixture",
    }


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
