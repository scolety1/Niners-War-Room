from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.truth_set_first_down_projection_estimator_service import (  # noqa: E402
    build_first_down_estimator_preview,
    write_first_down_estimator_outputs,
)

DEFAULT_PROJECTION_SOURCE = Path("local_exports/truth_set_lab/v1/source_clean/projections.csv")
DEFAULT_HISTORICAL_STATS = Path(
    "local_exports/nflverse/preview/sprint2_phase7_public_20260514/raw/"
    "nflverse_player_stats_weekly.csv"
)
DEFAULT_ESTIMATE_OUTPUT = Path(
    "local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_preview.csv"
)
DEFAULT_RATE_OUTPUT = Path(
    "local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_rates.csv"
)
DEFAULT_SUMMARY_OUTPUT = Path(
    "local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_summary.csv"
)
DEFAULT_SUMMARY_JSON = Path(
    "local_exports/truth_set_lab/v1/reports/first_down_projection_estimator_summary.json"
)


def main() -> None:
    result = build_first_down_estimator_preview(
        DEFAULT_PROJECTION_SOURCE,
        DEFAULT_HISTORICAL_STATS,
    )
    write_first_down_estimator_outputs(
        estimate_path=DEFAULT_ESTIMATE_OUTPUT,
        rate_path=DEFAULT_RATE_OUTPUT,
        summary_path=DEFAULT_SUMMARY_OUTPUT,
        result=result,
    )
    DEFAULT_SUMMARY_JSON.write_text(
        json.dumps(result.summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result.summary, indent=2))
    print(f"Wrote {DEFAULT_ESTIMATE_OUTPUT}")
    print(f"Wrote {DEFAULT_RATE_OUTPUT}")


if __name__ == "__main__":
    main()
