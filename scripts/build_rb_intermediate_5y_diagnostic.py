from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from src.services.rb_intermediate_5y_diagnostic_service import (
        write_rb_intermediate_5y_diagnostic_artifacts,
    )

    result = write_rb_intermediate_5y_diagnostic_artifacts()
    print(f"verdict={result.verdict}")
    print(f"output_root={result.output_root}")
    print(f"dataset_rows={result.dataset_rows}")
    print(f"target_summary={result.target_summary_path}")
    print(f"fold_metrics={result.fold_metrics_path}")
    print(f"recommendations={result.recommendations_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
