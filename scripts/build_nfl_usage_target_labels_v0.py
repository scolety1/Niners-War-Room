# ruff: noqa: E501

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.nfl_usage_target_label_service import build_target_label_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build review-only NFL usage target labels V0.")
    parser.add_argument("--run", action="store_true", help="Write shared-cache labels and committed summary artifacts.")
    parser.add_argument("--seasons", nargs="+", type=int, default=[2023, 2024], help="Target seasons to load.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.run:
        print("dry_run=true")
        print("pass --run to build target labels")
        return 0
    result = build_target_label_artifacts(seasons=args.seasons)
    print(f"status={result.status}")
    print(f"run_id={result.run_id}")
    print(f"target_rows={result.target_rows}")
    print(f"target_panel_path={result.target_panel_path}")
    print(f"docs_written={len(result.docs_written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
