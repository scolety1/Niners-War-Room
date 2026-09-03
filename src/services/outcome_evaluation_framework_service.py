"""Outcome evaluation framework (directive section 10).

Metrics are declared here BEFORE any real historical dataset exists, per
the directive's own instruction to avoid selecting metrics after seeing
which one makes NWR look best. Every function in this module is pure and
deterministic given its inputs -- none of them read shadow_numeric_
authorities_service, historical data, or any file; a caller supplies
already-computed realized production and the framework never invents it.

Every season/league-level metric is explicitly labeled OBSERVED or
SIMULATED (see `OutcomeEvaluationSource`) -- section 10's own instruction:
"Do not claim observed titles if historical league schedule/bracket data
does not actually exist." A caller that has no real bracket data must pass
`source=SIMULATED`; there is no default that silently claims OBSERVED.

Roster-level metrics reuse the real, unmodified
`roster_composition_report` / `optimal_starting_lineup_value` from
`shadow_numeric_authorities_service` -- called here on REALIZED (not
projected) RosterPlayer values, so "optimal legal lineup production" is
computed by the same starter-selection algorithm the research Team Score
already uses, not a second competing implementation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from src.services.redraft_engine_v1_service import LeagueProfile
from src.services.shadow_numeric_authorities_service import (
    RosterCompositionReport,
    RosterPlayer,
    optimal_starting_lineup_value,
    roster_composition_report,
)

OBSERVED = "OBSERVED"
SIMULATED = "SIMULATED"
OUTCOME_EVALUATION_SOURCES = frozenset({OBSERVED, SIMULATED})


class OutcomeEvaluationError(ValueError):
    pass


# --- Correlation primitives (no scipy dependency; small-N draft-sized data) --


def _rank(values: Sequence[float]) -> list[float]:
    """Average (fractional) ranks, ties sharing the mean rank -- the
    standard convention for Spearman's rho with ties."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = average_rank
        i = j + 1
    return ranks


def spearman_rank_correlation(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Pearson correlation of the two rank sequences. Returns None (never
    a fabricated 0.0) when fewer than 2 paired observations exist or either
    series has zero variance."""
    if len(x) != len(y):
        raise OutcomeEvaluationError("spearman_rank_correlation requires equal-length series.")
    if len(x) < 2:
        return None
    rx, ry = _rank(list(x)), _rank(list(y))
    return _pearson(rx, ry)


def kendall_tau(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Kendall's tau-a: (concordant - discordant) / total pairs. O(n^2),
    fine for draft-sized samples (tens to low hundreds of players)."""
    if len(x) != len(y):
        raise OutcomeEvaluationError("kendall_tau requires equal-length series.")
    n = len(x)
    if n < 2:
        return None
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            product = dx * dy
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return None
    return (concordant - discordant) / total_pairs


def _pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    n = len(x)
    if n < 2:
        return None
    mean_x, mean_y = sum(x) / n, sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y, strict=True))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)
    denom = math.sqrt(var_x * var_y)
    if denom == 0:
        return None
    return cov / denom


# --- Player-level metrics --------------------------------------------------


@dataclass(frozen=True)
class PlayerLevelMetrics:
    player_id: str
    realized_production: float
    projected_production: float | None
    projection_error: float | None  # realized - projected; None if no projection
    replacement_points: float | None
    realized_value_over_replacement: float | None


def player_level_metrics(
    *,
    player_id: str,
    realized_production: float,
    projected_production: float | None = None,
    replacement_points: float | None = None,
) -> PlayerLevelMetrics:
    projection_error = (
        round(realized_production - projected_production, 4)
        if projected_production is not None
        else None
    )
    vor = (
        round(realized_production - replacement_points, 4)
        if replacement_points is not None
        else None
    )
    return PlayerLevelMetrics(
        player_id=player_id,
        realized_production=realized_production,
        projected_production=projected_production,
        projection_error=projection_error,
        replacement_points=replacement_points,
        realized_value_over_replacement=vor,
    )


def player_rank_correlation(
    predicted_ranks: Sequence[float], realized_ranks: Sequence[float]
) -> Mapping[str, float | None]:
    """Both Spearman and Kendall between a predicted pre-draft rank
    ordering and a realized-production rank ordering -- pre-declared here,
    per the directive, rather than picked after seeing which correlation
    flatters NWR more."""
    return {
        "spearman": spearman_rank_correlation(predicted_ranks, realized_ranks),
        "kendall_tau": kendall_tau(predicted_ranks, realized_ranks),
    }


# --- Pick-level metrics -----------------------------------------------------


@dataclass(frozen=True)
class PickLevelMetrics:
    pick_number: int
    selected_player_id: str
    selected_realized_production: float
    best_available_player_id: str | None
    best_available_realized_production: float | None
    # best_available - selected; >= 0 means a better pick genuinely existed.
    realized_pick_regret: float | None
    # selected - replacement_points; negative means the pick underperformed replacement.
    replacement_loss: float | None
    made_it_back: bool | None  # did the passed-on top alternative survive to the next pick?


def pick_level_metrics(
    *,
    pick_number: int,
    selected_player_id: str,
    selected_realized_production: float,
    available_pool_realized_production: Mapping[str, float],
    replacement_points: float | None = None,
    next_pick_available_player_ids: Sequence[str] | None = None,
) -> PickLevelMetrics:
    """`available_pool_realized_production` is every OTHER candidate that
    was actually available at this pick (never a future-drafted player --
    the caller is responsible for that point-in-time boundary, exactly as
    the historical replay data contract already requires)."""
    best_id: str | None = None
    best_value: float | None = None
    for candidate_id, value in available_pool_realized_production.items():
        if candidate_id == selected_player_id:
            continue
        if best_value is None or value > best_value:
            best_id, best_value = candidate_id, value
    regret = (
        round(best_value - selected_realized_production, 4) if best_value is not None else None
    )
    replacement_loss = (
        round(selected_realized_production - replacement_points, 4)
        if replacement_points is not None
        else None
    )
    made_it_back: bool | None = None
    if best_id is not None and next_pick_available_player_ids is not None:
        made_it_back = best_id in next_pick_available_player_ids
    return PickLevelMetrics(
        pick_number=pick_number,
        selected_player_id=selected_player_id,
        selected_realized_production=selected_realized_production,
        best_available_player_id=best_id,
        best_available_realized_production=best_value,
        realized_pick_regret=regret,
        replacement_loss=replacement_loss,
        made_it_back=made_it_back,
    )


# --- Roster-level metrics ---------------------------------------------------


@dataclass(frozen=True)
class RosterLevelMetrics:
    optimal_legal_lineup_production: float
    starter_production: float
    roster_total_production: float
    replacement_adjusted_production: float | None
    unused_redundant_value: float
    roster_construction_failure_count: int
    composition: RosterCompositionReport


def roster_level_metrics(
    realized_roster: Sequence[RosterPlayer],
    profile: LeagueProfile,
    *,
    replacement_points_by_position: Mapping[str, float] | None = None,
) -> RosterLevelMetrics:
    """`realized_roster` carries REALIZED production in `.value`, not
    projected/pre-draft value -- the caller builds these RosterPlayer
    objects from actual outcomes. Reuses the real, unmodified
    roster_composition_report/optimal_starting_lineup_value rather than a
    second lineup-selection algorithm."""
    composition = roster_composition_report(realized_roster, profile)
    optimal = optimal_starting_lineup_value(realized_roster, profile)
    total = round(sum(p.value for p in realized_roster), 4)
    replacement_adjusted: float | None = None
    if replacement_points_by_position is not None:
        replacement_adjusted = round(
            sum(
                p.value - replacement_points_by_position.get(p.position, 0.0)
                for p in realized_roster
            ),
            4,
        )
    unused = round(total - composition.starting_lineup_value, 4)
    return RosterLevelMetrics(
        optimal_legal_lineup_production=optimal,
        starter_production=composition.starting_lineup_value,
        roster_total_production=total,
        replacement_adjusted_production=replacement_adjusted,
        unused_redundant_value=unused,
        roster_construction_failure_count=len(composition.starter_holes),
        composition=composition,
    )


# --- Season / league-level metrics ------------------------------------------


@dataclass(frozen=True)
class SeasonLevelMetrics:
    source: str  # OBSERVED or SIMULATED -- never defaulted
    regular_season_strength_percentile: float | None
    simulated_playoff_rate: float | None
    simulated_championship_rate: float | None
    sample_size: int

    def __post_init__(self) -> None:
        if self.source not in OUTCOME_EVALUATION_SOURCES:
            raise OutcomeEvaluationError(f"Unknown outcome evaluation source: {self.source!r}")


def season_level_metrics(
    *,
    source: str,
    regular_season_strength_percentile: float | None,
    simulated_playoff_rate: float | None,
    simulated_championship_rate: float | None,
    sample_size: int,
) -> SeasonLevelMetrics:
    if source == OBSERVED and (
        simulated_playoff_rate is not None or simulated_championship_rate is not None
    ):
        raise OutcomeEvaluationError(
            "source=OBSERVED but a *_rate field was supplied -- playoff/championship "
            "rates are inherently simulated probabilities, never an observed fact for a "
            "single realized season. Use source=SIMULATED, or omit these fields."
        )
    return SeasonLevelMetrics(
        source=source,
        regular_season_strength_percentile=regular_season_strength_percentile,
        simulated_playoff_rate=simulated_playoff_rate,
        simulated_championship_rate=simulated_championship_rate,
        sample_size=sample_size,
    )
