from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from src.services.model_v4_sprint14e_rookie_draft_review_service import (
    PICK_CANDIDATE_HEADER,
    ROOKIE_BOARD_HEADER,
    build_rookie_draft_review_outputs,
    write_rookie_draft_review_outputs,
)


def test_14e_builds_review_only_rookie_draft_surfaces() -> None:
    result = build_rookie_draft_review_outputs()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["rookie_board_rows"] > 150
    assert result.summary["pick_candidate_rows"] == 76
    assert result.summary["final_rookie_pick_recommendations_created"] is False
    assert result.summary["war_board_changed"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False


def test_14e_rookie_board_applies_1qb_no_premium_context() -> None:
    result = build_rookie_draft_review_outputs()
    by_name = {row["prospect_name"]: row for row in result.rookie_board_rows}

    assert by_name["Daniel Sobkowicz"]["board_rank"] > 50
    assert by_name["Daniel Sobkowicz"]["evidence_status"] == "watchlist_data_incomplete"
    assert (
        by_name["Daniel Sobkowicz"]["draft_board_band"]
        == "watchlist_or_data_incomplete_context_review"
    )
    assert by_name["Jeremiyah Love"]["board_rank"] < by_name["Daniel Sobkowicz"]["board_rank"]
    assert by_name["Mike Washington"]["evidence_status"] == "manual_scout_source_review"
    assert by_name["Ty Thompson"]["evidence_status"] == "watchlist_data_incomplete"
    assert by_name["Jalon Daniels"]["format_adjustment_factor"] == 0.62
    assert by_name["Ty Thompson"]["format_adjustment_factor"] == 0.82
    assert by_name["Jeremiyah Love"]["format_adjustment_factor"] == 1.0
    assert by_name["Jalon Daniels"]["league_format_adjusted_score"] < (
        by_name["Jalon Daniels"]["prospect_private_value_review_score"]
    )
    assert {row["blocked_use"] for row in result.rookie_board_rows} == {
        "do_not_use_as_final_rookie_draft_recommendation"
    }


def test_14e_pick_candidate_windows_are_context_not_final_picks() -> None:
    result = build_rookie_draft_review_outputs()
    by_pick: dict[str, list[dict[str, object]]] = {}
    for row in result.pick_candidate_rows:
        by_pick.setdefault(str(row["pick_label"]), []).append(row)

    assert len(by_pick["2026 1.03"]) == 8
    assert len(by_pick["2026 1.04"]) == 10
    assert len(by_pick["2026 2.04"]) == 21
    assert len(by_pick["2026 2.08"]) == 25
    assert len(by_pick["2026 5.04"]) == 12
    assert all(
        "watchlist_or_data_incomplete_context_review" not in row["warning_flags"]
        for row in result.pick_candidate_rows
        if row["pick_label"] != "2026 5.04"
    )
    assert {row["allowed_use"] for row in result.pick_candidate_rows} == {
        "review_only_rookie_pick_candidate_context_not_final_selection"
    }
    assert {row["blocked_use"] for row in result.pick_candidate_rows} == {
        "do_not_use_as_final_rookie_draft_recommendation"
    }


def test_14e_formula_balance_labels_separate_edge_from_source_warning() -> None:
    result = build_rookie_draft_review_outputs()
    by_name = {row["prospect_name"]: row for row in result.rookie_board_rows}

    assert "draft_capital_anchor_warning" in by_name["Carnell Tate"]["warning_flags"]
    assert "model_edge_weirdness" in by_name["Skyler Bell"]["warning_flags"]
    assert "no_premium_te_cap_warning" in by_name["Eli Stowers"]["warning_flags"]
    assert "no_premium_te_cap_warning" in by_name["Max Klare"]["warning_flags"]
    assert by_name["Daniel Sobkowicz"]["evidence_status"] == "watchlist_data_incomplete"


def test_14e_missing_pick_baseline_stays_warning_not_fake_value() -> None:
    result = build_rookie_draft_review_outputs()
    late_rows = [
        row for row in result.pick_candidate_rows if row["pick_label"] == "2026 5.04"
    ]

    assert late_rows
    assert {row["pick_value_review_score"] for row in late_rows} == {""}
    assert {row["pick_value_gap_review"] for row in late_rows} == {""}
    assert {row["candidate_window_band"] for row in late_rows} == {
        "late_watchlist_no_pick_baseline_review"
    }
    assert all("pick_value_baseline_missing" in row["warning_flags"] for row in late_rows)


def test_14e_components_warnings_docs_and_packet(tmp_path: Path) -> None:
    result = build_rookie_draft_review_outputs()
    paths = write_rookie_draft_review_outputs(
        output_root=tmp_path / "rookie_draft_review",
        packet_root=tmp_path / "packets",
        result=result,
    )

    assert _header(paths.rookie_board_rows) == ROOKIE_BOARD_HEADER
    assert _header(paths.pick_candidate_rows) == PICK_CANDIDATE_HEADER
    warning_codes = {row["warning_code"] for row in result.warning_rows}
    assert "no_final_rookie_draft_recommendations_created" in warning_codes
    assert "rookie_board_context_not_final_ranking" in warning_codes
    assert "does not create final rookie" in paths.doc.read_text(encoding="utf-8")
    assert paths.audit_packet.exists()
    with zipfile.ZipFile(paths.audit_packet) as archive:
        assert "docs/model_v4/SPRINT_14E_EXTERNAL_AUDIT_PROMPT.md" in archive.namelist()


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
