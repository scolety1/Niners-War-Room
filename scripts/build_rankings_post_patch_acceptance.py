from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.rankings_post_patch_acceptance_service import (  # noqa: E402
    build_rankings_post_patch_acceptance,
    write_rankings_post_patch_acceptance,
)


def main() -> None:
    result = build_rankings_post_patch_acceptance()
    paths = write_rankings_post_patch_acceptance(result)
    print(f"Wrote post-patch top-100 review CSV: {paths.top_100}")
    print(f"Wrote post-patch My Team review CSV: {paths.my_team}")
    print(f"Wrote post-patch QB/TE review CSV: {paths.qb_te}")
    print(f"Wrote post-patch acceptance report: {paths.acceptance_report}")
    print(f"Wrote final Rankings handoff: {paths.final_handoff}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
