from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.model_edge_evaluation_harness_service import (
    DEFAULT_BOARD_ROWS,
    DEFAULT_OUTPUT_ROOT,
    build_model_edge_evaluation_harness,
    write_model_edge_evaluation_harness_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build read-only model edge evaluation harness outputs."
    )
    parser.add_argument(
        "--board-rows",
        default=str(DEFAULT_BOARD_ROWS),
        help="Historical rookie tuning board rows CSV.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Output directory for harness review CSVs.",
    )
    args = parser.parse_args()

    result = build_model_edge_evaluation_harness(Path(args.board_rows))
    paths = write_model_edge_evaluation_harness_outputs(Path(args.output_root), result)
    print(f"wrote rows: {paths['rows']}")
    print(f"wrote summary: {paths['summary']}")
    print(f"wrote position summary: {paths['position_summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
