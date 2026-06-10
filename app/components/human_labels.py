from __future__ import annotations

import re
from collections.abc import Iterable

LABELS: dict[str, str] = {
    "manual_only_no_exact_model_baseline": "Manual only: no reliable baseline",
    "review_only_no_final_recommendation": "Review only",
    "review_only_no_final_decision_recommendation": "Review only",
    "review_only_no_final_rookie_pick_recommendation": "No final rookie pick",
    "review_only_no_cut_keep_recommendation": "No cut/keep call",
    "review_only_no_trade_recommendation": "No trade call",
    "review_only_no_pick_trade_recommendation": "No pick-trade call",
    "source_shape_warning": "Data shape warning",
    "model_edge_weirdness": "Model edge",
    "no_premium_te_cap": "No-TE-premium cap",
    "no_premium_te_cap_warning": "No-TE-premium cap",
    "no_premium_te_small_gap_cap": "No-TE-premium cap",
    "no_premium_te_replacement_level_cap": "No-TE-premium cap",
    "one_qb_qb_scarcity_cap": "1QB value cap",
    "one_qb_small_vorp_gap_cap": "1QB value cap",
    "missing_or_review_route_target_snap_evidence": "Missing route/target/snap evidence",
    "rb_age_cliff_guardrail_unavailable": "RB age-risk check needed",
    "rb_dynasty_age_curve_after_27_active": "RB dynasty age curve active",
    "rb_dynasty_age_curve_30_plus_active": "RB 30-plus age cliff active",
    "rb_extreme_age_cliff_active": "RB late-career age cliff active",
    "wr_age_curve_unavailable": "WR age check needed",
    "wr_dynasty_age_curve_after_30_active": "WR dynasty age curve active",
    "wr_mid_30s_age_cliff_active": "WR mid-30s age cliff active",
    "te_age_curve_unavailable": "TE age check needed",
    "te_no_premium_age_curve_after_30_active": "No-premium TE age curve active",
    "te_age_33_plus_cliff_active": "TE 33-plus age cliff active",
    "qb_rushing_age_caution_unavailable": "QB rushing-age check needed",
    "missing_lifecycle_or_role_shape_evidence": "Missing lifecycle/role evidence",
    "partial_or_quarantined_join_cap": "Partial/quarantined join",
    "identity_review_cap": "Identity review needed",
    "source_limited_evidence_cap": "Source-limited evidence",
    "third_party_combine_source_limited": "Third-party combine source-limited",
    "market_context_excluded_from_private_value": "Market context excluded from model value",
    "pick_value_baseline_missing": "Pick baseline missing",
    "rookie_pick_equivalent_uncertain": "Rookie pick equivalent uncertain",
    "heuristic_pick_curve_requires_audit": "Pick curve requires review",
    "future_pick_baseline_higher_than_current_same_slot": (
        "Future same-slot baseline is higher"
    ),
    "draft_capital_anchor_warning": "NFL draft pick signal guardrail",
    "format_discipline_case": "Format discipline",
}


def human_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text in LABELS:
        return LABELS[text]
    if ":" in text:
        prefix, detail = text.split(":", 1)
        prefix_label = LABELS.get(prefix, _title_from_code(prefix))
        detail_label = _title_from_code(detail)
        return f"{prefix_label}: {detail_label}"
    return _title_from_code(text)


def human_labels(value: object, *, separators: str = r"[|;]") -> str:
    labels = [label for label in re.split(separators, str(value or "")) if label.strip()]
    return "; ".join(human_label(label) for label in labels)


def human_label_list(values: Iterable[object]) -> list[str]:
    return [human_label(value) for value in values]


def _title_from_code(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().capitalize()
