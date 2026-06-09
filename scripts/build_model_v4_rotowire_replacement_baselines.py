from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_replacement_baseline_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_replacement_baselines,
    write_rotowire_replacement_baseline_outputs,
)


def main() -> None:
    result = build_rotowire_replacement_baselines()
    paths = write_rotowire_replacement_baseline_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"player_pool={len(result.player_pool_rows)}")
    print(f"baselines={len(result.baseline_rows)}")
    print(f"baselines_path={paths['baselines']}")


if __name__ == "__main__":
    main()
