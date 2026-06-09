from __future__ import annotations

from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_missing_score_repair_queue_service import (
    build_missing_score_repair_queue,
    write_missing_score_repair_queue,
)

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)


pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists(),
    reason="local active pack is required for missing-score repair queue tests",
)


def test_missing_score_repair_queue_contains_remaining_unscored_kickers_only() -> None:
    result = build_missing_score_repair_queue(ACTIVE_PACK)

    assert result.summary["repair_queue_rows"] == 8
    assert result.summary["kicker_unscored_rows"] == 8
    assert result.summary["my_team_unscored_rows"] == 0
    assert result.summary["available_unscored_rows"] == 0
    assert result.summary["rookie_unscored_rows"] == 0
    assert {row["position"] for row in result.rows} == {"K"}
    assert all(row["repair_priority"] == "P5_kicker_low_priority" for row in result.rows)
    assert all(
        "K-specific scoring contract" in row["candidate_source_files_needed"]
        for row in result.rows
    )


def test_missing_score_repair_queue_writes_required_columns(tmp_path: Path) -> None:
    output = tmp_path / "full_board_missing_score_repair_queue.csv"

    paths = write_missing_score_repair_queue(data_pack_path=ACTIVE_PACK, output_path=output)

    assert paths.rows == output
    text = output.read_text(encoding="utf-8")
    for column in (
        "player",
        "missing_score_reason_bucket",
        "human_readable_data_needed",
        "repair_action",
        "can_score_now_from_existing_private_sources",
        "identity_join_status",
        "source_disclosure_status",
    ):
        assert column in text
