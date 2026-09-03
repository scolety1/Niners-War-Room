import pytest

from src.services.calibration_toolkit_service import (
    PIPELINE_TEST_ONLY,
    REAL_EVIDENCE,
    CalibrationToolkitError,
    bucket_team_score_outcomes,
    evaluate_probability_calibration,
    fit_isotonic_regression,
    fit_pick_score_calibrator,
)
from src.services.outcome_evaluation_framework_service import OBSERVED, SIMULATED


def test_fit_isotonic_regression_rejects_an_unknown_data_source() -> None:
    with pytest.raises(CalibrationToolkitError):
        fit_isotonic_regression([1.0, 2.0], [1.0, 2.0], data_source="MADE_UP", model_version="v1")


def test_isotonic_fit_on_already_monotonic_data_reproduces_it_closely() -> None:
    model = fit_isotonic_regression(
        [1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0],
        data_source=PIPELINE_TEST_ONLY, model_version="v1",
    )
    assert model.predict(1.0) == pytest.approx(10.0)
    assert model.predict(4.0) == pytest.approx(40.0)
    assert model.predict(2.5) == pytest.approx(25.0, abs=5.0)


def test_isotonic_fit_pools_a_violation_pair() -> None:
    # y decreases from x=1 to x=2 -- PAVA must pool them into one
    # non-decreasing block (mean of the two), not just leave it violated.
    model = fit_isotonic_regression(
        [1.0, 2.0, 3.0], [10.0, 5.0, 30.0], data_source=PIPELINE_TEST_ONLY, model_version="v1",
    )
    # Predictions must be non-decreasing across the fitted range.
    predictions = [model.predict(x) for x in (1.0, 1.5, 2.0, 2.5, 3.0)]
    assert predictions == sorted(predictions)


def test_isotonic_prediction_clamps_outside_the_fitted_range() -> None:
    model = fit_isotonic_regression(
        [1.0, 2.0], [10.0, 20.0], data_source=PIPELINE_TEST_ONLY, model_version="v1",
    )
    assert model.predict(-5.0) == 10.0
    assert model.predict(100.0) == 20.0


def test_pick_score_calibrator_is_monotonic_and_bounded_0_100() -> None:
    pairs = [(-5.0, 20.0), (0.0, 50.0), (5.0, 70.0), (10.0, 95.0)]
    calibrator = fit_pick_score_calibrator(pairs, data_source=PIPELINE_TEST_ONLY)
    assert PIPELINE_TEST_ONLY in calibrator.model_version
    scores = [calibrator.calibrate(x) for x in (-5.0, 0.0, 5.0, 10.0)]
    assert scores == sorted(scores)
    assert all(0.0 <= s <= 100.0 for s in scores)


def test_pick_score_calibrator_real_evidence_source_is_labeled_distinctly() -> None:
    pairs = [(-5.0, 20.0), (5.0, 70.0)]
    calibrator = fit_pick_score_calibrator(pairs, data_source=REAL_EVIDENCE)
    assert PIPELINE_TEST_ONLY not in calibrator.model_version
    assert calibrator.data_source == REAL_EVIDENCE


def test_bucket_team_score_outcomes_detects_monotonic_real_relationship() -> None:
    pairs = [(10.0, 100.0), (30.0, 150.0), (50.0, 200.0), (70.0, 250.0), (90.0, 300.0)]
    report = bucket_team_score_outcomes(pairs, data_source=PIPELINE_TEST_ONLY, bucket_count=5)
    assert report.monotonic is True
    assert report.spearman == pytest.approx(1.0)
    assert report.sample_size == 5


def test_bucket_team_score_outcomes_detects_a_non_monotonic_relationship() -> None:
    pairs = [(10.0, 300.0), (30.0, 100.0), (50.0, 200.0), (70.0, 150.0), (90.0, 250.0)]
    report = bucket_team_score_outcomes(pairs, data_source=PIPELINE_TEST_ONLY, bucket_count=5)
    assert report.monotonic is False


def test_probability_calibration_requires_an_explicit_label_source() -> None:
    with pytest.raises(CalibrationToolkitError):
        evaluate_probability_calibration([(0.5, 1.0)], label_source="MADE_UP")


def test_probability_calibration_computes_a_real_brier_score() -> None:
    pairs = [(0.9, 1.0), (0.1, 0.0), (0.5, 1.0), (0.5, 0.0)]
    report = evaluate_probability_calibration(pairs, label_source=SIMULATED)
    # Brier = mean((p - o)^2) = (0.01 + 0.01 + 0.25 + 0.25) / 4 = 0.13
    assert report.brier_score == pytest.approx(0.13, abs=1e-6)
    assert report.label_source == SIMULATED


def test_probability_calibration_never_defaults_to_observed() -> None:
    pairs = [(0.5, 1.0)]
    report = evaluate_probability_calibration(pairs, label_source=OBSERVED)
    assert report.label_source == OBSERVED
    # Confirms the label is carried through exactly as given, not silently
    # coerced to SIMULATED or vice versa.


def test_reliability_bins_never_hide_a_bin_with_zero_samples() -> None:
    pairs = [(0.05, 0.0), (0.95, 1.0)]
    report = evaluate_probability_calibration(pairs, label_source=SIMULATED, bin_count=5)
    # Only 2 of 5 bins have data -- the other 3 must simply be absent,
    # never fabricated with a fake sample_size=0 entry.
    assert len(report.reliability_bins) == 2
    assert all(b.sample_size > 0 for b in report.reliability_bins)
