from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.draft_prep_data_foundation_service import (  # noqa: E402
    build_draft_prep_data_foundation,
)


def main() -> None:
    result = build_draft_prep_data_foundation()
    print(
        "draft_prep_data_foundation "
        f"prior_rows={result.prior_history_rows} "
        f"behavior_rows={result.behavior_rows} "
        f"readiness_rows={result.readiness_rows} "
        f"scouting_pool_rows={result.scouting_pool_rows} "
        f"legal_ready={result.confirmed_legal_pool_ready} "
        f"scouting_ready={result.scouting_pool_ready} "
        f"output={result.output_root}"
    )


if __name__ == "__main__":
    main()
