from __future__ import annotations

from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_player_board_value_service import (
    CURRENT_CHECKPOINT_SCORE_COLUMN,
    DEFAULT_CURRENT_VALUE_ROWS,
    FULL_BOARD_SCORE_COLUMN,
    build_full_player_board_value_rows,
    write_full_player_board_value_rows,
)

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)


pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists() or not DEFAULT_CURRENT_VALUE_ROWS.exists(),
    reason="local active pack and Model v4 current-value rows are required",
)


def test_full_player_board_export_attempts_all_active_player_rows() -> None:
    result = build_full_player_board_value_rows(ACTIVE_PACK)

    assert result.summary["active_board_rows"] == 240
    assert result.summary["qb_rb_wr_te_rows"] == 232
    assert result.summary["kicker_rows"] == 8
    assert result.summary["nwr_scored_rows"] == 232
    assert result.summary["no_private_score_rows"] == 8
    assert result.summary["source_repair_needed_rows"] == 8


def test_scored_rows_have_admitted_private_lineage_and_source_disclosure() -> None:
    result = build_full_player_board_value_rows(ACTIVE_PACK)
    scored = [row for row in result.rows if row[FULL_BOARD_SCORE_COLUMN]]

    assert scored
    assert {row["lineage_class"] for row in scored} == {"review_v4_current_player"}
    assert {row["source_column"] for row in scored} == {FULL_BOARD_SCORE_COLUMN}
    assert {row["upstream_source_column"] for row in scored} == {
        CURRENT_CHECKPOINT_SCORE_COLUMN
    }
    assert all(row["source_path"] for row in scored)
    assert all(row["upstream_source_path"] for row in scored)
    assert all(row["allowed_use"] for row in scored)
    assert all(row["blocked_use"] for row in scored)


def test_unscored_rows_fail_closed_with_data_needed_notes() -> None:
    result = build_full_player_board_value_rows(ACTIVE_PACK)
    unscored = [row for row in result.rows if not row[FULL_BOARD_SCORE_COLUMN]]

    assert unscored
    assert all(row["nwr_rank"] == "" for row in unscored)
    assert {row["lineage_class"] for row in unscored} == {"unknown"}
    assert all(row["trust_status"] == "Source Repair Needed" for row in unscored)
    assert {row["position"] for row in unscored} == {"K"}
    assert all(
        "Need a current Model v4 private score row" in row["data_needed"]
        for row in unscored
    )


def test_legacy_market_and_league_values_never_become_primary_nwr_score() -> None:
    result = build_full_player_board_value_rows(ACTIVE_PACK)

    assert result.summary["legacy_primary_scores_used"] == 0
    assert result.summary["market_or_league_primary_scores_used"] == 0
    assert all(row["source_column"] == FULL_BOARD_SCORE_COLUMN for row in result.rows)
    assert all(
        row["market_rank_source"] == "market_gap_report.dynasty_startup_adp"
        for row in result.rows
    )
    assert all(row["league_rank_source"] for row in result.rows)


def test_keenan_and_darius_legacy_scores_remain_comparison_only() -> None:
    result = build_full_player_board_value_rows(ACTIVE_PACK)
    keenan = _row(result.rows, "Keenan Allen")
    darius = _row(result.rows, "Darius Slayton")

    assert float(keenan["legacy_active_pack_score"]) == pytest.approx(82.4)
    assert float(keenan[FULL_BOARD_SCORE_COLUMN]) == pytest.approx(33.1581)
    assert keenan["lineage_class"] == "review_v4_current_player"
    assert float(keenan[FULL_BOARD_SCORE_COLUMN]) != pytest.approx(82.4)

    assert float(darius["legacy_active_pack_score"]) == pytest.approx(78.88)
    assert float(darius[FULL_BOARD_SCORE_COLUMN]) == pytest.approx(23.6148)
    assert darius["lineage_class"] == "review_v4_current_player"
    assert float(darius[FULL_BOARD_SCORE_COLUMN]) != pytest.approx(78.88)


def test_write_full_player_board_value_rows_creates_canonical_export(tmp_path: Path) -> None:
    output = tmp_path / "full_player_board_value_review_rows.csv"

    paths = write_full_player_board_value_rows(data_pack_path=ACTIVE_PACK, output_path=output)

    assert paths.review_rows == output
    text = output.read_text(encoding="utf-8")
    assert "nwr_dynasty_score" in text
    assert "data_needed" in text
    assert "legacy_active_pack_score" in text


def _row(rows: tuple[dict[str, object], ...], player_name: str) -> dict[str, object]:
    return next(row for row in rows if row["player_name"] == player_name)
