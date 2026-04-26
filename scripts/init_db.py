from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.db import connect, get_database_path
from src.data.migrations import initialize_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize the Niners War Room SQLite database.")
    parser.add_argument("--database", type=Path, default=None, help="Optional database path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_path = get_database_path(args.database)
    with connect(database_path) as connection:
        initialize_database(connection)
    print(f"Initialized database: {database_path}")


if __name__ == "__main__":
    main()
