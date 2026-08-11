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
        value for value in _text(row.get("candidate_evidence_fields_used")).split("|") if value
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
                "Effect": "HELPS"
                if _number(adjustment) > 0
                else ("HURTS" if _number(adjustment) < 0 else "NEUTRAL"),
            }
        )
    reasons = _text(row.get("candidate_reason_codes"))
    if reasons:
        reason_labels = tuple(
            _reason_label(reason) for reason in reasons.split("|") if reason
        )
        evidence_rows.append(
            {
                "Evidence": "Why / gate reasons",
                "Receipt value": "; ".join(reason_labels),
                "Effect": _reason_effect(reasons),
            }
        )
    caveat = owner_caveat_summary(_text(row.get("warning_flags")) or _text(row.get("data_needed")))
    return summary, pd.DataFrame(evidence_rows), caveat


def owner_rank_reason_bullets(row: dict[str, Any], *, limit: int = 5) -> tuple[str, ...]:
    """Translate admitted score receipts into a short owner explanation."""

    bullets: list[str] = []
    adjustment = _number(row.get("candidate_adjustment"))
    if adjustment:
        direction = "helps" if adjustment > 0 else "holds back"
        bullets.append(
            f"The admitted adjustment {direction} this player's board position ({adjustment:+.2f})."
        )
    fields = [
        value for value in _text(row.get("candidate_evidence_fields_used")).split("|") if value
    ]
    for field in fields:
        value = _text(row.get(field))
        label = FIELD_LABELS.get(field, field.replace("_", " ").title())
        effect = _effect(field, value)
        if effect == "HELPS":
            bullets.append(f"Helps: {label}" + (f" ({value})." if value else "."))
        elif effect == "HURTS":
            bullets.append(f"Holds them back: {label}" + (f" ({value})." if value else "."))
        elif effect == "MISSING":
            detail = (
                owner_caveat_summary(value)
                if value
                else f"{label} raw value is not carried by the admitted receipt"
            )
            bullets.append(f"Missing or limited: {detail}.")
        else:
            bullets.append(
                f"Neutral context: {label}" + (f" ({value})." if value else ".")
            )
    reasons = [
        _reason_label(value)
        for value in _text(row.get("candidate_reason_codes")).split("|")
        if value
    ]
    for reason in reasons:
        effect = _reason_effect(reason)
        prefix = {
            "HELPS": "Helps",
            "HURTS": "Holds them back",
            "MISSING": "Missing or limited",
        }.get(effect, "Gate context")
        bullets.append(f"{prefix}: {reason}.")
    raw_caveat = _text(row.get("warning_flags")) or _text(row.get("data_needed"))
    if raw_caveat:
        bullets.append(f"Watch-out: {owner_caveat_summary(raw_caveat)}")
    priorities = {
        "Helps:": 0,
        "The admitted adjustment helps": 0,
        "Holds them back:": 1,
        "The admitted adjustment holds back": 1,
        "Neutral context:": 2,
        "Gate context:": 2,
        "Missing or limited:": 3,
        "Watch-out:": 3,
    }
    unique = tuple(dict.fromkeys(bullets))
    ordered = sorted(
        enumerate(unique),
        key=lambda item: (
            next(
                (priority for prefix, priority in priorities.items() if item[1].startswith(prefix)),
                4,
            ),
            item[0],
        ),
    )
    return tuple(value for _index, value in ordered[:limit])


def _effect(field: str, value: str) -> str:
    number = _number(value)
    if field == "warning_flags" or not value:
        return "MISSING"
    if field in {
        "positive_vorp_points",
        "position_specific_review_score",
        "review_scoring_points",
        "imported_first_down_points",
    }:
        return "HELPS" if number > 0 else ("HURTS" if number < 0 else "NEUTRAL")
    if field in {"discipline_multiplier", "lifecycle_modifier_review"}:
        return "HELPS" if number > 1 else ("HURTS" if 0 < number < 1 else "NEUTRAL")
    if field in {"confidence_cap", "available_component_weight"}:
        return "HURTS" if 0 < number < 1 else "NEUTRAL"
    if field == "role_fragility_status":
        normalized = value.casefold()
        return (
            "HURTS"
            if any(term in normalized for term in ("fragile", "caution", "risk"))
            else "NEUTRAL"
        )
    return "NEUTRAL"


def _reason_effect(value: str) -> str:
    normalized = value.casefold().replace("_", " ").replace("-", " ")
    if any(
        term in normalized
        for term in ("no extra lift", "no lift", "neutral", "already supported")
    ):
        return "NEUTRAL"
    if any(term in normalized for term in ("missing", "unavailable", "insufficient")):
        return "MISSING"
    if any(term in normalized for term in ("penalty", "blocked", "fragile", "decline")):
        return "HURTS"
    if any(term in normalized for term in ("supported", "elite", "positive", "priority")):
        return "HELPS"
    return "NEUTRAL"


def _reason_label(value: str) -> str:
    words = value.replace("_", " ").strip().split()
    acronyms = {"qb", "rb", "wr", "te", "nwr", "vorp", "adp"}
    formatted = [word.upper() if word.casefold() in acronyms else word for word in words]
    text = " ".join(formatted)
    return text[:1].upper() + text[1:] if text else ""


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
