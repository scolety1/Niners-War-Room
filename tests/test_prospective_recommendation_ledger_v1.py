"""Prospective Recommendation Ledger V1 (NWR Post-UI Product V1, P1-4).

Extends -- does not replace -- the existing append-only in-season
decision-trace ledger (`in_season_decision_trace_service.py`). This file
covers what P1-3's own worker did not: the two real tool-type strings
(`TRADE_FINDER`, `TRADE_PACKAGE_SEARCH`) that were already being passed to
`record_decision_trace` by `desktop_facade.py` but silently failed because
neither was a member of the old `TOOL_TYPES` set (caught by
`_record_decision_trace_safe`'s best-effort wrapper, so both tools recorded
ZERO real traces in production despite looking fully wired) -- plus the new
History read surface and the append-only owner-action/outcome write paths.

`test_in_season_decision_trace_service.py` already covers the ledger
module's own schema-level contract (this file focuses on facade/HTTP-level
wiring); `test_trade_package_search_facade_wiring.py` /
`test_desktop_application_api.py`'s K/DST test already cover other
facade-level trace call sites -- not duplicated here.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.in_season_decision_trace_service import load_decision_traces
from src.services.redraft_engine_v1_service import load_profile, save_profile
from src.services.redraft_trade_analysis_service import TradeEvaluation
from src.services.trade_finder_service import TradeFinderCandidate
from src.services.trade_package_search_service import TradePackageCandidate, TradePackageSearchResult

REPO_ROOT = Path(__file__).resolve().parents[1]


def _empty_evaluation(net_marginal_utility: float = 1.0) -> TradeEvaluation:
    return TradeEvaluation(
        gives=(), receives=(), ros_value_delta=0.0, net_marginal_utility=net_marginal_utility,
        starting_lineup_value_before=0.0, starting_lineup_value_after=0.0, starting_lineup_value_delta=0.0,
        bench_contingency_value_before=0.0, bench_contingency_value_after=0.0,
        starter_holes_before=(), starter_holes_after=(),
        position_redundancy_before={}, position_redundancy_after={}, risk_flags=(),
    )


def _facade_with_sleeper_league(tmp_path: Path, *, league_name: str = "P1-4 Facade League") -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name=league_name)
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id="9999"))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": league_name},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


def _mock_sleeper_unmatched(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {"owner_id": "owner-1", "players": ["nobody-1"], "starters": []},
                {"owner_id": "owner-2", "players": ["nobody-2"], "starters": []},
            ]
        if path == "league/9999/users":
            return [
                {"user_id": "owner-1", "display_name": "Me"},
                {"user_id": "owner-2", "display_name": "Rival"},
            ]
        if path == "players/nfl":
            return {}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)


# ---------------------------------------------------------------------------
# The real, found bug: TRADE_FINDER / TRADE_PACKAGE_SEARCH silently recorded
# zero traces because neither tool string was in the old TOOL_TYPES set.
# ---------------------------------------------------------------------------


def test_trade_finder_now_records_a_real_decision_trace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper_unmatched(monkeypatch)
    evaluation = _empty_evaluation(net_marginal_utility=3.5)
    fake_candidate = TradeFinderCandidate(
        my_give_player_id="p1", my_give_player_name="My Player",
        opponent_give_player_id="p2", opponent_give_player_name="Their Player",
        opponent_roster_id="2", opponent_team_name="Rival Team",
        my_evaluation=evaluation, opponent_evaluation=evaluation,
    )
    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", lambda **kwargs: (fake_candidate,))

    result = facade.redraft_trade_finder()
    assert result.data["traceId"] is not None  # this used to be None -- the real, found bug

    traces = load_decision_traces(facade.redraft_root, profile_id, tool="TRADE_FINDER")
    assert len(traces) == 1
    trace = traces[0]
    assert trace.trace_id == result.data["traceId"]
    assert trace.recommendation["myGivePlayerId"] == "p1"
    assert trace.status == "RECOMMENDED"
    # NWR Post-UI Product V1 (P1-4): the new leagueSnapshotId/statusVersions
    # fields -- real values, not None/empty by accident.
    assert trace.league_snapshot_id == result.data["leagueSnapshotId"]
    assert trace.league_snapshot_id
    assert isinstance(trace.status_versions, dict)
    assert "playerAvailabilityStatusAuthority" in trace.status_versions


def test_trade_package_search_now_records_a_real_decision_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper_unmatched(monkeypatch)
    evaluation = _empty_evaluation(net_marginal_utility=2.0)
    fake_candidate = TradePackageCandidate(
        opponent_roster_id="2", opponent_team_name="Rival Team", package_shape="1-for-1",
        you_send=("p1",), you_receive=("p2",), you_send_names=("My Player",), you_receive_names=("Their Player",),
        owner_evaluation=evaluation, opponent_evaluation=evaluation,
        why_it_helps_you=("Fills a real starter hole.",), why_it_may_fit_them=("Adds real bench depth.",),
    )
    fake_result = TradePackageSearchResult(
        mode="FIND_WIN_WIN", candidates=(fake_candidate,), packages_evaluated=1,
        opponents_searched=1, truncated=False,
    )
    monkeypatch.setattr(desktop_facade_module, "search_win_win_packages", lambda **kwargs: fake_result)

    result = facade.redraft_trade_package_search(mode="FIND_WIN_WIN")
    assert result.data["traceId"] is not None  # this used to be None -- the real, found bug

    traces = load_decision_traces(facade.redraft_root, profile_id, tool="TRADE_PACKAGE_SEARCH")
    assert len(traces) == 1
    trace = traces[0]
    assert trace.trace_id == result.data["traceId"]
    assert trace.recommendation["packageShape"] == "1-for-1"
    assert trace.league_snapshot_id == result.data["leagueSnapshotId"]
    assert trace.league_snapshot_id


# ---------------------------------------------------------------------------
# History read surface.
# ---------------------------------------------------------------------------


def test_decision_trace_history_is_honest_about_zero_events(tmp_path: Path) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    result = facade.redraft_decision_trace_history()
    assert result.data["totalCount"] == 0
    assert result.data["events"] == []


def test_decision_trace_history_reflects_a_real_recorded_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper_unmatched(monkeypatch)
    evaluation = _empty_evaluation()
    fake_candidate = TradeFinderCandidate(
        my_give_player_id="p1", my_give_player_name="My Player",
        opponent_give_player_id="p2", opponent_give_player_name="Their Player",
        opponent_roster_id="2", opponent_team_name="Rival Team",
        my_evaluation=evaluation, opponent_evaluation=evaluation,
    )
    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", lambda **kwargs: (fake_candidate,))
    facade.redraft_trade_finder()

    history = facade.redraft_decision_trace_history()
    assert history.data["totalCount"] == 1
    event = history.data["events"][0]
    assert event["decisionType"] == "TRADE_FINDER"
    assert event["status"] == "RECOMMENDED"
    assert event["ownerAction"] is None
    assert event["outcome"] is None
    # No calibration/accuracy field of any kind is ever present.
    assert "accuracy" not in event and "calibration" not in event and "wasCorrect" not in event


def test_decision_trace_history_never_leaks_across_leagues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """State-leakage check (this shift's own established paranoia):
    recording a trace under League A must never appear in League B's
    History read, and switching the active profile must scope the read to
    whichever league is ACTUALLY active."""

    facade, profile_a = _facade_with_sleeper_league(tmp_path, league_name="League A")
    _mock_sleeper_unmatched(monkeypatch)
    evaluation = _empty_evaluation()
    fake_candidate = TradeFinderCandidate(
        my_give_player_id="p1", my_give_player_name="My Player",
        opponent_give_player_id="p2", opponent_give_player_name="Their Player",
        opponent_roster_id="2", opponent_team_name="Rival Team",
        my_evaluation=evaluation, opponent_evaluation=evaluation,
    )
    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", lambda **kwargs: (fake_candidate,))
    facade.redraft_trade_finder()  # records exactly one TRADE_FINDER trace under League A

    created_b = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="League B")
    profile_b = created_b.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_b)

    history_b = facade.redraft_decision_trace_history()
    assert history_b.data["totalCount"] == 0  # League B's own ledger is genuinely empty
    assert history_b.data["profileId"] == profile_b

    facade.activate_redraft_profile(profile_a)
    history_a = facade.redraft_decision_trace_history()
    assert history_a.data["totalCount"] == 1  # League A's real event is still there, untouched
    assert history_a.data["profileId"] == profile_a

    # Cross-check directly against the on-disk ledgers too, not just the facade read.
    assert load_decision_traces(facade.redraft_root, profile_b) == ()
    assert len(load_decision_traces(facade.redraft_root, profile_a)) == 1


def test_decision_trace_history_requires_an_active_profile(tmp_path: Path) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_decision_trace_history()
    assert exc_info.value.code == "REDRAFT_PROFILE_REQUIRED"


# ---------------------------------------------------------------------------
# Append-only owner-action / outcome write paths.
# ---------------------------------------------------------------------------


def test_owner_action_write_path_appends_never_mutates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper_unmatched(monkeypatch)
    evaluation = _empty_evaluation()
    fake_candidate = TradeFinderCandidate(
        my_give_player_id="p1", my_give_player_name="My Player",
        opponent_give_player_id="p2", opponent_give_player_name="Their Player",
        opponent_roster_id="2", opponent_team_name="Rival Team",
        my_evaluation=evaluation, opponent_evaluation=evaluation,
    )
    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", lambda **kwargs: (fake_candidate,))
    recorded = facade.redraft_trade_finder()
    trace_id = recorded.data["traceId"]

    ledger_path = facade.redraft_root / "decision_traces" / f"{profile_id}.jsonl"
    lines_before = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines_before) == 1

    updated = facade.redraft_record_decision_trace_owner_action(trace_id=trace_id, action="TRADED_AWAY", notes="did it")
    assert updated.data["status"] == "OWNER_ACTION_RECORDED"
    assert updated.data["ownerAction"] == {"action": "TRADED_AWAY", "notes": "did it"}

    lines_after = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines_after) == 2  # appended, original line untouched
    assert json.loads(lines_after[0])["status"] == "RECOMMENDED"  # original recommendation line unchanged

    history = facade.redraft_decision_trace_history()
    assert history.data["totalCount"] == 1  # folded to the one latest state per traceId, not duplicated
    assert history.data["events"][0]["ownerAction"] == {"action": "TRADED_AWAY", "notes": "did it"}


def test_owner_action_write_path_rejects_unknown_trace_id(tmp_path: Path) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_record_decision_trace_owner_action(trace_id="does-not-exist", action="ADDED")
    assert exc_info.value.code == "DECISION_TRACE_NOT_FOUND"


def test_outcome_write_path_is_real_and_append_only_though_nothing_calls_it_in_production(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The governing directive: 'even if nothing calls it yet -- define the
    contract.' This proves the contract is real and correct, not merely
    declared -- while the app's own production call graph never invokes it
    today (no real 2026-season outcome exists yet)."""

    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    _mock_sleeper_unmatched(monkeypatch)
    evaluation = _empty_evaluation()
    fake_candidate = TradeFinderCandidate(
        my_give_player_id="p1", my_give_player_name="My Player",
        opponent_give_player_id="p2", opponent_give_player_name="Their Player",
        opponent_roster_id="2", opponent_team_name="Rival Team",
        my_evaluation=evaluation, opponent_evaluation=evaluation,
    )
    monkeypatch.setattr(desktop_facade_module, "find_win_win_trades", lambda **kwargs: (fake_candidate,))
    recorded = facade.redraft_trade_finder()
    trace_id = recorded.data["traceId"]

    ledger_path = facade.redraft_root / "decision_traces" / f"{profile_id}.jsonl"
    lines_before = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines_before) == 1
    original_row = json.loads(lines_before[0])
    assert "outcome" not in original_row  # not even a null placeholder on the original recommendation

    updated = facade.redraft_record_decision_trace_outcome(trace_id=trace_id, outcome="WON_MATCHUP", notes="")
    assert updated.data["status"] == "OUTCOME_RECORDED"
    assert updated.data["outcome"] == {"outcome": "WON_MATCHUP", "notes": ""}

    lines_after = [line for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines_after) == 2  # appended, never rewrote the original line
    assert json.loads(lines_after[0]) == original_row  # byte-identical original recommendation line


def test_outcome_write_path_rejects_unknown_trace_id(tmp_path: Path) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_record_decision_trace_outcome(trace_id="does-not-exist", outcome="WON_MATCHUP")
    assert exc_info.value.code == "DECISION_TRACE_NOT_FOUND"
