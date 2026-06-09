from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.truth_set_v3_route_honesty_service import (  # noqa: E402
    write_route_honesty_outputs,
)
from src.services.truth_set_v3_usage_derivation_service import (  # noqa: E402
    DEFAULT_REPORT_ROOT,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build review-only Truth Set Lab v3 route data honesty report."
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_REPORT_ROOT)
    args = parser.parse_args()

    paths = write_route_honesty_outputs(args.output_root)
    for name, path in paths.items():
        print(f"{name}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
