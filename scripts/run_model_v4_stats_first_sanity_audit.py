from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_stats_first_sanity_audit_service import (  # noqa: E402
    run_model_v4_stats_first_sanity_audit,
)


def main() -> None:
    result = run_model_v4_stats_first_sanity_audit()
    print(f"csv={result.csv_path}")
    print(f"markdown={result.markdown_path}")
    print(f"rows={len(result.rows)}")
    print(f"issues={result.summary['issue_counts']}")
    print(f"guardrails={result.summary['guardrails']}")


if __name__ == "__main__":
    main()

