from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from src.services.model_v4_sprint14b_cut_keep_pressure_service import (
    COMPONENT_HEADER,
    PRESSURE_HEADER,
    SUMMARY_HEADER,
    build_cut_keep_pressure_outputs,
    write_cut_keep_pressure_outputs,
)


def test_14b_builds_review_only_pressure_without_cut_recommendations() -> None:
    result = build_cut_keep_pressure_outputs()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["roster_rows"] == 24
    assert result.summary["minimum_roster_pressure_count"] == 1
    assert result.summary["final_recommendations_created"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert {row["allowed_use"] for row in result.pressure_rows} == {
        "review_only_cut_keep_pressure_not_final_decision"
    }
    assert {row["blocked_use"] for row in result.pressure_rows} == {
        "do_not_use_as_cut_keep_recommendation"
    }


def test_14b_identifies_required_pressure_zone_as_review_band() -> None:
    result = build_cut_keep_pressure_outputs()
    pressure_zone = [
        row
        for row in result.pressure_rows
        if row["pressure_band"] == "required_pressure_zone_review"
    ]

    assert len(pressure_zone) == 1
    assert pressure_zone[0]["roster_value_rank"] == 24
    assert "review_only_no_cut_keep_recommendation" in pressure_zone[0]["warning_flags"]
    assert "below_inferred_protect_line" in pressure_zone[0]["risk_factors"]


def test_14b_keeps_core_assets_protected_by_band_not_recommendation() -> None:
    result = build_cut_keep_pressure_outputs()
    by_name = {row["player_name"]: row for row in result.pressure_rows}

    assert by_name["De'Von Achane"]["pressure_band"] == "protected_core_review"
    assert by_name["Lamar Jackson"]["pressure_band"] == "protected_core_review"
    assert "top_half_roster_value" in by_name["De'Von Achane"]["protection_factors"]


def test_14b_components_are_visible_and_receipted() -> None:
    result = build_cut_keep_pressure_outputs()

    assert len(result.component_rows) == len(result.pressure_rows) * 5
    assert len(result.receipt_rows) == len(result.pressure_rows)
    assert {row["source_status"] for row in result.component_rows} == {
        "review_only_sprint_14a_roster_contract"
    }


def test_14b_writes_outputs_docs_and_packet(tmp_path: Path) -> None:
    result = build_cut_keep_pressure_outputs()
    paths = write_cut_keep_pressure_outputs(
        output_root=tmp_path / "pressure",
        packet_root=tmp_path / "packets",
        result=result,
    )

    assert _header(paths.pressure_rows) == PRESSURE_HEADER
    assert _header(paths.component_rows) == COMPONENT_HEADER
    assert _header(paths.summary) == SUMMARY_HEADER
    assert "does not create cut" in paths.doc.read_text(encoding="utf-8")
    assert paths.audit_packet.exists()
    with zipfile.ZipFile(paths.audit_packet) as archive:
        assert "docs/model_v4/SPRINT_14B_EXTERNAL_AUDIT_PROMPT.md" in archive.namelist()


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
