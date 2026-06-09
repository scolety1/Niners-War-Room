from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_stats_first_expected_value_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_stats_first_expected_value_layer,
    write_stats_first_expected_value_outputs,
)


def main() -> None:
    result = build_stats_first_expected_value_layer()
    paths = write_stats_first_expected_value_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"players={len(result.expected_value_rows)}")
    print(f"component_rows={len(result.component_evidence_rows)}")
    print(f"unavailable_rows={len(result.unavailable_rows)}")
    print(f"warnings={len(result.source_warning_rows)}")
    print(f"expected={paths['expected']}")


if __name__ == "__main__":
    main()
