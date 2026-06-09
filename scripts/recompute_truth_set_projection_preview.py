from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.truth_set_projection_recompute_service import (  # noqa: E402
    recompute_truth_set_projection_rows,
    write_truth_set_projection_flags,
    write_truth_set_projection_recompute,
)

DEFAULT_SOURCE = Path("local_exports/truth_set_lab/v1/source_clean/projections.csv")
DEFAULT_OUTPUT = Path(
    "local_exports/truth_set_lab/v1/reports/projection_recompute_preview.csv"
)
DEFAULT_FLAGS = Path(
    "local_exports/truth_set_lab/v1/reports/projection_recompute_flags.csv"
)
DEFAULT_SUMMARY = Path(
    "local_exports/truth_set_lab/v1/reports/projection_recompute_summary.json"
)
DEFAULT_REFERENCE = Path(
    "local_exports/active_veteran_model_public_sources/stats_first_veteran_model_preview_outputs.csv"
)


def main() -> None:
    result = recompute_truth_set_projection_rows(
        DEFAULT_SOURCE,
        reference_player_path=DEFAULT_REFERENCE,
    )
    write_truth_set_projection_recompute(DEFAULT_OUTPUT, result.rows)
    write_truth_set_projection_flags(DEFAULT_FLAGS, result.flags)
    DEFAULT_SUMMARY.write_text(
        json.dumps(result.summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result.summary, indent=2))
    print(f"Wrote {DEFAULT_OUTPUT}")
    print(f"Wrote {DEFAULT_FLAGS}")


if __name__ == "__main__":
    main()
