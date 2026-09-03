"""Model health dashboard data contract (directive section 26).

A backend output contract for future owner visibility into model health
-- not a UI. Every metric carries its own dimensions (season, position,
league format, draft round) and its own sample size, so a caller (or a
future UI) can never present a metric without knowing how much evidence
backs it. `SMALL_SAMPLE_THRESHOLD` exists specifically to avoid the
directive's own named risk: misleading small-N conclusions -- any metric
below the threshold is flagged, never silently presented at the same
confidence as a well-supported one.

This module does not compute any of the underlying metrics itself --
those already exist for real in `outcome_evaluation_framework_service`
(player/pick/roster/season level) and `champion_challenger_registry_service`
(challenger lifecycle status). This module's job is only the health-area
contract and the small-sample-aware assembly, not a second metrics engine.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

HEALTH_AREA_PLAYER_SCORE = "PLAYER_SCORE_PREDICTION_QUALITY"
HEALTH_AREA_TEAM_SCORE = "TEAM_SCORE_MONOTONICITY"
HEALTH_AREA_CHAMPIONSHIP_EQUITY = "CHAMPIONSHIP_EQUITY_CALIBRATION"
HEALTH_AREA_PICK_SCORE = "PICK_SCORE_REGRET"
HEALTH_AREA_COST_OF_WAITING = "COST_OF_WAITING_CALIBRATION"
HEALTH_AREA_ROOKIE = "ROOKIE_PERFORMANCE"
HEALTH_AREA_QB = "QB_PERFORMANCE"

HEALTH_AREAS = frozenset(
    {
        HEALTH_AREA_PLAYER_SCORE,
        HEALTH_AREA_TEAM_SCORE,
        HEALTH_AREA_CHAMPIONSHIP_EQUITY,
        HEALTH_AREA_PICK_SCORE,
        HEALTH_AREA_COST_OF_WAITING,
        HEALTH_AREA_ROOKIE,
        HEALTH_AREA_QB,
    }
)

# Below this many observations, a metric is flagged low-confidence rather
# than silently shown alongside well-supported ones. A round, disclosed
# number -- not calibrated against real historical data, since none
# exists yet (see docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md).
SMALL_SAMPLE_THRESHOLD = 20


class ModelHealthDashboardError(ValueError):
    pass


def is_small_sample(sample_size: int) -> bool:
    return sample_size < SMALL_SAMPLE_THRESHOLD


@dataclass(frozen=True)
class ModelHealthMetric:
    health_area: str
    metric_name: str
    value: float
    sample_size: int
    season: int | None = None
    position: str | None = None
    league_format: str | None = None
    draft_round: int | None = None

    def __post_init__(self) -> None:
        if self.health_area not in HEALTH_AREAS:
            raise ModelHealthDashboardError(f"Unknown health_area: {self.health_area!r}")
        if self.sample_size < 0:
            raise ModelHealthDashboardError("sample_size cannot be negative.")

    @property
    def low_confidence(self) -> bool:
        return is_small_sample(self.sample_size)


@dataclass(frozen=True)
class ModelHealthReport:
    metrics: tuple[ModelHealthMetric, ...]
    metrics_by_area: dict[str, tuple[ModelHealthMetric, ...]]
    low_confidence_count: int
    total_sample_size: int


def build_model_health_report(metrics: Sequence[ModelHealthMetric]) -> ModelHealthReport:
    by_area: dict[str, list[ModelHealthMetric]] = {area: [] for area in HEALTH_AREAS}
    for metric in metrics:
        by_area[metric.health_area].append(metric)
    return ModelHealthReport(
        metrics=tuple(metrics),
        metrics_by_area={area: tuple(rows) for area, rows in by_area.items()},
        low_confidence_count=sum(1 for m in metrics if m.low_confidence),
        total_sample_size=sum(m.sample_size for m in metrics),
    )


def filter_confident_metrics(
    report: ModelHealthReport, *, health_area: str | None = None
) -> tuple[ModelHealthMetric, ...]:
    """Every metric NOT flagged low_confidence, optionally restricted to
    one health area -- the subset safe to present as a headline number
    without a small-N caveat attached."""
    candidates = (
        report.metrics if health_area is None else report.metrics_by_area.get(health_area, ())
    )
    return tuple(m for m in candidates if not m.low_confidence)
