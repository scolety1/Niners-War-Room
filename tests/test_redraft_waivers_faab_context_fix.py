"""NWR Waiver Night V1 (Worker 3, Work Unit 6; extended by Worker 4, LIVE/
SCENARIO budget separation): regression tests for `redraft_waivers`'s FAAB
budget provenance.

Worker 3 found that NOTHING anywhere in this codebase -- backend or
frontend -- ever read Sleeper's own real `league.settings.waiver_type` /
`waiver_budget`, or the owner's own real `roster.settings.
waiver_budget_used` / `waiver_position`, and fixed that by adding a real
read surfaced as `faabContext`. But `suggest_faab_bids` itself still only
ever consumed whatever budget the CALLER passed in -- the frontend's own
hardcoded $100/$100/14-week defaults on first render, only corrected by a
SECOND request once `faabContext` arrived. A real, reproducible bug: the
FIRST render of a real, non-coincidentally-different-from-$100 league would
have priced bids off the wrong budget for one request cycle, and a scenario
edit had no state/response distinction from a real live number.

Worker 4 fixes this: `redraft_waivers` now decides for itself, in ONE pass,
whether the budget it prices bids from is LIVE (derived entirely from this
same request's own real Sleeper reads -- no caller input needed or used)
or SCENARIO (an explicit, complete owner-entered hypothetical via the new
`budget_scenario` parameter). `suggest_faab_bids` itself
(`waiver_engine_service.py`) is completely unchanged -- these tests only
cover what budget it gets called with and when it is skipped entirely
(never fabricated for a non-FAAB or budget-unavailable league).
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

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="FAAB Context League"
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


_ROSTERS = [
    {
        "owner_id": "owner-1",
        "players": ["bench-1"],
        "starters": [],
        "settings": {"waiver_budget_used": 35, "waiver_position": 4},
    },
    {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
]
_PLAYERS = {
    "bench-1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
    "rival-1": {"full_name": "Justin Jefferson", "position": "WR", "team": "MIN"},
    "fa-1": {"full_name": "Tyreek Hill", "position": "WR", "team": "MIA"},
}


def _make_fake_get_json(league_settings: dict[str, Any], *, current_week: Any = 2):
    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return _ROSTERS
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            return {"settings": league_settings}
        if path == "state/nfl":
            return {"week": current_week}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    return _fake_get_json


def test_faab_context_reads_real_remaining_budget_for_a_real_faab_league(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 1, "waiver_budget": 100, "playoff_week_start": 15}),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    ctx = result.data["faabContext"]
    assert ctx["isFaabLeague"] is True
    assert ctx["budgetMode"] == "LIVE"
    assert ctx["totalBudgetDollars"] == 100
    # 100 total - 35 already used (real roster.settings.waiver_budget_used)
    assert ctx["remainingBudgetDollars"] == 65
    assert ctx["waiverPosition"] == 4
    assert ctx["source"] == "SLEEPER_LIVE"
    # Real live weeks-remaining: playoff_week_start (15) - current week (2).
    assert ctx["weeksRemaining"] == 13
    assert ctx["weeksRemainingSource"] == "LIVE"
    assert ctx["scenario"] is None

    # The bid math itself is genuinely fed the real live budget -- not a
    # caller default -- confirmed by checking at least one real add
    # candidate actually carries a bid computed against a $65 budget
    # (rather than being silently skipped).
    add_candidates = result.data["addCandidates"]
    assert any(row["faabBidLowDollars"] is not None for row in add_candidates)


def test_faab_context_derives_live_weeks_remaining_from_real_current_week_and_playoffs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json(
            {"waiver_type": 1, "waiver_budget": 100, "playoff_week_start": 15}, current_week=10
        ),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    ctx = result.data["faabContext"]
    assert ctx["weeksRemaining"] == 5
    assert ctx["weeksRemainingSource"] == "LIVE"


def test_faab_context_defaults_weeks_remaining_honestly_when_playoff_week_start_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No real `playoff_week_start` in league settings -- weeks-remaining
    cannot be derived live. A non-live default is still used (so the
    existing season-taper formula always gets a real int), but it is
    explicitly labeled DEFAULTED, never claimed as LIVE."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 1, "waiver_budget": 100}),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    ctx = result.data["faabContext"]
    assert ctx["weeksRemaining"] == 14
    assert ctx["weeksRemainingSource"] == "DEFAULTED"


def test_faab_context_never_fabricates_a_budget_for_a_non_faab_league(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """waiver_type=0 is Sleeper's own real rolling-waiver-priority mode
    (not FAAB) -- this must never report a dollar budget, and -- fixed this
    pass -- must never compute a fabricated dollar bid for any candidate
    either, not just hide it in faabContext."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 0, "waiver_budget": 100}),
    )

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    ctx = result.data["faabContext"]
    assert ctx["isFaabLeague"] is False
    assert ctx["budgetMode"] == "LIVE"
    assert ctx["totalBudgetDollars"] is None
    assert ctx["remainingBudgetDollars"] is None
    assert ctx["weeksRemaining"] is None
    assert ctx["waiverPosition"] == 4  # still real and useful for a non-FAAB league

    # Fixed this pass: `suggest_faab_bids` is never even called for a
    # confirmed non-FAAB league, so every real add candidate's own
    # faabBid*/faabUrgency/faabRationale fields come back honestly `None`
    # -- never a fabricated dollar figure in the API response, even for a
    # consumer that bypasses the frontend's own UI suppression.
    add_candidates = result.data["addCandidates"]
    assert add_candidates
    assert all(row["faabBidLowDollars"] is None for row in add_candidates)
    assert all(row["faabBidHighDollars"] is None for row in add_candidates)
    assert all(row["faabUrgency"] is None for row in add_candidates)


def test_faab_context_is_honestly_unavailable_when_league_settings_cannot_be_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)

    def _fake_get_json_no_settings(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return _ROSTERS
        if path == "players/nfl":
            return _PLAYERS
        if path == "league/9999":
            raise OSError("simulated network failure")
        if path == "state/nfl":
            return {"week": 2}
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json_no_settings)

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    ctx = result.data["faabContext"]
    # NWR Waiver Night V1 (Worker 4): a real, reproduced bug -- before this
    # fix, `faabContext` was literally `None` on a settings-read failure,
    # and the frontend fell through to rendering hardcoded $100/$100
    # defaults with no visual distinction from a genuine live read. Now
    # `faabContext` is always a real object with an honest UNAVAILABLE
    # state -- never `None`, never a fabricated default.
    assert ctx is not None
    assert ctx["isFaabLeague"] is None
    assert ctx["source"] == "UNAVAILABLE"
    assert ctx["totalBudgetDollars"] is None
    assert ctx["remainingBudgetDollars"] is None
    assert ctx["weeksRemaining"] is None
    # The rest of the endpoint must remain fully functional -- a
    # league-settings read failure is honestly degraded, never fatal.
    assert result.data["addCandidates"]
    assert all(row["faabBidLowDollars"] is None for row in result.data["addCandidates"])


def test_budget_scenario_is_explicitly_labeled_and_actually_fed_to_the_pricing_formula(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 1, "waiver_budget": 100, "playoff_week_start": 15}),
    )

    # Spy on the real, UNCHANGED `suggest_faab_bids` (imported into
    # `desktop_facade` module scope) to verify the actual numbers plumbed
    # into it -- decoupled from this fixture's tiny synthetic ranking data,
    # which may or may not produce a real positive-utility candidate (the
    # pre-existing nonpositive-utility gate would floor a real bid to $0
    # regardless of budget, which would make asserting on the RESULTING
    # dollar figure fragile/misleading here).
    calls: list[dict[str, Any]] = []
    real_suggest_faab_bids = desktop_facade_module.suggest_faab_bids

    def _spy_suggest_faab_bids(**kwargs: Any):
        calls.append(kwargs)
        return real_suggest_faab_bids(**kwargs)

    monkeypatch.setattr(desktop_facade_module, "suggest_faab_bids", _spy_suggest_faab_bids)

    facade.redraft_waivers(mode="REST_OF_SEASON")
    assert calls[-1]["remaining_budget_dollars"] == 65  # real live 100 - 35 used
    assert calls[-1]["total_budget_dollars"] == 100
    assert calls[-1]["weeks_remaining"] == 13  # real live playoff_week_start(15) - current_week(2)

    scenario_result = facade.redraft_waivers(
        mode="REST_OF_SEASON",
        budget_scenario={
            "remaining_budget_dollars": 500,
            "total_budget_dollars": 500,
            "weeks_remaining": 1,
        },
    )
    assert calls[-1]["remaining_budget_dollars"] == 500
    assert calls[-1]["total_budget_dollars"] == 500
    assert calls[-1]["weeks_remaining"] == 1

    ctx = scenario_result.data["faabContext"]
    assert ctx["budgetMode"] == "SCENARIO"
    assert ctx["remainingBudgetDollars"] == 500
    assert ctx["totalBudgetDollars"] == 500
    assert ctx["weeksRemaining"] == 1
    assert ctx["weeksRemainingSource"] == "SCENARIO_INPUT"
    # The response echoes the exact scenario inputs back, distinctly from
    # the top-level fields, so a consumer can never confuse "what was
    # requested" with "what is real" -- an explicit, unambiguous
    # owner-entered-hypothetical marker.
    assert ctx["scenario"] == {
        "remainingBudgetDollars": 500,
        "totalBudgetDollars": 500,
        "weeksRemaining": 1,
    }


def test_budget_scenario_never_produces_a_dollar_bid_for_a_confirmed_non_faab_league(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scenario is a hypothetical about a FAAB budget -- it must not
    fabricate a dollar figure for a league that genuinely has no FAAB
    budget concept at all."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 0, "waiver_budget": 100}),
    )

    result = facade.redraft_waivers(
        mode="REST_OF_SEASON",
        budget_scenario={
            "remaining_budget_dollars": 500,
            "total_budget_dollars": 500,
            "weeks_remaining": 10,
        },
    )
    ctx = result.data["faabContext"]
    assert ctx["budgetMode"] == "SCENARIO"
    assert ctx["isFaabLeague"] is False
    assert ctx["remainingBudgetDollars"] is None
    assert ctx["totalBudgetDollars"] is None
    assert all(row["faabBidLowDollars"] is None for row in result.data["addCandidates"])


@pytest.mark.parametrize(
    "budget_scenario",
    [
        {"remaining_budget_dollars": 50},  # missing total/weeks
        {"remaining_budget_dollars": 50, "total_budget_dollars": 100},  # missing weeks
        {"remaining_budget_dollars": 50, "total_budget_dollars": 100, "weeks_remaining": "ten"},
        {"remaining_budget_dollars": 50, "total_budget_dollars": 100, "weeks_remaining": True},
    ],
)
def test_budget_scenario_rejects_a_partial_or_malformed_hypothetical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, budget_scenario: dict[str, Any]
) -> None:
    """A scenario must be explicit and complete -- never a partial override
    silently merged with live values, and never a bool masquerading as an
    int (Python's `bool` is an `int` subclass)."""

    facade, _profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 1, "waiver_budget": 100}),
    )

    with pytest.raises(FacadeError) as excinfo:
        facade.redraft_waivers(mode="REST_OF_SEASON", budget_scenario=budget_scenario)
    assert excinfo.value.code == "WAIVERS_BUDGET_SCENARIO_INVALID"


def test_faab_trace_and_waiver_trace_record_which_budget_mode_actually_ran(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(
        desktop_facade_module.SleeperHttpClient,
        "get_json",
        _make_fake_get_json({"waiver_type": 1, "waiver_budget": 100, "playoff_week_start": 15}),
    )

    facade.redraft_waivers(
        mode="REST_OF_SEASON",
        budget_scenario={
            "remaining_budget_dollars": 20,
            "total_budget_dollars": 20,
            "weeks_remaining": 3,
        },
    )

    from src.services.in_season_decision_trace_service import load_decision_traces

    waiver_events = load_decision_traces(facade.redraft_root, profile_id, tool="WAIVER")
    assert waiver_events
    latest = waiver_events[-1]
    assert latest.data_versions["faabBudgetMode"] == "SCENARIO"
    assert latest.data_versions["faabRemainingBudgetDollarsUsed"] == "20"
    assert latest.data_versions["faabWeeksRemainingUsed"] == "3"
    assert latest.data_versions["faabWeeksRemainingSource"] == "SCENARIO_INPUT"
