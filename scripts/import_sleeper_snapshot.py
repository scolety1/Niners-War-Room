from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.sleeper_import_service import DEFAULT_LEAGUE_ID, export_sleeper_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a read-only Sleeper league snapshot to local CSV files."
    )
    parser.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--output-root", type=Path, default=Path("local_exports/sleeper"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = export_sleeper_snapshot(args.league_id, args.output_root)
    print(f"Exported Sleeper snapshot: {result.output_dir}")
    for name, path in result.files.items():
        print(f"- {name}: {path} ({result.counts[name]} rows)")


if __name__ == "__main__":
    main()
