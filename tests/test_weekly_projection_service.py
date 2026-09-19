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
        # No `sleeper_scoring_settings` -- the pre-W7-fix, still-honest
        # generic fallback path, unchanged.
    )
    kicker = next(row for row in result.rows if row.sleeper_player_id == "11533")
    assert kicker.scoring_context == KDST_SCORING_LABEL
    assert kicker.projected_points == 6.84
    assert kicker.raw_stats == {}  # never presented as NWR-scored raw stats


# NWR Sunday Readiness overnight cycle, Worker 3 (W7 fix) -- governing
# brief regression fixture 8 ("Kicker scoring boundary"): "raw provider
# points 9 with three short field goals returns 9 regardless of custom
# league weights (buggy). Three made 20-29-yard goals at Enginerds' real
# captured 2-points-each should contribute 6 (assuming no other scoring
# events) if custom scoring is properly applied where the raw stats support
# it -- or the gap must be explicitly disclosed if raw stats don't support
# exact mapping." `_ENGINERDS_REAL_KICKER_SCORING` below is Las Vegas
# Enginerds' own real, live-captured kicker scoring map (see the Sunday
# Readiness LEDGER): fgm_0_19/20_29/30_39 = 2.0, fgm_40_49 = 3.0,
# fgm_50p = 4.0, with a real, always-zero redundant fgm_50_59 = 0.0 key.
_ENGINERDS_REAL_KICKER_SCORING = {
    "fgm_0_19": 2.0, "fgm_20_29": 2.0, "fgm_30_39": 2.0, "fgm_40_49": 3.0,
    "fgm_50_59": 0.0, "fgm_50p": 4.0, "xpm": 1.0,
}


def _kicker_raw_projections(*, fgm_20_29: float) -> dict:
    return {
        "11533": {
            "fga": fgm_20_29, "fgm": fgm_20_29,
            "fgm_0_19": 0.0, "fgm_20_29": fgm_20_29, "fgm_30_39": 0.0, "fgm_40_49": 0.0,
            "xpm": 0.0, "xpmiss": 0.0,
            # The real generic provider total this fixture must NOT fall
            # back to once custom scoring genuinely applies -- exactly the
            # brief's own "9 regardless of custom league weights" bug.
            "pts_ppr": 9.0, "gp": 1.0,
        },
    }


def test_regression_fixture_8a_generic_provider_points_ignore_custom_league_weights_documented_fallback() -> None:
    """Buggy-documented (still-honest fallback) behavior: with no real
    league scoring map supplied, raw provider points (9.0) are used
    regardless of the league's own real per-tier weights -- exactly the
    brief's own fixture number. The next test proves the real fix."""
    result = build_weekly_projection_rows(
        raw_projections=_kicker_raw_projections(fgm_20_29=3.0), players=_players(),
        ranking_rows=_ranking_rows(), scoring=ScoringSettings(), season=2026, week=1,
        season_type="regular", league_id="league-1",
    )
    kicker = next(row for row in result.rows if row.sleeper_player_id == "11533")
    assert kicker.scoring_context == KDST_SCORING_LABEL
    assert kicker.projected_points == 9.0


def test_regression_fixture_8b_three_made_20_29_yard_goals_at_enginerds_real_tiers_score_exactly_6() -> None:
    """THE FIX, the brief's own exact number: three made 20-29-yard field
    goals at Las Vegas Enginerds' real captured 2-points-each tier
    contribute exactly 6.0 -- computed from the real raw stat
    (`fgm_20_29: 3.0`) times the league's real per-unit weight (`2.0`),
    never the generic provider `pts_ppr` (9.0) the pre-fix code always
    returned."""
    result = build_weekly_projection_rows(
        raw_projections=_kicker_raw_projections(fgm_20_29=3.0), players=_players(),
        ranking_rows=_ranking_rows(), scoring=ScoringSettings(), season=2026, week=1,
        season_type="regular", league_id="league-1",
        sleeper_scoring_settings=_ENGINERDS_REAL_KICKER_SCORING,
    )
    kicker = next(row for row in result.rows if row.sleeper_player_id == "11533")
    assert kicker.projected_points == 6.0
    # A real, nonzero-weighted category this league scores (fgm_50p = 4.0)
    # has NO raw breakout anywhere in Sleeper's real weekly-projection
    # payload -- disclosed explicitly, never silently dropped or
    # approximated by subtracting the other tiers from the overall `fgm`.
    assert kicker.scoring_context == "NWR_LEAGUE_SCORING_KDST_WEEKLY_PARTIAL"
    assert "fgm_50p" in kicker.unsupported_scoring_categories
    # The real, always-zero redundant fgm_50_59 key is correctly never
    # flagged as a gap (a zero-weighted category needs no raw support).
    assert "fgm_50_59" not in kicker.unsupported_scoring_categories


def test_regression_fixture_8c_fully_supported_kicker_tiers_report_the_exact_not_partial_label() -> None:
    """When every real, nonzero-weighted league scoring category this
    kicker's raw stats could contain IS present (Fantasy Gamers' real
    tiers run the full fgm_0_19...fgm_40_49 + xpm set with no 50+ weight at
    all), the label is the EXACT context, not the partial one -- the
    partial label is reserved for a genuine, disclosed gap, never applied
    when there isn't one."""
    fantasy_gamers_style_scoring = {
        "fgm_0_19": 3.0, "fgm_20_29": 3.0, "fgm_30_39": 3.0, "fgm_40_49": 4.0,
        "xpm": 1.0,
        # No 50+ tier weight configured at all by this league -- correctly
        # never checked/flagged (a real `None`/absent weight, not a real
        # nonzero one).
    }
    result = build_weekly_projection_rows(
        raw_projections=_kicker_raw_projections(fgm_20_29=2.0), players=_players(),
        ranking_rows=_ranking_rows(), scoring=ScoringSettings(), season=2026, week=1,
        season_type="regular", league_id="league-1",
        sleeper_scoring_settings=fantasy_gamers_style_scoring,
    )
    kicker = next(row for row in result.rows if row.sleeper_player_id == "11533")
    assert kicker.projected_points == 6.0  # 2 made * 3.0/each, 0 elsewhere
    assert kicker.scoring_context == "NWR_LEAGUE_SCORING_KDST_WEEKLY"
    assert kicker.unsupported_scoring_categories == ()


def test_regression_fixture_8d_dst_points_allowed_tier_also_scored_league_exactly() -> None:
    """The same real fix applies to DST -- a real points-allowed-tier
    weight times the real raw `pts_allow_*` bucket field, plus real
    sack/int/fum_rec/safe/blk_kick/def_td categories, never the generic
    provider passthrough once the league's real scoring map is supplied."""
    dst_raw = {
        "99998": {
            "sack": 2.0, "int": 1.0, "fum_rec": 0.0, "safe": 0.0, "blk_kick": 0.0, "def_td": 0.0,
            "pts_allow": 10.0, "pts_allow_7_13": 1.0,
            "pts_ppr": 4.0, "gp": 1.0,
        },
    }
    players = {**_players(), "99998": {"full_name": "Cowboys", "position": "DEF", "team": "DAL", "active": True}}
    league_scoring = {
        "sack": 1.0, "int": 2.0, "fum_rec": 2.0, "safe": 2.0, "blk_kick": 2.0, "def_td": 6.0,
        "pts_allow_0": 10.0, "pts_allow_1_6": 7.0, "pts_allow_7_13": 4.0, "pts_allow_14_20": 1.0,
        "pts_allow_21_27": 0.0, "pts_allow_28_34": -1.0, "pts_allow_35p": -4.0,
    }
    result = build_weekly_projection_rows(
        raw_projections=dst_raw, players=players, ranking_rows=_ranking_rows(),
        scoring=ScoringSettings(), season=2026, week=1, season_type="regular",
        league_id="league-1", sleeper_scoring_settings=league_scoring,
    )
    dst = next(row for row in result.rows if row.sleeper_player_id == "99998")
    # sack 2.0*1.0 + int 1.0*2.0 + pts_allow_7_13 1.0*4.0 = 2 + 2 + 4 = 8.0
    assert dst.projected_points == 8.0
    assert dst.scoring_context == "NWR_LEAGUE_SCORING_KDST_WEEKLY"
    assert dst.unsupported_scoring_categories == ()


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
