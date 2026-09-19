"""Refresh an ESPN league snapshot via Flaim (2026-09-19, design skeleton).

STATUS AS OF THIS PASS: NOT FUNCTIONAL. This script documents the
intended CLI contract and process for the reproducible refresh the Flaim-
integration cycle's Worker 1 task required, but it deliberately does not
call Flaim -- this Claude Code worker session has no Flaim MCP tool
available to it (only the separate, coordinating session does, and only
once the owner's `claude mcp login flaim` OAuth step completes; see
`docs/codex/flaim_integration_20260919/LEDGER.md` for the exact status).
Running this script raises `NotImplementedError` with that explanation,
by design, rather than silently doing nothing or fabricating output.

Intended real process, once Flaim access exists (for whichever agent/
session performs the actual refresh):

1. Resolve the target profile's real ESPN `provider_league_id` (from the
   existing profile JSON, e.g.
   `local_exports/redraft_v1/profiles/<profile_id>.json`).
2. Call Flaim's real MCP tools (per the July 2026 audit's own inventory:
   `get_league_info`, `get_roster`, `get_free_agents` -- NOT
   `get_standings` or `get_transactions`, which remain constrained/not
   enabled per this cycle's governance authorization -- see
   `docs/hq/master/flaim_scoped_capability_reauthorization_v1_20260919/
   CAPABILITY_AUTHORIZATION_MAP.md`).
3. Transform the real response into this codebase's documented
   `EspnFlaimSnapshot` schema (`src/services/espn_flaim_snapshot_service.py`)
   -- classifying each roster player's slot (STARTER/BENCH/RESERVE),
   recording each scoring setting with an honest
   `scoring_completeness` flag, recording the available-player pool with
   an honest `available_player_pool_coverage` flag (never COMPLETE --
   the loader itself rejects that per the July audit's own free-agent
   finding) and a human-readable bound description, and setting
   `retrieved_at_utc` to the real UTC time of this fetch (never
   inferred).
4. Validate the transformed snapshot with
   `parse_espn_flaim_snapshot` (raises loudly on any malformed shape)
   before writing it.
5. Write the validated snapshot to
   `espn_flaim_snapshot_path(redraft_root, profile_id)` -- i.e.
   `local_exports/redraft_v1/espn_flaim_snapshots/<profile_id>.json` --
   mirroring the existing Sleeper import-receipt convention exactly.
6. Never write anything back to ESPN, Sleeper, or Flaim's own
   connected-league registry (`refresh_leagues` is Flaim's own tool for
   that and is out of scope here) -- this process is read-only,
   consistent with every other data-import path in this codebase.

This script intentionally does NOT create a profile, does NOT modify an
existing profile's identity fields, and does NOT touch
`marginal_roster_utility_v2` or any governed valuation code -- it only
ever writes to the `espn_flaim_snapshots/` directory described above.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.espn_flaim_snapshot_service import espn_flaim_snapshot_path  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh a real ESPN league snapshot via Flaim's read-only MCP tools. "
            "NOT YET FUNCTIONAL -- see this file's module docstring."
        )
    )
    parser.add_argument(
        "--profile-id",
        required=True,
        help="The existing local Redraft profile ID to refresh a snapshot for.",
    )
    parser.add_argument(
        "--redraft-root",
        type=Path,
        default=Path("local_exports/redraft_v1"),
        help="Redraft data root (matches NWR_REDRAFT_HOME's default layout).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_path = espn_flaim_snapshot_path(args.redraft_root, args.profile_id)
    raise NotImplementedError(
        "refresh_espn_flaim_snapshot.py is a documented design skeleton, not a working "
        "refresh process yet. This worker session has no Flaim MCP access. Once the "
        "owner's Flaim OAuth login completes and a session with real Flaim MCP tools is "
        "available, that session should call Flaim's get_league_info/get_roster/"
        "get_free_agents tools, transform the result into the schema documented in "
        "src/services/espn_flaim_snapshot_service.py, validate it with "
        "parse_espn_flaim_snapshot, and write it to:\n"
        f"  {target_path}\n"
        "See this file's module docstring for the full intended process, and "
        "docs/codex/flaim_integration_20260919/LEDGER.md for current Flaim-access status."
    )


if __name__ == "__main__":
    main()
