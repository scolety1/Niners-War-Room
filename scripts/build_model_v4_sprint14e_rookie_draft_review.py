from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint14e_rookie_draft_review_service import (  # noqa: E402
    build_rookie_draft_review_outputs,
    write_rookie_draft_review_outputs,
)


def main() -> None:
    result = build_rookie_draft_review_outputs()
    paths = write_rookie_draft_review_outputs(result=result)
    print(f"rookie_board_rows={len(result.rookie_board_rows)}")
    print(f"pick_candidate_rows={len(result.pick_candidate_rows)}")
    print(f"component_rows={len(result.component_rows)}")
    print(f"warning_rows={len(result.warning_rows)}")
    print(f"rookie_board_rows_path={paths.rookie_board_rows}")
    print(f"pick_candidate_rows_path={paths.pick_candidate_rows}")
    print(f"audit_packet={paths.audit_packet}")
    print(f"audit_prompt={paths.audit_prompt}")


if __name__ == "__main__":
    main()
