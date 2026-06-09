from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_named_player_review_service import (  # noqa: E402
    run_model_v4_named_player_review,
)


def main() -> None:
    result = run_model_v4_named_player_review(
        output_csv_path="docs/model_v4/PHASE_6_NAMED_PLAYER_REVIEW.csv",
        output_md_path="docs/model_v4/PHASE_6_NAMED_PLAYER_REVIEW.md",
        report_title="Phase 6 Named Player Review",
    )
    print(f"wrote_csv={result.csv_path}")
    print(f"wrote_md={result.markdown_path}")
    print(f"matched={result.summary['matched_players']}")
    print(f"inspection_review_rows={result.summary['inspection_review_rows']}")


if __name__ == "__main__":
    main()
