# ruff: noqa: E501

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.nfl_usage_target_backtest_service import (
    run_backtest_artifacts,
    run_expanded_integration_candidate_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run review-only NFL usage target backtest diagnostics V0.")
    parser.add_argument("--run", action="store_true", help="Write shared-cache joined panel and committed summaries.")
    parser.add_argument("--expanded", action="store_true", help="Run expanded historical integration-candidate diagnostics.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to run backtest diagnostics")
        return 0
    if args.expanded:
        result = run_expanded_integration_candidate_artifacts()
    else:
        result = run_backtest_artifacts()
    print(f"status={result.status}")
    print(f"joined_rows={result.joined_rows}")
    print(f"feature_seasons={';'.join(str(s) for s in result.feature_seasons)}")
    print(f"target_seasons={';'.join(str(s) for s in result.target_seasons)}")
    print(f"joined_panel_path={result.joined_panel_path}")
    print(f"docs_written={len(result.docs_written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
