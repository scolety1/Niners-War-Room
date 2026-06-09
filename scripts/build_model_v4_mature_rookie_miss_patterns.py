from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.model_v4_mature_rookie_miss_pattern_service import (  # noqa: E402
    build_mature_miss_pattern_report,
    write_mature_miss_pattern_outputs,
)


def main() -> int:
    result = build_mature_miss_pattern_report()
    paths = write_mature_miss_pattern_outputs(result=result)
    print(f"rows={paths['rows']}")
    print(f"summary={paths['summary']}")
    print(f"doc={paths['doc']}")
    print(f"pattern_rows={len(result.pattern_rows)}")
    print(f"summary_rows={len(result.summary_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
