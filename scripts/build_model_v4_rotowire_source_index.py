from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_source_index_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_source_index,
    write_rotowire_source_index,
)


def main() -> None:
    result = build_rotowire_source_index()
    paths = write_rotowire_source_index(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"files={len(result.rows)}")
    print(f"clean={result.summary['clean_file_count']}")
    print(f"review={result.summary['review_file_count']}")
    print(f"active={result.summary['active_file_count']}")
    print(f"inactive={result.summary['inactive_file_count']}")
    print(f"index={paths['index']}")
    print(f"schema={paths['schema']}")


if __name__ == "__main__":
    main()
