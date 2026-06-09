from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_fantasypros_advanced_intake_service import (  # noqa: E402
    DEFAULT_CANONICAL_INDEX,
    DEFAULT_OUTPUT_ROOT,
    build_fantasypros_advanced_intake,
    write_fantasypros_advanced_intake_outputs,
)


def main() -> None:
    result = build_fantasypros_advanced_intake(DEFAULT_CANONICAL_INDEX)
    paths = write_fantasypros_advanced_intake_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"clean_rows={len(result.clean_rows)}")
    print(f"validation_rows={len(result.validation_rows)}")
    print(f"clean={paths['clean']}")
    print(f"validation={paths['validation']}")


if __name__ == "__main__":
    main()
