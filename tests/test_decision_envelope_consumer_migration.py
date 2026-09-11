"""DecisionResultEnvelope migration-completion tests (NWR pre-UI
architecture CLOSURE pass, 2026-09-10, directive section 4).

`DECISION_CONTRACTS.md` (prior pass) left Trade Analysis, Trade Finder,
and K/DST Streamer with only `traceId`/`leagueSnapshotId` identification
-- no `decisionEnvelope` field. This closure pass finishes all three
using the exact same `build_decision_envelope` (`decision_envelope_
service.py`) Start/Sit and Waivers already used, on top of each tool's
own already-computed real fields (no engine computation changed).

Draft (`redraft_decision_bundle{,_v2}`) remains deliberately untouched by
the envelope (it already has its own, older, separate hash/provenance
system -- see `DATA_AUTHORITY.md`'s "Draft-time hashing" section); this
pass's Draft work is PlayerAvailabilityStatus consumption only (see
`test_player_availability_status_consumer_consistency.py`), consistent
with `DECISION_CONTRACTS.md`'s explicit, disclosed scoping.

Real, disclosed environment constraint (unchanged, see `tests/
test_desktop_facade_architecture_wiring.py`'s module docstring): Trade
Analysis/Trade Finder cannot be exercised end-to-end in this environment
(expired governance receipt blocks the governed ranking both tools
require). K/DST Streamer does NOT depend on the governed ranking, so it
IS exercised end-to-end here, live-mocked -- proving `decisionEnvelopes`
is real and correctly shaped, not just present in source. Trade Analysis/
Trade Finder are proven via direct source inspection instead, the same
honest substitute `test_player_availability_status_consumer_consistency.
py` uses for the same reason.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import load_profile, save_profile
from src.services.fantasypros_kdst_consensus_service import ConsensusRow

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_trade_analysis_returns_a_real_decision_envelope_source() -> None:
    source = inspect.getsource(DesktopBackendFacade.redraft_trade_analysis)
    assert "build_decision_envelope(" in source
    assert 'task="TRADE",' in source
    assert '"decisionEnvelope": trade_analysis_envelope.to_dict()' in source
    # An empty alternatives list is the honest state for a single
    # proposed-trade evaluator -- never a fabricated list of "other trades".
    assert "alternatives=[]," in source


def test_trade_finder_returns_a_real_decision_envelope_source() -> None:
    source = inspect.getsource(DesktopBackendFacade.redraft_trade_finder)
    assert "build_decision_envelope(" in source
    assert 'task="TRADE_FINDER",' in source
    assert '"decisionEnvelope": trade_finder_envelope.to_dict()' in source
    assert 'confidence_state="NOMINAL" if top_result is not None else "UNAVAILABLE"' in source


def test_kdst_streamer_returns_a_real_decision_envelope_per_position(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = tmp_path / "redraft-store"
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=store)
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="KDST Envelope League"
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
        return (
            ConsensusRow("fp-d-2", "Free DST", "DST", "KC", 1, 1, week, season),
            ConsensusRow("fp-d-1", "Seahawks", "DST", "SEA", 2, 1, week, season),
        )

    monkeypatch.setattr(
        desktop_facade_module.FantasyProsConsensusClient,
        "consensus_rankings",
        _fake_consensus_rankings,
    )

    result = facade.redraft_kdst_streamer(week=1)
    envelopes = result.data["decisionEnvelopes"]
    assert {row["position"] for row in envelopes} == {"K", "DST"}
    by_position = {row["position"]: row["decisionEnvelope"] for row in envelopes}

    assert by_position["K"]["task"] == "K_STREAMER"
    assert by_position["DST"]["task"] == "DST_STREAMER"
    for position, envelope in by_position.items():
        assert envelope["profileId"] == profile_id
        assert envelope["leagueSnapshotId"] == result.data["leagueSnapshotId"]
        assert envelope["primaryRecommendation"] is not None
        assert envelope["confidenceState"] == "NOMINAL"
        assert envelope["generatedAtUtc"]
        trace_row = next(row for row in result.data["traceIds"] if row["position"] == position)
        assert envelope["traceId"] == trace_row["traceId"]
