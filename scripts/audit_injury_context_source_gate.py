from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from src.services.injury_context_source_gate_service import (
        write_injury_context_source_gate_artifacts,
    )

    result = write_injury_context_source_gate_artifacts()
    print(f"decision={result.decision}")
    print(f"row_count={result.row_count}")
    print(f"seasons_covered={result.seasons_covered}")
    print(f"gsis_coverage_rate={result.gsis_coverage_rate:.6f}")
    print(f"raw_output_path={result.raw_output_path}")
    print(f"audit_path={result.audit_path}")
    print(f"manifest_path={result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
