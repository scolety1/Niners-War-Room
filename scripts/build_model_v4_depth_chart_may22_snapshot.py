from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_depth_chart_snapshot_service import (  # noqa: E402
    build_may22_depth_chart_rows,
    write_may22_depth_chart_snapshot,
)


def main() -> None:
    rows = build_may22_depth_chart_rows()
    output, doc = write_may22_depth_chart_snapshot(rows=rows)
    print(f"depth_chart_rows={len(rows)}")
    print(f"depth_chart_output={output}")
    print(f"depth_chart_doc={doc}")


if __name__ == "__main__":
    main()
