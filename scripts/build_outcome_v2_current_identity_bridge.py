from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.outcome_v2_identity_bridge_service import (
    CURRENT_BOARD_PATH,
    HISTORICAL_SEASON_LABELS_PATH,
    OUTPUT_ROOT,
    ROSTER_CONTEXT_POINTER_PATH,
    write_outcome_v2_identity_bridge_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the review-only Outcome V2 current-board-to-GSIS identity bridge.",
    )
    parser.add_argument("--run", action="store_true", help="Write review-only bridge artifacts.")
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--current-board-path", type=Path, default=CURRENT_BOARD_PATH)
    parser.add_argument(
        "--roster-context-pointer-path",
        type=Path,
        default=ROSTER_CONTEXT_POINTER_PATH,
    )
    parser.add_argument("--roster-context-path", type=Path, default=None)
    parser.add_argument(
        "--historical-season-labels-path",
        type=Path,
        default=HISTORICAL_SEASON_LABELS_PATH,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to write review-only current identity bridge artifacts")
        print(f"default_output_root={args.output_root}")
        print(f"default_current_board_path={args.current_board_path}")
        print(f"default_roster_context_pointer_path={args.roster_context_pointer_path}")
        return 0

    result = write_outcome_v2_identity_bridge_artifacts(
        output_root=args.output_root,
        current_board_path=args.current_board_path,
        roster_context_pointer_path=args.roster_context_pointer_path,
        roster_context_path=args.roster_context_path,
        historical_season_labels_path=args.historical_season_labels_path,
    )
    print(f"status={result.status}")
    print(f"output_root={result.output_root}")
    print(f"bridge_path={result.bridge_path}")
    print(f"audit_path={result.audit_path}")
    print(f"manifest_path={result.manifest_path}")
    print(f"current_board_rows={result.current_board_rows}")
    print(f"bridge_rows={result.bridge_rows}")
    print(f"veteran_non_rookie_rows={result.veteran_non_rookie_rows}")
    print(f"matched_exact_rows={result.matched_exact_rows}")
    print(f"matched_high_confidence_rows={result.matched_high_confidence_rows}")
    print(f"missing_gsis_rows={result.missing_gsis_rows}")
    print(f"ambiguous_rows={result.ambiguous_rows}")
    print(f"out_of_scope_rookie_or_prospect_rows={result.out_of_scope_rookie_or_prospect_rows}")
    print(f"high_confidence_coverage_pct={result.high_confidence_coverage_pct}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
