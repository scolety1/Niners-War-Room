import pytest

from src.services.calibration_acceptance_gates_service import (
    ALL_GATE_SPECS,
    GATE_FAIL,
    GATE_PASS,
    GATE_UNSCORABLE,
    CalibrationGateError,
    evaluate_gate,
    evaluate_gates_for_subject,
)


def _spec(gate_id: str):
    return next(s for s in ALL_GATE_SPECS if s.gate_id == gate_id)


def test_every_declared_gate_has_a_non_empty_rationale() -> None:
    for spec in ALL_GATE_SPECS:
        assert spec.rationale.strip()


def test_gates_with_no_real_prior_basis_declare_threshold_none() -> None:
    # A sample -- not every gate, just confirming the pattern is real, not
    # accidental (some gates DO have a real defensible floor, e.g. zero
    # tolerance for construction regression).
    unscored = [spec for spec in ALL_GATE_SPECS if spec.threshold is None]
    assert len(unscored) > 0
    assert any(spec.comparison != "IMPROVES_ON_BASELINE" for spec in unscored)


def test_evaluate_gate_is_unscorable_when_the_metric_was_not_computed() -> None:
    spec = _spec("pick_score.no_catastrophic_construction_regression")
    result = evaluate_gate(spec, observed={})
    assert result.status == GATE_UNSCORABLE


def test_evaluate_gate_is_unscorable_when_no_threshold_is_declared_yet() -> None:
    spec = _spec("team_score.stability_across_seasons_formats")
    result = evaluate_gate(spec, observed={"cross_slice_spearman_variance": 0.02})
    assert result.status == GATE_UNSCORABLE


def test_evaluate_gate_passes_a_real_threshold_comparison() -> None:
    spec = _spec("team_score.positive_holdout_rank_correlation")
    passing = evaluate_gate(spec, observed={"spearman": 0.4})
    failing = evaluate_gate(spec, observed={"spearman": -0.1})
    assert passing.status == GATE_PASS
    assert failing.status == GATE_FAIL


def test_evaluate_gate_handles_improves_on_baseline_comparison() -> None:
    spec = _spec("pick_score.lower_regret_than_baseline")
    metric = "mean_realized_pick_regret"
    better = evaluate_gate(spec, observed={metric: 5.0, f"{metric}__baseline": 10.0})
    worse = evaluate_gate(spec, observed={metric: 15.0, f"{metric}__baseline": 10.0})
    unscorable = evaluate_gate(spec, observed={metric: 5.0})
    assert better.status == GATE_PASS
    assert worse.status == GATE_FAIL
    assert unscorable.status == GATE_UNSCORABLE


def test_evaluate_gate_rejects_an_unknown_gate_id() -> None:
    from src.services.calibration_acceptance_gates_service import GateSpec

    fake = GateSpec(
        gate_id="not_a_real_gate", subject="TEAM_SCORE", metric_name="x",
        comparison=">=", threshold=0.0, rationale="fake",
    )
    with pytest.raises(CalibrationGateError):
        evaluate_gate(fake, observed={"x": 1.0})


def test_evaluate_gates_for_subject_returns_every_declared_gate_for_that_subject() -> None:
    results = evaluate_gates_for_subject("PICK_SCORE", observed={})
    assert len(results) == len(
        [spec for spec in ALL_GATE_SPECS if spec.subject == "PICK_SCORE"]
    )


def test_evaluate_gates_for_subject_rejects_an_unknown_subject() -> None:
    with pytest.raises(CalibrationGateError):
        evaluate_gates_for_subject("NOT_A_REAL_SUBJECT", observed={})


def test_rookie_challenger_gate_thresholds_come_directly_from_directive_wording() -> None:
    spec = _spec("rookie_challenger.improves_across_multiple_classes")
    assert spec.threshold == 2.0  # "not merely 2026 KHA" -> at least 2 classes
