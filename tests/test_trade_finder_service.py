from __future__ import annotations

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.trade_finder_service import find_win_win_trades


def _row(player_id, name, position, value, rank):
    return RedraftRankingRow(
        rank, rank, player_id, name, position, "TST", value, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-09-01", False,
    )


def _ranking() -> RankingResult:
    rows = [
        # My roster: real RB bench depth beyond FLEX (my-rb4 is pure
        # deadweight, my 4th RB); no WR bench at all.
        _row("my-qb1", "My QB1", "QB", 300, 1),
        _row("my-rb1", "My RB1", "RB", 260, 2),
        _row("my-rb2", "My RB2", "RB", 220, 3),
        _row("my-rb3", "My RB3", "RB", 130, 4),  # fills FLEX
        _row("my-rb4", "My RB4", "RB", 60, 5),  # true deadweight bench
        _row("my-wr1", "My WR1", "WR", 200, 6),
        _row("my-wr2", "My WR2", "WR", 150, 7),
        _row("my-te1", "My TE1", "TE", 80, 8),
        # Opponent roster: real WR bench depth beyond FLEX (opp-wr4 is
        # pure deadweight, their 4th WR); thin at RB (only 2 total).
        _row("opp-qb1", "Opp QB1", "QB", 290, 9),
        _row("opp-rb1", "Opp RB1", "RB", 210, 10),
        _row("opp-rb2", "Opp RB2", "RB", 30, 11),  # their only depth at a thin position
        _row("opp-wr1", "Opp WR1", "WR", 230, 12),
        _row("opp-wr2", "Opp WR2", "WR", 190, 13),
        _row("opp-wr3", "Opp WR3", "WR", 140, 14),  # fills FLEX
        _row("opp-wr4", "Opp WR4", "WR", 50, 15),  # true deadweight bench
        _row("opp-te1", "Opp TE1", "TE", 70, 16),
    ]
    profile = LeagueProfile(
        "fixture-league", "Fixture League", 2026, 10,
        RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1), DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="lg1",
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")


def _my_ids():
    return ["my-qb1", "my-rb1", "my-rb2", "my-rb3", "my-rb4", "my-wr1", "my-wr2", "my-te1"]


def _opp_ids():
    return [
        "opp-qb1", "opp-rb1", "opp-rb2", "opp-wr1", "opp-wr2", "opp-wr3", "opp-wr4", "opp-te1",
    ]


def _names_positions(ids, ranking):
    by_id = {row.player_id: row for row in ranking.rows}
    return {pid: by_id[pid].player_name for pid in ids}, {pid: by_id[pid].position for pid in ids}


def test_finds_a_real_win_win_surplus_swap() -> None:
    ranking = _ranking()
    my_names, my_positions = _names_positions(_my_ids(), ranking)
    opp_names, opp_positions = _names_positions(_opp_ids(), ranking)
    opponents = [
        {
            "rosterId": "2", "teamName": "Rival Team",
            "canonicalIds": _opp_ids(), "names": opp_names, "positions": opp_positions,
        }
    ]
    results = find_win_win_trades(
        my_roster_canonical_ids=_my_ids(), my_player_names=my_names, my_player_positions=my_positions,
        opponents=opponents, profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    assert len(results) > 0
    for candidate in results:
        assert candidate.my_evaluation.net_marginal_utility > 0
        assert candidate.opponent_evaluation.net_marginal_utility > 0
        assert candidate.opponent_team_name == "Rival Team"
    # sorted descending by my own real gain
    gains = [c.my_evaluation.net_marginal_utility for c in results]
    assert gains == sorted(gains, reverse=True)


def test_no_opponents_returns_empty_not_an_error() -> None:
    ranking = _ranking()
    my_names, my_positions = _names_positions(_my_ids(), ranking)
    results = find_win_win_trades(
        my_roster_canonical_ids=_my_ids(), my_player_names=my_names, my_player_positions=my_positions,
        opponents=[], profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    assert results == ()


def test_never_proposes_trading_a_player_for_himself() -> None:
    ranking = _ranking()
    my_names, my_positions = _names_positions(_my_ids(), ranking)
    opponents = [
        {
            "rosterId": "2", "teamName": "Mirror", "canonicalIds": _my_ids(),
            "names": my_names, "positions": my_positions,
        }
    ]
    results = find_win_win_trades(
        my_roster_canonical_ids=_my_ids(), my_player_names=my_names, my_player_positions=my_positions,
        opponents=opponents, profile=ranking.profile, ranking=ranking, manual_assets=[],
    )
    for candidate in results:
        assert candidate.my_give_player_id != candidate.opponent_give_player_id
