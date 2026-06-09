from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.config.constants import DEFAULT_DATA_PACK
from src.services.full_board_current_value_export_service import (
    DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS,
)
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.player_board_score_service import build_player_board_score_rows

ACTIVE_PACK = Path(DEFAULT_DATA_PACK)
CURRENT_VALUE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)


pytestmark = pytest.mark.skipif(
    not ACTIVE_PACK.exists() or not CURRENT_VALUE_ROWS.exists(),
    reason="local Model v4 exports are required for Player Board routing sentinel tests",
)


def test_player_board_uses_checkpoint_review_score_as_primary_value() -> None:
    rows = build_player_board_score_rows(ACTIVE_PACK, current_value_path=CURRENT_VALUE_ROWS)
    keenan = _row(rows, "Keenan Allen")

    assert keenan["source_column"] == "checkpoint_review_score"
    assert keenan["lineage_class"] == "review_v4_current_player"
    assert float(keenan["primary_review_score"]) == pytest.approx(41.6097)
    assert float(keenan["private_score"]) == pytest.approx(41.6097)


def test_player_board_prefers_full_board_export_when_available() -> None:
    rows = build_player_board_score_rows(ACTIVE_PACK)
    keenan = _row(rows, "Keenan Allen")

    if DEFAULT_FULL_PLAYER_BOARD_ROWS.exists():
        assert keenan["source_column"] == "nwr_dynasty_score"
        assert keenan["source_path"] == str(DEFAULT_FULL_PLAYER_BOARD_ROWS)
        assert keenan["nwr_trust_status"] == "Capped Score"
        if DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.exists():
            assert float(keenan["private_score"]) == pytest.approx(33.1581)
        else:
            assert float(keenan["private_score"]) == pytest.approx(41.6097)
    else:
        assert keenan["source_column"] == "checkpoint_review_score"


def test_active_pack_private_score_is_renamed_legacy_active_pack_score() -> None:
    rows = build_player_board_score_rows(ACTIVE_PACK)
    keenan = _row(rows, "Keenan Allen")

    assert float(keenan["legacy_active_pack_score"]) == pytest.approx(82.4)
    assert keenan["legacy_formula_warning"] is True
    assert keenan["stale_or_legacy_formula_warning"] is True


def test_legacy_active_pack_score_cannot_drive_primary_review_score() -> None:
    rows = build_player_board_score_rows(ACTIVE_PACK)
    keenan = _row(rows, "Keenan Allen")
    darius = _row(rows, "Darius Slayton")

    assert float(keenan["legacy_active_pack_score"]) == pytest.approx(82.4)
    assert float(keenan["private_score"]) != pytest.approx(82.4)
    assert float(darius["legacy_active_pack_score"]) == pytest.approx(78.88)
    if DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.exists():
        assert float(darius["private_score"]) == pytest.approx(23.6148)
        assert darius["lineage_class"] == "review_v4_current_player"
    else:
        assert darius["private_score"] in {"", None}
        assert darius["overall_rank"] == ""
    assert darius["manual_decision_required"] is True


def test_player_board_fails_closed_on_duplicate_model_v4_identity_rows(tmp_path: Path) -> None:
    current_rows = tmp_path / "current_player_value_review_rows.csv"
    _write_current_value_rows(
        current_rows,
        [
            _current_value_row("Keenan Allen", "WR", "41.6097"),
            _current_value_row("Keenan Allen", "WR", "42.0000"),
        ],
    )

    rows = build_player_board_score_rows(ACTIVE_PACK, current_value_path=current_rows)
    keenan = _row(rows, "Keenan Allen")

    assert keenan["private_score"] == ""
    assert keenan["primary_review_score"] == ""
    assert keenan["manual_decision_required"] is True
    assert keenan["identity_uncertain"] is True
    assert "duplicate_identity_join_key" in str(keenan["warning_reasons"])
    assert float(keenan["legacy_active_pack_score"]) == pytest.approx(82.4)


def test_player_board_fails_closed_on_unmatched_model_v4_identity_rows(tmp_path: Path) -> None:
    current_rows = tmp_path / "current_player_value_review_rows.csv"
    _write_current_value_rows(
        current_rows,
        [_current_value_row("Keenan Allen", "WR", "41.6097")],
    )

    rows = build_player_board_score_rows(ACTIVE_PACK, current_value_path=current_rows)
    darius = _row(rows, "Darius Slayton")

    assert darius["private_score"] == ""
    assert darius["primary_review_score"] == ""
    assert darius["manual_decision_required"] is True
    assert darius["identity_uncertain"] is True
    assert "unmatched_identity_join_key" in str(darius["warning_reasons"])
    assert float(darius["legacy_active_pack_score"]) == pytest.approx(78.88)


def test_player_board_requires_manual_review_on_stale_team_or_missing_role_evidence(
    tmp_path: Path,
) -> None:
    current_rows = tmp_path / "current_player_value_review_rows.csv"
    _write_current_value_rows(
        current_rows,
        [
            _current_value_row(
                "Keenan Allen",
                "WR",
                "41.6097",
                warning_flags=(
                    "team_mismatch_or_missing_model_team|"
                    "missing_or_review_route_target_snap_evidence"
                ),
            )
        ],
    )

    rows = build_player_board_score_rows(ACTIVE_PACK, current_value_path=current_rows)
    keenan = _row(rows, "Keenan Allen")

    assert float(keenan["primary_review_score"]) == pytest.approx(41.6097)
    assert keenan["manual_decision_required"] is True
    assert keenan["stale_team_or_status"] is True
    assert keenan["missing_role_evidence"] is True
    assert "stale_team_or_status_evidence" in str(keenan["warning_reasons"])
    assert "missing_role_evidence_gate" in str(keenan["warning_reasons"])


def test_player_board_requires_manual_review_on_partial_or_quarantined_contribution(
    tmp_path: Path,
) -> None:
    current_rows = tmp_path / "current_player_value_review_rows.csv"
    _write_current_value_rows(
        current_rows,
        [
            _current_value_row(
                "Keenan Allen",
                "WR",
                "41.6097",
                warning_flags="source_limited_evidence_cap",
            )
        ],
    )

    rows = build_player_board_score_rows(ACTIVE_PACK, current_value_path=current_rows)
    keenan = _row(rows, "Keenan Allen")

    assert float(keenan["primary_review_score"]) == pytest.approx(41.6097)
    assert keenan["manual_decision_required"] is True
    assert keenan["partial_or_quarantined_contribution"] is True
    assert "partial_or_quarantined_join_evidence" in str(keenan["warning_reasons"])
    assert float(keenan["legacy_active_pack_score"]) == pytest.approx(82.4)


def _row(rows: list[dict[str, object]], player: str) -> dict[str, object]:
    return next(row for row in rows if row["player"] == player)


def _write_current_value_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _current_value_row(
    player_name: str,
    position: str,
    score: str,
    *,
    warning_flags: str = "test_warning",
) -> dict[str, str]:
    return {
        "canonical_player_key": f"nfl:{player_name.lower().replace(' ', '')}:{position}",
        "player_name": player_name,
        "normalized_player_name": player_name.lower().replace(" ", ""),
        "position": position,
        "nfl_team": "UNK",
        "checkpoint_review_score": score,
        "confidence_cap": "0.8",
        "allowed_use": "review_only_current_value_checkpoint",
        "blocked_use": "do_not_use_as_final_ranking_or_roster_recommendation",
        "warning_flags": warning_flags,
        "checkpoint_version": "model_v4_phase_11g_current_value_checkpoint_0.1.0",
    }
