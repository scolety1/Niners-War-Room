import pytest

from src.services.historical_ranking_bridge_service import (
    KDST_OVERRIDE_FIELD,
    MISSING_PROJECTION_STATS,
    HistoricalRankingBridgeError,
    build_projection_player_from_historical_row,
    build_ranking_result_from_historical_rows,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RosterSettings,
    ScoringSettings,
)


def _profile() -> LeagueProfile:
    return LeagueProfile(
        profile_id="hist-2019", league_name="Historical 2019", season=2019, team_count=4,
        roster=RosterSettings(
            qb=1, rb=1, wr=1, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=2
        ),
        scoring=ScoringSettings(reception=1.0), draft=DraftContext(rounds=4, draft_slot=1),
    )


def _row(player_id, position, **overrides):
    row = {
        "player_id": player_id, "player_name": f"Player {player_id}", "position": position,
        "team": "T1", "season": 2019, "draft_date": "2019-08-25",
        "projection_as_of": "2019-08-20", "adp_as_of": "2019-08-20",
        "platform_adp": 10.0, "status_as_of": "2019-08-25", "scoring_format": "ppr",
        "rookie": False,
    }
    row.update(overrides)
    return row


def _real_rows() -> list[dict]:
    rows = []
    # profile requires team_count(4) * roster_count(1) + 1 = 5 per position
    # (generate_rankings()'s own "insufficient universe" guardrail).
    for position, count in (("QB", 5), ("RB", 5), ("WR", 5), ("TE", 5)):
        for i in range(count):
            rows.append(
                _row(
                    f"{position}-{i}", position,
                    passing_yards=4000.0 if position == "QB" else 0.0,
                    passing_tds=25.0 if position == "QB" else 0.0,
                    rushing_yards=1000.0 if position == "RB" else 0.0,
                    rushing_tds=8.0 if position == "RB" else 0.0,
                    receiving_yards=1000.0 if position in {"WR", "TE"} else 0.0,
                    receptions=80.0 if position in {"WR", "TE"} else 0.0,
                    receiving_tds=7.0 if position in {"WR", "TE"} else 0.0,
                    platform_adp=float(len(rows) + 1),
                )
            )
    for i in range(5):
        rows.append(_row(f"K-{i}", "K", **{KDST_OVERRIDE_FIELD: 120.0}))
    for i in range(5):
        rows.append(_row(f"DST-{i}", "DST", **{KDST_OVERRIDE_FIELD: 110.0}))
    return rows


def test_build_projection_player_returns_none_without_any_stat_components() -> None:
    row = _row("RB-0", "RB")  # no stat fields at all
    assert build_projection_player_from_historical_row(row, source_as_of="2019-08-20") is None


def test_build_projection_player_returns_none_for_kdst_without_an_override() -> None:
    row = _row("K-0", "K")  # no projected_points_override
    assert build_projection_player_from_historical_row(row, source_as_of="2019-08-20") is None


def test_build_projection_player_succeeds_with_real_stat_components() -> None:
    row = _row("RB-0", "RB", rushing_yards=1200.0, rushing_tds=10.0)
    player = build_projection_player_from_historical_row(row, source_as_of="2019-08-20")
    assert player is not None
    assert player.stats["rushing_yards"] == 1200.0
    assert player.source_status == "imported_real_data"


def test_bridge_builds_a_real_ranking_result_via_the_production_engine() -> None:
    result = build_ranking_result_from_historical_rows(
        _real_rows(), _profile(), generated_at_utc="2019-08-25T00:00:00Z",
        source_sha256="deadbeef" * 8,
    )
    assert result.ranking.ready
    assert len(result.ranking.rows) == len(result.included_player_ids)
    # Tiers/confidence/replacement_adjusted_value are computed by the real
    # generate_rankings(), not hand-set -- just confirm they're populated.
    assert all(row.tier >= 1 for row in result.ranking.rows)
    assert all(row.replacement_adjusted_value is not None for row in result.ranking.rows)


def test_bridge_excludes_rather_than_zero_scores_a_player_with_no_stats() -> None:
    rows = _real_rows()
    rows.append(_row("RB-ghost", "RB"))  # no stat components at all
    result = build_ranking_result_from_historical_rows(
        rows, _profile(), generated_at_utc="2019-08-25T00:00:00Z",
        source_sha256="deadbeef" * 8,
    )
    assert "RB-ghost" not in result.included_player_ids
    excluded_ids = {e.player_id for e in result.excluded_players}
    assert "RB-ghost" in excluded_ids
    excluded = next(e for e in result.excluded_players if e.player_id == "RB-ghost")
    assert excluded.value_status == MISSING_PROJECTION_STATS
    # Never present in the ranking output at all -- not scored as 0.
    ranked_ids = {row.player_id for row in result.ranking.rows}
    assert "RB-ghost" not in ranked_ids


def test_bridge_builds_a_real_adp_snapshot_from_platform_adp() -> None:
    result = build_ranking_result_from_historical_rows(
        _real_rows(), _profile(), generated_at_utc="2019-08-25T00:00:00Z",
        source_sha256="deadbeef" * 8,
    )
    assert len(result.adp.entries) > 0
    assert all(entry.overall_adp is not None for entry in result.adp.entries)


def test_bridge_builds_point_in_time_features_for_position_and_team() -> None:
    result = build_ranking_result_from_historical_rows(
        _real_rows(), _profile(), generated_at_utc="2019-08-25T00:00:00Z",
        source_sha256="deadbeef" * 8,
    )
    feature = result.feature_store.lookup_as_of(
        player_id="RB-0", season=2019, feature_name="position", as_of="2019-08-25",
    )
    assert feature.value == "RB"


def test_bridge_refuses_when_no_row_has_any_real_stats() -> None:
    rows = [_row("RB-0", "RB"), _row("WR-0", "WR")]
    with pytest.raises(HistoricalRankingBridgeError):
        build_ranking_result_from_historical_rows(
            rows, _profile(), generated_at_utc="2019-08-25T00:00:00Z",
            source_sha256="deadbeef" * 8,
        )
