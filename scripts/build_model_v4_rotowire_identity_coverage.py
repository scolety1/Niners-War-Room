from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_identity_coverage_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_identity_coverage,
    write_rotowire_identity_coverage_outputs,
)


def main() -> None:
    result = build_rotowire_identity_coverage()
    paths = write_rotowire_identity_coverage_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"truth_players={len(result.rows)}")
    print(f"covered={result.summary['covered_player_count']}")
    print(f"review={result.summary['review_player_count']}")
    print(f"coverage={paths['coverage']}")


if __name__ == "__main__":
    main()
