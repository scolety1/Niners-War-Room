from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_phase6_movement_audit_service import (  # noqa: E402
    run_model_v4_phase6_movement_audit,
)


def main() -> None:
    result = run_model_v4_phase6_movement_audit()
    print(f"phase5_baseline={result.reconstructed_phase5_preview_path}")
    print(f"wrote_csv={result.csv_path}")
    print(f"wrote_md={result.markdown_path}")
    print(f"meaningful_movement_rows={result.summary['meaningful_movement_rows']}")
    print(f"unexpected_movement_rows={result.summary['unexpected_movement_rows']}")


if __name__ == "__main__":
    main()
