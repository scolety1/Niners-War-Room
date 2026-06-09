from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.model_v4_rookie_replay_baseline_comparison_service import (  # noqa: E402
    build_rookie_replay_baseline_comparison,
    write_rookie_replay_baseline_comparison_outputs,
)


def main() -> int:
    result = build_rookie_replay_baseline_comparison()
    paths = write_rookie_replay_baseline_comparison_outputs(result=result)
    print(f"comparison={paths['comparison']}")
    print(f"summary={paths['summary']}")
    print(f"by_position={paths['by_position']}")
    print(f"doc={paths['doc']}")
    print(f"comparison_rows={len(result.comparison_rows)}")
    print(f"summary_rows={len(result.summary_rows)}")
    print(f"by_position_rows={len(result.by_position_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
