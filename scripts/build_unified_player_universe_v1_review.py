from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.unified_player_universe_validation_service import (
    build_unified_player_universe_review,
)


def main() -> None:
    result = build_unified_player_universe_review()
    print(f"review_path={result.review_path}")
    print(f"validation_report_path={result.validation_report_path}")
    print(f"duplicate_review_path={result.duplicate_review_path}")
    print(f"identity_gap_review_path={result.identity_gap_review_path}")
    print(f"identity_triage_path={result.identity_triage_path}")
    print(f"source_summary_path={result.source_summary_path}")
    print(f"total_rows={result.total_rows}")
    print(f"veteran_rows={result.veteran_rows}")
    print(f"rookie_rows={result.rookie_rows}")
    print(f"pdf_fa_rows={result.pdf_fa_rows}")
    print(f"duplicate_review_count={result.duplicate_review_count}")
    print(f"identity_gap_count={result.identity_gap_count}")
    print(f"safe_repair_count={result.safe_repair_count}")


if __name__ == "__main__":
    main()
