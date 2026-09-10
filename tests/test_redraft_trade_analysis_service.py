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
