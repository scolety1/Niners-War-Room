from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_replacement_vorp_core_service import (  # noqa: E402
    build_replacement_vorp_core,
    write_replacement_vorp_core_outputs,
)


def main() -> None:
    result = build_replacement_vorp_core()
    paths = write_replacement_vorp_core_outputs(result=result)
    print(f"player_rows={result.summary['player_rows']}")
    print(f"baseline_rows={result.summary['baseline_rows']}")
    print(f"component_rows={result.summary['component_rows']}")
    print(f"receipt_rows={result.summary['receipt_rows']}")
    print(f"warning_rows={result.summary['warning_rows']}")
    print(f"baselines={paths.baselines}")
    print(f"player_vorp={paths.player_rows}")
    print(f"components={paths.component_rows}")
    print(f"receipts={paths.receipts}")
    print(f"warnings={paths.warnings}")
    print(f"doc={paths.doc}")


if __name__ == "__main__":
    main()
