from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_draft_capital_snapshot_service import (  # noqa: E402
    build_2026_draft_capital_rows,
    write_2026_draft_capital_snapshot,
)


def main() -> None:
    rows = build_2026_draft_capital_rows()
    output, manifest, doc = write_2026_draft_capital_snapshot(rows=rows)
    print(f"draft_capital_rows={len(rows)}")
    print(f"draft_capital_output={output}")
    print(f"draft_capital_manifest={manifest}")
    print(f"draft_capital_doc={doc}")


if __name__ == "__main__":
    main()
