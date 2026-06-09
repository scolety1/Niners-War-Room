from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_dynasty_candidate_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_dynasty_candidate_layer,
    write_rotowire_dynasty_candidate_outputs,
)


def main() -> None:
    result = build_rotowire_dynasty_candidate_layer()
    paths = write_rotowire_dynasty_candidate_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"candidate_rows={len(result.candidate_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"receipt_rows={len(result.receipt_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    for key, path in paths.items():
        print(f"{key}={path}")


if __name__ == "__main__":
    main()
