from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_veteran_missing_data_penalty_audit_service import (  # noqa: E402
    run_veteran_missing_data_penalty_audit,
)


def main() -> None:
    result = run_veteran_missing_data_penalty_audit()
    print(f"wrote={result.csv_path}")
    print(f"wrote={result.markdown_path}")
    print(f"audited_rows={result.summary['audited_rows']}")
    print(f"evidence_adjusted_rows={result.summary['evidence_adjusted_rows']}")


if __name__ == "__main__":
    main()
