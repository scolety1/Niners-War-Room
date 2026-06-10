from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.model_v4_qb_age_horizon_shadow_service import (  # noqa: E402
    build_qb_age_horizon_shadow,
    write_qb_age_horizon_shadow_exports,
)


def main() -> None:
    result = build_qb_age_horizon_shadow()
    paths = write_qb_age_horizon_shadow_exports(result=result)
    failed = [row for row in result.gate_rows if row["status"] != "pass"]
    print(
        json.dumps(
            {
                "shadow_model": result.summary_rows[0]["value"],
                "gate_failures": len(failed),
                "qb_rows": next(
                    row["value"]
                    for row in result.summary_rows
                    if row["metric"] == "qb_rows"
                ),
                "qb_score_changed_rows": next(
                    row["value"]
                    for row in result.summary_rows
                    if row["metric"] == "qb_score_changed_rows"
                ),
                "paths": {
                    "rankings": str(paths.rankings),
                    "qb_movement": str(paths.qb_movement),
                    "watch_rows": str(paths.watch_rows),
                    "gate_report": str(paths.gate_report),
                    "summary": str(paths.summary),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
