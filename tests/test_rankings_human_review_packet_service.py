from __future__ import annotations

from pathlib import Path

import pytest

from src.services.full_board_rankings_sanity_gate_service import DEFAULT_SANITY_ISSUE_QUEUE
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.rankings_human_review_packet_service import (
    DEFAULT_COMPONENT_READBACK,
    DEFAULT_FORMULA_TRIAGE_REPORT,
    DEFAULT_MORNING_HANDOFF,
    DEFAULT_MY_TEAM_REVIEW,
    DEFAULT_QB_TRIAGE,
    DEFAULT_READINESS_REPORT,
    DEFAULT_SUSPICIOUS_REVIEW,
    DEFAULT_TE_TRIAGE,
    DEFAULT_TOP_100_REVIEW,
    build_rankings_human_review_packet,
    write_rankings_human_review_packet,
)

pytestmark = pytest.mark.skipif(
    not DEFAULT_FULL_PLAYER_BOARD_ROWS.exists() or not DEFAULT_SANITY_ISSUE_QUEUE.exists(),
    reason="full-board rows and sanity issue queue are required",
)


def test_rankings_human_review_packet_summary_counts_and_guardrails() -> None:
    result = build_rankings_human_review_packet()

    assert result.summary["active_rows"] == 240
    assert result.summary["qb_rb_wr_te_rows"] == 232
    assert result.summary["kicker_rows"] == 8
    assert result.summary["nwr_scored_rows"] == 232
    assert result.summary["source_quarantine_non_kickers"] == 0
    assert result.summary["sentinels_safe"] is True
    assert result.summary["contamination_safe"] is True
    assert result.summary["decision_board_blocked"] is True


def test_readiness_report_contains_required_sections() -> None:
    result = build_rankings_human_review_packet()
    report = result.readiness_report

    for section in (
        "## Executive Summary",
        "## Coverage Counts",
        "## Top 25 Current Full-Board Rankings",
        "## QB 1QB Sanity Summary",
        "## TE No-Premium Sanity Summary",
        "## Blockers Before Formula Work",
        "## Blockers Before Decision Board Work",
        "## Exact Next Recommended Task",
    ):
        assert section in report


def test_formula_triage_is_proposal_only_and_names_candidate_lanes() -> None:
    result = build_rankings_human_review_packet()
    report = result.formula_triage_report

    assert "proposal-only" in report
    assert "does not tune formulas" in report
    assert "QB 1QB spread/compression" in report
    assert "TE no-premium ceiling/cap" in report
    assert "shadow" in report


def test_review_csv_rows_have_no_trade_cut_draft_actions() -> None:
    result = build_rankings_human_review_packet()
    forbidden = ("trade", "cut", "draft", "buy", "sell", "start", "sit", "target", "defer")

    assert result.suspicious_rows
    for row in result.suspicious_rows:
        action = str(row["recommended_next_action"]).lower()
        assert not any(word in action for word in forbidden)


def test_component_readback_includes_named_sentinels_and_components() -> None:
    result = build_rankings_human_review_packet()
    rows = {row["player"]: row for row in result.component_rows}

    assert rows["Keenan Allen"]["lineage_class"] == "review_v4_current_player"
    assert rows["Darius Slayton"]["lineage_class"] == "review_v4_current_player"
    assert rows["Trey McBride"]["component_fields_available"] == "yes"
    assert "confidence_cap" in rows["Trey McBride"]


def test_write_rankings_human_review_packet_creates_all_outputs(tmp_path: Path) -> None:
    paths = write_rankings_human_review_packet(
        top_100_path=tmp_path / DEFAULT_TOP_100_REVIEW.name,
        my_team_path=tmp_path / DEFAULT_MY_TEAM_REVIEW.name,
        qb_triage_path=tmp_path / DEFAULT_QB_TRIAGE.name,
        te_triage_path=tmp_path / DEFAULT_TE_TRIAGE.name,
        suspicious_path=tmp_path / DEFAULT_SUSPICIOUS_REVIEW.name,
        component_readback_path=tmp_path / DEFAULT_COMPONENT_READBACK.name,
        readiness_report_path=tmp_path / DEFAULT_READINESS_REPORT.name,
        formula_triage_report_path=tmp_path / DEFAULT_FORMULA_TRIAGE_REPORT.name,
        morning_handoff_path=tmp_path / DEFAULT_MORNING_HANDOFF.name,
    )

    for path in (
        paths.top_100,
        paths.my_team,
        paths.qb_triage,
        paths.te_triage,
        paths.suspicious,
        paths.component_readback,
        paths.readiness_report,
        paths.formula_triage_report,
        paths.morning_handoff,
    ):
        assert path.exists()
    assert "nwr_rank" in paths.top_100.read_text(encoding="utf-8")
    assert "Decision Board should remain blocked" in paths.morning_handoff.read_text(
        encoding="utf-8"
    )
