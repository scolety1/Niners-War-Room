"""Worker 4 (Work Unit 7) -- shadow-mode consumer plumbing test.

Real target: the read-only Fantasy Gamers Sleeper league (league id
`1312983576827920384`, username `scolety`), imported via the SAME
established, already-existing, read-only import path every other real
Sleeper-league test/script in this repo already uses
(`DesktopBackendFacade.import_sleeper_redraft_profile` ->
`import_sleeper_redraft_profile` -> Sleeper's own public, read-only
`/league`, `/rosters`, `/users` endpoints -- the same ones
`test_redraft_league_switching_isolates_draft_state_and_persists_active_
profile` and `test_sleeper_redraft_owner_service.py` already exercise).
Imports into an ISOLATED, throwaway `redraft_root` under this session's
scratch directory -- never the owner's real production AppData store
(`AppData/Local/com.ninerswarroom.redraft`), so this script can be re-run
freely with zero risk to the real installed app's state. Zero writes to
Sleeper: every Sleeper call this path makes is a plain HTTP GET against
Sleeper's own public, keyless, read-only API (verified by grep -- this repo
has no Sleeper write/POST call anywhere in `sleeper_client_service.py` or
`sleeper_redraft_owner_service.py`).

What this proves (and does NOT prove):
  * PROVES the real end-to-end identity plumbing: real player ids surfaced
    by Home/Lineup/Improve-Team(Waivers)/Waivers/Trades/Player-Drawer's
    real backend reads for this real, live league CAN be resolved into a
    real composed shadow status (built by Work Unit 6's
    `live_player_intelligence_composition_v1_service.py`, still entirely
    unwired to production) without error.
  * PROVES zero side effects: every one of those real facade reads is
    captured BEFORE any shadow-composition activity, then captured AGAIN
    AFTER, and byte-for-byte diffed -- confirming building/comparing the
    shadow status in a separate process path changed NOTHING about what
    these surfaces actually return today (the hard boundary: no live
    recommendation's actual output changes in this pass).
  * Does NOT prove, and does not claim, that the shadow status itself is
    admission-worthy -- that is Work Unit 8's separate, evidence-based
    decision, made in `PRODUCTION_ADMISSION_DECISION_V1.md`, not this
    script.

Writes:
  * `docs/codex/live_player_intelligence_v1/shadow_consumer_test_v1/
    summary.json` -- committed, machine-readable (BEFORE/AFTER hashes,
    identity-resolution counts, the real 3-way comparison table).

NOT exercised by pytest (real network I/O against Sleeper's public API).
Reproducible via:
  `python scripts/build_live_player_intelligence_worker4_shadow_consumer_test_v1.py`
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.application.desktop_facade import DesktopBackendFacade  # noqa: E402
from src.services.live_player_intelligence_composition_v1_service import (  # noqa: E402
    compose_player_availability,
    observations_from_manual_override,
    observations_from_nflverse_depth_chart_shadow,
    observations_from_nflverse_injury_shadow,
    observations_from_sleeper_shadow,
)
from src.services.live_player_intelligence_identity_mapping_v1_service import (  # noqa: E402
    classify_rows,
    common_rows_from_nflverse_depth_charts,
    common_rows_from_nflverse_injuries,
    common_rows_from_sleeper_catalog,
    latest_snapshot_only,
    load_canonical_pool,
)
from src.services.live_player_intelligence_shadow_v1_service import (  # noqa: E402
    build_nflverse_injury_shadow_records,
    build_sleeper_shadow_records,
    match_shadow_records_to_canonical,
)
from src.services.player_availability_status_service import (  # noqa: E402
    load_player_availability_statuses,
)

SHADOW_ROOT = REPO_ROOT / "local_exports" / "live_player_intelligence_shadow_v1"
BENCHMARK_CSV = (
    REPO_ROOT
    / "docs"
    / "codex"
    / "live_player_intelligence_v1"
    / "official_truth_benchmark_v1"
    / "nflverse_week1_2026_official_truth_benchmark.csv"
)
OUTPUT_DIR = REPO_ROOT / "docs" / "codex" / "live_player_intelligence_v1" / "shadow_consumer_test_v1"

LEAGUE_ID = "1312983576827920384"
USERNAME = "scolety"


def _hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


# Real, PRE-EXISTING volatility this repo's own facade already has, entirely
# unrelated to this pass's work -- confirmed by calling the same real facade
# methods twice in a row against the same real league with NO shadow-
# composition code involved at all (see the diagnostic run in this Work
# Unit's evidence): a second call's own `generatedAtUtc`/`lastUpdate` wall-
# clock stamps naturally advance by real elapsed seconds, and
# `servedFromCache` flips true once the first call has warmed a real cache.
# Neither reflects a changed RECOMMENDATION -- both are metadata about WHEN/
# HOW the same answer was computed. Stripped ONLY for the "no substantive
# change" comparison below; the RAW (unstripped) hashes are reported
# alongside, honestly, so this normalization is never silently hiding a
# real difference.
_KNOWN_VOLATILE_KEYS = frozenset(
    {"generatedAtUtc", "lastUpdate", "servedFromCache", "lastGeneratedTimestamp"}
)


def _strip_known_volatile_fields(payload: object) -> object:
    if isinstance(payload, dict):
        return {
            key: _strip_known_volatile_fields(value)
            for key, value in payload.items()
            if key not in _KNOWN_VOLATILE_KEYS
        }
    if isinstance(payload, list):
        return [_strip_known_volatile_fields(item) for item in payload]
    return payload


def _extract_player_ids(payload: object, found: set[str]) -> None:
    """Best-effort real player-id harvesting across a facade payload's real
    shape -- walks every dict/list, collecting any string value found under
    a key that plausibly names a player id, without assuming one fixed
    schema across all seven surfaces (Home/Lineup/Waivers/Trades/etc. each
    shape their own payload)."""

    id_keys = {"playerId", "player_id", "id", "myGivePlayerId", "opponentGivePlayerId"}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in id_keys and isinstance(value, str) and value:
                found.add(value)
            _extract_player_ids(value, found)
    elif isinstance(payload, list):
        for item in payload:
            _extract_player_ids(item, found)


def capture_real_consumer_surfaces(facade: DesktopBackendFacade) -> dict[str, dict]:
    """Real reads backing each of the seven named consumer surfaces. Every
    call here is read-only against this session's isolated profile store
    (and, transitively, Sleeper's public read-only API for roster-shaped
    reads) -- no write path is exercised anywhere in this function."""

    surfaces: dict[str, dict] = {}
    surfaces["Bootstrap_used_by_Home"] = facade.redraft_bootstrap().data
    surfaces["PlayerAvailabilityStatus_authority_used_by_Lineup_Waivers_Trades_PlayerDrawer"] = (
        facade.redraft_player_availability_status().data
    )
    surfaces["Home_weekly_home_actions"] = facade.redraft_weekly_home_actions(week=1).data
    surfaces["Lineup_weekly_lineup"] = facade.redraft_weekly_lineup(week=1).data
    surfaces["MyRoster_used_by_Home_ImproveTeam_AttentionCenter"] = facade.redraft_my_roster().data
    surfaces["FreeAgents_used_by_Waivers_AttentionCenter"] = facade.redraft_free_agents().data
    surfaces["OpponentRosters_used_by_Trades_AttentionCenter"] = facade.redraft_opponent_rosters().data
    surfaces["Waivers_ImproveTeam_REST_OF_SEASON"] = facade.redraft_waivers(mode="REST_OF_SEASON").data
    surfaces["TradeFinder_used_by_Trades"] = facade.redraft_trade_finder().data
    surfaces["LeagueWorkspaceContext_used_by_AttentionCenter"] = facade.redraft_league_workspace_context().data
    surfaces["DataHealth_used_by_AttentionCenter"] = facade.redraft_data_health().data
    return surfaces


def build_real_shadow_composition(repo_root: Path) -> dict[str, dict]:
    """Builds a real composed shadow status for every player this cycle's
    already-fetched local nflverse/Sleeper snapshots + Work Unit 4's manual
    override wrapper can resolve to a canonical id -- the SAME
    already-fetched local files Worker 3 used (no new Sleeper fetch here;
    Sleeper's own 24h refetch policy is respected)."""

    canonical_pool = load_canonical_pool()
    canonical_ids = {row.player_id for row in canonical_pool}

    # nflverse injuries
    with (SHADOW_ROOT / "nflverse_injuries" / "latest" / "injuries_2026.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        injury_rows = list(csv.DictReader(handle))
    nflverse_shadow = build_nflverse_injury_shadow_records(injury_rows)
    nflverse_shadow_matched = match_shadow_records_to_canonical(nflverse_shadow, canonical_pool)
    nflverse_fetched_at = json.loads(
        (SHADOW_ROOT / "nflverse_injuries" / "latest" / "manifest_2026.json").read_text(encoding="utf-8")
    )["fetched_at_utc"]
    nflverse_observations = observations_from_nflverse_injury_shadow(
        nflverse_shadow_matched, fetched_at=nflverse_fetched_at
    )

    # Sleeper catalog (already-fetched local snapshot -- no re-fetch)
    with (SHADOW_ROOT / "sleeper_players" / "latest" / "sleeper_players_snapshot.json").open(
        encoding="utf-8"
    ) as handle:
        sleeper_catalog = json.load(handle)
    sleeper_shadow = build_sleeper_shadow_records(sleeper_catalog)
    sleeper_shadow_matched = match_shadow_records_to_canonical(sleeper_shadow, canonical_pool)
    sleeper_fetch_log = json.loads(
        (SHADOW_ROOT / "sleeper_players" / "latest" / "fetch_log.json").read_text(encoding="utf-8")
    )
    sleeper_fetched_at = sleeper_fetch_log.get("fetched_at_utc")
    sleeper_observations = observations_from_sleeper_shadow(sleeper_shadow_matched, fetched_at=sleeper_fetched_at)

    # nflverse depth charts (latest single-day snapshot)
    with (SHADOW_ROOT / "nflverse_depth_charts" / "latest" / "depth_charts_2026.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        depth_rows_all = list(csv.DictReader(handle))
    depth_rows_latest = latest_snapshot_only(depth_rows_all)
    depth_common_rows = common_rows_from_nflverse_depth_charts(depth_rows_latest)
    depth_classified = classify_rows(depth_common_rows, canonical_pool)
    depth_observations = observations_from_nflverse_depth_chart_shadow(
        depth_common_rows, depth_classified, fetched_at=nflverse_fetched_at
    )

    # Manual overrides (today's real production authority)
    manual_statuses = load_player_availability_statuses(repo_root)
    manual_by_id = {status.player_id: status for status in manual_statuses}

    observations_by_player: dict[str, list] = {}
    for obs_group, matched_records in (
        (nflverse_observations, nflverse_shadow_matched),
        (sleeper_observations, sleeper_shadow_matched),
    ):
        pass  # observations already carry no player id -- re-derive per-player below

    # Re-derive per-player observation lists (FieldObservation itself is
    # player-agnostic; group by the matched record's canonical id instead).
    per_player_observations: dict[str, list] = {pid: [] for pid in canonical_ids}
    for record in nflverse_shadow_matched:
        if not record.matched_canonical_player_id:
            continue
        per_player_observations.setdefault(record.matched_canonical_player_id, [])
        per_player_observations[record.matched_canonical_player_id].extend(
            observations_from_nflverse_injury_shadow((record,), fetched_at=nflverse_fetched_at)
        )
    for record in sleeper_shadow_matched:
        if not record.matched_canonical_player_id:
            continue
        per_player_observations.setdefault(record.matched_canonical_player_id, [])
        per_player_observations[record.matched_canonical_player_id].extend(
            observations_from_sleeper_shadow((record,), fetched_at=sleeper_fetched_at)
        )
    for common_row, classified in zip(depth_common_rows, depth_classified):
        if not classified.matched_canonical_player_id:
            continue
        pid = classified.matched_canonical_player_id
        per_player_observations.setdefault(pid, [])
        per_player_observations[pid].extend(
            observations_from_nflverse_depth_chart_shadow((common_row,), (classified,), fetched_at=nflverse_fetched_at)
        )
    for pid, status in manual_by_id.items():
        per_player_observations.setdefault(pid, [])
        per_player_observations[pid].extend(observations_from_manual_override(status))

    composed_by_id: dict[str, dict] = {}
    for pid, observations in per_player_observations.items():
        if not observations:
            continue
        player_name = next(
            (row.player_name for row in canonical_pool if row.player_id == pid), pid
        )
        composed = compose_player_availability(pid, player_name, observations)
        composed_by_id[pid] = composed.to_dict()
    return composed_by_id


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="nwr_wu7_shadow_consumer_test_") as tmp:
        redraft_root = Path(tmp) / "redraft-store"
        facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=redraft_root)
        import_result = facade.import_sleeper_redraft_profile(league_id=LEAGUE_ID, username=USERNAME)
        profile_id = import_result.data["profile"]["profileId"]
        facade.activate_redraft_profile(profile_id)
        # Warm-up: triggers the one-time bundled-projection-seed install
        # (idempotent after this point) so it cannot bleed into the
        # BEFORE-vs-AFTER zero-side-effect comparison below.
        facade.redraft_bootstrap()

        before_surfaces = capture_real_consumer_surfaces(facade)
        before_hashes = {name: _hash(payload) for name, payload in before_surfaces.items()}
        before_hashes_normalized = {
            name: _hash(_strip_known_volatile_fields(payload)) for name, payload in before_surfaces.items()
        }

        player_ids_seen: set[str] = set()
        for payload in before_surfaces.values():
            _extract_player_ids(payload, player_ids_seen)

        # Build the real composed shadow status entirely OUTSIDE the facade
        # -- proves the identity join works on real production data shapes
        # without touching any facade/consumer code path.
        composed_by_id = build_real_shadow_composition(REPO_ROOT)

        resolvable = sorted(pid for pid in player_ids_seen if pid in composed_by_id)
        unresolvable = sorted(pid for pid in player_ids_seen if pid not in composed_by_id)

        # Real 3-way comparison for players this league actually rosters
        # who ALSO appear in Worker 2's 182-row benchmark (injury-report
        # population) -- likely a small overlap, reported honestly either
        # way.
        with BENCHMARK_CSV.open(newline="", encoding="utf-8") as handle:
            benchmark_rows = list(csv.DictReader(handle))
        benchmark_by_id = {r["matchedCanonicalPlayerId"]: r for r in benchmark_rows if r["matchedCanonicalPlayerId"]}
        manual_statuses = {s.player_id: s.to_dict() for s in load_player_availability_statuses(REPO_ROOT)}

        three_way_comparison = []
        for pid in sorted(player_ids_seen):
            in_benchmark = benchmark_by_id.get(pid)
            composed = composed_by_id.get(pid)
            if not in_benchmark and not composed:
                continue
            three_way_comparison.append(
                {
                    "playerId": pid,
                    "currentProductionStatus": manual_statuses.get(pid),  # None if no manual override exists
                    "composedShadowInjuryDesignation": (
                        composed["fields"]["injury_designation"]["value"] if composed else None
                    ),
                    "composedShadowSource": (
                        composed["fields"]["injury_designation"]["source"] if composed else None
                    ),
                    "officialBenchmarkTruth": (
                        in_benchmark["reportStatusCategory"] if in_benchmark else None
                    ),
                }
            )

        # Re-capture the SAME surfaces AFTER building the shadow composition
        # -- proves zero side effects.
        after_surfaces = capture_real_consumer_surfaces(facade)
        after_hashes = {name: _hash(payload) for name, payload in after_surfaces.items()}
        after_hashes_normalized = {
            name: _hash(_strip_known_volatile_fields(payload)) for name, payload in after_surfaces.items()
        }

        identical_raw = {name: before_hashes[name] == after_hashes[name] for name in before_hashes}
        identical_normalized = {
            name: before_hashes_normalized[name] == after_hashes_normalized[name] for name in before_hashes_normalized
        }

        result = {
            "league": {"leagueId": LEAGUE_ID, "username": USERNAME, "importedProfileId": profile_id},
            "zeroSideEffectProof": {
                "surfaces": list(before_hashes),
                "beforeHashesRaw": before_hashes,
                "afterHashesRaw": after_hashes,
                "allIdenticalRaw": all(identical_raw.values()),
                "perSurfaceIdenticalRaw": identical_raw,
                "note": (
                    "RAW hashes include real, pre-existing, ALREADY-PRESENT volatility unrelated to "
                    "this pass's work: generatedAtUtc/lastUpdate wall-clock stamps naturally advance "
                    "between two real calls, and servedFromCache flips true once a real cache warms "
                    "-- confirmed by calling these same facade methods twice with ZERO shadow-"
                    "composition code involved at all. The NORMALIZED hashes below strip only those "
                    "documented volatile keys and are the real, honest zero-side-effect proof."
                ),
                "beforeHashesNormalized": before_hashes_normalized,
                "afterHashesNormalized": after_hashes_normalized,
                "allIdenticalNormalized": all(identical_normalized.values()),
                "perSurfaceIdenticalNormalized": identical_normalized,
            },
            "identityPlumbing": {
                "distinctPlayerIdsSeenAcrossSurfaces": len(player_ids_seen),
                "resolvableIntoComposedShadowStatus": len(resolvable),
                "unresolvable": len(unresolvable),
                "resolutionRatio": (
                    round(len(resolvable) / len(player_ids_seen), 4) if player_ids_seen else None
                ),
                "sampleResolvableIds": resolvable[:10],
                "sampleUnresolvableIds": unresolvable[:10],
            },
            "threeWayComparison": {
                "note": (
                    "Rows where either the real Fantasy Gamers roster league's own real players "
                    "overlap Worker 2's real 182-row Week-1 official injury-report benchmark, OR a "
                    "real composed shadow injury_designation exists for them. Recorded for "
                    "disclosure only -- nothing here is acted on or wired into any recommendation."
                ),
                "rows": three_way_comparison,
            },
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
