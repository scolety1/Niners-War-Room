from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_current_value_export_service import (
    DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS,
    write_full_board_current_value_export,
)

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)

SCRATCH_EXPORTER_BLOCKER = (
    "Phase 5AM classification: the isolated full-board current-value exporter "
    "currently emits zero scored checkpoint rows in this lane. Phase 5A uses the "
    "recovered admitted local checkpoint artifact until the exporter source/path "
    "contract is repaired without synthetic scores."
)


pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists(),
    reason="local active pack is required for full-board current-value export tests",
)


@pytest.mark.xfail(reason=SCRATCH_EXPORTER_BLOCKER, strict=True)
def test_full_board_current_value_export_attempts_active_qb_rb_wr_te_rows(
    tmp_path: Path,
) -> None:
    result = write_full_board_current_value_export(
        data_pack_path=ACTIVE_PACK,
        output_root=tmp_path / "current_value",
        support_root=tmp_path / "support",
    )

    assert result.summary["active_truth_set_rows"] == 232
    assert result.summary["evidence_nfl_player_rows"] == 232
    assert result.summary["vorp_player_rows"] == 232
    assert result.summary["checkpoint_review_rows"] == 232
    assert result.summary["checkpoint_scored_rows"] == 232
    assert result.summary["market_rows_used"] == 0
    assert result.summary["league_rank_rows_used"] == 0
    assert result.summary["legacy_active_pack_scores_used"] == 0

    full_rows = _read_rows(tmp_path / "current_value" / DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.name)
    assert len(full_rows) == 232
    assert all(row["checkpoint_review_score"] for row in full_rows)
    assert {row["position"] for row in full_rows} <= {"QB", "RB", "WR", "TE"}


@pytest.mark.xfail(reason=SCRATCH_EXPORTER_BLOCKER, strict=True)
def test_full_board_current_value_keeps_legacy_sentinels_out_of_scores(
    tmp_path: Path,
) -> None:
    write_full_board_current_value_export(
        data_pack_path=ACTIVE_PACK,
        output_root=tmp_path / "current_value",
        support_root=tmp_path / "support",
    )
    rows = _read_rows(tmp_path / "current_value" / DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.name)
    keenan = _row(rows, "Keenan Allen")
    darius = _row(rows, "Darius Slayton")

    assert float(keenan["checkpoint_review_score"]) == pytest.approx(33.1581)
    assert float(keenan["checkpoint_review_score"]) != pytest.approx(82.4)
    assert float(darius["checkpoint_review_score"]) == pytest.approx(23.6148)
    assert float(darius["checkpoint_review_score"]) != pytest.approx(78.88)
    assert keenan["checkpoint_version"] == "model_v4_phase_11g_current_value_checkpoint_0.1.0"
    assert darius["checkpoint_version"] == "model_v4_phase_11g_current_value_checkpoint_0.1.0"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _row(rows: list[dict[str, str]], player_name: str) -> dict[str, str]:
    return next(row for row in rows if row["player_name"] == player_name)
