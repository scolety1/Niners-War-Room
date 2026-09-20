"""NWR Sunday Readiness overnight cycle, Worker 3 (W6 fix): regression
tests for `redraft_kdst_streamer`'s primary-recommendation selection and
position-configuration enforcement.

Governing brief regression fixture 6 (exact numbers): "owned starting K has
ECR1; free K has ECR10. Buggy: actions are START and ADD, facade primary
selects the ADD. Fix must select KEEP/START as primary in this scenario."

Root cause (`desktop_facade.py`'s `redraft_kdst_streamer`): `top_action`
used to be `add_action or (actions[0] if actions else None)` -- i.e. it
ALWAYS preferred the best-ECR unrostered ("ADD") row over the owner's own
better-ranked starter, ownership alone never being considered. Fixed: the
primary recommendation is now the first REAL, ECR-ranked, actionable row
(START/HOLD/ADD -- never a real opponent's ROSTERED_ELSEWHERE row), so
KEEP CURRENT (`recommendation == "START"`) is a genuinely reachable primary
result whenever the owner's own starter really is the best real, accessible
option.

Also covers the brief's position-configuration requirement: a league with
`roster.dst == 0` (e.g. the real Las Vegas Enginerds roster shape) must
never be offered a DST pickup at all.
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


def _facade_with_kdst_league(tmp_path: Path, *, k_slots: int, dst_slots: int) -> tuple[DesktopBackendFacade, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="KDST Keep-Current League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(
        store,
        replace(
            profile, provider="sleeper", provider_league_id="9999",
            roster=replace(profile.roster, k=k_slots, dst=dst_slots),
        ),
    )
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "KDST Keep-Current League"},
                "owner": {"user_id": "owner-1"},
                # Flaim-integration cycle, Worker 2: real receipts always
                # carry a `roster_snapshot.players` list -- the capability
                # guard now reads it, so this fixture must mirror that real
                # shape (a minimal, honest placeholder list, not a real
                # roster) rather than the pre-guard, roster-less shape.
                "roster_snapshot": {"players": ["k-owned"]},
            }
        ),
        encoding="utf-8",
    )
    return facade, profile_id


def _fake_get_json(self: Any, path: str) -> Any:
    if path == "league/9999/rosters":
        return [
            {"owner_id": "owner-1", "players": ["k-owned"], "starters": ["k-owned"]},
            {"owner_id": "owner-2", "players": ["d-opponent"], "starters": ["d-opponent"]},
        ]
    if path == "players/nfl":
        return {
            "k-owned": {"full_name": "Owned Kicker", "position": "K", "team": "SF"},
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


def test_regression_fixture_6_owned_ecr1_starter_beats_a_free_ecr10_kicker_keep_current_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact brief fixture: owned starting K at real ECR1, a free K at
    real ECR10. Primary recommendation must be KEEP CURRENT (`START`), not
    the worse-ranked free-agent ADD."""

    facade, _profile_id = _facade_with_kdst_league(tmp_path, k_slots=1, dst_slots=1)
    _configure_fantasypros(monkeypatch)

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        if position == "K":
            return (
                ConsensusRow("fp-k-owned", "Owned Kicker", "K", "SF", 1, 1, week, season),
                ConsensusRow("fp-k-free", "Free Kicker", "K", "MIA", 10, 3, week, season),
            )
        # No real DST candidates needed for this fixture's own assertion --
        # a minimal, real, honest row set.
        return (ConsensusRow("fp-d-opponent", "49ers", "DST", "SF", 1, 1, week, season),)

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient, "consensus_rankings", _fake_consensus_rankings
    )

    result = facade.redraft_kdst_streamer(week=1)
    envelopes = {row["position"]: row["decisionEnvelope"] for row in result.data["decisionEnvelopes"]}
    k_primary = envelopes["K"]["primaryRecommendation"]

    # THE FIX: primary recommendation is the owned, better-ranked starter,
    # not the worse-ranked free-agent ADD.
    assert k_primary is not None
    assert k_primary["playerName"] == "Owned Kicker"
    assert k_primary["recommendation"] == "START"
    assert k_primary["rosterStatus"] == "YOUR_STARTER"
    assert k_primary["ecr"] == 1

    # Real, still-visible alternative row -- `streamer_actions` itself still
    # honestly labels the best real unrostered option "ADD" on its own row
    # (a per-row "this is the best real add option" fact, unchanged by this
    # fix); what changed is which row the facade leads with as PRIMARY.
    # The app never hides the free option, it just correctly does not lead
    # with it.
    k_rows = [row for row in result.data["positions"] if row["position"] == "K"]
    free_row = next(row for row in k_rows if row["playerName"] == "Free Kicker")
    assert free_row["recommendation"] == "ADD"
    assert free_row["ecr"] == 10
    # It IS listed among the real alternatives the K envelope carries.
    k_alternatives = envelopes["K"]["alternatives"]
    assert any(alt.get("playerName") == "Free Kicker" for alt in k_alternatives)


def test_regression_fixture_6b_genuine_upgrade_still_recommends_the_add(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanity companion to fixture 6: when the owned starter genuinely
    ranks WORSE than an available free agent, ADD must still be selected --
    the fix must not have overcorrected into always preferring KEEP."""

    facade, _profile_id = _facade_with_kdst_league(tmp_path, k_slots=1, dst_slots=1)
    _configure_fantasypros(monkeypatch)

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        if position == "K":
            return (
                ConsensusRow("fp-k-free", "Free Kicker", "K", "MIA", 1, 1, week, season),
                ConsensusRow("fp-k-owned", "Owned Kicker", "K", "SF", 10, 3, week, season),
            )
        return (ConsensusRow("fp-d-opponent", "49ers", "DST", "SF", 1, 1, week, season),)

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient, "consensus_rankings", _fake_consensus_rankings
    )

    result = facade.redraft_kdst_streamer(week=1)
    envelopes = {row["position"]: row["decisionEnvelope"] for row in result.data["decisionEnvelopes"]}
    k_primary = envelopes["K"]["primaryRecommendation"]
    assert k_primary["playerName"] == "Free Kicker"
    assert k_primary["recommendation"] == "ADD"


def test_regression_fixture_6c_an_opponents_rostered_player_is_never_the_primary_recommendation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Opponents' rostered players must NOT be suggested as acquisitions,
    even when they carry the single best real ECR in the whole pool."""

    facade, _profile_id = _facade_with_kdst_league(tmp_path, k_slots=1, dst_slots=1)
    _configure_fantasypros(monkeypatch)

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        if position == "K":
            return (ConsensusRow("fp-k-owned", "Owned Kicker", "K", "SF", 5, 2, week, season),)
        # Real opponent-rostered DST (best ECR) plus a real, genuinely
        # available alternative.
        return (
            ConsensusRow("fp-d-opponent", "49ers", "DST", "SF", 1, 1, week, season),
            ConsensusRow("fp-d-free", "Free Defense", "DST", "GB", 4, 1, week, season),
        )

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient, "consensus_rankings", _fake_consensus_rankings
    )

    result = facade.redraft_kdst_streamer(week=1)
    envelopes = {row["position"]: row["decisionEnvelope"] for row in result.data["decisionEnvelopes"]}
    dst_primary = envelopes["DST"]["primaryRecommendation"]
    assert dst_primary is not None
    assert dst_primary["playerName"] != "49ers"
    assert dst_primary["playerName"] == "Free Defense"
    assert dst_primary["recommendation"] == "ADD"


def test_never_recommends_a_dst_pickup_for_a_league_with_no_dst_slot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Position-configuration enforcement (brief: 'never recommend a DST
    pickup for Enginerds' -- generalized here to any league with a real
    `roster.dst == 0`, matching Las Vegas Enginerds' own real roster
    shape). A league with no DST slot must never be offered a DST
    recommendation, and the DST FantasyPros consensus read must never even
    be attempted."""

    facade, _profile_id = _facade_with_kdst_league(tmp_path, k_slots=1, dst_slots=0)
    _configure_fantasypros(monkeypatch)

    consensus_calls: list[str] = []

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        consensus_calls.append(position)
        if position == "K":
            return (ConsensusRow("fp-k-owned", "Owned Kicker", "K", "SF", 1, 1, week, season),)
        raise AssertionError("DST consensus must never be requested for a no-DST-slot league.")

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient, "consensus_rankings", _fake_consensus_rankings
    )

    result = facade.redraft_kdst_streamer(week=1)
    assert consensus_calls == ["K"]  # DST was never even queried
    envelopes = {row["position"]: row["decisionEnvelope"] for row in result.data["decisionEnvelopes"]}
    dst_envelope = envelopes["DST"]
    assert dst_envelope["primaryRecommendation"] is None
    assert dst_envelope["confidenceState"] == "UNAVAILABLE"
    assert "no DST roster slot" in dst_envelope["rationale"] or "no DST" in dst_envelope["rationale"]
    dst_rows = [row for row in result.data["positions"] if row["position"] == "DST"]
    assert dst_rows == []
    # K, which the league DOES use, is unaffected by the DST guard.
    assert envelopes["K"]["primaryRecommendation"]["playerName"] == "Owned Kicker"
