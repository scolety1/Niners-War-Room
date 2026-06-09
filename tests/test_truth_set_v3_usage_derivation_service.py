from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_v3_usage_derivation_service import (
    V3_USAGE_SEASON_HEADER,
    V3_USAGE_WEEK_HEADER,
    TruthSetV3UsageResult,
    UsagePlayer,
    UsagePlayerWeek,
    aggregate_usage_season_rows,
    derive_usage_week_rows_from_pbp_rows,
    write_truth_set_v3_usage_outputs,
)


def test_usage_derivation_calculates_target_share_red_zone_and_goal_line() -> None:
    players = [
        UsagePlayer(
            truth_set_player_name="Receiver One",
            matched_player_name="Receiver One",
            player_id="00-r",
            position="WR",
            nfl_team="SF",
        )
    ]
    pbp_rows = [
        _target("00-r", season=2024, week=1, team="SF", yardline=15),
        _target("00-other", season=2024, week=1, team="SF", yardline=50),
        _target("00-other2", season=2024, week=1, team="SF", yardline=4),
    ]

    rows = derive_usage_week_rows_from_pbp_rows(pbp_rows, players=players)

    assert len(rows) == 1
    row = rows[0]
    assert row["targets"] == 1
    assert row["team_targets"] == 3
    assert row["target_share"] == 0.3333
    assert row["red_zone_targets"] == 1
    assert row["goal_line_targets"] == 0
    assert row["source_status"] == "derived_real_data"
    assert "route_participation" in row["notes"]


def test_usage_derivation_calculates_rb_carry_share_and_weighted_opportunities() -> None:
    players = [
        UsagePlayer(
            truth_set_player_name="Runner One",
            matched_player_name="Runner One",
            player_id="00-rb",
            position="RB",
            nfl_team="ATL",
        )
    ]
    pbp_rows = [
        _rush("00-rb", season=2024, week=1, team="ATL", yardline=3, ydstogo=1),
        _rush("00-rb", season=2024, week=1, team="ATL", yardline=30, ydstogo=10),
        _rush("00-qb", season=2024, week=1, team="ATL", yardline=10, ydstogo=2),
        _target("00-rb", season=2024, week=1, team="ATL", yardline=4),
        _target("00-wr", season=2024, week=1, team="ATL", yardline=20),
    ]

    row = derive_usage_week_rows_from_pbp_rows(pbp_rows, players=players)[0]

    assert row["rushing_attempts"] == 2
    assert row["team_rushing_attempts"] == 3
    assert row["rb_carry_share"] == 0.6667
    assert row["targets"] == 1
    assert row["team_targets"] == 2
    assert row["rb_target_share"] == 0.5
    assert row["weighted_opportunities"] == 3.15
    assert row["red_zone_carries"] == 1
    assert row["goal_line_carries"] == 1
    assert row["goal_line_targets"] == 1
    assert row["short_yardage_carries"] == 1


def test_usage_derivation_ignores_no_play_rows() -> None:
    players = [
        UsagePlayer("Runner One", "Runner One", "00-rb", "RB", "ATL"),
    ]
    pbp_rows = [
        {**_rush("00-rb", season=2024, week=1, team="ATL", yardline=3, ydstogo=1), "no_play": 1},
    ]

    rows = derive_usage_week_rows_from_pbp_rows(pbp_rows, players=players)

    assert rows == []


def test_usage_derivation_seeds_active_zero_usage_weeks() -> None:
    players = [UsagePlayer("Receiver One", "Receiver One", "00-wr", "WR", "SF")]
    pbp_rows = [
        _target("00-other", season=2024, week=1, team="SF", yardline=50),
    ]

    rows = derive_usage_week_rows_from_pbp_rows(
        pbp_rows,
        players=players,
        player_weeks=[UsagePlayerWeek("00-wr", 2024, 1, "SF")],
    )

    assert len(rows) == 1
    assert rows[0]["targets"] == 0
    assert rows[0]["team_targets"] == 1
    assert rows[0]["target_share"] == 0.0


def test_usage_season_aggregation_recomputes_shares_from_totals() -> None:
    players = [UsagePlayer("Runner One", "Runner One", "00-rb", "RB", "ATL")]
    week_rows = derive_usage_week_rows_from_pbp_rows(
        [
            _rush("00-rb", season=2024, week=1, team="ATL", yardline=50, ydstogo=10),
            _rush("00-other", season=2024, week=1, team="ATL", yardline=50, ydstogo=10),
            _target("00-rb", season=2024, week=2, team="ATL", yardline=19),
            _target("00-other", season=2024, week=2, team="ATL", yardline=50),
        ],
        players=players,
    )

    season = aggregate_usage_season_rows(week_rows)[0]

    assert season["games_with_usage"] == 2
    assert season["rushing_attempts"] == 1
    assert season["team_rushing_attempts"] == 2
    assert season["rb_carry_share"] == 0.5
    assert season["targets"] == 1
    assert season["team_targets"] == 2
    assert season["target_share"] == 0.5
    assert season["weighted_opportunities"] == 2.15


def test_usage_write_uses_stable_headers(tmp_path: Path) -> None:
    result = TruthSetV3UsageResult(
        week_rows=tuple(
            derive_usage_week_rows_from_pbp_rows(
                [_target("00-wr", season=2024, week=1, team="SF", yardline=15)],
                players=[UsagePlayer("WR One", "WR One", "00-wr", "WR", "SF")],
            )
        ),
        season_rows=(),
        missing_rows=(),
        summary={"status": "ready"},
    )
    paths = write_truth_set_v3_usage_outputs(tmp_path, result)

    assert _header(paths["week"]) == V3_USAGE_WEEK_HEADER
    assert _header(paths["season"]) == V3_USAGE_SEASON_HEADER


def _target(
    player_id: str,
    *,
    season: int,
    week: int,
    team: str,
    yardline: int,
) -> dict[str, object]:
    return {
        "season": season,
        "week": week,
        "posteam": team,
        "pass_attempt": 1,
        "rush_attempt": 0,
        "no_play": 0,
        "yardline_100": yardline,
        "ydstogo": 10,
        "receiver_player_id": player_id,
        "receiver_player_name": "Receiver",
        "rusher_player_id": "",
        "rusher_player_name": "",
    }


def _rush(
    player_id: str,
    *,
    season: int,
    week: int,
    team: str,
    yardline: int,
    ydstogo: int,
) -> dict[str, object]:
    return {
        "season": season,
        "week": week,
        "posteam": team,
        "pass_attempt": 0,
        "rush_attempt": 1,
        "no_play": 0,
        "yardline_100": yardline,
        "ydstogo": ydstogo,
        "receiver_player_id": "",
        "receiver_player_name": "",
        "rusher_player_id": player_id,
        "rusher_player_name": "Runner",
    }


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
