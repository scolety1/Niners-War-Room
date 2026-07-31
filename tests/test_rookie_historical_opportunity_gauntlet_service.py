from __future__ import annotations

import pytest

from src.services.rookie_historical_opportunity_gauntlet_service import (
    MUTATIONS,
    Fold,
    GauntletContractError,
    PromotionGate,
    chronological_outer_folds,
    expected_calibration_error,
    ndcg,
    pr_auc,
    safe_ratio,
    same_row_ids,
    spearman,
    validate_feature_name,
    validate_fold,
    validate_join_mode,
    validate_mutation,
    validate_outcome_season,
    validate_output_path,
)


def test_chronological_outer_folds_use_only_earlier_classes() -> None:
    folds = chronological_outer_folds(range(2012, 2026), min_train_classes=4)
    assert folds[0] == Fold(2016, (2012, 2013, 2014, 2015))
    assert folds[-1].test_class == 2025
    assert max(folds[-1].train_classes) == 2024
    for fold in folds:
        validate_fold(fold, fold.train_classes)


@pytest.mark.parametrize(
    "fold,normalization",
    [
        (Fold(2020, (2018, 2020)), (2018,)),
        (Fold(2020, (2018, 2019)), (2018, 2020)),
    ],
)
def test_temporal_mutations_fail(fold: Fold, normalization: tuple[int, ...]) -> None:
    with pytest.raises(GauntletContractError):
        validate_fold(fold, normalization)


def test_outcome_maturity_and_2026_are_fail_closed() -> None:
    validate_outcome_season(2023, 3, 2025)
    with pytest.raises(GauntletContractError):
        validate_outcome_season(2024, 3, 2026)
    with pytest.raises(GauntletContractError):
        validate_outcome_season(2026, 1, 2026)


@pytest.mark.parametrize(
    "mode", ["name_only", "normalized_name", "nearest_name", "name_plus_college"]
)
def test_identity_shortcuts_fail(mode: str) -> None:
    with pytest.raises(GauntletContractError):
        validate_join_mode(mode)
    validate_join_mode("cfbd_draft_year_overall_to_exact_gsis")


def test_semantic_mislabeling_fails() -> None:
    validate_feature_name("RB_REC_PER_TEAM_PA")
    with pytest.raises(GauntletContractError):
        validate_feature_name("rb_targets_from_receptions")
    with pytest.raises(GauntletContractError):
        validate_feature_name("qb_pressure_to_sack_rate")
    with pytest.raises(GauntletContractError):
        validate_feature_name("post_draft_adp")


def test_missingness_is_not_zero() -> None:
    assert safe_ratio(None, 10) is None
    assert safe_ratio(4, 0) is None
    assert safe_ratio(4, 8) == 0.5


def test_same_row_comparison_is_enforced() -> None:
    assert same_row_ids(["b", "a"], ["a", "b"]) == ("a", "b")
    with pytest.raises(GauntletContractError):
        same_row_ids(["a", "b"], ["a"])


def test_metrics_are_deterministic() -> None:
    assert spearman([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
    assert ndcg([0, 1, 3], [0, 1, 3]) == pytest.approx(1.0)
    assert pr_auc([0, 1, 1], [0.1, 0.8, 0.9]) == pytest.approx(1.0)
    assert expected_calibration_error([0, 1], [0.1, 0.9]) == pytest.approx(0.1)


def test_promotion_gate_requires_all_materiality_and_safety_terms() -> None:
    passing = PromotionGate(0.02, 0.60, 0.01, 0.0, 0.01, True, True, True)
    assert passing.passes()
    assert not PromotionGate(0.02, 0.59, 0.01, 0.0, 0.01, True, True, True).passes()


def test_all_twenty_real_path_mutations_are_rejected() -> None:
    assert len(MUTATIONS) == 20
    for mutation in MUTATIONS:
        with pytest.raises(GauntletContractError, match="mutation blocked"):
            validate_mutation(mutation)


def test_output_path_gate_blocks_production_targets() -> None:
    validate_output_path(
        "docs/hq/master/nwr_rookie_historical_opportunity_feature_gauntlet_v1_20260731/x.csv"
    )
    with pytest.raises(GauntletContractError):
        validate_output_path("data_packs/active/x.csv")

