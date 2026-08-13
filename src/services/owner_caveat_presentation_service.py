"""Deterministic owner-facing presentation for governed caveat receipt codes."""

from __future__ import annotations

import re
from collections.abc import Iterable

CAVEAT_PRESENTATION_MAP: dict[str, str] = {
    "BLOCKED_UNRESOLVED_IDENTITY": (
        "The source draft record does not yet have an exact player ID."
    ),
    "Canonical nflverse draft row has no exact GSIS player_id.": (
        "The source draft record does not yet have an exact player ID."
    ),
    "licensed_route_metrics_not_available": "Route-level metrics are unavailable.",
    "not_used_in_stats_first_value": (
        "This evidence is context only and was not used in the production value."
    ),
    "missing_lifecycle_or_role_shape_evidence": "Role/lifecycle evidence is incomplete.",
    "missing_or_review_route_target_snap_evidence": (
        "Route, target, or snap evidence is incomplete."
    ),
    "missing_stats_first_component_evidence": "Some production-component evidence is unavailable.",
    "missing_efficiency_context_evidence": "Efficiency context is incomplete.",
    "partial_first_down_confidence_cap": "First-down evidence is partial, so confidence is capped.",
    "missing_stats_first_confidence_cap": "Missing production evidence limits confidence.",
    "missing_or_review_first_down_evidence": "First-down evidence needs review.",
    "first_down_missing_confidence_cap": "Missing first-down evidence limits confidence.",
    "no_historical_evidence_for_component": "Historical evidence for one component is unavailable.",
    "shifted_header_expected_player_header_inferred": (
        "One source header required a governed identity repair."
    ),
    "rb_dynasty_age_curve_after_27_active": "RB age-related decline adjustment is active.",
    "rb_age_window_caution_active": "The running back is in an age-window that deserves caution.",
    "te_upper_band_guard_v2_te_exception_gate_not_met": (
        "The tight-end upper-band exception was not supported."
    ),
    "te_no_premium_age_curve_after_30_active": "TE age-related decline adjustment is active.",
    "one_qb_replacement_level_qb_cap": "1QB replacement depth limits QB scarcity value.",
    "one_qb_context_balance_upper_band_guard_v2": "The 1QB format limits the upper value band.",
    "owned_by_other_team": "This pick is currently owned by another team.",
    "player_equivalence_unavailable": (
        "No governed player-equivalence value is available for this pick."
    ),
}

EVIDENCE_STATUS_PRESENTATION_MAP: dict[str, str] = {
    "RESEARCH_ONLY_NOT_ADMITTED": "Research-only; not admitted to Finished V1.",
    "research_only_not_admitted": "Research-only; not admitted to Finished V1.",
    "drafted_admitted_review_only": "Admitted to Rookie Review; review-only evidence.",
    "REVIEW_ONLY": "Review-only evidence.",
}


def caveat_codes(value: object) -> tuple[str, ...]:
    """Return stable, de-duplicated raw receipt codes from a source field."""

    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        parts = [str(item or "").strip() for item in value]
    else:
        parts = re.split(r"[|;,]", str(value or ""))
    return tuple(dict.fromkeys(part.strip() for part in parts if part.strip()))


def owner_caveat_text(code: object) -> str:
    """Translate one raw receipt code without changing its stored meaning."""

    raw = str(code or "").strip()
    if not raw:
        return ""
    if raw in CAVEAT_PRESENTATION_MAP:
        return CAVEAT_PRESENTATION_MAP[raw]
    if "gsis" in raw.casefold():
        if "newer governed source" in raw.casefold():
            return (
                "A newer source has an exact player ID, but the frozen Rookie Review "
                "has not been rebuilt with it. The prospect remains visible and unranked."
            )
        return "The source draft record does not yet have an exact player ID."
    if " " in raw and "_" not in raw:
        return raw if raw.endswith((".", "!", "?")) else f"{raw}."
    words = re.sub(r"_v\d+\b", "", raw).replace("_", " ")
    words = re.sub(r"\s+", " ", words).strip()
    if not words:
        return "Additional governed evidence caveat is recorded."
    return words[0].upper() + words[1:] + ("" if words.endswith(".") else ".")


def owner_caveats(value: object, *, limit: int | None = None) -> tuple[str, ...]:
    translated = tuple(dict.fromkeys(owner_caveat_text(code) for code in caveat_codes(value)))
    translated = tuple(text for text in translated if text)
    return translated if limit is None else translated[:limit]


def owner_caveat_summary(value: object, *, limit: int = 2) -> str:
    translated = owner_caveats(value, limit=limit)
    return " ".join(translated) if translated else "No major caveat is recorded."


def owner_evidence_status(value: object) -> str:
    """Translate a research/admission receipt status for primary owner surfaces."""

    raw = str(value or "").strip()
    if not raw:
        return "Review-only evidence."
    if raw in EVIDENCE_STATUS_PRESENTATION_MAP:
        return EVIDENCE_STATUS_PRESENTATION_MAP[raw]
    if "_" not in raw and not raw.isupper():
        return raw if raw.endswith((".", "!", "?")) else f"{raw}."
    words = re.sub(r"_v\d+\b", "", raw).replace("_", " ").lower()
    words = re.sub(r"\s+", " ", words).strip()
    return words[:1].upper() + words[1:] + ("" if words.endswith(".") else ".")
