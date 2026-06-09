from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_stats_first_value_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_stats_first_value_layer,
    write_rotowire_stats_first_value_outputs,
)


def main() -> None:
    result = build_rotowire_stats_first_value_layer()
    paths = write_rotowire_stats_first_value_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"value_rows={len(result.value_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"review_confidence={result.summary['review_confidence_count']}")
    print(f"value={paths['value']}")


if __name__ == "__main__":
    main()
