"""Predeclared calibration acceptance gates (directive section 16).

Declared BEFORE any real historical result is seen -- these thresholds
are written from general reasoning about what "the model works" should
mean, not chosen after looking at a real (or even synthetic) run's
numbers to make NWR look good. Where no real prior basis exists for a
specific number, the metric and comparison rule are declared without a
fabricated threshold (`threshold=None`), per the directive's own explicit
instruction not to invent an unrealistic number just to have one.

Evaluating a `GateSpec` against real results is purely mechanical
(`evaluate_gate`) -- this module makes no promotion decision; it only
reports PASS/FAIL/UNSCORABLE per gate, for a human (or
`champion_challenger_registry_service.record_promotion_decision`,
already gated behind a human identity) to act on.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

GATE_PASS = "PASS"
GATE_FAIL = "FAIL"
GATE_UNSCORABLE = "UNSCORABLE"  # the metric this gate needs was not computable this run


class CalibrationGateError(ValueError):
    pass


@dataclass(frozen=True)
class GateSpec:
    gate_id: str
    # e.g. "TEAM_SCORE", "CHAMPIONSHIP_EQUITY", "PICK_SCORE", "COST_OF_WAITING",
    # "ROOKIE_CHALLENGER".
    subject: str
    metric_name: str
    comparison: str  # ">=" | "<=" | "==" | "MONOTONIC_NONDECREASING" | "IMPROVES_ON_BASELINE"
    threshold: float | None  # None when no real prior basis exists for a specific number
    rationale: str


@dataclass(frozen=True)
class GateEvaluation:
    gate_id: str
    status: str
    observed_value: float | bool | None
    detail: str


# --- Predeclared gate set ----------------------------------------------------
# One GateSpec per directive-named criterion. Every `threshold=None` entry
# is deliberate -- see each rationale for why no number is fabricated.

TEAM_SCORE_GATES = (
    GateSpec(
        gate_id="team_score.monotonic_with_realized_strength", subject="TEAM_SCORE",
        metric_name="monotonic", comparison="== True", threshold=None,
        rationale="Higher Team Score buckets must show non-decreasing mean realized "
        "roster strength -- a binary pass/fail, not a magnitude threshold.",
    ),
    GateSpec(
        gate_id="team_score.positive_holdout_rank_correlation", subject="TEAM_SCORE",
        metric_name="spearman", comparison=">=", threshold=0.0,
        rationale="Merely positive is the floor -- Team Score must correlate in the "
        "right DIRECTION with realized outcomes on held-out data before any stronger "
        "claim is meaningful. No specific magnitude (e.g. 0.3, 0.5) is fabricated "
        "without a real prior distribution of what's achievable to compare against.",
    ),
    GateSpec(
        gate_id="team_score.stability_across_seasons_formats", subject="TEAM_SCORE",
        metric_name="cross_slice_spearman_variance", comparison="<=", threshold=None,
        rationale="Stability requires multiple real seasons/formats to even measure "
        "variance across -- no threshold fabricated before that data exists.",
    ),
)

CHAMPIONSHIP_EQUITY_GATES = (
    GateSpec(
        gate_id="championship_equity.beats_declared_baseline", subject="CHAMPIONSHIP_EQUITY",
        metric_name="brier_score", comparison="IMPROVES_ON_BASELINE", threshold=None,
        rationale="Must be compared against a declared baseline (e.g. seed-based "
        "uniform-probability or ADP-rank-based baseline) computed the same way -- "
        "not an absolute number until that baseline itself is chosen and run.",
    ),
    GateSpec(
        gate_id="championship_equity.discrimination", subject="CHAMPIONSHIP_EQUITY",
        metric_name="expected_calibration_error", comparison="<=", threshold=None,
        rationale="No real historical championship outcome sample exists yet to set an "
        "ECE threshold against; declaring the metric now, not a fabricated number.",
    ),
)

PICK_SCORE_GATES = (
    GateSpec(
        gate_id="pick_score.lower_regret_than_baseline", subject="PICK_SCORE",
        metric_name="mean_realized_pick_regret", comparison="IMPROVES_ON_BASELINE",
        threshold=None,
        rationale="Regret must be lower than the declared baseline strategy's own "
        "regret on the SAME picks -- a relative, not absolute, criterion.",
    ),
    GateSpec(
        gate_id="pick_score.monotonic_outcome_by_bucket", subject="PICK_SCORE",
        metric_name="monotonic", comparison="== True", threshold=None,
        rationale="Higher Pick Score buckets must show non-decreasing realized outcome "
        "quality -- binary, not a magnitude.",
    ),
    GateSpec(
        gate_id="pick_score.no_catastrophic_construction_regression", subject="PICK_SCORE",
        metric_name="roster_construction_failure_count", comparison="<=", threshold=0,
        rationale="A promotable Pick Score strategy must not increase starter-hole "
        "counts versus the champion strategy on the same replay -- zero tolerance is "
        "a real, defensible floor (not merely 'better on average').",
    ),
)

COST_OF_WAITING_GATES = (
    GateSpec(
        gate_id="cost_of_waiting.reasonably_calibrated_survival", subject="COST_OF_WAITING",
        metric_name="expected_calibration_error", comparison="<=", threshold=None,
        rationale="No real make-it-back sample exists yet to set a numeric ECE floor.",
    ),
    GateSpec(
        gate_id="cost_of_waiting.improves_on_raw_adp_gap", subject="COST_OF_WAITING",
        metric_name="brier_score", comparison="IMPROVES_ON_BASELINE", threshold=None,
        rationale="Must beat the raw-ADP-gap-only baseline's own Brier score on the "
        "same picks -- relative, not absolute.",
    ),
)

ROOKIE_CHALLENGER_GATES = (
    GateSpec(
        gate_id="rookie_challenger.improves_across_multiple_classes",
        subject="ROOKIE_CHALLENGER", metric_name="classes_improved_count", comparison=">=",
        threshold=2.0,
        rationale="'Not merely 2026 KHA' -- at least 2 distinct real rookie classes "
        "must show improvement, a real, defensible floor directly from the "
        "directive's own wording, not a magnitude threshold requiring a prior "
        "distribution.",
    ),
    GateSpec(
        gate_id="rookie_challenger.no_unacceptable_subgroup_degradation",
        subject="ROOKIE_CHALLENGER", metric_name="worst_subgroup_degradation",
        comparison="<=", threshold=0.0,
        rationale="No named subgroup (position, tier, etc.) may get WORSE under the "
        "challenger versus champion -- zero tolerance, a real floor.",
    ),
)

ALL_GATE_SPECS: tuple[GateSpec, ...] = (
    TEAM_SCORE_GATES + CHAMPIONSHIP_EQUITY_GATES + PICK_SCORE_GATES
    + COST_OF_WAITING_GATES + ROOKIE_CHALLENGER_GATES
)


def evaluate_gate(spec: GateSpec, *, observed: Mapping[str, float | bool | None]) -> GateEvaluation:
    """Purely mechanical -- makes no promotion decision. Returns
    UNSCORABLE (never a silent PASS) when the metric this gate needs
    was not computed this run, or when the gate's own threshold is
    still None (no real basis declared yet)."""
    if spec.gate_id not in {s.gate_id for s in ALL_GATE_SPECS}:
        raise CalibrationGateError(f"Unknown gate_id: {spec.gate_id!r}")
    value = observed.get(spec.metric_name)
    if value is None:
        return GateEvaluation(
            gate_id=spec.gate_id, status=GATE_UNSCORABLE, observed_value=None,
            detail=f"{spec.metric_name} was not computed this run.",
        )
    if spec.threshold is None and spec.comparison not in {"IMPROVES_ON_BASELINE"}:
        return GateEvaluation(
            gate_id=spec.gate_id, status=GATE_UNSCORABLE, observed_value=value,
            detail="No threshold declared yet (no real prior basis) -- see rationale.",
        )
    if spec.comparison == "IMPROVES_ON_BASELINE":
        baseline_value = observed.get(f"{spec.metric_name}__baseline")
        if baseline_value is None:
            return GateEvaluation(
                gate_id=spec.gate_id, status=GATE_UNSCORABLE, observed_value=value,
                detail=f"No {spec.metric_name}__baseline supplied for comparison.",
            )
        passed = float(value) < float(baseline_value)
        return GateEvaluation(
            gate_id=spec.gate_id, status=GATE_PASS if passed else GATE_FAIL, observed_value=value,
            detail=f"{value} vs baseline {baseline_value}",
        )
    if spec.comparison == "== True":
        passed = bool(value) is True
    elif spec.comparison == ">=":
        passed = float(value) >= float(spec.threshold)
    elif spec.comparison == "<=":
        passed = float(value) <= float(spec.threshold)
    else:
        raise CalibrationGateError(f"Unknown comparison: {spec.comparison!r}")
    return GateEvaluation(
        gate_id=spec.gate_id, status=GATE_PASS if passed else GATE_FAIL, observed_value=value,
        detail=f"{value} {spec.comparison} {spec.threshold}",
    )


def evaluate_gates_for_subject(
    subject: str, *, observed: Mapping[str, float | bool | None]
) -> tuple[GateEvaluation, ...]:
    specs = [spec for spec in ALL_GATE_SPECS if spec.subject == subject]
    if not specs:
        raise CalibrationGateError(f"No gates declared for subject: {subject!r}")
    return tuple(evaluate_gate(spec, observed=observed) for spec in specs)
