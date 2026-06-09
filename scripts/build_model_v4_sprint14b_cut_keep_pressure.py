from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint14b_cut_keep_pressure_service import (  # noqa: E402
    build_cut_keep_pressure_outputs,
    write_cut_keep_pressure_outputs,
)


def main() -> None:
    result = build_cut_keep_pressure_outputs()
    paths = write_cut_keep_pressure_outputs(result=result)
    print(f"pressure_rows={len(result.pressure_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"receipt_rows={len(result.receipt_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"pressure_rows_path={paths.pressure_rows}")
    print(f"audit_packet={paths.audit_packet}")
    print(f"audit_prompt={paths.audit_prompt}")


if __name__ == "__main__":
    main()
