from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_first_down_canonicalization_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_canonical_first_downs,
    write_canonical_first_down_outputs,
)


def main() -> None:
    result = build_canonical_first_downs()
    paths = write_canonical_first_down_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"rushing_rows={len(result.rushing_rows)}")
    print(f"receiving_rows={len(result.receiving_rows)}")
    print(f"validation_files={len(result.validation_rows)}")
    print(f"receipts={len(result.receipt_rows)}")
    print(f"coverage={len(result.coverage_rows)}")
    print(f"missing_join_rows={result.summary['missing_join_rows']}")
    print(f"ambiguous_join_rows={result.summary['ambiguous_join_rows']}")
    print(f"admitted_rushing_rows={result.summary['admitted_rushing_rows']}")
    print(f"admitted_receiving_rows={result.summary['admitted_receiving_rows']}")
    print(f"rushing={paths['rushing']}")
    print(f"receiving={paths['receiving']}")
    print(f"admitted_rushing={paths['admitted_rushing']}")
    print(f"admitted_receiving={paths['admitted_receiving']}")


if __name__ == "__main__":
    main()
