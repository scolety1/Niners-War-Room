from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_v3_production_import_service import (
    V3_PRODUCTION_SEASON_HEADER,
    V3_PRODUCTION_WEEK_HEADER,
    build_truth_set_v3_production_preview,
    write_truth_set_v3_production_outputs,
)

TRUTH_HEADER = (
    "player_name",
    "position",
    "nfl_team",
)

PLAYER_STATS_HEADER = (
    "player_id",
    "player_name",
    "player_display_name",
    "position",
    "position_group",
    "headshot_url",
    "recent_team",
    "season",
    "week",
    "season_type",
    "opponent_team",
    "completions",
    "attempts",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "sacks",
    "sack_yards",
    "sack_fumbles",
    "sack_fumbles_lost",
    "passing_air_yards",
    "passing_yards_after_catch",
    "passing_first_downs",
    "passing_epa",
    "passing_2pt_conversions",
    "pacr",
    "dakota",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "rushing_fumbles",
    "rushing_fumbles_lost",
    "rushing_first_downs",
    "rushing_epa",
    "rushing_2pt_conversions",
    "receptions",
    "targets",
    "receiving_yards",
    "receiving_tds",
    "receiving_fumbles",
    "receiving_fumbles_lost",
    "receiving_air_yards",
    "receiving_yards_after_catch",
    "receiving_first_downs",
    "receiving_epa",
    "receiving_2pt_conversions",
    "racr",
    "target_share",
    "air_yards_share",
    "wopr",
    "special_teams_tds",
    "fantasy_points",
    "fantasy_points_ppr",
)


def test_v3_production_import_maps_fields_and_first_downs(tmp_path: Path) -> None:
    truth_set = tmp_path / "truth.csv"
    player_stats = tmp_path / "player_stats.csv"
    _write_truth_set(
        truth_set,
        [
            {"player_name": "Runner Jr.", "position": "RB", "nfl_team": "ATL"},
        ],
    )
    _write_player_stats(
        player_stats,
        [
            {
                "player_id": "00-1",
                "player_display_name": "Runner",
                "position": "RB",
                "recent_team": "ATL",
                "season": "2024",
                "week": "1",
                "season_type": "REG",
                "carries": "10",
                "rushing_yards": "55",
                "rushing_tds": "1",
                "rushing_first_downs": "4",
                "targets": "3",
                "receptions": "2",
                "receiving_yards": "20",
                "receiving_tds": "0",
                "receiving_first_downs": "1",
                "rushing_fumbles": "1",
                "rushing_fumbles_lost": "1",
            }
        ],
    )

    result = build_truth_set_v3_production_preview(
        truth_set_path=truth_set,
        player_stats_path=player_stats,
        download_if_missing=False,
        seasons={2024},
    )

    assert result.summary["status"] == "ready"
    assert result.summary["matched_players"] == 1
    week = result.week_rows[0]
    assert week["truth_set_player_name"] == "Runner Jr."
    assert week["matched_player_name"] == "Runner"
    assert week["source_status"] == "imported_real_data"
    assert week["rushing_first_downs"] == 4
    assert week["receiving_first_downs"] == 1
    assert week["total_fumbles"] == 1
    assert week["fumbles_lost"] == 1


def test_v3_production_import_resolves_known_name_aliases(tmp_path: Path) -> None:
    truth_set = tmp_path / "truth.csv"
    player_stats = tmp_path / "player_stats.csv"
    _write_truth_set(
        truth_set,
        [{"player_name": "Hollywood Brown", "position": "WR", "nfl_team": "KC"}],
    )
    _write_player_stats(
        player_stats,
        [
            {
                "player_id": "00-35662",
                "player_display_name": "Marquise Brown",
                "position": "WR",
                "recent_team": "KC",
                "season": "2024",
                "week": "1",
                "season_type": "REG",
                "targets": "8",
                "receptions": "5",
                "receiving_yards": "45",
                "receiving_first_downs": "3",
            }
        ],
    )

    result = build_truth_set_v3_production_preview(
        truth_set_path=truth_set,
        player_stats_path=player_stats,
        download_if_missing=False,
        seasons={2024},
    )

    assert result.summary["matched_players"] == 1
    assert result.week_rows[0]["truth_set_player_name"] == "Hollywood Brown"
    assert result.week_rows[0]["matched_player_name"] == "Marquise Brown"
    assert result.week_rows[0]["targets"] == 8
    assert result.missing_rows == ()


def test_v3_production_import_builds_player_season_totals(tmp_path: Path) -> None:
    truth_set = tmp_path / "truth.csv"
    player_stats = tmp_path / "player_stats.csv"
    _write_truth_set(
        truth_set,
        [{"player_name": "Passer One", "position": "QB", "nfl_team": "BAL"}],
    )
    _write_player_stats(
        player_stats,
        [
            {
                "player_id": "00-2",
                "player_display_name": "Passer One",
                "position": "QB",
                "recent_team": "BAL",
                "season": "2024",
                "week": "1",
                "season_type": "REG",
                "passing_yards": "250",
                "passing_tds": "2",
                "interceptions": "1",
                "carries": "8",
                "rushing_yards": "40",
                "rushing_tds": "1",
                "rushing_first_downs": "3",
            },
            {
                "player_id": "00-2",
                "player_display_name": "Passer One",
                "position": "QB",
                "recent_team": "BAL",
                "season": "2024",
                "week": "2",
                "season_type": "REG",
                "passing_yards": "200",
                "passing_tds": "1",
                "interceptions": "0",
                "carries": "5",
                "rushing_yards": "30",
                "rushing_tds": "0",
                "rushing_first_downs": "2",
            },
        ],
    )

    result = build_truth_set_v3_production_preview(
        truth_set_path=truth_set,
        player_stats_path=player_stats,
        download_if_missing=False,
        seasons={2024},
    )

    season = result.season_rows[0]
    assert season["games"] == 2
    assert season["passing_yards"] == 450
    assert season["passing_tds"] == 3
    assert season["interceptions"] == 1
    assert season["rushing_attempts"] == 13
    assert season["rushing_first_downs"] == 5
    assert season["source_status"] == "imported_real_data"


def test_v3_production_import_marks_missing_players_without_fake_rows(
    tmp_path: Path,
) -> None:
    truth_set = tmp_path / "truth.csv"
    player_stats = tmp_path / "player_stats.csv"
    _write_truth_set(
        truth_set,
        [
            {"player_name": "Incoming Rookie", "position": "WR", "nfl_team": "CHI"},
        ],
    )
    _write_player_stats(player_stats, [])

    result = build_truth_set_v3_production_preview(
        truth_set_path=truth_set,
        player_stats_path=player_stats,
        download_if_missing=False,
        seasons={2024},
    )

    assert result.week_rows == ()
    assert result.season_rows == ()
    assert result.missing_rows[0]["source_status"] == "missing"
    assert result.missing_rows[0]["match_status"] == "missing_nflverse_player_stats"


def test_v3_production_import_rejects_missing_first_down_fields(
    tmp_path: Path,
) -> None:
    truth_set = tmp_path / "truth.csv"
    player_stats = tmp_path / "player_stats.csv"
    _write_truth_set(
        truth_set,
        [{"player_name": "Runner One", "position": "RB", "nfl_team": "ATL"}],
    )
    with player_stats.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=tuple(
                field
                for field in PLAYER_STATS_HEADER
                if field not in {"rushing_first_downs", "receiving_first_downs"}
            ),
        )
        writer.writeheader()

    result = build_truth_set_v3_production_preview(
        truth_set_path=truth_set,
        player_stats_path=player_stats,
        download_if_missing=False,
        seasons={2024},
    )

    assert result.summary["status"] == "blocked"
    assert any("first-down" in error for error in result.validation_errors)


def test_v3_production_write_uses_stable_headers(tmp_path: Path) -> None:
    truth_set = tmp_path / "truth.csv"
    player_stats = tmp_path / "player_stats.csv"
    output = tmp_path / "reports"
    _write_truth_set(
        truth_set,
        [{"player_name": "Runner One", "position": "RB", "nfl_team": "ATL"}],
    )
    _write_player_stats(
        player_stats,
        [
            {
                "player_id": "00-1",
                "player_display_name": "Runner One",
                "position": "RB",
                "recent_team": "ATL",
                "season": "2024",
                "week": "1",
                "season_type": "REG",
                "carries": "1",
                "rushing_first_downs": "1",
            }
        ],
    )
    result = build_truth_set_v3_production_preview(
        truth_set_path=truth_set,
        player_stats_path=player_stats,
        download_if_missing=False,
        seasons={2024},
    )

    paths = write_truth_set_v3_production_outputs(output, result)

    assert _header(paths["week"]) == V3_PRODUCTION_WEEK_HEADER
    assert _header(paths["season"]) == V3_PRODUCTION_SEASON_HEADER


def _write_truth_set(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRUTH_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _write_player_stats(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAYER_STATS_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
