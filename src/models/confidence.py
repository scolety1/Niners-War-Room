from __future__ import annotations

from dataclasses import dataclass

from src.utils.scoring import clamp_score


@dataclass(frozen=True)
class ConfidenceInputs:
    data_completeness: float = 0.0
    historical_cohort_size: float = 0.0
    market_agreement: float = 0.0
    model_separation: float = 0.0


def confidence_score(inputs: ConfidenceInputs) -> float:
    score = (
        (0.35 * clamp_score(inputs.data_completeness, 0.0, 1.0))
        + (0.25 * clamp_score(inputs.historical_cohort_size, 0.0, 1.0))
        + (0.20 * clamp_score(inputs.market_agreement, 0.0, 1.0))
        + (0.20 * clamp_score(inputs.model_separation, 0.0, 1.0))
    )
    return round(clamp_score(score, 0.0, 1.0), 3)


def risk_level(score: float) -> str:
    if score >= 0.75:
        return "low"
    if score >= 0.55:
        return "medium"
    return "high"
