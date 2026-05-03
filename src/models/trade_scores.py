from __future__ import annotations

from dataclasses import dataclass

from src.utils.scoring import clamp_score

CONFIDENCE_FLOOR = 0.1
CONFIDENCE_CEILING = 1.0

TRADE_LABELS = (
    "OFFER",
    "CONSIDER",
    "HOLD",
    "DECLINE",
    "AVOID",
    "POLITICAL RISK",
)


@dataclass(frozen=True)
class TradeAsset:
    name: str
    private_value: float
    market_value: float
    keeper_value: float = 0.0


@dataclass(frozen=True)
class TradeScoreInputs:
    incoming_assets: tuple[TradeAsset, ...]
    outgoing_assets: tuple[TradeAsset, ...]
    political_risk: float = 0.0


@dataclass(frozen=True)
class TradeScore:
    private_trade_score: float
    market_trade_score: float
    keeper_impact_score: float
    niners_edge_score: float
    opponent_benefit_score: float
    acceptance_chance: float
    label: str


def score_trade(inputs: TradeScoreInputs) -> TradeScore:
    private_score = private_trade_score(inputs)
    market_score = market_trade_score(inputs)
    keeper_score = keeper_impact_score(inputs)
    edge_score = niners_edge_score(
        private_trade_score_value=private_score,
        market_trade_score_value=market_score,
        keeper_impact_score_value=keeper_score,
    )
    opponent_score = opponent_benefit_score(inputs)
    acceptance_score = acceptance_chance(
        niners_edge_score_value=edge_score,
        opponent_benefit_score_value=opponent_score,
        political_risk=inputs.political_risk,
    )
    label = trade_review_label(
        niners_edge_score_value=edge_score,
        keeper_impact_score_value=keeper_score,
        opponent_benefit_score_value=opponent_score,
        acceptance_chance_value=acceptance_score,
        political_risk=inputs.political_risk,
    )
    return TradeScore(
        private_trade_score=private_score,
        market_trade_score=market_score,
        keeper_impact_score=keeper_score,
        niners_edge_score=edge_score,
        opponent_benefit_score=opponent_score,
        acceptance_chance=acceptance_score,
        label=label,
    )


def private_trade_score(inputs: TradeScoreInputs) -> float:
    return _value_delta(inputs, "private_value")


def market_trade_score(inputs: TradeScoreInputs) -> float:
    return _value_delta(inputs, "market_value")


def keeper_impact_score(inputs: TradeScoreInputs) -> float:
    return _value_delta(inputs, "keeper_value")


def niners_edge_score(
    *,
    private_trade_score_value: float | int,
    market_trade_score_value: float | int,
    keeper_impact_score_value: float | int,
) -> float:
    score = (
        (0.50 * float(private_trade_score_value))
        + (0.20 * float(market_trade_score_value))
        + (0.30 * float(keeper_impact_score_value))
    )
    return round(score, 1)


def opponent_benefit_score(inputs: TradeScoreInputs) -> float:
    incoming_cost = _package_owner_value(inputs.incoming_assets)
    outgoing_gain = _package_owner_value(inputs.outgoing_assets)
    return round(outgoing_gain - incoming_cost, 1)


def acceptance_chance(
    *,
    niners_edge_score_value: float | int,
    opponent_benefit_score_value: float | int,
    political_risk: float | int = 0.0,
) -> float:
    score = (
        50.0
        + (0.20 * float(opponent_benefit_score_value))
        - (0.05 * float(niners_edge_score_value))
        - (0.30 * float(political_risk))
    )
    return round(clamp_score(score), 1)


def trade_review_label(
    *,
    niners_edge_score_value: float | int,
    keeper_impact_score_value: float | int,
    opponent_benefit_score_value: float | int,
    acceptance_chance_value: float | int,
    political_risk: float | int = 0.0,
) -> str:
    edge = float(niners_edge_score_value)
    keeper = float(keeper_impact_score_value)
    opponent = float(opponent_benefit_score_value)
    acceptance = float(acceptance_chance_value)
    risk = float(political_risk)
    if risk >= 70:
        return "POLITICAL RISK"
    if edge <= -150 or keeper <= -150:
        return "AVOID"
    if edge >= 75 and opponent >= -125 and acceptance >= 20:
        return "OFFER"
    if edge >= 20 and opponent >= -175:
        return "CONSIDER"
    if edge >= -25 and keeper >= -75:
        return "HOLD"
    return "DECLINE"


def trade_asset_value(
    pick_adjusted_value: float | int | None,
    confidence_score: float | int | None,
) -> float:
    """Convert a player model value into a trade-inspection value."""
    if pick_adjusted_value is None:
        return 0.0
    confidence = _bounded_confidence(confidence_score)
    return round(max(float(pick_adjusted_value), 0.0) * confidence, 1)


def trade_value_gap(
    incoming_value: float | int | None,
    outgoing_value: float | int | None,
) -> float:
    return round(float(incoming_value or 0.0) - float(outgoing_value or 0.0), 1)


def _bounded_confidence(confidence_score: float | int | None) -> float:
    if confidence_score is None:
        return CONFIDENCE_FLOOR
    return min(max(float(confidence_score), CONFIDENCE_FLOOR), CONFIDENCE_CEILING)


def _value_delta(inputs: TradeScoreInputs, attribute: str) -> float:
    incoming_value = sum(
        float(getattr(asset, attribute)) for asset in inputs.incoming_assets
    )
    outgoing_value = sum(
        float(getattr(asset, attribute)) for asset in inputs.outgoing_assets
    )
    return round(incoming_value - outgoing_value, 1)


def _package_owner_value(assets: tuple[TradeAsset, ...]) -> float:
    return sum(
        (0.60 * float(asset.market_value)) + (0.40 * float(asset.keeper_value))
        for asset in assets
    )
