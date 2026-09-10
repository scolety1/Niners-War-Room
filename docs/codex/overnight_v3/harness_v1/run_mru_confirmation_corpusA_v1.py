"""NWR V2 PROMOTION CONFIRMATION -- preregistered, extended team-count run.

Governed by docs/codex/overnight_v3/NWR_V2_CONFIRMATION_PREREGISTRATION.md,
filed and committed BEFORE this script was executed. Identical to
`run_mru_walk_forward_v2.py` in every mechanical respect (same bridge,
same seed, same corpus, same parity check) except TEAM_COUNTS is extended
from the prior pass's disclosed-narrowed {10, 12} to the full {8, 10, 12,
16} the frozen corpus supports, per the confirmation directive's explicit
request for 8/10/12/16-team coverage. No other parameter changed. Output
goes to a NEW report file -- the original `mru_walk_forward_v2_report.json`
is left untouched as prior evidence.

--- original module docstring below, preserved for provenance ---

NWR Overnight V3 strategic-model-validation resume, sections 1-2.

Cross-worktree walk-forward harness: runs REFERENCE
(`marginal_roster_utility`, this branch's live-promoted v1) and
CHALLENGER (`marginal_roster_utility_v2`) as the OWNER seat in real,
historical, pick-by-pick snake-draft replays built on top of the
frozen historical-tuning corpus infrastructure
(`work/nwr-full-historical-tuning-v1-20260904`, commit `9132f501` and
its current HEAD `33327ee3` -- read-only; this script writes NOTHING
into that worktree).

Bridge mechanism (the "minimum compatibility adapter" the directive
asks for): this script runs WITH THE HISTORICAL WORKTREE ON sys.path
(so `run_historical_draft_replay`, `build_ranking_result_from_
historical_rows`, etc. are the historical worktree's own, unmodified,
already-tested functions) but the "owner" DraftStrategy closure never
calls this branch's marginal_roster_utility in-process (that would
require importing two independently-diverged `src.services.*` package
trees into one interpreter -- the exact hazard the prior pass declined
to risk). Instead each owner pick shells out to
`mru_bridge_worker.py`, run under THIS branch's OWN `.venv` python as a
subprocess, passing only plain-data JSON (already-computed ranking
rows, roster-slot config, available/rostered player-id lists) -- never
a live cross-import.

PARITY PROOF (must run and pass before any real evaluation is
trusted): reproduces GREEDY_NWR (pick lowest overall_rank) THROUGH the
same bridge mechanism (`mru_bridge_worker.py --cmd pick_greedy_rank`,
which touches none of this branch's marginal_roster_utility code, only
the serialization plumbing) for one fixed (season, team_count,
draft_slot) already present natively in
`.codex-tmp/team_score_v2_multi_league_corpus.json`, and asserts the
resulting roster_player_ids list is IDENTICAL to that corpus's own
native (non-bridged) GREEDY_NWR entry. This proves the bridge's JSON
round trip, point-in-time row serialization, and argmax selection
introduce no distortion -- independent of anything
marginal_roster_utility-specific, which has no pre-existing native
benchmark of its own to compare against.

Scope, disclosed (time-boxed, not exhaustive): all 9 real development
seasons (2012, 2013, 2017, 2018, 2019, 2020, 2021, 2022, 2023 -- same
DEV_SEASONS as the frozen corpus; 2016/2024/2025 never touched) x
team_count in {10, 12} (narrowed from the corpus's own {8, 10, 12, 16}
to keep this pass's real wall-clock bounded -- 8/16-team is a real,
disclosed gap, not silently dropped) x 3 representative draft slots
(first, middle, last) x {REFERENCE, CHALLENGER} = up to 9*2*3*2 = 108
paired replays, each a real 6-round snake draft (this corpus's own
fixed historical roster shape: QB1/RB1/WR1/TE1/FLEX1/BENCH1).
"""

from __future__ import annotations

import csv
import json
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path

HIST_ROOT = Path(
    r"C:\Users\codex-agent\orca\workspaces\Niners-War-Room\nwr-full-historical-tuning-v1"
)
THIS_BRANCH_ROOT = Path(r"C:\NWR\overnight-full-advance-v3")
THIS_VENV_PYTHON = THIS_BRANCH_ROOT / ".venv" / "Scripts" / "python.exe"
WORKER_SCRIPT = THIS_BRANCH_ROOT / "docs/codex/overnight_v3/harness_v1/mru_bridge_worker.py"
SCRATCH = Path(
    r"C:\Users\CODEX-~1\AppData\Local\Temp\claude\C--NWR-Niners-War-Room"
    r"\73e6052b-0875-45e0-8c65-6e7ac0e890f3\scratchpad\mru_bridge"
)
OUT_PATH = THIS_BRANCH_ROOT / "docs/codex/overnight_v3/harness_v1/mru_confirmation_corpusA_v1_report.json"

sys.path.insert(0, str(HIST_ROOT))

from scripts.run_historical_calibration_readiness_v1 import (  # noqa: E402
    _HISTORICAL_ROSTER,
    _HISTORICAL_ROSTER_TOTAL_SLOTS,
    _profile_for_season,
    _reception_points_for_rows,
)
from src.services.draft_strategy_framework_service import (  # noqa: E402
    StrategyDecision,
    StrategyDecisionContext,
    baseline_strategy_registry,
)
from src.services.historical_draft_replay_engine_service import (  # noqa: E402
    run_historical_draft_replay,
)
from src.services.historical_ranking_bridge_service import (  # noqa: E402
    build_ranking_result_from_historical_rows,
)
from src.services.shadow_numeric_authorities_service import (  # noqa: E402
    RosterPlayer,
    optimal_starting_lineup_value,
)

DATASET_PATH = HIST_ROOT / ".codex-tmp/development_dataset/historical_replay_rows.csv"
CORPUS_PATH = HIST_ROOT / ".codex-tmp/team_score_v2_multi_league_corpus.json"
DEV_SEASONS = (2012, 2013, 2017, 2018, 2019, 2020, 2021, 2022, 2023)
TEAM_COUNTS = (8, 10, 12, 16)  # full set, per the confirmation preregistration -- extended from the prior pass's {10, 12}
BASE_SEED = 20260905
ROSTER_SLOTS_DICT = {
    "qb": _HISTORICAL_ROSTER.qb, "rb": _HISTORICAL_ROSTER.rb, "wr": _HISTORICAL_ROSTER.wr,
    "te": _HISTORICAL_ROSTER.te, "flex": _HISTORICAL_ROSTER.flex,
    "superflex": _HISTORICAL_ROSTER.superflex, "k": _HISTORICAL_ROSTER.k,
    "dst": _HISTORICAL_ROSTER.dst, "bench_size": _HISTORICAL_ROSTER.bench_size,
}


def _row_to_dict(row) -> dict:
    if is_dataclass(row):
        return asdict(row)
    return dict(row)


def slots_for(team_count: int) -> tuple[int, ...]:
    """3 representative slots (first, middle, last) -- narrowed from the
    corpus builder's own 4 (first/~1/3/~2/3/last), disclosed."""
    return tuple(sorted({1, max(1, team_count // 2), team_count}))


class BridgeError(RuntimeError):
    pass


def _call_worker(request: dict) -> dict:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    token = f"{time.time_ns()}"
    req_path = SCRATCH / f"req_{token}.json"
    resp_path = SCRATCH / f"resp_{token}.json"
    req_path.write_text(json.dumps(request), encoding="utf-8")
    result = subprocess.run(
        [str(THIS_VENV_PYTHON), str(WORKER_SCRIPT), str(req_path), str(resp_path)],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0 or not resp_path.exists():
        raise BridgeError(f"worker failed rc={result.returncode} stderr={result.stderr[-2000:]}")
    response = json.loads(resp_path.read_text(encoding="utf-8"))
    req_path.unlink(missing_ok=True)
    resp_path.unlink(missing_ok=True)
    if "error" in response:
        raise BridgeError(response["error"])
    return response


def make_bridge_strategy(strategy_key: str, rows_payload: list[dict], profile_payload: dict):
    """Real owner DraftStrategy: every call shells out to
    mru_bridge_worker.py (this branch's own venv) for candidate
    selection. `strategy_key` is 'MRU_V1_BRIDGE', 'MRU_V2_BRIDGE', or
    'GREEDY_RANK_PARITY_CHECK'."""

    def strategy(context: StrategyDecisionContext) -> StrategyDecision:
        start = time.perf_counter()
        base = dict(profile_payload)
        base["rows"] = rows_payload
        base["roster_player_ids"] = list(context.roster_player_ids)
        base["available_player_ids"] = list(context.available_player_ids)
        if strategy_key == "GREEDY_RANK_PARITY_CHECK":
            base["cmd"] = "pick_greedy_rank"
        else:
            base["cmd"] = "pick"
            base["strategy"] = strategy_key
        response = _call_worker(base)
        selected = response.get("selected_player_id")
        elapsed = time.perf_counter() - start
        ranking = (selected,) if selected else ()
        return StrategyDecision(
            strategy_name=strategy_key, strategy_version="bridge-v1",
            selected_player_id=selected, candidate_ranking=ranking,
            decision_metadata={"bridge_response": response}, runtime_seconds=round(elapsed, 4),
        )

    return strategy


def run_one(
    season: int, team_count: int, draft_slot: int, strategy_key: str,
    season_rows: list[dict], realized_by_player: dict[str, float],
) -> dict:
    reception_points = _reception_points_for_rows(season_rows)
    profile = _profile_for_season(season, team_count=team_count, reception_points=reception_points)
    bridge = build_ranking_result_from_historical_rows(
        season_rows, profile, generated_at_utc="2026-09-09T00:00:00Z", source_sha256="0" * 64,
    )
    if not bridge.ranking.ready:
        return {"skipped": "ranking bridge not ready"}
    rows_payload = [
        {
            "player_id": r.player_id, "player_name": r.player_name, "position": r.position,
            "team": r.team, "overall_rank": r.overall_rank, "position_rank": r.position_rank,
            "replacement_adjusted_value": r.replacement_adjusted_value,
            "confidence": r.confidence, "tier": r.tier,
        }
        for r in bridge.ranking.rows
    ]
    profile_payload = {
        "season": season, "team_count": team_count, "draft_slot": draft_slot,
        "roster_slots": ROSTER_SLOTS_DICT, "rounds": _HISTORICAL_ROSTER_TOTAL_SLOTS,
        "as_of": season_rows[0]["draft_date"],
    }
    strategy_fn = make_bridge_strategy(strategy_key, rows_payload, profile_payload)
    receipt = run_historical_draft_replay(
        season=season, team_count=team_count, rounds=_HISTORICAL_ROSTER_TOTAL_SLOTS,
        available_player_ids=bridge.included_player_ids, feature_store=bridge.feature_store,
        as_of=str(season_rows[0]["draft_date"]), owner_slot=draft_slot,
        owner_strategy_name=strategy_key, owner_strategy=strategy_fn, seed=BASE_SEED,
    )
    roster_ids = [
        p.selected_player_id for p in receipt.picks
        if p.team_slot == draft_slot and p.selected_player_id
    ]
    fully_realized = len(roster_ids) == _HISTORICAL_ROSTER_TOTAL_SLOTS and all(
        pid in realized_by_player for pid in roster_ids
    )
    position_by_player = {str(r["player_id"]): str(r["position"]) for r in season_rows}
    oracle_value = None
    if fully_realized:
        realized_players = [
            RosterPlayer(pid, position_by_player.get(pid, "UNKNOWN"), realized_by_player[pid])
            for pid in roster_ids
        ]
        oracle_value = optimal_starting_lineup_value(realized_players, profile)
    position_counts: dict[str, int] = {}
    for pid in roster_ids:
        pos = position_by_player.get(pid, "UNKNOWN")
        position_counts[pos] = position_counts.get(pos, 0) + 1
    return {
        "season": season, "team_count": team_count, "draft_slot": draft_slot,
        "strategy_name": strategy_key, "roster_player_ids": roster_ids,
        "fully_realized": fully_realized, "oracle_realized_optimal_lineup_value": oracle_value,
        "position_counts": position_counts,
        "picks": [
            {
                "pick_number": p.pick_number, "round_number": p.round_number,
                "team_slot": p.team_slot, "selected_player_id": p.selected_player_id,
            }
            for p in receipt.picks if p.team_slot == draft_slot
        ],
    }


def parity_check() -> dict:
    """Runs GREEDY_NWR through the bridge for (season=2019, team_count=10,
    draft_slot=1) and compares roster_player_ids against the corpus's own
    native GREEDY_NWR entry for the identical combination."""
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    native = next(
        (
            o for o in corpus["observations"]
            if o["season"] == 2019 and o["team_count"] == 10 and o["draft_slot"] == 1
            and o["strategy_name"] == "GREEDY_NWR"
        ),
        None,
    )
    if native is None:
        return {"pass": False, "reason": "no native GREEDY_NWR corpus entry found for parity target"}

    with DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    season_rows = [r for r in rows if int(r["season"]) == 2019]
    realized_by_player = {
        str(r["player_id"]): float(r["realized_weekly_points"])
        for r in season_rows if str(r.get("realized_weekly_points") or "").strip()
    }
    bridged = run_one(2019, 10, 1, "GREEDY_RANK_PARITY_CHECK", season_rows, realized_by_player)
    native_ids = native["roster_player_ids"]
    bridged_ids = bridged["roster_player_ids"]
    return {
        "pass": native_ids == bridged_ids,
        "native_roster_player_ids": native_ids,
        "bridged_roster_player_ids": bridged_ids,
        "native_oracle_value": native.get("oracle_realized_optimal_lineup_value"),
        "bridged_oracle_value": bridged.get("oracle_realized_optimal_lineup_value"),
    }


def main() -> int:
    t0 = time.perf_counter()
    print("=== PARITY CHECK ===")
    parity = parity_check()
    print(json.dumps(parity, indent=2, default=str))
    if not parity["pass"]:
        print("PARITY CHECK FAILED -- stopping before real evaluation.")
        OUT_PATH.write_text(
            json.dumps({"parity_check": parity, "observations": []}, indent=2, default=str),
            encoding="utf-8",
        )
        return 1
    print("PARITY CHECK PASSED. Proceeding to real v1/v2 evaluation.\n")

    with DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows_by_season: dict[int, list[dict]] = {}
    for row in rows:
        rows_by_season.setdefault(int(row["season"]), []).append(row)

    observations: list[dict] = []
    skipped: list[dict] = []
    for team_count in TEAM_COUNTS:
        needed = team_count * _HISTORICAL_ROSTER_TOTAL_SLOTS
        for season in DEV_SEASONS:
            season_rows = rows_by_season.get(season, [])
            if len(season_rows) < needed:
                skipped.append({"season": season, "team_count": team_count, "reason": "insufficient players"})
                continue
            realized_by_player = {
                str(r["player_id"]): float(r["realized_weekly_points"])
                for r in season_rows if str(r.get("realized_weekly_points") or "").strip()
            }
            for draft_slot in slots_for(team_count):
                for strategy_key in ("MRU_V1_BRIDGE", "MRU_V2_BRIDGE"):
                    try:
                        obs = run_one(season, team_count, draft_slot, strategy_key, season_rows, realized_by_player)
                    except Exception as exc:  # noqa: BLE001
                        skipped.append({
                            "season": season, "team_count": team_count, "draft_slot": draft_slot,
                            "strategy_name": strategy_key, "reason": f"replay failed: {exc}",
                        })
                        continue
                    observations.append(obs)
            print(f"season={season} team_count={team_count} done "
                  f"({len(observations)} total observations so far, {time.perf_counter()-t0:.1f}s elapsed)")

    report = {
        "parity_check": parity, "dev_seasons": list(DEV_SEASONS), "team_counts": list(TEAM_COUNTS),
        "slots_by_team_count": {tc: list(slots_for(tc)) for tc in TEAM_COUNTS},
        "n_total": len(observations), "n_skipped": len(skipped), "skipped": skipped,
        "observations": observations, "elapsed_seconds": round(time.perf_counter() - t0, 1),
    }
    OUT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}: {len(observations)} observations, {len(skipped)} skipped, "
          f"{time.perf_counter()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
