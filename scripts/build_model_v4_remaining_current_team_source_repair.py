from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.remaining_current_team_source_repair_service import (  # noqa: E402
    build_remaining_current_team_source_repair,
    write_remaining_current_team_source_repair,
)


def main() -> None:
    result = build_remaining_current_team_source_repair()
    paths = write_remaining_current_team_source_repair(result=result)
    print(f"Wrote remaining current-team repair CSV: {paths.repair_csv}")
    print(f"Wrote remaining current-team repair report: {paths.report}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
