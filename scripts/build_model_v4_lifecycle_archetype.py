from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_lifecycle_archetype_service import (  # noqa: E402
    build_lifecycle_archetype_layer,
    write_lifecycle_archetype_outputs,
)


def main() -> None:
    result = build_lifecycle_archetype_layer()
    paths = write_lifecycle_archetype_outputs(result=result)
    print(f"player_rows={len(result.review_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"receipt_rows={len(result.receipt_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"review_rows={paths.review_rows}")
    print(f"components={paths.component_rows}")
    print(f"receipts={paths.receipts}")
    print(f"warnings={paths.warnings}")
    print(f"doc={paths.doc}")


if __name__ == "__main__":
    main()
