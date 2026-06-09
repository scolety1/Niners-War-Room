from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.full_board_rankings_sanity_gate_service import (  # noqa: E402
    build_rankings_sanity_gate,
    write_rankings_sanity_gate,
)


def main() -> None:
    result = build_rankings_sanity_gate()
    paths = write_rankings_sanity_gate(result=result)
    print(f"Wrote source quarantine CSV: {paths.source_quarantine_csv}")
    print(f"Wrote source quarantine report: {paths.source_quarantine_doc}")
    print(f"Wrote QB sanity report: {paths.qb_sanity_doc}")
    print(f"Wrote TE sanity report: {paths.te_sanity_doc}")
    print(f"Wrote sanity issue queue: {paths.issue_queue_csv}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
