from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.rotowire_local_team_status_service import (  # noqa: E402
    build_rotowire_team_status_source,
    write_rotowire_team_status_source,
)


def main() -> None:
    result = build_rotowire_team_status_source()
    paths = write_rotowire_team_status_source(result=result)
    print(f"Wrote RotoWire team/status rows: {paths.review_rows}")
    print(f"Wrote RotoWire source manifest: {paths.manifest}")
    print(f"Wrote RotoWire discovery report: {paths.discovery_report}")
    print(f"Wrote RotoWire source contract: {paths.source_contract}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
