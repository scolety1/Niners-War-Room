"""Prospective Outcomes V1 -- Work Unit 12: the real, callable, idempotent
ingestion-orchestration COMMAND.

A thin CLI wrapper around
`src.services.prospective_outcome_ingestion_orchestrator_v1_service.run_ingestion`
-- all real logic lives in that module (unit-tested, hermetic, no network
I/O in pytest); this script is what a future scheduled job or an on-demand
owner invocation would actually call.

Defaults to the real, read-only Fantasy Gamers Sleeper league (id
`1312983576827920384`, owner `scolety`, roster_id `9`) -- the one real,
confirmed `{league_id: owner_roster_id}` mapping this codebase has (see
`scripts/build_prospective_outcome_ingestion_v1_startsit_demo.py`'s own
precedent). A general, dynamic multi-league resolver is explicitly out of
scope this pass (see the orchestrator module's own docstring / the
LEDGER's open issues) -- pass `--owner-roster-id-map` for any other league.

Zero writes to Sleeper. Every real network call this script makes is a
plain, public, keyless GET (`state/nfl`, `league/{id}/matchups/{week}`) --
the exact same real, already-wired, read-only endpoints every other real
call site in this codebase uses. Real LOCAL writes happen only to the
`--root` decision-trace ledger (NWR's own outcome records) -- the entire
point of this script.

Usage:
    python scripts/run_prospective_outcome_ingestion_v1.py --root <path>
    python scripts/run_prospective_outcome_ingestion_v1.py --root <path> --dry-run
    python scripts/run_prospective_outcome_ingestion_v1.py --root <path> --summary-out out.json

Re-runnable freely -- see the orchestrator module's own idempotency
guarantee (proven in
`tests/test_prospective_outcome_ingestion_orchestrator_v1_service.py`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.prospective_outcome_ingestion_orchestrator_v1_service import (  # noqa: E402
    run_ingestion,
)
from src.services.sleeper_import_service import SleeperHttpClient  # noqa: E402

DEFAULT_OWNER_ROSTER_ID_BY_LEAGUE = {
    "1312983576827920384": 9,  # Fantasy Gamers, owner scolety -- the one real, confirmed mapping.
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--root", required=True,
        help="The redraft root containing decision_traces/<profile_id>.jsonl (e.g. the real "
        "AppData\\Local\\com.ninerswarroom.redraft\\state\\redraft path, or an isolated test root).",
    )
    parser.add_argument(
        "--profile-id", action="append", dest="profile_ids", default=None,
        help="Restrict to one profile id (repeatable). Default: every *.jsonl file under "
        "<root>/decision_traces/.",
    )
    parser.add_argument(
        "--owner-roster-id-map", default=None,
        help='A JSON object string mapping league_id -> owner roster id, e.g. \'{"123": 9}\'. '
        "Merged ON TOP OF the one real, built-in Fantasy Gamers mapping (does not replace it unless "
        "the same league_id key is supplied).",
    )
    parser.add_argument(
        "--current-nfl-week", type=int, default=None,
        help="Override the real current NFL week instead of fetching GET /state/nfl. Mostly for "
        "reproducible manual runs; omit to use the real, live value.",
    )
    parser.add_argument(
        "--summary-out", default=None,
        help="Write the full run report (JSON) to this path. Always printed to stdout regardless.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Plan only -- print what WOULD be done, make zero network calls and zero ledger writes. "
        "(Implemented by calling the same planner the real run uses, but never executing a PROCESS_* "
        "item.)",
    )
    return parser.parse_args(argv)


def _dry_run_report(root: Path, *, profile_ids, current_nfl_week: int | None, owner_roster_id_by_league) -> dict:
    from src.services.in_season_decision_trace_service import load_decision_traces
    from src.services.prospective_outcome_ingestion_orchestrator_v1_service import (
        _discover_profile_ids,
        plan_ingestion_action,
    )
    from src.services.sleeper_league_context_service import parse_current_nfl_week

    client = SleeperHttpClient()
    week = current_nfl_week
    if week is None:
        week = parse_current_nfl_week(client.get_json("state/nfl"))
        if week is None:
            raise SystemExit("Could not determine the real current NFL week -- refusing to guess.")

    resolved_profile_ids = profile_ids if profile_ids else _discover_profile_ids(root)
    items = []
    for profile_id in resolved_profile_ids:
        for record in load_decision_traces(root, profile_id):
            item = plan_ingestion_action(
                record, current_nfl_week=week, owner_roster_id_by_league=owner_roster_id_by_league,
            )
            items.append(item.to_dict())
    counts: dict[str, int] = {}
    for item in items:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
    return {"dryRun": True, "currentNflWeek": week, "countsByAction": counts, "plan": items}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)

    owner_roster_id_by_league = dict(DEFAULT_OWNER_ROSTER_ID_BY_LEAGUE)
    if args.owner_roster_id_map:
        owner_roster_id_by_league.update(json.loads(args.owner_roster_id_map))

    if args.dry_run:
        report = _dry_run_report(
            root, profile_ids=tuple(args.profile_ids) if args.profile_ids else None,
            current_nfl_week=args.current_nfl_week, owner_roster_id_by_league=owner_roster_id_by_league,
        )
    else:
        result = run_ingestion(
            root,
            profile_ids=tuple(args.profile_ids) if args.profile_ids else None,
            current_nfl_week=args.current_nfl_week,
            owner_roster_id_by_league=owner_roster_id_by_league,
        )
        report = result.to_dict()

    payload = json.dumps(report, indent=2, sort_keys=True)
    print(payload)
    if args.summary_out:
        Path(args.summary_out).write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
