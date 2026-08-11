"""Source-separated, manual descriptive Trading Lab brief exports."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from src.services.owner_caveat_presentation_service import owner_caveats

DISCLAIMER = "Manual descriptive analysis — no automatic recommendation"
EXPORT_SCHEMA = "NWR_TRADE_BRIEF_V1"
_PROHIBITED = re.compile(
    r"\b(?:accept|reject|winner|loser|fair|unfair|steal|overpay|exact equal value|"
    r"automatic counteroffer)\b",
    re.IGNORECASE,
)


class TradeBriefValidationError(ValueError):
    pass


@dataclass(frozen=True)
class TradeBriefExport:
    markdown: str
    structured_json: str
    missing_data: tuple[str, ...]


def build_trade_brief(
    scenario: Mapping[str, Any],
    *,
    assets: Mapping[str, Mapping[str, Any]],
    personal: Mapping[str, Mapping[str, Any]] | None = None,
    include_personal: bool = False,
) -> TradeBriefExport:
    required = {"title", "created_at_utc", "side_a", "side_b", "team_window", "rationale"}
    if required - set(scenario):
        raise TradeBriefValidationError("Trade brief scenario is missing required fields.")
    _reject_prohibited_text(scenario)
    personal_rows = personal or {}
    missing: list[str] = []
    sides: dict[str, list[dict[str, Any]]] = {}
    for side_key in ("side_a", "side_b"):
        rows = []
        identifiers = scenario[side_key]
        if not isinstance(identifiers, list):
            raise TradeBriefValidationError("Trade brief sides must be asset-ID lists.")
        for asset_id in identifiers:
            item = assets.get(str(asset_id))
            if item is None:
                missing.append(f"Unknown asset: {asset_id}")
                continue
            row = _brief_asset(str(asset_id), item, missing)
            if include_personal and str(asset_id) in personal_rows:
                overlay = personal_rows[str(asset_id)]
                row["personal"] = {
                    "tier": overlay.get("my_tier", ""),
                    "tags": list(overlay.get("tags", ())),
                    "notes": overlay.get("notes", ""),
                }
            rows.append(row)
        sides[side_key] = rows
    value = {
        "schema": EXPORT_SCHEMA,
        "scenario_title": str(scenario["title"]),
        "created_at_utc": str(scenario["created_at_utc"]),
        "team_window": str(scenario["team_window"]),
        "user_rationale": str(scenario["rationale"]),
        "side_a": sides["side_a"],
        "side_b": sides["side_b"],
        "evidence_warnings": list(scenario.get("evidence_warnings", ())),
        "missing_data": missing,
        "disclaimer": DISCLAIMER,
    }
    markdown = _markdown(value)
    if _PROHIBITED.search(markdown):
        raise TradeBriefValidationError("Trade brief contains prohibited recommendation language.")
    return TradeBriefExport(
        markdown,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        tuple(missing),
    )


def _brief_asset(asset_id: str, item: Mapping[str, Any], missing: list[str]) -> dict[str, Any]:
    asset_type = str(item.get("asset_type", "Not documented"))
    blocked_or_pick = asset_type in {"Blocked Rookie", "Draft Pick"}
    row: dict[str, Any] = {
        "asset_id": asset_id,
        "name": str(item.get("asset_name") or "Not documented"),
        "source_type": asset_type,
        "source_label": str(item.get("source_label") or "Not documented"),
        "authority": str(item.get("authority_status") or "Not documented"),
        "position": str(item.get("position") or "Not documented"),
        "team": str(item.get("team") or "Not documented"),
        "age": str(item.get("age") or ""),
        "position_rank": str(item.get("position_rank") or ""),
        "nwr_dynasty_score": str(item.get("nwr_dynasty_score") or ""),
        "value_band": str(item.get("value_band") or item.get("tier") or ""),
        "confidence": str(item.get("confidence") or ""),
        "market": {
            "dp_value": str(item.get("market_dp_value") or ""),
            "dp_rank": str(item.get("market_dp_rank") or ""),
            "status": str(item.get("market_status") or ""),
            "evidence_date": str(item.get("market_evidence_date") or ""),
        },
        "research": {
            "rank": str(item.get("research_rank") or ""),
            "tier": str(item.get("research_tier") or ""),
            "status": str(item.get("research_status") or ""),
        },
        "outcome_signals": list(item.get("outcome_signals") or ()),
        "warnings": list(
            item.get("owner_caveats")
            or owner_caveats(item.get("warnings") or item.get("blocking_reason") or "")
        ),
    }
    if not blocked_or_pick and item.get("rank_value") not in (None, ""):
        row["rank"] = {
            "label": str(item.get("rank_label") or "Source rank"),
            "value": str(item["rank_value"]),
        }
    elif blocked_or_pick:
        row["rank"] = None
    else:
        row["rank"] = None
        missing.append(f"Missing source rank: {asset_id}")
    if asset_type == "Blocked Rookie" and not row["warnings"]:
        missing.append(f"Missing blocking explanation: {asset_id}")
    return row


def _markdown(value: Mapping[str, Any]) -> str:
    lines = [
        f"# {value['scenario_title']}",
        "",
        f"Created: {value['created_at_utc']}",
        f"Team window: {value['team_window']}",
        "",
    ]
    for title, side_key in (("You give", "side_a"), ("You receive", "side_b")):
        lines.extend((f"## {title}", ""))
        rows = value[side_key]
        if not rows:
            lines.append("- Not documented")
        for row in rows:
            lines.append(
                f"- {row['name']} — {row['source_type']} | {row['source_label']} | "
                f"{row['authority']}"
            )
            lines.append(f"  - Position/team: {row['position']} / {row['team']}")
            rank = row.get("rank")
            if rank:
                lines.append(f"  - {rank['label']}: {rank['value']}")
            else:
                lines.append("  - Source rank: Not provided for this asset type")
            if row.get("position_rank"):
                lines.append(f"  - Position rank: {row['position_rank']}")
            if row.get("age"):
                lines.append(f"  - Age: {row['age']}")
            if row.get("nwr_dynasty_score"):
                lines.append(f"  - NWR Dynasty Score: {row['nwr_dynasty_score']}")
            market = row.get("market", {})
            if market.get("dp_value") or market.get("dp_rank"):
                lines.append(
                    "  - Market context: "
                    f"DP Value {market.get('dp_value') or 'not available'}; "
                    f"DP Rank {market.get('dp_rank') or 'not available'}; "
                    f"{market.get('status') or 'display-only'}"
                )
            for signal in row.get("outcome_signals", ()):
                lines.append(f"  - Outcome context: {signal}")
            for warning in row.get("warnings", ()):
                lines.append(f"  - Evidence warning: {warning}")
            if row.get("personal"):
                overlay = row["personal"]
                lines.append(f"  - Personal tier: {overlay.get('tier') or 'Not documented'}")
                lines.append(
                    f"  - Personal tags: {', '.join(overlay.get('tags', ())) or 'Not documented'}"
                )
                lines.append(f"  - Personal notes: {overlay.get('notes') or 'Not documented'}")
        lines.append("")
    lines.extend(("## User rationale", "", str(value["user_rationale"]) or "Not documented", ""))
    lines.extend(("## Missing data", ""))
    lines.extend(f"- {item}" for item in value["missing_data"])
    if not value["missing_data"]:
        lines.append("- None recorded")
    lines.extend(("", f"> {value['disclaimer']}", ""))
    return "\n".join(lines)


def _reject_prohibited_text(value: Any) -> None:
    values: Iterable[Any]
    if isinstance(value, Mapping):
        values = value.values()
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        if isinstance(value, str) and _PROHIBITED.search(value):
            raise TradeBriefValidationError(
                "User-entered brief text contains prohibited recommendation language."
            )
        return
    for child in values:
        _reject_prohibited_text(child)
