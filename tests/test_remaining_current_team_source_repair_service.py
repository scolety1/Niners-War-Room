from __future__ import annotations

from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.remaining_current_team_source_repair_service import (
    DEFAULT_REMAINING_TEAM_REPAIR_CSV,
    DEFAULT_REMAINING_TEAM_REPAIR_REPORT,
    NAMED_REMAINING_TEAM_PLAYERS,
    build_remaining_current_team_source_repair,
    write_remaining_current_team_source_repair,
)

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)


pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists() or not DEFAULT_FULL_PLAYER_BOARD_ROWS.exists(),
    reason="local active pack and full-board rows are required",
)


def test_remaining_current_team_source_repair_report_exists_in_result() -> None:
    result = build_remaining_current_team_source_repair()

    assert "Remaining Current Team Source Repair" in result.report_text
    assert "fact_rosters.csv" in result.report_text
    assert "Historical/component team hits were treated as context-only" in result.report_text


def test_all_named_remaining_rows_appear_in_repair_csv_result() -> None:
    result = build_remaining_current_team_source_repair()
    players = {str(row["player"]) for row in result.rows}

    assert players == set(NAMED_REMAINING_TEAM_PLAYERS)


def test_unresolved_non_kickers_remain_quarantined_with_data_needed() -> None:
    result = build_remaining_current_team_source_repair()
    rows = {str(row["player"]): row for row in result.rows}

    for player in (
        "Stefon Diggs",
        "Joe Mixon",
        "Keenan Allen",
        "Kareem Hunt",
        "Gabe Davis",
        "Zach Ertz",
        "Najee Harris",
        "Nick Chubb",
        "Darren Waller",
    ):
        row = rows[player]
        assert row["repair_status"] == "current_status_verified_no_team"
        assert row["should_remain_quarantined"] == "1"
        assert row["selected_current_team"] == ""
        assert row["rotowire_matched"] == "yes"
        assert row["rotowire_status"] == "free_agent_or_no_team"
        assert (
            row["human_readable_data_needed"]
            == "Local RotoWire source verifies no current NFL team; do not invent a team."
        )


def test_resolved_rows_have_source_path_and_column_receipts() -> None:
    result = build_remaining_current_team_source_repair()
    resolved = [
        row
        for row in result.rows
        if row["repair_status"] == "resolved_current_team_verified"
    ]

    assert resolved
    assert all(row["selected_current_team"] for row in resolved)
    assert all(row["selected_source_path"] for row in resolved)
    assert all(row["selected_source_column"] for row in resolved)


def test_rotowire_resolves_named_current_team_rows() -> None:
    result = build_remaining_current_team_source_repair()
    rows = {str(row["player"]): row for row in result.rows}

    expected = {
        "Jauan Jennings": "MIN",
        "David Njoku": "LAC",
        "Aaron Rodgers": "PIT",
    }
    for player, team in expected.items():
        row = rows[player]
        assert row["repair_status"] == "resolved_current_team_verified"
        assert row["selected_current_team"] == team
        assert row["rotowire_matched"] == "yes"
        assert "RotoWire" in str(row["selected_source_path"]) or "rotowire" in str(
            row["selected_source_path"]
        ).lower()


def test_matt_prater_is_formally_hidden_as_default_off_kicker() -> None:
    result = build_remaining_current_team_source_repair()
    prater = next(row for row in result.rows if row["player"] == "Matt Prater")

    assert prater["position"] == "K"
    assert prater["repair_status"] == "intentionally_hidden_kicker"
    assert prater["should_remain_quarantined"] == "1"
    assert "Kicker hidden by default" in str(prater["human_readable_data_needed"])


def test_keenen_and_darius_legacy_scores_remain_comparison_only() -> None:
    result = build_remaining_current_team_source_repair()
    rows = {str(row["player"]): row for row in result.rows}

    assert rows["Keenan Allen"]["nwr_score"] != "82.4"
    assert rows["Darius Slayton"]["nwr_score"] != "78.88"
    assert rows["Keenan Allen"]["repair_status"] == "current_status_verified_no_team"
    assert rows["Darius Slayton"]["repair_status"] == "resolved_current_team_verified"


def test_write_remaining_current_team_source_repair_creates_csv_and_report(
    tmp_path: Path,
) -> None:
    paths = write_remaining_current_team_source_repair(
        repair_csv=tmp_path / DEFAULT_REMAINING_TEAM_REPAIR_CSV.name,
        report_path=tmp_path / DEFAULT_REMAINING_TEAM_REPAIR_REPORT.name,
    )

    assert paths.repair_csv.exists()
    assert paths.report.exists()
    assert "repair_status" in paths.repair_csv.read_text(encoding="utf-8")
    assert "Remaining Current Team Source Repair" in paths.report.read_text(
        encoding="utf-8"
    )
