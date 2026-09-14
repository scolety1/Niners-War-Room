"""Prospective Outcome V1 -- real end-to-end ingestion demonstration
(START_SIT, the one decision type with genuinely real Week 1 2026 data).

Real target: the same read-only Fantasy Gamers Sleeper league (id
`1312983576827920384`, owner `scolety`, roster_id 9) every other real-data
script/test in this repo's recent cycles already uses. Zero writes to
Sleeper: only plain GETs against Sleeper's own public, keyless, read-only
API (`league/{id}`, `league/{id}/matchups/1`).

Writes into an ISOLATED, throwaway `redraft_root` under a local temp
directory -- NEVER the owner's real production AppData store
(`AppData/Local/com.ninerswarroom.redraft`). Re-runnable freely.

What this proves: the full real pipeline -- a real `record_decision_trace`
append, a real `ingest_start_sit_outcome` computation over genuinely real
Week 1 2026 Sleeper data, and a real `record_outcome(..., detail=...)`
append -- works end-to-end against a real, live league, and that the
original recommendation line is provably never mutated by the outcome
append (byte-for-byte checked below).

What this does NOT prove/claim: the `recommendation` this script records is
a MECHANISM-DEMONSTRATION baseline (NWR "recommending" the exact lineup the
owner actually used), not a real historical NWR forecast -- no real
START_SIT trace existed for this league before this pass to attach a real
outcome to (History UI recording of this decision type only began in an
earlier session this same cycle). The OUTCOME half (real points, real
starters) is 100% real. See docs/codex/prospective_outcome_v1/
PROSPECTIVE_OUTCOME_V1.md for the honest accounting of what is/isn't a
"real outcome ingested" this session.

NOT exercised by pytest (real network I/O). Reproducible via:
  `python scripts/build_prospective_outcome_ingestion_v1_startsit_demo.py`
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.in_season_decision_trace_service import (  # noqa: E402
    load_decision_traces,
    record_decision_trace,
    record_outcome,
)
from src.services.prospective_outcome_ingestion_v1_service import (  # noqa: E402
    ingest_start_sit_outcome,
)

LEAGUE_ID = "1312983576827920384"
OWNER_ROSTER_ID = 9
WEEK = 1
PROFILE_ID = "prospective-outcome-v1-startsit-demo"
OUTPUT_PATH = (
    REPO_ROOT / "docs" / "codex" / "prospective_outcome_v1"
    / "startsit_ingestion_demo_v1" / "summary.json"
)


def _get_json(path: str) -> object:
    with urlopen(f"https://api.sleeper.app/v1/{path}", timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    league = _get_json(f"league/{LEAGUE_ID}")
    matchups = _get_json(f"league/{LEAGUE_ID}/matchups/{WEEK}")
    owner_matchup = next(
        (entry for entry in matchups if isinstance(entry, dict) and entry.get("roster_id") == OWNER_ROSTER_ID),
        None,
    )
    if owner_matchup is None:
        raise SystemExit("Real Week 1 matchup data for roster 9 was not found -- nothing to demonstrate.")

    real_full_roster = [str(pid) for pid in owner_matchup.get("players") or []]
    real_actual_starters = [str(pid) for pid in owner_matchup.get("starters") or []]

    with tempfile.TemporaryDirectory(prefix="nwr_prospective_outcome_v1_demo_") as tmp:
        redraft_root = Path(tmp)

        trace = record_decision_trace(
            redraft_root, PROFILE_ID, league_id=LEAGUE_ID, season=int(league.get("season") or 2026),
            week=WEEK, tool="START_SIT", engine_version="prospective_outcome_v1_demo",
            data_versions={"source": "sleeper_real_week1_2026"},
            roster_state_player_ids=real_full_roster,
            # Mechanism-demonstration baseline -- see module docstring.
            recommendation={"projectedTotal": None, "starters": real_actual_starters},
        )

        detail = ingest_start_sit_outcome(
            week=WEEK, recommendation=trace.recommendation,
            roster_state_player_ids=trace.roster_state_player_ids,
            actual_matchup_entry=owner_matchup,
        )

        before_lines = (redraft_root / "decision_traces" / f"{PROFILE_ID}.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()

        updated = record_outcome(
            redraft_root, PROFILE_ID, trace.trace_id,
            outcome="STARTER_MATCHED_RECOMMENDATION" if not detail.recommended_only_ids else "STARTER_DEVIATED",
            detail=detail.to_detail_dict(),
        )

        after_lines = (redraft_root / "decision_traces" / f"{PROFILE_ID}.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        original_line_unchanged = before_lines[0] == after_lines[0]
        reloaded = load_decision_traces(redraft_root, PROFILE_ID)

    summary = {
        "leagueId": LEAGUE_ID,
        "week": WEEK,
        "ownerRosterId": OWNER_ROSTER_ID,
        "realOwnerActualPointsTotal": owner_matchup.get("points"),
        "traceId": trace.trace_id,
        "outcome": updated.outcome,
        "appendOnlyProof": {
            "lineCountBeforeOutcome": len(before_lines),
            "lineCountAfterOutcome": len(after_lines),
            "originalRecommendationLineByteIdentical": original_line_unchanged,
        },
        "reloadedRecordCount": len(reloaded),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
