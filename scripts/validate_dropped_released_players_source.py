from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.dropped_released_players_source_service import (
    DEFAULT_REPORT_PATH,
    validate_dropped_released_players_source,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a future dropped/released players CSV without mutating active "
            "data packs."
        )
    )
    parser.add_argument("csv_path", help="Path to dropped/released players CSV.")
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT_PATH),
        help="Validation report output path.",
    )
    args = parser.parse_args()

    result = validate_dropped_released_players_source(
        args.csv_path,
        report_path=args.report_path,
    )
    print(
        "dropped_released_players_validation "
        f"rows={result.row_count} issues={result.issue_count} "
        f"valid={result.valid} report={result.report_path}"
    )
    raise SystemExit(0 if result.valid else 1)


if __name__ == "__main__":
    main()
