from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_evidence_layer_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    build_rotowire_evidence_layer,
    write_rotowire_evidence_layer_outputs,
)


def main() -> None:
    result = build_rotowire_evidence_layer()
    paths = write_rotowire_evidence_layer_outputs(DEFAULT_OUTPUT_ROOT, result)
    print(f"wrote={DEFAULT_OUTPUT_ROOT}")
    print(f"evidence_rows={len(result.evidence_rows)}")
    print(f"coverage_rows={len(result.coverage_rows)}")
    print(f"review={result.summary['review_player_count']}")
    print(f"evidence={paths['evidence']}")


if __name__ == "__main__":
    main()
