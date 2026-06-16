from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.full_player_board_value_service import (  # noqa: E402
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
)
from src.services.model_v4_wr_qb_v2_candidate_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
    MODEL_VERSION,
    build_wr_qb_v2_candidate,
    write_wr_qb_v2_candidate_exports,
)


def main() -> int:
    latest_path = DEFAULT_FULL_PLAYER_BOARD_ROWS
    if not latest_path.exists():
        raise FileNotFoundError(
            f"Missing active full-board rows at {latest_path}. "
            "Run scripts/build_model_v4_full_board_rankings_exports.py first."
        )

    candidate_path = DEFAULT_OUTPUT_ROOT / "full_player_board_value_review_rows.csv"
    result = build_wr_qb_v2_candidate(candidate_board_path=candidate_path)
    paths = write_wr_qb_v2_candidate_exports(output_root=DEFAULT_OUTPUT_ROOT, result=result)
    failures = [row for row in result.guardrails if row["status"] != "pass"]
    if failures:
        print(
            json.dumps(
                {
                    "model_version": MODEL_VERSION,
                    "status": "blocked",
                    "gate_failures": failures,
                    "candidate_path": str(paths.full_candidate_board),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = latest_path.with_name(
        f"{latest_path.stem}.pre_{MODEL_VERSION}_{stamp}{latest_path.suffix}"
    )
    shutil.copy2(latest_path, backup_path)
    shutil.copy2(paths.full_candidate_board, latest_path)

    print(
        json.dumps(
            {
                "model_version": MODEL_VERSION,
                "status": "promoted",
                "backup_path": str(backup_path),
                "latest_path": str(latest_path),
                "candidate_path": str(paths.full_candidate_board),
                "production_hash_before": result.production_hash_before,
                "production_hash_after_builder": result.production_hash_after,
                "candidate_rows_hash": result.candidate_hash,
                "gate_failures": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
