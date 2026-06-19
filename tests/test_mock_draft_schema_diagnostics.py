from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_schema_diagnostics import diagnose_schema


def test_missing_required_columns_are_listed() -> None:
    report = diagnose_schema("pick_order", ["overall_pick", "round"])

    assert report.readiness == "RED"
    assert "current_owner" in report.missing_columns
    assert "Required columns are missing." in report.errors


def test_market_columns_in_private_value_source_are_red() -> None:
    report = diagnose_schema(
        "nwr_private_values",
        ["asset_id", "player", "position", "nwr_private_value", "market_adp_pick"],
    )

    assert report.readiness == "RED"
    assert "market_adp_pick" in report.forbidden_columns


def test_private_columns_in_market_source_are_red() -> None:
    report = diagnose_schema(
        "market_context",
        ["asset_id", "player", "position", "market_adp_pick", "nwr_private_value"],
    )

    assert report.readiness == "RED"
    assert "nwr_private_value" in report.forbidden_columns


def test_harmless_extra_columns_can_be_warnings() -> None:
    report = diagnose_schema(
        "team_needs",
        ["team_id", "team_name", "position", "need_weight", "tendency_note", "note"],
    )

    assert report.readiness == "YELLOW"
    assert "note" in report.unexpected_columns


def test_diagnostics_do_not_write_files(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())

    report = diagnose_schema("frozen_rookie_input", ["asset_id"])

    assert report.no_draft_output is True
    assert set(tmp_path.iterdir()) == before
