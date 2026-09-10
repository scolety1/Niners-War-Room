from __future__ import annotations

import pytest

from src.services.redraft_engine_v1_service import ScoringSettings
from src.services.weekly_projection_service import (
    KDST_SCORING_LABEL,
    NWR_SCORING_LABEL,
    WeeklyProjectionError,
    build_weekly_projection_rows,
    fetch_sleeper_weekly_projections,
    unavailable_weekly_projection_result,
)


class _FakeHttp:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_json(self, path):
        self.calls.append(path)
        return self.payload


def _players():
    return {
        "6904": {"full_name": "Jalen Hurts", "position": "QB", "team": "PHI", "active": True},
        "4034": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF", "active": True},
        "11533": {"full_name": "Brandon Aubrey", "position": "K", "team": "DAL", "active": True},
        "99999": {"full_name": "Bench Warmer", "position": "QB", "team": "SF", "active": True},
    }


def _raw_projections():
    return {
        "6904": {
            "pass_yd": 254.89, "pass_td": 1.67, "pass_int": 0.46,
            "rush_yd": 30.1, "rush_td": 0.52, "fum_lost": 0.17,
            "pts_ppr": 22.44, "gp": 1.0,
        },
        "4034": {
            "rush_yd": 69.33, "rush_td": 0.44, "rec_yd": 33.41,
            "rec": 4.92, "rec_td": 0.3, "fum_lost": 0.09,
            "pts_ppr": 19.58, "gp": 1.0,
        },
        "11533": {"fga": 2.42, "fgm": 2.1, "pts_ppr": 6.84, "gp": 1.0},
        "not-a-dict": "malformed-entry-must-not-crash",
    }


def _ranking_rows():
    return [
        {"playerId": "nwr-hurts", "playerName": "Jalen Hurts", "position": "QB", "team": "PHI"},
        {"playerId": "nwr-cmc", "playerName": "Christian McCaffrey", "position": "RB", "team": "SF"},
    ]


def test_fetch_calls_the_real_sleeper_path_shape() -> None:
    http = _FakeHttp({"1": {"pts_ppr": 1.0}})
    result = fetch_sleeper_weekly_projections(season=2026, week=1, season_type="regular", http=http)
    assert http.calls == ["projections/nfl/regular/2026/1"]
    assert result == {"1": {"pts_ppr": 1.0}}


def test_fetch_rejects_invalid_week_and_season_type() -> None:
    http = _FakeHttp({})
    with pytest.raises(WeeklyProjectionError):
        fetch_sleeper_weekly_projections(season=2026, week=0, http=http)
    with pytest.raises(WeeklyProjectionError):
        fetch_sleeper_weekly_projections(season=2026, week=1, season_type="bogus", http=http)


def test_fetch_wraps_network_failures_without_crashing() -> None:
    class _BoomHttp:
        def get_json(self, path):
            raise OSError("no network")

    with pytest.raises(WeeklyProjectionError):
        fetch_sleeper_weekly_projections(season=2026, week=1, http=_BoomHttp())


def test_skill_position_scored_via_real_league_scoring_engine() -> None:
    scoring = ScoringSettings(reception=1.0)  # full PPR
    result = build_weekly_projection_rows(
        raw_projections=_raw_projections(),
        players=_players(),
        ranking_rows=_ranking_rows(),
        scoring=scoring,
        season=2026,
        week=1,
        season_type="regular",
        league_id="league-1",
    )
    by_id = {row.sleeper_player_id: row for row in result.rows}
    cmc = by_id["4034"]
    assert cmc.scoring_context == NWR_SCORING_LABEL
    assert cmc.canonical_player_id == "nwr-cmc"
    assert cmc.identity_match == "MATCHED"
    # 0.04*0 (no pass) + 69.33*0.1 + 0.44*6 + 33.41*0.1 + 4.92*1.0(rec) + 0.3*6 + (-2)*0.09
    expected = round(69.33 * 0.1 + 0.44 * 6 + 33.41 * 0.1 + 4.92 * 1.0 + 0.3 * 6 + 0.09 * -2, 4)
    assert cmc.projected_points == pytest.approx(expected, abs=0.05)
    assert cmc.raw_stats["rushing_yards"] == 69.33


def test_kdst_uses_sleeper_provider_points_not_a_fabricated_formula() -> None:
    scoring = ScoringSettings()
    result = build_weekly_projection_rows(
        raw_projections=_raw_projections(), players=_players(), ranking_rows=_ranking_rows(),
        scoring=scoring, season=2026, week=1, season_type="regular", league_id="league-1",
    )
    kicker = next(row for row in result.rows if row.sleeper_player_id == "11533")
    assert kicker.scoring_context == KDST_SCORING_LABEL
    assert kicker.projected_points == 6.84
    assert kicker.raw_stats == {}  # never presented as NWR-scored raw stats


def test_unmatched_and_malformed_rows_are_reported_not_dropped_silently() -> None:
    result = build_weekly_projection_rows(
        raw_projections=_raw_projections(), players=_players(), ranking_rows=_ranking_rows(),
        scoring=ScoringSettings(), season=2026, week=1, season_type="regular", league_id="league-1",
    )
    by_id = {row.sleeper_player_id: row for row in result.rows}
    assert by_id["11533"].identity_match == "UNMATCHED"  # kicker not in the tiny ranking fixture
    assert result.matched == 2
    assert result.unmatched >= 1
    assert "not-a-dict" not in by_id  # malformed source entry skipped, not crashed on


def test_ambiguous_identity_reported_when_ranking_pool_has_a_duplicate() -> None:
    ranking = _ranking_rows() + [
        {"playerId": "nwr-hurts-dupe", "playerName": "Jalen Hurts", "position": "QB", "team": "PHI"},
    ]
    result = build_weekly_projection_rows(
        raw_projections=_raw_projections(), players=_players(), ranking_rows=ranking,
        scoring=ScoringSettings(), season=2026, week=1, season_type="regular", league_id="league-1",
    )
    hurts = next(row for row in result.rows if row.sleeper_player_id == "6904")
    assert hurts.identity_match == "AMBIGUOUS"
    assert hurts.canonical_player_id == "sleeper:6904"  # never silently guesses one of the two
    assert result.ambiguous == 1


def test_inactive_and_ineligible_positions_excluded() -> None:
    players = _players()
    players["77777"] = {"full_name": "Retired Guy", "position": "QB", "team": "SF", "active": False}
    raw = _raw_projections()
    raw["77777"] = {"pass_yd": 10, "pts_ppr": 1.0}
    result = build_weekly_projection_rows(
        raw_projections=raw, players=players, ranking_rows=_ranking_rows(),
        scoring=ScoringSettings(), season=2026, week=1, season_type="regular", league_id="league-1",
    )
    assert "77777" not in {row.sleeper_player_id for row in result.rows}


def test_unavailable_result_never_fabricates_rows() -> None:
    result = unavailable_weekly_projection_result(
        season=2026, week=1, season_type="regular", league_id="league-1", error="timeout"
    )
    assert result.source_status == "UNAVAILABLE"
    assert result.rows == ()
    assert result.error == "timeout"
