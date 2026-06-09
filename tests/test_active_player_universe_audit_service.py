from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import src.services.active_player_universe_audit_service as universe_service
from src.services.active_player_universe_audit_service import (
    build_active_player_universe_audit,
)
from src.services.command_board_service import WarBoard
from src.services.draft_service import DraftRoomBoard
from src.services.identity_audit_service import IdentityAuditReport


def test_universe_audit_flags_unrostered_visible_war_board_row(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(universe_service, "validate_data_pack", _validated_fixture)
    monkeypatch.setattr(universe_service, "build_identity_audit", _identity_fixture)
    monkeypatch.setattr(universe_service, "build_war_board", _war_board_with_unrostered)
    monkeypatch.setattr(universe_service, "build_draft_room", _draft_room_fixture)

    report = build_active_player_universe_audit(tmp_path)
    blocker = [
        row
        for row in report.blocker_rows
        if row["player_name"] == "Unrostered Visible"
    ][0]

    assert blocker["warning"] == "unrostered_player_visible_on_war_board"
    assert blocker["ranking_allowed"] is True


def test_universe_audit_separates_draftable_pool_from_rostered_players(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(universe_service, "validate_data_pack", _validated_fixture)
    monkeypatch.setattr(universe_service, "build_identity_audit", _identity_fixture)
    monkeypatch.setattr(universe_service, "build_war_board", _war_board_rostered_only)
    monkeypatch.setattr(universe_service, "build_draft_room", _draft_room_fixture)

    report = build_active_player_universe_audit(tmp_path)

    assert {row["player_name"] for row in report.draft_pool_rows} == {
        "Draftable Rookie",
        "Available Veteran",
    }
    assert all(row["universe"] == "draftable_pool_only" for row in report.draft_pool_rows)
    assert not any(row["warning"] != "No active warning." for row in report.rows)


def _validated_fixture(path: object) -> object:
    class Validated:
        rows_by_table = {
            "players": [
                {
                    "player_id": "rostered_1",
                    "sleeper_id": "rostered_1",
                    "player_name": "Rostered Player",
                    "position": "WR",
                    "nfl_team": "MIN",
                    "active_flag": "1",
                    "pfr_id": "RostPl00",
                },
                {
                    "player_id": "unrostered_1",
                    "sleeper_id": "unrostered_1",
                    "player_name": "Unrostered Visible",
                    "position": "RB",
                    "nfl_team": "FA",
                    "active_flag": "1",
                    "pfr_id": "UnroVi00",
                },
            ],
            "rosters": [
                {
                    "player_id": "rostered_1",
                    "player_name": "Rostered Player",
                    "position": "WR",
                    "nfl_team": "MIN",
                    "team_name": "Niners",
                    "roster_status": "rostered",
                }
            ],
        }

    return Validated()


def _identity_fixture(path: object, *, source_root: object = None) -> IdentityAuditReport:
    rows = [
        _identity_row("rostered_1", "Rostered Player", "WR", "MIN"),
        _identity_row("unrostered_1", "Unrostered Visible", "RB", "FA"),
    ]
    return IdentityAuditReport(
        rows=rows,
        summary_rows=[],
        blocked_rows=[],
        statuses=["ready"],
        match_methods=["sleeper_gsis_exact"],
        issues=[],
        source_root="fixture",
    )


def _war_board_with_unrostered(path: object) -> WarBoard:
    return WarBoard(
        rows=[
            {"player_id": "rostered_1", "player": "Rostered Player"},
            {"player_id": "unrostered_1", "player": "Unrostered Visible"},
        ],
        data_source_audit_rows=[],
        positions=[],
        teams=[],
        actions=[],
        recommendations=[],
        edge_types=[],
        confidence_buckets=[],
        sort_metadata={},
    )


def _war_board_rostered_only(path: object) -> WarBoard:
    return WarBoard(
        rows=[{"player_id": "rostered_1", "player": "Rostered Player"}],
        data_source_audit_rows=[],
        positions=[],
        teams=[],
        actions=[],
        recommendations=[],
        edge_types=[],
        confidence_buckets=[],
        sort_metadata={},
    )


def _draft_room_fixture(path: object, *, team_id: str = "niners") -> DraftRoomBoard:
    _ = team_id
    return DraftRoomBoard(
        snapshot_date="2026-pre-draft",
        pick_rows=[],
        my_pick_rows=[],
        team_rows=[],
        asset_rows=[],
        rookie_rows=[],
        released_veteran_rows=[],
        manual_draftable_rows=[],
        available_pool_source_rows=[],
        combined_rows=[
            {
                "asset_id": "rookie:rookie_1",
                "asset_type": "rookie",
                "player": "Draftable Rookie",
                "position": "RB",
                "team": "CHI",
                "availability": "rookie_pool",
                "why_available": "rookie_current_year",
                "draft_value": 88,
                "confidence": 72,
                "source": "fact_rookie_draftables.csv",
            },
            {
                "asset_id": "released_veteran:vet_1",
                "asset_type": "released_veteran",
                "player": "Available Veteran",
                "position": "WR",
                "team": "FA",
                "availability": "released_veteran",
                "why_available": "released_veteran_declared",
                "draft_value": 70,
                "confidence": 65,
                "source": "fact_available_veterans.csv",
            },
        ],
        best_available_rows=[],
        rookie_veteran_comparison_rows=[],
        release_target_rows=[],
        available_pool_warnings=[],
        teams=[],
        certainties=[],
        asset_types=[],
        positions=[],
        asset_recommendations=[],
        reach_labels=[],
        sort_metadata={},
    )


def _identity_row(
    player_id: str,
    player: str,
    position: str,
    team: str,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "sleeper_id": player_id,
        "player": player,
        "position": position,
        "team": team,
        "sleeper_gsis_id": f"gsis_{player_id}",
        "nflverse_gsis_id": f"gsis_{player_id}",
        "pfr_id": f"pfr_{player_id}",
        "match_method": "sleeper_gsis_exact",
        "identity_status": "exact_id_match",
        "identity_confidence": 98,
        "audit_status": "ready",
        "ranking_trust_status": "ready",
    }
