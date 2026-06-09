from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_current_value_checkpoint_service import (
    COMPONENT_HEADER,
    RECEIPT_HEADER,
    VALUE_REVIEW_HEADER,
    WARNING_HEADER,
    build_current_value_checkpoint,
    write_current_value_checkpoint_outputs,
)


def test_phase_11g_builds_review_only_current_value_checkpoint() -> None:
    result = build_current_value_checkpoint()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["market_rows_used"] == 0
    assert result.summary["projection_rows_used"] == 0
    assert result.summary["adp_rows_used"] == 0
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert len(result.review_rows) == 80
    assert {row["position"] for row in result.review_rows} == {"QB", "RB", "WR", "TE"}


def test_phase_11g_keeps_position_lifecycle_and_confidence_visible() -> None:
    result = build_current_value_checkpoint()
    puka = next(row for row in result.review_rows if row["player_name"] == "Puka Nacua")

    assert puka["position_module"] == "rb_wr_current_value"
    assert puka["position_specific_review_score"] != ""
    assert puka["lifecycle_modifier_review"] != ""
    assert puka["role_archetype"] == "wr_target_earner"
    assert puka["confidence_cap"] != ""
    expected = round(
        float(puka["position_specific_review_score"])
        * float(puka["lifecycle_modifier_review"])
        * float(puka["confidence_cap"]),
        4,
    )
    assert float(puka["checkpoint_review_score"]) == expected


def test_phase_11g_qb_te_discipline_holds() -> None:
    result = build_current_value_checkpoint()
    by_name = {row["player_name"]: row for row in result.review_rows}

    assert by_name["Josh Allen"]["discipline_status"] == "one_qb_real_vorp_gap"
    assert by_name["Lamar Jackson"]["discipline_status"] == "one_qb_small_vorp_gap_cap"
    assert by_name["Brock Purdy"]["discipline_status"] == "one_qb_pocket_mid_qb_cap"
    assert by_name["Brock Bowers"]["discipline_status"] == "no_premium_te_real_vorp_gap"
    assert by_name["George Kittle"]["discipline_status"] == "no_premium_te_small_gap_cap"
    assert float(by_name["Brock Purdy"]["checkpoint_review_score"]) < float(
        by_name["Josh Allen"]["checkpoint_review_score"]
    )


def test_phase_11g_rb_wr_balance_and_named_players_are_present() -> None:
    result = build_current_value_checkpoint()
    by_name = {row["player_name"]: row for row in result.review_rows}

    for name in (
        "Christian McCaffrey",
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "Ja'Marr Chase",
    ):
        assert name in by_name
        assert by_name[name]["position"] in {"RB", "WR"}
        assert by_name[name]["role_archetype"]
    assert float(by_name["Puka Nacua"]["checkpoint_review_score"]) > float(
        by_name["Brock Bowers"]["checkpoint_review_score"]
    )


def test_phase_11g_niners_roster_sanity_warnings_are_present() -> None:
    result = build_current_value_checkpoint()
    niners = {row["player_name"] for row in result.review_rows if row["nfl_team"] == "SF"}
    warning_codes = {row["warning_code"] for row in result.warning_rows}

    assert {"Christian McCaffrey", "Brock Purdy", "George Kittle"} <= niners
    assert "niners_roster_checkpoint" in warning_codes
    assert "confidence_caps_visible_sanity" in warning_codes


def test_phase_11g_outputs_do_not_consume_market_projection_or_adp() -> None:
    result = build_current_value_checkpoint()
    blocked_tokens = ("adp", "projection", "projected", "mock", "big_board", "market")

    for rows in (result.review_rows, result.component_rows, result.receipt_rows):
        for row in rows:
            haystack = " ".join(str(value).lower() for value in row.values())
            assert not any(token in haystack for token in blocked_tokens), row


def test_phase_11g_writes_doc_and_csvs(tmp_path: Path) -> None:
    paths = write_current_value_checkpoint_outputs(
        output_root=tmp_path / "current_value",
        doc_path=tmp_path / "PHASE_11G_CURRENT_VALUE_CHECKPOINT.md",
    )

    assert _header(paths.review_rows) == VALUE_REVIEW_HEADER
    assert _header(paths.component_rows) == COMPONENT_HEADER
    assert _header(paths.receipts) == RECEIPT_HEADER
    assert _header(paths.warnings) == WARNING_HEADER
    doc = paths.doc.read_text(encoding="utf-8")
    assert "Phase 11G combines" in doc
    assert "not a final dynasty" in doc


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
