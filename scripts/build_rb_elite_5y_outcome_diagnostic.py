from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.rb_elite_5y_outcome_diagnostic_service import (  # noqa: E402
    SHARED_OUTPUT_ROOT,
    write_rb_elite_5y_diagnostic_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build review-only RB elite within-5Y Outcome V2 diagnostics.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Write diagnostic CSV artifacts under ignored shared data.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=SHARED_OUTPUT_ROOT,
        help="Output folder for review-only diagnostic artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to write RB elite 5Y diagnostic artifacts")
        print(f"default_output_root={args.output_root}")
        return 0

    result = write_rb_elite_5y_diagnostic_artifacts(args.output_root)
    print(f"verdict={result.verdict}")
    print(f"output_root={result.output_root}")
    print(f"dataset_rows={result.dataset_rows}")
    print(f"complete_rows_by_target={result.complete_rows_by_target}")
    print(f"dataset_path={result.dataset_path}")
    print(f"target_summary_path={result.target_summary_path}")
    print(f"fold_metrics_path={result.fold_metrics_path}")
    print(f"calibration_path={result.calibration_path}")
    print(f"error_slices_path={result.error_slices_path}")
    print(f"recommendations_path={result.recommendations_path}")
    print(f"manifest_path={result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
