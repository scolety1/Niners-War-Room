"""Flaim-integration cycle, Worker 2 (2026-09-19): regression tests for
`redraft_kdst_streamer`'s guard being rewritten from a direct "does a
Sleeper import receipt parse" check into a provider-agnostic
`league_capability_service.capabilities_for_profile(...)` check.

Three real behaviors must hold:

1. A real-shaped Sleeper receipt (identity + `roster_snapshot.players`)
   still satisfies the guard exactly as before -- no regression for a real,
   working Sleeper league (Fantasy Gamers / Las Vegas Enginerds pattern).
2. A profile with NO roster data at all (no Sleeper receipt file, no ESPN/
   Flaim snapshot file -- the real, honest state for KHA and 403 N 18th
   today, since no real ESPN snapshot has been fetched yet) is rejected
   with the new capability-based 409 message, not a crash and not a
   false positive.
3. A Sleeper receipt file that exists but is malformed (parses as JSON but
   is missing the `league`/`owner` blocks the live Sleeper fetch itself
   needs) still produces the old, Sleeper-specific 409 -- the capability
   check alone isn't sufficient once a receipt is present but broken.

No live Flaim/ESPN data is used anywhere in this file -- only clearly
synthetic, in-memory test fixtures, consistent with this cycle's governance
discipline (see `docs/codex/flaim_integration_20260919/LEDGER.md`).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.fantasypros_kdst_consensus_service import ConsensusRow
from src.services.redraft_engine_v1_service import load_profile, save_profile

REPO_ROOT = Path(__file__).resolve().parents[1]


def _create_active_profile(tmp_path: Path, *, league_name: str) -> tuple[DesktopBackendFacade, Path, str]:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name=league_name)
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    profile = load_profile(store, profile_id)
    save_profile(
        store,
        replace(
            profile,
            provider="sleeper",
            provider_league_id="9999",
            roster=replace(profile.roster, k=1, dst=1),
        ),
    )
    return facade, store, profile_id


def _configure_fantasypros(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        desktop_facade_module,
        "fantasypros_provider_status",
        lambda: SimpleNamespace(
            configured=True, authority="EXTERNAL CONSENSUS — FANTASYPROS", message="ok"
        ),
    )

    def _fake_get_json(self: Any, path: str) -> Any:
        if path == "league/9999/rosters":
            return [
                {"owner_id": "owner-1", "players": ["k-1"], "starters": ["k-1"]},
                {"owner_id": "owner-2", "players": ["d-1"], "starters": []},
            ]
        if path == "players/nfl":
            return {
                "k-1": {"full_name": "Kicker One", "position": "K", "team": "SF"},
                "d-1": {"full_name": "Seahawks", "position": "DEF", "team": "SEA"},
            }
        raise AssertionError(f"unexpected Sleeper GET path in test: {path}")

    monkeypatch.setattr(desktop_facade_module.SleeperHttpClient, "get_json", _fake_get_json)

    def _fake_consensus_rankings(
        self: Any, *, season: int, position: str, week: int, scoring: str
    ) -> tuple[ConsensusRow, ...]:
        if position == "K":
            return (ConsensusRow("fp-k-1", "Kicker One", "K", "SF", 1, 1, week, season),)
        return (ConsensusRow("fp-d-1", "Seahawks", "DST", "SEA", 1, 1, week, season),)

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient, "consensus_rankings", _fake_consensus_rankings
    )


def test_real_shaped_sleeper_receipt_still_works_no_regression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real-shaped Sleeper receipt (matching what
    `sleeper_redraft_owner_service.py` actually writes for real leagues like
    Fantasy Gamers / Las Vegas Enginerds -- identity + `roster_snapshot.
    players`) satisfies the new capability guard exactly as the old direct
    receipt-parse check did, and the streamer runs normally."""

    facade, store, profile_id = _create_active_profile(tmp_path, league_name="Real Shape League")
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "Real Shape League"},
                "owner": {"user_id": "owner-1"},
                "roster_snapshot": {"players": ["k-1"], "synced_at_utc": "2026-09-19T00:00:00Z"},
                "roster_positions": ["K", "DST"],
                "scoring_reconciliation": {"pass_td": 4},
                "unsupported_scoring": [],
            }
        ),
        encoding="utf-8",
    )
    _configure_fantasypros(monkeypatch)

    result = facade.redraft_kdst_streamer(week=1)
    envelopes = {row["position"]: row["decisionEnvelope"] for row in result.data["decisionEnvelopes"]}
    assert envelopes["K"]["primaryRecommendation"]["playerName"] == "Kicker One"
    assert envelopes["DST"]["primaryRecommendation"]["playerName"] == "Seahawks"


def test_no_roster_data_at_all_is_rejected_with_capability_based_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A profile with no Sleeper receipt file and no ESPN/Flaim snapshot
    file -- the real, current, honest state for KHA and 403 N 18th, since
    no real ESPN snapshot has ever been fetched -- is rejected with the new
    capability-based 409 message, not a crash and not a false positive."""

    facade, _store, _profile_id = _create_active_profile(tmp_path, league_name="No Data League")
    _configure_fantasypros(monkeypatch)

    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_kdst_streamer(week=1)

    assert exc_info.value.status == 409
    assert exc_info.value.code == "KDST_STREAMER_LEAGUE_DATA_REQUIRED"
    assert "No verified league data available for this league" in exc_info.value.message
    # The old, Sleeper-specific wording must be gone from this branch --
    # the whole point of the rewrite is that this message no longer
    # presupposes Sleeper.
    assert "Sleeper import receipt" not in exc_info.value.message


def test_real_fantasy_gamers_shaped_receipt_with_null_roster_snapshot_still_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real, LIVE-discovered edge case (this pass): Fantasy Gamers' real
    on-disk receipt (`local_exports/redraft_v1/sleeper_imports/
    941b99ade350410391b1b67c0890af79.json`) has `roster_snapshot: null`,
    unlike Las Vegas Enginerds' receipt. A guard gated on `has_roster_data`
    would incorrectly 409 this real, already-working league -- this test
    pins the real fix (gating on `has_verified_identity` instead)."""

    facade, store, profile_id = _create_active_profile(tmp_path, league_name="Fantasy Gamers")
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps(
            {
                "league": {"league_id": "9999", "name": "Fantasy Gamers"},
                "owner": {"user_id": "owner-1"},
                "roster_snapshot": None,
                "roster_positions": None,
                "scoring_reconciliation": None,
                "unsupported_scoring": None,
            }
        ),
        encoding="utf-8",
    )
    _configure_fantasypros(monkeypatch)

    result = facade.redraft_kdst_streamer(week=1)
    envelopes = {row["position"]: row["decisionEnvelope"] for row in result.data["decisionEnvelopes"]}
    assert envelopes["K"]["primaryRecommendation"]["playerName"] == "Kicker One"


def test_present_but_malformed_sleeper_receipt_still_blocks_with_sleeper_specific_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A receipt file that exists and parses as JSON, and even carries real
    roster data (so the capability check passes), but is missing the
    `league`/`owner` blocks the live Sleeper fetch itself needs, must still
    be rejected -- the capability check is necessary but not sufficient for
    actually running the Sleeper-specific live fetch below it."""

    facade, store, profile_id = _create_active_profile(tmp_path, league_name="Malformed League")
    receipt_dir = store / "sleeper_imports"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / f"{profile_id}.json").write_text(
        json.dumps({"league": {"league_id": "9999", "name": "Malformed League"},
                     "roster_snapshot": {"players": ["k-1"]}}),
        encoding="utf-8",
    )
    _configure_fantasypros(monkeypatch)

    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_kdst_streamer(week=1)

    assert exc_info.value.status == 409
    assert exc_info.value.code == "KDST_STREAMER_SLEEPER_CONTEXT_REQUIRED"
    assert "valid Sleeper import receipt" in exc_info.value.message


def test_no_active_profile_is_rejected_as_before(tmp_path: Path) -> None:
    """Unrelated, upstream guard (no active profile at all) is untouched by
    this pass -- still its own distinct 409, checked first."""

    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    with pytest.raises(FacadeError) as exc_info:
        facade.redraft_kdst_streamer(week=1)
    assert exc_info.value.status == 409
    assert exc_info.value.code == "KDST_STREAMER_PROFILE_REQUIRED"
