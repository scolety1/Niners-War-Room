from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.model_v4_wr_qb_v2_candidate_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    MODEL_VERSION,
    build_wr_qb_v2_candidate,
    write_wr_qb_v2_candidate_exports,
)


def main() -> int:
    candidate_board_path = DEFAULT_OUTPUT_ROOT / "full_player_board_value_review_rows.csv"
    result = build_wr_qb_v2_candidate(candidate_board_path=candidate_board_path)
    paths = write_wr_qb_v2_candidate_exports(output_root=DEFAULT_OUTPUT_ROOT, result=result)
    print(
        json.dumps(
            {
                "candidate_model": MODEL_VERSION,
                "output_root": str(DEFAULT_OUTPUT_ROOT),
                "production_hash_before": result.production_hash_before,
                "production_hash_after": result.production_hash_after,
                "candidate_hash": result.candidate_hash,
                "active_production_changed": (
                    result.production_hash_before != result.production_hash_after
                ),
                "gate_failures": sum(1 for row in result.guardrails if row["status"] != "pass"),
                "paths": {
                    "full_candidate_board": str(paths.full_candidate_board),
                    "top_40_diff": str(paths.top_40_diff),
                    "watch_row_diff": str(paths.watch_row_diff),
                    "guardrail_report": str(paths.guardrail_report),
                    "reason_code_report": str(paths.reason_code_report),
                    "summary": str(paths.summary),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
