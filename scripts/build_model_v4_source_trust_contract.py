from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_source_trust_contract_service import (  # noqa: E402
    build_source_trust_contract_rows,
    no_leakage_violations,
    write_source_trust_contract_outputs,
)


def main() -> None:
    rows = build_source_trust_contract_rows()
    violations = no_leakage_violations(rows)
    if violations:
        raise SystemExit(f"source trust leakage violations={len(violations)}")
    paths = write_source_trust_contract_outputs()
    print(f"rows={len(rows)}")
    print(f"csv={paths['csv']}")
    print(f"doc={paths['doc']}")


if __name__ == "__main__":
    main()
