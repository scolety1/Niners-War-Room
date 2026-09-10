"""NWR Overnight V3 strategic-model-validation resume, section 1:
cross-worktree walk-forward harness -- BRIDGE WORKER (runs inside THIS
branch's own venv/process, never the historical worktree's).

This is the "minimum compatibility adapter/serialization bridge" the
directive asks for, in place of a live cross-import of the historical
worktree's diverged `LeagueProfile`/`RankingResult` dataclass lineage
into this branch's process (or vice versa) -- the exact blocker the
prior pass hit and correctly declined to force.

Contract: invoked once per real historical draft PICK by the historical
worktree's own `run_historical_draft_replay` (via a small owner-strategy
closure in `run_mru_walk_forward_v2.py`, executed with THIS branch's
`.venv` python as a subprocess). Reads one JSON request from
`sys.argv[1]`, writes one JSON response to `sys.argv[2]`. The request
carries only PLAIN DATA -- player rows (player_id/player_name/position/
team/overall_rank/replacement_adjusted_value/confidence, already
computed by the historical worktree's own `generate_rankings` via its
`historical_ranking_bridge_service`, field-for-field identical in name
to this branch's `RedraftRankingRow`), a roster-slot config, and the
current pick's available/rostered player-id lists. Nothing about the
historical worktree's own Python types crosses the process boundary --
only the already-shared, human-legible ranking-row schema both branches
independently compute from the same original lineage.

This worker calls THIS branch's real, unmodified
`marginal_roster_utility` (REFERENCE, v1) or `marginal_roster_utility_v2`
(CHALLENGER) -- never a re-derivation -- against a `LeagueProfile`/
`RankingResult` it constructs NATIVELY in this branch's own process
(no cross-import needed to build them; they are plain dataclasses this
branch already owns).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.redraft_roster_legality_service import evaluate_draft_pick_legality
from src.services.shadow_numeric_authorities_service import (
    marginal_roster_utility,
    marginal_roster_utility_v2,
)

STRATEGY_FNS = {
    "MRU_V1_BRIDGE": marginal_roster_utility,
    "MRU_V2_BRIDGE": marginal_roster_utility_v2,
}


def _build_profile(payload: dict) -> LeagueProfile:
    rs = payload["roster_slots"]
    return LeagueProfile(
        profile_id=f"historical-bridge-{payload['season']}-{payload['team_count']}",
        league_name=f"Historical Bridge {payload['season']}",
        season=int(payload["season"]),
        team_count=int(payload["team_count"]),
        roster=RosterSettings(
            qb=rs.get("qb", 0), rb=rs.get("rb", 0), wr=rs.get("wr", 0), te=rs.get("te", 0),
            flex=rs.get("flex", 0), superflex=rs.get("superflex", 0), k=rs.get("k", 0),
            dst=rs.get("dst", 0), bench_size=rs.get("bench_size", 0),
        ),
        scoring=ScoringSettings(),
        draft=DraftContext(rounds=payload.get("rounds", 6), draft_slot=payload.get("draft_slot")),
    )


def _build_ranking(payload: dict) -> RankingResult:
    rows = tuple(
        RedraftRankingRow(
            overall_rank=int(r["overall_rank"]),
            position_rank=int(r.get("position_rank", 1)),
            player_id=str(r["player_id"]),
            player_name=str(r.get("player_name") or r["player_id"]),
            position=str(r["position"]),
            team=str(r.get("team") or ""),
            projected_points=float(r.get("projected_points", 0.0)),
            replacement_points=float(r.get("replacement_points", 0.0)),
            replacement_adjusted_value=float(r["replacement_adjusted_value"]),
            starter_gap=float(r.get("starter_gap", 0.0)),
            confidence=str(r.get("confidence") or "HISTORICAL_BRIDGE"),
            tier=int(r.get("tier", 1)),
            profile_id=str(payload.get("profile_id", "historical-bridge")),
            profile_name="Historical Bridge",
            source_status="ADMITTED",
            evidence_status="REAL",
            source_as_of=str(payload.get("as_of", "")),
            rookie=bool(r.get("rookie", False)),
        )
        for r in payload["rows"]
    )
    return RankingResult(
        profile=_build_profile(payload),
        rows=rows,
        replacement_levels=(),
        blocked_rows=(),
        generated_at_utc=str(payload.get("as_of", "")),
        projection_sha256="0" * 64,
    )


def main() -> int:
    req_path, resp_path = sys.argv[1], sys.argv[2]
    payload = json.loads(Path(req_path).read_text(encoding="utf-8"))
    cmd = payload["cmd"]

    if cmd == "pick":
        profile = _build_profile(payload)
        ranking = _build_ranking(payload)
        fn = STRATEGY_FNS[payload["strategy"]]
        position_by_id = {row.player_id: row.position for row in ranking.rows}
        pool_ids = set(position_by_id)
        current_ids = tuple(payload["roster_player_ids"])
        # Real production behavior (decision_bundle_service.build_decision_
        # bundle's own docstring): `candidate_player_ids` reaching
        # marginal_roster_utility are "already legality-filtered by the
        # caller" via the canonical `evaluate_draft_pick_legality` authority
        # -- marginal_roster_utility itself has NEVER been evaluated
        # standalone over an unfiltered pool in production. The first
        # version of this bridge omitted this filter and produced a
        # spurious QB-hoarding artifact (v1 drafting QB x4-5 into a 1-QB
        # roster) that does not occur in real usage -- fixed here, disclosed
        # in the harness report.
        roster_counts: dict[str, int] = {}
        for pid in current_ids:
            pos = position_by_id.get(pid)
            if pos:
                roster_counts[pos] = roster_counts.get(pos, 0) + 1
        utilities: dict[str, float] = {}
        best_id: str | None = None
        best_utility: float | None = None
        n_legal = 0
        for candidate_id in payload["available_player_ids"]:
            if candidate_id not in pool_ids:
                continue  # unmodeled/unknown asset -- never guessed at
            candidate_position = position_by_id[candidate_id]
            legality = evaluate_draft_pick_legality(profile, roster_counts, candidate_position)
            if not legality.allowed:
                continue
            n_legal += 1
            result = fn(candidate_id, current_ids, profile, ranking, ())
            utilities[candidate_id] = result.utility
            if best_utility is None or result.utility > best_utility:
                best_utility = result.utility
                best_id = candidate_id
        response = {
            "selected_player_id": best_id,
            "utility": best_utility,
            "n_candidates_evaluated": len(utilities),
            "n_candidates_legal": n_legal,
            "n_candidates_offered": len(payload["available_player_ids"]),
        }
    elif cmd == "pick_greedy_rank":
        # Parity-check mode ONLY: selects purely by lowest overall_rank
        # among available_player_ids, reproducing GREEDY_NWR without
        # calling marginal_roster_utility at all -- used to prove the
        # bridge's serialization/round-trip mechanism itself is faithful
        # (see run_mru_walk_forward_v2.py's parity check), independent
        # of anything marginal_roster_utility-specific.
        rows_by_id = {str(r["player_id"]): r for r in payload["rows"]}
        best_id = None
        best_rank = None
        for candidate_id in payload["available_player_ids"]:
            row = rows_by_id.get(candidate_id)
            if row is None:
                continue
            rank = int(row["overall_rank"])
            if best_rank is None or rank < best_rank:
                best_rank = rank
                best_id = candidate_id
        response = {"selected_player_id": best_id, "utility": None}
    else:
        response = {"error": f"unknown cmd {cmd!r}"}

    Path(resp_path).write_text(json.dumps(response), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
