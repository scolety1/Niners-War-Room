"""NWR Overnight V3 strategic closure -- section 8/9.

Real, live 10-team PPR 1QB slot-5 16-round blind draft, policy = ALWAYS
TAKE THE ONE CANONICAL NWR PICK NOW (candidates[0] from the real, live
`redraft_decision_bundle` facade call -- the exact same authority the
banner/row-1/CPU-auto-pick all share). No rescue -- emergency_override
never used; any real error stops the run and is reported, not worked
around.

Uses the freeze V7 governed 2026 snapshot (564 real players, owner-
authorized 2026-09-08, valid_until 2026-10-08), hash-verified reused
from `.codex-tmp/rendered_pass_v2_isolated_store` into a fresh isolated
store (`.codex-tmp/live_blind_draft_v1`) -- never the real owner AppData
install, never the prior session's own profiles/draft boards.
"""
from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, "C:/NWR/overnight-full-advance-v3")

STORE = "C:/NWR/overnight-full-advance-v3/.codex-tmp/live_blind_draft_v1/redraft_v1"
REPO_ROOT = "C:/NWR/overnight-full-advance-v3"
SKILL_CSV = "C:/NWR/overnight-full-advance-v3/sample_data/kha_real_draft_2026/udk_skill_position_snapshot_with_identity_status.csv"
KDST_CSV = "C:/NWR/overnight-full-advance-v3/sample_data/kha_real_draft_2026/udk_kdst_snapshot_20260902.csv"

from src.application.desktop_facade import DesktopBackendFacade, FacadeError

facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=STORE)

created = facade.create_redraft_profile(
    preset_key="10_TEAM_1QB_STANDARD",
    league_name="Overnight V3 Live Blind Draft",
    roster_limits={"WR": 8},
)
profile_id = created.data["profile"]["profileId"]
print("created profile", profile_id)

# Fix scoring to full PPR and set the real draft slot -- the preset
# template is standard scoring; roster/team_count/rounds already match
# (10-team, 1QB, 16 rounds).
profile_payload = created.data["profile"]
updated = facade.update_redraft_profile(
    profile_id,
    league_name="Overnight V3 Live Blind Draft",
    team_count=10,
    roster={
        "qb": 1, "rb": 2, "wr": 2, "te": 1, "flex": 1, "superflex": 0,
        "k": 1, "dst": 1, "benchSize": 7,
    },
    scoring={"reception": 1.0, "passingTd": 4, "interception": -2, "tePremium": 0},
    draft={"rounds": 16, "draftSlot": 5, "replacementMethod": "expected_available", "rosterLimits": {"WR": 8}},
)
print("scoring/roster updated")

facade.activate_redraft_profile(profile_id)

skill_result = facade.import_udk_unmodeled_skill_assets(profile_id=profile_id, csv_path=SKILL_CSV)
print("skill manual assets:", skill_result.data.get("addedCount"), "added, total", len(skill_result.data.get("manualAssets", [])))

with open(KDST_CSV, "r", encoding="utf-8") as f:
    kdst_csv_text = f.read()
kdst_result = facade.import_udk_kdst_snapshot(profile_id=profile_id, csv_text=kdst_csv_text)
print("kdst manual assets:", kdst_result.data.get("addedCount"), "added, total", len(kdst_result.data.get("manualAssets", [])))

start = facade.start_redraft_draft_room(
    profile_id=profile_id, owner_slot=5, seed=20260909, speed="FAST", mode="MOCK",
)
print("draft room started")

owner_picks = []
latencies = []
turn_traces = []
MAX_TURNS = 20  # safety bound -- 16 real owner picks expected

for turn in range(MAX_TURNS):
    t0 = time.perf_counter()
    try:
        bundle_result = facade.redraft_decision_bundle(profile_id=profile_id, speed="FAST")
    except FacadeError as exc:
        print(f"TURN {turn}: FacadeError calling decision bundle: {exc}")
        break
    elapsed = time.perf_counter() - t0
    db = bundle_result.data["decisionBundle"]
    if not db.get("available"):
        print(f"TURN {turn}: decision bundle unavailable: {db.get('reason')}")
        break
    candidates = db.get("candidates", [])
    if not candidates:
        print(f"TURN {turn}: no candidates -- draft likely complete or roster full.")
        break
    top = candidates[0]
    player_id = top["playerId"]
    latencies.append(elapsed)
    illegal_in_top = [c["playerId"] for c in candidates if c.get("rosterLegal") is False]
    turn_trace = {
        "turn": turn, "player_id": player_id, "player_name": top.get("playerName"),
        "position": top.get("position"), "latency_s": round(elapsed, 3),
        "n_candidates": len(candidates),
        "top_candidate_illegal": top.get("rosterLegal") is False,
        "any_illegal_in_top5": any(c.get("rosterLegal") is False for c in candidates[:5]),
    }
    turn_traces.append(turn_trace)
    print(f"TURN {turn}: PICK NOW = {top.get('playerName')} ({top.get('position')})  latency={elapsed:.3f}s  legal={top.get('rosterLegal')}")
    try:
        facade.mark_redraft_player(profile_id=profile_id, player_id=player_id, drafted=True, emergency_override=False)
    except FacadeError as exc:
        print(f"TURN {turn}: FacadeError recording pick {player_id}: {exc}")
        break
    owner_picks.append(top)

print(f"\n=== {len(owner_picks)} owner picks recorded ===")
from collections import Counter
counts = Counter(p.get("position") for p in owner_picks)
print("Position counts:", dict(counts))
print("Illegal top-candidate turns:", sum(1 for t in turn_traces if t["top_candidate_illegal"]))
print("Illegal-in-top-5 turns:", sum(1 for t in turn_traces if t["any_illegal_in_top5"]))
if latencies:
    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)
    print(f"Latency: n={n}  mean={sum(latencies)/n:.3f}s  median={latencies_sorted[n//2]:.3f}s  "
          f"p95={latencies_sorted[min(n-1, int(n*0.95))]:.3f}s  min={latencies_sorted[0]:.3f}s  max={latencies_sorted[-1]:.3f}s  "
          f"first(cold)={latencies[0]:.3f}s")

out_path = "C:/Users/CODEX-~1/AppData/Local/Temp/claude/C--NWR-Niners-War-Room/73e6052b-0875-45e0-8c65-6e7ac0e890f3/scratchpad/live_blind_draft_trace.json"
with open(out_path, "w") as f:
    json.dump({"owner_picks": owner_picks, "turn_traces": turn_traces, "latencies": latencies}, f, indent=2, default=str)
print("wrote", out_path)
