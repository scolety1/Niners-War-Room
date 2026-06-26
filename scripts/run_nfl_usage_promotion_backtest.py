from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.nfl_usage_promotion_backtest_service import (
    PROMOTION_ROOT,
    run_promotion_gate,
    validate_no_enabled_flags,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run NFL usage promotion gate diagnostics. Defaults to dry-run."
    )
    parser.add_argument("--run", action="store_true", help="Write sanitized promotion artifacts.")
    parser.add_argument("--output-root", type=Path, default=PROMOTION_ROOT)
    parser.add_argument(
        "--skip-predictive",
        action="store_true",
        help="Do not request predictive mode; still writes fallback diagnostics with --run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_promotion_gate(
        output_root=args.output_root,
        write=args.run,
        predictive_requested=not args.skip_predictive,
    )
    if result.files_written:
        validate_no_enabled_flags(result.files_written)
    print(f"output_root={result.output_root}")
    print(f"predictive_backtest_status={result.predictive_backtest_status}")
    print(f"predictive_backtest_run={result.predictive_backtest_run}")
    print(f"files_written={len(result.files_written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
