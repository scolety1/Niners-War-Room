"""Shared cross-metric result-status contract (owner-feedback closure).

Every decision-support metric (Player Score, Team Score, Championship Equity,
Cost of Waiting, Make-It-Back, Raw Action Value / expected regret, Pick
Score) already discloses SOME of its own status today, but each does it a
different, ad hoc way -- a `warnings` string here, a `None` there, a
"OK"/"UNAVAILABLE: <reason>" string somewhere else. This module gives every
one of those metrics ONE shared, additive status shape instead of a new
parallel system: it reads the SAME already-computed values/conditions each
metric's own service already exposes and labels them consistently. It never
recomputes, retunes, or overrides a metric's own numeric value.

Three independent axes, deliberately NOT collapsed into one label, because a
single result can be true on more than one of them at once (a candidate can
be a real, evaluated, genuine tie AND still rest on a stale input snapshot):

- `computation_state`: did the metric actually run for this candidate, and
  if not, why. One of EVALUATED / PENDING / BUDGET_LIMITED / UNSUPPORTED /
  MISSING_INPUT / ERROR. Never inferred from the numeric value itself (a
  real 0.0 is EVALUATED with `genuine_zero=True`, never MISSING_INPUT).
- Result properties: `genuine_zero` (the value is a real, computed zero, not
  a stand-in for "unknown") and `tied_no_spread` (every candidate in this
  evaluation shares the same underlying value -- None where a metric has no
  meaningful notion of a "tie", e.g. Player Score).
- Evidence/data properties: `validation_domain` (what historical validation,
  if any, backs this metric -- a fixed per-metric-family fact, not
  recomputed here) and `source_freshness` (the projection snapshot's own
  `source_as_of`, shared by every metric that consumes projections).
  `data_coverage` is an optional short note for a metric whose evaluated
  population is itself limited (e.g. Make-It-Back's trial count).

A missing/unevaluated value is NEVER coerced to 0, 50, or 100% anywhere in
this module -- `computation_state` carries that fact instead, and the raw
value stays whatever the underlying metric actually returned (including
`None`).
"""

from __future__ import annotations

from dataclasses import dataclass

COMPUTATION_STATES = (
    "EVALUATED",
    "PENDING",
    "BUDGET_LIMITED",
    "UNSUPPORTED",
    "MISSING_INPUT",
    "ERROR",
)

# Fixed per-metric-family validation-domain facts. Deliberately conservative:
# each string only restates a verdict already shipped elsewhere in this
# codebase (see the constants/labels referenced in each comment), never a
# new claim invented for this module.
TEAM_SCORE_VALIDATION_DOMAIN = (
    "TEAM SCORE — RESEARCH. Frozen formula; historically backtested against "
    "2016, 2024, and 2025 holdouts, all now burned. No live/blind holdout remains."
)
CHAMPIONSHIP_EQUITY_VALIDATION_DOMAIN = (
    "CHAMPIONSHIP EQUITY — SIMULATED RESEARCH. Monte Carlo simulation over "
    "Team Score/ADP inputs; no independent historical holdout backs this metric."
)
PICK_SCORE_VALIDATION_DOMAIN = (
    "RESEARCH_ONLY_PICK_SCORE. Composite of Team Score + Championship Equity; "
    "Decision Confidence is a standing NOT_VALIDATED program verdict."
)
PLAYER_SCORE_VALIDATION_DOMAIN = (
    "Walk-forward validated against ADP (beat ADP 9/9 seasons); weaker at QB "
    "and at the very top of the market -- see the walk-forward findings."
)
COST_OF_WAITING_VALIDATION_DOMAIN = (
    "Derived from the same Championship Equity Monte Carlo engine; inherits "
    "its NOT independently historically validated status."
)
MAKE_IT_BACK_VALIDATION_DOMAIN = (
    "Monte Carlo survival probability; sensitivity-tested (opponent position "
    "caps, intervening-pick count, seed/trial consumption) but not an "
    "independent historical holdout."
)
RAW_ACTION_VALUE_VALIDATION_DOMAIN = (
    "Raw Action Value / expected regret / decision-quality percentile: real "
    "wiring of the frozen decision_engine_v2_contracts_service formulas, "
    "computed only for the top max_rav_candidates for cost control -- see "
    "raw_action_value_live_service.py for the full trace."
)


@dataclass(frozen=True)
class MetricStatus:
    computation_state: str
    genuine_zero: bool
    tied_no_spread: bool | None
    validation_domain: str
    source_freshness: str
    data_coverage: str | None = None

    def __post_init__(self) -> None:
        if self.computation_state not in COMPUTATION_STATES:
            raise ValueError(f"Unknown computation_state: {self.computation_state!r}")


def _freshness(source_as_of: str) -> str:
    return f"Projection snapshot source_as_of={source_as_of}" if source_as_of else "UNKNOWN"


def player_score_status(value: float | None, *, source_as_of: str) -> MetricStatus:
    if value is None:
        return MetricStatus(
            computation_state="MISSING_INPUT",
            genuine_zero=False,
            tied_no_spread=None,
            validation_domain=PLAYER_SCORE_VALIDATION_DOMAIN,
            source_freshness=_freshness(source_as_of),
        )
    return MetricStatus(
        computation_state="EVALUATED",
        genuine_zero=value == 0.0,
        tied_no_spread=None,
        validation_domain=PLAYER_SCORE_VALIDATION_DOMAIN,
        source_freshness=_freshness(source_as_of),
    )


def team_score_status(value: float, *, source_as_of: str) -> MetricStatus:
    return MetricStatus(
        computation_state="EVALUATED",
        genuine_zero=value == 0.0,
        tied_no_spread=None,
        validation_domain=TEAM_SCORE_VALIDATION_DOMAIN,
        source_freshness=_freshness(source_as_of),
    )


def championship_equity_status(
    value: float, *, standard_error: float, source_as_of: str
) -> MetricStatus:
    coverage = f"Monte Carlo standard error={standard_error:.4f}"
    return MetricStatus(
        computation_state="EVALUATED",
        genuine_zero=value == 0.0,
        tied_no_spread=None,
        validation_domain=CHAMPIONSHIP_EQUITY_VALIDATION_DOMAIN,
        source_freshness=_freshness(source_as_of),
        data_coverage=coverage,
    )


def cost_of_waiting_status(
    value: float, *, from_v2_evaluation: bool, source_as_of: str
) -> MetricStatus:
    """`from_v2_evaluation=False` means this candidate fell back to the
    plainer Pick-Score-embedded estimate because the richer per-candidate
    Cost-of-Waiting-V2 evaluation did not cover it (e.g.
    `include_cost_of_waiting=False` for this bundle) -- a real, previously
    silent evidence-quality distinction, now disclosed via `data_coverage`
    rather than left indistinguishable from a fully-evaluated value."""
    return MetricStatus(
        computation_state="EVALUATED",
        genuine_zero=value == 0.0,
        tied_no_spread=None,
        validation_domain=COST_OF_WAITING_VALIDATION_DOMAIN,
        source_freshness=_freshness(source_as_of),
        data_coverage=(
            "Full Cost-of-Waiting-V2 evaluation"
            if from_v2_evaluation
            else "Fallback: Pick-Score-embedded estimate, not the full V2 evaluation"
        ),
    )


def make_it_back_status(
    probability: float | None, trials: int | None, *, source_as_of: str
) -> MetricStatus:
    if probability is None:
        return MetricStatus(
            computation_state="PENDING",
            genuine_zero=False,
            tied_no_spread=None,
            validation_domain=MAKE_IT_BACK_VALIDATION_DOMAIN,
            source_freshness=_freshness(source_as_of),
        )
    return MetricStatus(
        computation_state="EVALUATED",
        genuine_zero=probability == 0.0,
        tied_no_spread=None,
        validation_domain=MAKE_IT_BACK_VALIDATION_DOMAIN,
        source_freshness=_freshness(source_as_of),
        data_coverage=f"{trials} simulated continuations" if trials else None,
    )


def pick_score_status(
    value: float, *, tied_no_spread: bool, source_as_of: str
) -> MetricStatus:
    return MetricStatus(
        computation_state="EVALUATED",
        genuine_zero=value == 0.0,
        tied_no_spread=tied_no_spread,
        validation_domain=PICK_SCORE_VALIDATION_DOMAIN,
        source_freshness=_freshness(source_as_of),
    )


def raw_action_value_status(
    status_string: str, value: float | None, *, source_as_of: str
) -> MetricStatus:
    """Maps the existing real `"OK"` / `"UNAVAILABLE: <reason>"` string
    (`raw_action_value_live_service.py`) into the shared vocabulary without
    changing what that module computes or when it computes it."""
    if status_string == "OK":
        return MetricStatus(
            computation_state="EVALUATED",
            genuine_zero=value == 0.0 if value is not None else False,
            tied_no_spread=None,
            validation_domain=RAW_ACTION_VALUE_VALIDATION_DOMAIN,
            source_freshness=_freshness(source_as_of),
        )
    reason = status_string.removeprefix("UNAVAILABLE:").strip()
    computation_state = "BUDGET_LIMITED" if "top" in reason.lower() else "UNSUPPORTED"
    return MetricStatus(
        computation_state=computation_state,
        genuine_zero=False,
        tied_no_spread=None,
        validation_domain=RAW_ACTION_VALUE_VALIDATION_DOMAIN,
        source_freshness=_freshness(source_as_of),
        data_coverage=reason or None,
    )
