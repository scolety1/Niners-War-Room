from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load a local data pack into SQLite.")
    parser.add_argument("data_pack", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raise SystemExit(f"Task 3 will implement loading for: {args.data_pack}")


if __name__ == "__main__":
    main()
