"""Trade Package Quality Benchmark V1 -- real-data runner (NWR Prospective
Outcomes V1, Work Unit 16).

Rubric: `docs/codex/prospective_outcomes_v1/TRADE_PACKAGE_QUALITY_
BENCHMARK_V1.md`. This script does not modify `trade_package_search_
service.py`, `redraft_trade_analysis_service.py`, or any ranking/scoring
module -- it only calls the real, unmodified `search_win_win_packages`/
`search_target_player_packages`/`search_improve_position_packages`
functions and measures the output.

READ-ONLY, twice over:
  * The real NWR ranking is loaded from the owner's real AppData Redraft
    profile (`4c5f04762921420595e4d8c7cda76582`, "Fantasy Gamers") via
    plain `load_profile`/`load_projection_snapshot`/`generate_rankings`
    calls -- nothing is ever written back to that root. No facade
    instance is constructed (the facade's own `redraft_trade_package_
    search` would additionally append a real decision trace; this script
    deliberately bypasses the facade and calls the search functions
    directly so ZERO local writes happen anywhere, in addition to zero
    Sleeper writes).
  * Sleeper reads are plain `urlopen` GETs against the public, unauthenticated
    API (`league/{id}/rosters`, `/users`, `players/nfl`) -- the same
    real, read-only Fantasy Gamers league (id `1312983576827920384`,
    owner `scolety`) every other real-data script in this cycle uses.

Also runs the same rubric against a clearly-labeled SYNTHETIC 10-team
league fixture (deterministic, not real player data) for a larger
candidate sample -- never blended with the real-league numbers.

Output: `docs/codex/prospective_outcomes_v1/trade_package_quality_
benchmark_v1/results.json`. Reproducible via:
  `python scripts/run_trade_package_quality_benchmark_v1.py`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.current_player_status_overrides_service import (  # noqa: E402
    apply_status_overrides_to_ranking,
    load_status_overrides,
)
from src.services.fantasypros_kdst_consensus_service import sleeper_opponent_rosters  # noqa: E402
from src.services.redraft_engine_v1_service import (  # noqa: E402
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
    generate_rankings,
    load_profile,
    load_projection_snapshot,
    projection_snapshot_path,
)
from src.services.trade_package_quality_benchmark_v1_service import (  # noqa: E402
    measure_latency,
    run_trade_package_quality_benchmark,
)
from src.services.trade_package_search_service import (  # noqa: E402
    search_improve_position_packages,
    search_target_player_packages,
    search_win_win_packages,
)
from src.services.waiver_engine_service import resolve_roster_canonical_ids  # noqa: E402

REAL_APPDATA_REDRAFT_ROOT = Path.home() / "AppData" / "Local" / "com.ninerswarroom.redraft" / "state" / "redraft"
REAL_PROFILE_ID = "4c5f04762921420595e4d8c7cda76582"  # "Fantasy Gamers", provider=sleeper
REAL_LEAGUE_ID = "1312983576827920384"
REAL_TARGET_PLAYER_SLEEPER_ID = "10859"  # Sam LaPorta (TE, roster 2) -- real starter at owner's real thin position
REAL_IMPROVE_POSITION = "TE"

OUTPUT_PATH = (
    REPO_ROOT / "docs" / "codex" / "prospective_outcomes_v1"
    / "trade_package_quality_benchmark_v1" / "results.json"
)


def _sleeper_get(path: str) -> object:
    with urlopen(f"https://api.sleeper.app/v1/{path}", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _load_real_ranking() -> tuple[LeagueProfile, RankingResult]:
    profile = load_profile(REAL_APPDATA_REDRAFT_ROOT, REAL_PROFILE_ID)
    snapshot = load_projection_snapshot(
        projection_snapshot_path(REAL_APPDATA_REDRAFT_ROOT, profile.season),
        season=profile.season, require_manifest=True,
    )
    ranking = generate_rankings(profile, snapshot)
    ranking = apply_status_overrides_to_ranking(ranking, load_status_overrides(REPO_ROOT))
    if ranking.errors:
        raise SystemExit(f"Real ranking unavailable: {ranking.errors}")
    return profile, ranking


def _ranking_payloads(ranking: RankingResult) -> list[dict]:
    return [
        {
            "playerId": row.player_id, "playerName": row.player_name, "position": row.position,
            "team": row.team,
        }
        for row in ranking.rows
    ]


def _run_real_league() -> tuple[list[dict], list[str]]:
    profile, ranking = _load_real_ranking()
    ranking_rows = _ranking_payloads(ranking)

    rosters = _sleeper_get(f"league/{REAL_LEAGUE_ID}/rosters")
    users = _sleeper_get(f"league/{REAL_LEAGUE_ID}/users")
    players = _sleeper_get("players/nfl")

    own_user = next(
        (u for u in users if str(u.get("username") or "") == "scolety" or str(u.get("display_name") or "") == "scolety"),
        None,
    )
    if own_user is None:
        raise SystemExit("Real owner user (scolety) not found in the real Fantasy Gamers league.")
    owner_user_id = str(own_user["user_id"])
    own_roster = next(r for r in rosters if str(r.get("owner_id") or "") == owner_user_id)
    own_sleeper_ids = [str(pid) for pid in own_roster.get("players") or []]
    own_resolved = resolve_roster_canonical_ids(
        roster_sleeper_player_ids=own_sleeper_ids, players_catalog=players, ranking_rows=ranking_rows,
    )
    # Real, disclosed data-coverage gap found live while running this
    # script: the search operates on the CANONICAL (identity-resolved)
    # roster, not the raw Sleeper roster -- K/DST are never NWR-projected
    # (by design, unrelated to this pass) and a real identity-match gap
    # this pass found (a rostered WR not present in the current ranking
    # pool) both drop out here. Using the RAW Sleeper roster size as
    # "before" size (this script's own first draft) produced 8 false
    # roster-consolidation-legality "violations" that were actually a
    # measurement-script bug, not a real generator defect -- fixed by
    # using the same canonical count the search itself uses.
    notes: list[str] = []
    if own_resolved.unmatched_sleeper_player_ids:
        note = (
            f"{len(own_resolved.unmatched_sleeper_player_ids)} of the owner's real rostered Sleeper "
            f"players did not resolve to the canonical ranking pool: "
            f"{list(own_resolved.unmatched_sleeper_player_ids)} (K/DST are never NWR-projected by "
            "design; any other id here is a real identity-match gap, not fabricated)."
        )
        notes.append(note)
        print(f"NOTE: {note}")

    opponent_rows = sleeper_opponent_rosters(
        rosters=rosters, users=users, players=players, owner_user_id=owner_user_id,
    )
    opponents: list[dict] = []
    opponent_roster_size_before_by_id: dict[str, int] = {}
    for opponent in opponent_rows:
        opp_sleeper_ids = [str(row["sleeperPlayerId"]) for row in opponent["players"]]
        opp_resolved = resolve_roster_canonical_ids(
            roster_sleeper_player_ids=opp_sleeper_ids, players_catalog=players, ranking_rows=ranking_rows,
        )
        opponents.append({
            "rosterId": opponent["rosterId"], "teamName": opponent["teamName"],
            "canonicalIds": opp_resolved.canonical_player_ids,
            "names": opp_resolved.player_names_by_canonical_id,
            "positions": opp_resolved.player_positions_by_canonical_id,
        })
        # Canonical count, matching what the search itself operates on --
        # see the note above `own_resolved` for why this must not be the
        # raw Sleeper roster size.
        opponent_roster_size_before_by_id[opponent["rosterId"]] = len(opp_resolved.canonical_player_ids)

    target_resolved = resolve_roster_canonical_ids(
        roster_sleeper_player_ids=[REAL_TARGET_PLAYER_SLEEPER_ID], players_catalog=players,
        ranking_rows=ranking_rows,
    )
    if not target_resolved.canonical_player_ids:
        raise SystemExit("Real TARGET_PLAYER identity could not be resolved against the real ranking pool.")
    target_player_id = target_resolved.canonical_player_ids[0]

    search_kwargs = dict(
        my_roster_canonical_ids=own_resolved.canonical_player_ids,
        my_player_names=own_resolved.player_names_by_canonical_id,
        my_player_positions=own_resolved.player_positions_by_canonical_id,
        opponents=opponents, profile=profile, ranking=ranking, manual_assets=[],
    )

    reports = []
    for label, mode_call in (
        ("REAL_FANTASY_GAMERS_FIND_WIN_WIN", lambda: search_win_win_packages(**search_kwargs)),
        (
            "REAL_FANTASY_GAMERS_TARGET_PLAYER_LAPORTA",
            lambda: search_target_player_packages(target_player_id=target_player_id, **search_kwargs),
        ),
        (
            "REAL_FANTASY_GAMERS_IMPROVE_POSITION_TE",
            lambda: search_improve_position_packages(position=REAL_IMPROVE_POSITION, **search_kwargs),
        ),
    ):
        result, elapsed = measure_latency(mode_call)
        report = run_trade_package_quality_benchmark(
            result, label=label, owner_roster_size_before=len(own_resolved.canonical_player_ids),
            opponent_roster_size_before_by_id=opponent_roster_size_before_by_id,
            profile=profile, elapsed_seconds=elapsed,
        )
        reports.append(report.to_dict())
    return reports, notes


# ---------------------------------------------------------------------------
# Synthetic fixture (clearly labeled -- not real player data).
# ---------------------------------------------------------------------------


def _row(player_id, name, position, value, rank):
    return RedraftRankingRow(
        rank, rank, player_id, name, position, "TST", value, 0, value, 0,
        "HIGH", 1, "fixture", "Fixture", "GOVERNED", "AVAILABLE", "2026-09-01", False,
    )


def _synthetic_profile() -> LeagueProfile:
    return LeagueProfile(
        profile_id="synthetic-fixture-league", league_name="Synthetic Fixture League", season=2026,
        # bench_size=9 -> total roster cap 16, matching this fixture's real
        # built roster size (2 QB + 5 RB + 6 WR + 3 TE = 16) exactly -- a
        # roster built OVER its own league's cap would make every trade
        # illegal by construction (found and fixed live while running this
        # script; see the ledger).
        team_count=10, roster=RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, k=0, dst=0, bench_size=9),
        scoring=ScoringSettings(reception=1), draft=DraftContext(rounds=15, draft_slot=5),
        practical_mode=True, provider="sleeper", provider_league_id="synthetic-lg1",
    )


def _build_synthetic_league(num_opponents: int = 9):
    rows = []
    idx = 0

    def add(prefix, position, base_value, count):
        nonlocal idx
        ids = []
        for i in range(count):
            player_id = f"{prefix}-{position.lower()}{i}"
            value = max(5.0, base_value - i * 17.0)
            rows.append(_row(player_id, f"{prefix} {position}{i}", position, value, idx))
            ids.append(player_id)
            idx += 1
        return ids

    def build_roster(prefix):
        ids = []
        ids += add(prefix, "QB", 260, 2)
        ids += add(prefix, "RB", 230, 5)
        ids += add(prefix, "WR", 220, 6)
        ids += add(prefix, "TE", 110, 3)
        return ids

    my_ids = build_roster("my")
    opponents = []
    for opp_num in range(num_opponents):
        prefix = f"opp{opp_num}"
        opp_ids = build_roster(prefix)
        opponents.append({"rosterId": str(opp_num + 2), "teamName": f"Team {opp_num + 2}", "canonicalIds": opp_ids})

    profile = _synthetic_profile()
    ranking = RankingResult(profile, tuple(rows), (), (), "2026-09-01T00:00:00+00:00", "fixture")
    rows_by_id = {row.player_id: row for row in rows}

    def names_positions(ids):
        return (
            {pid: rows_by_id[pid].player_name for pid in ids},
            {pid: rows_by_id[pid].position for pid in ids},
        )

    my_names, my_positions = names_positions(my_ids)
    for opponent in opponents:
        names, positions = names_positions(opponent["canonicalIds"])
        opponent["names"] = names
        opponent["positions"] = positions
    return profile, ranking, my_ids, my_names, my_positions, opponents


def _run_synthetic_fixture() -> list[dict]:
    profile, ranking, my_ids, my_names, my_positions, opponents = _build_synthetic_league()
    opponent_roster_size_before_by_id = {o["rosterId"]: len(o["canonicalIds"]) for o in opponents}
    search_kwargs = dict(
        my_roster_canonical_ids=my_ids, my_player_names=my_names, my_player_positions=my_positions,
        opponents=opponents, profile=profile, ranking=ranking, manual_assets=[],
    )
    result, elapsed = measure_latency(lambda: search_win_win_packages(**search_kwargs))
    report = run_trade_package_quality_benchmark(
        result, label="SYNTHETIC_FIXTURE_FIND_WIN_WIN", owner_roster_size_before=len(my_ids),
        opponent_roster_size_before_by_id=opponent_roster_size_before_by_id, profile=profile,
        elapsed_seconds=elapsed,
    )
    return [report.to_dict()]


def main() -> None:
    real_reports, real_notes = _run_real_league()
    synthetic_reports = _run_synthetic_fixture()
    summary = {
        "realLeagueId": REAL_LEAGUE_ID,
        "realProfileId": REAL_PROFILE_ID,
        "notes": real_notes,
        "reports": real_reports + synthetic_reports,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
