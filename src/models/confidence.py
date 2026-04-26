from __future__ import annotations

from dataclasses import dataclass

from src.utils.scoring import clamp_score


@dataclass(frozen=True)
class ConfidenceInputs:
    data_completeness: float = 1.0
    source_count: int = 1
    rank_age_days: int = 0
    projection_variance: float = 0.0


def confidence_score(inputs: ConfidenceInputs) -> float:
    completeness = clamp_score(inputs.data_completeness, 0.0, 1.0)
    source_factor = clamp_score(inputs.source_count / 4, 0.0, 1.0)
    freshness_factor = clamp_score(1 - (max(0, inputs.rank_age_days) / 120), 0.0, 1.0)
    stability_factor = clamp_score(1 - inputs.projection_variance, 0.0, 1.0)

    score = (
        (0.45 * completeness)
        + (0.25 * source_factor)
        + (0.20 * freshness_factor)
        + (0.10 * stability_factor)
    )
    return round(clamp_score(score, 0.0, 1.0), 3)


def risk_level(score: float) -> str:
    if score >= 0.75:
        return "low"
    if score >= 0.55:
        return "medium"
    return "high"
