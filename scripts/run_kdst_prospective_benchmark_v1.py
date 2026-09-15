"""K/DST Prospective Benchmark V1 -- real Week 1 2026 data population (NWR
Prospective Outcomes V1, Work Unit 17).

Design: `docs/codex/prospective_outcomes_v1/KDST_PROSPECTIVE_BENCHMARK_V1.md`
(read first -- documents a real, mechanical DST identity-matching defect
this cycle found in `fantasypros_kdst_consensus_service.py`, disclosed but
NOT fixed here, per the hard boundary).

READ-ONLY: every network call is a plain, public, keyless/API-keyed GET
(Sleeper's own public API; FantasyPros via the owner's already-configured
`NWR_FANTASYPROS_API_KEY`, the SAME real client
`fantasypros_kdst_consensus_service.FantasyProsConsensusClient` the live
app already uses). Nothing is written to Sleeper, FantasyPros, or the
owner's real AppData store. Output is written only under this repo's own
`docs/codex/prospective_outcomes_v1/kdst_prospective_benchmark_v1/`.

Real target: the real "Fantasy Gamers" Sleeper league (id
`1312983576827920384`, owner `scolety`, roster_id 9) every other real-data
script in this cycle uses. Real week populated: **Week 1 2026 only** --
the one real, fully-COMPLETE week as of this pass (current real NFL week
is 2; Week 2 has not finished). This is a genuinely small, honestly
`PRELIMINARY` sample by design, not an oversight.

Reproducible via: `python scripts/run_kdst_prospective_benchmark_v1.py`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.fantasypros_kdst_consensus_service import (  # noqa: E402
    FantasyProsConsensusClient,
    sleeper_streamer_actions,
)
from src.services.kdst_prospective_benchmark_v1_service import (  # noqa: E402
    build_kdst_benchmark_week_record,
    sleeper_team_code,
    summarize_kdst_benchmark,
)
from src.services.weekly_projection_service import (  # noqa: E402
    build_weekly_projection_rows,
    fetch_sleeper_weekly_projections,
)
from src.services.redraft_engine_v1_service import ScoringSettings  # noqa: E402

LEAGUE_ID = "1312983576827920384"
OWNER_ROSTER_ID = "9"
SEASON = 2026
WEEK = 1

OUTPUT_DIR = REPO_ROOT / "docs" / "codex" / "prospective_outcomes_v1" / "kdst_prospective_benchmark_v1"


def _sleeper_get(path: str) -> object:
    with urlopen(f"https://api.sleeper.app/v1/{path}", timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _replacement_level_current(*, position: str, own_roster_sleeper_ids: list[str], players: dict) -> dict | None:
    """The real player already rostered at this position before any
    streaming move -- read directly from the real roster, never
    fabricated. `None` if the owner rostered no player at this position."""

    for sleeper_id in own_roster_sleeper_ids:
        entry = players.get(str(sleeper_id))
        if not isinstance(entry, dict):
            continue
        raw_position = str(entry.get("position") or "").upper()
        normalized = "DST" if raw_position == "DEF" else raw_position
        if normalized != position:
            continue
        team = str(entry.get("team") or "").upper()
        name = str(entry.get("full_name") or entry.get("search_full_name") or "").strip()
        if position == "DST" and not name and team:
            name = f"{team} D/ST"
        return {"playerId": str(sleeper_id), "playerName": name, "team": team, "ecr": None}
    return None


def _raw_projection_best(
    *, position: str, raw_projections: dict, players: dict, rostered_sleeper_ids: set[str]
) -> dict | None:
    """The real, unrostered K/DST with the HIGHEST real Sleeper `pts_ppr`
    weekly projection -- a genuinely different selection signal than ECR
    rank. Uses `build_weekly_projection_rows` (real, existing module),
    never re-deriving the K/DST scoring rule."""

    result = build_weekly_projection_rows(
        raw_projections=raw_projections, players=players, ranking_rows=(),
        scoring=ScoringSettings(), season=SEASON, week=WEEK, season_type="regular", league_id=LEAGUE_ID,
    )
    candidates = [
        row for row in result.rows
        if row.position == position and row.sleeper_player_id not in rostered_sleeper_ids
        and row.projected_points is not None
    ]
    if not candidates:
        return None
    best = max(candidates, key=lambda row: row.projected_points)
    return {"playerId": best.sleeper_player_id, "playerName": best.player_name, "team": best.team,
            "projectedPoints": best.projected_points}


def _build_week_record(
    *, position: str, consensus_rows, rosters, players, owner_user_id: str,
    own_roster_sleeper_ids: list[str], raw_projections: dict, actual_stats: dict,
) -> tuple[dict, list[str]]:
    notes: list[str] = []
    actions, unresolved = sleeper_streamer_actions(
        consensus_rows, rosters=rosters, players=players, owner_user_id=owner_user_id,
    )
    if position == "DST" and unresolved:
        notes.append(
            f"{len(unresolved)} real Sleeper roster id(s) for {position} did not resolve to a "
            "FantasyPros consensus row this week -- this is the real, disclosed DST identity-"
            "matching defect documented in KDST_PROSPECTIVE_BENCHMARK_V1.md (Sleeper's own DST "
            "catalog entries carry no full_name/search_full_name field), NOT fixed by this pass."
        )
    add_action = next((a for a in actions if a.get("recommendation") == "ADD"), None)
    top_action = add_action or (actions[0] if actions else None)
    nwr_recommendation = (
        {"playerId": None, "playerName": top_action["playerName"], "team": top_action["team"],
         "ecr": top_action["ecr"]}
        if top_action else None
    )
    consensus_rank1 = min(consensus_rows, key=lambda row: row.ecr) if consensus_rows else None
    provider_consensus = (
        {"playerId": None, "playerName": consensus_rank1.player_name, "team": consensus_rank1.team,
         "ecr": consensus_rank1.ecr}
        if consensus_rank1 else None
    )

    # Real Sleeper-id resolution for the NWR/consensus arms: match by real
    # team code (translated JAC->JAX where needed) for DST, by real name
    # match against the players catalog for K -- a small, disclosed,
    # benchmark-local join, never touching the production identity code.
    def _resolve_sleeper_id(arm: dict | None) -> dict | None:
        if arm is None:
            return arm
        team = sleeper_team_code(str(arm.get("team") or ""))
        if position == "DST":
            return {**arm, "playerId": team}
        for sleeper_id, entry in players.items():
            if not isinstance(entry, dict):
                continue
            if str(entry.get("position") or "").upper() != "K":
                continue
            if str(entry.get("full_name") or "").strip() == arm.get("playerName"):
                return {**arm, "playerId": str(sleeper_id)}
        return {**arm, "playerId": None}

    nwr_recommendation = _resolve_sleeper_id(nwr_recommendation)
    provider_consensus = _resolve_sleeper_id(provider_consensus)

    rostered_sleeper_ids = {
        str(pid) for roster in rosters for pid in (roster.get("players") or [])
    }
    raw_projection_best = _raw_projection_best(
        position=position, raw_projections=raw_projections, players=players,
        rostered_sleeper_ids=rostered_sleeper_ids,
    )
    replacement_level = _replacement_level_current(
        position=position, own_roster_sleeper_ids=own_roster_sleeper_ids, players=players,
    )

    record = build_kdst_benchmark_week_record(
        season=SEASON, week=WEEK, position=position, league_id=LEAGUE_ID, owner_roster_id=OWNER_ROSTER_ID,
        nwr_recommendation=nwr_recommendation, provider_consensus_rank1=provider_consensus,
        raw_projection_best=raw_projection_best, replacement_level_current=replacement_level,
        actual_points_by_sleeper_id=actual_stats, notes=notes,
    )
    return record.to_dict(), notes


def main() -> None:
    rosters = _sleeper_get(f"league/{LEAGUE_ID}/rosters")
    users = _sleeper_get(f"league/{LEAGUE_ID}/users")
    players = _sleeper_get("players/nfl")
    own_user = next(
        u for u in users
        if str(u.get("username") or "") == "scolety" or str(u.get("display_name") or "") == "scolety"
    )
    owner_user_id = str(own_user["user_id"])
    own_roster = next(r for r in rosters if str(r.get("owner_id") or "") == owner_user_id)
    own_roster_sleeper_ids = [str(pid) for pid in own_roster.get("players") or []]

    raw_projections = fetch_sleeper_weekly_projections(season=SEASON, week=WEEK)
    actual_stats = _sleeper_get(f"stats/nfl/regular/{SEASON}/{WEEK}")

    client = FantasyProsConsensusClient()
    records = []
    all_notes: list[str] = []
    for position in ("K", "DST"):
        consensus_rows = client.consensus_rankings(season=SEASON, position=position, week=WEEK, scoring="PPR")
        record_dict, notes = _build_week_record(
            position=position, consensus_rows=consensus_rows, rosters=rosters, players=players,
            owner_user_id=owner_user_id, own_roster_sleeper_ids=own_roster_sleeper_ids,
            raw_projections=raw_projections, actual_stats={
                k: (v.get("pts_ppr") if isinstance(v, dict) else None) for k, v in actual_stats.items()
            },
        )
        records.append(record_dict)
        all_notes.extend(notes)

    from src.services.kdst_prospective_benchmark_v1_service import KdstBenchmarkArmResult, KdstBenchmarkWeekRecord

    def _rehydrate(d: dict) -> KdstBenchmarkWeekRecord:
        return KdstBenchmarkWeekRecord(
            season=d["season"], week=d["week"], position=d["position"], league_id=d["leagueId"],
            owner_roster_id=d["ownerRosterId"],
            arms=tuple(
                KdstBenchmarkArmResult(
                    arm=a["arm"], player_id=a["playerId"], player_name=a["playerName"], team=a["team"],
                    source_value=a["sourceValue"], actual_points=a["actualPoints"],
                    data_status=a["dataStatus"], note=a["note"],
                )
                for a in d["arms"]
            ),
            notes=tuple(d["notes"]),
        )

    summary = summarize_kdst_benchmark([_rehydrate(r) for r in records])

    output = {
        "leagueId": LEAGUE_ID, "ownerRosterId": OWNER_ROSTER_ID, "season": SEASON, "week": WEEK,
        "sampleLabel": "PRELIMINARY",
        "notes": all_notes,
        "records": records,
        "summary": summary,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"week_{WEEK:02d}_{SEASON}.json"
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
