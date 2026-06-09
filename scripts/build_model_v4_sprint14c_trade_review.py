from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint14c_trade_review_service import (  # noqa: E402
    build_trade_review_outputs,
    write_trade_review_outputs,
)


def main() -> None:
    result = build_trade_review_outputs()
    paths = write_trade_review_outputs(result=result)
    print(f"trade_away_rows={len(result.trade_away_rows)}")
    print(f"trade_for_rows={len(result.trade_for_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"trade_away_rows_path={paths.trade_away_rows}")
    print(f"trade_for_rows_path={paths.trade_for_rows}")
    print(f"audit_packet={paths.audit_packet}")
    print(f"audit_prompt={paths.audit_prompt}")


if __name__ == "__main__":
    main()
