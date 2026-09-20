"""NWR Waiver Night V1 (Worker 5, Work Unit 11): regression test for two
real, previously-undocumented WAIVER/FAAB decision-trace completeness gaps
found while verifying `redraft_waivers`'s traces against the directive's
required-field list (league, week, roster snapshot, free-agent snapshot,
weekly-projection version, ROS version, recommendation, DROP, FAAB range,
alternatives, trace ID):

1. The WAIVER trace's `recommendation` dict only ever recorded the top ADD
   (`topAdd`/`topAddCanonicalId`) -- never the paired DROP, even though
   `pair_add_drop` (unchanged) already computes it a few lines above the
   trace call. A real WAIVER recommendation is "add X, drop Y"; the ledger
   only ever recorded half of it.
2. `data_versions` on both the WAIVER and FAAB traces only ever carried
   `{"mode": mode}` -- never the real ROS ranking provenance
   (`ranking.projection_sha256`, the same field other call sites in this
   file already treat as the real ranking-version signal). Fixed by adding
   `rosProjectionSha256` to `data_versions` for both traces (purely
   additive; `_content_fingerprint` never hashes `data_versions`, so this
   cannot affect the existing dedup mechanism -- verified below).

Also verifies the FAAB trace now records real bid-range alternatives (it
previously recorded none at all), and that the dedup window still holds
for both WAIVER and FAAB after these changes (an immediate re-call with an
unchanged roster/free-agent state returns the SAME trace id, no duplicate
line).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.in_season_decision_trace_service import load_decision_traces
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_sleeper_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Trace Completeness League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(store, replace(profile, provider="sleeper", provider_league_id="9999"))
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "Trace Completeness League"},
                "owner": {"user_id": "owner-1"},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


# Two real, ranked free agents (matches the repo's bundled governed ranking,
# same real-identity pattern `test_weekly_home_sleeper_fetch_caching.py`
# already uses) so `add_candidates` has more than one row -- needed to
# exercise the FAAB trace's new `alternatives` field.
_ROSTERS = [
    {
        "owner_id": "owner-1",
        "players": ["bench-1"],
        "starters": [],
        "settings": {"waiver_budget_used": 0, "waiver_position": 4},
    },
    {"owner_id": "owner-2", "players": ["rival-1"], "starters": []},
]
_PLAYERS = {
    "bench-1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
    "rival-1": {"full_name": "Justin Jefferson", "position": "WR", "team": "MIN"},
    "fa-1": {"full_name": "Saquon Barkley", "position": "RB", "team": "PHI"},
    "fa-2": {"full_name": "CeeDee Lamb", "position": "WR", "team": "DAL"},
}


def _fake_get_json(self: Any, path: str) -> Any:
    if path == "league/9999/rosters":
        return _ROSTERS
    if path == "players/nfl":
        return _PLAYERS
    if path == "league/9999":
        # NWR Sunday Readiness overnight cycle, Worker 3 (CRITICAL FIRST
        # TASK): real Sleeper `waiver_type` is 2=FAAB, not 1 (see the real
        # evidence on `desktop_facade.py`'s `is_faab_league` assignment) --
        # this fixture wants a real FAAB league for its FAAB-trace
        # assertions below.
        return {"settings": {"waiver_type": 2, "waiver_budget": 100}}
    if path == "state/nfl":
        # NWR Waiver Night V1 (Worker 4, LIVE/SCENARIO budget separation):
        # `redraft_waivers` also now reads the real current NFL week.
        return {"week": 2}
    raise AssertionError(f"unexpected Sleeper GET path in test: {path}")


def test_waiver_trace_now_records_the_paired_drop_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    result = facade.redraft_waivers(mode="REST_OF_SEASON")
    assert result.data["addCandidates"], "fixture must produce real add candidates"

    traces = load_decision_traces(facade.redraft_root, profile_id, tool="WAIVER")
    assert len(traces) == 1
    recommendation = traces[0].recommendation
    assert recommendation["topAdd"]
    # The real bug: before the fix, neither key existed on this dict at
    # all -- a WAIVER trace only ever recorded "what to add", never "what
    # to drop", despite `pair_add_drop` already computing it.
    assert "dropPlayerName" in recommendation
    assert recommendation["dropPlayerName"] == "Christian McCaffrey"
    assert recommendation["dropCanonicalPlayerId"]


def test_waiver_and_faab_traces_now_carry_the_real_ros_ranking_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    facade.redraft_waivers(mode="REST_OF_SEASON")

    waiver_trace = load_decision_traces(facade.redraft_root, profile_id, tool="WAIVER")[0]
    faab_trace = load_decision_traces(facade.redraft_root, profile_id, tool="FAAB")[0]
    # Before the fix, `data_versions` was only ever `{"mode": mode}` on
    # both traces -- no way to tell which admitted projection snapshot a
    # given recommendation was actually computed from.
    assert waiver_trace.data_versions.get("rosProjectionSha256")
    assert faab_trace.data_versions.get("rosProjectionSha256")
    assert waiver_trace.data_versions["rosProjectionSha256"] == faab_trace.data_versions["rosProjectionSha256"]


def test_faab_trace_now_records_real_bid_range_alternatives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    facade.redraft_waivers(mode="REST_OF_SEASON")

    faab_trace = load_decision_traces(facade.redraft_root, profile_id, tool="FAAB")[0]
    # Before the fix, the FAAB trace call never passed `alternatives` at
    # all (defaulted to an empty tuple) -- with 2 real free agents in this
    # fixture, there is now a real second bid-range alternative to record.
    assert len(faab_trace.alternatives) >= 1
    for alt in faab_trace.alternatives:
        assert alt["playerName"]
        assert "bidLowDollars" in alt
        assert "bidHighDollars" in alt


def test_dedup_window_still_holds_for_waiver_and_faab_after_the_fix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The hard boundary protects the dedup MECHANISM itself (unchanged --
    `_content_fingerprint` in `in_season_decision_trace_service.py` was not
    touched); this only verifies it still holds for these two specific call
    sites after their `data_versions`/`recommendation` payloads changed,
    per the directive's explicit ask to re-verify dedup for the newly-fixed
    waiver/FAAB paths."""

    facade, profile_id = _facade_with_sleeper_league(tmp_path)
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    facade.redraft_waivers(mode="REST_OF_SEASON")
    facade.redraft_waivers(mode="REST_OF_SEASON")
    facade.redraft_waivers(mode="REST_OF_SEASON")

    waiver_traces = load_decision_traces(facade.redraft_root, profile_id, tool="WAIVER")
    faab_traces = load_decision_traces(facade.redraft_root, profile_id, tool="FAAB")
    assert len(waiver_traces) == 1, "three quick, identical calls must not create three WAIVER lines"
    assert len(faab_traces) == 1, "three quick, identical calls must not create three FAAB lines"
