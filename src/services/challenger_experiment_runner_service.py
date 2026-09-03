"""Hyperparameter / challenger experiment runner (directive section 25).

A bounded experiment runner: given a small, PRE-DECLARED grid of
(strategy/model version, feature set, parameter set, train/validate/
holdout windows, league formats, seed) combinations, runs each one
through a caller-supplied evaluator and returns one `ExperimentReceipt`
per combination -- metrics, runtime, failures, and provenance, never a
brute-forced massive grid (the directive's own explicit instruction).

This module does not know how to evaluate anything itself -- it is pure
orchestration over a caller-supplied `evaluate` callback (e.g. running
`historical_draft_replay_engine_service.run_historical_draft_replay` plus
`outcome_evaluation_framework_service` metrics, or a rookie challenger
backtest) so it stays usable for any future challenger shape without
this module needing to know about draft strategies, rookies, or any
other domain specifics.
"""

from __future__ import annotations

import time
import traceback
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

MAX_EXPERIMENT_GRID_SIZE = 50


class ChallengerExperimentRunnerError(ValueError):
    pass


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    strategy_version: str
    feature_set_version: str
    parameter_set: Mapping[str, Any]
    train_window: str
    validate_window: str
    holdout_window: str
    league_formats: tuple[str, ...]
    seed: int


@dataclass(frozen=True)
class ExperimentReceipt:
    experiment_id: str
    spec: ExperimentSpec
    succeeded: bool
    metrics: Mapping[str, Any]
    runtime_seconds: float
    failure_reason: str | None
    provenance: Mapping[str, Any]


ExperimentEvaluator = Callable[[ExperimentSpec], Mapping[str, Any]]


def run_experiment_grid(
    specs: Sequence[ExperimentSpec],
    evaluate: ExperimentEvaluator,
) -> tuple[ExperimentReceipt, ...]:
    """Runs every spec through `evaluate`, catching and recording any
    failure per-experiment rather than letting one bad combination abort
    the whole grid -- a caller can inspect `succeeded`/`failure_reason`
    per receipt. Refuses a grid larger than MAX_EXPERIMENT_GRID_SIZE
    (the directive's own "do not brute-force massive grids" instruction,
    enforced rather than just stated) and refuses duplicate
    experiment_ids (each receipt must be individually addressable)."""
    if len(specs) > MAX_EXPERIMENT_GRID_SIZE:
        raise ChallengerExperimentRunnerError(
            f"Experiment grid of {len(specs)} exceeds the bounded maximum of "
            f"{MAX_EXPERIMENT_GRID_SIZE} -- predeclare a smaller, deliberate grid."
        )
    seen_ids: set[str] = set()
    for spec in specs:
        if spec.experiment_id in seen_ids:
            raise ChallengerExperimentRunnerError(
                f"Duplicate experiment_id: {spec.experiment_id!r}"
            )
        seen_ids.add(spec.experiment_id)

    receipts: list[ExperimentReceipt] = []
    for spec in specs:
        start = time.perf_counter()
        try:
            metrics = evaluate(spec)
            elapsed = time.perf_counter() - start
            receipts.append(
                ExperimentReceipt(
                    experiment_id=spec.experiment_id, spec=spec, succeeded=True,
                    metrics=metrics, runtime_seconds=round(elapsed, 4), failure_reason=None,
                    provenance=_provenance(spec),
                )
            )
        except Exception as exc:  # noqa: BLE001 -- deliberately broad: one bad
            # experiment must never abort the rest of a predeclared grid.
            elapsed = time.perf_counter() - start
            receipts.append(
                ExperimentReceipt(
                    experiment_id=spec.experiment_id, spec=spec, succeeded=False,
                    metrics={}, runtime_seconds=round(elapsed, 4),
                    failure_reason=f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=3)}",
                    provenance=_provenance(spec),
                )
            )
    return tuple(receipts)


def _provenance(spec: ExperimentSpec) -> Mapping[str, Any]:
    return {
        "strategy_version": spec.strategy_version,
        "feature_set_version": spec.feature_set_version,
        "parameter_set": dict(spec.parameter_set),
        "train_window": spec.train_window,
        "validate_window": spec.validate_window,
        "holdout_window": spec.holdout_window,
        "league_formats": spec.league_formats,
        "seed": spec.seed,
    }


def summarize_experiment_grid(receipts: Sequence[ExperimentReceipt]) -> Mapping[str, Any]:
    """A small, honest rollup -- succeeded/failed counts and total
    runtime, never silently hiding failures inside an aggregate metric."""
    succeeded = [r for r in receipts if r.succeeded]
    failed = [r for r in receipts if not r.succeeded]
    return {
        "total": len(receipts),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "failed_experiment_ids": tuple(r.experiment_id for r in failed),
        "total_runtime_seconds": round(sum(r.runtime_seconds for r in receipts), 4),
    }
