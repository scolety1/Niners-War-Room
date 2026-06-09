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
    result = run_model_v4_sanity_fixture_dry_run()
    print(f"wrote={result.csv_path}")
    print(f"wrote={result.markdown_path}")
    print(f"fixtures={result.summary['fixture_count']}")
    print(f"review={result.summary['review_count']}")


if __name__ == "__main__":
    main()
