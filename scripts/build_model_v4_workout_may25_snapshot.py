from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_workout_snapshot_service import (  # noqa: E402
    build_may25_workout_snapshot,
    write_may25_workout_snapshot,
)


def main() -> None:
    rows = build_may25_workout_snapshot()
    output, manifest, doc = write_may25_workout_snapshot(rows=rows)
    print(f"workout_rows={len(rows)}")
    print(f"workout_output={output}")
    print(f"workout_manifest={manifest}")
    print(f"workout_doc={doc}")


if __name__ == "__main__":
    main()
