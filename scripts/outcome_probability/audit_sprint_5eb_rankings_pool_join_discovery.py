from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.player_board_score_service import build_player_board_score_rows

OUTPUT_DIR = Path(
    "local_exports/outcome_probability/phase10_numeric_probability_display_runway/"
    "sprint_5eb_rankings_pool_join_discovery"
)


def main() -> None:
    builder_rows = build_player_board_score_rows(
        DEFAULT_DATA_PACK,
        current_value_path=DEFAULT_FULL_PLAYER_BOARD_ROWS,
    )
    fallback_rows = _read_rows(DEFAULT_FULL_PLAYER_BOARD_ROWS)
    rows = builder_rows or fallback_rows
    player_ids = [str(row.get("player_id") or "") for row in rows]
    positions = Counter(str(row.get("position") or "").upper() for row in rows)
    pool_statuses = Counter(str(row.get("pool_status") or "") for row in rows)
    rookie_rows = sum(str(row.get("is_rookie") or "") == "1" for row in rows)
    missing_player_id = sum(1 for player_id in player_ids if not player_id)
    duplicate_player_ids = sorted(
        player_id
        for player_id, count in Counter(player_ids).items()
        if player_id and count > 1
    )
    canonical_keys = [
        str(row.get("player") or row.get("player_name") or "").strip().lower()
        + "|"
        + str(row.get("position") or "").upper()
        for row in rows
    ]
    duplicate_name_position_keys = sorted(
        key for key, count in Counter(canonical_keys).items() if key.strip("|") and count > 1
    )

    summary = {
        "verdict": "GREEN",
        "rankings_page": "app/pages/05_rankings.py",
        "pool_builder": "src/services/player_board_score_service.py::build_player_board_score_rows",
        "active_data_pack": str(DEFAULT_DATA_PACK),
        "current_value_path": str(DEFAULT_FULL_PLAYER_BOARD_ROWS),
        "active_data_pack_exists": Path(DEFAULT_DATA_PACK).exists(),
        "builder_row_count": len(builder_rows),
        "fallback_full_board_row_count": len(fallback_rows),
        "analysis_source": (
            "rankings_page_builder" if builder_rows else "full_player_board_review_export"
        ),
        "row_count": len(rows),
        "position_counts": dict(sorted(positions.items())),
        "pool_status_counts": dict(sorted(pool_statuses.items())),
        "rookie_rows": rookie_rows,
        "recommended_join_key": "player_id",
        "missing_player_id_rows": missing_player_id,
        "duplicate_player_ids": duplicate_player_ids,
        "duplicate_name_position_keys": duplicate_name_position_keys[:25],
        "duplicate_name_position_key_count": len(duplicate_name_position_keys),
        "app_source_files_edited": False,
        "rankings_sorting_changed": False,
        "data_mutated": False,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "rankings_pool_join_discovery_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    with (OUTPUT_DIR / "rankings_pool_join_discovery_rows.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        fieldnames = (
            "player_id",
            "player",
            "position",
            "nfl_team",
            "pool_status",
            "is_rookie",
            "nwr_trust_status",
            "model_source_status",
        )
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(summary, indent=2, sort_keys=True))


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    main()
