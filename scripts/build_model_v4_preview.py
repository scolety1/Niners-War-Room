from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_preview_engine_service import build_model_v4_preview  # noqa: E402
from src.services.truth_set_v3_production_import_service import (  # noqa: E402
    build_truth_set_v3_production_preview,
    write_truth_set_v3_production_outputs,
)
from src.services.truth_set_v3_snap_share_import_service import (  # noqa: E402
    build_truth_set_v3_snap_share_preview,
    write_truth_set_v3_snap_outputs,
)
from src.services.truth_set_v3_usage_derivation_service import (  # noqa: E402
    build_truth_set_v3_usage_preview,
    write_truth_set_v3_usage_outputs,
)

MODEL_V4_TRUTH_SET = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
MODEL_V4_SOURCE_REPORT_ROOT = Path("local_exports/model_v4/source_reports")


def main() -> None:
    production = build_truth_set_v3_production_preview(
        truth_set_path=MODEL_V4_TRUTH_SET,
    )
    production_paths = write_truth_set_v3_production_outputs(
        MODEL_V4_SOURCE_REPORT_ROOT,
        production,
    )
    usage = build_truth_set_v3_usage_preview(
        truth_set_path=MODEL_V4_TRUTH_SET,
    )
    write_truth_set_v3_usage_outputs(MODEL_V4_SOURCE_REPORT_ROOT, usage)
    snap = build_truth_set_v3_snap_share_preview(
        truth_set_path=MODEL_V4_TRUTH_SET,
        production_week_path=production_paths["week"],
    )
    write_truth_set_v3_snap_outputs(MODEL_V4_SOURCE_REPORT_ROOT, snap)
    result = build_model_v4_preview(v3_report_root=MODEL_V4_SOURCE_REPORT_ROOT)
    print(f"wrote={result.output_root}")
    print(f"rows={result.summary['preview_output_rows']}")
    print(f"review_status={result.summary['review_status']}")


if __name__ == "__main__":
    main()
