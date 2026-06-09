from __future__ import annotations

from src.services.player_feature_receipts_service import (
    FORMULA_DERIVED_WARNING,
    PlayerFeatureReceiptsReport,
    receipt_rows_for_players,
)
from src.services.warning_language_service import (
    confidence_explanation,
    confidence_label,
    warning_summary,
)

BRIDGE_RECEIPT_FEATURES = {
    "draft_capital_prior_score",
    "young_nfl_bridge_decay_weight",
    "young_nfl_bridge_nfl_evidence_weight",
    "young_nfl_bridge_prior",
}
DETAILED_PRIVATE_COMPONENTS = {
    "veteran_base_value",
    "win_now_value",
    "dynasty_hold_value",
    "horizon_retention_score",
    "lve_format_fit",
}
WRAPPER_FEATURES = {
    "private_lve_value",
    "keeper_score",
    "trade_value",
    "win_now_value",
    "dynasty_hold_value",
    "confidence_score",
}


def build_my_team_decision_receipts(
    team_rows: list[dict[str, object]],
    receipt_report: PlayerFeatureReceiptsReport,
) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for team_row in team_rows:
        receipt_rows = receipt_rows_for_players(
            receipt_report,
            [
                {
                    "player": team_row.get("player", ""),
                    "position": team_row.get("pos") or team_row.get("position") or "",
                }
            ],
            player_column="player",
            position_column="position",
            include_fallback_rows=False,
            page_source="My Team",
        )
        receipts.append(_decision_receipt(team_row, receipt_rows))
    return receipts


def _decision_receipt(
    team_row: dict[str, object],
    receipt_rows: list[dict[str, object]],
) -> dict[str, object]:
    warnings = _warnings(team_row, receipt_rows)
    confidence = _float(team_row.get("confidence"))
    return {
        "player": team_row.get("player", ""),
        "position": team_row.get("pos") or team_row.get("position") or "",
        "lifecycle": team_row.get("asset_lifecycle_label")
        or team_row.get("asset_lifecycle")
        or "",
        "lifecycle_explanation": _lifecycle_explanation(team_row, receipt_rows),
        "top_five_rule": team_row.get("top_five_rule", ""),
        "model_recommendation": team_row.get("model_recommendation", ""),
        "release_pain": team_row.get("release_pain", ""),
        "release_pain_explanation": _release_pain_explanation(team_row),
        "top_positive_drivers": _driver_summary(receipt_rows, positive=True),
        "top_negative_drivers": _driver_summary(receipt_rows, positive=False),
        "model_value_drivers": _driver_summary(receipt_rows, positive=True),
        "stats_value_drivers": _driver_summary(receipt_rows, positive=True),
        "bridge_prior": _bridge_prior_summary(receipt_rows),
        "market_edge": _market_edge_summary(team_row, receipt_rows),
        "source_warnings": "; ".join(warnings) if warnings else "No active source warning.",
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(confidence, *warnings),
    }


def _private_driver_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    driver_rows = [
        row
        for row in rows
        if str(row.get("component") or "") in DETAILED_PRIVATE_COMPONENTS
        and str(row.get("formula_feature_name") or "") not in BRIDGE_RECEIPT_FEATURES
        and str(row.get("formula_feature_name") or "") not in WRAPPER_FEATURES
        and str(row.get("receipt_section_label") or "") != "Market/Liquidity"
    ]
    if not driver_rows:
        driver_rows = [
            row
            for row in rows
            if str(row.get("component") or "") == "private_lve_value"
            and str(row.get("formula_feature_name") or "") not in BRIDGE_RECEIPT_FEATURES
            and str(row.get("receipt_section_label") or "") != "Market/Liquidity"
        ]
    return _dedupe_driver_rows(driver_rows)


def _driver_summary(rows: list[dict[str, object]], *, positive: bool) -> str:
    driver_rows = [
        row
        for row in _private_driver_rows(rows)
        if _contribution_matches_direction(row, positive=positive)
    ]
    top_rows = sorted(
        driver_rows,
        key=lambda row: -abs(_float(row.get("contribution"))),
    )[:3]
    if not top_rows:
        return (
            "No positive private/stat drivers are available."
            if positive
            else "No negative private/stat drivers are available."
        )
    return " | ".join(
        f"{_feature_label(row.get('formula_feature_name'))}: {_float(row.get('contribution')):.2f}"
        for row in top_rows
    )


def _contribution_matches_direction(
    row: dict[str, object],
    *,
    positive: bool,
) -> bool:
    contribution = _float(row.get("contribution"))
    return contribution > 0 if positive else contribution < 0


def _lifecycle_explanation(
    team_row: dict[str, object],
    rows: list[dict[str, object]],
) -> str:
    lifecycle = str(
        team_row.get("asset_lifecycle_label")
        or team_row.get("asset_lifecycle")
        or "Unknown"
    )
    lower = lifecycle.lower()
    if "year-one" in lower or "year one" in lower:
        return (
            f"{lifecycle}: limited NFL evidence, so the model shows a young-player "
            "bridge prior separately from current NFL/stat drivers."
        )
    if "year-two" in lower or "year two" in lower:
        return (
            f"{lifecycle}: NFL evidence is taking over, but the draft/prospect "
            "prior can still contribute a smaller bridge amount."
        )
    if "year-three" in lower or "year three" in lower:
        return (
            f"{lifecycle}: mostly NFL evidence, with only a small remaining "
            "young-player bridge prior."
        )
    if "bridge" in lower:
        bridge = _bridge_prior_summary(rows)
        return f"{lifecycle}: young-player bridge is active. {bridge}"
    if "established" in lower:
        return f"{lifecycle}: draft capital is display-only; value comes from NFL/stat evidence."
    if "rookie" in lower:
        return (
            f"{lifecycle}: should be evaluated through rookie/prospect inputs, "
            "not veteran stats."
        )
    return f"{lifecycle}: inspect source warnings if this assignment looks wrong."


def _bridge_prior_summary(rows: list[dict[str, object]]) -> str:
    bridge_rows = [
        row
        for row in rows
        if str(row.get("formula_feature_name") or "") in BRIDGE_RECEIPT_FEATURES
    ]
    if not bridge_rows:
        return "No young-player bridge prior scored."
    by_feature = {
        str(row.get("formula_feature_name") or ""): row for row in bridge_rows
    }
    parts = []
    prior_row = by_feature.get("draft_capital_prior_score")
    if prior_row:
        parts.append(f"draft/prospect prior {_float(prior_row.get('normalized_score')):.1f}")
    bridge_weight_row = by_feature.get("young_nfl_bridge_decay_weight")
    if bridge_weight_row:
        parts.append(f"bridge prior weight {_bridge_weight_text(bridge_weight_row)}")
    nfl_weight_row = by_feature.get("young_nfl_bridge_nfl_evidence_weight")
    if nfl_weight_row:
        parts.append(f"NFL evidence weight {_bridge_weight_text(nfl_weight_row)}")
    contribution_row = by_feature.get("young_nfl_bridge_prior")
    if contribution_row:
        parts.append(f"bridge contribution {_float(contribution_row.get('contribution')):.2f}")
    return "; ".join(parts)


def _market_edge_summary(
    team_row: dict[str, object],
    rows: list[dict[str, object]],
) -> str:
    market_status = str(team_row.get("market_value_status") or "").strip().lower()
    market_warning = str(team_row.get("market_edge_warning") or "").strip()
    if market_status in {
        "missing_market",
        "neutral_market_placeholder",
        "disabled_market",
        "stale_market",
    }:
        return (
            "Trade market unavailable; no Model vs Market edge is trusted."
            if not market_warning
            else (
                "Trade market unavailable; "
                f"{warning_summary(market_warning, default=market_warning)}."
            )
        )
    market_edge = team_row.get("market_edge")
    if market_edge not in (None, ""):
        return f"Model vs market {float(market_edge):.2f}."
    market_rows = [
        row
        for row in rows
        if str(row.get("receipt_section_label") or "") == "Market/Liquidity"
    ]
    if not market_rows:
        return "No market/liquidity receipt available."
    top = max(market_rows, key=lambda row: abs(_float(row.get("contribution"))))
    return (
        f"{_feature_label(top.get('formula_feature_name'))}: "
        f"{_float(top.get('contribution')):.2f}."
    )


def _release_pain_explanation(team_row: dict[str, object]) -> str:
    top_five_rule = str(team_row.get("top_five_rule") or "")
    recommendation = str(team_row.get("model_recommendation") or "")
    explanation = str(
        team_row.get("decision_explanation")
        or team_row.get("top_five_rule_note")
        or ""
    )
    if top_five_rule == "Required Top-Five Release Slot":
        pain = team_row.get("release_pain")
        pain_text = "" if pain in (None, "") else f" Release pain: {float(pain):.2f}."
        return (
            "This player currently satisfies the Required Top-Five Release Slot "
            "for this roster. "
            f"Model recommendation: {recommendation}.{pain_text} {explanation}"
        ).strip()
    return (
        f"Top-Five Rule Status: {top_five_rule}. "
        f"Model recommendation: {recommendation}. {explanation}"
    ).strip()


def _warnings(
    team_row: dict[str, object],
    rows: list[dict[str, object]],
) -> list[str]:
    warnings = {
        _first_view_warning(value)
        for value in (
            team_row.get("warning_reason"),
            team_row.get("warning_status"),
            team_row.get("market_edge_warning"),
        )
        if _first_view_warning(value)
    }
    for row in rows:
        for field in ("warning_reason", "warning_status"):
            value = _first_view_warning(row.get(field))
            if value:
                warnings.add(value)
    return sorted(warnings)


def _feature_label(value: object) -> str:
    text = str(value or "").strip()
    labels = {
        "weighted_recent_lve_ppg_score": "recent LVE scoring",
        "expected_lve_points_score": "expected LVE points",
        "lve_projection_value": "projection value",
        "role_security": "role security",
        "workload_earning": "workload earning",
        "target_earning_stability": "target earning",
        "route_share_stability": "route share stability",
        "route_role": "route role",
        "efficiency_score": "efficiency",
        "first_down_td_fit": "first-down/TD fit",
        "first_down_td_fit_capped": "first-down/TD fit cap",
        "age_curve": "age window",
        "injury_durability": "injury durability",
        "position_replaceability": "position replaceability",
        "lve_structural_formula_adjustment": "LVE structural adjustment",
        "market_liquidity": "trade market liquidity",
        "market_edge": "model vs market",
    }
    return labels.get(text, text.replace("_", " "))


def _dedupe_driver_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_feature: dict[str, dict[str, object]] = {}
    for row in rows:
        feature = str(row.get("formula_feature_name") or "")
        current = by_feature.get(feature)
        if current is None or abs(_float(row.get("contribution"))) > abs(
            _float(current.get("contribution"))
        ):
            by_feature[feature] = row
    return list(by_feature.values())


def _bridge_weight_text(row: dict[str, object]) -> str:
    value = _float(row.get("normalized_score"))
    if 0.0 < value <= 1.0:
        value *= 100.0
    return f"{value:.0f}%"


def _first_view_warning(value: object) -> str:
    text = str(value or "").strip()
    if not text or text == FORMULA_DERIVED_WARNING:
        return ""
    if text == "missing stats-first source feature; model used neutral formula default":
        return "missing stats-first feature; neutral default used"
    return warning_summary(text, default=text)


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default
