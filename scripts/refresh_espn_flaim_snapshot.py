"""Preview or activate a deterministic ESPN/Flaim snapshot import.

No Flaim/ESPN call happens here. An authenticated session first saves one
raw capture matching ``nwr_espn_flaim_raw_capture_v1`` (documented in
``espn_flaim_snapshot_import_service.py``), or supplies an already-shaped
``EspnFlaimSnapshot`` for the emergency manual path. Preview is the default;
``--activate`` is the only mode that writes local state.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.espn_flaim_snapshot_import_service import (  # noqa: E402
    EspnSnapshotImportError,
    SnapshotImportExpectations,
    activate_snapshot,
    prepare_snapshot_import,
)
from src.services.espn_flaim_snapshot_service import espn_flaim_snapshot_path  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transform/validate a saved ESPN/Flaim capture, or validate a manual "
            "EspnFlaimSnapshot, then preview or atomically activate it. No provider writes."
        )
    )
    parser.add_argument("--profile-id", required=True, help="Existing ESPN Redraft profile ID.")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Saved raw capture or already-shaped snapshot JSON file.",
    )
    parser.add_argument(
        "--input-kind",
        choices=("raw", "snapshot"),
        default="raw",
        help="raw = NWR capture envelope; snapshot = emergency already-shaped import.",
    )
    parser.add_argument(
        "--expected-provider-league-id",
        required=True,
        help=(
            "Operator-confirmed ESPN league ID; required because real ESPN profiles may store null."
        ),
    )
    parser.add_argument(
        "--expected-owner-team-id",
        required=True,
        help="Operator-confirmed owner team ID from the same provider retrieval.",
    )
    parser.add_argument(
        "--expected-owner-team-name",
        required=True,
        help="Operator-confirmed owner team name from the same provider retrieval.",
    )
    parser.add_argument(
        "--redraft-root",
        type=Path,
        default=Path("local_exports/redraft_v1"),
        help="Worktree-local Redraft data root.",
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Write atomically after validation. Omit for the default read-only preview.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    expectations = SnapshotImportExpectations(
        provider_league_id=args.expected_provider_league_id,
        owner_team_id=args.expected_owner_team_id,
        owner_team_name=args.expected_owner_team_name,
    )
    try:
        profile, snapshot, source_sha256 = prepare_snapshot_import(
            redraft_root=args.redraft_root,
            profile_id=args.profile_id,
            input_path=args.input,
            input_kind=args.input_kind,
            expectations=expectations,
        )
        target = espn_flaim_snapshot_path(args.redraft_root, args.profile_id)
        print("VALID: ESPN snapshot schema and identity checks passed.")
        print(f"Profile: {profile.profile_id} | {profile.league_name}")
        print(
            f"Provider league/team: {snapshot.provider_league_id} | "
            f"{snapshot.owner_team_id} | {snapshot.owner_team_name}"
        )
        print(
            f"Roster/free agents: {len(snapshot.roster)} / "
            f"{len(snapshot.available_player_pool)} ({snapshot.available_player_pool_coverage})"
        )
        print(
            f"Scoring completeness: {snapshot.scoring_completeness}; "
            f"retrieved: {snapshot.retrieved_at_utc}"
        )
        print(f"Input SHA-256: {source_sha256}")
        print(f"Target: {target}")
        print(f"Current target exists: {'yes' if target.exists() else 'no'}")
        if not args.activate:
            print("PREVIEW ONLY: no files were written. Re-run with --activate to install.")
            return 0
        result = activate_snapshot(
            redraft_root=args.redraft_root,
            snapshot=snapshot,
            input_path=args.input,
            source_sha256=source_sha256,
        )
        print(f"ACTIVATED: {result.target_path}")
        if result.backup_path is None:
            print("Previous snapshot: none (no backup needed).")
        else:
            print(f"Previous snapshot preserved at: {result.backup_path}")
        print(f"Installed SHA-256: {result.snapshot_sha256}")
        print(f"Imported at UTC: {result.imported_at_utc}")
        print("Reversal: copy the preserved history file back through this same importer.")
        return 0
    except EspnSnapshotImportError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        print("No active snapshot was changed.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
