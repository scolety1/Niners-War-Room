"""NWR V2 PROMOTION CONFIRMATION -- preregistered Superflex sample.

Governed by docs/codex/overnight_v3/NWR_V2_CONFIRMATION_PREREGISTRATION.md,
filed and committed BEFORE this script was executed. The prior pass's own
Superflex evidence (`mru_superflex_smoke_v1.json`) was an undisclosed-
protocol "smoke" of only 2 seasons x 1 slot (2 paired observations),
generated inline and never saved as a standalone driver script. This
script builds a real, reusable, paired Superflex sample across every dev
season the roster shape can support and 3 draft slots (early/mid/late),
using the exact same proven bridge mechanism (`mru_bridge_worker.py`,
parity-proven in `run_mru_walk_forward_v2.py`).

Roster: QB1/SFLEX1/RB2/WR2/TE1/FLEX1/BENCH3 = 11 rounds (matches the
prior smoke's own roster shape exactly). team_count=10 only (matches the
prior smoke and Test 18's real league shape). Same infeasible-season
skip precedent as the bigroster driver (insufficient real players logged
and skipped, not padded).
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
OUT_PATH = THIS_BRANCH_ROOT / "docs/codex/overnight_v3/harness_v1/mru_confirmation_superflex_v1_report.json"

sys.path.insert(0, str(HIST_ROOT))

from scripts.run_historical_calibration_readiness_v1 import _reception_points_for_rows  # noqa: E402
from src.services.draft_strategy_framework_service import (  # noqa: E402
    StrategyDecision,
    StrategyDecisionContext,
)
from src.services.historical_draft_replay_engine_service import (  # noqa: E402
    run_historical_draft_replay,
)
from src.services.historical_ranking_bridge_service import (  # noqa: E402
    build_ranking_result_from_historical_rows,
)
from src.services.redraft_engine_v1_service import (  # noqa: E402
    DraftContext,
    LeagueProfile,
    RosterSettings,
    ScoringSettings,
)
from src.services.shadow_numeric_authorities_service import (  # noqa: E402
    RosterPlayer,
    optimal_starting_lineup_value,
)

DATASET_PATH = HIST_ROOT / ".codex-tmp/development_dataset/historical_replay_rows.csv"
DEV_SEASONS = (2012, 2013, 2017, 2018, 2019, 2020, 2021, 2022, 2023)
TEAM_COUNT = 10
BASE_SEED = 20260905
BIG_ROSTER = RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=1, k=0, dst=0, bench_size=3)
TOTAL_ROUNDS = (
    BIG_ROSTER.qb + BIG_ROSTER.rb + BIG_ROSTER.wr + BIG_ROSTER.te + BIG_ROSTER.flex
    + BIG_ROSTER.superflex + BIG_ROSTER.k + BIG_ROSTER.dst + BIG_ROSTER.bench_size
)
ROSTER_SLOTS_DICT = {
    "qb": BIG_ROSTER.qb, "rb": BIG_ROSTER.rb, "wr": BIG_ROSTER.wr, "te": BIG_ROSTER.te,
    "flex": BIG_ROSTER.flex, "superflex": BIG_ROSTER.superflex, "k": BIG_ROSTER.k,
    "dst": BIG_ROSTER.dst, "bench_size": BIG_ROSTER.bench_size,
}


def _profile_for(season: int, reception_points: float) -> LeagueProfile:
    return LeagueProfile(
        profile_id=f"historical-big-{season}", league_name=f"Historical Big {season}",
        season=season, team_count=TEAM_COUNT, roster=BIG_ROSTER,
        scoring=ScoringSettings(reception=reception_points),
        draft=DraftContext(rounds=TOTAL_ROUNDS, draft_slot=1),
    )


def slots_for() -> tuple[int, ...]:
    return (1, 5, 10)  # early / middle / late, matches Test 18's own slot-5 emphasis


class BridgeError(RuntimeError):
    pass


def _call_worker(request: dict) -> dict:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    token = f"{time.time_ns()}"
    req_path = SCRATCH / f"reqb_{token}.json"
    resp_path = SCRATCH / f"respb_{token}.json"
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
    def strategy(context: StrategyDecisionContext) -> StrategyDecision:
        start = time.perf_counter()
        base = dict(profile_payload)
        base["rows"] = rows_payload
        base["roster_player_ids"] = list(context.roster_player_ids)
        base["available_player_ids"] = list(context.available_player_ids)
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


def run_one(season: int, draft_slot: int, strategy_key: str, season_rows: list[dict], realized_by_player: dict[str, float]) -> dict:
    reception_points = _reception_points_for_rows(season_rows)
    profile = _profile_for(season, reception_points)
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
        "season": season, "team_count": TEAM_COUNT, "draft_slot": draft_slot,
        "roster_slots": ROSTER_SLOTS_DICT, "rounds": TOTAL_ROUNDS,
        "as_of": season_rows[0]["draft_date"],
    }
    strategy_fn = make_bridge_strategy(strategy_key, rows_payload, profile_payload)
    receipt = run_historical_draft_replay(
        season=season, team_count=TEAM_COUNT, rounds=TOTAL_ROUNDS,
        available_player_ids=bridge.included_player_ids, feature_store=bridge.feature_store,
        as_of=str(season_rows[0]["draft_date"]), owner_slot=draft_slot,
        owner_strategy_name=strategy_key, owner_strategy=strategy_fn, seed=BASE_SEED,
    )
    roster_ids = [p.selected_player_id for p in receipt.picks if p.team_slot == draft_slot and p.selected_player_id]
    fully_realized = len(roster_ids) == TOTAL_ROUNDS and all(pid in realized_by_player for pid in roster_ids)
    position_by_player = {str(r["player_id"]): str(r["position"]) for r in season_rows}
    oracle_value = None
    if fully_realized:
        realized_players = [RosterPlayer(pid, position_by_player.get(pid, "UNKNOWN"), realized_by_player[pid]) for pid in roster_ids]
        oracle_value = optimal_starting_lineup_value(realized_players, profile)
    position_counts: dict[str, int] = {}
    for pid in roster_ids:
        pos = position_by_player.get(pid, "UNKNOWN")
        position_counts[pos] = position_counts.get(pos, 0) + 1
    max_single_position = max(position_counts.values()) if position_counts else 0
    return {
        "season": season, "team_count": TEAM_COUNT, "draft_slot": draft_slot,
        "strategy_name": strategy_key, "roster_player_ids": roster_ids,
        "fully_realized": fully_realized, "oracle_realized_optimal_lineup_value": oracle_value,
        "position_counts": position_counts, "max_single_position_count": max_single_position,
        "n_rounds_total": TOTAL_ROUNDS,
    }


def main() -> int:
    t0 = time.perf_counter()
    with DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows_by_season: dict[int, list[dict]] = {}
    for row in rows:
        rows_by_season.setdefault(int(row["season"]), []).append(row)

    observations: list[dict] = []
    skipped: list[dict] = []
    needed = TEAM_COUNT * TOTAL_ROUNDS
    for season in DEV_SEASONS:
        season_rows = rows_by_season.get(season, [])
        if len(season_rows) < needed:
            skipped.append({"season": season, "reason": f"insufficient real players: {len(season_rows)} < {needed}"})
            print(f"SKIP season={season}: {len(season_rows)} < {needed} needed.")
            continue
        realized_by_player = {
            str(r["player_id"]): float(r["realized_weekly_points"])
            for r in season_rows if str(r.get("realized_weekly_points") or "").strip()
        }
        for draft_slot in slots_for():
            for strategy_key in ("MRU_V1_BRIDGE", "MRU_V2_BRIDGE"):
                try:
                    obs = run_one(season, draft_slot, strategy_key, season_rows, realized_by_player)
                except Exception as exc:  # noqa: BLE001
                    skipped.append({"season": season, "draft_slot": draft_slot, "strategy_name": strategy_key, "reason": f"replay failed: {exc}"})
                    continue
                observations.append(obs)
        print(f"season={season} done ({len(observations)} total, {time.perf_counter()-t0:.1f}s elapsed)")

    report = {
        "roster": ROSTER_SLOTS_DICT, "total_rounds": TOTAL_ROUNDS, "team_count": TEAM_COUNT,
        "dev_seasons": list(DEV_SEASONS), "slots": list(slots_for()),
        "n_total": len(observations), "n_skipped": len(skipped), "skipped": skipped,
        "observations": observations, "elapsed_seconds": round(time.perf_counter() - t0, 1),
    }
    OUT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}: {len(observations)} observations, {len(skipped)} skipped, {time.perf_counter()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
