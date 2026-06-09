from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from src.services.model_v4_sprint14f_june15_decision_board_service import (
    DECISION_BOARD_HEADER,
    build_june15_decision_board_outputs,
    write_june15_decision_board_outputs,
)


def test_14f_builds_review_only_june15_decision_board() -> None:
    result = build_june15_decision_board_outputs()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["decision_rows"] == 105
    assert result.summary["roster_decision_rows"] == 24
    assert result.summary["pick_decision_rows"] == 5
    assert result.summary["rookie_candidate_rows"] == 76
    assert result.summary["final_recommendations_created"] is False
    assert result.summary["war_board_changed"] is False
    assert result.summary["my_team_changed"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False


def test_14f_preserves_roster_pressure_without_final_cut_call() -> None:
    result = build_june15_decision_board_outputs()
    by_entity = {
        row["entity_label"]: row
        for row in result.decision_rows
        if row["decision_area"] == "roster_pressure_trade_context"
    }

    assert by_entity["Kaleb Johnson"]["primary_review_band"] == (
        "roster_pressure_line_review"
    )
    assert by_entity["De'Von Achane"]["primary_review_band"] == "core_hold_context_review"
    assert {row["blocked_use"] for row in by_entity.values()} == {
        "do_not_use_as_final_cut_keep_trade_or_draft_recommendation"
    }


def test_14f_preserves_pick_defer_and_missing_baseline_context() -> None:
    result = build_june15_decision_board_outputs()
    by_pick = {
        row["entity_label"]: row
        for row in result.decision_rows
        if row["decision_area"] == "pick_trade_defer_context"
    }

    assert by_pick["2026 1.03"]["primary_review_band"] == (
        "future_first_defer_premium_context_review"
    )
    assert by_pick["2026 5.04"]["primary_review_band"] == "pick_baseline_missing_review"
    assert by_pick["2026 5.04"]["source_review_score"] == ""
    assert "manual_only_no_exact_model_baseline" in by_pick["2026 5.04"]["review_context"]
    assert "Manual-only: no exact model baseline exists" in by_pick["2026 5.04"]["next_review_step"]
    assert "pick_value_baseline_missing" in by_pick["2026 5.04"]["warning_flags"]
    assert "manual_only_no_exact_model_baseline" in by_pick["2026 5.04"]["warning_flags"]


def test_14f_rookie_candidate_rows_remain_context_only() -> None:
    result = build_june15_decision_board_outputs()
    rookie_rows = [
        row for row in result.decision_rows if row["decision_area"] == "rookie_pick_window_context"
    ]

    assert len(rookie_rows) == 76
    assert not any(row["entity_label"] == "Daniel Sobkowicz" for row in rookie_rows)
    assert {row["allowed_use"] for row in rookie_rows} == {
        "review_only_june15_decision_context_not_final_action"
    }
    assert {row["blocked_use"] for row in rookie_rows} == {
        "do_not_use_as_final_cut_keep_trade_or_draft_recommendation"
    }


def test_14f_writes_outputs_docs_and_packet(tmp_path: Path) -> None:
    result = build_june15_decision_board_outputs()
    paths = write_june15_decision_board_outputs(
        output_root=tmp_path / "june15",
        packet_root=tmp_path / "packets",
        result=result,
    )

    assert _header(paths.decision_rows) == DECISION_BOARD_HEADER
    assert len(result.component_rows) == result.summary["decision_rows"] * 3
    assert len(result.receipt_rows) == result.summary["decision_rows"]
    warning_codes = {row["warning_code"] for row in result.warning_rows}
    assert "no_final_decisions_or_mutations_created" in warning_codes
    assert "roster_pressure_line_review" in warning_codes
    assert "does not create final cut" in paths.doc.read_text(encoding="utf-8")
    assert paths.audit_packet.exists()
    with zipfile.ZipFile(paths.audit_packet) as archive:
        assert "docs/model_v4/SPRINT_14F_EXTERNAL_AUDIT_PROMPT.md" in archive.namelist()


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
