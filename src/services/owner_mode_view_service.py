"""Deterministic owner-mode translations over governed evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


def market_decision_label(nwr_rank: object, market_rank: object) -> tuple[str, str]:
    """Return a display-only five-band interpretation and signed rank gap."""

    nwr = _number(nwr_rank)
    market = _number(market_rank)
    if nwr is None or market is None:
        return "Market data unavailable", ""
    gap = nwr - market
    if gap <= -20:
        label = "Potential buy — NWR materially higher"
    elif gap < -5:
        label = "NWR slightly higher"
    elif gap <= 5:
        label = "Market aligned"
    elif gap < 20:
        label = "Market slightly higher"
    else:
        label = "Potential sell / caution — market materially higher"
    return label, f"{gap:+.1f} ranks (NWR minus market)"


def owner_range(row: Mapping[str, Any]) -> dict[str, str]:
    """Use the frozen research signals without inventing a numeric interval."""

    return {
        "Floor": _probability_label("Downside signal", row.get("research_downside_signal")),
        "Expected": translate_research_tier(row.get("research_tier") or row.get("source_tier")),
        "Ceiling": _probability_label("Ceiling signal", row.get("research_ceiling_signal")),
    }


def translate_research_tier(value: object) -> str:
    text = _text(value)
    if not text:
        return "Not enough information"
    if text.upper().startswith("RESEARCH_TIER_"):
        return f"Research neighborhood {text.rsplit('_', 1)[-1]}"
    return text.replace("_", " ").title()


def owner_rankings_frame(rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    output: list[dict[str, object]] = []
    for row in rows:
        if _text(row.get("asset_type")) != "Current Player":
            continue
        label, gap = market_decision_label(row.get("dynasty_rank"), row.get("market_dp_rank"))
        range_values = owner_range(row)
        output.append(
            {
                "Rank": _integer(row.get("dynasty_rank")),
                "Player": _text(row.get("asset_name")),
                "Pos": _text(row.get("position")),
                "Team": _text(row.get("team")),
                "Pos Rank": _text(row.get("position_rank")),
                "NWR Score": _text(row.get("nwr_dynasty_score")),
                "Expected": range_values["Expected"],
                "Market": label,
                "Market Gap": gap,
                "Confidence": _text(row.get("confidence")) or "Not enough information",
                "asset_id": _text(row.get("asset_id")),
            }
        )
    frame = pd.DataFrame(output)
    if not frame.empty:
        frame = frame.sort_values(["Rank", "Player"], na_position="last", kind="stable")
    return frame.reset_index(drop=True)


def _number(value: object) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return None if pd.isna(number) else number


def _integer(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _probability_label(label: str, value: object) -> str:
    number = _number(value)
    if number is not None and 0 <= number <= 1:
        return f"{label}: {number:.1%}"
    text = _text(value)
    return text or "Not enough information"


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.casefold() in {"", "nan", "none", "null", "<na>"} else text
