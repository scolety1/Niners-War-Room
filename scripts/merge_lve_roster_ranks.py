from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.lve_rank_merge_service import merge_lve_roster_ranks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge LVE summer league ranks from extracted PDF text into Sleeper rosters."
    )
    parser.add_argument("--sleeper-rosters", type=Path, required=True)
    parser.add_argument("--rank-text", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = merge_lve_roster_ranks(
        sleeper_rosters_csv=args.sleeper_rosters,
        rank_text_path=args.rank_text,
        output_dir=args.output_dir,
    )
    print(f"Merged LVE roster ranks: {result.output_dir}")
    for name, path in result.files.items():
        print(f"- {name}: {path} ({result.counts[name]} rows)")


if __name__ == "__main__":
    main()
