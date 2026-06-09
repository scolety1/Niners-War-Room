from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint14d_pick_trade_defer_service import (  # noqa: E402
    build_pick_trade_defer_outputs,
    write_pick_trade_defer_outputs,
)


def main() -> None:
    result = build_pick_trade_defer_outputs()
    paths = write_pick_trade_defer_outputs(result=result)
    print(f"niners_pick_rows={len(result.pick_inventory_rows)}")
    print(f"defer_scenario_rows={len(result.defer_scenario_rows)}")
    print(f"future_pick_context_rows={len(result.future_pick_context_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"pick_inventory_rows_path={paths.pick_inventory_rows}")
    print(f"defer_scenario_rows_path={paths.defer_scenario_rows}")
    print(f"future_pick_context_rows_path={paths.future_pick_context_rows}")
    print(f"audit_packet={paths.audit_packet}")
    print(f"audit_prompt={paths.audit_prompt}")


if __name__ == "__main__":
    main()
