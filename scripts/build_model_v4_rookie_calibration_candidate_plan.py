from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.model_v4_rookie_calibration_candidate_plan_service import (  # noqa: E402
    build_rookie_calibration_candidate_plan,
    write_rookie_calibration_candidate_plan_outputs,
)


def main() -> int:
    result = build_rookie_calibration_candidate_plan()
    paths = write_rookie_calibration_candidate_plan_outputs(result=result)
    print(f"candidates={paths['candidates']}")
    print(f"doc={paths['doc']}")
    print(f"candidate_rows={len(result.candidate_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
