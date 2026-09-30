from __future__ import annotations

import pytest

from src.services.current_player_status_overrides_service import StatusOverride
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.redraft_trade_analysis_service import TradeAnalysisError, evaluate_trade
from src.services.waiver_engine_service import (
    resolve_full_roster_with_unranked_occupants,
    resolve_roster_canonical_ids,
)


def _row(player_id, name, position, value, rank):
    return RedraftRankingRow(
        rank, rank, player_id, name, position, "TST", value, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-09-01", False,
    )


def _ranking() -> RankingResult:
    rows = [
        _row("qb1", "QB One", "QB", 300, 1),
        _row("rb1", "RB One", "RB", 250, 2),
        _row("rb2", "RB Two", "RB", 150, 3),
        _row("rb3", "RB Three", "RB", 60, 4),
        _row("wr1", "WR One", "WR", 240, 5),
        _row("wr2", "WR Two", "WR", 100, 6),
        _row("te1", "TE One", "TE", 90, 7),
        _row("wr-star", "WR Star", "WR", 320, 8),  # trade target -- big upgrade
    ]
    profile = LeagueProfile(
        "fixture-league", "Fixture League", 2026, 10,
        RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1), DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="lg1",
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")


def _roster_ids():
    return ["qb1", "rb1", "rb2", "rb3", "wr1", "wr2", "te1"]


def test_upgrade_trade_shows_positive_ros_delta_and_real_marginal_utility() -> None:
    ranking = _ranking()
    result = evaluate_trade(
        roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    assert result.ros_value_delta == pytest.approx(320.0 - 60.0)
    assert result.net_marginal_utility is not None
    received = result.receives[0]
    assert received.player_id == "wr-star"
    assert received.becomes_starter is True  # WR Star (320) clearly beats a current WR starter


def test_cannot_give_a_player_not_on_roster() -> None:
    ranking = _ranking()
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=_roster_ids(), gives_ids=["not-mine"], receives_ids=["wr-star"],
            profile=ranking.profile, ranking=ranking, manual_assets=[],
        )


def test_cannot_receive_a_player_already_rostered() -> None:
    ranking = _ranking()
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["wr1"],
            profile=ranking.profile, ranking=ranking, manual_assets=[],
        )


def test_same_asset_cannot_be_both_given_and_received() -> None:
    """Full Trust Hardening V1 (Worker 3): `evaluate_trade` already contains
    this exact validation (line ~145's `overlap = set(gives) & set(receives)`)
    but it had zero test coverage until now -- a permanent regression guard,
    not a new fix."""
    ranking = _ranking()
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["rb3"],
            profile=ranking.profile, ranking=ranking, manual_assets=[],
        )


def test_evaluate_trade_is_deterministic() -> None:
    """Full Trust Hardening V1 (Worker 3): identical inputs must produce an
    identical evaluation -- a pure function over its real inputs, no hidden
    global/cached state."""
    ranking = _ranking()
    kwargs = dict(
        roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    first = evaluate_trade(**kwargs)
    second = evaluate_trade(**kwargs)
    assert first == second


def test_empty_trade_rejected() -> None:
    ranking = _ranking()
    with pytest.raises(TradeAnalysisError):
        evaluate_trade(
            roster_before_ids=_roster_ids(), gives_ids=[], receives_ids=[],
            profile=ranking.profile, ranking=ranking, manual_assets=[],
        )


def test_status_override_produces_a_real_risk_flag_not_a_second_injury_system() -> None:
    ranking = _ranking()
    overrides = (
        StatusOverride(
            player_id="wr-star", player_name="WR Star", kind="SEASON_OUT", reason="Achilles",
            effective_date="2026-09-01", verified_at_utc="2026-09-01T00:00:00Z", sources=("test",),
        ),
    )
    result = evaluate_trade(
        roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[], status_overrides=overrides,
    )
    assert any("SEASON_OUT" in flag for flag in result.risk_flags)


def test_starting_lineup_value_strictly_improves_on_a_real_upgrade() -> None:
    ranking = _ranking()
    result = evaluate_trade(
        roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    assert result.starting_lineup_value_after > result.starting_lineup_value_before
    assert result.starting_lineup_value_delta == pytest.approx(
        result.starting_lineup_value_after - result.starting_lineup_value_before
    )
    # position_redundancy is a real, reused report field -- present for both sides even
    # when this specific swap doesn't move it (FLEX absorbs the traded-away RB depth).
    assert set(result.position_redundancy_before) == {"QB", "RB", "WR", "TE"}
    assert set(result.position_redundancy_after) == {"QB", "RB", "WR", "TE"}


def test_championship_equity_honestly_disclosed_as_not_evaluated() -> None:
    ranking = _ranking()
    result = evaluate_trade(
        roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    assert "not evaluated" in result.championship_equity_note
    assert "live standings store" in result.championship_equity_note


def test_fully_ranked_trade_reports_ros_value_delta_as_fully_known() -> None:
    # Regression guard: a real, fully-ranked trade must keep reporting
    # ros_value_delta_all_known True on both the evaluation and every
    # individual impact -- the new disclosure fields must never make a
    # normal, fully-known trade look uncertain.
    ranking = _ranking()
    result = evaluate_trade(
        roster_before_ids=_roster_ids(), gives_ids=["rb3"], receives_ids=["wr-star"],
        profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    assert result.ros_value_delta_all_known is True
    assert all(impact.ros_replacement_value_known for impact in result.gives)
    assert all(impact.ros_replacement_value_known for impact in result.receives)


def test_unranked_manual_asset_ros_value_is_honestly_unknown_not_silently_zero() -> None:
    # Full Trust Hardening V1 (Worker 2): reproduces the exact undisclosed
    # gap Worker 1 flagged at redraft_trade_analysis_service.py:149 -- a
    # K/DST or otherwise-unmodeled manual asset has no real
    # replacement_adjusted_value (_asset_pool sets it to None, "NOT
    # MODELED"). Before this fix, ros_replacement_value silently collapsed
    # to 0.0 with no way to tell "unknown" from "genuinely worth zero,"
    # which could fabricate a confident-looking rosValueDelta arbitrage
    # number. Now the value stays 0.0 for arithmetic convenience but is
    # explicitly flagged unknown on both the impact and the evaluation.
    ranking = _ranking()
    manual_assets = [
        {
            "player_id": "dst-unmodeled",
            "player_name": "Unmodeled DST",
            "position": "DST",
            "team": "TST",
        }
    ]
    result = evaluate_trade(
        roster_before_ids=[*_roster_ids(), "dst-unmodeled"],
        gives_ids=["dst-unmodeled"],
        receives_ids=["wr-star"],
        profile=ranking.profile,
        ranking=ranking,
        manual_assets=manual_assets,
    )
    given = result.gives[0]
    assert given.player_id == "dst-unmodeled"
    # Arithmetic default stays 0.0 for the delta computation...
    assert given.ros_replacement_value == 0.0
    # ...but it must be explicitly disclosed as unknown, never a bare zero.
    assert given.ros_replacement_value_known is False
    # The received (fully-ranked) side is unaffected.
    assert result.receives[0].ros_replacement_value_known is True
    # And the top-level delta must be flagged as partial/not-fully-known,
    # since it silently summed a real known value against an unknown one.
    assert result.ros_value_delta_all_known is False


def test_real_kdst_roster_occupants_are_reported_filled_not_holes_before_and_after_trade() -> None:
    """NWR Dogfood Rebuild V1, item 4 -- real, owner-reported P0 bug.

    Live-reproduced against the real Fantasy Gamers Sleeper league
    (2026-09-29): the owner has a real, real-catalog-resolvable kicker
    and team defense rostered, yet Trade Analysis reported
    `starterHolesBefore`/`starterHolesAfter` as `["K 0/1", "DST 0/1"]`
    for a trade that never touched either position. Root cause: the
    facade fed `resolve_roster_canonical_ids`'s `canonical_player_ids`
    straight into `evaluate_trade` as `roster_before_ids` --  and that
    resolver's own `ranking_by_identity` is sourced only from the
    governed ranking, which structurally never has K/DST rows (NWR has
    no ranked model for them), so a real K/DST occupant is ALWAYS
    dropped, making a filled slot look empty.

    This test builds a realistic roster (a real kicker + a real team
    defense resolved from a Sleeper-shaped catalog, exactly like the live
    reproduction) the same way `desktop_facade.redraft_trade_analysis`
    now does -- `resolve_roster_canonical_ids` followed by the real fix,
    `resolve_full_roster_with_unranked_occupants` -- and proves the K/DST
    slots are reported FILLED, never a hole, both BEFORE and AFTER a
    trade that only swaps two skill-position players.
    """

    ranking = _ranking()
    ranking_rows = [
        {
            "playerId": row.player_id, "playerName": row.player_name,
            "position": row.position, "team": row.team,
        }
        for row in ranking.rows
    ]
    # A Sleeper-shaped players/nfl catalog entry per rostered skill player,
    # plus a real kicker and a real team defense -- neither has (or ever
    # will have) a row in `ranking_rows`, matching NWR's real, permanent
    # "K/DST are always manual" scope boundary.
    players_catalog = {
        "s-qb1": {"full_name": "QB One", "position": "QB", "team": "TST"},
        "s-rb1": {"full_name": "RB One", "position": "RB", "team": "TST"},
        "s-rb2": {"full_name": "RB Two", "position": "RB", "team": "TST"},
        "s-rb3": {"full_name": "RB Three", "position": "RB", "team": "TST"},
        "s-wr1": {"full_name": "WR One", "position": "WR", "team": "TST"},
        "s-wr2": {"full_name": "WR Two", "position": "WR", "team": "TST"},
        "s-te1": {"full_name": "TE One", "position": "TE", "team": "TST"},
        "3451": {"full_name": "Ka'imi Fairbairn", "position": "K", "team": "HOU"},
        "NE": {"position": "DEF", "team": "NE"},
    }
    resolved = resolve_roster_canonical_ids(
        roster_sleeper_player_ids=list(players_catalog),
        players_catalog=players_catalog, ranking_rows=ranking_rows,
    )
    # Confirm the bug's real precondition: the resolver drops the K/DST.
    assert set(resolved.unmatched_sleeper_player_ids) == {"3451", "NE"}
    assert "qb1" in resolved.canonical_player_ids

    roster_before_ids, extra_manual_assets = resolve_full_roster_with_unranked_occupants(
        resolved=resolved, players_catalog=players_catalog, manual_assets=(),
    )

    result = evaluate_trade(
        roster_before_ids=roster_before_ids,
        gives_ids=["rb3"],
        receives_ids=["wr-star"],
        profile=ranking.profile,
        ranking=ranking,
        manual_assets=extra_manual_assets,
    )
    # The real correctness assertion: neither K nor DST is reported as a
    # hole, before or after a trade that never touches either position.
    assert result.starter_holes_before == ()
    assert result.starter_holes_after == ()
