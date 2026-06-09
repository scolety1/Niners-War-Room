from __future__ import annotations

import csv
from pathlib import Path

from src.services.public_data_preview_import_service import (
    build_identity_map_rows,
    build_preview_coverage_rows,
    transform_official_injury_rows,
)


def test_identity_map_prefers_dynastyprocess_sleeper_to_gsis_bridge(
    tmp_path: Path,
) -> None:
    pack = _data_pack(tmp_path)

    rows = build_identity_map_rows(
        data_pack_path=pack,
        sleeper_player_rows=[
            {
                "sleeper_id": "100",
                "player_name": "Alpha Receiver",
                "position": "WR",
                "team": "SEA",
                "status": "Active",
                "birth_date": "2001-01-01",
                "age": "25",
                "gsis_id": "",
                "espn_id": "",
                "fantasy_data_id": "",
                "pfr_id": "",
            }
        ],
        ffid_rows=[
            {
                "sleeper_id": "100",
                "gsis_id": "00-001",
                "pfr_id": "AlphRe00",
                "espn_id": "999",
                "fantasy_data_id": "888",
                "nfl_id": "777",
                "name": "Alpha Receiver",
                "position": "WR",
                "team": "SEA",
            }
        ],
        nflverse_player_rows=[
            {
                "gsis_id": "00-001",
                "display_name": "Alpha Receiver",
                "birth_date": "2001-01-01",
                "position": "WR",
            }
        ],
    )

    assert rows[0]["player_id"] == "100"
    assert rows[0]["sleeper_id"] == "100"
    assert rows[0]["gsis_id"] == "00-001"
    assert rows[0]["match_method"] == "sleeper_id"
    assert rows[0]["match_confidence"] == "98"
    assert rows[0]["review_status"] == "ready"


def test_injury_transform_maps_status_and_body_part() -> None:
    rows = transform_official_injury_rows(
        [
            {
                "season": "2025",
                "season_type": "REG",
                "team": "SEA",
                "week": "4",
                "gsis_id": "00-001",
                "position": "RB",
                "full_name": "Back One",
                "report_primary_injury": "Knee",
                "report_status": "Questionable",
                "practice_primary_injury": "Knee",
                "practice_status": "Limited Participation",
            }
        ],
        season=2025,
        identity_rows=[{"gsis_id": "00-001", "sleeper_id": "100"}],
    )

    assert rows == [
        {
            "season": "2025",
            "week": "4",
            "team": "SEA",
            "gsis_id": "00-001",
            "sleeper_id": "100",
            "player_name": "Back One",
            "position": "RB",
            "report_primary_injury": "Knee",
            "report_secondary_injury": "",
            "report_status": "Questionable",
            "practice_primary_injury": "Knee",
            "practice_secondary_injury": "",
            "practice_status": "Limited Participation",
            "normalized_body_part": "lower_body",
            "date_modified": "",
            "source_confidence": "88",
        }
    ]


def test_preview_coverage_marks_missing_critical_buckets(
    tmp_path: Path,
) -> None:
    pack = _data_pack(tmp_path)

    coverage, gaps = build_preview_coverage_rows(
        data_pack_path=pack,
        identity_rows=[
            {
                "player_id": "100",
                "sleeper_id": "100",
                "gsis_id": "00-001",
                "match_confidence": "98",
                "review_status": "ready",
            }
        ],
        player_stats_rows=[{"gsis_id": "00-001"}],
        snap_rows=[],
        depth_rows=[],
        ffid_rows=[{"sleeper_id": "100", "birthdate": "2001-01-01"}],
        nflverse_player_rows=[],
    )

    assert coverage[0]["identity_status"] == "ready"
    assert coverage[0]["production_status"] == "ready"
    assert coverage[0]["age_bio_status"] == "ready"
    assert coverage[0]["role_usage_status"] == "blocked"
    assert coverage[0]["decision_effect"] == "blocks_decision_ready"
    assert gaps == [
        {
            "player_id": "100",
            "player_name": "Alpha Receiver",
            "position": "WR",
            "team": "SEA",
            "missing_bucket": "role/usage",
            "decision_effect": "blocks_decision_ready",
            "next_action": "Confirm snap/depth ID mapping or add reviewed role source.",
        }
    ]


def _data_pack(tmp_path: Path) -> Path:
    root = tmp_path / "pack"
    root.mkdir()
    _write(
        root / "dim_players.csv",
        (
            "player_id",
            "player_name",
            "merge_name",
            "position",
            "nfl_team",
            "birth_date",
            "rookie_year",
            "height_in",
            "weight_lb",
            "sleeper_id",
            "fantasypros_id",
            "ktc_id",
            "fantasycalc_id",
            "pfr_id",
            "cfb_id",
            "active_flag",
            "created_at",
            "updated_at",
        ),
        [
            {
                "player_id": "100",
                "player_name": "Alpha Receiver",
                "merge_name": "alpha receiver",
                "position": "WR",
                "nfl_team": "SEA",
                "sleeper_id": "100",
                "active_flag": "1",
            }
        ],
    )
    _write(
        root / "dim_teams.csv",
        (
            "team_id",
            "team_name",
            "owner_name",
            "sleeper_roster_id",
            "is_user_team",
            "created_at",
            "updated_at",
        ),
        [{"team_id": "1", "team_name": "Niners", "owner_name": "me"}],
    )
    _write(
        root / "fact_rosters.csv",
        (
            "snapshot_date",
            "season",
            "team_id",
            "team_name",
            "player_id",
            "league_id",
            "owner_name",
            "player_name",
            "position",
            "nfl_team",
            "roster_status",
            "league_rank",
            "official_rank",
            "source",
        ),
        [
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "team_id": "1",
                "team_name": "Niners",
                "player_id": "100",
                "league_id": "league",
                "owner_name": "me",
                "player_name": "Alpha Receiver",
                "position": "WR",
                "nfl_team": "SEA",
                "roster_status": "rostered",
                "source": "test",
            }
        ],
    )
    _write(
        root / "fact_future_picks.csv",
        (
            "snapshot_date",
            "season",
            "pick_year",
            "round",
            "slot",
            "pick_label",
            "overall_pick",
            "original_team_id",
            "original_team_name",
            "current_team_id",
            "current_team_name",
            "current_owner_name",
            "certainty",
            "source",
        ),
        [
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "pick_year": "2026",
                "round": "1",
                "slot": "1",
                "pick_label": "2026 1.01",
                "overall_pick": "1",
                "original_team_id": "1",
                "original_team_name": "Niners",
                "current_team_id": "1",
                "current_team_name": "Niners",
                "current_owner_name": "me",
                "certainty": "test",
                "source": "test",
            }
        ],
    )
    _write(
        root / "model_outputs.csv",
        (
            "snapshot_date",
            "season",
            "player_id",
            "player_name",
            "position",
            "team_id",
            "team_name",
            "market_score",
            "keeper_score",
            "drop_candidate_score",
            "trade_value",
            "war_room_score",
            "confidence_score",
            "risk_level",
            "recommendation",
            "reasons",
            "model_version",
        ),
        [
            {
                "snapshot_date": "2026-pre-draft",
                "season": "2026",
                "player_id": "100",
                "player_name": "Alpha Receiver",
                "position": "WR",
                "team_id": "1",
                "team_name": "Niners",
                "market_score": "80",
                "keeper_score": "80",
                "drop_candidate_score": "20",
                "trade_value": "80",
                "war_room_score": "80",
                "confidence_score": "80",
                "risk_level": "low",
                "recommendation": "keep",
                "reasons": "test",
                "model_version": "test",
            }
        ],
    )
    _write(
        root / "source_metadata.csv",
        (
            "snapshot_date",
            "league_id",
            "file_name",
            "source_name",
            "source_type",
            "review_status",
            "notes",
        ),
        [
            {
                "snapshot_date": "2026-pre-draft",
                "league_id": "league",
                "file_name": "dim_players.csv",
                "source_name": "test",
                "source_type": "test",
                "review_status": "ready",
                "notes": "test",
            }
        ],
    )
    return root


def _write(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
