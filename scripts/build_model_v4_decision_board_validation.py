from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_decision_board_validation_service import (  # noqa: E402
    build_decision_board_validation,
    write_decision_board_validation,
)


def main() -> None:
    result = build_decision_board_validation()
    paths = write_decision_board_validation(result=result)
    print(f"verdict={result.summary['verdict']}")
    print(f"decision_rows={result.summary['decision_rows']}")
    print(f"focus_rows={result.summary['focus_rows']}")
    print(f"blocker_warnings={result.summary['blocker_warnings']}")
    print(f"summary_path={paths.summary}")
    print(f"focus_rows_path={paths.focus_rows}")
    print(f"doc_path={paths.doc}")


if __name__ == "__main__":
    main()
