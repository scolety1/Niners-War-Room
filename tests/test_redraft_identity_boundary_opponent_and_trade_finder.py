"""NWR Post-UI closure pass, bug 2: the canonical-player-id vs. Sleeper-
provider-id identity boundary.

Root cause (Worker 7's original finding, ledger item 10 / open item 3):
the old Find Trades "Open in Analyze" button passed
`TradeFinderCandidate.myGivePlayerId`/`opponentGivePlayerId` (NWR's own
canonical, GSIS-style ids) into `redraftTradeAnalysis`, which requires real
raw Sleeper ids -- an always-fails path
(`TRADE_ANALYSIS_IDENTITY_UNRESOLVED`) for the opponent side.

This file proves the two-part fix at the facade level:
  1. `redraft_opponent_rosters` now attaches a `canonicalPlayerId`/
     `identityStatus` pair to every opponent player row -- the SAME
     identity boundary `redraft_my_roster` already exposes via
     `RedraftMyRosterPlayer.canonicalPlayerId`, computed with the SAME
     `resolve_roster_canonical_ids` matcher (never a new heuristic).
  2. `redraft_trade_finder`'s candidates now ALSO carry the real raw
     Sleeper id for each side (`mySleeperPlayerId`/
     `opponentSleeperPlayerId`), reverse-mapped from the SAME canonical-id
     resolution already computed for that exact roster -- so a caller can
     resolve the correct provider-boundary id instead of assuming
     `myGivePlayerId`/`opponentGivePlayerId` (canonical) are Sleeper ids.

Uses the real, bootstrapped Freeze V7 governed ranking (not a synthetic
ranking double) with real player rows (Aaron Rodgers/PIT, Joe Flacco/CIN)
so the canonical-id resolution being tested is the real identity matcher,
not a stub.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.redraft_engine_v1_service import load_profile, save_profile
from src.services.redraft_trade_analysis_service import TradeEvaluation
from src.services.trade_finder_service import TradeFinderCandidate

REPO_ROOT = Path(__file__).resolve().parents[1]

# Real rows from the bundled Freeze V7 governed seed (GOVERNED_COMBINED_564_
# PROJECTION_SNAPSHOT.csv) -- real canonical ids, names, positions, teams.
_RODGERS_CANONICAL_ID = "00-0023459"
_FLACCO_CANONICAL_ID = "00-0026158"


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()  # installs the real governed Freeze V7 seed into this fresh store
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Identity Boundary League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id="9999"))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps({"league": {"league_id": "9999"}, "owner": {"user_id": "owner-1"}}),
        encoding="utf-8",
    )
    return facade, profile_id


_PLAYERS_CATALOG = {
    "sleeper-rodgers": {"full_name": "Aaron Rodgers", "position": "QB", "team": "PIT"},
    "sleeper-flacco": {"full_name": "Joe Flacco", "position": "QB", "team": "CIN"},
    # A deliberately unmatched Sleeper id -- no catalog entry at all, so
    # `resolve_roster_canonical_ids` can never match it (an honest
    # unmatched-identity case, not a crash).
}


def _mock_sleeper(monkeypatch: pytest.MonkeyPatch, *, my_players: list[str], opp_players: list[str]) -> None:
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {"owner_id": "owner-1", "roster_id": "1", "players": my_players, "starters": []},
                {"owner_id": "owner-2", "roster_id": "2", "players": opp_players, "starters": []},
            ]
        if path == "league/9999/users":
            return [
                {"user_id": "owner-1", "display_name": "Me"},
                {"user_id": "owner-2", "display_name": "Rival"},
            ]
        if path == "players/nfl":
            return _PLAYERS_CATALOG
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)


# ---------------------------------------------------------------------------
# 1. `redraft_opponent_rosters` -- the new canonicalPlayerId/identityStatus
#    fields, mirroring `RedraftMyRosterPlayer`.
# ---------------------------------------------------------------------------


def test_opponent_rosters_attaches_canonical_id_for_a_matched_player(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch, my_players=["sleeper-rodgers"], opp_players=["sleeper-flacco"])

    result = facade.redraft_opponent_rosters().data
    assert result["rankingWarning"] == ""
    opponent = result["opponents"][0]
    row = opponent["players"][0]
    assert row["sleeperPlayerId"] == "sleeper-flacco"
    assert row["canonicalPlayerId"] == _FLACCO_CANONICAL_ID
    assert row["identityStatus"] == "MATCHED"
    assert row["playerName"] == "Joe Flacco"


def test_opponent_rosters_reports_an_unmatched_player_honestly_not_as_a_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch, my_players=["sleeper-rodgers"], opp_players=["nobody-unmatched"])

    result = facade.redraft_opponent_rosters().data
    opponent = result["opponents"][0]
    # `nobody-unmatched` has no catalog entry at all -- `sleeper_opponent_
    # rosters` reports it under `unresolvedSleeperPlayerIds`, so `players`
    # is legitimately empty here; the important assertion is that this
    # degrades honestly (no crash, no fabricated row) rather than raising.
    assert opponent["players"] == []
    assert opponent["unresolvedSleeperPlayerIds"] == ["nobody-unmatched"]


def test_opponent_rosters_reports_unmatched_identity_for_a_catalog_hit_with_no_ranking_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A player who exists in the Sleeper catalog (so `sleeper_opponent_
    rosters` renders a real row for them) but cannot be identity-matched
    into NWR's governed ranking pool (e.g. a name/position/team the
    ranking doesn't carry) must be reported as `UNMATCHED_IDENTITY` with a
    `null` canonical id -- never a crash, never a silently wrong id."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    catalog_with_unranked_player = dict(_PLAYERS_CATALOG)
    catalog_with_unranked_player["sleeper-nobody-in-ranking"] = {
        "full_name": "Nobody In Ranking", "position": "WR", "team": "ZZZ",
    }

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {"owner_id": "owner-1", "players": ["sleeper-rodgers"], "starters": []},
                {"owner_id": "owner-2", "players": ["sleeper-nobody-in-ranking"], "starters": []},
            ]
        if path == "league/9999/users":
            return [
                {"user_id": "owner-1", "display_name": "Me"},
                {"user_id": "owner-2", "display_name": "Rival"},
            ]
        if path == "players/nfl":
            return catalog_with_unranked_player
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    result = facade.redraft_opponent_rosters().data
    row = result["opponents"][0]["players"][0]
    assert row["sleeperPlayerId"] == "sleeper-nobody-in-ranking"
    assert row["canonicalPlayerId"] is None
    assert row["identityStatus"] == "UNMATCHED_IDENTITY"


# ---------------------------------------------------------------------------
# 2. `redraft_trade_finder` -- the new `mySleeperPlayerId`/
#    `opponentSleeperPlayerId` fields, the exact identity-boundary fix for
#    the old "Open in Analyze" button.
# ---------------------------------------------------------------------------


def test_trade_finder_candidate_carries_the_real_sleeper_id_alongside_the_canonical_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch, my_players=["sleeper-rodgers"], opp_players=["sleeper-flacco"])

    fake_evaluation = TradeEvaluation(
        gives=(), receives=(), ros_value_delta=1.0, net_marginal_utility=1.0,
        starting_lineup_value_before=0.0, starting_lineup_value_after=0.0,
        starting_lineup_value_delta=0.0,
        bench_contingency_value_before=0.0, bench_contingency_value_after=0.0,
        starter_holes_before=(), starter_holes_after=(),
        position_redundancy_before={}, position_redundancy_after={},
        risk_flags=(),
    )
    fake_candidate = TradeFinderCandidate(
        my_give_player_id=_RODGERS_CANONICAL_ID,
        my_give_player_name="Aaron Rodgers",
        opponent_give_player_id=_FLACCO_CANONICAL_ID,
        opponent_give_player_name="Joe Flacco",
        opponent_roster_id="2",  # sleeper_opponent_rosters assigns roster_id from the mocked roster's own position
        opponent_team_name="Rival",
        my_evaluation=fake_evaluation,
        opponent_evaluation=fake_evaluation,
    )

    def _fake_find_win_win_trades(**kwargs: Any) -> list[TradeFinderCandidate]:
        # Confirms the real reverse-lookup wiring rather than the search
        # algorithm itself (covered separately in
        # test_trade_finder_service.py) -- this test targets exactly the
        # id-plumbing fix in desktop_facade.py.
        return [fake_candidate]

    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", _fake_find_win_win_trades)

    result = facade.redraft_trade_finder().data
    assert len(result["candidates"]) == 1
    candidate = result["candidates"][0]
    assert candidate["myGivePlayerId"] == _RODGERS_CANONICAL_ID
    assert candidate["mySleeperPlayerId"] == "sleeper-rodgers"
    assert candidate["opponentGivePlayerId"] == _FLACCO_CANONICAL_ID
    assert candidate["opponentSleeperPlayerId"] == "sleeper-flacco"
    # The exact original bug shape: the canonical and Sleeper ids for the
    # same player must never collapse to the same value here (this repo's
    # real ids are drawn from disjoint id spaces -- GSIS-style vs. Sleeper
    # numeric/opaque ids).
    assert candidate["myGivePlayerId"] != candidate["mySleeperPlayerId"]
    assert candidate["opponentGivePlayerId"] != candidate["opponentSleeperPlayerId"]


def test_trade_finder_sleeper_id_end_to_end_flows_into_a_real_trade_analysis_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Full canonical-id action flow, end to end: the real Sleeper ids
    `redraft_trade_finder` now returns actually work when handed to
    `redraft_trade_analysis` (the real provider boundary) -- and the OLD,
    broken shape (passing the canonical ids as if they were Sleeper ids,
    exactly what the pre-fix "Open in Analyze" button did) is confirmed to
    still fail the same honest way, proving the fix actually matters."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch, my_players=["sleeper-rodgers"], opp_players=["sleeper-flacco"])

    fake_evaluation = TradeEvaluation(
        gives=(), receives=(), ros_value_delta=1.0, net_marginal_utility=1.0,
        starting_lineup_value_before=0.0, starting_lineup_value_after=0.0,
        starting_lineup_value_delta=0.0,
        bench_contingency_value_before=0.0, bench_contingency_value_after=0.0,
        starter_holes_before=(), starter_holes_after=(),
        position_redundancy_before={}, position_redundancy_after={},
        risk_flags=(),
    )
    fake_candidate = TradeFinderCandidate(
        my_give_player_id=_RODGERS_CANONICAL_ID,
        my_give_player_name="Aaron Rodgers",
        opponent_give_player_id=_FLACCO_CANONICAL_ID,
        opponent_give_player_name="Joe Flacco",
        opponent_roster_id="2",
        opponent_team_name="Rival",
        my_evaluation=fake_evaluation,
        opponent_evaluation=fake_evaluation,
    )
    monkeypatch.setattr(
        desktop_facade_module, "find_win_win_trades", lambda **kwargs: [fake_candidate]
    )

    candidate = facade.redraft_trade_finder().data["candidates"][0]

    # FIXED path: the real raw Sleeper ids this pass added.
    fixed_result = facade.redraft_trade_analysis(
        gives_sleeper_player_ids=[candidate["mySleeperPlayerId"]],
        receives_sleeper_player_ids=[candidate["opponentSleeperPlayerId"]],
    )
    assert fixed_result.data["gives"][0]["playerName"] == "Aaron Rodgers"
    assert fixed_result.data["receives"][0]["playerName"] == "Joe Flacco"

    # OLD BUGGY shape: the canonical ids, exactly what the pre-fix "Open in
    # Analyze" button sent as if they were Sleeper ids -- confirmed to
    # still fail honestly (never silently "work" by accident).
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_trade_analysis(
            gives_sleeper_player_ids=[candidate["myGivePlayerId"]],
            receives_sleeper_player_ids=[candidate["opponentGivePlayerId"]],
        )
    assert exc_info.value.code == "TRADE_ANALYSIS_IDENTITY_UNRESOLVED"


def test_trade_finder_stale_or_wrong_sleeper_id_is_caught_not_silently_wrong(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale/wrong provider id (one that no longer resolves to any
    rostered Sleeper player) must be caught by `redraft_trade_analysis`'s
    own existing identity check -- never silently treated as a valid
    trade."""
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper(monkeypatch, my_players=["sleeper-rodgers"], opp_players=["sleeper-flacco"])

    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_trade_analysis(
            gives_sleeper_player_ids=["sleeper-rodgers"],
            receives_sleeper_player_ids=["sleeper-stale-id-not-on-any-roster"],
        )
    assert exc_info.value.code == "TRADE_ANALYSIS_IDENTITY_UNRESOLVED"
