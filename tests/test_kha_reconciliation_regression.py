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
import re
import unicodedata
from pathlib import Path

from src.services.redraft_draft_room_v1_service import (
    AdpSnapshot,
    _asset_pool,
    apply_catch_up_paste,
    load_room_state,
    preview_catch_up_paste,
    start_draft_room,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RosterSettings,
    ScoringSettings,
)
from src.services.udk_unmodeled_skill_asset_service import (
    merge_manual_assets,
    parse_udk_unmatched_skill_assets,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "kha_real_draft_2026"


def _empty_ranking() -> RankingResult:
    return RankingResult(None, (), (), (), "", "")  # type: ignore[arg-type]


def _real_manual_kdst_assets() -> list[dict[str, str]]:
    payload = json.loads(
        (FIXTURE_DIR / "live_manual_kdst_assets_64.json").read_text(encoding="utf-8")
    )
    return payload["assets"]


def _historical_kdst_picks() -> list[dict[str, str]]:
    with (FIXTURE_DIR / "RECONCILIATION_LEDGER.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    picks = [row for row in rows if row["classification"] == "K_DST_UNREPRESENTABLE"]
    assert len(picks) == 14, (
        f"expected 14 historical K_DST_UNREPRESENTABLE rows, found {len(picks)}"
    )
    return picks


def _historical_missing_player_picks() -> list[dict[str, str]]:
    with (FIXTURE_DIR / "RECONCILIATION_LEDGER.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    picks = [row for row in rows if row["classification"] == "OWNER_PLACEHOLDER_FOR_MISSING_PLAYER"]
    assert len(picks) == 5, (
        f"expected 5 historical OWNER_PLACEHOLDER_FOR_MISSING_PLAYER rows, found {len(picks)}"
    )
    return picks


def _normalize_command_search(value: str) -> str:
    # Mirrors normalizeCommandSearch in desktop/packages/ui/src/components.tsx
    # (NFKD-decompose, strip combining marks, lowercase, strip non-alnum) --
    # globalPickSearchRows in pages.tsx now uses that same helper, so this
    # test's predicate must match the real production behavior, not a
    # plain .lower() substring check.
    decomposed = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", stripped.lower())


def _matches_query(asset: dict[str, str], fragment: str) -> bool:
    haystack = _normalize_command_search(f"{asset['player_name']} {asset['team']}")
    return _normalize_command_search(fragment) in haystack


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
    lar_kicker = next(
        entry for entry in pool.values() if entry["position"] == "K" and entry["team"] == "LA"
    )
    assert lar_kicker["player_name"] == "Joshua Karty"
    assert lar_kicker["player_name"] != "Harrison Mevis"


def test_all_5_historical_missing_player_picks_are_findable_once_udk_assets_are_merged_in() -> None:
    """Lane C acceptance for OWNER_PLACEHOLDER_FOR_MISSING_PLAYER: after
    merging the UDK-sourced unmodeled-skill-player assets
    (udk_unmodeled_skill_asset_service) into the manual asset pool and
    running the real _asset_pool merge, every one of the 5 historical
    missing-player picks must resolve to a real, drafted-representable
    asset -- unlike before this lane's work, where they existed in no pool
    at all (neither ranked nor manual)."""
    udk_rows = parse_udk_unmatched_skill_assets(
        FIXTURE_DIR / "udk_skill_position_snapshot_with_identity_status.csv"
    )
    manual_assets = merge_manual_assets(_real_manual_kdst_assets(), udk_rows)
    pool = _asset_pool(_empty_ranking(), manual_assets)
    assets = list(pool.values())
    unresolved: list[str] = []
    for row in _historical_missing_player_picks():
        recap_name = row["recap_player_name"]
        fragment = recap_name.split()[-1].rstrip(".")
        found = [asset for asset in assets if fragment.lower() in asset["player_name"].lower()]
        if not found:
            unresolved.append(recap_name)
    assert not unresolved, (
        f"historical missing-player picks not found even after UDK merge: {unresolved}"
    )


def test_missing_player_assets_do_not_shadow_or_conflict_with_kdst() -> None:
    udk_rows = parse_udk_unmatched_skill_assets(
        FIXTURE_DIR / "udk_skill_position_snapshot_with_identity_status.csv"
    )
    kdst = _real_manual_kdst_assets()
    merged = merge_manual_assets(kdst, udk_rows)
    assert len(merged) == len(kdst) + len(udk_rows)
    pool = _asset_pool(_empty_ranking(), merged)
    assert len(pool) == len(merged)
    positions = {entry["position"] for entry in pool.values()}
    assert positions == {"K", "DST", "QB", "RB", "WR", "TE"}


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


def test_all_14_historical_k_dst_picks_resolve_against_the_current_udk_source() -> None:
    """Section 1B of the Saturday NWR PURE release-candidate wave: close
    the 13/14 -> 14/14 gap using a CURRENT K/DST source
    (udk_kdst_snapshot_20260902.csv, verified byte-identical to the
    already-correct UDK export -- the stale entry was in the real
    live-draft-night manual_assets file, never in this source), not by
    hand-patching the historical evidence fixture.
    """
    from src.services.udk_unmodeled_skill_asset_service import parse_udk_kdst_snapshot

    current_kdst = parse_udk_kdst_snapshot(FIXTURE_DIR / "udk_kdst_snapshot_20260902.csv")
    pool = _asset_pool(_empty_ranking(), current_kdst)
    assets = list(pool.values())
    unresolved: list[str] = []
    for row in _historical_kdst_picks():
        recap_name = row["recap_player_name"]
        fragment = recap_name.replace(" D/ST", "").split()[-1]
        found = [asset for asset in assets if _matches_query(asset, fragment)]
        if not found:
            unresolved.append(recap_name)
    assert not unresolved, f"historical K/DST picks not found in the CURRENT pool: {unresolved}"


def _empty_adp(profile_id: str) -> AdpSnapshot:
    return AdpSnapshot(profile_id, "", "ppr", 12, "", "", "", (), ())


def test_catch_up_mode_resolves_all_35_real_kha_tail_picks_unambiguously(tmp_path: Path) -> None:
    """Acceptance test from docs/codex/CATCH_UP_MODE_CONTRACT_20260903.md:
    paste the 35 real KHA tail player names (classification NO_LIVE_RECORD
    -- the real picks 158-192, entered from the recap after live capture
    stopped) in real recap order and confirm every one resolves
    unambiguously and applies without any invented data.

    This does not replay the full 192-pick draft against the real KHA team
    order/round structure (that is the separate, larger section-29 KHA
    replay regression, not yet built); it isolates catch-up mode's own
    identity-resolution and apply path -- the actual new code this test
    exists to prove -- against real evidence, in a fresh room sized only
    for these 35 picks."""
    with (FIXTURE_DIR / "RECONCILIATION_LEDGER.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    tail = sorted(
        (row for row in rows if row["classification"] == "NO_LIVE_RECORD"),
        key=lambda row: int(row["recap_overall_pick"]),
    )
    assert len(tail) == 35

    manual_assets = [
        {
            "player_id": f"kha-tail:{index}",
            "player_name": row["recap_player_name"],
            "position": "DST" if row["recap_position"] == "D/ST" else row["recap_position"],
            "team": row["recap_nfl_team"],
            "authority": "REAL_KHA_RECAP_EVIDENCE",
        }
        for index, row in enumerate(tail)
    ]
    profile = LeagueProfile(
        "kha-tail-catchup-test",
        "KHA Tail Catch-Up Test",
        2026,
        12,
        RosterSettings(k=1, dst=1, bench_size=6),
        ScoringSettings(reception=1),
        DraftContext(rounds=3, draft_slot=1),  # 12 * 3 = 36 >= 35 target slots
    )
    ranking = RankingResult(profile, (), (), (), "2026-08-17T00:00:00+00:00", "kha-tail-fixture")
    adp = _empty_adp(profile.profile_id)
    start_draft_room(
        tmp_path, profile, ranking, manual_assets, adp, owner_slot=1, mode="LIVE_READ_ONLY"
    )

    paste = "\n".join(row["recap_player_name"] for row in tail)
    preview = preview_catch_up_paste(tmp_path, profile, ranking, manual_assets, paste=paste)
    assert preview["overflowNames"] == []
    assert [row["status"] for row in preview["rows"]] == ["MATCHED"] * 35
    assert preview["readyToApply"] is True

    applied = apply_catch_up_paste(tmp_path, profile, ranking, manual_assets, paste=paste)
    assert len(applied["applied"]) == 35

    state = load_room_state(tmp_path, profile, ranking, manual_assets)
    assert [pick["player_name"] for pick in state["picks"]] == [
        row["recap_player_name"] for row in tail
    ]
    assert all(pick["actor"] == "OWNER_CATCH_UP" for pick in state["picks"])
    assert all(pick["selection_behavior"] == "CATCH_UP_PASTE_EVENT" for pick in state["picks"])
