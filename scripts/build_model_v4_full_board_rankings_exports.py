from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_current_value_export_service import (
    write_full_board_current_value_export,
)
from src.services.full_board_missing_score_repair_queue_service import (
    build_missing_score_repair_queue,
    write_missing_score_repair_queue,
)
from src.services.full_player_board_value_service import (
    build_full_player_board_value_rows,
    write_full_player_board_value_rows,
)


def main() -> None:
    current_value = write_full_board_current_value_export(data_pack_path=DEFAULT_DATA_PACK)
    full_board = build_full_player_board_value_rows(DEFAULT_DATA_PACK)
    full_board_paths = write_full_player_board_value_rows(
        data_pack_path=DEFAULT_DATA_PACK,
        result=full_board,
    )
    queue = build_missing_score_repair_queue(
        DEFAULT_DATA_PACK,
        full_board_result=full_board,
    )
    queue_paths = write_missing_score_repair_queue(result=queue)
    print(
        json.dumps(
            {
                "current_value": str(current_value.checkpoint_paths.review_rows),
                "full_board_current_value_review_rows": (
                    "local_exports/model_v4/current_value/latest/"
                    "current_player_value_full_board_review_rows.csv"
                ),
                "full_player_board": str(full_board_paths.review_rows),
                "missing_score_repair_queue": str(queue_paths.rows),
                "current_value_summary": current_value.summary,
                "full_board_summary": full_board.summary,
                "repair_queue_summary": queue.summary,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
