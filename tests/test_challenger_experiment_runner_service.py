import pytest

from src.services.challenger_experiment_runner_service import (
    MAX_EXPERIMENT_GRID_SIZE,
    ChallengerExperimentRunnerError,
    ExperimentSpec,
    run_experiment_grid,
    summarize_experiment_grid,
)


def _spec(experiment_id: str, **overrides) -> ExperimentSpec:
    defaults = dict(
        experiment_id=experiment_id, strategy_version="v1", feature_set_version="fs-v1",
        parameter_set={"blend_weight": 0.3}, train_window="2020-2022",
        validate_window="2023", holdout_window="2024",
        league_formats=("10T_1QB", "12T_1QB"), seed=7,
    )
    defaults.update(overrides)
    return ExperimentSpec(**defaults)


def test_run_experiment_grid_calls_the_evaluator_for_every_spec() -> None:
    specs = [_spec("e1"), _spec("e2", seed=8)]
    calls = []

    def evaluate(spec):
        calls.append(spec.experiment_id)
        return {"mean_error": 0.1}

    receipts = run_experiment_grid(specs, evaluate)
    assert len(receipts) == 2
    assert set(calls) == {"e1", "e2"}
    assert all(r.succeeded for r in receipts)


def test_a_failing_experiment_does_not_abort_the_rest_of_the_grid() -> None:
    specs = [_spec("good"), _spec("bad")]

    def evaluate(spec):
        if spec.experiment_id == "bad":
            raise RuntimeError("synthetic evaluator failure")
        return {"mean_error": 0.05}

    receipts = run_experiment_grid(specs, evaluate)
    by_id = {r.experiment_id: r for r in receipts}
    assert by_id["good"].succeeded is True
    assert by_id["bad"].succeeded is False
    assert "synthetic evaluator failure" in by_id["bad"].failure_reason


def test_grid_rejects_duplicate_experiment_ids() -> None:
    specs = [_spec("dup"), _spec("dup", seed=9)]
    with pytest.raises(ChallengerExperimentRunnerError):
        run_experiment_grid(specs, lambda spec: {})


def test_grid_refuses_to_brute_force_beyond_the_bounded_maximum() -> None:
    specs = [_spec(f"e{i}") for i in range(MAX_EXPERIMENT_GRID_SIZE + 1)]
    with pytest.raises(ChallengerExperimentRunnerError):
        run_experiment_grid(specs, lambda spec: {})


def test_receipt_provenance_carries_every_declared_input() -> None:
    receipts = run_experiment_grid([_spec("e1")], lambda spec: {"mean_error": 0.1})
    provenance = receipts[0].provenance
    assert provenance["strategy_version"] == "v1"
    assert provenance["parameter_set"] == {"blend_weight": 0.3}
    assert provenance["league_formats"] == ("10T_1QB", "12T_1QB")


def test_summarize_experiment_grid_never_hides_a_failure_inside_the_rollup() -> None:
    specs = [_spec("good"), _spec("bad")]

    def evaluate(spec):
        if spec.experiment_id == "bad":
            raise ValueError("boom")
        return {"mean_error": 0.05}

    receipts = run_experiment_grid(specs, evaluate)
    summary = summarize_experiment_grid(receipts)
    assert summary["total"] == 2
    assert summary["succeeded"] == 1
    assert summary["failed"] == 1
    assert summary["failed_experiment_ids"] == ("bad",)
