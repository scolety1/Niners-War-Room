"""Owner-facing explanation of the receipts carried by Finished V1 rows."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.services.owner_caveat_presentation_service import owner_caveat_summary

FIELD_LABELS = {
    "position": "Position context",
    "nwr_dynasty_score": "Admitted dynasty score",
    "production_nwr_score": "Production-based NWR score",
    "position_specific_review_score": "Position-specific review score",
    "positive_vorp_points": "Positive value over replacement",
    "review_scoring_points": "League scoring production",
    "imported_first_down_points": "First-down production",
    "discipline_multiplier": "Position / format discipline",
    "lifecycle_modifier_review": "Age and lifecycle adjustment",
    "role_archetype": "Role archetype",
    "role_fragility_status": "Role fragility check",
    "confidence_cap": "Evidence confidence cap",
    "available_component_weight": "Available evidence weight",
    "warning_flags": "Warnings / missing evidence",
}


def owner_rank_explanation(
    row: dict[str, Any], *, total_ranked: int
) -> tuple[str, pd.DataFrame, str]:
    name = _text(row.get("player_name")) or "This player"
    rank = _integer(row.get("nwr_rank"))
    score = _text(row.get("nwr_dynasty_score")) or "unavailable"
    if rank is None:
        summary = f"{name} is unranked because the admitted Finished V1 score is unavailable."
    elif rank <= 25:
        summary = (
            f"NWR is high on {name}: the admitted score ({score}) places the player "
            f"#{rank} of {total_ranked} ranked skill players."
        )
    elif rank > max(150, int(total_ranked * 0.65)):
        summary = (
            f"NWR is cautious on {name}: the admitted score ({score}) places the player "
            f"#{rank} of {total_ranked}."
        )
    else:
        summary = (
            f"NWR places {name} in the middle of the board at #{rank} of {total_ranked} "
            f"with an admitted score of {score}."
        )
    fields = [
        value
        for value in _text(row.get("candidate_evidence_fields_used")).split("|")
        if value
    ]
    evidence_rows: list[dict[str, str]] = []
    for field in fields:
        value = _text(row.get(field))
        evidence_rows.append(
            {
                "Evidence": FIELD_LABELS.get(field, field.replace("_", " ").title()),
                "Receipt value": value or "Used by admitted receipt; raw value not carried here",
                "Effect": _effect(field, value),
            }
        )
    adjustment = _text(row.get("candidate_adjustment"))
    if adjustment:
        evidence_rows.append(
            {
                "Evidence": "Admitted adjustment",
                "Receipt value": adjustment,
                "Effect": "HELPED" if _number(adjustment) > 0 else (
                    "HURT" if _number(adjustment) < 0 else "NEUTRAL"
                ),
            }
        )
    reasons = _text(row.get("candidate_reason_codes"))
    if reasons:
        evidence_rows.append(
            {
                "Evidence": "Why / gate reasons",
                "Receipt value": reasons.replace("|", "; ").replace("_", " "),
                "Effect": "CONTEXT",
            }
        )
    caveat = owner_caveat_summary(
        _text(row.get("warning_flags")) or _text(row.get("data_needed"))
    )
    return summary, pd.DataFrame(evidence_rows), caveat


def _effect(field: str, value: str) -> str:
    if field == "positive_vorp_points":
        return "HELPED"
    if field in {"confidence_cap", "role_fragility_status", "warning_flags"}:
        return "RISK / CAP"
    if field in {"nwr_dynasty_score", "production_nwr_score"}:
        return "BASE"
    return "USED"


def _number(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _integer(value: object) -> int | None:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return None


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.casefold() in {"nan", "none", "null", "<na>"} else text
