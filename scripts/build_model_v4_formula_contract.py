from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_formula_contract_service import (  # noqa: E402
    write_formula_contract_outputs,
)


def main() -> None:
    paths = write_formula_contract_outputs()
    print(f"allowed_registry={paths.allowed_registry}")
    print(f"blocked_registry={paths.blocked_registry}")
    print(f"guard_report={paths.guard_report}")
    print(f"doc={paths.doc}")


if __name__ == "__main__":
    main()
