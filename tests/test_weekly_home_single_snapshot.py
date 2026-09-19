"""Weekly Home single-LeagueSnapshot test (NWR pre-UI architecture CLOSURE
pass, 2026-09-10, directive section 3).

Before this pass, `redraft_weekly_home_actions` built its action list from
an internal `self.redraft_weekly_lineup(...)` call but discarded that
sub-call's own `leagueSnapshotId`/full payload -- the frontend then made
TWO MORE independent facade calls (`redraftWeeklyLineup`, `redraftFree
Agents`) to render the rest of Weekly Home, each performing its own live
Sleeper roster read with no snapshot value threaded/asserted across them
(`PRODUCT_ARCHITECTURE.md` invariant F, "NOT ARCHITECTURALLY GUARANTEED").

This closure pass makes `redraft_weekly_home_actions` embed the SAME
lineup/free-agents sub-payloads it already computed internally, and
surface ONE top-level `leagueSnapshotId` (the lineup sub-call's own real
id). This test proves that wiring directly: it monkeypatches the six
internal sub-calls (`redraft_weekly_lineup`, `redraft_waivers`,
`redraft_trade_finder`, `redraft_kdst_streamer`, `redraft_free_agents`)
at the facade-instance level with realistic fixtures/failures, so it
exercises the REAL `redraft_weekly_home_actions` code path -- the exact
production method this pass edited -- without needing the full live
Sleeper/weekly-projection mock chain a true end-to-end run would require
(the same disclosed environment constraint documented in `tests/
test_desktop_facade_architecture_wiring.py`'s module docstring: a fully
live round trip through the governed ranking is blocked in this worktree
by the expired projection-seed governance receipt, unrelated to this
pass).
"""

from __future__ import annotations

from pathlib import Path

from src.application.desktop_facade import DesktopBackendFacade, FacadeError, FacadePayload

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fresh_local_facade(tmp_path: Path):
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Weekly Home Snapshot League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    return facade, profile_id


_FAKE_SNAPSHOT_ID = "snap-fixture-0001"


def test_weekly_home_actions_embeds_the_same_lineup_and_free_agent_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    facade, _profile_id = _fresh_local_facade(tmp_path)

    lineup_payload = {
        "season": 2026, "week": 1, "leagueId": "9999",
        "leagueSnapshotId": _FAKE_SNAPSHOT_ID,
        "traceId": "trace-lineup-1",
        "providerHealth": {"freshness": "LIVE", "issues": []},
        "projectedTotal": 111.5,
        "starters": [], "bench": [], "excluded": [], "swaps": [],
        "writeBehavior": "NO_SLEEPER_WRITES",
    }
    free_agents_payload = {
        "leagueId": "9999",
        "freeAgents": [{"sleeperPlayerId": "fa-1", "playerName": "Free Agent One"}],
        "rankingWarning": "",
        "writeBehavior": "NO_SLEEPER_WRITES",
    }

    monkeypatch.setattr(
        facade, "redraft_weekly_lineup", lambda *, week: FacadePayload(data=lineup_payload)
    )
    monkeypatch.setattr(
        facade, "redraft_free_agents", lambda: FacadePayload(data=free_agents_payload)
    )

    def _unavailable(*args, **kwargs):
        raise FacadeError("SUB_TOOL_UNAVAILABLE", "not configured in this fixture", status=409)

    monkeypatch.setattr(facade, "redraft_waivers", _unavailable)
    monkeypatch.setattr(facade, "redraft_trade_finder", _unavailable)
    monkeypatch.setattr(facade, "redraft_kdst_streamer", _unavailable)

    result = facade.redraft_weekly_home_actions(week=1).data

    # ONE snapshot id, sourced from the exact same sub-call that built the
    # embedded lineup payload -- not independently recomputed.
    assert result["leagueSnapshotId"] == _FAKE_SNAPSHOT_ID
    assert result["lineup"]["leagueSnapshotId"] == result["leagueSnapshotId"]
    assert result["lineup"] == lineup_payload
    assert result["freeAgents"] == free_agents_payload

    # The three intentionally-failing sub-tools are disclosed, not silently
    # dropped -- the same honest degradation contract this endpoint already
    # had before this pass.
    unavailable_sections = {row["section"] for row in result["unavailableSections"]}
    assert unavailable_sections == {"WAIVER", "TRADE", "STREAMER"}


def test_weekly_home_actions_snapshot_id_is_null_when_lineup_itself_is_unavailable(
    tmp_path: Path, monkeypatch
) -> None:
    """No fabricated snapshot id when the one real sub-call that produces
    it fails -- an honest `null`, surfaced via `unavailableSections`."""
    facade, _profile_id = _fresh_local_facade(tmp_path)

    def _unavailable(*args, **kwargs):
        raise FacadeError("SUB_TOOL_UNAVAILABLE", "not configured in this fixture", status=409)

    monkeypatch.setattr(facade, "redraft_weekly_lineup", _unavailable)
    monkeypatch.setattr(facade, "redraft_waivers", _unavailable)
    monkeypatch.setattr(facade, "redraft_trade_finder", _unavailable)
    monkeypatch.setattr(facade, "redraft_kdst_streamer", _unavailable)
    monkeypatch.setattr(
        facade, "redraft_free_agents",
        lambda: FacadePayload(data={"leagueId": "9999", "freeAgents": [], "rankingWarning": "", "writeBehavior": "NO_SLEEPER_WRITES"}),
    )

    result = facade.redraft_weekly_home_actions(week=1).data
    assert result["leagueSnapshotId"] is None
    assert result["lineup"] is None
    assert "START_SIT" in {row["section"] for row in result["unavailableSections"]}


# --- NWR Post-UI closure pass (bug 1): permanent regression fixture ---------
#
# `redraft_kdst_streamer`'s real, live response shape returns `positions` as
# a FLAT LIST of decision-envelope-style rows (each row self-identifying its
# own "position" key), not a `{"K": [...], "DST": [...]}` dict.
# `redraft_weekly_home_actions` used to assume the old dict shape and called
# `.items()` on this list, raising an uncaught `AttributeError` that escaped
# every `except FacadeError` handler in the method and surfaced as a bare
# HTTP 500 on a real Sleeper-imported active roster (Worker 3's original
# P0-3 finding, reconfirmed unchanged through Worker 11's final shift
# consolidation pass). This fixture reproduces the EXACT real shape
# `redraft_kdst_streamer` actually returns (verified against its own
# `streamer_actions()`/`positions = [*positions["K"], *positions["DST"]]`
# implementation), not a synthetic simplification.
_REAL_SHAPE_KDST_PAYLOAD = {
    "authority": "fantasypros",
    "week": 1,
    "leagueId": "9999",
    "traceIds": [{"position": "K", "traceId": "trace-k-1"}, {"position": "DST", "traceId": "trace-dst-1"}],
    "leagueSnapshotId": _FAKE_SNAPSHOT_ID,
    # NWR Sunday Readiness overnight cycle, Worker 3 (W6 fix): `redraft_
    # weekly_home_actions`'s own STREAMER action loop now reads
    # `decisionEnvelopes[].decisionEnvelope.primaryRecommendation` (the
    # SAME already-corrected primary recommendation `redraft_kdst_
    # streamer` itself computes) instead of independently re-deriving
    # "first ADD row" from the flat `positions` list below -- this fixture
    # now carries the real shape that call site actually consumes.
    "decisionEnvelopes": [
        {
            "position": "K",
            "decisionEnvelope": {
                "primaryRecommendation": {
                    "playerName": "Real Kicker One", "position": "K", "team": "SF", "ecr": 3.0,
                    "tier": 1, "week": 1, "authority": "fantasypros", "rosterStatus": "AVAILABLE",
                    "recommendation": "ADD",
                },
            },
        },
        {
            "position": "DST",
            "decisionEnvelope": {
                "primaryRecommendation": {
                    "playerName": "Real Defense Two", "position": "DST", "team": "BUF", "ecr": 4.0,
                    "tier": 1, "week": 1, "authority": "fantasypros", "rosterStatus": "AVAILABLE",
                    "recommendation": "ADD",
                },
            },
        },
    ],
    "positions": [
        {
            "playerName": "Real Kicker One", "position": "K", "team": "SF", "ecr": 3.0,
            "tier": 1, "week": 1, "authority": "fantasypros", "rosterStatus": "AVAILABLE",
            "recommendation": "ADD",
        },
        {
            "playerName": "Real Kicker Two", "position": "K", "team": "KC", "ecr": 5.0,
            "tier": 1, "week": 1, "authority": "fantasypros", "rosterStatus": "AVAILABLE",
            "recommendation": "ALTERNATIVE",
        },
        {
            "playerName": "Real Defense One", "position": "DST", "team": "SF", "ecr": 2.0,
            "tier": 1, "week": 1, "authority": "fantasypros", "rosterStatus": "YOUR_ROSTER",
            "recommendation": "HOLD",
        },
        {
            "playerName": "Real Defense Two", "position": "DST", "team": "BUF", "ecr": 4.0,
            "tier": 1, "week": 1, "authority": "fantasypros", "rosterStatus": "AVAILABLE",
            "recommendation": "ADD",
        },
    ],
    "unmatchedSleeperPlayerIds": [],
    "writeBehavior": "NO_SLEEPER_WRITES_NO_FANTASYPROS_WRITES",
}


def test_weekly_home_actions_does_not_500_on_the_real_kdst_flat_list_shape(
    tmp_path: Path, monkeypatch
) -> None:
    """Regression for the real, previously-disclosed `weekly-home-actions`
    500 bug: a Sleeper-imported active roster's real K/DST streamer payload
    (a flat list, not a dict-keyed-by-position) must not crash the whole
    endpoint, and its one real "ADD" candidate per position must still
    surface as a real STREAMER action -- honest partial degradation was
    never actually needed here once the shape assumption itself is fixed."""
    facade, _profile_id = _fresh_local_facade(tmp_path)

    lineup_payload = {
        "season": 2026, "week": 1, "leagueId": "9999",
        "leagueSnapshotId": _FAKE_SNAPSHOT_ID,
        "traceId": "trace-lineup-1",
        "providerHealth": {"freshness": "LIVE", "issues": []},
        "projectedTotal": 111.5,
        "starters": [], "bench": [], "excluded": [], "swaps": [],
        "writeBehavior": "NO_SLEEPER_WRITES",
    }

    monkeypatch.setattr(
        facade, "redraft_weekly_lineup", lambda *, week: FacadePayload(data=lineup_payload)
    )
    monkeypatch.setattr(
        facade, "redraft_kdst_streamer",
        lambda *, week: FacadePayload(data=_REAL_SHAPE_KDST_PAYLOAD),
    )

    def _unavailable(*args, **kwargs):
        raise FacadeError("SUB_TOOL_UNAVAILABLE", "not configured in this fixture", status=409)

    monkeypatch.setattr(facade, "redraft_waivers", _unavailable)
    monkeypatch.setattr(facade, "redraft_trade_finder", _unavailable)
    monkeypatch.setattr(
        facade, "redraft_free_agents",
        lambda: FacadePayload(data={"leagueId": "9999", "freeAgents": [], "rankingWarning": "", "writeBehavior": "NO_SLEEPER_WRITES"}),
    )

    # This call must NOT raise -- before the fix, the real flat-list shape
    # above raised `AttributeError: 'list' object has no attribute 'items'`
    # here, uncaught, surfacing as a bare HTTP 500.
    result = facade.redraft_weekly_home_actions(week=1).data

    streamer_actions_found = [row for row in result["actions"] if row["category"] == "STREAMER"]
    assert {row["summary"] for row in streamer_actions_found} == {
        "Stream K: Real Kicker One",
        "Stream DST: Real Defense Two",
    }
    # STREAMER is genuinely available here (real ADD rows exist) -- it must
    # NOT be reported as unavailable/degraded when it actually worked.
    assert "STREAMER" not in {row["section"] for row in result["unavailableSections"]}
    # The other real, valid sub-sections still render -- one bad/misread
    # section never takes down the whole Home response.
    assert result["leagueSnapshotId"] == _FAKE_SNAPSHOT_ID
    unavailable_sections = {row["section"] for row in result["unavailableSections"]}
    assert unavailable_sections == {"WAIVER", "TRADE"}


def test_weekly_home_actions_degrades_streamer_honestly_on_a_genuinely_malformed_payload(
    tmp_path: Path, monkeypatch
) -> None:
    """If `decisionEnvelopes` (the real shape the STREAMER action loop reads
    -- NWR Sunday Readiness overnight cycle, Worker 3, W6 fix) is ever some
    OTHER unexpected shape, the endpoint must still return 200 with every
    other real action intact, and disclose STREAMER as degraded -- never a
    bare 500, and never a silently-empty Home."""
    facade, _profile_id = _fresh_local_facade(tmp_path)

    lineup_payload = {
        "season": 2026, "week": 1, "leagueId": "9999",
        "leagueSnapshotId": _FAKE_SNAPSHOT_ID,
        "traceId": "trace-lineup-1",
        "providerHealth": {"freshness": "LIVE", "issues": []},
        "projectedTotal": 111.5,
        "starters": [], "bench": [], "excluded": [], "swaps": [],
        "writeBehavior": "NO_SLEEPER_WRITES",
    }
    malformed_kdst_payload = {**_REAL_SHAPE_KDST_PAYLOAD, "decisionEnvelopes": "not-a-list-or-dict"}

    monkeypatch.setattr(
        facade, "redraft_weekly_lineup", lambda *, week: FacadePayload(data=lineup_payload)
    )
    monkeypatch.setattr(
        facade, "redraft_kdst_streamer",
        lambda *, week: FacadePayload(data=malformed_kdst_payload),
    )

    def _unavailable(*args, **kwargs):
        raise FacadeError("SUB_TOOL_UNAVAILABLE", "not configured in this fixture", status=409)

    monkeypatch.setattr(facade, "redraft_waivers", _unavailable)
    monkeypatch.setattr(facade, "redraft_trade_finder", _unavailable)
    monkeypatch.setattr(
        facade, "redraft_free_agents",
        lambda: FacadePayload(data={"leagueId": "9999", "freeAgents": [], "rankingWarning": "", "writeBehavior": "NO_SLEEPER_WRITES"}),
    )

    result = facade.redraft_weekly_home_actions(week=1).data

    assert result["leagueSnapshotId"] == _FAKE_SNAPSHOT_ID
    assert result["lineup"] == lineup_payload
    unavailable_sections = {row["section"] for row in result["unavailableSections"]}
    assert unavailable_sections == {"WAIVER", "TRADE", "STREAMER"}
    assert not any(row["category"] == "STREAMER" for row in result["actions"])
