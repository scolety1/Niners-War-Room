from __future__ import annotations

from datetime import UTC, datetime

from src.utils.scoring import clamp_score

MARKET_PRIVATE_VALUE_WEIGHT = 0.0
MARKET_STAT_VALUE_WEIGHT = 0.0
MAX_MARKET_KEEPER_NUDGE = 0.0
MAX_MARKET_BLEND_NUDGE = 4.0
MARKET_ONLY_COMPONENTS = frozenset(
    {
        "trade_liquidity",
        "trade_value",
        "market_edge",
    }
)
MARKET_EDGE_STRONG_THRESHOLD = 8.0
MARKET_EDGE_THRESHOLD = 4.0
REAL_IMPORTED_MARKET = "real_imported_market"
STALE_MARKET = "stale_market"
MISSING_MARKET = "missing_market"
DISABLED_MARKET = "disabled_market"
NEUTRAL_MARKET_PLACEHOLDER = "neutral_market_placeholder"
MARKET_VALUE_STATUSES = frozenset(
    {
        REAL_IMPORTED_MARKET,
        STALE_MARKET,
        MISSING_MARKET,
        DISABLED_MARKET,
        NEUTRAL_MARKET_PLACEHOLDER,
    }
)
USABLE_MARKET_VALUE_STATUSES = frozenset({REAL_IMPORTED_MARKET})
REVIEW_MARKET_VALUE_STATUSES = frozenset({STALE_MARKET})
UNUSABLE_MARKET_VALUE_STATUSES = frozenset(
    {MISSING_MARKET, DISABLED_MARKET, NEUTRAL_MARKET_PLACEHOLDER}
)


def market_keeper_nudge(market_liquidity: float) -> float:
    """Research lock: market/liquidity cannot move private or keeper value."""
    _ = market_liquidity
    return 0.0


def cap_market_blended_value(
    football_anchor: float,
    raw_blended_value: float,
    *,
    cap: float = MAX_MARKET_BLEND_NUDGE,
) -> float:
    """Limit trade/market drift when a blended board value includes liquidity."""
    anchor = clamp_score(float(football_anchor))
    return round(
        clamp_score(
            float(raw_blended_value),
            max(0.0, anchor - cap),
            min(100.0, anchor + cap),
        ),
        2,
    )


def market_edge_score(private_value: float, market_trade_value: float) -> float:
    """Positive means the stats model is higher than trade-market liquidity."""
    return round(float(private_value) - float(market_trade_value), 2)


def market_edge_label(edge_score: float) -> str:
    edge = float(edge_score)
    if edge >= MARKET_EDGE_STRONG_THRESHOLD:
        return "strong_positive_edge_model_higher"
    if edge >= MARKET_EDGE_THRESHOLD:
        return "positive_edge_model_higher"
    if edge <= -MARKET_EDGE_STRONG_THRESHOLD:
        return "strong_negative_edge_market_higher"
    if edge <= -MARKET_EDGE_THRESHOLD:
        return "negative_edge_market_higher"
    return "near_market"


def market_value_status(
    row: dict[str, object],
    *,
    value_keys: tuple[str, ...] = (
        "market_trade_value",
        "market_score",
        "market_liquidity",
        "market_value",
    ),
) -> str:
    """Classify whether market value is real evidence or only review context."""
    explicit = _explicit_market_status(row)
    if explicit:
        return explicit
    if _boolish(row.get("market_disabled")):
        return DISABLED_MARKET
    value = first_market_value(row, value_keys=value_keys)
    if value is None:
        return MISSING_MARKET
    if _looks_neutral_placeholder(row, value):
        return NEUTRAL_MARKET_PLACEHOLDER
    if _is_stale_market(row):
        return STALE_MARKET
    return REAL_IMPORTED_MARKET


def first_market_value(
    row: dict[str, object],
    *,
    value_keys: tuple[str, ...] = (
        "market_trade_value",
        "market_score",
        "market_liquidity",
        "market_value",
    ),
) -> float | None:
    for key in value_keys:
        value = row.get(key)
        if value in {None, ""}:
            continue
        try:
            return float(str(value))
        except (TypeError, ValueError):
            continue
    return None


def safe_market_edge_score(
    private_value: float | None,
    market_value: float | None,
    status: str,
    *,
    explicit_edge: object = None,
) -> float | None:
    """Return an edge only when the market input is real or explicitly reviewable."""
    if private_value is None or market_value is None:
        return None
    if status in UNUSABLE_MARKET_VALUE_STATUSES:
        return None
    if explicit_edge not in {None, ""}:
        try:
            return round(float(str(explicit_edge)), 2)
        except (TypeError, ValueError):
            pass
    return market_edge_score(private_value, market_value)


def market_edge_classification(status: str, edge: float | None) -> str:
    if status == REAL_IMPORTED_MARKET and edge is not None:
        return market_edge_label(edge)
    return status if status in MARKET_VALUE_STATUSES else "market_review_needed"


def market_edge_view(status: str, edge: float | None) -> str:
    if status in UNUSABLE_MARKET_VALUE_STATUSES or edge is None:
        return "market_unavailable"
    if status == STALE_MARKET:
        return "market_review_needed"
    if edge >= MARKET_EDGE_THRESHOLD:
        return "model_higher_than_market"
    if edge <= -MARKET_EDGE_THRESHOLD:
        return "market_higher_than_model"
    return "near_market"


def market_status_warning(status: str) -> str:
    return {
        REAL_IMPORTED_MARKET: "none",
        STALE_MARKET: "stale_market_value",
        MISSING_MARKET: "missing_market_trade_value",
        DISABLED_MARKET: "market_value_disabled",
        NEUTRAL_MARKET_PLACEHOLDER: "neutral_market_placeholder",
    }.get(status, "market_review_needed")


def market_status_label(status: str) -> str:
    return {
        REAL_IMPORTED_MARKET: "real imported market",
        STALE_MARKET: "stale market",
        MISSING_MARKET: "missing market",
        DISABLED_MARKET: "market disabled",
        NEUTRAL_MARKET_PLACEHOLDER: "neutral market placeholder",
    }.get(status, str(status).replace("_", " "))


def _explicit_market_status(row: dict[str, object]) -> str:
    for key in ("market_value_status", "market_source_status", "market_status"):
        value = str(row.get(key) or "").strip()
        if value in MARKET_VALUE_STATUSES:
            return value
    return ""


def _looks_neutral_placeholder(row: dict[str, object], value: float) -> bool:
    if abs(value - 50.0) > 0.01:
        return False
    source_parts = [
        str(row.get(key) or "").lower()
        for key in (
            "market_source",
            "market_source_key",
            "market_edge_warning",
            "source_status",
            "warnings",
        )
        if str(row.get(key) or "").strip()
    ]
    source_text = "|".join(source_parts)
    if not source_text:
        return True
    placeholder_markers = (
        "neutral",
        "placeholder",
        "baseline",
        "missing_market",
        "review_missing",
    )
    return any(marker in source_text for marker in placeholder_markers)


def _is_stale_market(row: dict[str, object]) -> bool:
    if "stale" in str(row.get("market_edge_warning") or "").lower():
        return True
    source_date = _parse_date(
        row.get("market_source_date")
        or row.get("market_export_date")
        or row.get("source_date")
    )
    computed_at = _parse_date(row.get("computed_at"))
    if source_date is None or computed_at is None:
        return False
    return (computed_at - source_date).days > 45


def _parse_date(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


def _boolish(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
