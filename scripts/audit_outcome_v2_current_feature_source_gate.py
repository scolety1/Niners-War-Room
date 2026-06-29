from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.outcome_v2_current_feature_source_gate import (
    IDENTITY_BRIDGE_PATH,
    OUTPUT_ROOT,
    SEASON_STATS_POINTER_PATH,
    VALIDATION_RESULTS_PATH,
    write_current_feature_source_gate_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit the Outcome V2 current feature source approval gate.",
    )
    parser.add_argument("--run", action="store_true", help="Write review-only audit artifacts.")
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--season-stats-pointer-path", type=Path, default=SEASON_STATS_POINTER_PATH)
    parser.add_argument("--identity-bridge-path", type=Path, default=IDENTITY_BRIDGE_PATH)
    parser.add_argument("--validation-results-path", type=Path, default=VALIDATION_RESULTS_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to write review-only current feature source gate artifacts")
        print(f"default_output_root={args.output_root}")
        print(f"default_season_stats_pointer_path={args.season_stats_pointer_path}")
        return 0

    result = write_current_feature_source_gate_artifacts(
        output_root=args.output_root,
        season_stats_pointer_path=args.season_stats_pointer_path,
        identity_bridge_path=args.identity_bridge_path,
        validation_results_path=args.validation_results_path,
    )
    print(f"decision={result.decision}")
    print(f"output_root={result.output_root}")
    print(f"audit_path={result.audit_path}")
    print(f"manifest_path={result.manifest_path}")
    print(f"total_candidate_rows={result.total_candidate_rows}")
    print(f"candidate_2025_rows={result.candidate_2025_rows}")
    print(f"veteran_bridge_rows={result.veteran_bridge_rows}")
    print(f"matched_feature_rows={result.matched_feature_rows}")
    print(f"missing_feature_rows={result.missing_feature_rows}")
    print(f"rookie_out_of_scope_rows={result.rookie_out_of_scope_rows}")
    print(f"validated_fields={result.validated_fields}")
    print(f"blocked_fields={result.blocked_fields}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
