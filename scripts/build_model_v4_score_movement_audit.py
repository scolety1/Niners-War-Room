from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.full_board_score_movement_audit_service import (  # noqa: E402
    build_score_movement_audit,
    write_score_movement_audit,
)


def main() -> None:
    result = build_score_movement_audit()
    paths = write_score_movement_audit(result=result)
    print(f"Wrote movement audit rows: {paths.movement_rows}")
    print(f"Wrote movement audit report: {paths.report}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
