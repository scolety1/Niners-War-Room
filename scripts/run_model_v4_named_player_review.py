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
    result = run_model_v4_named_player_review()
    print(f"wrote={result.csv_path}")
    print(f"wrote={result.markdown_path}")
    print(f"players={result.summary['requested_players']}")
    print(f"inspection_review={result.summary['inspection_review_rows']}")


if __name__ == "__main__":
    main()
