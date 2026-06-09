from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_evidence_admission_recheck_service import (  # noqa: E402
    run_evidence_admission_recheck,
    write_phase_10n_doc,
)
from src.services.model_v4_evidence_matrix_service import (  # noqa: E402
    write_evidence_matrix_outputs,
)


def main() -> None:
    matrix_paths = write_evidence_matrix_outputs()
    result = run_evidence_admission_recheck()
    doc_path = write_phase_10n_doc(result)
    print(f"phase10n_status={result.summary['status']}")
    print(f"phase10n_checks={result.summary['check_count']}")
    print(f"phase10n_failed_checks={result.summary['failed_check_count']}")
    print(f"phase10n_issues={result.summary['issue_count']}")
    print(f"admitted_current_prospect_identity_rows={result.summary['admitted_current_prospect_identity_rows']}")
    print(f"admitted_prospect_feature_rows={result.summary['admitted_prospect_feature_rows']}")
    print(f"review_current_prospect_identity_rows={result.summary['review_current_prospect_identity_rows']}")
    print(f"evidence_summary={matrix_paths.summary}")
    print(f"phase10n_doc={doc_path}")


if __name__ == "__main__":
    main()
