from __future__ import annotations

import pytest

from src.services.replacement_baseline_service import (
    load_replacement_baselines,
    replacement_baseline_rows,
    replacement_gap_score,
)


def test_replacement_baselines_load_both_lve_contexts() -> None:
    baselines = load_replacement_baselines()

    assert ("steady_state", "WR") in baselines
    assert ("declaration_window", "WR") in baselines
    assert baselines[("steady_state", "WR")].weekly_replacement_rank == 46
    assert baselines[("declaration_window", "WR")].stash_threshold_rank == 100
    assert len(replacement_baseline_rows()) == 8


def test_replacement_gap_score_uses_anchor_weekly_and_stash_thresholds() -> None:
    assert replacement_gap_score("WR", 1, context="steady_state") == pytest.approx(100.0)
    assert replacement_gap_score("WR", 15, context="steady_state") == pytest.approx(85.0)
    assert replacement_gap_score("WR", 46, context="steady_state") == pytest.approx(50.0)
    assert replacement_gap_score("WR", 60, context="steady_state") == pytest.approx(20.0)
    assert replacement_gap_score("WR", 66, context="steady_state") == pytest.approx(0.0)
    assert replacement_gap_score("WR", 67, context="steady_state") == pytest.approx(0.0)


def test_replacement_gap_score_keeps_contexts_separate() -> None:
    steady = replacement_gap_score("WR", 70, context="steady_state")
    declaration = replacement_gap_score("WR", 70, context="declaration_window")

    assert steady == pytest.approx(0.0)
    assert declaration > 20.0


def test_unknown_replacement_rank_or_position_neutralizes_to_review_score() -> None:
    assert replacement_gap_score("WR", None) == pytest.approx(50.0)
    assert replacement_gap_score("K", 1) == pytest.approx(50.0)
