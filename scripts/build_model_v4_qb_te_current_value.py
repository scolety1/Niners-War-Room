from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_qb_te_current_value_service import (  # noqa: E402
    build_qb_te_current_value,
    write_qb_te_current_value_outputs,
)


def main() -> None:
    result = build_qb_te_current_value()
    paths = write_qb_te_current_value_outputs(result=result)
    print(f"player_rows={len(result.value_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"receipt_rows={len(result.receipt_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"value_rows={paths.value_rows}")
    print(f"components={paths.component_rows}")
    print(f"receipts={paths.receipts}")
    print(f"warnings={paths.warnings}")
    print(f"doc={paths.doc}")


if __name__ == "__main__":
    main()
