from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint14_15_calibration_service import (  # noqa: E402
    build_sprint14_15_review_outputs,
    write_sprint14_15_review_outputs,
)


def main() -> None:
    result = build_sprint14_15_review_outputs()
    paths = write_sprint14_15_review_outputs(result=result)
    print(f"niners_roster_rows={len(result.roster_rows)}")
    print(f"contract_rows={len(result.contract_rows)}")
    print(f"calibration_fixture_rows={len(result.fixture_rows)}")
    print(f"suspicious_rows={len(result.suspicious_rows)}")
    print(f"roster_state={paths.roster_state}")
    print(f"deadline_contract={paths.deadline_contract}")
    print(f"calibration_fixtures={paths.calibration_fixtures}")
    print(f"audit_packet={paths.audit_packet}")
    print(f"audit_prompt={paths.audit_prompt}")


if __name__ == "__main__":
    main()
