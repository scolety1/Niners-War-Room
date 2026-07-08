from __future__ import annotations

from app.components.development_lab import render_display_only_ngs_context_panel
from src.services.data_health_dashboard_service import build_data_health_dashboard
from src.services.display_only_ngs_context_service import (
    NGS_GATE,
    REVIEW_ONLY_WARNING,
    blocked_ngs_metric_rows,
    data_health_ngs_rows,
    development_lab_ngs_rows,
    ngs_gate_validation_rows,
    player_compare_ngs_rows,
)


def test_development_lab_ngs_rows_are_review_only_and_position_scoped() -> None:
    rows = development_lab_ngs_rows()
    positions = {row["Position"] for row in rows}
    metrics = {row["Metric"] for row in rows}

    assert rows
    assert {"QB", "RB", "WR/TE"} <= positions
    assert "CPOE" in metrics
    assert "RYOE per attempt" in metrics
    assert "Avg separation" in metrics
    assert {row["Gate"] for row in rows} == {NGS_GATE}
    assert all("recommendation" not in row["Metric"].lower() for row in rows)


def test_blocked_metric_rows_stay_out_of_runtime_display() -> None:
    blocked = blocked_ngs_metric_rows()
    display_text = "\n".join(str(row) for row in development_lab_ngs_rows()).lower()

    assert blocked
    assert all(row["Runtime included"] == "false" for row in blocked)
    for forbidden in ("pfr", "espn", "ftn", "pff", "ffopportunity", "tprr", "yprr", "rz_att"):
        assert forbidden not in display_text


def test_data_health_ngs_rows_expose_gate_and_hide_identity_review_rows() -> None:
    rows = data_health_ngs_rows()
    by_source = {row["Source family"]: row for row in rows}

    assert by_source["ngs_passing"]["Gate"] == NGS_GATE
    assert by_source["ngs_rushing"]["Gate"] == NGS_GATE
    assert by_source["ngs_receiving"]["Gate"] == NGS_GATE
    assert by_source["ngs_passing"]["Identity-review count"] == "6"
    assert by_source["ngs_rushing"]["Identity-review count"] == "2"
    assert by_source["ngs_receiving"]["Identity-review count"] == "8"


def test_data_health_dashboard_includes_review_only_ngs_context(tmp_path) -> None:
    report = build_data_health_dashboard(runtime_root=tmp_path)
    frame = report.ngs_context

    assert not frame.empty
    assert str(frame.loc[frame["check"].eq("NGS display gate")].iloc[0]["value"]) == NGS_GATE
    assert "Not used in rankings" in str(
        frame.loc[frame["check"].eq("NGS display gate")].iloc[0]["detail"]
    )
    assert "ngs_passing safe display coverage" in set(frame["check"])


def test_ngs_gate_validation_blocks_rank_model_and_recommendation_language() -> None:
    rows = ngs_gate_validation_rows()
    text = "\n".join(str(row) for row in rows)

    assert rows
    assert "no hidden sort" in text.lower()
    assert "not model-approved" in text.lower()
    assert "no recommendation" in text.lower()
    assert REVIEW_ONLY_WARNING.startswith("Display-only context")


def test_development_lab_page_wires_ngs_panel_without_rank_promotion_language() -> None:
    assert callable(render_display_only_ngs_context_panel)
    text = "\n".join(str(row) for row in development_lab_ngs_rows()).lower()

    assert "review_only_ngs_context".lower() in text
    assert "source truth" not in text
    assert "hidden sort" not in text


def test_player_compare_ngs_context_can_build_from_tracked_artifacts() -> None:
    rows = player_compare_ngs_rows(
        [
            {"player": "Puka Nacua", "position": "WR", "player_id": "9493"},
            {"player": "Jaxon Smith-Njigba", "position": "WR", "player_id": "9488"},
        ]
    )

    assert rows
    assert {row["Gate"] for row in rows} == {NGS_GATE}
    assert any(row["Metric"] == "Avg separation" for row in rows)
