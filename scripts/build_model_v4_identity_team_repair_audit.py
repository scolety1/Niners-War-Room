from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.full_board_identity_team_repair_service import (  # noqa: E402
    build_identity_team_repair_audit,
    write_identity_team_repair_audit,
)


def main() -> None:
    result = build_identity_team_repair_audit()
    paths = write_identity_team_repair_audit(result=result)
    print(f"Wrote identity/team repair audit CSV: {paths.audit_csv}")
    print(f"Wrote identity/team source repair report: {paths.report}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
