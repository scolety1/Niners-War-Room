from __future__ import annotations

import sqlite3

from src.data.csv_schemas import REQUIRED_V1_FILES
from src.data.loaders import load_data_pack
from src.data.validators import validate_data_pack


def test_required_v1_files_include_core_csvs() -> None:
    assert "dim_players.csv" in REQUIRED_V1_FILES
    assert "fact_rosters.csv" in REQUIRED_V1_FILES
    assert "metadata_sources.csv" in REQUIRED_V1_FILES


def test_sample_data_pack_validates_with_full_sample_roster() -> None:
    result = validate_data_pack("sample_data/2026_pre_declaration")

    assert not result.has_errors
    assert result.issues == ()


def test_validation_catches_duplicate_players_and_missing_official_rank(tmp_path) -> None:
    pack = _write_pack(
        tmp_path,
        rosters=[
            "2026-08-01,2026,niners,Niners,p1,Lamar Jackson,QB,BAL,starter,1,manual",
            "2026-08-01,2026,owls,Owls,p1,Lamar Jackson,QB,BAL,starter,1,manual",
        ],
        rankings=[
            "2026-08-01,2026,manual,FantasyPros,2026-07-30,p2,Other Player,RB,SEA,400,,1",
        ],
    )

    result = validate_data_pack(pack)
    issues = {(issue.severity, issue.issue) for issue in result.issues}

    assert ("error", "Player appears on multiple teams.") in issues
    assert ("warning", "Roster player is missing an official rank.") in issues
    assert ("warning", "Official rank is 400.") in issues


def test_validation_catches_duplicate_draft_picks_invalid_labels_and_unknown_teams(
    tmp_path,
) -> None:
    pack = _write_pack(
        tmp_path,
        future_picks=[
            "2026-08-01,2026,2026,1,1,2026 1.01,1,niners,Niners,niners,Niners,Michael,known,manual",
            "2026-08-01,2026,2026,1,1,2026 1.01,1,niners,Niners,niners,Niners,Michael,known,manual",
            "2026-08-01,2026,2026,1,2,2026 1.02,2,ghost,Ghost,niners,Niners,Michael,known,manual",
            "2026-08-01,2026,2026,1,3,bad-label,3,niners,Niners,niners,Niners,Michael,known,manual",
        ],
    )

    result = validate_data_pack(pack)
    issues = {(issue.severity, issue.issue) for issue in result.issues}

    assert ("error", "Duplicate draft pick.") in issues
    assert ("error", "Invalid pick label.") in issues
    assert ("warning", "Unknown team.") in issues


def test_validation_catches_duplicate_draft_pick_when_slot_is_blank(tmp_path) -> None:
    pack = _write_pack(
        tmp_path,
        future_picks=[
            "2026-08-01,2026,2026,1,1,2026 1.01,1,niners,Niners,niners,Niners,Michael,known,manual",
            "2026-08-01,2026,2026,1,,2026 1.01,1,niners,Niners,niners,Niners,Michael,known,manual",
        ],
    )

    result = validate_data_pack(pack)
    issues = {(issue.severity, issue.issue) for issue in result.issues}

    assert ("error", "Duplicate draft pick.") in issues


def test_validation_catches_missing_player_identity(tmp_path) -> None:
    pack = _write_pack(
        tmp_path,
        rosters=[
            "2026-08-01,2026,niners,Niners,,,QB,BAL,starter,1,manual",
        ],
    )

    result = validate_data_pack(pack)
    issues = {(issue.severity, issue.issue) for issue in result.issues}

    assert ("error", "Missing player identity.") in issues
    assert ("error", "Missing required value for player_id.") in issues


def test_load_data_pack_writes_rows_and_import_errors(tmp_path) -> None:
    database_path = tmp_path / "war_room.sqlite"
    result = load_data_pack("sample_data/2026_pre_declaration", database_path)
    connection = sqlite3.connect(database_path)

    player_count = connection.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    roster_count = connection.execute("SELECT COUNT(*) FROM rosters").fetchone()[0]
    import_issue_count = connection.execute("SELECT COUNT(*) FROM import_errors").fetchone()[0]

    assert result.inserted_rows["players"] == 24
    assert player_count == 24
    assert roster_count == 24
    assert import_issue_count == 0


def _write_pack(
    root,
    rosters: list[str] | None = None,
    rankings: list[str] | None = None,
    future_picks: list[str] | None = None,
):
    pack = root / "pack"
    pack.mkdir()
    _write_file(
        pack / "dim_players.csv",
        [
            "player_id,player_name,position,nfl_team",
            "p1,Lamar Jackson,QB,BAL",
            "p2,Other Player,RB,SEA",
        ],
    )
    _write_file(
        pack / "fact_rosters.csv",
        [
            (
                "snapshot_date,season,team_id,team_name,player_id,player_name,position,"
                "nfl_team,roster_status,official_rank,source"
            ),
            *(
                rosters
                or ["2026-08-01,2026,niners,Niners,p1,Lamar Jackson,QB,BAL,starter,1,manual"]
            ),
        ],
    )
    _write_file(
        pack / "fact_official_rankings.csv",
        [
            (
                "snapshot_date,season,source,rank_source_name,rank_source_date,player_id,"
                "player_name,position,nfl_team,official_rank,rank_tier,is_rank_placeholder"
            ),
            *(
                rankings
                or ["2026-08-01,2026,manual,FantasyPros,2026-07-30,p1,Lamar Jackson,QB,BAL,1,,0"]
            ),
        ],
    )
    _write_file(
        pack / "fact_future_picks.csv",
        [
            (
                "snapshot_date,season,pick_year,round,slot,pick_label,overall_pick,"
                "original_team_id,original_team_name,current_team_id,current_team_name,"
                "current_owner_name,certainty,source"
            ),
            *(
                future_picks
                or [
                    (
                        "2026-08-01,2026,2026,1,1,2026 1.01,1,niners,Niners,niners,"
                        "Niners,Michael,known,manual"
                    )
                ]
            ),
        ],
    )
    _write_file(
        pack / "fact_pick_values.csv",
        [
            (
                "snapshot_date,pick_year,pick_label,round,slot,overall_pick,base_value_1000,"
                "future_discount,certainty_adjustment,declaration_adjustment,final_pick_value,"
                "bucket,source"
            ),
            "2026-08-01,2026,2026 1.01,1,1,1,1000,1,1,0,1000,elite,manual",
        ],
    )
    _write_file(
        pack / "model_outputs.csv",
        [
            "snapshot_date,player_id,player_name,position,private_score,war_score,recommendation",
            "2026-08-01,p1,Lamar Jackson,QB,95,95,keep",
        ],
    )
    _write_file(
        pack / "metadata_sources.csv",
        [
            "snapshot_date,data_pack_name,file_name,source_name,source_type,review_status",
            "2026-08-01,pack,dim_players.csv,manual,csv,reviewed",
        ],
    )
    return pack


def _write_file(path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
