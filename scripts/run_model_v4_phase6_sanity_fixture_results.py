from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sanity_fixture_dry_run_service import (  # noqa: E402
    run_model_v4_sanity_fixture_dry_run,
)


def main() -> None:
    result = run_model_v4_sanity_fixture_dry_run(
        output_csv_path="docs/model_v4/PHASE_6_SANITY_FIXTURE_RESULTS.csv",
        output_md_path="docs/model_v4/PHASE_6_SANITY_FIXTURE_RESULTS.md",
        report_title="Phase 6 Sanity Fixture Results",
    )
    print(f"wrote_csv={result.csv_path}")
    print(f"wrote_md={result.markdown_path}")
    print(f"ready={result.summary['ready_count']}")
    print(f"review={result.summary['review_count']}")
    print(f"blocked={result.summary['blocked_count']}")


if __name__ == "__main__":
    main()
