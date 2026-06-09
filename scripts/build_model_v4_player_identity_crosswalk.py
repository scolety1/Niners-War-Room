from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_player_identity_crosswalk_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_player_identity_crosswalk,
    write_player_identity_crosswalk_outputs,
)


def main() -> None:
    result = build_player_identity_crosswalk()
    paths = write_player_identity_crosswalk_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"source_records={result.summary['source_records']}")
    print(f"canonical_rows={result.summary['canonical_rows']}")
    print(f"unresolved_rows={result.summary['unresolved_rows']}")
    print(f"ambiguous_rows={result.summary['ambiguous_rows']}")
    print(f"crosswalk={paths['crosswalk']}")
    print(f"unresolved={paths['unresolved']}")
    print(f"ambiguous={paths['ambiguous']}")
    print(f"doc={paths['doc']}")


if __name__ == "__main__":
    main()
