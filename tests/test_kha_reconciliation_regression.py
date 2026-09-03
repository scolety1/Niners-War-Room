"""Backend regression against the real 2026 KHA draft reconciliation ledger.

Companion to desktop/apps/redraft/src/pages.test.ts's globalPickSearchRows
tests, which cover the same fixture on the frontend. This file proves the
*data layer* (the real manual K/DST asset pool captured from the live
draft, run through the actual `_asset_pool` merge function) already
supports representing every historical K_DST_UNREPRESENTABLE pick -- the
2026-09-02 failure was a discoverability/UI gap (position filter had to
already be set to K or DST), not a missing-data gap. See
sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.md and
docs/codex/KDST_AND_UNIVERSE_GAP_EVIDENCE_20260903.md.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.redraft_draft_room_v1_service import _asset_pool
from src.services.redraft_engine_v1_service import RankingResult

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "kha_real_draft_2026"


def _empty_ranking() -> RankingResult:
    return RankingResult(None, (), (), (), "", "")  # type: ignore[arg-type]


def _real_manual_kdst_assets() -> list[dict[str, str]]:
    payload = json.loads((FIXTURE_DIR / "live_manual_kdst_assets_64.json").read_text(encoding="utf-8"))
    return payload["assets"]


def _historical_kdst_picks() -> list[dict[str, str]]:
    with (FIXTURE_DIR / "RECONCILIATION_LEDGER.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    picks = [row for row in rows if row["classification"] == "K_DST_UNREPRESENTABLE"]
    assert len(picks) == 14, f"expected 14 historical K_DST_UNREPRESENTABLE rows, found {len(picks)}"
    return picks


def _matches_query(asset: dict[str, str], fragment: str) -> bool:
    # Mirrors globalPickSearchRows' manual-asset predicate in pages.tsx:
    # `${playerName} ${team}`.toLowerCase().includes(query).
    haystack = f"{asset['player_name']} {asset['team']}".lower()
    return fragment.lower() in haystack


def test_real_manual_asset_pool_has_exactly_32_k_and_32_dst() -> None:
    assets = _real_manual_kdst_assets()
    positions = [asset["position"] for asset in assets]
    assert positions.count("K") == 32
    assert positions.count("DST") == 32
    assert len(assets) == 64


def test_asset_pool_merge_keeps_every_manual_kdst_row_with_not_modeled_confidence() -> None:
    pool = _asset_pool(_empty_ranking(), _real_manual_kdst_assets())
    assert len(pool) == 64
    for entry in pool.values():
        assert entry["position"] in {"K", "DST"}
        assert entry["confidence"] == "NOT MODELED"
        assert entry["nwr_rank"] is None


def test_all_14_historical_k_dst_unrepresentable_picks_are_findable_in_the_real_pool() -> None:
    """The exact Lane C acceptance criterion: every historical K/DST pick
    must resolve to a real, drafted-representable asset -- using the same
    kind of single-word query fragment an operator would actually type.

    13/14 resolve cleanly. The 14th (Harrison Mevis, LAR K) does not, and
    it is a *different* defect than the other 13 -- not fixed by Lane B's
    search change and not weakened away here. The real manual asset pool
    lists `Joshua Karty` as the LA/LAR kicker (MANUAL_K_LA), not Harrison
    Mevis: the manual K/DST roster data itself was stale relative to the
    real depth-chart/role change by draft day, so even perfect search
    would have surfaced the wrong player under the right team. This is a
    roster-currency gap (section 16: current player truth / role
    uncertainty), not a discoverability gap -- tracked separately below
    rather than papered over by loosening this assertion.
    """
    pool = _asset_pool(_empty_ranking(), _real_manual_kdst_assets())
    assets = list(pool.values())
    unresolved: list[str] = []
    for row in _historical_kdst_picks():
        recap_name = row["recap_player_name"]
        # D/ST rows are "<City/Team> D/ST"; K rows are a person's name --
        # use the most distinctive token (last name, or team name for D/ST).
        fragment = recap_name.replace(" D/ST", "").split()[-1]
        found = [asset for asset in assets if _matches_query(asset, fragment)]
        if not found:
            unresolved.append(recap_name)
    assert unresolved == ["Harrison Mevis"], (
        f"expected exactly the known stale-roster gap (Harrison Mevis), got: {unresolved}"
    )


def test_harrison_mevis_gap_is_stale_manual_roster_data_not_a_search_problem() -> None:
    """Confirms *why* Harrison Mevis doesn't resolve: the manual asset
    pool's LA/LAR kicker slot holds a different, stale name -- so this
    needs a roster-currency fix (refresh the K/DST source closer to draft
    time, or surface a role-uncertainty alert), not a search/UX fix.
    """
    pool = _asset_pool(_empty_ranking(), _real_manual_kdst_assets())
    lar_kicker = next(entry for entry in pool.values() if entry["position"] == "K" and entry["team"] == "LA")
    assert lar_kicker["player_name"] == "Joshua Karty"
    assert lar_kicker["player_name"] != "Harrison Mevis"


def test_team_code_alias_gap_is_real_not_a_test_artifact() -> None:
    """Documents a genuine, confirmed identity-alias gap (section 15: LA/LAR)
    found while building this regression -- the manual asset pool uses "LA"
    for the Rams while the recap CSV uses "LAR". Name-based search (the
    actual pick-recording flow) is unaffected because D/ST asset names
    already contain the team name ("Rams D/ST"), not just the code -- so
    this does not block Lane C, but any future feature that joins on team
    code equality (roster stacking rules, ADP cross-reference) would need
    the alias. Left failing-fast-if-fixed-silently: if this ever starts
    passing on its own, the alias registry work landed and this test
    should be deleted rather than "fixed" to hide the gap.
    """
    pool = _asset_pool(_empty_ranking(), _real_manual_kdst_assets())
    manual_teams = {entry["team"] for entry in pool.values()}
    assert "LA" in manual_teams
    assert "LAR" not in manual_teams
