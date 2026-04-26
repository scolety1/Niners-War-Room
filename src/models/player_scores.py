from __future__ import annotations

from dataclasses import dataclass

from src.utils.scoring import clamp_score

POSITION_AGE_PEAKS = {
    "QB": 29,
    "RB": 24,
    "WR": 25,
    "TE": 26,
}


@dataclass(frozen=True)
class PlayerScoreInputs:
    position: str
    production_score: float
    opportunity_score: float
    official_rank: int | None = None
    market_rank: int | None = None
    age: float | None = None
    receiving_score: float = 0.0
    rushing_score: float = 0.0
    target_earning_score: float = 0.0
    breakout_score: float = 0.0
    environment_score: float = 50.0
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
    return _score(
        inputs,
        {
            "production": 0.34,
            "opportunity": 0.20,
            "rushing": 0.16,
            "market": 0.12,
            "official": 0.10,
            "environment": 0.08,
        },
    )


def rb_private_score(inputs: PlayerScoreInputs) -> float:
    return _score(
        inputs,
        {
            "production": 0.30,
            "opportunity": 0.20,
            "receiving": 0.16,
            "age": 0.12,
            "market": 0.10,
            "official": 0.07,
            "environment": 0.05,
        },
    )


def wr_private_score(inputs: PlayerScoreInputs) -> float:
    return _score(
        inputs,
        {
            "production": 0.28,
            "target_earning": 0.20,
            "breakout": 0.16,
            "opportunity": 0.12,
            "market": 0.10,
            "official": 0.08,
            "environment": 0.06,
        },
    )


def te_private_score(inputs: PlayerScoreInputs) -> float:
    return _score(
        inputs,
        {
            "production": 0.28,
            "target_earning": 0.18,
            "opportunity": 0.16,
            "breakout": 0.12,
            "age": 0.10,
            "market": 0.08,
            "official": 0.05,
            "environment": 0.03,
        },
    )


def first_down_rate(first_downs: float, opportunities: float) -> float:
    if opportunities <= 0:
        return 0.0
    return clamp_score(first_downs / opportunities, 0.0, 1.0)


def first_down_rate_adjustment(position: str, first_downs: float, opportunities: float) -> float:
    baselines = {
        "QB": 0.31,
        "RB": 0.24,
        "WR": 0.54,
        "TE": 0.50,
    }
    position_key = position.upper()
    baseline = baselines.get(position_key, 0.30)
    rate_delta = first_down_rate(first_downs, opportunities) - baseline
    return round(clamp_score(rate_delta * 20, -4.0, 4.0), 2)


def first_down_volume_adjustment(position: str, first_downs: float) -> float:
    baselines = {
        "QB": 160,
        "RB": 55,
        "WR": 50,
        "TE": 38,
    }
    position_key = position.upper()
    baseline = baselines.get(position_key, 50)
    volume_delta = (first_downs - baseline) / baseline
    return round(clamp_score(volume_delta * 3, -3.0, 3.0), 2)


def official_rank_score(rank: int | None, replacement_rank: int = 400) -> float:
    if rank is None:
        return 35.0
    resolved_rank = clamp_score(float(rank), 1.0, float(replacement_rank))
    return round(100 - (((resolved_rank - 1) / (replacement_rank - 1)) * 100), 2)


def age_fit_score(position: str, age: float | None) -> float:
    if age is None:
        return 50.0
    peak = POSITION_AGE_PEAKS.get(position.upper(), 26)
    penalty = abs(age - peak) * 7
    return round(clamp_score(100 - penalty), 2)


def _score(inputs: PlayerScoreInputs, weights: dict[str, float]) -> float:
    components = {
        "production": inputs.production_score,
        "opportunity": inputs.opportunity_score,
        "receiving": inputs.receiving_score,
        "rushing": inputs.rushing_score,
        "target_earning": inputs.target_earning_score,
        "breakout": inputs.breakout_score,
        "environment": inputs.environment_score,
        "official": official_rank_score(inputs.official_rank),
        "market": official_rank_score(inputs.market_rank),
        "age": age_fit_score(inputs.position, inputs.age),
    }
    base = sum(clamp_score(components[name]) * weight for name, weight in weights.items())
    first_down_adjustment = first_down_rate_adjustment(
        inputs.position, inputs.first_downs, inputs.first_down_opportunities
    ) + first_down_volume_adjustment(inputs.position, inputs.first_downs)
    return round(clamp_score(base + first_down_adjustment - inputs.risk_penalty), 2)
