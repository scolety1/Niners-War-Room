from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint12_13_review_service import (  # noqa: E402
    build_sprint12_13_review_outputs,
    write_sprint12_13_review_outputs,
)


def main() -> None:
    result = build_sprint12_13_review_outputs()
    paths = write_sprint12_13_review_outputs(result=result)
    print(f"prospect_rows={len(result.prospect_rows)}")
    print(f"prospect_component_rows={len(result.prospect_component_rows)}")
    print(f"prospect_receipt_rows={len(result.prospect_receipt_rows)}")
    print(f"prospect_warning_rows={len(result.prospect_warning_rows)}")
    print(f"pick_rows={len(result.pick_rows)}")
    print(f"dynasty_asset_rows={len(result.dynasty_rows)}")
    print(f"dynasty_component_rows={len(result.dynasty_component_rows)}")
    print(f"dynasty_receipt_rows={len(result.dynasty_receipt_rows)}")
    print(f"dynasty_warning_rows={len(result.dynasty_warning_rows)}")
    print(f"prospect_review_rows_path={paths.prospect_review_rows}")
    print(f"pick_baselines_path={paths.pick_baselines}")
    print(f"dynasty_review_rows_path={paths.dynasty_review_rows}")
    print(f"sprint12_doc={paths.sprint12_doc}")
    print(f"sprint13_doc={paths.sprint13_doc}")


if __name__ == "__main__":
    main()
