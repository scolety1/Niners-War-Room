from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_role_usage_intake_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_role_usage_intake,
    write_rotowire_role_usage_intake_outputs,
)


def main() -> None:
    result = build_rotowire_role_usage_intake()
    paths = write_rotowire_role_usage_intake_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"rows={len(result.clean_rows)}")
    print(f"files={len(result.validation_rows)}")
    print(f"warnings={result.summary['warning_row_count']}")
    print(f"clean={paths['clean']}")


if __name__ == "__main__":
    main()
