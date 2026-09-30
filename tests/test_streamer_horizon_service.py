from __future__ import annotations

from src.services.streamer_horizon_service import build_streamer_horizon


def _row(player_id: str, name: str, position: str, team: str, points: float) -> dict[str, object]:
    return {
        "sleeperPlayerId": player_id,
        "playerName": name,
        "position": position,
        "team": team,
        "projectedPoints": points,
    }


def test_selected_horizon_changes_real_projection_order() -> None:
    weekly = {
        4: [_row("a", "One Week Star", "K", "AAA", 14), _row("b", "Four Week Play", "K", "BBB", 9)],
        5: [_row("a", "One Week Star", "K", "AAA", 2), _row("b", "Four Week Play", "K", "BBB", 9)],
        6: [_row("a", "One Week Star", "K", "AAA", 2), _row("b", "Four Week Play", "K", "BBB", 9)],
        7: [_row("a", "One Week Star", "K", "AAA", 2), _row("b", "Four Week Play", "K", "BBB", 9)],
    }
    schedule = {week: {"AAA": "vs CCC", "BBB": "@ DDD"} for week in weekly}
    one_week = build_streamer_horizon(
        start_week=4,
        horizon_weeks=1,
        weekly_rows=weekly,
        schedule_opponents=schedule,
        own_player_ids=(),
        owned_player_ids=(),
        relevant_positions=("K",),
    )
    four_week = build_streamer_horizon(
        start_week=4,
        horizon_weeks=4,
        weekly_rows=weekly,
        schedule_opponents=schedule,
        own_player_ids=(),
        owned_player_ids=(),
        relevant_positions=("K",),
    )
    assert one_week.rows[0].player_name == "One Week Star"
    assert one_week.rows[0].selected_horizon_value == 14
    assert four_week.rows[0].player_name == "Four Week Play"
    assert four_week.rows[0].selected_horizon_value == 36
    assert four_week.rows[0].values == (9.0, 18.0, 27.0, 36.0)


def test_streamer_rows_exclude_other_rosters_and_compare_to_current_player() -> None:
    weekly = {
        4: [
            _row("mine", "My Tight End", "TE", "AAA", 7),
            _row("free", "Free Tight End", "TE", "BBB", 10),
            _row("other", "Opponent Tight End", "TE", "CCC", 15),
        ]
    }
    result = build_streamer_horizon(
        start_week=4,
        horizon_weeks=1,
        weekly_rows=weekly,
        schedule_opponents={4: {"AAA": "vs DDD", "BBB": "@ EEE", "CCC": "vs FFF"}},
        own_player_ids=("mine",),
        owned_player_ids=("mine", "other"),
        relevant_positions=("TE",),
    )
    by_id = {row.sleeper_player_id: row for row in result.rows}
    assert set(by_id) == {"mine", "free"}
    assert by_id["free"].availability == "AVAILABLE"
    assert by_id["free"].action == "STREAM"
    assert by_id["mine"].availability == "ON YOUR ROSTER"
    assert by_id["mine"].action == "KEEP CURRENT"
    assert by_id["free"].schedule == ("W4 @ EEE", "W5 unknown", "W6 unknown", "W7 unknown")


def test_missing_future_projection_week_never_fakes_four_week_value() -> None:
    result = build_streamer_horizon(
        start_week=4,
        horizon_weeks=4,
        weekly_rows={4: [_row("qb", "Quarterback", "QB", "AAA", 20)]},
        schedule_opponents={4: {"AAA": "vs BBB"}},
        own_player_ids=(),
        owned_player_ids=(),
        relevant_positions=("QB",),
    )
    assert result.rows[0].values[0] == 20
    assert result.rows[0].values[3] is None
    assert result.rows[0].selected_horizon_value is None
    assert result.rows[0].action == "NOT ENOUGH DATA"
    assert any("Week 5" in limitation for limitation in result.limitations)
