from __future__ import annotations

from dataclasses import dataclass

from src.utils.scoring import clamp_score

QB_PRIVATE_WEIGHTS = {
    "draft_cap": 0.40,
    "rush_profile": 0.30,
    "start_path": 0.15,
    "passing_trait": 0.10,
    "environment": 0.05,
}

RB_PRIVATE_WEIGHTS = {
    "draft_cap": 0.28,
    "opportunity": 0.22,
    "production": 0.15,
    "receiving": 0.14,
    "elusiveness": 0.12,
    "size_durability": 0.05,
    "athleticism": 0.04,
}

WR_PRIVATE_WEIGHTS = {
    "draft_cap": 0.27,
    "age_adj_production": 0.21,
    "target_earning_efficiency": 0.17,
    "breakout_class": 0.12,
    "film_separation": 0.11,
    "size_role": 0.05,
    "athleticism": 0.03,
    "environment": 0.04,
}

TE_PRIVATE_WEIGHTS = {
    "draft_cap": 0.23,
    "receiving_production": 0.22,
    "route_role": 0.17,
    "athleticism": 0.12,
    "film_receiving": 0.11,
    "role_path": 0.08,
    "age_timeline": 0.04,
    "environment": 0.03,
}

FIRST_DOWN_RATE_BASELINES = {
    "QB": 0.31,
    "RB": 0.24,
    "WR": 0.54,
    "TE": 0.50,
}
FIRST_DOWN_VOLUME_BASELINES = {
    "QB": 160,
    "RB": 55,
    "WR": 50,
    "TE": 38,
}
FIRST_DOWN_RATE_MULTIPLIER = 10
FIRST_DOWN_RATE_CAP = 2.0
FIRST_DOWN_VOLUME_MULTIPLIER = 1.5
FIRST_DOWN_VOLUME_CAP = 1.5


@dataclass(frozen=True)
class PlayerScoreInputs:
    position: str
    draft_cap: float
    rush_profile: float = 0.0
    start_path: float = 0.0
    passing_trait: float = 0.0
    opportunity: float = 0.0
    production: float = 0.0
    receiving: float = 0.0
    elusiveness: float = 0.0
    size_durability: float = 0.0
    athleticism: float = 0.0
    age_adj_production: float = 0.0
    target_earning_efficiency: float = 0.0
    breakout_class: float = 0.0
    film_separation: float = 0.0
    size_role: float = 0.0
    receiving_production: float = 0.0
    route_role: float = 0.0
    film_receiving: float = 0.0
    role_path: float = 0.0
    age_timeline: float = 0.0
    environment: float = 50.0
    first_downs: float = 0.0
    first_down_opportunities: float = 0.0
    risk_penalty: float = 0.0


def private_score(inputs: PlayerScoreInputs) -> float:
    position = inputs.position.upper()
    if position == "QB":
        return qb_private_score(inputs)
    if position == "RB":
        return rb_private_score(inputs)
    if position == "WR":
        return wr_private_score(inputs)
    if position == "TE":
        return te_private_score(inputs)
    raise ValueError(f"Unsupported private-score position: {inputs.position}")


def qb_private_score(inputs: PlayerScoreInputs) -> float:
    return _score(inputs, QB_PRIVATE_WEIGHTS)


def rb_private_score(inputs: PlayerScoreInputs) -> float:
    return _score(inputs, RB_PRIVATE_WEIGHTS)


def wr_private_score(inputs: PlayerScoreInputs) -> float:
    return _score(inputs, WR_PRIVATE_WEIGHTS)


def te_private_score(inputs: PlayerScoreInputs) -> float:
    return _score(inputs, TE_PRIVATE_WEIGHTS)


def first_down_rate(first_downs: float, opportunities: float) -> float:
    if opportunities <= 0:
        return 0.0
    return clamp_score(first_downs / opportunities, 0.0, 1.0)


def first_down_rate_adjustment(position: str, first_downs: float, opportunities: float) -> float:
    position_key = position.upper()
    baseline = FIRST_DOWN_RATE_BASELINES.get(position_key, 0.30)
    rate_delta = first_down_rate(first_downs, opportunities) - baseline
    return round(
        clamp_score(
            rate_delta * FIRST_DOWN_RATE_MULTIPLIER,
            -FIRST_DOWN_RATE_CAP,
            FIRST_DOWN_RATE_CAP,
        ),
        2,
    )


def first_down_volume_adjustment(position: str, first_downs: float) -> float:
    position_key = position.upper()
    baseline = FIRST_DOWN_VOLUME_BASELINES.get(position_key, 50)
    volume_delta = (first_downs - baseline) / baseline
    return round(
        clamp_score(
            volume_delta * FIRST_DOWN_VOLUME_MULTIPLIER,
            -FIRST_DOWN_VOLUME_CAP,
            FIRST_DOWN_VOLUME_CAP,
        ),
        2,
    )


def official_rank_score(rank: int | None, replacement_rank: int = 400) -> float:
    if rank is None:
        return 35.0
    resolved_rank = clamp_score(float(rank), 1.0, float(replacement_rank))
    return round(100 - (((resolved_rank - 1) / (replacement_rank - 1)) * 100), 2)


def _score(inputs: PlayerScoreInputs, weights: dict[str, float]) -> float:
    components = {
        "draft_cap": inputs.draft_cap,
        "rush_profile": inputs.rush_profile,
        "start_path": inputs.start_path,
        "passing_trait": inputs.passing_trait,
        "opportunity": inputs.opportunity,
        "production": inputs.production,
        "receiving": inputs.receiving,
        "elusiveness": inputs.elusiveness,
        "size_durability": inputs.size_durability,
        "athleticism": inputs.athleticism,
        "age_adj_production": inputs.age_adj_production,
        "target_earning_efficiency": inputs.target_earning_efficiency,
        "breakout_class": inputs.breakout_class,
        "film_separation": inputs.film_separation,
        "size_role": inputs.size_role,
        "receiving_production": inputs.receiving_production,
        "route_role": inputs.route_role,
        "film_receiving": inputs.film_receiving,
        "role_path": inputs.role_path,
        "age_timeline": inputs.age_timeline,
        "environment": inputs.environment,
    }
    base = sum(clamp_score(components[name]) * weight for name, weight in weights.items())
    first_down_adjustment = first_down_rate_adjustment(
        inputs.position, inputs.first_downs, inputs.first_down_opportunities
    ) + first_down_volume_adjustment(inputs.position, inputs.first_downs)
    return round(clamp_score(base + first_down_adjustment - inputs.risk_penalty), 2)
