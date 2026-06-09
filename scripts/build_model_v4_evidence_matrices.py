from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_evidence_matrix_service import (  # noqa: E402
    build_evidence_matrices,
    write_evidence_matrix_outputs,
)


def main() -> None:
    result = build_evidence_matrices()
    paths = write_evidence_matrix_outputs(result=result)
    print(f"nfl_player_rows={result.summary['nfl_player_rows']}")
    print(f"current_prospect_rows={result.summary['current_prospect_rows']}")
    print(
        "admitted_current_prospect_identity_rows="
        f"{result.summary['admitted_current_prospect_identity_rows']}"
    )
    print(f"admitted_prospect_feature_rows={result.summary['admitted_prospect_feature_rows']}")
    print(
        "review_current_prospect_identity_rows="
        f"{result.summary['review_current_prospect_identity_rows']}"
    )
    print(f"historical_backtest_rows={result.summary['historical_backtest_rows']}")
    print(f"source_coverage_rows={result.summary['source_coverage_rows']}")
    print(f"warning_rows={result.summary['warning_rows']}")
    print(f"status={result.summary['status']}")
    print(f"nfl={paths.nfl}")
    print(f"prospects={paths.prospects}")
    print(f"admitted_prospect_features={paths.admitted_prospect_features}")
    print(f"backtest={paths.backtest}")
    print(f"coverage={paths.coverage}")
    print(f"warnings={paths.warnings}")
    print(f"admitted_prospects={paths.admitted_prospects}")
    print(f"prospect_identity_review={paths.prospect_identity_review}")
    print(f"prospect_identity_notes={paths.prospect_identity_notes}")
    print(f"doc={paths.doc}")


if __name__ == "__main__":
    main()
