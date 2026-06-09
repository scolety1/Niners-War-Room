from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_fantasypros_identity_mapping_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_fantasypros_identity_mapping,
    write_fantasypros_identity_mapping_outputs,
)


def main() -> None:
    result = build_fantasypros_identity_mapping()
    paths = write_fantasypros_identity_mapping_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"mapping_rows={len(result.mapping_rows)}")
    print(f"unresolved_rows={len(result.unresolved_rows)}")
    print(f"mapping={paths['mapping']}")
    print(f"unresolved={paths['unresolved']}")


if __name__ == "__main__":
    main()
