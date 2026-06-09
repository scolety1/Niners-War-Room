from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_replacement_vorp_core_service import (
    BASELINE_HEADER,
    COMPONENT_HEADER,
    PLAYER_VORP_HEADER,
    RECEIPT_HEADER,
    REPLACEMENT_DEFAULTS,
    WARNING_HEADER,
    build_replacement_vorp_core,
    write_replacement_vorp_core_outputs,
)


def test_phase_11b_builds_review_only_replacement_vorp_outputs() -> None:
    result = build_replacement_vorp_core()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["market_rows_used"] == 0
    assert result.summary["projection_rows_used"] == 0
    assert result.summary["adp_rows_used"] == 0
    assert result.summary["rank_rows_used"] == 0
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert len(result.baseline_rows) == 4
    assert len(result.player_rows) == 80


def test_phase_11b_replacement_levels_are_explicit_and_visible() -> None:
    result = build_replacement_vorp_core()
    baselines = {row["position"]: row for row in result.baseline_rows}

    assert set(baselines) == {"QB", "RB", "WR", "TE"}
    for position, config in REPLACEMENT_DEFAULTS.items():
        row = baselines[position]
        assert int(row["configured_replacement_rank"]) == config[
            "configured_replacement_rank"
        ]
        assert int(row["required_starter_rank"]) == config["required_starter_rank"]
        assert row["allowed_use"] == "review_only_replacement_vorp_core"
        assert int(row["applied_replacement_rank"]) <= int(
            row["configured_replacement_rank"]
        )
        if int(row["player_pool_count"]) < int(row["configured_replacement_rank"]):
            assert "admitted_pool_smaller" in str(row["replacement_warning"])


def test_phase_11b_first_downs_are_imported_or_missing_not_estimated() -> None:
    result = build_replacement_vorp_core()
    statuses = {str(row["first_down_source_status"]) for row in result.player_rows}

    assert statuses
    assert not any(status.startswith("estimated_from_history") for status in statuses)
    assert any(status == "imported_real_data" for status in statuses)
    assert any("missing_not_estimated" in status for status in statuses)

    components = [
        row
        for row in result.component_rows
        if row["component_name"] == "imported_first_down_points"
    ]
    assert components
    assert all(
        "admitted_first_down_view" == row["allowed_lane"] for row in components
    )
    assert all("canonical_first_down" not in row["allowed_input_file"] for row in components)


def test_phase_11b_return_data_is_direct_scoring_only() -> None:
    result = build_replacement_vorp_core()
    return_components = [
        row for row in result.component_rows if row["component_name"] == "return_scoring_points"
    ]
    return_warnings = [
        row
        for row in result.warning_rows
        if row["warning_code"] == "return_scoring_direct_only_not_talent_signal"
    ]

    assert return_components
    assert all(row["allowed_lane"] == "admitted_return_view" for row in return_components)
    assert all(
        row["allowed_field_or_json_path"] == "return_yards_total|return_td_total"
        for row in return_components
    )
    assert return_warnings


def test_phase_11b_qb_and_te_replacement_discipline_is_visible() -> None:
    result = build_replacement_vorp_core()
    player_rows = list(result.player_rows)
    qbs = [row for row in player_rows if row["position"] == "QB"]
    tes = [row for row in player_rows if row["position"] == "TE"]
    non_qb_top = max(
        float(row["vorp_points"])
        for row in player_rows
        if row["position"] != "QB" and row["vorp_points"] != ""
    )

    assert qbs
    assert tes
    assert all(
        "one_qb" in row["qb_te_discipline_status"]
        for row in qbs
        if row["vorp_points"] != ""
    )
    assert all(
        "te" in row["qb_te_discipline_status"]
        for row in tes
        if row["vorp_points"] != ""
    )
    assert not [
        row
        for row in qbs
        if row["position_rank"]
        and int(row["position_rank"]) > 5
        and float(row["vorp_points"]) > non_qb_top
    ]


def test_phase_11b_sanity_fixtures_are_written_as_warnings() -> None:
    result = build_replacement_vorp_core()
    fixture_codes = {
        row["warning_code"]
        for row in result.warning_rows
        if row["warning_type"] == "sanity_fixture"
    }

    assert {
        "elite_rb_vorp_sanity",
        "elite_wr_vorp_sanity",
        "one_qb_qb_sanity",
        "no_premium_te_sanity",
        "aging_veteran_warning_sanity",
        "niners_roster_sanity",
        "mid_qb_cannot_clear_elite_non_qb_without_edge",
    } <= fixture_codes


def test_phase_11b_no_market_projection_or_adp_inputs_in_outputs() -> None:
    result = build_replacement_vorp_core()
    blocked_tokens = ("adp", "projection", "projected", "mock", "big_board", "market")

    for rows in (
        result.baseline_rows,
        result.player_rows,
        result.component_rows,
        result.receipt_rows,
    ):
        for row in rows:
            haystack = " ".join(str(value).lower() for value in row.values())
            assert not any(token in haystack for token in blocked_tokens), row


def test_phase_11b_outputs_write_doc_and_csvs(tmp_path: Path) -> None:
    paths = write_replacement_vorp_core_outputs(
        output_root=tmp_path / "replacement_vorp",
        doc_path=tmp_path / "PHASE_11B_REPLACEMENT_VORP_CORE.md",
    )

    assert _header(paths.baselines) == BASELINE_HEADER
    assert _header(paths.player_rows) == PLAYER_VORP_HEADER
    assert _header(paths.component_rows) == COMPONENT_HEADER
    assert _header(paths.receipts) == RECEIPT_HEADER
    assert _header(paths.warnings) == WARNING_HEADER
    doc = paths.doc.read_text(encoding="utf-8")
    assert "review-only" in doc
    assert "No market, projection, ADP" in doc


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
