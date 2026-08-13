"""Deterministic owner-mode translations over governed evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from src.services.owner_caveat_presentation_service import owner_caveats

MARKET_BANDS = (
    "Potential Buy",
    "NWR Higher",
    "Aligned",
    "Market Higher",
    "Potential Sell / Caution",
)

_VALUE_BAND_PRESENTATION = {
    "priority candidate": ("Tier A", "Core priority"),
    "strong candidate": ("Tier B", "Strong asset"),
    "viable candidate": ("Tier C", "Viable starter"),
    "viable with caveats": ("Tier C", "Viable with caveats"),
    "depth/discount candidate": ("Tier D", "Depth or value target"),
    "depth/format-dependent": ("Tier D", "Depth / format dependent"),
    "strong review target": ("Tier E", "Monitor closely"),
    "priority review target": ("Tier E", "Monitor closely"),
    "human-review hold": ("Tier E", "Hold / monitor"),
    "human-review only longshot": ("Tier F", "Long shot"),
}


def market_decision_label(nwr_rank: object, market_rank: object) -> tuple[str, str]:
    """Return a display-only five-band interpretation and signed rank gap."""

    nwr = _number(nwr_rank)
    market = _number(market_rank)
    if nwr is None or market is None:
        return "Market data unavailable", ""
    gap = market - nwr
    if gap >= 20:
        label = "Potential Buy"
    elif gap > 5:
        label = "NWR Higher"
    elif gap >= -5:
        label = "Aligned"
    elif gap > -20:
        label = "Market Higher"
    else:
        label = "Potential Sell / Caution"
    return label, f"{gap:+.1f} ranks vs market"


def market_rank_gap(nwr_rank: object, market_rank: object) -> float | None:
    """Return market rank minus NWR rank; positive means NWR is higher."""

    nwr = _number(nwr_rank)
    market = _number(market_rank)
    return None if nwr is None or market is None else market - nwr


def owner_range(row: Mapping[str, Any]) -> dict[str, str]:
    """Use the frozen research signals without inventing a numeric interval."""

    return {
        "Floor": _probability_label("Downside signal", row.get("research_downside_signal")),
        "Expected": translate_research_tier(row.get("research_tier") or row.get("source_tier")),
        "Ceiling": _probability_label("Ceiling signal", row.get("research_ceiling_signal")),
    }


def owner_range_contract(row: Mapping[str, Any]) -> dict[str, str]:
    """Describe the admitted range vocabulary and its asset-specific method."""

    values = owner_range(row)
    asset_type = _text(row.get("asset_type") or row.get("compare_asset_type"))
    supported = any(value != "Not enough information" for value in values.values())
    if asset_type == "Current Player":
        method = (
            "Frozen Unified Research downside, tier, and ceiling signals, read beside "
            "Finished V1 rank, lifecycle, confidence, and governed Outcome context."
        )
        authority = "Research context beside Finished V1"
    elif asset_type == "Rookie Review":
        method = (
            "Rookie Review and frozen Unified Research neighborhoods. Rookie uncertainty "
            "is intentionally wider and never becomes a Finished V1 veteran range."
        )
        authority = "Rookie Review / research only"
    else:
        method = "No admitted dynasty or rookie outlook-signal method for this asset authority."
        authority = "Unsupported for this asset type"
    return {
        **values,
        "NWR Expected": values["Expected"],
        "Downside label": "Downside signal",
        "Expected label": "Research neighborhood",
        "Upside label": "Upside signal",
        "Method": method,
        "Authority": authority,
        "Status": "Supported context" if supported else "Not enough information",
    }


def owner_value_tier(value: object) -> tuple[str, str]:
    """Translate the admitted candidate value band into stable owner language."""

    text = _text(value)
    if not text:
        return "Unassigned", "No admitted value band"
    return _VALUE_BAND_PRESENTATION.get(
        text.casefold(),
        ("Unassigned", text.replace("_", " ").title()),
    )


def owner_risk(row: Mapping[str, Any]) -> str:
    direct = _text(row.get("risk") or row.get("risk_level"))
    if direct:
        return direct.replace("_", " ").title()
    caveats = owner_caveats(
        row.get("raw_caveat_codes")
        or row.get("risk_notes")
        or row.get("warning_flags"),
    )
    material = tuple(
        caveat
        for caveat in caveats
        if any(
            term in caveat.casefold()
            for term in ("age", "confidence", "incomplete", "decline", "fragility", "caution")
        )
    )
    if material:
        return material[0]
    confidence = _text(row.get("confidence") or row.get("research_confidence"))
    return f"Confidence: {confidence}" if confidence else "No major risk flag"


def owner_availability(row: Mapping[str, Any]) -> str:
    """Return only an admitted injury/availability note, otherwise fail closed."""

    caveats = owner_caveats(
        row.get("raw_caveat_codes")
        or row.get("risk_notes")
        or row.get("warning_flags"),
    )
    availability = tuple(
        caveat
        for caveat in caveats
        if any(
            term in caveat.casefold()
            for term in ("injury", "injured", "availability", "inactive", "reserve")
        )
    )
    return availability[0] if availability else "Not enough information"


def translate_research_tier(value: object) -> str:
    text = _text(value)
    if not text:
        return "Not enough information"
    if text.upper().startswith("RESEARCH_TIER_"):
        return f"Research neighborhood {text.rsplit('_', 1)[-1]}"
    return text.replace("_", " ").title() if "_" in text else text


def owner_rankings_frame(rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    output: list[dict[str, object]] = []
    for row in rows:
        if _text(row.get("asset_type")) != "Current Player":
            continue
        label, _gap_text = market_decision_label(
            row.get("dynasty_rank"), row.get("market_dp_rank")
        )
        gap = market_rank_gap(row.get("dynasty_rank"), row.get("market_dp_rank"))
        range_values = owner_range(row)
        tier, nwr_view = owner_value_tier(row.get("value_band"))
        output.append(
            {
                "Rank": _integer(row.get("dynasty_rank")),
                "Player": _text(row.get("asset_name")),
                "Pos": _text(row.get("position")),
                "Team": _text(row.get("team")),
                "Age": _number(row.get("age")),
                "Pos Rank": _text(row.get("position_rank")),
                "Tier": tier,
                "NWR Score": _number(row.get("nwr_dynasty_score")),
                "NWR View": nwr_view,
                "Range": range_values["Expected"],
                "Market": label,
                "Market Rank": _integer(row.get("market_dp_rank")),
                "NWR vs Market": gap,
                "Market Value": _number(row.get("market_dp_value")),
                "Market Date": _text(row.get("market_evidence_date")) or "Unavailable",
                "Confidence": _text(row.get("confidence")) or "Not enough information",
                "Risk": owner_risk(row),
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
