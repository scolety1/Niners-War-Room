from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_vorp_review_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_vorp_review,
    write_rotowire_vorp_review_outputs,
)


def main() -> None:
    result = build_rotowire_vorp_review()
    paths = write_rotowire_vorp_review_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"vorp_rows={len(result.vorp_rows)}")
    print(f"positive_vorp={result.summary['positive_vorp_count']}")
    print(f"vorp={paths['vorp']}")


if __name__ == "__main__":
    main()
