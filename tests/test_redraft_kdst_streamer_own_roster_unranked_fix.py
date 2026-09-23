"""Waiver-Night Hardening cycle, Worker B (2026-09-22): regression test for
a real, live-reproduced disclosure gap in `redraft_kdst_streamer`.

Live evidence (real Fantasy Gamers league, week 3, this pass): the owner's
real rostered DST (New England, Sleeper id "NE") is genuinely outside
FantasyPros' real current top-10 DST ECR this week. Before this fix, that
meant New England never appeared anywhere in the response -- not in
`positions`, not labeled `YOUR_STARTER`, nothing -- it was only present as
an anonymous, unnamed id buried in the generic `unmatchedSleeperPlayerIds`
list alongside opponents' unranked DSTs. The DST decision envelope's
primary recommendation flatly said "ADD <some available team>" with no
caveat that the owner's actual current DST was never evaluable at all.
This directly undermines the streamer's stated job ("should I keep my
current K/DST or stream someone else" -- never merely rank free agents).

Fix: resolve the owner's own unmatched K/DST sleeper id(s) to a real
name/team, surface them in a new `ownRosterUnranked` field, append an
honest disclosure to that position's `rationale`/`confidenceBasis`/
`issues`, and downgrade `confidenceState` to LOW (never NOMINAL) when the
owner's own current asset for that position could not be evaluated.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.fantasypros_kdst_consensus_service import ConsensusRow
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_kdst_league(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="KDST Own-Roster-Unranked League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(
        store,
        replace(
            profile, provider="sleeper", provider_league_id="9999",
            roster=replace(profile.roster, k=1, dst=1),
        ),
    )
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "KDST Own-Roster-Unranked League"},
                "owner": {"user_id": "owner-1"},
                "roster_snapshot": {"players": ["k-owned", "d-owned-unranked"]},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


def _fake_get_json(self: Any, path: str) -> Any:
    if path == "league/9999/rosters":
        return [
            {
                "owner_id": "owner-1",
                "players": ["k-owned", "d-owned-unranked"],
                "starters": ["k-owned", "d-owned-unranked"],
            },
            {"owner_id": "owner-2", "players": ["d-opponent"], "starters": ["d-opponent"]},
        ]
    if path == "players/nfl":
        return {
            "k-owned": {"full_name": "Owned Kicker", "position": "K", "team": "SF"},
            # Real Sleeper DST catalog shape (per
            # `fantasypros_kdst_consensus_service.py`'s own documented
            # finding): DST rows carry first_name/last_name, never
            # full_name/search_full_name.
            "d-owned-unranked": {
                "position": "DEF", "team": "NE",
                "first_name": "New England", "last_name": "Patriots",
            },
            "d-opponent": {"full_name": "49ers", "position": "DEF", "team": "SF"},
        }
    raise AssertionError(f"unexpected Sleeper GET path in test: {path}")


def _configure_fantasypros(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        desktop_facade_module,
        "fantasypros_provider_status",
        lambda: SimpleNamespace(
            configured=True, authority="EXTERNAL CONSENSUS — FANTASYPROS", message="ok"
        ),
    )
    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)


def test_owners_own_unranked_dst_is_disclosed_not_silently_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    facade, _profile_id = _facade_with_kdst_league(tmp_path)
    _configure_fantasypros(monkeypatch)

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        if position == "K":
            return (ConsensusRow("fp-k-owned", "Owned Kicker", "K", "SF", 1, 1, week, season),)
        # New England (the owner's real rostered DST) is deliberately
        # absent from this week's real FantasyPros consensus rows --
        # only the opponent's DST and a genuinely available one are
        # returned, mirroring the live-observed real gap.
        return (
            ConsensusRow("fp-d-opponent", "49ers", "DST", "SF", 1, 1, week, season),
            ConsensusRow("fp-d-free", "Free Defense", "DST", "GB", 2, 1, week, season),
        )

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient,
        "consensus_rankings",
        _fake_consensus_rankings,
    )

    result = facade.redraft_kdst_streamer(week=3)
    data = result.data

    # THE FIX: the owner's own unranked DST is now named, not silently
    # dropped into an anonymous id list.
    own_unranked = data["ownRosterUnranked"]
    assert own_unranked == [
        {
            "position": "DST",
            "sleeperPlayerId": "d-owned-unranked",
            "playerName": "New England Patriots",
            "team": "NE",
        }
    ]

    # Real regression guard: New England genuinely never appears in
    # `positions` (FantasyPros never ranked it this week) -- but it IS
    # still visible in `unmatchedSleeperPlayerIds` (the pre-existing,
    # now-supplemented disclosure), proving this fix is additive, not a
    # replacement of the existing honest-gap signal.
    dst_rows = [row for row in data["positions"] if row["position"] == "DST"]
    assert all(row["playerName"] != "New England Patriots" for row in dst_rows)
    unmatched_ids = data["unmatchedSleeperPlayerIds"]
    assert {"position": "DST", "sleeperPlayerId": "d-owned-unranked"} in unmatched_ids

    envelopes = {row["position"]: row["decisionEnvelope"] for row in data["decisionEnvelopes"]}
    dst_envelope = envelopes["DST"]
    # A real primary recommendation still exists (Free Defense is a real,
    # genuinely available ADD) -- the fix does not suppress it.
    assert dst_envelope["primaryRecommendation"]["playerName"] == "Free Defense"
    # But confidence is honestly downgraded: NWR could not evaluate the
    # owner's OWN current asset, so it must never claim NOMINAL here.
    assert dst_envelope["confidenceState"] == "LOW"
    assert "New England Patriots" in dst_envelope["confidenceBasis"]
    assert "could not be evaluated" in dst_envelope["confidenceBasis"]
    assert "New England Patriots" in dst_envelope["rationale"]
    assert any("New England Patriots" in issue for issue in dst_envelope["issues"])

    # K is unaffected (fully matched, no owner-unranked gap for K).
    k_envelope = envelopes["K"]
    assert k_envelope["confidenceState"] == "NOMINAL"
    assert not any(entry["position"] == "K" for entry in own_unranked)

    # Real, uncached, live-every-call freshness disclosure now present.
    assert isinstance(data["retrievedAtUtc"], str) and data["retrievedAtUtc"]


def test_no_own_roster_unranked_gap_produces_an_empty_list_not_a_missing_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression safety: when nothing is affected, `ownRosterUnranked` is
    still present as an honest empty list -- the key is never simply
    absent, which would make an API consumer unable to distinguish "not
    checked" from "checked, nothing found"."""

    facade, _profile_id = _facade_with_kdst_league(tmp_path)
    _configure_fantasypros(monkeypatch)

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        if position == "K":
            return (ConsensusRow("fp-k-owned", "Owned Kicker", "K", "SF", 1, 1, week, season),)
        return (
            ConsensusRow("fp-d-owned", "New England Patriots", "DST", "NE", 1, 1, week, season),
            ConsensusRow("fp-d-opponent", "49ers", "DST", "SF", 2, 1, week, season),
        )

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient,
        "consensus_rankings",
        _fake_consensus_rankings,
    )

    result = facade.redraft_kdst_streamer(week=3)
    assert result.data["ownRosterUnranked"] == []
    envelopes = {
        row["position"]: row["decisionEnvelope"] for row in result.data["decisionEnvelopes"]
    }
    assert envelopes["DST"]["confidenceState"] == "NOMINAL"
    assert envelopes["DST"]["primaryRecommendation"]["rosterStatus"] == "YOUR_STARTER"
