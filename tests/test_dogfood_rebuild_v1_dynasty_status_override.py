"""Dogfood Rebuild V1 (Worker 4), Item 3 -- real regression coverage for the
root-cause bug this pass found and fixed: Dynasty never consumed the real,
sourced current-player-status-override authority
(`current_player_status_overrides_service.py`) at all -- confirmed by a
full-repo grep showing every call site of `load_status_overrides`/
`apply_status_overrides_to_ranking` was prefixed `redraft_*`. This file
covers the new choke-point wiring (`owner_asset_evidence_service.
compose_owner_asset_evidence`'s `status_overrides` parameter), its
passthrough (`owner_mode_view_service.owner_rankings_frame`), its JSON
shape (`DesktopBackendFacade._status_override_json`), and the exact
give/receive-scoping bug this worker found and fixed live (in the Dynasty
Trade Decision Lab) before committing -- an earlier version of the fix
iterated the WHOLE trade-item lookup universe instead of just the assets in
the trade, which leaked unrelated players' real overrides (e.g. Jayden
Higgins) into a trade that never involved them.

Uses only synthetic fixtures for the isolated unit tests (never the real
committed override file), plus two of the real committed overrides
(Jayden Higgins / Kayshon Boutte) for the live facade scoping-regression
test -- chosen deliberately instead of the also-real De'Von Achane entry
this same pass added, so this test's core assertion (notices never leak to
an asset outside the trade) does not become coupled to one specific
current-event entry that could later be archived/removed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.application.desktop_facade import DesktopBackendFacade
from src.services.current_player_status_overrides_service import StatusOverride
from src.services.owner_asset_evidence_service import compose_owner_asset_evidence
from src.services.owner_mode_view_service import owner_rankings_frame

REPO_ROOT = Path(__file__).resolve().parents[1]


def _asset(
    asset_id: str,
    name: str,
    *,
    asset_type: str = "Current Player",
    position: str = "WR",
    rank: str = "",
    score: str = "",
) -> dict[str, str]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_name": name,
        "position": position,
        "team": "TEST",
        "age": "",
        "source_label": "Finished V1" if asset_type == "Current Player" else "Rookie Review",
        "authority_status": "Production" if asset_type == "Current Player" else "Review-Only",
        "rank_label": "NWR Dynasty Rank",
        "rank_value": rank,
        "tier": "",
        "score_label": "NWR Dynasty Score",
        "score_value": score,
        "confidence": "usable",
        "warnings": "",
        "blocking_reason": "",
        "comparison_scope": "Source-separated only",
    }


def _override(name: str, kind: str = "SEASON_OUT") -> StatusOverride:
    return StatusOverride(
        player_id="00-0000000",
        player_name=name,
        kind=kind,
        reason="Synthetic test override -- not a real event.",
        effective_date="2026-09-27",
        verified_at_utc="2026-09-29T00:00:00Z",
        sources=("https://example.com/synthetic-source",),
    )


def test_compose_owner_asset_evidence_matches_override_by_normalized_name() -> None:
    rows = (
        _asset("current:1", "De'Von Achane", rank="9", score="61.3"),
        _asset("current:2", "Puka Nacua", rank="1", score="83.0"),
    )

    evidence = compose_owner_asset_evidence(
        rows, include_market=False, status_overrides=(_override("De'Von Achane"),)
    )
    by_id = evidence.by_id

    override = by_id["current:1"]["current_status_override"]
    assert override is not None
    assert override["kind"] == "SEASON_OUT"
    assert override["sources"] == ["https://example.com/synthetic-source"]
    # Never touches the governed value/rank fields.
    assert by_id["current:1"]["nwr_dynasty_score"] == "61.3"
    assert by_id["current:1"]["dynasty_rank"] == "9"
    # An unrelated player is explicitly None, never a fabricated absence.
    assert by_id["current:2"]["current_status_override"] is None


def test_compose_owner_asset_evidence_normalizes_apostrophes_and_suffixes() -> None:
    # "De'Von Achane" vs "Devon Achane" -- the exact class of mismatch
    # `normalize_identity_name` exists to close (apostrophe/case-insensitive).
    rows = (_asset("current:1", "De'Von Achane", rank="9"),)

    evidence = compose_owner_asset_evidence(
        rows, include_market=False, status_overrides=(_override("Devon Achane"),)
    )

    assert evidence.by_id["current:1"]["current_status_override"]["kind"] == "SEASON_OUT"


def test_compose_owner_asset_evidence_with_no_overrides_leaves_every_row_none() -> None:
    rows = (_asset("current:1", "De'Von Achane", rank="9"),)

    evidence = compose_owner_asset_evidence(rows, include_market=False)

    assert evidence.by_id["current:1"]["current_status_override"] is None


def test_owner_rankings_frame_passes_through_override_without_affecting_sort() -> None:
    rows = (
        _asset("current:1", "Zed Player", rank="2"),
        _asset("current:2", "Able Player", rank="1"),
    )
    evidence = compose_owner_asset_evidence(
        rows, include_market=False, status_overrides=(_override("Able Player"),)
    )

    frame = owner_rankings_frame(evidence.rows)

    # Sort order is by Rank, unaffected by the presence of an override.
    assert frame["Player"].tolist() == ["Able Player", "Zed Player"]
    override_value = frame.loc[frame["Player"] == "Able Player", "current_status_override"].iloc[0]
    assert override_value["kind"] == "SEASON_OUT"
    assert frame.loc[frame["Player"] == "Zed Player", "current_status_override"].iloc[0] is None


def test_status_override_json_camel_cases_and_handles_none() -> None:
    payload = DesktopBackendFacade._status_override_json(
        {
            "kind": "SEASON_OUT",
            "reason": "Torn ACL.",
            "effective_date": "2026-09-27",
            "verified_at_utc": "2026-09-29T00:00:00Z",
            "sources": ["https://example.com/a"],
            "corrected_team": "",
        }
    )
    assert payload == {
        "kind": "SEASON_OUT",
        "reason": "Torn ACL.",
        "effectiveDate": "2026-09-27",
        "verifiedAtUtc": "2026-09-29T00:00:00Z",
        "sources": ["https://example.com/a"],
        "correctedTeam": "",
    }
    assert DesktopBackendFacade._status_override_json(None) is None
    assert DesktopBackendFacade._status_override_json("not-a-mapping") is None


@pytest.fixture(scope="module")
def _real_dynasty_facade() -> DesktopBackendFacade:
    return DesktopBackendFacade(repo_root=REPO_ROOT, mode="dynasty")


def test_dynasty_rankings_surface_real_committed_status_overrides(
    _real_dynasty_facade: DesktopBackendFacade,
) -> None:
    """Live, real-fixture proof that Dynasty Rankings (previously blind to
    this authority entirely) now surfaces a real committed override --
    Jayden Higgins (SEASON_OUT) -- without it needing to be one of THIS
    pass's own new entries."""

    bootstrap = _real_dynasty_facade.dynasty_bootstrap()
    higgins = [row for row in bootstrap.data["rankings"] if row["player"] == "Jayden Higgins"]
    healthy = [row for row in bootstrap.data["rankings"] if row["player"] == "Puka Nacua"]

    assert higgins, "Jayden Higgins must be present in the real Finished V1 board."
    assert higgins[0]["currentStatusOverride"] is not None
    assert higgins[0]["currentStatusOverride"]["kind"] == "SEASON_OUT"
    assert healthy, "Puka Nacua must be present in the real Finished V1 board."
    assert healthy[0]["currentStatusOverride"] is None


def test_dynasty_bootstrap_discloses_finished_v1_is_a_frozen_base_model(
    _real_dynasty_facade: DesktopBackendFacade,
) -> None:
    bootstrap = _real_dynasty_facade.dynasty_bootstrap()
    titles = [notice["title"] for notice in bootstrap.data["notices"]]
    assert "Finished V1 is a frozen base model, not a live weekly ranking" in titles


def test_dynasty_trade_asset_status_notices_scoped_to_trade_assets_only(
    _real_dynasty_facade: DesktopBackendFacade,
) -> None:
    """Regression test for the exact scoping bug this worker found and fixed
    live before committing: an earlier version iterated the WHOLE trade-item
    lookup universe (built once and shared across every possible trade)
    instead of only `give_ids`/`receive_ids`, which leaked every other
    real overridden player in the entire registry (e.g. Jayden Higgins,
    Kayshon Boutte) into a trade that never involved them."""

    bootstrap = _real_dynasty_facade.dynasty_bootstrap()
    by_name = {row["player"]: row["assetId"] for row in bootstrap.data["rankings"]}
    higgins_id = by_name["Jayden Higgins"]
    healthy_a = by_name["Puka Nacua"]
    healthy_b = by_name["Zay Flowers"]

    # A trade that DOES include the overridden asset must surface exactly
    # one notice, for that asset only.
    with_override = _real_dynasty_facade.evaluate_dynasty_trade(
        give=[higgins_id], receive=[healthy_a], team_window="Balanced"
    )
    notices = with_override.data.get("assetStatusNotices")
    assert notices is not None
    assert [notice["assetId"] for notice in notices] == [higgins_id]

    # A trade that does NOT include Higgins (or any other overridden asset)
    # must carry no leaked notice from elsewhere in the registry -- the key
    # itself is omitted, never an empty-but-present list.
    without_override = _real_dynasty_facade.evaluate_dynasty_trade(
        give=[healthy_a], receive=[healthy_b], team_window="Balanced"
    )
    assert "assetStatusNotices" not in without_override.data


def test_dynasty_compare_asset_status_notices_scoped_to_compared_assets_only(
    _real_dynasty_facade: DesktopBackendFacade,
) -> None:
    """Owner feedback closure (gap closure, Dynasty Compare): Compare never
    surfaced `currentStatusOverride` at all before this fix (Master
    Requirement Ledger Sec1.3/Sec7.13's long-standing "REMAINING ACTION").
    Mirrors `test_dynasty_trade_asset_status_notices_scoped_to_trade_assets_
    only` above -- same real committed overrides, same scoping discipline:
    a comparison that includes the overridden asset surfaces exactly one
    notice for that asset, and a comparison that omits it carries no leaked
    notice from elsewhere in the registry."""

    bootstrap = _real_dynasty_facade.dynasty_bootstrap()
    by_name = {row["player"]: row["assetId"] for row in bootstrap.data["rankings"]}
    higgins_id = by_name["Jayden Higgins"]
    healthy_a = by_name["Puka Nacua"]
    healthy_b = by_name["Zay Flowers"]

    with_override = _real_dynasty_facade.compare_dynasty_assets([higgins_id, healthy_a])
    notices = with_override.data.get("assetStatusNotices")
    assert notices is not None
    assert [notice["assetId"] for notice in notices] == [higgins_id]
    assert notices[0]["kind"] == "SEASON_OUT"
    assert notices[0]["playerName"] == "Jayden Higgins"
    # Base governed comparison fields are present and untouched by this
    # purely additive disclosure layer.
    assert {player["assetId"] for player in with_override.data["players"]} == {
        higgins_id,
        healthy_a,
    }

    without_override = _real_dynasty_facade.compare_dynasty_assets([healthy_a, healthy_b])
    assert "assetStatusNotices" not in without_override.data
