from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.model_v4_rookie_shadow_formula_experiment_service import (  # noqa: E402
    build_rookie_shadow_formula_experiment,
    write_rookie_shadow_formula_experiment_outputs,
)


def main() -> int:
    result = build_rookie_shadow_formula_experiment()
    paths = write_rookie_shadow_formula_experiment_outputs(result=result)
    print(f"rows={paths['rows']}")
    print(f"summary={paths['summary']}")
    print(f"movement={paths['movement']}")
    print(f"doc={paths['doc']}")
    print(f"variant_rows={len(result.variant_rows)}")
    print(f"summary_rows={len(result.summary_rows)}")
    print(f"movement_rows={len(result.movement_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
