from __future__ import annotations

CONFIDENCE_FLOOR = 0.1
CONFIDENCE_CEILING = 1.0
EVEN_VALUE_BAND = 75.0


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


def trade_path_signal(value_gap: float | int | None) -> str:
    gap = float(value_gap or 0.0)
    if abs(gap) <= EVEN_VALUE_BAND:
        return "Even"
    if gap > 0:
        return "Ask+"
    return "Short"


def _bounded_confidence(confidence_score: float | int | None) -> float:
    if confidence_score is None:
        return CONFIDENCE_FLOOR
    return min(max(float(confidence_score), CONFIDENCE_FLOOR), CONFIDENCE_CEILING)
