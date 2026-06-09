from __future__ import annotations

from dataclasses import dataclass

from src.services.player_feature_receipts_service import PlayerFeatureReceiptsReport

RECEIPT_SECTION_ORDER = {
    "NFL Production": 1,
    "Role/Usage": 2,
    "First-Down/TD Fit": 3,
    "Age/Injury": 4,
    "Projection": 5,
    "Young-Player Bridge Prior": 6,
    "Market/Liquidity": 7,
}

BRIDGE_FEATURE_LABELS = {
    "draft_capital_prior_score": "Draft capital / prospect prior",
    "young_nfl_bridge_prior_score": "Draft capital / prospect prior",
    "young_nfl_bridge_decay_weight": "Prior decay weight",
    "young_nfl_bridge_nfl_evidence_weight": "NFL evidence weight",
    "young_nfl_bridge_prior": "Final bridge contribution",
}


@dataclass(frozen=True)
class LifecycleReceiptDrilldownReport:
    player: str
    position: str
    lifecycle_label: str
    lifecycle_explanation: str
    section_rows: list[dict[str, object]]
    bridge_rows: list[dict[str, object]]
    component_reconciliation_rows: list[dict[str, object]]
    receipt_rows: list[dict[str, object]]
    issues: list[str]


def build_lifecycle_receipt_drilldown(
    report: PlayerFeatureReceiptsReport,
    player: str,
) -> LifecycleReceiptDrilldownReport:
    rows = _rows_for_player(report, player)
    if not rows:
        return LifecycleReceiptDrilldownReport(
            player=player,
            position="",
            lifecycle_label="",
            lifecycle_explanation="No receipt rows are available for this player.",
            section_rows=[],
            bridge_rows=[],
            component_reconciliation_rows=[],
            receipt_rows=[],
            issues=[f"No lifecycle receipt rows found for {player}."],
        )

    first = rows[0]
    lifecycle_label = str(first.get("asset_lifecycle_label") or "")
    explanation = _lifecycle_explanation(rows)
    return LifecycleReceiptDrilldownReport(
        player=str(first.get("player") or player),
        position=str(first.get("position") or ""),
        lifecycle_label=lifecycle_label,
        lifecycle_explanation=explanation,
        section_rows=_section_rows(rows),
        bridge_rows=_bridge_rows(rows),
        component_reconciliation_rows=_component_reconciliation_rows(report, rows),
        receipt_rows=_sort_receipt_rows(rows),
        issues=[],
    )


def _rows_for_player(
    report: PlayerFeatureReceiptsReport,
    player: str,
) -> list[dict[str, object]]:
    player_key = _match_key(player)
    return [
        row
        for row in report.rows
        if _match_key(row.get("player")) == player_key
    ]


def _section_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        section = str(row.get("receipt_section_label") or "NFL Production")
        grouped.setdefault(section, []).append(row)

    section_rows = []
    for section, section_receipts in grouped.items():
        contribution_sum = round(
            sum(_float(row.get("contribution")) for row in section_receipts),
            4,
        )
        warning_count = sum(
            1 for row in section_receipts if str(row.get("warning_reason") or "")
        )
        imputed_count = sum(1 for row in section_receipts if _truthy(row.get("imputed_flag")))
        top_features = _top_features(section_receipts)
        section_rows.append(
            {
                "section": section,
                "receipt_rows": len(section_receipts),
                "section_contribution": contribution_sum,
                "warnings": warning_count,
                "imputed": imputed_count,
                "top_features": top_features,
            }
        )
    return sorted(
        section_rows,
        key=lambda row: (
            RECEIPT_SECTION_ORDER.get(str(row["section"]), 99),
            str(row["section"]),
        ),
    )


def _bridge_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    bridge_rows = []
    for row in rows:
        feature = str(row.get("formula_feature_name") or "")
        if feature not in BRIDGE_FEATURE_LABELS:
            continue
        bridge_rows.append(
            {
                "bridge_item": BRIDGE_FEATURE_LABELS[feature],
                "feature": feature,
                "raw_value": row.get("raw_feature_value", ""),
                "normalized_score": row.get("normalized_score", ""),
                "feature_weight": row.get("feature_weight", ""),
                "contribution": row.get("contribution", ""),
                "source": row.get("source_file", "") or row.get("source_name", ""),
                "warning": row.get("warning_reason", ""),
            }
        )
    return sorted(
        bridge_rows,
        key=lambda row: (
            {
                "Draft capital / prospect prior": 1,
                "Prior decay weight": 2,
                "NFL evidence weight": 3,
                "Final bridge contribution": 4,
            }.get(str(row["bridge_item"]), 99),
            str(row["feature"]),
        ),
    )


def _component_reconciliation_rows(
    report: PlayerFeatureReceiptsReport,
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    player_key = _match_key(rows[0].get("player"))
    summary_by_component = {
        str(row.get("component") or ""): row
        for row in report.component_summary_rows
        if _match_key(row.get("player")) == player_key
    }
    components = sorted(
        {str(row.get("component") or "") for row in rows},
        key=_component_sort_key,
    )
    reconciliation_rows = []
    for component in components:
        component_rows = [
            row for row in rows if str(row.get("component") or "") == component
        ]
        section_total_sum = round(
            sum(_float(row.get("contribution")) for row in component_rows),
            4,
        )
        summary = summary_by_component.get(component, {})
        receipt_contribution_sum = _float(
            summary.get("contribution_sum", section_total_sum),
        )
        delta = round(section_total_sum - receipt_contribution_sum, 4)
        if abs(delta) <= 0.05:
            status = "matched"
        else:
            status = "review_delta"
        reconciliation_rows.append(
            {
                "component": component,
                "section_total_sum": section_total_sum,
                "receipt_contribution_sum": receipt_contribution_sum,
                "component_score": summary.get("component_score", ""),
                "delta": delta,
                "status": status,
            }
        )
    return reconciliation_rows


def _lifecycle_explanation(rows: list[dict[str, object]]) -> str:
    first_explanation = next(
        (
            str(row.get("lifecycle_explanation") or "")
            for row in rows
            if str(row.get("lifecycle_explanation") or "")
        ),
        "",
    )
    lifecycle_label = str(rows[0].get("asset_lifecycle_label") or "")
    if lifecycle_label == "Established Veteran":
        note = "Draft capital not scored for established veterans."
        if note.lower() not in first_explanation.lower():
            return f"{first_explanation} {note}".strip()
    return first_explanation or (
        "This drilldown groups the player's receipts so each score source can be audited."
    )


def _sort_receipt_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        rows,
        key=lambda row: (
            RECEIPT_SECTION_ORDER.get(str(row.get("receipt_section_label") or ""), 99),
            -abs(_float(row.get("contribution"))),
            str(row.get("component") or ""),
            str(row.get("formula_feature_name") or ""),
        ),
    )


def _top_features(rows: list[dict[str, object]]) -> str:
    top_rows = sorted(
        rows,
        key=lambda row: -abs(_float(row.get("contribution"))),
    )[:3]
    return " | ".join(
        f"{row.get('formula_feature_name', '')}: {round(_float(row.get('contribution')), 2)}"
        for row in top_rows
        if row.get("formula_feature_name")
    )


def _component_sort_key(component: str) -> tuple[int, str]:
    order = {
        "private_lve_value": 1,
        "win_now_value": 2,
        "dynasty_hold_value": 3,
        "keeper_score": 4,
        "trade_value": 5,
    }
    return order.get(component, 99), component


def _match_key(value: object) -> str:
    return "".join(character.lower() for character in str(value or "") if character.isalnum())


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
