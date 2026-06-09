from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.model_v4_export_summary_index_service import (  # noqa: E402
    write_export_summary_index_outputs,
)


def main() -> None:
    paths = write_export_summary_index_outputs()
    for key, path in paths.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
