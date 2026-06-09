from __future__ import annotations

import re

NO_ACTIVE_WARNING = "No active warning."

_WARNING_TRANSLATIONS = {
    "data_warning": "source data needs review",
    "data_warning_stale_sources": "stale source: imported NFL stats stop before current snapshot",
    "data_warning_missing_inputs": "missing core football inputs",
    "data_warning_confidence_below_target": "confidence below target",
    "model_warning": "model output needs review",
    "model_warning_role_or_keeper_fragility": "role or keeper fragility",
    "model_warning_keeper_fragility": "keeper fragility",
    "review_needed": "review needed",
    "review_needed_low_confidence": "low confidence",
    "blocking_low_confidence": "blocked confidence",
    "review_needed_missing_core_inputs": "missing core football inputs",
    "local_baseline_projection_not_independent": (
        "projection is a local baseline, not forecast"
    ),
    "missing_participation_proxy": "missing route/participation data; using proxy role evidence",
    "missing_snap_counts": "missing snap-count data",
    "stale_lve_scoring_source": "stale production source",
    "accepted_source_gap_confidence_drag": (
        "accepted optional source gap; confidence penalty retained"
    ),
    "review_source_gap": "source gap needs review",
    "critical_source_review": "critical source bucket needs review",
    "imputed_core_source_bucket": "proxy-heavy core data",
    "blocked": "blocked",
    "stale_source": "stale source",
    "stale_sources": "stale source",
    "source_stale": "stale source",
    "using_stale_sources": "stale source",
    "missing_projection": "missing projection",
    "missing_projections": "missing projection",
    "projection_missing": "missing projection",
    "missing_source_projection": "missing projection",
    "imputed_role": "imputed role",
    "role_imputed": "imputed role",
    "missing_role": "imputed role",
    "missing_role_usage": "imputed role",
    "identity_review": "identity review",
    "identity_ambiguous": "identity review",
    "identity_match_review": "identity review",
    "identity_low_confidence": "identity review",
    "low_confidence": "low confidence",
    "confidence_low": "low confidence",
    "one_feature_driven_rank": "one-feature-driven rank",
    "single_feature_driven_rank": "one-feature-driven rank",
    "high_single_feature_share": "one-feature-driven rank",
    "market_disagreement": "market disagreement",
    "market_edge_warning": "market disagreement",
    "market_gap": "market disagreement",
    "market_resistance": "market disagreement",
    "market_higher_than_model": "market disagreement",
    "model_higher_than_market": "market disagreement",
    "missing_private_and_market_values": "missing market value",
    "missing_market_trade_value": "missing market value",
    "missing_market": "missing market value",
    "neutral_market_placeholder": "market value is a neutral placeholder",
    "market_value_disabled": "market value disabled",
    "disabled_market": "market value disabled",
    "stale_market": "stale market value",
    "stale_market_value": "stale market value",
    "missing_private_value": "missing model value",
    "missing_source_feature_uses_formula_default": "missing source feature",
    "source_feature_marked_missing": "missing source feature",
    "derived_component_input": "derived component",
    "keeper_bubble": "keeper bubble",
    "drop_candidate": "drop candidate",
    "injury_risk": "injury risk",
    "committee_risk": "committee risk",
    "rb_weak_age_window": "RB age window risk",
    "rb_workload_injury_fragility": "RB workload/injury fragility",
    "weak_chain_or_td_role": "weak first-down or TD role",
    "weak_target_earning": "weak target earning",
    "route_role_fragility": "route role fragility",
    "wr_unstable_role": "unstable WR role",
    "replaceable_1qb_profile": "replaceable 1QB profile",
    "qb_below_replacement_edge": "QB near replacement line",
    "qb_start_security_risk": "QB start security risk",
    "qb_rushing_not_start_gated": "QB rushing not backed by start security",
    "pocket_qb_1qb_suppression": "pocket QB suppression in 1QB",
    "blocking_dependency_risk": "blocking dependency risk",
    "weak_te_target_earning": "weak TE target earning",
    "low_route_te_profile": "low-route TE profile",
    "replaceable_no_premium_te": "replaceable TE in no-premium scoring",
}

_READY_CODES = {"", "ready", "ok", "none", "no_warning", "no_active_warning"}
_SPLIT_PATTERN = re.compile(r"[|,;]+")


def warning_phrase(code: object) -> str:
    normalized = _normalize_code(code)
    if normalized in _READY_CODES:
        return ""
    if normalized.startswith("formula_proxy_from_"):
        feature = normalized.removeprefix("formula_proxy_from_").replace("_", " ")
        return f"uses {feature} proxy"
    category = _category_phrase(normalized)
    if category:
        return category
    return _WARNING_TRANSLATIONS.get(normalized, normalized.replace("_", " "))


def warning_summary(
    *values: object,
    default: str = NO_ACTIVE_WARNING,
) -> str:
    phrases: list[str] = []
    for value in values:
        for token in _warning_tokens(value):
            phrase = warning_phrase(token)
            if phrase and phrase not in phrases:
                phrases.append(phrase)
    if not phrases:
        return default
    return "; ".join(phrases)


def warning_list(*values: object) -> list[str]:
    summary = warning_summary(*values, default="")
    if not summary:
        return []
    return summary.split("; ")


def confidence_label(value: object) -> str:
    score = _score(value)
    if score is None:
        return "blocked"
    if score >= 85:
        return "strong"
    if score >= 78:
        return "usable"
    if score >= 65:
        return "review"
    if score >= 40:
        return "weak"
    return "blocked"


def confidence_explanation(
    value: object,
    *warnings: object,
) -> str:
    label = confidence_label(value)
    score = _score(value)
    score_text = "n/a" if score is None else f"{score:.1f}"
    warning_text = warning_summary(*warnings, default="")
    base = {
        "strong": "Strong confidence: source quality supports normal roster review.",
        "usable": (
            "Usable confidence: source quality is acceptable, but still inspect "
            "key warnings."
        ),
        "review": "Review confidence: do not act without checking receipts and source notes.",
        "weak": "Weak confidence: source gaps or proxy data materially limit trust.",
        "blocked": "Blocked confidence: missing or unreliable inputs prevent trusted action.",
    }[label]
    if warning_text:
        return f"{base} Score {score_text}. Main warning: {warning_text}."
    return f"{base} Score {score_text}."


def _warning_tokens(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [
        token
        for token in (_normalize_code(part) for part in _SPLIT_PATTERN.split(text))
        if token and token not in _READY_CODES
    ]


def _normalize_code(value: object) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("-", "_").replace(" ", "_")
    return re.sub(r"[^a-z0-9_]+", "", text)


def _category_phrase(code: str) -> str:
    if code in _WARNING_TRANSLATIONS:
        return _WARNING_TRANSLATIONS[code]
    if "identity" in code:
        return "identity review"
    if "stale" in code or "freshness" in code:
        return "stale source"
    if "projection" in code and "missing" in code:
        return "missing projection"
    if "local_baseline_projection" in code:
        return "projection is a local baseline, not forecast"
    if "participation" in code or "snap_count" in code or "snap_counts" in code:
        return "missing route/participation data; using proxy role evidence"
    if "source_gap" in code and "accepted" in code:
        return "accepted optional source gap; confidence penalty retained"
    if "role" in code and ("imputed" in code or "missing" in code):
        return "imputed role"
    if "confidence" in code and ("low" in code or "warning" in code):
        return "low confidence"
    if "one_feature" in code or "single_feature" in code:
        return "one-feature-driven rank"
    if "market" in code and ("gap" in code or "disagreement" in code or "warning" in code):
        return "market disagreement"
    return ""


def _score(value: object) -> float | None:
    try:
        text = str(value)
        if text == "":
            return None
        score = float(text)
    except (TypeError, ValueError):
        return None
    if 0 < score <= 1:
        score *= 100.0
    return max(0.0, min(100.0, score))
