from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint14f_june15_decision_board_service import (  # noqa: E402
    build_june15_decision_board_outputs,
    write_june15_decision_board_outputs,
)


def main() -> None:
    result = build_june15_decision_board_outputs()
    paths = write_june15_decision_board_outputs(result=result)
    print(f"decision_rows={len(result.decision_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"decision_rows_path={paths.decision_rows}")
    print(f"audit_packet={paths.audit_packet}")
    print(f"audit_prompt={paths.audit_prompt}")


if __name__ == "__main__":
    main()
