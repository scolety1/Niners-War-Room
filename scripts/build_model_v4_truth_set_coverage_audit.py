from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_truth_set_coverage_audit_service import (  # noqa: E402
    TRUTH_SET_COVERAGE_AUDIT_CSV_PATH,
    TRUTH_SET_COVERAGE_AUDIT_MD_PATH,
    build_model_v4_truth_set_coverage_audit,
)


def main() -> None:
    audit = build_model_v4_truth_set_coverage_audit(
        output_csv_path=TRUTH_SET_COVERAGE_AUDIT_CSV_PATH,
        output_md_path=TRUTH_SET_COVERAGE_AUDIT_MD_PATH,
    )
    print(f"wrote {TRUTH_SET_COVERAGE_AUDIT_CSV_PATH}")
    print(f"wrote {TRUTH_SET_COVERAGE_AUDIT_MD_PATH}")
    print(audit.summary)


if __name__ == "__main__":
    main()
