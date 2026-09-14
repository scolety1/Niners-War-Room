"""History UI V2 (NWR Live Player Intelligence V1, Worker 6) -- real,
live end-to-end verification fixture.

Real target: the same read-only Fantasy Gamers Sleeper league (id
`1312983576827920384`, owner `scolety`, roster_id 9) every other real-data
script in this repo's recent cycles already uses. Zero writes to Sleeper:
only plain GETs against Sleeper's own public, keyless, read-only API.

Writes into an ISOLATED, throwaway `redraft_root` under a local temp
directory -- NEVER the owner's real production AppData store
(`AppData/Local/com.ninerswarroom.redraft`), same convention Worker 5's own
demo script established. A real check of that production store (done as
part of this same pass, not by this script) found ZERO existing
`decision_traces/` ledger for the real Fantasy Gamers profile
(`4c5f04762921420595e4d8c7cda76582`) -- the "Worker F" owner-action capture
UI shipped, but no real recommendation/owner-action has actually been
recorded against it in THIS local install yet. So there is nothing real to
read there this session; this script instead reproduces Worker 5's own
real, live-data mechanism (a real START_SIT trace + a real
`ingest_start_sit_outcome` computation over genuinely real Week 1 2026
Sleeper matchup data) and, this pass, additionally runs the payload all the
way through `_decision_trace_history_event_payload` -- the EXACT function
`desktop_facade.redraft_decision_trace_history()` uses -- so the committed
output here is the literal real JSON shape the new frontend rendering code
consumes, not a hand-typed approximation of it.

What this proves: the real backend pipeline (ingestion -> record_outcome ->
facade payload projection) produces a JSON shape the new
`buildOutcomeDetailSections`/`hasOutcomeDetail` frontend functions render
correctly -- verified separately by
`desktop/apps/redraft/src/decision-history-format.test.ts`'s
"real Fantasy Gamers Week 1 2026 live data" test, which loads this exact
committed file as its fixture.

What this does NOT prove/claim: the `recommendation` recorded here is a
MECHANISM-DEMONSTRATION baseline (see Worker 5's own demo script and
`PROSPECTIVE_OUTCOME_V1.md`), not a genuine historical NWR forecast. The
OUTCOME half (real points, real starters, real per-player scoring) is 100%
real.

NOT exercised by pytest (real network I/O). Reproducible via:
  `python scripts/build_history_ui_v2_live_verification_v1.py`
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.application.desktop_facade import _decision_trace_history_event_payload  # noqa: E402
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
PROFILE_ID = "history-ui-v2-live-verification"
OUTPUT_PATH = (
    REPO_ROOT / "docs" / "codex" / "live_player_intelligence_v1"
    / "history_ui_v2_live_verification_v1" / "real_decision_trace_history_event.json"
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
        raise SystemExit("Real Week 1 matchup data for roster 9 was not found -- nothing to verify against.")

    real_full_roster = [str(pid) for pid in owner_matchup.get("players") or []]
    real_actual_starters = [str(pid) for pid in owner_matchup.get("starters") or []]

    with tempfile.TemporaryDirectory(prefix="nwr_history_ui_v2_live_verification_") as tmp:
        redraft_root = Path(tmp)

        trace = record_decision_trace(
            redraft_root, PROFILE_ID, league_id=LEAGUE_ID, season=int(league.get("season") or 2026),
            week=WEEK, tool="START_SIT", engine_version="history_ui_v2_live_verification_v1",
            data_versions={"source": "sleeper_real_week1_2026"},
            roster_state_player_ids=real_full_roster,
            recommendation={"projectedTotal": None, "starters": real_actual_starters},
        )

        detail = ingest_start_sit_outcome(
            week=WEEK, recommendation=trace.recommendation,
            roster_state_player_ids=trace.roster_state_player_ids,
            actual_matchup_entry=owner_matchup,
        )

        updated = record_outcome(
            redraft_root, PROFILE_ID, trace.trace_id,
            outcome="STARTER_MATCHED_RECOMMENDATION" if not detail.recommended_only_ids else "STARTER_DEVIATED",
            detail=detail.to_detail_dict(),
        )

        reloaded = load_decision_traces(redraft_root, PROFILE_ID)
        assert len(reloaded) == 1 and reloaded[0].trace_id == trace.trace_id

        # The EXACT real JSON payload shape `desktop_facade.
        # redraft_decision_trace_history()` sends the frontend for this row
        # -- not a hand-typed approximation.
        real_event_payload = _decision_trace_history_event_payload(updated)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(real_event_payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(real_event_payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
