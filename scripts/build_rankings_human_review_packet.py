from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.rankings_human_review_packet_service import (  # noqa: E402
    build_rankings_human_review_packet,
    write_rankings_human_review_packet,
)


def main() -> None:
    result = build_rankings_human_review_packet()
    paths = write_rankings_human_review_packet(result=result)
    print(f"Wrote Rankings readiness report: {paths.readiness_report}")
    print(f"Wrote formula-candidate triage report: {paths.formula_triage_report}")
    print(f"Wrote morning handoff: {paths.morning_handoff}")
    print(f"Wrote top-100 review CSV: {paths.top_100}")
    print(f"Wrote My Team review CSV: {paths.my_team}")
    print(f"Wrote QB triage CSV: {paths.qb_triage}")
    print(f"Wrote TE triage CSV: {paths.te_triage}")
    print(f"Wrote suspicious rows CSV: {paths.suspicious}")
    print(f"Wrote component readback CSV: {paths.component_readback}")
    for key, value in result.summary.items():
        if isinstance(value, dict):
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
