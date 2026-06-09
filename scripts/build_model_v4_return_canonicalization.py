from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_return_canonicalization_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_canonical_returns,
    write_canonical_return_outputs,
)


def main() -> None:
    result = build_canonical_returns()
    paths = write_canonical_return_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"canonical_rows={len(result.canonical_rows)}")
    print(f"validation_files={len(result.validation_rows)}")
    print(f"receipts={len(result.receipt_rows)}")
    print(f"coverage={len(result.coverage_rows)}")
    print(f"missing_join_rows={result.summary['missing_join_rows']}")
    print(f"ambiguous_join_rows={result.summary['ambiguous_join_rows']}")
    print(f"admitted_return_rows={result.summary['admitted_return_rows']}")
    print(f"return_yards={result.summary['total_return_yards']}")
    print(f"return_tds={result.summary['total_return_tds']}")
    print(f"canonical={paths['canonical']}")
    print(f"admitted={paths['admitted']}")


if __name__ == "__main__":
    main()
