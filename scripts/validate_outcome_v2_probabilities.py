from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.outcome_v2_probability_validation_service import (
    ANCHOR_LABEL_PATH,
    SEASON_LABEL_PATH,
    SHARED_VALIDATION_ROOT,
    write_validation_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate review-only Outcome V2 probability fields.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Write review-only validation artifacts to ignored shared-data output.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=SHARED_VALIDATION_ROOT,
        help="Output folder for validation CSV artifacts.",
    )
    parser.add_argument(
        "--anchor-labels-path",
        type=Path,
        default=ANCHOR_LABEL_PATH,
        help="Anchor horizon labels to validate.",
    )
    parser.add_argument(
        "--season-labels-path",
        type=Path,
        default=SEASON_LABEL_PATH,
        help="Season outcome labels to use as anchor features.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to validate review-only Outcome V2 probabilities")
        print(f"default_output_root={args.output_root}")
        return 0

    result = write_validation_artifacts(
        args.output_root,
        anchor_labels_path=args.anchor_labels_path,
        season_labels_path=args.season_labels_path,
    )
    print(f"output_root={result.output_root}")
    print(f"passed_fields={result.passed_fields}")
    print(f"blocked_fields={result.blocked_fields}")
    print(f"validation_results_path={result.validation_results_path}")
    print(f"calibration_path={result.calibration_path}")
    print(f"model_buckets_path={result.model_buckets_path}")
    print(f"manifest_path={result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
