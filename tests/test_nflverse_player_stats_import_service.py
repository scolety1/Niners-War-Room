from __future__ import annotations

import csv
from pathlib import Path

from src.services.nflverse_player_stats_import_service import (
    LOCAL_DEPTH_CHARTS_FILE_NAME,
    LOCAL_PLAYER_STATS_FILE_NAME,
    LOCAL_SNAP_COUNTS_FILE_NAME,
    official_player_stats_source_rows,
    transform_official_depth_chart_csv,
    transform_official_depth_chart_rows,
    transform_official_player_stats_csv,
    transform_official_player_stats_rows,
    transform_official_snap_counts_csv,
    transform_official_snap_counts_rows,
)
from src.services.nflverse_raw_import_service import validate_nflverse_raw_imports
from src.services.real_input_template_service import NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS


def test_transform_official_player_stats_maps_lve_fields() -> None:
    rows = transform_official_player_stats_rows(
        [
            {
                "season": "2025",
                "week": "1",
                "season_type": "REG",
                "player_id": "00-0031234",
                "player_display_name": "Receiver One",
                "position": "WR",
                "recent_team": "SEA",
                "targets": "11",
                "receptions": "8",
                "receiving_yards": "124",
                "receiving_tds": "1",
                "receiving_first_downs": "7",
                "receiving_air_yards": "140",
                "target_share": "0.31",
                "air_yards_share": "0.42",
                "wopr": "0.78",
                "receiving_epa": "7.5",
                "rushing_fumbles_lost": "1",
            }
        ],
        seasons={2025},
    )

    assert rows == [
        {
            "season": "2025",
            "week": "1",
            "player_id": "00-0031234",
            "gsis_id": "00-0031234",
            "sleeper_id": "",
            "player_name": "Receiver One",
            "position": "WR",
            "team": "SEA",
            "passing_yards": "",
            "passing_tds": "",
            "interceptions": "",
            "rushing_attempts": "",
            "rushing_yards": "",
            "rushing_tds": "",
            "rushing_first_downs": "",
            "targets": "11",
            "receptions": "8",
            "receiving_yards": "124",
            "receiving_tds": "1",
            "receiving_first_downs": "7",
            "passing_first_downs": "",
            "passing_epa": "",
            "rushing_epa": "",
            "receiving_epa": "7.5",
            "receiving_air_yards": "140",
            "target_share": "0.31",
            "air_yards_share": "0.42",
            "wopr": "0.78",
            "return_yards": "",
            "return_tds": "",
            "kick_return_yards": "",
            "kick_return_tds": "",
            "punt_return_yards": "",
            "punt_return_tds": "",
            "fumbles_lost": "1",
            "source_updated_at": "",
        }
    ]


def test_transform_filters_playoffs_and_unsupported_positions() -> None:
    rows = transform_official_player_stats_rows(
        [
            {"season": "2025", "week": "1", "season_type": "REG", "position": "RB"},
            {"season": "2025", "week": "2", "season_type": "POST", "position": "WR"},
            {"season": "2025", "week": "3", "season_type": "REG", "position": "K"},
        ],
        seasons={2025},
    )

    assert len(rows) == 1
    assert rows[0]["position"] == "RB"


def test_transform_sums_all_fumbles_lost() -> None:
    rows = transform_official_player_stats_rows(
        [
            {
                "season": "2025",
                "week": "1",
                "season_type": "REG",
                "player_id": "00-0039999",
                "position": "QB",
                "sack_fumbles_lost": "1",
                "rushing_fumbles_lost": "2",
                "receiving_fumbles_lost": "0",
            }
        ],
    )

    assert rows[0]["fumbles_lost"] == "3"


def test_transformed_csv_validates_against_raw_import_contract(tmp_path: Path) -> None:
    input_path = tmp_path / "official_player_stats.csv"
    output_root = tmp_path / "raw"
    output_path = output_root / LOCAL_PLAYER_STATS_FILE_NAME
    _write_csv(
        input_path,
        [
            {
                "season": "2025",
                "week": "1",
                "season_type": "REG",
                "player_id": "00-0031234",
                "player_display_name": "Receiver One",
                "position": "WR",
                "recent_team": "SEA",
                "receiving_yards": "124",
                "receiving_first_downs": "7",
            }
        ],
    )
    for file_name, header in NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS.items():
        if file_name != LOCAL_PLAYER_STATS_FILE_NAME:
            _write_csv(output_root / file_name, [], header=header)

    report = transform_official_player_stats_csv(input_path, output_path, seasons={2025})
    validation_report = validate_nflverse_raw_imports(output_root)

    assert report.status == "ready"
    assert report.rows_transformed == 1
    assert validation_report.status == "ready"


def test_transform_official_snap_counts_uses_identity_map_when_present() -> None:
    rows = transform_official_snap_counts_rows(
        [
            {
                "game_id": "2025_01_SEA_LAR",
                "season": "2025",
                "game_type": "REG",
                "week": "1",
                "player": "Receiver One",
                "pfr_player_id": "ReceOn00",
                "position": "WR",
                "team": "SEA",
                "opponent": "LAR",
                "offense_snaps": "61",
                "offense_pct": "89%",
                "st_snaps": "2",
                "st_pct": "5%",
            }
        ],
        seasons={2025},
        identity_rows=[
            {
                "pfr_id": "ReceOn00",
                "gsis_id": "00-0031234",
                "sleeper_id": "9999",
            }
        ],
    )

    assert rows == [
        {
            "season": "2025",
            "week": "1",
            "game_id": "2025_01_SEA_LAR",
            "gsis_id": "00-0031234",
            "sleeper_id": "9999",
            "player_name": "Receiver One",
            "position": "WR",
            "team": "SEA",
            "opponent": "LAR",
            "offense_snaps": "61",
            "offense_pct": "0.89",
            "st_snaps": "2",
            "st_pct": "0.05",
            "source_updated_at": "",
        }
    ]


def test_transform_official_depth_chart_maps_role_context() -> None:
    rows = transform_official_depth_chart_rows(
        [
            {
                "dt": "2025-09-01",
                "team": "SEA",
                "player_name": "Receiver One",
                "espn_id": "123",
                "gsis_id": "00-0031234",
                "pos_abb": "WR",
                "pos_slot": "WR1",
                "pos_rank": "1",
            }
        ],
        season=2025,
        default_week=1,
        identity_rows=[
            {
                "gsis_id": "00-0031234",
                "espn_id": "123",
                "sleeper_id": "9999",
            }
        ],
    )

    assert rows == [
        {
            "season": "2025",
            "week": "1",
            "team": "SEA",
            "dt": "2025-09-01",
            "gsis_id": "00-0031234",
            "espn_id": "123",
            "sleeper_id": "9999",
            "player_name": "Receiver One",
            "position": "WR",
            "pos_slot": "WR1",
            "pos_rank": "1",
            "depth_chart_role_score": "100",
            "schema_version": "official_nflverse_depth_charts_v1",
        }
    ]


def test_transform_official_depth_chart_supports_legacy_depth_schema() -> None:
    rows = transform_official_depth_chart_rows(
        [
            {
                "season": "2024",
                "club_code": "SEA",
                "week": "1",
                "game_type": "REG",
                "depth_team": "2",
                "position": "WR",
                "depth_position": "WR2",
                "full_name": "Receiver One",
                "gsis_id": "00-0031234",
            }
        ],
        season=2024,
        identity_rows=[
            {
                "gsis_id": "00-0031234",
                "sleeper_id": "9999",
            }
        ],
    )

    assert rows == [
        {
            "season": "2024",
            "week": "1",
            "team": "SEA",
            "dt": "",
            "gsis_id": "00-0031234",
            "espn_id": "",
            "sleeper_id": "9999",
            "player_name": "Receiver One",
            "position": "WR",
            "pos_slot": "WR2",
            "pos_rank": "2",
            "depth_chart_role_score": "82",
            "schema_version": "official_nflverse_depth_charts_v1",
        }
    ]


def test_transform_official_depth_chart_skips_incomplete_source_rows() -> None:
    rows = transform_official_depth_chart_rows(
        [
            {
                "season": "2024",
                "club_code": "SEA",
                "week": "1",
                "game_type": "REG",
                "depth_team": "2",
                "position": "WR",
                "depth_position": "WR2",
                "full_name": "",
                "gsis_id": "00-0031234",
            }
        ],
        season=2024,
    )

    assert rows == []


def test_snap_and_depth_transformed_csvs_validate_contract(tmp_path: Path) -> None:
    output_root = tmp_path / "raw"
    snap_input = tmp_path / "snap_counts_2025.csv"
    depth_input = tmp_path / "depth_charts_2025.csv"
    _write_csv(
        snap_input,
        [
            {
                "game_id": "2025_01_SEA_LAR",
                "season": "2025",
                "game_type": "REG",
                "week": "1",
                "player": "Receiver One",
                "position": "WR",
                "team": "SEA",
                "opponent": "LAR",
                "offense_snaps": "61",
                "offense_pct": "0.89",
                "st_snaps": "2",
                "st_pct": "0.05",
            }
        ],
    )
    _write_csv(
        depth_input,
        [
            {
                "dt": "2025-09-01",
                "team": "SEA",
                "player_name": "Receiver One",
                "gsis_id": "00-0031234",
                "pos_abb": "WR",
                "pos_slot": "WR1",
                "pos_rank": "1",
            }
        ],
    )
    for file_name, header in NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS.items():
        if file_name not in {
            LOCAL_SNAP_COUNTS_FILE_NAME,
            LOCAL_DEPTH_CHARTS_FILE_NAME,
        }:
            _write_csv(output_root / file_name, [], header=header)

    snap_report = transform_official_snap_counts_csv(
        snap_input,
        output_root / LOCAL_SNAP_COUNTS_FILE_NAME,
        seasons={2025},
    )
    depth_report = transform_official_depth_chart_csv(
        depth_input,
        output_root / LOCAL_DEPTH_CHARTS_FILE_NAME,
        season=2025,
        default_week=1,
    )
    validation_report = validate_nflverse_raw_imports(output_root)

    assert snap_report.rows_transformed == 1
    assert depth_report.rows_transformed == 1
    assert validation_report.status == "ready"


def test_official_source_manifest_is_review_only_and_stats_first() -> None:
    rows = official_player_stats_source_rows()
    by_source = {str(row["source_name"]): row for row in rows}

    assert rows[0]["scraping_required"] == "false"
    assert "none until transformed" in str(rows[0]["scoring_effect"])
    assert "rushing_first_downs" in str(rows[0]["key_fields"])
    assert "wopr" in str(rows[0]["key_fields"])
    assert "nflverse snap counts" in by_source
    assert "pfr_player_id" in str(by_source["nflverse snap counts"]["key_fields"])
    assert "joined to players by name alone" in str(
        by_source["nflverse snap counts"]["limitations"]
    )
    assert "nflverse depth charts" in by_source
    assert "gsis_id" in str(by_source["nflverse depth charts"]["key_fields"])


def _write_csv(
    path: Path,
    rows: list[dict[str, str]],
    *,
    header: tuple[str, ...] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(header or sorted({key for row in rows for key in row}))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
