from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.loaders import load_data_pack


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load a local data pack into SQLite.")
    parser.add_argument("data_pack", type=Path)
    parser.add_argument("--database", type=Path, default=None, help="Optional database path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = load_data_pack(args.data_pack, args.database)
    print(f"Loaded data pack: {result.data_pack_name}")
    print(f"Issues: {result.issue_counts}")
    print(f"Inserted rows: {result.inserted_rows}")


if __name__ == "__main__":
    main()
