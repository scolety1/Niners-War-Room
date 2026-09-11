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
