from __future__ import annotations

import csv
from pathlib import Path

from src.services.real_draft_pool_preview_service import (
    build_free_agent_rows,
    build_rookie_draftable_rows,
    draft_pool_readiness_rows,
)


def test_rookie_draftables_use_public_draft_picks_and_exclude_protected() -> None:
    rows = build_rookie_draftable_rows(
        draft_pick_rows=[
            {
                "season": "2026",
                "round": "1",
                "pick": "3",
                "team": "ARI",
                "gsis_id": "00-001",
                "pfr_player_id": "LoveJe00",
                "pfr_player_name": "Jeremiyah Love",
                "position": "RB",
                "college": "Notre Dame",
            },
            {
                "season": "2026",
                "round": "1",
                "pick": "8",
                "team": "SEA",
                "gsis_id": "00-002",
                "pfr_player_id": "ProtWr00",
                "pfr_player_name": "Protected Wideout",
                "position": "WR",
                "college": "Test U",
            },
            {
                "season": "2026",
                "round": "1",
                "pick": "9",
                "team": "DAL",
                "gsis_id": "00-003",
                "pfr_player_id": "EdgeRu00",
                "pfr_player_name": "Edge Rusher",
                "position": "DE",
                "college": "Defense U",
            },
        ],
        ffid_rows=[
            {
                "sleeper_id": "9001",
                "gsis_id": "00-001",
                "pfr_id": "LoveJe00",
            },
            {
                "sleeper_id": "9002",
                "gsis_id": "00-002",
                "pfr_id": "ProtWr00",
            },
        ],
        sleeper_rows=[
            {
                "sleeper_id": "9001",
                "player_name": "Jeremiyah Love",
                "position": "RB",
                "nfl_team": "ARI",
            },
            {
                "sleeper_id": "9002",
                "player_name": "Protected Wideout",
                "position": "WR",
                "nfl_team": "SEA",
            },
        ],
        protected_player_ids={"9002"},
        draft_year=2026,
        source_updated_at="2026-05-08T00:00:00Z",
    )

    assert len(rows) == 1
    assert rows[0]["player_name"] == "Jeremiyah Love"
    assert rows[0]["asset_type"] == "rookie"
    assert rows[0]["why_available"] == "rookie_current_year"
    assert rows[0]["sleeper_id"] == "9001"
    assert rows[0]["draft_value"] > 90


def test_free_agent_pool_excludes_rostered_rookies_and_unsupported_positions() -> None:
    rows = build_free_agent_rows(
        sleeper_rows=[
            {
                "sleeper_id": "100",
                "player_name": "Rostered Back",
                "position": "RB",
                "nfl_team": "SEA",
                "status": "Active",
                "active": "True",
                "depth_chart_order": "2",
            },
            {
                "sleeper_id": "101",
                "player_name": "Rookie Receiver",
                "position": "WR",
                "nfl_team": "SEA",
                "status": "Active",
                "active": "True",
                "depth_chart_order": "3",
            },
            {
                "sleeper_id": "102",
                "player_name": "Free Agent Tight End",
                "position": "TE",
                "nfl_team": "DAL",
                "status": "Active",
                "active": "True",
                "depth_chart_order": "2",
            },
            {
                "sleeper_id": "103",
                "player_name": "Kicker Guy",
                "position": "K",
                "nfl_team": "DAL",
                "status": "Active",
                "active": "True",
                "depth_chart_order": "1",
            },
            {
                "sleeper_id": "104",
                "player_name": "Stale Universe Back",
                "position": "RB",
                "nfl_team": "TB",
                "status": "Active",
                "active": "False",
                "depth_chart_order": "",
            },
            {
                "sleeper_id": "105",
                "player_name": "Teamless Quarterback",
                "position": "QB",
                "nfl_team": "",
                "status": "Active",
                "active": "True",
                "depth_chart_order": "2",
            },
        ],
        protected_player_ids={"100"},
        rookie_sleeper_ids={"101"},
        season=2026,
        source_updated_at="2026-05-08T00:00:00Z",
    )

    assert [row["player_name"] for row in rows] == ["Free Agent Tight End"]
    assert rows[0]["asset_type"] == "free_agent"
    assert rows[0]["why_available"] == "sleeper_unrostered_free_agent"
    assert rows[0]["review_status"] == "review_needed"
    assert rows[0]["draft_value"] == 0


def test_draft_pool_readiness_keeps_released_veterans_review_needed() -> None:
    rows = draft_pool_readiness_rows(
        rookie_rows=[{"player_name": "Rookie"}],
        free_agent_rows=[{"player_name": "Free Agent"}],
        released_veteran_count=0,
        manual_count=0,
    )
    by_source = {str(row["source"]): row for row in rows}

    assert by_source["rookies"]["status"] == "loaded"
    assert by_source["free agents"]["status"] == "loaded"
    assert by_source["released veterans"]["status"] == "review_needed"
    assert (
        by_source["released veterans"]["decision_effect"]
        == "blocks_draft_ready_not_roster_declaration"
    )
    assert by_source["manual draftables"]["status"] == "optional_missing"


def test_preview_pool_files_are_compatible_with_draft_service(
    tmp_path: Path,
) -> None:
    pack = tmp_path / "pack"
    pack.mkdir()
    _write(
        pack / "fact_rookie_draftables.csv",
        (
            "season",
            "player_id",
            "player_name",
            "position",
            "nfl_team",
            "asset_type",
            "draft_value",
            "market_value",
            "confidence",
            "why_available",
            "recommendation",
        ),
        [
            {
                "season": "2026",
                "player_id": "9001",
                "player_name": "Jeremiyah Love",
                "position": "RB",
                "nfl_team": "ARI",
                "asset_type": "rookie",
                "draft_value": "94",
                "market_value": "",
                "confidence": "72",
                "why_available": "rookie_current_year",
                "recommendation": "rookie_review",
            }
        ],
    )
    _write(
        pack / "fact_available_veterans.csv",
        (
            "season",
            "player_id",
            "player_name",
            "position",
            "nfl_team",
            "asset_type",
            "availability_status",
            "draft_value",
            "confidence",
            "why_available",
            "recommendation",
        ),
        [
            {
                "season": "2026",
                "player_id": "102",
                "player_name": "Free Agent Tight End",
                "position": "TE",
                "nfl_team": "DAL",
                "asset_type": "free_agent",
                "availability_status": "sleeper_unrostered",
                "draft_value": "0",
                "confidence": "35",
                "why_available": "sleeper_unrostered_free_agent",
                "recommendation": "free_agent_review",
            }
        ],
    )

    assert (pack / "fact_rookie_draftables.csv").exists()
    assert (pack / "fact_available_veterans.csv").exists()


def _write(path: Path, header: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
