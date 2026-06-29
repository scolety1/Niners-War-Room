from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.outcome_v2_historical_label_factory import (
    SHARED_OUTPUT_ROOT,
    write_historical_label_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build review-only Outcome V2 historical horizon labels.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Write review-only labels to ignored C:\\NWR_SHARED_DATA output.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=SHARED_OUTPUT_ROOT,
        help="Output folder for generated review-only CSV artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to build review-only historical labels")
        print(f"default_output_root={args.output_root}")
        return 0

    result = write_historical_label_artifacts(args.output_root)
    print(f"status={result.validation_status}")
    print(f"output_root={result.output_root}")
    print(f"season_rows={result.season_rows}")
    print(f"anchor_rows={result.anchor_rows}")
    print(f"season_label_path={result.season_label_path}")
    print(f"anchor_label_path={result.anchor_label_path}")
    print(f"manifest_path={result.manifest_path}")
    print(f"validation_path={result.validation_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
