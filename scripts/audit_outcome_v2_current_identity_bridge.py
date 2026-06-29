from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.outcome_v2_current_identity_bridge_gate import (
    OUTPUT_ROOT,
    write_current_identity_bridge_gate_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit the Outcome V2 current-player GSIS identity bridge gate.",
    )
    parser.add_argument("--run", action="store_true", help="Write review-only audit artifacts.")
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to write review-only current identity bridge audit artifacts")
        print(f"default_output_root={args.output_root}")
        return 0

    result = write_current_identity_bridge_gate_artifacts(output_root=args.output_root)
    print(f"status={result.status}")
    print(f"output_root={result.output_root}")
    print(f"board_rows={result.board_rows}")
    print(f"eligible_rows={result.eligible_rows}")
    print(f"approved_bridge_rows={result.approved_bridge_rows}")
    print(f"diagnostic_name_position_matches={result.diagnostic_name_position_matches}")
    print(f"current_display_artifact_created={result.current_display_artifact_created}")
    print(f"audit_path={result.audit_path}")
    print(f"summary_path={result.summary_path}")
    print(f"manifest_path={result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
