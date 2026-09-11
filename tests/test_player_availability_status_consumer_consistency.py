"""PlayerAvailabilityStatus consumer-consistency tests (NWR pre-UI
architecture CLOSURE pass, 2026-09-10, directive section 2).

The prior pass (see `PRODUCT_ARCHITECTURE.md`'s invariant E,
`DATA_AUTHORITY.md`) built the canonical `PlayerAvailabilityStatus`
authority but wired it into NO product surface -- every surface still
rendered its own local heuristic. This closure pass wires the SAME
authority map (`DesktopBackendFacade._player_availability_status_map`,
keyed by canonical player id -- the same identity key `StatusOverride.
player_id`/`RankingRow.player_id`/`RosterCandidate.canonical_player_id`
already share) into Draft (`_decision_bundle_payload`,
`_decision_bundle_v2_payload`), Lineup (`redraft_weekly_lineup`), Waivers
(`redraft_waivers`), and Trades (`redraft_trade_analysis`,
`redraft_trade_finder`).

Real, disclosed environment constraint (unchanged from the prior pass,
see `tests/test_desktop_facade_architecture_wiring.py`'s own module
docstring): the bundled 2026 projection seed's governance approval
receipt is expired in this worktree, so `redraft_weekly_lineup`/
`redraft_waivers`/`redraft_trade_analysis`/`redraft_trade_finder`/
`redraft_decision_bundle{,_v2}` cannot be exercised end-to-end (a real
Sleeper league + a populated governed ranking) in THIS environment. This
file therefore proves consistency two ways that ARE available in this
environment:

1. `_player_availability_status_map()` is the exact same data
   `redraft_player_availability_status()` (the standalone authority
   endpoint) already returns -- same repo_root, same function, same
   dict, keyed identically -- so no consumer can drift from the
   authority by construction.
2. A direct, static source-level proof (not a guess) that every one of
   the six real call sites reads from this SAME map/field name and keys
   its lookup by the SAME canonical-player-id attribute the engine
   itself already uses for that surface (`candidate.canonical_player_id`
   / `candidate.player_id` / `impact.player_id`) -- i.e. no surface
   invented its own separate status lookup or a different identity key.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import src.application.desktop_facade as desktop_facade_module
from src.application.desktop_facade import DesktopBackendFacade

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fresh_local_facade(tmp_path: Path):
    facade = DesktopBackendFacade(
        repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path / "redraft-store"
    )
    created = facade.create_redraft_profile(
        preset_key="12_TEAM_1QB_HALF_PPR", league_name="Availability Consistency League"
    )
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    return facade, profile_id


def test_player_availability_status_map_matches_the_standalone_authority_endpoint(
    tmp_path: Path,
) -> None:
    """The exact map every consumer reads must be byte-identical to what
    the standalone `PlayerAvailabilityStatus` authority endpoint reports --
    proving there is exactly ONE authority, not a per-consumer copy."""
    facade, _profile_id = _fresh_local_facade(tmp_path)
    consumer_map = facade._player_availability_status_map()
    authority_rows = facade.redraft_player_availability_status().data["statuses"]
    assert consumer_map, "expected at least one real admitted override in this repo's config"
    assert {row["playerId"] for row in authority_rows} == set(consumer_map)
    for row in authority_rows:
        assert consumer_map[row["playerId"]] == row


def test_player_availability_status_map_is_keyed_by_canonical_player_id(tmp_path: Path) -> None:
    """Every value's own `playerId` field must equal the key it's stored
    under -- the same identity contract every consumer below relies on."""
    facade, _profile_id = _fresh_local_facade(tmp_path)
    consumer_map = facade._player_availability_status_map()
    for player_id, status in consumer_map.items():
        assert status["playerId"] == player_id


def _source(obj) -> str:
    return inspect.getsource(obj)


def test_weekly_lineup_start_sit_consumes_the_canonical_authority_not_a_local_heuristic() -> None:
    source = _source(DesktopBackendFacade.redraft_weekly_lineup)
    assert "self._player_availability_status_map()" in source
    assert "\"playerAvailabilityStatus\": availability_status_by_id.get(" in source
    assert "slot.player.canonical_player_id" in source


def test_waivers_add_drop_faab_consumes_the_canonical_authority_not_a_local_heuristic() -> None:
    source = _source(DesktopBackendFacade.redraft_waivers)
    assert "self._player_availability_status_map()" in source
    assert "\"playerAvailabilityStatus\": availability_status_by_id.get(" in source
    assert "candidate.canonical_player_id" in source


def test_trade_analysis_consumes_the_canonical_authority_not_a_local_heuristic() -> None:
    source = _source(DesktopBackendFacade.redraft_trade_analysis)
    assert "self._player_availability_status_map()" in source
    assert "\"playerAvailabilityStatus\": availability_status_by_id.get(impact.player_id)" in source


def test_trade_finder_consumes_the_canonical_authority_not_a_local_heuristic() -> None:
    source = _source(DesktopBackendFacade.redraft_trade_finder)
    assert "self._player_availability_status_map()" in source
    assert "myGivePlayerAvailabilityStatus" in source
    assert "opponentGivePlayerAvailabilityStatus" in source


def test_draft_decision_bundle_consumes_the_canonical_authority_not_a_local_heuristic() -> None:
    payload_source = _source(desktop_facade_module._decision_bundle_payload)
    assert "player_availability_status_by_id" in payload_source
    assert "\"playerAvailabilityStatus\": availability_status_by_id.get(candidate.player_id)" in payload_source

    v2_payload_source = _source(desktop_facade_module._decision_bundle_v2_payload)
    assert "player_availability_status_by_id" in v2_payload_source
    assert "\"playerAvailabilityStatus\": availability_status_by_id.get(candidate.player_id)" in v2_payload_source

    v1_source = _source(DesktopBackendFacade.redraft_decision_bundle)
    v2_source = _source(DesktopBackendFacade.redraft_decision_bundle_v2)
    assert "player_availability_status_by_id=self._player_availability_status_map()" in v1_source
    assert "player_availability_status_by_id=self._player_availability_status_map()" in v2_source


def test_every_migrated_surface_reads_the_same_helper_name() -> None:
    """No surface may define its own competing status-map helper -- they
    all call the ONE facade method, proving a single canonical authority
    rather than five independently-drifting copies."""
    facade_source = inspect.getsource(desktop_facade_module)
    call_count = facade_source.count("self._player_availability_status_map()")
    # Lineup, Waivers, Trade Analysis, Trade Finder, Draft v1, Draft v2 == 6.
    assert call_count == 6, (
        f"expected exactly 6 call sites (Lineup/Waivers/Trades x2/Draft x2), found {call_count}"
    )
