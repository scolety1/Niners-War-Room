from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.model_v4_2026_rookie_board_review_service import (
    BOARD_LABEL,
    BOARD_VERSION,
    FORMULA_WEIGHTS,
    INPUT_PACK_VERSION,
    POSITION_FORMAT_FACTORS,
    RANK_LABEL,
    SCORE_LABEL,
    RookieBoardReconstructionError,
    _validate_config,
    assert_output_root_safe,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / "config" / "model_v4_2026_compatible_input_pack_v1.json"


def test_compatible_pack_freezes_existing_analyzer_versions_and_weights() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))

    _validate_config(config)

    assert config["input_pack_version"] == INPUT_PACK_VERSION
    assert config["board_version"] == BOARD_VERSION
    assert config["formula_freeze"] == FORMULA_WEIGHTS
    assert config["format_factors"] == POSITION_FORMAT_FACTORS
    assert config["analyzers"] == {
        "sprint_12_13_version": "model_v4_sprint_12_13_review_0.1.1",
        "sprint_14e_version": "model_v4_sprint_14e_rookie_draft_review_0.1.0",
    }


def test_review_only_labels_are_exact() -> None:
    assert SCORE_LABEL == "Rookie Analyzer Review Score"
    assert RANK_LABEL == "2026 Rookie Review Rank"
    assert BOARD_LABEL == "Review-Only"


@pytest.mark.parametrize(
    "path",
    [
        "full_player_board_value_review_rows.csv",
        "OUTCOME_V3_INTEGRATION_PACK.csv",
        "PROSPECTIVE_2026_BASELINE_FREEZE.csv",
        "local_exports/active_pack/rookies.csv",
        "local_exports/trading_lab/rookies.csv",
    ],
)
def test_protected_output_paths_fail_closed(path: str) -> None:
    with pytest.raises(
        RookieBoardReconstructionError, match="protected production/output path"
    ):
        assert_output_root_safe(Path(path))


def test_isolated_research_output_path_is_allowed(tmp_path: Path) -> None:
    assert_output_root_safe(tmp_path / "model_v4_2026_rookie_board" / "run-a")
