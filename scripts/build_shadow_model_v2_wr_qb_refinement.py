from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.shadow_model_v2_wr_qb_refinement_service import (  # noqa: E402
    build_shadow_model_v2_wr_qb_refinement,
    write_shadow_model_v2_wr_qb_refinement_outputs,
)


def main() -> int:
    result = build_shadow_model_v2_wr_qb_refinement()
    paths = write_shadow_model_v2_wr_qb_refinement_outputs(result=result)
    print(
        json.dumps(
            {
                "current_rows": len(result.current_rows),
                "historical_rows": len(result.historical_rows),
                "watch_rows": len(result.watch_rows),
                "metric_rows": len(result.metric_rows),
                "baseline_hash_before": result.baseline_hash_before,
                "baseline_hash_after": result.baseline_hash_after,
                "paths": {key: str(value) for key, value in paths.items()},
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
