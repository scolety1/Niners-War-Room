from __future__ import annotations

import pandas as pd

from src.services.redraft_2026_projection_model_service import (
    MODEL_ID,
    build_current_projection_candidate,
    temporal_backtest,
)


def _history_row(
    player_id: str,
    name: str,
    position: str,
    season: int,
    *,
    games: int = 17,
    passing_yards: int = 0,
    rushing_yards: int = 0,
    receiving_yards: int = 0,
    receptions: int = 0,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_display_name": name,
        "player_name": name,
        "position": position,
        "recent_team": "OLD",
        "season": season,
        "games": games,
        "attempts": 0,
        "completions": 0,
        "passing_yards": passing_yards,
        "passing_tds": 0,
        "passing_interceptions": 0,
        "carries": 0,
        "rushing_yards": rushing_yards,
        "rushing_tds": 0,
        "targets": 0,
        "receptions": receptions,
        "receiving_yards": receiving_yards,
        "receiving_tds": 0,
        "passing_first_downs": 0,
        "rushing_first_downs": 0,
        "receiving_first_downs": 0,
        "punt_return_yards": 0,
        "kickoff_return_yards": 0,
        "special_teams_tds": 0,
        "fumbles_lost_total": 0,
    }


def _player(
    player_id: str,
    name: str,
    position: str,
    *,
    rookie_season: int,
    last_season: int = 2026,
    status: str = "ACT",
) -> dict[str, object]:
    return {
        "gsis_id": player_id,
        "display_name": name,
        "position": position,
        "latest_team": "NEW",
        "status": status,
        "rookie_season": rookie_season,
        "last_season": last_season,
    }


def test_current_candidate_uses_exact_id_and_prior_season_stat_line() -> None:
    history = pd.DataFrame(
        [
            _history_row(
                "00-1",
                "Exact Veteran",
                "WR",
                2025,
                receiving_yards=1234,
                receptions=88,
            ),
            _history_row("00-3", "Old Veteran", "RB", 2024, rushing_yards=700),
        ]
    )
    players = pd.DataFrame(
        [
            _player("00-1", "Exact Veteran", "WR", rookie_season=2022),
            _player("00-2", "Blocked Rookie", "WR", rookie_season=2026),
            _player("00-3", "Old Veteran", "RB", rookie_season=2020),
        ]
    )
    result = build_current_projection_candidate(
        players,
        history,
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"WR": 50.0},
    )
    assert result.projections["player_id"].tolist() == ["00-1"]
    projection = result.projections.iloc[0]
    assert projection["receiving_yards"] == 1234
    assert projection["receptions"] == 88
    assert projection["team"] == "NEW"
    assert projection["source_id"] == MODEL_ID
    assert projection["source_status"] == "GOVERNANCE_PENDING"
    assert set(result.identity["identity_status"]) == {"EXACT"}
    assert set(result.blocked["player_id"]) == {"00-2", "00-3"}


def test_rookie_workload_is_fail_closed_even_when_history_name_collides() -> None:
    history = pd.DataFrame(
        [_history_row("different-id", "Same Name", "WR", 2025, receiving_yards=1500)]
    )
    players = pd.DataFrame([_player("rookie-id", "Same Name", "WR", rookie_season=2026)])
    result = build_current_projection_candidate(
        players,
        history,
        season=2026,
        source_as_of="2026-08-08",
    )
    assert result.projections.empty
    assert result.blocked.iloc[0]["player_id"] == "rookie-id"
    assert "rookie workload" in result.blocked.iloc[0]["reason"]


def test_last_season_one_year_widening_admits_a_real_active_player_diggs_class() -> None:
    """A real, currently active player (status=ACT) whose most recent recorded stat
    line lags one season behind (`last_season == season - 1`) must still be admitted --
    the Diggs-class gap this widening exists to fix."""
    history = pd.DataFrame(
        [_history_row("00-1", "Missed A Season", "WR", 2025, receiving_yards=900, receptions=70)]
    )
    players = pd.DataFrame(
        [_player("00-1", "Missed A Season", "WR", rookie_season=2018, last_season=2025)]
    )
    result = build_current_projection_candidate(
        players,
        history,
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"WR": 50.0},
    )
    assert result.projections["player_id"].tolist() == ["00-1"]


def test_roster_status_cross_check_excludes_a_real_retired_player_rivers_class() -> None:
    """The nflverse player-registry `status` field alone does not reliably flag real
    retirement (a real, verified case: Philip Rivers/Russell Wilson both still show
    status=ACT years after they stopped playing). When a real, gsis_id-keyed
    seasonal-rosters cross-check is supplied and shows the player is no longer
    actually rostered (INA/RET/CUT), the widened slice must exclude them."""
    history = pd.DataFrame(
        [_history_row("00-retired", "Long Retired", "QB", 2020, passing_yards=4000)]
    )
    players = pd.DataFrame(
        [_player("00-retired", "Long Retired", "QB", rookie_season=2004, last_season=2025)]
    )
    result = build_current_projection_candidate(
        players,
        history,
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"QB": 50.0},
        roster_status_by_gsis_id={"00-retired": "INA"},
    )
    assert result.projections.empty
    assert result.blocked.empty
    assert result.identity.empty


def test_roster_status_cross_check_never_touches_the_unwidened_current_season_slice() -> None:
    """The cross-check only removes rows from the newly-widened `last_season ==
    season - 1` slice -- a real player whose `last_season == season` (the original,
    unwidened admission rule) must be unaffected even if a (deliberately wrong, here)
    roster status would otherwise exclude them."""
    history = pd.DataFrame(
        [_history_row("00-current", "Current Season", "RB", 2025, rushing_yards=1000)]
    )
    players = pd.DataFrame(
        [_player("00-current", "Current Season", "RB", rookie_season=2021, last_season=2026)]
    )
    result = build_current_projection_candidate(
        players,
        history,
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"RB": 50.0},
        roster_status_by_gsis_id={"00-current": "INA"},
    )
    assert result.projections["player_id"].tolist() == ["00-current"]


def test_roster_status_cross_check_keeps_players_with_no_roster_snapshot_entry() -> None:
    """Missing coverage in the roster snapshot is not treated as evidence of
    retirement -- a gsis_id absent from `roster_status_by_gsis_id` is kept."""
    history = pd.DataFrame(
        [_history_row("00-uncovered", "Not In Roster Snapshot", "TE", 2025, receiving_yards=500)]
    )
    players = pd.DataFrame(
        [_player("00-uncovered", "Not In Roster Snapshot", "TE", rookie_season=2019, last_season=2025)]
    )
    result = build_current_projection_candidate(
        players,
        history,
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"TE": 50.0},
        roster_status_by_gsis_id={"some-other-id": "INA"},
    )
    assert result.projections["player_id"].tolist() == ["00-uncovered"]


def test_temporal_backtest_uses_prior_season_persistence() -> None:
    history = pd.DataFrame(
        [
            _history_row("qb-1", "QB One", "QB", 2024, passing_yards=4000),
            _history_row("qb-2", "QB Two", "QB", 2024, passing_yards=2000),
            _history_row("qb-1", "QB One", "QB", 2025, passing_yards=3500),
            _history_row("qb-2", "QB Two", "QB", 2025, passing_yards=2500),
        ]
    )
    result = temporal_backtest(history, seasons=[2025])
    row = result.iloc[0]
    assert row["season"] == 2025
    assert row["position"] == "QB"
    assert row["player_count"] == 2
    assert row["model_mae"] == 20.0
    assert row["spearman"] == 1.0
